"""
Thin wrappers around Superset's chart and dashboard creation commands.

Provides a clean interface for the LLM service to create Superset resources
without directly coupling to Superset's internal command layer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app

logger = logging.getLogger(__name__)

# Module-level imports with fallback so tests can patch directly.
try:
    from superset.utils.core import get_user
except ImportError:
    get_user = None  # type: ignore[assignment]

try:
    from superset.charts.commands.create import CreateChartCommand
except ImportError:
    CreateChartCommand = None  # type: ignore[assignment]

try:
    from superset.dashboards.commands.create import CreateDashboardCommand
except ImportError:
    CreateDashboardCommand = None  # type: ignore[assignment]

try:
    from superset.daos.dashboard import DashboardDAO
except ImportError:
    DashboardDAO = None  # type: ignore[assignment]


def preview_chart(
    dataset_id: int,
    viz_type: str,
    form_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate a Superset Explore URL for previewing a chart configuration
    without saving it permanently.

    Returns a dict with an "explore_url" key.
    """
    from flask import current_app

    merged_form_data = {
        "datasource": f"{dataset_id}__table",
        "viz_type": viz_type,
        **form_data,
    }
    params = json.dumps(merged_form_data)

    base_url = current_app.config.get("WEBDRIVER_BASEURL", "http://localhost:8088/")
    explore_url = (
        f"{base_url.rstrip('/')}/explore/"
        f"?datasource_type=table&datasource_id={dataset_id}"
        f"&form_data={params}"
    )
    return {
        "type": "explore_link",
        "explore_url": explore_url,
        "dataset_id": dataset_id,
        "viz_type": viz_type,
    }


def create_chart(
    slice_name: str,
    datasource_id: int,
    viz_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    Permanently create and save a chart in Superset.

    Returns a dict with the created chart's ID and a link to view it.
    """
    user = get_user()
    command = CreateChartCommand(
        actor=user,
        data={
            "slice_name": slice_name,
            "datasource_id": datasource_id,
            "datasource_type": "table",
            "viz_type": viz_type,
            "params": json.dumps(params),
            "owners": [user.id] if user else [],
        },
    )
    chart = command.run()
    logger.info("Created chart id=%s name=%s", chart.id, slice_name)

    base_url = current_app.config.get("WEBDRIVER_BASEURL", "http://localhost:8088/")
    return {
        "type": "chart_created",
        "chart_id": chart.id,
        "chart_name": chart.slice_name,
        "chart_url": f"{base_url.rstrip('/')}/explore/?slice_id={chart.id}",
    }


def create_dashboard(
    title: str,
    chart_ids: list[int],
) -> dict[str, Any]:
    """
    Create a new Superset dashboard containing the specified charts.

    Returns a dict with the created dashboard's ID and URL.
    """
    user = get_user()

    # Build a minimal position JSON placing charts in a single-column layout
    position_json = _build_position_json(chart_ids)

    command = CreateDashboardCommand(
        actor=user,
        data={
            "dashboard_title": title,
            "slug": None,
            "owners": [user.id] if user else [],
            "position_json": json.dumps(position_json),
            "css": "",
            "json_metadata": "{}",
            "published": False,
        },
    )
    dashboard = command.run()

    DashboardDAO.set_dash_to_charts(dashboard, chart_ids)

    logger.info("Created dashboard id=%s title=%s", dashboard.id, title)

    base_url = current_app.config.get("WEBDRIVER_BASEURL", "http://localhost:8088/")
    return {
        "type": "dashboard_created",
        "dashboard_id": dashboard.id,
        "dashboard_title": dashboard.dashboard_title,
        "dashboard_url": f"{base_url.rstrip('/')}/superset/dashboard/{dashboard.id}/",
    }


def _build_position_json(chart_ids: list[int]) -> dict[str, Any]:
    """Build a simple vertical layout position_json for a set of chart IDs."""
    import uuid

    children = []
    components: dict[str, Any] = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": children},
    }

    for idx, chart_id in enumerate(chart_ids):
        row_id = f"ROW-{idx}"
        col_id = f"COL-{idx}"
        chart_comp_id = f"CHART-{chart_id}"

        components[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [col_id],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        components[col_id] = {
            "type": "COLUMN",
            "id": col_id,
            "children": [chart_comp_id],
            "meta": {"background": "BACKGROUND_TRANSPARENT", "width": 12},
        }
        components[chart_comp_id] = {
            "type": "CHART",
            "id": chart_comp_id,
            "children": [],
            "meta": {"chartId": chart_id, "width": 4, "height": 50},
        }
        children.append(row_id)

    return components
