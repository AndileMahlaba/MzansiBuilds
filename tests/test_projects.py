from backend.constants import PROJECT_COMPLETED
from backend.extensions import db
from backend.models.project import Project

from tests.utils import csrf_token_for


def test_create_project_and_complete(client, app):
    client.post(
        "/register",
        data={
            "name": "Owner",
            "email": "owner@example.com",
            "password": "password123",
            "csrf_token": csrf_token_for(client, "/register"),
        },
        follow_redirects=True,
    )

    client.post(
        "/projects/new",
        data={
            "title": "Portfolio site",
            "description": "A small portfolio.",
            "stage": "development",
            "support_needed": "UI review",
            "csrf_token": csrf_token_for(client, "/projects/new"),
            "submit": "Publish project",
        },
        follow_redirects=True,
    )

    feed = client.get("/feed")
    assert b"Portfolio site" in feed.data

    with app.app_context():
        p = db.session.query(Project).filter_by(title="Portfolio site").first()
        assert p is not None
        pid = p.id

    client.post(
        f"/projects/{pid}/complete",
        data={
            "csrf_token": csrf_token_for(client, f"/projects/{pid}"),
            "submit": "Mark project as complete",
        },
        follow_redirects=True,
    )

    with app.app_context():
        p2 = db.session.get(Project, pid)
        assert p2.status == PROJECT_COMPLETED

    wall = client.get("/celebration")
    assert b"Portfolio site" in wall.data
