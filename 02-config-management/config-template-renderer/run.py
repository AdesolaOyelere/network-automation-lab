#!/usr/bin/env python3
"""Render an offline device configuration from a template and JSON data."""

import argparse
import json
from pathlib import Path

from template_renderer import TemplateError, render_template

HERE = Path(__file__).parent


def render_files(template_path: Path, data_path: Path) -> str:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    return render_template(template_path.read_text(encoding="utf-8"), data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=HERE / "ios_config.template")
    parser.add_argument("--data", type=Path, default=HERE / "device_data.json")
    parser.add_argument("--output", type=Path, default=HERE / "results" / "rendered_config.txt")
    args = parser.parse_args()
    try:
        rendered = render_files(args.template, args.data)
    except (OSError, json.JSONDecodeError, TemplateError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    line_count = len(rendered.splitlines())
    try:
        output_name = str(args.output.resolve().relative_to(HERE.resolve()))
    except ValueError:
        output_name = str(args.output)
    summary = {"output": output_name, "lines": line_count, "bytes": len(rendered.encode())}
    (HERE / "results" / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"rendered: {args.output}")
    print(f"lines: {line_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
