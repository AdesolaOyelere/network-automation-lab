#!/usr/bin/env python3
"""Audit ACLs from the deterministic mock device and save results."""

import argparse
import json
import os
from pathlib import Path

from acl_auditor import audit_device
from transport import MockDeviceTransport

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# ACL Rule Audit Results",
        "",
        f"- Device: **{result['hostname']}**",
        f"- ACLs/rules: **{result['acl_count']} / {result['rule_count']}**",
        f"- Findings: **{result['finding_count']}**",
        "",
        "| ACL | Seq | Type | Severity | Detail |",
        "|---|---:|---|---|---|",
    ]
    for finding in result["findings"]:
        lines.append(
            f"| {finding['acl']} | {finding['sequence']} | {finding['type']} | "
            f"{finding['severity']} | {finding['detail']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default=str(HERE / "mock_device.json"))
    parser.add_argument("--unused-after-days", type=int, default=60)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    result = audit_device(MockDeviceTransport(args.fixture), args.unused_after_days)
    output_dir = HERE / "results"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.report:
        write_report(result, output_dir / "results.md")
    print(f"device: {result['hostname']}")
    print(f"acls: {result['acl_count']}  rules: {result['rule_count']}")
    print(f"findings: {result['finding_count']}")
    for kind, count in result["findings_by_type"].items():
        print(f"  {kind:16s} {count}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
