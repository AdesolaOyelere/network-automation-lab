#!/usr/bin/env python3
"""Check the committed intents against the committed device config.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from intent_checker import parse_config, run_intents

HERE = Path(__file__).parent


def write_report(results: list[dict], path: Path) -> None:
    n_pass = sum(1 for r in results if r["passed"])
    lines = [
        "# Config Intent Checker — Results",
        "",
        f"- Intents checked: **{len(results)}**",
        f"- Passed: **{n_pass}**",
        "",
        "| Intent | Passed | Reason |",
        "|---|---|---|",
    ]
    for r in results:
        intent_desc = json.dumps(r["intent"])
        reason = r["reason"] or "—"
        lines.append(f"| `{intent_desc}` | {r['passed']} | {reason} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(HERE / "device_config.txt"))
    ap.add_argument("--intents", default=str(HERE / "intents.json"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    blocks = parse_config(Path(args.config).read_text(encoding="utf-8"))
    intents = json.loads(Path(args.intents).read_text(encoding="utf-8"))
    results = run_intents(intents, blocks)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if args.report:
        write_report(results, out_dir / "results.md")

    n_pass = sum(1 for r in results if r["passed"])
    print(f"{n_pass}/{len(results)} intents passed")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
