#!/usr/bin/env python3
"""Run the VLSM allocator against the committed requirements and write results.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from subnet_calc import allocate_vlsm

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# Subnet Calculator — VLSM Allocation Results",
        "",
        f"- Supernet: **{result['supernet']}**",
        f"- All requirements fit: **{result['fits']}**",
        "",
        "| Name | CIDR | Hosts requested | Hosts available |",
        "|---|---|---|---|",
    ]
    for a in result["allocations"]:
        lines.append(f"| `{a['name']}` | {a['cidr']} | {a['hosts_requested']} | {a['hosts_available']} |")
    if result["unallocated"]:
        lines += ["", "**Unallocated:**", ""]
        for u in result["unallocated"]:
            lines.append(f"- `{u['name']}` ({u['hosts']} hosts): {u['reason']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--requirements", default=str(HERE / "requirements.json"))
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    data = json.loads(Path(args.requirements).read_text(encoding="utf-8"))
    result = allocate_vlsm(data["supernet"], data["requirements"])

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if args.report:
        write_report(result, out_dir / "results.md")

    print(f"supernet: {result['supernet']}")
    print(f"fits: {result['fits']}")
    for a in result["allocations"]:
        print(
            f"  {a['name']:12s} {a['cidr']:18s} "
            f"requested={a['hosts_requested']:<4d} available={a['hosts_available']}"
        )
    return 0


if __name__ == "__main__":
    os.chdir(HERE)  # so relative default paths resolve when invoked from anywhere
    raise SystemExit(main())
