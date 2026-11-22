"""aegis-log: a small log-enrichment service."""

import logging

from flask import Flask

from aegis.config import Settings, load_settings
from aegis.intel import LocalFeedProvider
from aegis.normalize import MAX_BODY_BYTES
from aegis.rules import load_rules
from aegis.store import EventStore


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES  # larger bodies get 413
    app.extensions["aegis"] = {
        "settings": settings,
        "store": EventStore(settings.db_path),
        "intel": LocalFeedProvider(settings.intel_feed),
        "rules": load_rules(settings.rules_dir),
    }

    from aegis.routes import bp

    app.register_blueprint(bp)
    return app
