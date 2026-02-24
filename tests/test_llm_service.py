"""
Tests for nl_explorer.llm_service
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


@patch("nl_explorer.llm_service.litellm")
def test_chat_returns_text_message(mock_litellm, mock_flask_app):
    """chat() should extract the text content from a non-tool-call response."""
    from nl_explorer.llm_service import chat

    mock_choice = MagicMock()
    mock_choice.message.content = "Here is a bar chart."
    mock_choice.message.tool_calls = None
    mock_litellm.completion.return_value = MagicMock(choices=[mock_choice])

    with mock_flask_app.app_context():
        result = chat(
            messages=[{"role": "user", "content": "Show me sales by month"}],
            stream=False,
        )

    assert isinstance(result, dict)
    assert result["message"] == "Here is a bar chart."
    assert result["tool_calls"] == []


@patch("nl_explorer.llm_service.litellm")
def test_chat_returns_tool_calls(mock_litellm, mock_flask_app):
    """chat() should parse tool calls when the LLM responds with function calls."""
    import json
    from nl_explorer.llm_service import chat

    tc = MagicMock()
    tc.id = "call_abc"
    tc.function.name = "list_datasets"
    tc.function.arguments = json.dumps({})

    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_choice.message.tool_calls = [tc]
    mock_litellm.completion.return_value = MagicMock(choices=[mock_choice])

    with mock_flask_app.app_context():
        result = chat(messages=[{"role": "user", "content": "what datasets do I have?"}])

    assert result["tool_calls"][0]["name"] == "list_datasets"


@patch("nl_explorer.context_builder.DatasetDAO")
def test_dispatch_list_datasets(mock_dao, mock_flask_app):
    """dispatch_tool_call for list_datasets should call context_builder."""
    from unittest.mock import MagicMock

    mock_dao.find_all.return_value = []

    from nl_explorer.llm_service import dispatch_tool_call

    with mock_flask_app.app_context():
        result = dispatch_tool_call("list_datasets", {})

    import json
    payload = json.loads(result["content"])
    assert isinstance(payload, list)
