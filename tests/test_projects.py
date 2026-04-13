from backend.constants import PROJECT_COMPLETED
from backend.extensions import db
from backend.models.collaboration import CollaborationRequest
from backend.models.project import Project


def test_create_project_and_complete_via_api(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Owner",
            "email": "owner@example.com",
            "password": "password123",
        },
    )
    r = client.post(
        "/api/v1/projects",
        json={
            "title": "Portfolio site",
            "description": "A small portfolio.",
            "stage": "development",
            "support_needed": "UI review",
        },
    )
    assert r.status_code == 201
    pid = r.get_json()["project"]["id"]

    feed = client.get("/api/v1/feed")
    assert feed.status_code == 200
    titles = [p["title"] for p in feed.get_json()["projects"]]
    assert "Portfolio site" in titles

    with app.app_context():
        p = db.session.get(Project, pid)
        assert p is not None

    r = client.post(f"/api/v1/projects/{pid}/complete")
    assert r.status_code == 200

    with app.app_context():
        p2 = db.session.get(Project, pid)
        assert p2.status == PROJECT_COMPLETED

    wall = client.get("/api/v1/celebration")
    assert wall.status_code == 200
    ctitles = [p["title"] for p in wall.get_json()["projects"]]
    assert "Portfolio site" in ctitles


def test_duplicate_collaboration_request_blocked_api(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
        },
    )
    r = client.post(
        "/api/v1/projects",
        json={
            "title": "Collab test project",
            "description": "Desc",
            "stage": "development",
            "support_needed": "Tester",
        },
    )
    pid = r.get_json()["project"]["id"]

    client.post("/api/v1/auth/logout")

    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "password123",
        },
    )

    def post_collab():
        return client.post(
            f"/api/v1/projects/{pid}/collaboration",
            json={"message": "Keen to help"},
        )

    assert post_collab().status_code == 201
    r2 = post_collab()
    assert r2.status_code == 400

    with app.app_context():
        n = (
            db.session.query(CollaborationRequest)
            .filter_by(project_id=pid)
            .count()
        )
        assert n == 1
