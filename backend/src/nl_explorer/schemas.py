"""
Marshmallow schemas for NL Explorer API request/response validation.
"""

from __future__ import annotations

from marshmallow import fields, Schema, validate


class MessageSchema(Schema):
    role = fields.Str(required=True, validate=validate.OneOf(["user", "assistant", "system"]))
    content = fields.Str(required=True)


class ChatRequestSchema(Schema):
    message = fields.Str(required=True, metadata={"description": "User's natural language query"})
    conversation = fields.List(
        fields.Nested(MessageSchema),
        load_default=[],
        metadata={"description": "Prior conversation history"},
    )
    dataset_id = fields.Int(
        load_default=None,
        metadata={"description": "Optional dataset ID to scope the conversation"},
    )
    dashboard_id = fields.Int(
        load_default=None,
        metadata={"description": "Optional dashboard ID to scope the conversation"},
    )
    stream = fields.Bool(
        load_default=False,
        metadata={"description": "Whether to stream the response via SSE"},
    )


class ColumnInfoSchema(Schema):
    name = fields.Str()
    type = fields.Str()
    description = fields.Str(allow_none=True)


class DatasetContextSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    columns = fields.List(fields.Nested(ColumnInfoSchema))


class ContextResponseSchema(Schema):
    datasets = fields.List(fields.Nested(DatasetContextSchema))


class ActionSchema(Schema):
    type = fields.Str(
        metadata={"description": "Action type: create_chart, create_dashboard, run_sql, explore_link"}
    )
    payload = fields.Dict()


class ChatResponseSchema(Schema):
    message = fields.Str(metadata={"description": "LLM text response"})
    actions = fields.List(
        fields.Nested(ActionSchema),
        metadata={"description": "Structured actions for the frontend to render"},
    )
    conversation = fields.List(
        fields.Nested(MessageSchema),
        metadata={"description": "Updated conversation history including this turn"},
    )


class ExecuteRequestSchema(Schema):
    action = fields.Nested(ActionSchema, required=True)


class ExecuteResponseSchema(Schema):
    success = fields.Bool()
    result = fields.Dict()
    error = fields.Str(allow_none=True)


class PluginConfigResponseSchema(Schema):
    model = fields.Str()
    streaming_enabled = fields.Bool()
    max_datasets_in_context = fields.Int()
