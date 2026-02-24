"""
Extension entrypoint called by Superset's extension loader at startup.

Registers the NL Explorer REST API with Superset.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register() -> None:
    """Register all extension APIs and blueprints with Superset."""
    try:
        from superset_core.api.rest_api import add_extension_api

        from nl_explorer.api import NLExplorerRestApi

        add_extension_api(NLExplorerRestApi)
        logger.info("NL Explorer extension registered successfully")
    except Exception:
        logger.exception("Failed to register NL Explorer extension")
        raise


# Superset calls the module's register() at extension load time
register()
