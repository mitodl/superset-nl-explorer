"""
Builds LLM context (system prompt payload) from Superset datasets and schemas
visible to the currently authenticated user.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import with fallback so the module can be imported without Superset installed.
# Tests patch nl_explorer.context_builder.DatasetDAO directly.
try:
    from superset.daos.dataset import DatasetDAO
except ImportError:
    DatasetDAO = None  # type: ignore[assignment,misc]

# Maximum number of datasets to include in the LLM context window.
# Operators can override via NL_EXPLORER_CONFIG["max_datasets_in_context"].
DEFAULT_MAX_DATASETS = 20
# Maximum columns per dataset included in context.
DEFAULT_MAX_COLUMNS = 50


def get_user_context(
    dataset_id: int | None = None,
    max_datasets: int = DEFAULT_MAX_DATASETS,
    max_columns: int = DEFAULT_MAX_COLUMNS,
) -> dict[str, Any]:
    """
    Return a structured context dict describing datasets available to the
    current user. Used to build the LLM system prompt.

    Args:
        dataset_id: If provided, only include this specific dataset (for
            Explore/Dashboard panel context).
        max_datasets: Maximum number of datasets to include.
        max_columns: Maximum columns per dataset.

    Returns:
        Dict with "datasets" key containing summarised dataset info.
    """
    try:
        if dataset_id is not None:
            datasets = DatasetDAO.find_by_ids([dataset_id])
        else:
            # Fetch all datasets; DatasetDAO respects current user's permissions
            datasets = DatasetDAO.find_all()[:max_datasets]
    except Exception:
        logger.exception("Failed to fetch datasets for NL Explorer context")
        return {"datasets": []}

    result = []
    for ds in datasets:
        try:
            columns = []
            for col in (ds.columns or [])[:max_columns]:
                columns.append(
                    {
                        "name": col.column_name,
                        "type": str(col.type) if col.type else "unknown",
                        "description": col.description or None,
                    }
                )
            result.append(
                {
                    "id": ds.id,
                    "name": ds.table_name,
                    "description": getattr(ds, "description", None),
                    "columns": columns,
                }
            )
        except Exception:
            logger.exception("Failed to serialize dataset %s for context", getattr(ds, "id", "?"))

    return {"datasets": result}
