"""
System prompt builder for the NL Explorer LLM.

Injects Superset instance context (available datasets, chart types, current user)
into the LLM system prompt.
"""

from __future__ import annotations

from typing import Any

CHART_TYPE_GUIDE = """
Available Superset chart types (use the viz_type value when calling tools):
- echarts_timeseries_line  : Line chart for time series data
- echarts_timeseries_bar   : Bar chart for time series or categorical comparisons
- echarts_area             : Area chart for cumulative/stacked time series
- table                    : Tabular data display with sorting/filtering
- pie                      : Pie/donut chart for part-to-whole relationships
- scatter                  : Scatter plot for correlation analysis
- echarts_box_plot         : Box-and-whisker plot for distributions
- big_number_total         : Single KPI metric display
- big_number               : KPI with trend line
- histogram                : Distribution histogram
- heatmap                  : Heatmap for two-dimensional comparisons
- treemap_v2               : Treemap for hierarchical proportions
- funnel                   : Funnel chart for conversion analysis
""".strip()


def build_system_prompt(context: dict[str, Any], current_user: str | None = None) -> str:
    """
    Build the LLM system prompt with dataset context and instructions.

    Args:
        context: Dict from context_builder.get_user_context().
        current_user: Display name of the authenticated Superset user.

    Returns:
        System prompt string.
    """
    datasets = context.get("datasets", [])

    dataset_summary_lines = []
    for ds in datasets:
        col_names = ", ".join(c["name"] for c in ds.get("columns", [])[:20])
        desc = f" — {ds['description']}" if ds.get("description") else ""
        dataset_summary_lines.append(
            f"  • [{ds['id']}] {ds['name']}{desc}\n    Columns: {col_names}"
        )

    dataset_block = "\n".join(dataset_summary_lines) if dataset_summary_lines else "  (none available)"
    user_line = f"Current user: {current_user}\n" if current_user else ""

    return f"""You are an AI data analyst assistant embedded in Apache Superset.
{user_line}
Your job is to help users explore data and create charts and dashboards using natural language.

You have access to the following tools:
- list_datasets: see all available datasets
- get_dataset_schema: inspect columns and metrics for a dataset
- run_sql: execute SQL for data exploration (respects user permissions)
- preview_chart: generate an Explore link to preview a chart configuration
- create_chart: permanently save a chart (ask for confirmation first)
- create_dashboard: create a dashboard from chart IDs (ask for confirmation first)

Available datasets (as of this session):
{dataset_block}

{CHART_TYPE_GUIDE}

Guidelines:
- Always confirm with the user before permanently creating charts or dashboards.
- When the user asks to visualise something, start with preview_chart to show an Explore link.
- For ambiguous requests, ask a clarifying question rather than guessing.
- When running SQL, keep queries efficient — use LIMIT when exploring.
- Be concise but helpful. Explain what you are doing and why.
"""
