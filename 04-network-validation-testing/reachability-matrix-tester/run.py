#!/usr/bin/env python3
"""Test the committed intent matrix against the committed ACL and write results.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from reachability import evaluate_intent

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    s = result["summary"]
    lines = [
        "# Reachability Matrix Tester — Results",
        "",
        f"- Total: **{s['total']}** · pass **{s['pass']}** · "
        f"violation **{s['violation']}** · ambiguous **{s['ambiguous']}**",
        "",
        "| Intent | Expected | Verdict | Status | Reason |",
        "|---|---|---|---|---|",
    ]
    for r in result["results"]:
        reason = r["reason"] or "—"
        lines.append(f"| `{r['name']}` | {r['expected']} | {r['verdict']} | {r['status']} | {reason} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", default=str(HERE / "policy.json"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    data = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    result = evaluate_intent(data["intent"], data["acl_rules"])

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.report:
        write_report(result, out_dir / "results.md")

    print(json.dumps(result["summary"]))
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
