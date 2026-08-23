#!/usr/bin/env python3
"""Scaffold a new project folder that matches the repo's shape.

Usage:
    python scripts/new_project.py 02-config-management golden-config-diff "Golden Config Diff" "One line summary"

Creates <category>/<slug>/ with README.md, meta.json, and a tests/ folder.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "shared" / "README_TEMPLATE.md"


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2
    category, slug, title = argv[0], argv[1], argv[2]
    summary = argv[3] if len(argv) > 3 else ""

    dest = ROOT / category / slug
    if dest.exists():
        print(f"already exists: {dest}", file=sys.stderr)
        return 1
    (dest / "tests").mkdir(parents=True)
    (dest / "results").mkdir()

    readme = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else "# " + title
    readme = readme.replace("<Project Title>", title).replace("<category>", category)
    (dest / "README.md").write_text(readme, encoding="utf-8")

    meta = {
        "title": title,
        "slug": slug,
        "category": category,
        "status": "in-progress",
        "skills": [],
        "summary": summary,
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (dest / "tests" / "__init__.py").write_text("", encoding="utf-8")

    print(f"created {dest.relative_to(ROOT).as_posix()}")
    print("next: fill README.md, add code + tests, then run scripts/gen_index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
