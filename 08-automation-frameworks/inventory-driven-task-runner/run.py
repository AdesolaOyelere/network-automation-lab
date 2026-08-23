#!/usr/bin/env python3
"""Run get_version across the prod-tagged subset of the committed inventory.

Examples:
    python run.py
    python run.py --report   # also write results/results.md
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from task_runner import filter_inventory, run_task
from transport import get_version

HERE = Path(__file__).parent


def write_report(inventory_count: int, filtered_count: int, results: list[dict], path: Path) -> None:
    n_success = sum(1 for r in results if r["success"])
    lines = [
        "# Inventory-Driven Task Runner — Results",
        "",
        f"- Inventory: **{inventory_count}** devices, filtered to **{filtered_count}**",
        f"- Task succeeded on **{n_success}/{len(results)}**",
        "",
        "| Device | Success | Result | Error |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['device']} | {r['success']} | {r['result'] or '—'} | {r['error'] or '—'} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", default=str(HERE / "inventory.json"))
    ap.add_argument("--tag", default="prod", help="tag to filter the inventory by")
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--report", action="store_true", help="write results/results.md")
    args = ap.parse_args()

    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    filtered = filter_inventory(inventory, tags=[args.tag])
    results = run_task(filtered, get_version, max_workers=args.max_workers)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    payload = {"n_inventory": len(inventory), "n_filtered": len(filtered), "results": results}
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.report:
        write_report(len(inventory), len(filtered), results, out_dir / "results.md")

    n_success = sum(1 for r in results if r["success"])
    print(f"inventory={len(inventory)} filtered={len(filtered)} success={n_success}/{len(results)}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
