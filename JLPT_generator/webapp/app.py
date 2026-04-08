from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from JLPT_generator.webapp.routes import bp as web_bp


def create_app() -> Flask:
    repo_root = Path(__file__).resolve().parents[2]
    assets_dir = repo_root / "assets"
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder=str(assets_dir),
        static_url_path="/static",
    )

    # Flask sessions aren't used for app state (we keep state in a signed token),
    # but Flask still wants a secret key for some internals/extensions.
    app.secret_key = os.getenv("SECRET_KEY", "").strip() or "dev-insecure-secret-key"

    app.register_blueprint(web_bp)
    return app

