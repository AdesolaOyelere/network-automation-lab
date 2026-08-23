#!/usr/bin/env python3
"""Look up one MAC address or a batch from a file.

Examples:
    python run.py --mac 00:0C:29:3A:7B:11
    python run.py --batch sample_macs.txt --report
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from vendors import lookup_batch, lookup_vendor

HERE = Path(__file__).parent


def write_report(results: list[dict], path: Path) -> None:
    lines = ["# MAC Vendor Lookup — Results", "", "| Input | OUI | Vendor / Error |", "|---|---|---|"]
    for r in results:
        if r["error"]:
            lines.append(f"| `{r['input']}` | — | error: {r['error']} |")
        else:
            lines.append(f"| `{r['input']}` | {r['oui']} | {r['vendor']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mac", help="look up a single MAC address")
    ap.add_argument("--batch", default=str(HERE / "sample_macs.txt"), help="file of MACs, one per line")
    ap.add_argument("--report", action="store_true", help="write results/results.md (batch mode)")
    args = ap.parse_args()

    if args.mac:
        result = lookup_vendor(args.mac)
        print(json.dumps(result, indent=2))
        return 0

    macs = [line.strip() for line in Path(args.batch).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = lookup_batch(macs)

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if args.report:
        write_report(results, out_dir / "results.md")

    n_ok = sum(1 for r in results if not r["error"])
    n_known = sum(1 for r in results if r["vendor"] and r["vendor"] != "Unknown vendor")
    print(f"{len(results)} entries: {n_ok} valid, {n_known} matched a known vendor")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
