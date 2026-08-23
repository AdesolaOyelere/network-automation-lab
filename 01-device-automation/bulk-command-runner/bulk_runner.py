"""Run one command across a device fleet and extract a field from each reply.

The flagship use case is "which switches are NOT on the expected image": run
`show version` across the fleet, regex out the version token from each
device's raw output, and diff every device against a declared baseline. A
device that's unreachable is reported as its own failure entry, not silently
dropped from the summary — a bulk report that quietly loses unreachable
devices is worse than useless for exactly the audit it's meant to support.
"""
from __future__ import annotations

import re

from transport import ConnectionError, MockTransport

VERSION_RE = re.compile(r"Version\s+([^\s,]+)")


def extract_version(raw_output: str) -> str | None:
    match = VERSION_RE.search(raw_output)
    return match.group(1) if match else None


def run_bulk(
    devices: list[str], command: str, transport: MockTransport, extractor=extract_version
) -> list[dict]:
    results = []
    for device in devices:
        try:
            raw = transport.send_command(device, command)
        except ConnectionError as exc:
            results.append({
                "device": device, "reachable": False, "raw_output": None,
                "extracted": None, "error": str(exc),
            })
            continue
        results.append({
            "device": device, "reachable": True, "raw_output": raw,
            "extracted": extractor(raw), "error": None,
        })
    return results


def compare_to_baseline(results: list[dict], baseline: str) -> dict:
    matched, drifted, unreachable = [], [], []
    for r in results:
        if not r["reachable"]:
            unreachable.append(r["device"])
        elif r["extracted"] == baseline:
            matched.append(r["device"])
        else:
            drifted.append({"device": r["device"], "extracted": r["extracted"]})
    return {
        "baseline": baseline,
        "n_devices": len(results),
        "n_matched": len(matched),
        "n_drifted": len(drifted),
        "n_unreachable": len(unreachable),
        "matched": matched,
        "drifted": drifted,
        "unreachable": unreachable,
    }
