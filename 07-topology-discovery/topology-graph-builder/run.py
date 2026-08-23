#!/usr/bin/env python3
"""Analyze the committed adjacency records and write results.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from topology import analyze

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# Topology Graph Builder — Results",
        "",
        f"- Devices: **{result['n_devices']}** (from {result['n_raw_records']} raw records, "
        f"{result['n_unique_edges']} unique edges after dedup)",
        f"- Components: **{result['n_components']}**",
        f"- Articulation points (single points of failure): **{', '.join(result['articulation_points']) or 'none'}**",
        "",
        "## Components",
        "",
    ]
    for i, comp in enumerate(result["components"], 1):
        lines.append(f"{i}. {', '.join(comp)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adjacency", default=str(HERE / "adjacency.json"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    records = json.loads(Path(args.adjacency).read_text(encoding="utf-8"))
    result = analyze(records)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.report:
        write_report(result, out_dir / "results.md")

    print(f"devices: {result['n_devices']}  components: {result['n_components']}")
    print(f"articulation points: {result['articulation_points']}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
