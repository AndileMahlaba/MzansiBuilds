from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from flask import Flask, redirect, request
from flask_cors import CORS
from sqlalchemy.exc import OperationalError

from backend.config import Config, TestConfig
from backend.extensions import csrf, db, login_manager
import backend.models  # noqa: F401  # registers ORM mappers for create_all
from backend.models.user import User

_BACKEND_ROOT = Path(__file__).resolve().parent


def create_app(test_config: bool = False) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(_BACKEND_ROOT / "templates"),
        static_folder=str(_BACKEND_ROOT / "static"),
        static_url_path="/static",
    )

    app.config.from_object(TestConfig if test_config else Config)
    if test_config:
        app.config["TESTING"] = True

    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    cors_origins = [
        o.strip()
        for o in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if o.strip()
    ]
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "allow_headers": ["Content-Type"],
                "methods": ["GET", "POST", "PATCH", "OPTIONS"],
            }
        },
    )

    from backend.routes.api_v1 import api_v1_bp
    from backend.routes.main import main_bp

    @app.before_request
    def _normalize_api_urls():
        """Avoid the SPA catch-all returning 404 for common API mistakes.

        - /api and /api/ → /api/v1 (some dev proxies only mount ``/api``, so people often open /api in the browser).
        - /api/v1/.../ trailing slash → canonical path without slash (strict Flask routes do not match).
        """
        p = request.path
        if p in ("/api", "/api/") and request.method in ("GET", "HEAD"):
            return redirect("/api/v1", code=308)
        if p.startswith("/api/v1") and len(p) > len("/api/v1") and p.endswith("/"):
            return redirect(p.rstrip("/"), code=308)
        return None

    # Register explicit /api/v1 routes after the SPA catch-all so they override ``/<path:path>``.
    app.register_blueprint(main_bp)
    app.register_blueprint(api_v1_bp)

    with app.app_context():
        try:
            db.create_all()
        except OperationalError as err:
            parts = [str(err)]
            if getattr(err, "orig", None) is not None:
                parts.append(str(err.orig))
            msg = " ".join(parts)
            if "could not translate host name" in msg or "Name or service not known" in msg:
                raise RuntimeError(
                    "Database DNS failed (common on IPv4 with Supabase direct db.* host). "
                    "Set DATABASE_SESSION_URL to the Session pooler URI from Supabase → Connect, "
                    "or DATABASE_URL + SUPABASE_POOLER_REGION. See .env.example."
                ) from err
            raise

    return app
