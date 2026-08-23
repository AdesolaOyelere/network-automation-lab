#!/usr/bin/env python3
"""Analyze the committed routing table dump and write results.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from route_analyzer import (
    determine_installed_routes,
    flag_high_metric_routes,
    has_default_route,
    parse_routing_table,
)

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# Routing Table Analyzer — Results",
        "",
        f"- Routes parsed: **{result['n_routes']}**",
        f"- Default route present: **{result['has_default_route']}**",
        f"- Not-installed candidates: **{len(result['not_installed'])}**",
        f"- Metric outliers flagged: **{len(result['flagged_high_metric'])}**",
        "",
    ]
    if result["not_installed"]:
        lines += ["## Not installed", ""]
        for n in result["not_installed"]:
            r = n["route"]
            lines.append(f"- `{r['network']}/{r['prefix_len']}` ({r['protocol']}): {n['reason']}")
    if result["flagged_high_metric"]:
        lines += ["", "## High-metric outliers", ""]
        for f in result["flagged_high_metric"]:
            lines.append(
                f"- `{f['network']}/{f['prefix_len']}` ({f['protocol']}): metric {f['metric']} "
                f"vs protocol median {f['protocol_median_metric']}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", default=str(HERE / "routing_table.txt"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    text = Path(args.table).read_text(encoding="utf-8")
    routes = parse_routing_table(text)
    installed_result = determine_installed_routes(routes)
    result = {
        "n_routes": len(routes),
        "has_default_route": has_default_route(routes),
        "not_installed": installed_result["not_installed"],
        "flagged_high_metric": flag_high_metric_routes(routes),
    }

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.report:
        write_report(result, out_dir / "results.md")

    print(f"routes parsed: {result['n_routes']}")
    print(f"has default route: {result['has_default_route']}")
    print(f"not-installed candidates: {len(result['not_installed'])}")
    print(f"metric outliers: {len(result['flagged_high_metric'])}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
