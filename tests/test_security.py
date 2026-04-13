from backend.utils.security import safe_redirect_path


def test_safe_redirect_path_accepts_relative():
    assert safe_redirect_path("/feed") == "/feed"
    assert safe_redirect_path("/projects/1") == "/projects/1"


def test_safe_redirect_path_rejects_external_and_protocol_relative():
    assert safe_redirect_path("//evil.example/phish") is None
    assert safe_redirect_path("https://evil.example") is None
    assert safe_redirect_path(None) is None
    assert safe_redirect_path("") is None


def test_safe_redirect_path_rejects_newlines():
    assert safe_redirect_path("/feed\n//evil") is None
