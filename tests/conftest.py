"""
Pytest configuration and fixtures for NL Explorer tests.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def mock_flask_app():
    """Minimal Flask app context for testing without a full Superset instance."""
    from flask import Flask

    app = Flask(__name__)
    app.config["NL_EXPLORER_CONFIG"] = {
        "model": "gpt-4o",
        "api_key": "test-key",
        "streaming": False,
        "max_datasets_in_context": 5,
    }
    app.config["WEBDRIVER_BASEURL"] = "http://localhost:8088/"
    return app
