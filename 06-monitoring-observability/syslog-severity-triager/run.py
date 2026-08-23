#!/usr/bin/env python3
"""Triage the committed sample syslog and write results.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from syslog_triage import triage

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# Syslog Severity Triager — Results",
        "",
        f"- Raw lines: **{result['n_raw_lines']}** ({result['n_parsed']} parsed, "
        f"{result['n_parse_errors']} parse errors)",
        f"- Aggregated entries: **{result['n_aggregated_entries']}**",
        f"- Buckets: critical={result['buckets']['critical']} "
        f"warning={result['buckets']['warning']} info={result['buckets']['info']}",
        "",
        "## Top entries by count",
        "",
        "| Host | Facility-Sev-Mnemonic | Count | First seen | Last seen |",
        "|---|---|---|---|---|",
    ]
    for e in result["top_entries"]:
        tag = f"{e['facility']}-{e['severity']}-{e['mnemonic']}"
        lines.append(f"| {e['hostname']} | {tag} | {e['count']} | {e['first_seen']} | {e['last_seen']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", default=str(HERE / "syslog_sample.log"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    lines = Path(args.log).read_text(encoding="utf-8").splitlines()
    result = triage(lines)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.report:
        write_report(result, out_dir / "results.md")

    print(f"raw={result['n_raw_lines']} parsed={result['n_parsed']} errors={result['n_parse_errors']}")
    print(f"aggregated entries: {result['n_aggregated_entries']}")
    print(f"buckets: {result['buckets']}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
