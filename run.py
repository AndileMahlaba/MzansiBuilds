"""
Run from repo root:  python run.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.app import create_app

if __name__ == "__main__":
    application = create_app()
    print("MzansiBuilds -> http://127.0.0.1:5000/  (SSR + /api/v1)")
    application.run(host="127.0.0.1", port=5000, debug=True)
