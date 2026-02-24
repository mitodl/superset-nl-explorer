"""
superset-nl-explorer: Natural language LLM interface for Apache Superset.

Provides a chat-based UI for data exploration and chart/dashboard creation,
deployed as a Superset extension.
"""

from __future__ import annotations

import importlib.resources as _res
from pathlib import Path


def extension_path() -> str:
    """Return the path to the bundled extension directory.

    Use this in superset_config.py::

        import nl_explorer
        LOCAL_EXTENSIONS = [nl_explorer.extension_path()]
    """
    return str(Path(__file__).parent.parent.parent)


__all__ = ["extension_path"]
