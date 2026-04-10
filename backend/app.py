from __future__ import annotations

from pathlib import Path

from flask import Flask

from backend.config import Config, TestConfig
from backend.extensions import csrf, db, login_manager
import backend.models  # noqa: F401  # registers ORM mappers for create_all
from backend.models.user import User


def create_app(test_config: bool = False) -> Flask:
    repo_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(repo_root / "backend" / "templates"),
        static_folder=str(repo_root / "frontend"),
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

    from backend.routes.auth import auth_bp
    from backend.routes.main import main_bp
    from backend.routes.projects import projects_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()
