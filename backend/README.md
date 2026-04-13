# Backend

| Area | Contents |
|------|----------|
| `routes/` | JSON API under `/api/v1`; server-rendered HTML routes; static assets |
| `services/` | Auth, projects, feed, and related rules |
| `repositories/` | Data access (SQLAlchemy) |
| `models/` | ORM entities |
| `algorithms/` | Feed ordering and layout helpers |
| `app.py` | Application factory `create_app()` (used by `run.py` and Gunicorn) |

Configuration lives in **`config.py`** (reads `.env` from the repo root). The database is **PostgreSQL**, configured via your environment variables.
