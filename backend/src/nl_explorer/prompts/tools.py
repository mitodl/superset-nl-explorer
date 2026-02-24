"""
LLM tool definitions (function calling) passed to the LLM alongside user messages.

Each tool maps to an action that the NL Explorer backend can execute.
"""

from __future__ import annotations

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_datasets",
            "description": (
                "List Superset datasets available to the current user. "
                "Returns dataset IDs, names, and column summaries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter datasets by name.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dataset_schema",
            "description": (
                "Get detailed schema for a specific dataset including all columns, "
                "data types, and available metrics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "integer",
                        "description": "Numeric Superset dataset ID.",
                    }
                },
                "required": ["dataset_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Execute a SQL query against a Superset database and return sample results. "
                "Use for data exploration and to verify column values before chart creation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to execute."},
                    "database_id": {
                        "type": "integer",
                        "description": "Superset database ID to run the query against.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum rows to return (default 100).",
                        "default": 100,
                    },
                },
                "required": ["sql", "database_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "preview_chart",
            "description": (
                "Generate an Explore link (interactive chart builder URL) for a chart "
                "configuration without permanently saving it. Use this to let the user "
                "preview and refine a chart before saving."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "integer",
                        "description": "Superset dataset ID.",
                    },
                    "viz_type": {
                        "type": "string",
                        "description": (
                            "Superset visualisation type. Common values: "
                            "'echarts_timeseries_line', 'echarts_timeseries_bar', "
                            "'echarts_area', 'table', 'pie', 'scatter'."
                        ),
                    },
                    "form_data": {
                        "type": "object",
                        "description": (
                            "Superset form_data dict with chart configuration. "
                            "At minimum include 'metrics' and 'groupby'."
                        ),
                    },
                },
                "required": ["dataset_id", "viz_type", "form_data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_chart",
            "description": (
                "Permanently create and save a chart in Superset. "
                "Use only after the user confirms they want to save the chart."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slice_name": {
                        "type": "string",
                        "description": "Human-readable name for the chart.",
                    },
                    "datasource_id": {
                        "type": "integer",
                        "description": "Superset dataset ID.",
                    },
                    "viz_type": {
                        "type": "string",
                        "description": "Superset visualisation type.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Superset form_data dict for the chart.",
                    },
                },
                "required": ["slice_name", "datasource_id", "viz_type", "params"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_dashboard",
            "description": (
                "Create a new Superset dashboard from a list of existing chart IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Dashboard title.",
                    },
                    "chart_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of Superset chart IDs to include.",
                    },
                },
                "required": ["title", "chart_ids"],
            },
        },
    },
]
