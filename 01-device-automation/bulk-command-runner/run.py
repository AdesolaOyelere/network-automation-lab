#!/usr/bin/env python3
"""Run the committed fleet's command and report baseline drift.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from bulk_runner import compare_to_baseline, run_bulk
from transport import MockTransport

HERE = Path(__file__).parent


def write_report(summary: dict, path: Path) -> None:
    lines = [
        "# Bulk Command Runner — Results",
        "",
        f"- Baseline version: **{summary['baseline']}**",
        f"- Devices: **{summary['n_devices']}** "
        f"({summary['n_matched']} matched, {summary['n_drifted']} drifted, {summary['n_unreachable']} unreachable)",
        "",
    ]
    if summary["drifted"]:
        lines += ["## Drifted", ""]
        for d in summary["drifted"]:
            lines.append(f"- `{d['device']}`: {d['extracted']}")
    if summary["unreachable"]:
        lines += ["", "## Unreachable", ""]
        for d in summary["unreachable"]:
            lines.append(f"- `{d}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fleet", default=str(HERE / "fleet.json"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    data = json.loads(Path(args.fleet).read_text(encoding="utf-8"))
    transport = MockTransport(data["fixtures"], unreachable=set(data["unreachable"]))
    results = run_bulk(data["devices"], data["command"], transport)
    summary = compare_to_baseline(results, data["baseline_version"])

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.report:
        write_report(summary, out_dir / "results.md")

    print(f"baseline: {summary['baseline']}")
    print(
        f"{summary['n_devices']} devices: {summary['n_matched']} matched, "
        f"{summary['n_drifted']} drifted, {summary['n_unreachable']} unreachable"
    )
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
