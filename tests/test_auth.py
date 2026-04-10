from backend.extensions import db
from backend.models.user import User

from tests.utils import csrf_token_for


def test_register_and_login(client, app):
    resp = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "csrf_token": csrf_token_for(client, "/register"),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        u = db.session.query(User).filter_by(email="test@example.com").first()
        assert u is not None
        assert u.check_password("password123")

    out = client.get("/logout", follow_redirects=False)
    assert out.status_code == 405

    login = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "password123",
            "csrf_token": csrf_token_for(client, "/login"),
        },
        follow_redirects=True,
    )
    assert login.status_code == 200
