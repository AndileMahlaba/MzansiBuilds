from __future__ import annotations


def safe_redirect_path(url: str | None) -> str | None:
    """
    Only allow same-site relative paths after login. Rejects scheme-relative URLs like
    //evil.example which still start with a slash in a naive check.
    """
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u.startswith("/") or u.startswith("//"):
        return None
    if "\n" in u or "\r" in u:
        return None
    return u
