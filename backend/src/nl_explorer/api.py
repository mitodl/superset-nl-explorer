"""
NL Explorer REST API.

Registered with Flask-AppBuilder via FLASK_APP_MUTATOR in superset_config.py.
Mounted at /api/v1/nl_explorer/ by FAB's add_api().
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app, request, Response, stream_with_context
from flask_appbuilder.api import BaseApi, expose, permission_name, protect, safe

from nl_explorer import context_builder, llm_service
from nl_explorer.prompts.system import build_system_prompt
from nl_explorer.prompts.tools import TOOLS
from nl_explorer.schemas import (
    ChatRequestSchema,
    ChatResponseSchema,
    ContextResponseSchema,
    ExecuteRequestSchema,
    ExecuteResponseSchema,
    PluginConfigResponseSchema,
)

logger = logging.getLogger(__name__)


class NLExplorerRestApi(BaseApi):
    """NL Explorer REST API — registered via appbuilder.add_api()."""

    allow_browser_login = True
    resource_name = "nl_explorer"
    openapi_spec_tag = "NL Explorer"
    class_permission_name = "nl_explorer"

    # ------------------------------------------------------------------ #
    # GET /api/v1/nl_explorer/context
    # ------------------------------------------------------------------ #

    @expose("/context", methods=("GET",))
    @protect()
    @safe
    @permission_name("read")
    def get_context(self) -> Response:
        """Return datasets available to the current user for the chat UI."""
        cfg = current_app.config.get("NL_EXPLORER_CONFIG", {})
        max_datasets = cfg.get("max_datasets_in_context", context_builder.DEFAULT_MAX_DATASETS)
        ctx = context_builder.get_user_context(max_datasets=max_datasets)
        return self.response(200, **ContextResponseSchema().dump(ctx))

    # ------------------------------------------------------------------ #
    # POST /api/v1/nl_explorer/chat
    # ------------------------------------------------------------------ #

    @expose("/chat", methods=("POST",))
    @protect()
    @safe
    @permission_name("read")
    def chat(self) -> Response:
        """Send a natural language message and receive an LLM response."""
        body = request.get_json(force=True) or {}
        req = ChatRequestSchema().load(body)

        cfg = current_app.config.get("NL_EXPLORER_CONFIG", {})
        max_datasets = cfg.get("max_datasets_in_context", context_builder.DEFAULT_MAX_DATASETS)

        ctx = context_builder.get_user_context(
            dataset_id=req.get("dataset_id"),
            max_datasets=max_datasets,
        )
        try:
            from superset.utils.core import get_user

            user = get_user()
            current_user_name = f"{user.first_name} {user.last_name}".strip() if user else None
        except Exception:
            current_user_name = None

        system_prompt = build_system_prompt(ctx, current_user=current_user_name)

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for turn in req.get("conversation", []):
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": req["message"]})

        if req.get("stream"):
            return self._stream_chat(messages, req)

        return self._sync_chat(messages, req)

    def _sync_chat(self, messages: list[dict], req: dict) -> Response:
        """Run a synchronous (non-streaming) chat turn with tool call loop."""
        MAX_TOOL_ROUNDS = 5

        for _ in range(MAX_TOOL_ROUNDS):
            result = llm_service.chat(messages=messages, tools=TOOLS, stream=False)
            assert isinstance(result, dict)

            tool_calls = result.get("tool_calls", [])
            if not tool_calls:
                break

            messages.append({"role": "assistant", "content": result.get("message", ""), "tool_calls": tool_calls})
            for tc in tool_calls:
                tool_result = llm_service.dispatch_tool_call(tc["name"], tc["arguments"])
                messages.append(tool_result)

        conversation_out = [
            {"role": m["role"], "content": m.get("content") or ""}
            for m in messages
            if m["role"] in ("user", "assistant") and m.get("content")
        ]

        response_payload = {
            "message": result.get("message", ""),  # type: ignore[possibly-undefined]
            "actions": [],
            "conversation": conversation_out,
        }
        return self.response(200, **ChatResponseSchema().dump(response_payload))

    def _stream_chat(self, messages: list[dict], req: dict) -> Response:
        """Return an SSE streaming response."""

        def generate():  # type: ignore[return]
            try:
                gen = llm_service.chat(messages=messages, tools=TOOLS, stream=True)
                for chunk in gen:  # type: ignore[union-attr]
                    yield chunk
            except Exception as exc:
                logger.exception("Streaming chat error")
                yield f'data: {json.dumps({"type": "error", "content": str(exc)})}\n\n'

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ------------------------------------------------------------------ #
    # POST /api/v1/nl_explorer/execute
    # ------------------------------------------------------------------ #

    @expose("/execute", methods=("POST",))
    @protect()
    @safe
    @permission_name("write")
    def execute(self) -> Response:
        """Execute a structured action (create chart, dashboard, run SQL)."""
        body = request.get_json(force=True) or {}
        req = ExecuteRequestSchema().load(body)
        action = req["action"]

        result = llm_service.dispatch_tool_call(action["type"], action.get("payload", {}))
        payload = json.loads(result.get("content", "{}"))

        response_payload = {
            "success": "error" not in payload,
            "result": payload,
            "error": payload.get("error"),
        }
        return self.response(200, **ExecuteResponseSchema().dump(response_payload))

    # ------------------------------------------------------------------ #
    # GET /api/v1/nl_explorer/config
    # ------------------------------------------------------------------ #

    @expose("/config", methods=("GET",))
    @protect()
    @safe
    @permission_name("read")
    def get_plugin_config(self) -> Response:
        """Return non-sensitive plugin configuration for the frontend."""
        cfg = current_app.config.get("NL_EXPLORER_CONFIG", {})
        payload = {
            "model": cfg.get("model", "gpt-4o"),
            "streaming_enabled": cfg.get("streaming", True),
            "max_datasets_in_context": cfg.get(
                "max_datasets_in_context", context_builder.DEFAULT_MAX_DATASETS
            ),
        }
        return self.response(200, **PluginConfigResponseSchema().dump(payload))
