# MzansiBuilds

Web application for **building in public**: developers register, publish projects (stage and support needed), follow a live feed, comment, request collaboration, record milestones, and mark work complete so it appears on a **Celebration Wall**. UI theme: green, white, and black. Layout inspired by a GitHub-style project view and a Discord-style sidebar / navigation pattern.

## Requirements coverage

| Area | Implementation |
|------|----------------|
| Account | Registration, login, session auth, profile (name, bio) |
| Projects | Create / edit, stage, support needed, description |
| Feed | Paginated list with stage filter; spotlight ordering |
| Engagement | Comments; collaboration (“raise hand”) |
| Progress | Milestones with timestamps |
| Completion | Owner marks complete; project listed on Celebration Wall |
| API | JSON under `/api/v1` (same app as the HTML routes) |

## Stack

- Python 3, Flask, Flask-Login, Flask-WTF (CSRF), SQLAlchemy  
- Jinja2 templates, static CSS (no SPA build required for the shipped UI)  
- PostgreSQL in production; tests use in-memory SQLite  

## Repository layout

- `backend/` — application factory, routes, services, repositories, models, templates, `static/`  
- `frontend/` — empty placeholder with `.gitignore` only (kept so optional future client tooling does not pollute the repo)  
- `docs/` — architecture diagrams, schema reference, technical notes  
- `tests/` — pytest  
- `run.py` — local dev server  
- `Procfile` — Gunicorn entry for deployment  

## Setup

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set `SECRET_KEY` and `DATABASE_URL`. Then run:

```text
python run.py
```

Open `http://127.0.0.1:5000/`. Tests:

```text
set MZANSI_SKIP_DOTENV=1
python -m pytest -q
```

(On PowerShell: `$env:MZANSI_SKIP_DOTENV="1"`.)

## Deployment

Set the same environment variables on the host and run the command in `Procfile` (Gunicorn with `backend.app:create_app`). Serve one HTTPS origin for both pages and `/api/v1`.

## Author

Software engineering project: full-stack design, data modelling, automated tests, and deployment configuration.
