#!/usr/bin/env python3
"""Compare mock running configuration with the committed golden baseline."""

import argparse
import json
import os
from pathlib import Path

from drift_detector import audit_device
from transport import MockConfigTransport

HERE = Path(__file__).parent


def write_report(result: dict, path: Path) -> None:
    lines = [
        "# Golden Configuration Drift Results",
        "",
        f"- Device: **{result['hostname']}**",
        f"- In sync: **{result['in_sync']}**",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {kind} | {count} |" for kind, count in result["summary"].items())
    for kind in ("changed", "missing", "unexpected"):
        lines.extend(["", f"## {kind.title()}", ""])
        if not result[kind]:
            lines.append("None.")
        for item in result[kind]:
            if kind == "changed":
                lines.append(f"- `{item['context']}`: `{item['expected']}` → `{item['actual']}`")
            else:
                lines.append(f"- `{item['context']}`: `{item['command']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default=str(HERE / "mock_device.json"))
    parser.add_argument("--golden", default=str(HERE / "golden_config.txt"))
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    result = audit_device(MockConfigTransport(args.fixture), args.golden)
    output_dir = HERE / "results"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.report:
        write_report(result, output_dir / "results.md")
    print(f"device: {result['hostname']}")
    print(f"in sync: {result['in_sync']}")
    for kind, count in result["summary"].items():
        print(f"  {kind:10s} {count}")
    return 0


if __name__ == "__main__":
    os.chdir(HERE)
    raise SystemExit(main())
