"""Parse Cisco-IOS-style syslog lines, bucket by severity, and collapse
consecutive repeats (e.g. a flapping interface) into aggregated counts.

Line format: `<timestamp> <hostname> %<FACILITY>-<SEVERITY 0-7>-<MNEMONIC>: <message>`
e.g. `Jan 15 09:20:03 dist-sw2 %LINK-3-UPDOWN: Interface GigabitEthernet0/3, changed state to down`

`dedupe_and_aggregate` only collapses a *consecutive run* of identical
(hostname, facility, mnemonic) entries — it is not a time-windowed dedup. If
the same event recurs after something else was logged in between, it starts
a new aggregated entry rather than merging with an earlier one. That's a
deliberate, stated scope limit: a full time-windowed correlator is a
different (and heavier) tool.
"""
from __future__ import annotations

import re

SEVERITY_NAMES = {
    0: "emergency", 1: "alert", 2: "critical", 3: "error",
    4: "warning", 5: "notice", 6: "informational", 7: "debug",
}

_LINE_RE = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"%(?P<facility>[A-Z0-9_]+)-(?P<severity>\d)-(?P<mnemonic>[A-Z0-9_]+):\s*"
    r"(?P<message>.*)$"
)


def bucket(severity: int) -> str:
    if severity <= 3:
        return "critical"
    if severity <= 5:
        return "warning"
    return "info"


def parse_syslog(lines: list[str]) -> tuple[list[dict], list[dict]]:
    """Returns (records, errors). A line that doesn't match the expected shape,
    or whose severity digit is outside 0-7, becomes an error entry rather than
    raising — one bad line shouldn't take down triage of the rest."""
    records: list[dict] = []
    errors: list[dict] = []
    for line in lines:
        m = _LINE_RE.match(line)
        if not m:
            errors.append({"line": line, "reason": "does not match expected syslog format"})
            continue
        severity = int(m.group("severity"))
        if not 0 <= severity <= 7:
            errors.append({"line": line, "reason": f"severity {severity} out of range 0-7"})
            continue
        records.append({
            "timestamp": m.group("timestamp"),
            "hostname": m.group("hostname"),
            "facility": m.group("facility"),
            "severity": severity,
            "severity_name": SEVERITY_NAMES[severity],
            "mnemonic": m.group("mnemonic"),
            "message": m.group("message"),
        })
    return records, errors


def dedupe_and_aggregate(records: list[dict]) -> list[dict]:
    """Collapse consecutive identical (hostname, facility, mnemonic) records."""
    aggregated: list[dict] = []
    for r in records:
        if aggregated:
            last = aggregated[-1]
            if (r["hostname"], r["facility"], r["mnemonic"]) == (last["hostname"], last["facility"], last["mnemonic"]):
                last["count"] += 1
                last["last_seen"] = r["timestamp"]
                continue
        aggregated.append({
            "hostname": r["hostname"],
            "facility": r["facility"],
            "severity": r["severity"],
            "severity_name": r["severity_name"],
            "mnemonic": r["mnemonic"],
            "message": r["message"],
            "count": 1,
            "first_seen": r["timestamp"],
            "last_seen": r["timestamp"],
        })
    return aggregated


def triage(lines: list[str]) -> dict:
    records, parse_errors = parse_syslog(lines)
    aggregated = dedupe_and_aggregate(records)

    buckets = {"critical": 0, "warning": 0, "info": 0}
    for entry in aggregated:
        buckets[bucket(entry["severity"])] += entry["count"]

    top = sorted(aggregated, key=lambda e: -e["count"])[:5]

    return {
        "n_raw_lines": len(lines),
        "n_parsed": len(records),
        "n_parse_errors": len(parse_errors),
        "n_aggregated_entries": len(aggregated),
        "buckets": buckets,
        "top_entries": top,
        "aggregated": aggregated,
        "parse_errors": parse_errors,
    }
