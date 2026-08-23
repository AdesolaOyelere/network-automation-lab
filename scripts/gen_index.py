#!/usr/bin/env python3
"""Regenerate the project index in README.md and PROJECTS.md from meta.json files.

Each project lives at <category>/<slug>/meta.json with this shape:

    {
      "title": "Golden Config Drift Detector",
      "slug": "golden-config-drift-detector",
      "category": "02-config-management",
      "status": "done",            # done | in-progress | planned
      "skills": ["config-management", "diffing"],
      "summary": "One line."
    }

Run from the repo root:  python scripts/gen_index.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STATUS_ICON = {"done": "✅", "in-progress": "🔨", "planned": "⬜"}


def find_metas() -> list[dict]:
    metas: list[dict] = []
    for meta_path in sorted(ROOT.glob("[0-9][0-9]-*/*/meta.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"skip (bad json): {meta_path}: {exc}", file=sys.stderr)
            continue
        data["_dir"] = meta_path.parent.relative_to(ROOT).as_posix()
        metas.append(data)
    return metas


def build_table(metas: list[dict]) -> str:
    if not metas:
        return "_No projects with meta.json yet._"
    lines = ["| Project | Category | Status | Summary |", "|---|---|---|---|"]
    for m in sorted(metas, key=lambda x: (x.get("category", ""), x.get("slug", ""))):
        icon = STATUS_ICON.get(m.get("status", "planned"), "⬜")
        title = m.get("title", m.get("slug", "?"))
        link = f"[{title}]({m['_dir']}/)"
        cat = m.get("category", "")
        summary = m.get("summary", "").replace("|", "\\|")
        lines.append(f"| {link} | `{cat}` | {icon} | {summary} |")
    return "\n".join(lines)


def build_summary(metas: list[dict]) -> str:
    total = len(metas)
    done = sum(1 for m in metas if m.get("status") == "done")
    prog = sum(1 for m in metas if m.get("status") == "in-progress")
    planned = total - done - prog
    return (
        f"**{total}** projects tracked · "
        f"✅ {done} done · 🔨 {prog} in progress · ⬜ {planned} planned"
    )


def replace_between(text: str, marker: str, payload: str) -> str:
    start, end = f"<!-- {marker}:START -->", f"<!-- {marker}:END -->"
    if start not in text or end not in text:
        print(f"marker {marker} not found; skipping", file=sys.stderr)
        return text
    head = text.split(start)[0]
    tail = text.split(end)[1]
    return f"{head}{start}\n{payload}\n{end}{tail}"


def main() -> int:
    metas = find_metas()
    table = build_table(metas)
    summary = build_summary(metas)

    readme = ROOT / "README.md"
    projects = ROOT / "PROJECTS.md"

    r = readme.read_text(encoding="utf-8")
    r = replace_between(r, "INDEX:SUMMARY", summary)
    readme.write_text(r, encoding="utf-8")

    p = projects.read_text(encoding="utf-8")
    p = replace_between(p, "INDEX:TABLE", table)
    projects.write_text(p, encoding="utf-8")

    print(f"indexed {len(metas)} project(s)")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
