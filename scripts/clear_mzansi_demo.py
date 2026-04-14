#!/usr/bin/env python3
"""Remove users (and cascaded data) created by seed_mzansi_demo.py (@seed.example.com)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.extensions import db
from backend.models.user import User

SEED_DOMAIN = "seed.example.com"


def run() -> None:
    app = create_app()
    with app.app_context():
        n = (
            db.session.query(User)
            .filter(User.email.like(f"%@{SEED_DOMAIN}"))
            .delete(synchronize_session=False)
        )
        db.session.commit()
        print(f"Removed {n} demo user(s) and related rows (cascade).")


if __name__ == "__main__":
    if os.environ.get("MZANSI_CONFIRM_CLEAR_DEMO") != "1":
        print(
            "Set MZANSI_CONFIRM_CLEAR_DEMO=1 to confirm deletion of *@seed.example.com users.",
            file=sys.stderr,
        )
        sys.exit(1)
    run()
