# Deployment, email, demo data, and hosting

## Is it ready to ship?

Reasonable for a **first deploy** if you:

- Set a strong **`SECRET_KEY`**, **`DATABASE_URL`** (PostgreSQL), and **`SESSION_COOKIE_SECURE=true`** behind HTTPS.
- Configure **SMTP** (or turn off **`EMAIL_VERIFICATION_REQUIRED`** until mail works).
- Run **`pytest`** in CI and smoke-test register, feed, project page, celebration.

This stack is a **public build journal** plus links to GitHub/GitLab, milestones, build log, and comments. It does not host git objects; that stays on your forge until you add a future GitHub API integration.

## Email not sending (troubleshooting)

Mail sends only if **`MAIL_SERVER`** and **`MAIL_USERNAME`** are set (see `.env.example`).

Typical **Gmail**:

1. Use an **App Password** (Google Account → Security → 2-Step Verification → App passwords), not your normal login password.
2. **Port 587** + **`MAIL_USE_TLS=true`** (default), or **port 465** with **`MAIL_USE_TLS=false`** and **`MAIL_USE_SSL=true`**.
3. **`MAIL_DEFAULT_SENDER`** should match the mailbox you authenticate as (e.g. your Gmail address).

If sending still fails, check the **error returned** from SMTP (auth vs connection). The app logs failures when SMTP is configured but the server rejects the message.

## Demo / dummy data (local or staging)

Populate rich sample users, projects, milestones, build logs, comments, collaboration requests, and completed projects:

```bash
python scripts/seed_mzansi_demo.py
```

If you use **PostgreSQL / Supabase** in `.env`, the script will refuse until you opt in (one line per session):

```powershell
$env:MZANSI_ALLOW_DEMO_SEED = "1"
python scripts/seed_mzansi_demo.py
```

- Default: only runs on **local SQLite** (`instance/mzansi.db`) or when **`MZANSI_ALLOW_DEMO_SEED=1`** (required for Postgres or other URLs).
- Log in as **`andile@seed.example.com`** (and others `*@seed.example.com`) with password **`DemoSeed123!`**.

Remove all demo rows:

```bash
set MZANSI_CONFIRM_CLEAR_DEMO=1   # PowerShell: $env:MZANSI_CONFIRM_CLEAR_DEMO="1"
python scripts/clear_mzansi_demo.py
```

## Hosting: “free” and “always up”

Truthfully, **always-on + globally reliable + $0 forever** is rare. Products change tiers often; verify current docs before you commit.

| Option | Rough fit | Notes |
|--------|-----------|--------|
| **Vercel** | Great for your **portfolio** (static/frontend) | Not a traditional home for a **long-lived Flask + DB** app; people usually pair Vercel with a separate API host or serverless with limits. |
| **Render (free)** | Easy Flask + Postgres | **Cold start / sleep** on idle is a common pain (what you want to avoid). |
| **Koyeb** | Small container, often cited as **no sleep** on free nano | Good for always-on **small** APIs; check current limits. |
| **Fly.io** | Containers close to users | **Free tier has changed**; many projects now budget a few **$/month** for a tiny VM. Still often cheaper than surprise usage bills. |
| **Railway** | Very fast to deploy | **Credit-based**; not “free forever” in the old sense—watch usage. |
| **Oracle Cloud “Always Free”** | **VMs that stay up** | More setup (you manage the VM), but strong if you want **no platform sleep** on a budget. |
| **Supabase** | **Postgres** for this app | Host the **database** there; run the **Flask web** process on Fly/Koyeb/your VM. |

**Practical recipe** many teams use: **Supabase Postgres** + **one small always-on host** (paid coffee-money tier if needed) + **Cloudflare** in front for DNS/SSL. That avoids Render-style sleep on the app **if** the host does not spin down.

## Process manager

The repo includes a **`Procfile`** for **`gunicorn`**:

```bash
web: gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --factory backend.app:create_app
```

Set **`PORT`** from the platform and point **`DATABASE_URL`** at Postgres (session pooler URI for Supabase if you use it).
