"""
LiteLLM-based LLM service for NL Explorer.

Handles:
- Non-streaming chat completions
- SSE streaming completions
- LLM tool/function call dispatch
- Config from Flask app config (NL_EXPLORER_CONFIG)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Generator
from typing import Any

# Module-level import so tests can patch nl_explorer.llm_service.litellm
try:
    import litellm
except ImportError:
    litellm = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _get_config() -> dict[str, Any]:
    """Read NL_EXPLORER_CONFIG from the Flask app config."""
    from flask import current_app

    return current_app.config.get("NL_EXPLORER_CONFIG", {})


def chat(
    messages: list[dict[str, Any]],
    tools: list[dict] | None = None,
    stream: bool = False,
) -> dict[str, Any] | Generator[str, None, None]:
    """
    Send a chat request to the configured LLM via LiteLLM.

    Args:
        messages: List of OpenAI-format message dicts (role + content).
        tools: Optional list of tool definitions for function calling.
        stream: If True, returns a generator of SSE-formatted strings.

    Returns:
        If stream=False: dict with "message" and "tool_calls" keys.
        If stream=True: generator of SSE event strings.
    """
    cfg = _get_config()
    model = cfg.get("model", "gpt-4o")
    api_key = cfg.get("api_key")
    api_base = cfg.get("api_base")  # For Ollama / custom endpoints
    max_tokens = cfg.get("max_tokens", 4096)

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    if stream:
        return _stream_response(litellm.completion(**kwargs))

    response = litellm.completion(**kwargs)
    choice = response.choices[0]
    msg = choice.message

    tool_calls = []
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments or "{}"),
                }
            )

    return {
        "message": msg.content or "",
        "tool_calls": tool_calls,
    }


def _stream_response(response: Any) -> Generator[str, None, None]:
    """Convert a LiteLLM streaming response to SSE-formatted strings."""
    for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            data = json.dumps({"type": "text", "content": delta.content})
            yield f"data: {data}\n\n"
    yield "data: [DONE]\n\n"


def dispatch_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch a tool call from the LLM to the appropriate executor.

    Returns a dict suitable for appending to the conversation as a tool message.
    """
    from nl_explorer import chart_creator, context_builder

    try:
        if tool_name == "list_datasets":
            ctx = context_builder.get_user_context()
            result = ctx["datasets"]
        elif tool_name == "get_dataset_schema":
            ctx = context_builder.get_user_context(dataset_id=arguments["dataset_id"], max_columns=200)
            result = ctx["datasets"][0] if ctx["datasets"] else {}
        elif tool_name == "run_sql":
            result = _run_sql(arguments)
        elif tool_name == "preview_chart":
            result = chart_creator.preview_chart(
                dataset_id=arguments["dataset_id"],
                viz_type=arguments["viz_type"],
                form_data=arguments.get("form_data", {}),
            )
        elif tool_name == "create_chart":
            result = chart_creator.create_chart(
                slice_name=arguments["slice_name"],
                datasource_id=arguments["datasource_id"],
                viz_type=arguments["viz_type"],
                params=arguments.get("params", {}),
            )
        elif tool_name == "create_dashboard":
            result = chart_creator.create_dashboard(
                title=arguments["title"],
                chart_ids=arguments["chart_ids"],
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except Exception as exc:
        logger.exception("Tool call %s failed", tool_name)
        result = {"error": str(exc)}

    return {
        "role": "tool",
        "name": tool_name,
        "content": json.dumps(result),
    }


def _run_sql(arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute SQL via Superset's SQL Lab execution layer."""
    from superset.daos.database import DatabaseDAO
    from superset.sql_lab import get_sql_results

    database_id = arguments["database_id"]
    sql = arguments["sql"]
    limit = arguments.get("limit", 100)

    database = DatabaseDAO.find_by_id(database_id)
    if not database:
        return {"error": f"Database {database_id} not found"}

    # Append a LIMIT clause if not already present
    if "limit" not in sql.lower():
        sql = f"{sql.rstrip(';')} LIMIT {limit}"

    results = get_sql_results(
        ct=None,
        query_id=None,
        rendered_query=sql,
        return_results=True,
        store_results=False,
        username=None,
        start_time=None,
        expand_data=False,
        datasource_id=database_id,
        datasource_type="table",
    )
    return results or {}
