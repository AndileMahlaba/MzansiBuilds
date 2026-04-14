from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from flask import Flask, redirect, request
from flask_cors import CORS
from flask_login import current_user
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from backend.config import Config, TestConfig
from backend.extensions import csrf, db, limiter, login_manager
from backend.http_security import register_error_handlers, register_security_headers
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
    limiter.init_app(app)
    register_security_headers(app)
    register_error_handlers(app)

    @app.template_global("visible_owner_bio")
    def visible_owner_bio(owner):
        """Return bio text for SSR when the viewer may see it (public profile or self)."""
        if owner is None:
            return None
        bio = (getattr(owner, "bio", None) or "").strip()
        if not bio:
            return None
        if getattr(owner, "profile_public", True):
            return bio
        if current_user.is_authenticated and getattr(current_user, "id", None) == owner.id:
            return bio
        return None

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
    csrf.exempt(api_v1_bp)

    with app.app_context():
        try:
            db.create_all()
            _ensure_user_profile_public_column()
            _ensure_user_email_verified_column()
            _ensure_project_repo_demo_columns()
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


def _ensure_user_profile_public_column() -> None:
    """Add profile_public when upgrading existing DBs (SQLite / Postgres)."""
    engine = db.engine
    dialect = engine.dialect.name
    if dialect == "sqlite":
        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("users")}
        if "profile_public" in cols:
            return
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN profile_public BOOLEAN NOT NULL DEFAULT 1")
            )
    elif dialect == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_public BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )


def _ensure_user_email_verified_column() -> None:
    engine = db.engine
    dialect = engine.dialect.name
    if dialect == "sqlite":
        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("users")}
        if "email_verified" in cols:
            return
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 1")
            )
    elif dialect == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )


def _ensure_project_repo_demo_columns() -> None:
    engine = db.engine
    dialect = engine.dialect.name
    if dialect == "sqlite":
        insp = inspect(engine)
        if "projects" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("projects")}
        with engine.begin() as conn:
            if "repo_url" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN repo_url VARCHAR(500) NOT NULL DEFAULT ''"))
            if "demo_url" not in cols:
                conn.execute(text("ALTER TABLE projects ADD COLUMN demo_url VARCHAR(500) NOT NULL DEFAULT ''"))
    elif dialect == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS repo_url VARCHAR(500) NOT NULL DEFAULT ''"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS demo_url VARCHAR(500) NOT NULL DEFAULT ''"
                )
            )
