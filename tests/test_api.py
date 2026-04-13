def test_ssr_feed_and_static(client):
    r = client.get("/ssr/feed")
    assert r.status_code == 200
    assert b"Developer feed" in r.data
    r2 = client.get("/mzansi-assets/css/mzansi_ssr.css")
    assert r2.status_code == 200
    assert b"--green" in r2.data
    assert client.get("/ssr/feed").headers.get("X-Mzansi-Template") == "feed_ssr_v2"


def test_api_root_redirects_from_slash_only_paths(client):
    """Opening /api or /api/ in the browser used to hit the SPA catch-all and show a generic 404."""
    for path in ("/api", "/api/"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 308
        assert r.headers.get("Location") == "/api/v1"
    r = client.get("/api/v1/", follow_redirects=False)
    assert r.status_code == 308
    assert r.headers.get("Location") == "/api/v1"


def test_api_discovery(client):
    r = client.get("/api/v1")
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("system")
    assert "version" in data
    assert "endpoints" in data
    assert data["endpoints"].get("stats") == "/api/v1/stats"


def test_api_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"


def test_api_stats(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    data = r.get_json()
    assert "developers" in data
    assert "stage_counts" in data
    assert "idea" in data["stage_counts"]


def test_api_register_me_logout(client, app):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": "API User",
            "email": "apiuser@example.com",
            "password": "password123",
        },
    )
    assert r.status_code == 201
    assert r.get_json()["user"]["email"] == "apiuser@example.com"

    r = client.get("/api/v1/me")
    assert r.status_code == 200
    assert r.get_json()["user"]["name"] == "API User"

    client.post("/api/v1/auth/logout")
    r = client.get("/api/v1/me")
    assert r.status_code == 401


def test_api_create_project_and_feed(client, app):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Owner",
            "email": "ownerapi@example.com",
            "password": "password123",
        },
    )
    r = client.post(
        "/api/v1/projects",
        json={
            "title": "API Project",
            "description": "From tests",
            "stage": "development",
            "support_needed": "Reviewer",
        },
    )
    assert r.status_code == 201
    pid = r.get_json()["project"]["id"]

    r = client.get("/api/v1/feed")
    assert r.status_code == 200
    titles = [p["title"] for p in r.get_json()["projects"]]
    assert "API Project" in titles

    r = client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    assert r.get_json()["project"]["title"] == "API Project"


def test_supabase_session_pooler_rewrite_from_direct_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:sekrit@db.abcdefghijklmnop.supabase.co:5432/postgres",
    )
    monkeypatch.setenv("SUPABASE_POOLER_REGION", "eu-west-2")
    from backend.config import _database_uri

    uri = _database_uri()
    assert "aws-0-eu-west-2.pooler.supabase.com" in uri
    assert "postgres.abcdefghijklmnop" in uri
    assert "sslmode=require" in uri


def test_supabase_rewrite_when_direct_url_uses_pooler_style_username(monkeypatch):
    """Mixed-up copy/paste: postgres.ref on db.* host — still rewrite to pooler."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres.abcdefghijklmnop:sekrit@db.abcdefghijklmnop.supabase.co:5432/postgres",
    )
    monkeypatch.setenv("SUPABASE_POOLER_REGION", "eu-west-1")
    monkeypatch.delenv("DATABASE_SESSION_URL", raising=False)
    from backend.config import _database_uri

    uri = _database_uri()
    assert "aws-0-eu-west-1.pooler.supabase.com" in uri
    assert "db." not in uri.split("@")[-1]


def test_database_session_url_overrides_direct_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:wrong@db.shouldnotuse.supabase.co:5432/postgres",
    )
    monkeypatch.setenv(
        "DATABASE_SESSION_URL",
        "postgresql://postgres.abc:good@aws-0-ap-south-1.pooler.supabase.com:5432/postgres",
    )
    monkeypatch.delenv("SUPABASE_POOLER_REGION", raising=False)
    from backend.config import _database_uri

    uri = _database_uri()
    assert "ap-south-1.pooler.supabase.com" in uri
    assert "shouldnotuse" not in uri
