"""Parse per-switch `show mac address-table`-style output from successive
polls and detect MAC flapping: the same MAC learned on a different port
within a short time window, a classic sign of a bridging loop or a spoofed
source MAC racing the real host.

A single MAC table snapshot can't show flapping on its own — flapping is a
change *over time*, so this works from a time series of polls (poll the
table periodically, timestamp each poll, and diff consecutive observations
per (switch, vlan, mac)). A MAC that legitimately moves to a new port (a
laptop unplugged and replugged elsewhere) still shows up as a port change,
but if that change happens well outside the flap-detection window it's not
flagged — it's a real, slow move, not a loop.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

_LINE_RE = re.compile(
    r"^\s*(?P<vlan>\d+)\s+(?P<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+"
    r"(?P<type>\S+)\s+(?P<port>\S+)\s*$"
)


def parse_mac_table(text: str, switch: str, timestamp: str) -> list[dict]:
    """Parse one poll's raw table text into flat entries. Header/separator
    lines that don't match the Vlan/Mac/Type/Ports row shape are skipped."""
    entries = []
    for line in text.splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        entries.append({
            "timestamp": timestamp,
            "switch": switch,
            "vlan": int(m.group("vlan")),
            "mac": m.group("mac").lower(),
            "port": m.group("port"),
        })
    return entries


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def detect_flapping(entries: list[dict], window_seconds: int = 60) -> list[dict]:
    """entries: flattened observations across one or more polls (see
    parse_mac_table). Groups by (switch, vlan, mac), and for each consecutive
    pair of observations with a different port, flags it as a flap only if
    the two observations are within `window_seconds` of each other."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in entries:
        groups[(e["switch"], e["vlan"], e["mac"])].append(e)

    flaps = []
    for (switch, vlan, mac), group in groups.items():
        ordered = sorted(group, key=lambda e: _parse_ts(e["timestamp"]))
        for prev, curr in zip(ordered, ordered[1:], strict=False):
            if prev["port"] == curr["port"]:
                continue
            delta = (_parse_ts(curr["timestamp"]) - _parse_ts(prev["timestamp"])).total_seconds()
            if delta <= window_seconds:
                flaps.append({
                    "switch": switch, "vlan": vlan, "mac": mac,
                    "from_port": prev["port"], "to_port": curr["port"],
                    "from_timestamp": prev["timestamp"], "to_timestamp": curr["timestamp"],
                    "delta_seconds": delta,
                })
    return sorted(flaps, key=lambda f: (f["switch"], f["mac"], f["from_timestamp"]))
