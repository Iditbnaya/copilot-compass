from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from flask import render_template

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
sys.path.insert(0, str(ROOT))

from app import BEST_PRACTICES, FEATURES, app, get_updates


def build() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    shutil.copytree(ROOT / "static", OUTPUT / "static")

    updates = get_updates(force=True)
    payload = {
        "items": updates["items"],
        "updated_at": updates["updated_at"],
        "stale": bool(updates["errors"]),
        "source_errors": updates["errors"],
    }
    (OUTPUT / "updates.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with app.app_context():
        page = render_template(
            "index.html",
            features=FEATURES,
            best_practices=BEST_PRACTICES,
            updates_endpoint="updates.json",
        )
    (OUTPUT / "index.html").write_text(page, encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()


if __name__ == "__main__":
    build()
