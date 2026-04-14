#!/usr/bin/env python3
"""
Load realistic demo data so you can click through the whole product (feed, projects, logs, celebration).

Safety:
  - Only runs against SQLite (local instance/mzansi.db or :memory:) OR when MZANSI_ALLOW_DEMO_SEED=1 is set.
  - All demo users use emails ending in @seed.example.com (easy to remove with clear_mzansi_demo.py).

Usage (repo root):
  python scripts/seed_mzansi_demo.py
  python scripts/clear_mzansi_demo.py

Demo login (all accounts):
  Password:  DemoSeed123!
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.constants import COLLAB_PENDING, PROJECT_ACTIVE, PROJECT_COMPLETED
from backend.extensions import db
from backend.models.collaboration import CollaborationRequest
from backend.models.comment import Comment
from backend.models.milestone import Milestone
from backend.models.project import Project
from backend.models.project_build_log import ProjectBuildLog
from backend.models.user import User

SEED_DOMAIN = "seed.example.com"
DEMO_PASSWORD = "DemoSeed123!"


def _allow_seed(uri: str) -> bool:
    if os.environ.get("MZANSI_ALLOW_DEMO_SEED", "").strip() in ("1", "true", "yes"):
        return True
    u = (uri or "").lower().replace("\\", "/")
    if "sqlite" in u and "memory" not in u:
        return True
    if u.endswith("mzansi.db") or "/instance/" in u:
        return True
    return False


def _refuse_seed_message(uri: str) -> str:
    u = (uri or "").lower()
    db = "PostgreSQL or other remote DB" if "postgresql" in u else "this database URL"
    return (
        f"Refusing to seed: your DATABASE_URL points to {db}.\n\n"
        "To load demo data into the database you are using now, run (PowerShell):\n"
        '  $env:MZANSI_ALLOW_DEMO_SEED = "1"\n'
        "  python scripts/seed_mzansi_demo.py\n\n"
        "Or switch to local SQLite for dev only: set DATABASE_URL to\n"
        "  sqlite:///<path-to-repo>/instance/mzansi.db\n"
        "then run this script again without the env var."
    )


def _email(local: str) -> str:
    return f"{local}@{SEED_DOMAIN}"


def run() -> None:
    app = create_app()
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not _allow_seed(uri):
        print(_refuse_seed_message(uri), file=sys.stderr)
        sys.exit(1)

    with app.app_context():
        if db.session.query(User).filter(User.email.like(f"%@{SEED_DOMAIN}")).first():
            print("Demo data already present. Run: python scripts/clear_mzansi_demo.py")
            sys.exit(0)

        users_spec = [
            ("andile", "Andile Mahlaba", "Full-stack builder in Cape Town. Shipping in public."),
            ("nomsa", "Nomsa K.", "Mobile money APIs and UX. Open to pair on Kotlin."),
            ("sipho", "Sipho Dlamini", "Data + maps. Learning Rust on the side."),
            ("thabo", "Thabo M.", "DevOps and small SaaS. Coffee-powered."),
            ("lindi", "Lindiwe N.", "Design systems and accessible UI."),
            ("kamo", "Kamo P.", "Backend + Postgres. Here for code review."),
            ("neo", "Neo R.", "Student dev. Building a township delivery tracker."),
            ("zola", "Zola T.", "Game tools and scripting. Python + Godot."),
        ]

        users: list[User] = []
        for local, name, bio in users_spec:
            u = User(
                name=name,
                email=_email(local),
                bio=bio,
                profile_public=True,
                email_verified=True,
            )
            u.set_password(DEMO_PASSWORD)
            db.session.add(u)
            users.append(u)
        db.session.flush()

        projects_data: list[tuple[User, str, str, str, str, str, str, str]] = [
            (
                users[0],
                "Township delivery tracker",
                "Route optimisation MVP for spaza deliveries. Postgres + maps API.",
                "development",
                "Mobile testers in Soweto",
                "https://github.com/octocat/Hello-World",
                "https://example.com",
            ),
            (
                users[1],
                "Stokvel ledger API",
                "Transparent rotating savings ledger with SMS receipts.",
                "testing",
                "Security review",
                "https://github.com/octocat/Hello-World",
                "",
            ),
            (
                users[2],
                "Load-shedding notifier",
                "Push alerts when Eskom stage changes. Scraping + resilient cache.",
                "planning",
                "Design partner",
                "",
                "",
            ),
            (
                users[3],
                "Mzansi skills graph",
                "Graph of who builds what, to match collaborators.",
                "idea",
                "Graph DB advice",
                "https://github.com/octocat/Hello-World",
                "",
            ),
            (
                users[4],
                "Accessible form kit",
                "Reusable form primitives with ZA locale and screen-reader testing.",
                "development",
                "Accessibility audit",
                "https://github.com/octocat/Hello-World",
                "https://example.com",
            ),
            (
                users[5],
                "Webhook bridge",
                "Normalize Stripe + PayFast webhooks into one queue.",
                "testing",
                "Staging environment access",
                "https://github.com/octocat/Hello-World",
                "",
            ),
            (
                users[6],
                "Study buddy bot",
                "WhatsApp reminders for matric study blocks. Twilio sandbox.",
                "idea",
                "Conversation copywriter",
                "",
                "",
            ),
            (
                users[7],
                "Sprite pipeline",
                "CLI to pack sprites for 2D jam games.",
                "planning",
                "Pixel artist",
                "https://github.com/octocat/Hello-World",
                "",
            ),
        ]

        active_projects: list[Project] = []
        for owner, title, desc, stage, support, repo, demo in projects_data:
            p = Project(
                user_id=owner.id,
                title=title,
                description=desc,
                stage=stage,
                support_needed=support,
                repo_url=repo,
                demo_url=demo,
                status=PROJECT_ACTIVE,
            )
            db.session.add(p)
            active_projects.append(p)
        db.session.flush()

        # Completed (celebration wall)
        completed_projects: list[Project] = []
        done = [
            (
                users[0],
                "Portfolio v1 shipped",
                "First public portfolio with case studies.",
                "development",
                PROJECT_COMPLETED,
            ),
            (
                users[3],
                "CLI dotfile sync",
                "Tiny Python CLI to symlink dotfiles. Done and archived.",
                "development",
                PROJECT_COMPLETED,
            ),
            (
                users[4],
                "Colour token pack",
                "Design tokens for green palette experiments.",
                "testing",
                PROJECT_COMPLETED,
            ),
        ]
        for owner, title, desc, stage, status in done:
            p = Project(
                user_id=owner.id,
                title=title,
                description=desc,
                stage=stage,
                support_needed="",
                repo_url="https://github.com/octocat/Hello-World",
                demo_url="",
                status=status,
            )
            db.session.add(p)
            completed_projects.append(p)
        db.session.flush()

        # Milestones (first few active projects)
        for p in active_projects[:5]:
            m1 = Milestone(
                project_id=p.id,
                title="Scaffold repo + CI",
                description="Lint, test, deploy hook.",
                achieved_at=date.today() - timedelta(days=14),
            )
            m2 = Milestone(
                project_id=p.id,
                title="User-visible slice",
                description="First screen people can try.",
                achieved_at=date.today() - timedelta(days=3),
            )
            db.session.add_all([m1, m2])

        # Build logs
        bl_titles = [
            ("Shipped dark mode", "Toggle + tokens; still polishing contrast."),
            ("Weekend spike: maps SDK", "Proof of route drawing. Throwing away if perf bad."),
        ]
        for p in active_projects[:4]:
            owner = db.session.get(User, p.user_id)
            if not owner:
                continue
            for title, body in bl_titles:
                db.session.add(
                    ProjectBuildLog(
                        project_id=p.id,
                        user_id=owner.id,
                        title=title,
                        body=body,
                        created_at=datetime.now(timezone.utc) - timedelta(days=1),
                    )
                )

        # Comments (cross-team)
        c1 = Comment(
            project_id=active_projects[0].id,
            user_id=users[5].id,
            content="Happy to review the API contract when you have OpenAPI draft.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5),
        )
        c2 = Comment(
            project_id=active_projects[1].id,
            user_id=users[0].id,
            content="SMS receipt flow is clever. Consider idempotency keys on webhook.",
            created_at=datetime.now(timezone.utc) - timedelta(hours=12),
        )
        c3 = Comment(
            project_id=active_projects[2].id,
            user_id=users[4].id,
            content="For scraping resilience, backoff + jitter saved us on a similar project.",
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.session.add_all([c1, c2, c3])

        # Collaboration request
        cr = CollaborationRequest(
            project_id=active_projects[0].id,
            requester_id=users[2].id,
            message="I have mapping experience—can help with geocoding edge cases.",
            status=COLLAB_PENDING,
        )
        db.session.add(cr)

        db.session.commit()

        print("Demo data loaded.")
        print(f"  All passwords: {DEMO_PASSWORD}")
        print(f"  Emails: *@{SEED_DOMAIN} (e.g. {_email('andile')})")
        print("  Remove later: python scripts/clear_mzansi_demo.py")


if __name__ == "__main__":
    run()
