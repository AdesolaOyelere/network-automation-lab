#!/usr/bin/env python3
"""Detect flapping interfaces and report uptime over the committed event log.

Examples:
    python run.py
    python run.py --window 60 --threshold 4 --report
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from interface_flap import DEFAULT_THRESHOLD, DEFAULT_WINDOW_SECONDS, compute_uptime, detect_flapping

HERE = Path(__file__).parent


def write_report(flap_result: dict, uptime_result: dict, path: Path) -> None:
    uptime_by_key = {(u["device"], u["interface"]): u for u in uptime_result["interfaces"]}
    lines = [
        "# Interface Flap Detector — Results",
        "",
        f"- Window: **{flap_result['window_seconds']}s**, threshold: **{flap_result['threshold']} transitions**",
        f"- Observed period: **{uptime_result['observed_start']}** to **{uptime_result['observed_end']}**",
        "",
        "| Device | Interface | Transitions | Max in window | Flapping | Uptime |",
        "|---|---|---|---|---|---|",
    ]
    for i in flap_result["interfaces"]:
        u = uptime_by_key[(i["device"], i["interface"])]
        lines.append(
            f"| {i['device']} | {i['interface']} | {i['n_transitions']} | "
            f"{i['max_transitions_in_window']} | {i['flapping']} | {u['uptime_pct']:.2%} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", default=str(HERE / "events.json"))
    ap.add_argument("--window", type=int, default=DEFAULT_WINDOW_SECONDS)
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    events = json.loads(Path(args.events).read_text(encoding="utf-8"))
    flap_result = detect_flapping(events, window_seconds=args.window, threshold=args.threshold)
    uptime_result = compute_uptime(events)
    combined = {"flapping": flap_result, "uptime": uptime_result}

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")
    if args.report:
        write_report(flap_result, uptime_result, out_dir / "results.md")

    n_flapping = sum(1 for i in flap_result["interfaces"] if i["flapping"])
    print(f"{len(flap_result['interfaces'])} interfaces, {n_flapping} flapping")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
