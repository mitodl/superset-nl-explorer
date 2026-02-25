"""
Flask Blueprint that serves the NL Explorer SPA and registers the REST API.

Registered via FLASK_APP_MUTATOR in superset_config.py.
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, Response, send_from_directory

logger = logging.getLogger(__name__)

# Compiled frontend assets are placed here during the Docker build
_DEFAULT_STATIC_DIR = "/app/extensions/nl-explorer/dist/frontend/dist"


def create_blueprint(static_dir: str | None = None) -> Blueprint:
    """Create and return the NL Explorer UI blueprint."""
    dist_dir = static_dir or os.environ.get("NL_EXPLORER_STATIC_DIR", _DEFAULT_STATIC_DIR)

    bp = Blueprint(
        "nl_explorer_ui",
        __name__,
        url_prefix="/nl-explorer",
    )

    @bp.route("/", defaults={"path": ""})
    @bp.route("/<path:path>")
    def serve_spa(path: str) -> Response:
        """Serve the SPA index or static assets."""
        if path and os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)  # type: ignore[return-value]
        return send_from_directory(dist_dir, "index.html")  # type: ignore[return-value]

    return bp
