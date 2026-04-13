import os

# Must run before importing backend (so tests do not read developer .env for URL assertions).
os.environ.setdefault("MZANSI_SKIP_DOTENV", "1")

import pytest

from backend.app import create_app
from backend.extensions import db


@pytest.fixture
def app():
    application = create_app(test_config=True)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
