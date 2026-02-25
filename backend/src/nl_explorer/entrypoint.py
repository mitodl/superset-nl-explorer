"""
Extension entrypoint for use with FLASK_APP_MUTATOR in superset_config.py.

Usage in superset_config.py:

    def FLASK_APP_MUTATOR(app):
        from nl_explorer.entrypoint import register
        register(app)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register(app) -> None:  # type: ignore[type-arg]
    """Register the NL Explorer blueprint and REST API with a Flask app."""
    try:
        from nl_explorer.blueprint import create_blueprint

        app.register_blueprint(create_blueprint())
        logger.info("NL Explorer UI blueprint registered at /nl-explorer/")
    except Exception:
        logger.exception("Failed to register NL Explorer UI blueprint")
        raise

    try:
        from superset.extensions import appbuilder

        from nl_explorer.api import NLExplorerRestApi

        appbuilder.add_api(NLExplorerRestApi)
        logger.info("NL Explorer REST API registered at /api/v1/nl_explorer/")
    except Exception:
        logger.exception("Failed to register NL Explorer REST API")
        raise
