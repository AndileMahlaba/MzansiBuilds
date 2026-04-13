def test_stats_api(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    data = r.get_json()
    assert "developers" in data
    assert "stage_counts" in data


def test_home_shows_landing(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Ship in the open" in r.data
    assert b"MZANSI_TEMPLATE_V2" in r.data


def test_ssr_celebration_and_system(client):
    r = client.get("/celebration")
    assert r.status_code == 200
    assert b"Celebration wall" in r.data
    r2 = client.get("/system")
    assert r2.status_code == 200
    assert b"Command center" in r2.data


def test_feed_redirects_to_ssr(client):
    r = client.get("/feed", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("Location", "").endswith("/ssr/feed")


def test_legacy_static_css_path_serves_theme(client):
    """Old HTML linked /static/css/main.css; file delegates to mzansi_ssr.css."""
    r = client.get("/static/css/main.css")
    assert r.status_code == 200
    assert r.mimetype == "text/css"
    assert b"mzansi_ssr.css" in r.data
    r2 = client.get("/static/css/mzansi_ssr.css")
    assert r2.status_code == 200
    assert b"--green" in r2.data


def test_ping(client):
    r = client.get("/api/v1/ping")
    assert r.status_code == 200
    assert r.get_json().get("ok") is True
