from backend.extensions import db
from backend.models.user import User


def test_register_and_login_via_api(client, app):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert r.status_code == 201

    with app.app_context():
        u = db.session.query(User).filter_by(email="test@example.com").first()
        assert u is not None
        assert u.check_password("password123")

    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200

    r = client.get("/api/v1/me")
    assert r.status_code == 401

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert r.status_code == 200

    r = client.get("/api/v1/me")
    assert r.status_code == 200
    assert r.get_json()["user"]["email"] == "test@example.com"
