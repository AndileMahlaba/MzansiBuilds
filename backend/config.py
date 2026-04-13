import os
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
# Tests set MZANSI_SKIP_DOTENV so .env on disk does not override monkeypatched URLs.
if not os.environ.get("MZANSI_SKIP_DOTENV"):
    load_dotenv(_BASE / ".env")


def _rewrite_direct_supabase_to_session_pooler(url: str) -> str | None:
    """
    Direct host db.<ref>.supabase.co is often IPv6-only. Session pooler (IPv4-friendly) uses:
    postgresql://postgres.<ref>:password@aws-0-<region>.pooler.supabase.com:5432/postgres
    Set SUPABASE_POOLER_REGION (e.g. eu-west-2) from the dashboard pooler host.
    """
    region = os.environ.get("SUPABASE_POOLER_REGION", "").strip()
    if not region:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not (host.startswith("db.") and host.endswith(".supabase.co")):
        return None
    project_ref = host[3 : -len(".supabase.co")]
    if not project_ref:
        return None
    # Direct URL must use user `postgres` only; if someone mixed in `postgres.<ref>` here,
    # we still rewrite using ref from the hostname and the password from the URL.
    password = parsed.password or ""
    pooler_host = f"aws-0-{region}.pooler.supabase.com"
    user = f"postgres.{project_ref}"
    netloc = f"{quote(user, safe='.')}:{quote(password, safe='')}@{pooler_host}:5432"
    path = parsed.path or "/postgres"
    return urlunparse(("postgresql", netloc, path, "", parsed.query, ""))


def _validate_supabase_pooler_username(url: str) -> None:
    """Session pooler rejects user `postgres`; dashboard uses `postgres.<project-ref>`."""
    if not url.startswith("postgresql"):
        return
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if "pooler.supabase.com" not in host:
        return
    user = parsed.username or ""
    if user == "postgres":
        raise ValueError(
            "Invalid database user for Supabase session pooler: use postgres.<your-project-ref>, "
            "not postgres alone. Copy the full connection string from Supabase → Connect → "
            "Session pooler (it looks like postgres.xxxxx:password@aws-0-...pooler...)."
        )


def _database_uri() -> str:
    """
    SQLite when no Postgres URL is set (local dev only).

    For Supabase on IPv4: paste the **Session pooler** URI into DATABASE_SESSION_URL (Supabase
    dashboard → Connect), or set DATABASE_URL to the direct string plus SUPABASE_POOLER_REGION.
    Direct host db.*.supabase.co is often IPv6-only and fails DNS on IPv4 networks.
    """
    # Full session-pooler URI from dashboard (recommended — no region variable needed).
    url = os.environ.get("DATABASE_SESSION_URL", "").strip()
    if not url:
        url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    rewritten = _rewrite_direct_supabase_to_session_pooler(url)
    if rewritten:
        url = rewritten
    if url.startswith("postgresql"):
        if "sslmode=" not in url and "ssl=" not in url:
            url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
        _validate_supabase_pooler_username(url)
    if url:
        return url
    return f"sqlite:///{_BASE / 'instance' / 'mzansi.db'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-in-production")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in (
        "1",
        "true",
        "yes",
    )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
