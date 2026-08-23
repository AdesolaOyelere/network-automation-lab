#!/usr/bin/env python3
"""Parse the committed poll set and detect MAC flapping.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from mac_table import detect_flapping, parse_mac_table

HERE = Path(__file__).parent


def write_report(n_entries: int, flaps: list[dict], path: Path) -> None:
    lines = [
        "# MAC Address Table Analyzer — Results",
        "",
        f"- Entries parsed: **{n_entries}**",
        f"- Flaps detected: **{len(flaps)}**",
        "",
        "| Switch | VLAN | MAC | From port | To port | Delta (s) |",
        "|---|---|---|---|---|---|",
    ]
    for f in flaps:
        lines.append(
            f"| {f['switch']} | {f['vlan']} | {f['mac']} | {f['from_port']} | "
            f"{f['to_port']} | {f['delta_seconds']:.0f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--polls", default=str(HERE / "polls.json"))
    ap.add_argument("--window-seconds", type=int, default=60)
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    polls = json.loads(Path(args.polls).read_text(encoding="utf-8"))
    entries = []
    for p in polls:
        entries.extend(parse_mac_table(p["text"], p["switch"], p["timestamp"]))
    flaps = detect_flapping(entries, window_seconds=args.window_seconds)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    payload = {"n_entries": len(entries), "n_flaps": len(flaps), "flaps": flaps}
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.report:
        write_report(len(entries), flaps, out_dir / "results.md")

    print(f"entries={len(entries)} flaps={len(flaps)}")
    for f in flaps:
        print(f"  {f['switch']} {f['mac']} {f['from_port']} -> {f['to_port']} in {f['delta_seconds']:.0f}s")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
