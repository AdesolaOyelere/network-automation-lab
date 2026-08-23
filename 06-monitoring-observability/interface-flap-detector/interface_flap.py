"""Detect flapping interfaces from a chronological, interleaved event log.

An interface is "flapping" if it has more than `threshold` state transitions
within any `window_seconds`-wide sliding window — not just "more than
threshold transitions in the whole log," which would treat six transitions
spread across three hours the same as six transitions in forty seconds. Only
the second is actually an operational problem, so the detector uses a real
sliding-window (two-pointer) scan over each interface's own sorted event
timestamps.

Defaults (4 transitions in 60 seconds) are a reasonable illustrative
threshold for this dataset, not an asserted industry standard — tune them to
the actual environment.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_THRESHOLD = 4


def _parse_events(raw_events: list[dict]) -> list[dict]:
    return [{**e, "timestamp": datetime.fromisoformat(e["timestamp"])} for e in raw_events]


def _group_by_interface(events: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in events:
        groups[(e["device"], e["interface"])].append(e)
    for group in groups.values():
        group.sort(key=lambda e: e["timestamp"])
    return groups


def max_transitions_in_window(timestamps: list[datetime], window_seconds: int) -> int:
    """Max number of timestamps falling within any window of `window_seconds`,
    via a sliding two-pointer scan over sorted timestamps."""
    left = 0
    best = 0
    for right in range(len(timestamps)):
        while (timestamps[right] - timestamps[left]).total_seconds() > window_seconds:
            left += 1
        best = max(best, right - left + 1)
    return best


def detect_flapping(
    raw_events: list[dict], window_seconds: int = DEFAULT_WINDOW_SECONDS, threshold: int = DEFAULT_THRESHOLD
) -> dict:
    groups = _group_by_interface(_parse_events(raw_events))
    interfaces = []
    for (device, interface), group in groups.items():
        timestamps = [e["timestamp"] for e in group]
        max_count = max_transitions_in_window(timestamps, window_seconds)
        interfaces.append({
            "device": device, "interface": interface, "n_transitions": len(group),
            "max_transitions_in_window": max_count, "flapping": max_count > threshold,
        })
    interfaces.sort(key=lambda r: (r["device"], r["interface"]))
    return {"window_seconds": window_seconds, "threshold": threshold, "interfaces": interfaces}


def compute_uptime(raw_events: list[dict], initial_state: str = "up") -> dict:
    """Uptime % per interface over the observed period (first to last event
    timestamp across the whole log). Assumes each interface was in
    `initial_state` before its first logged event — a stated assumption, not
    a claim of ground truth from before the log started."""
    events = _parse_events(raw_events)
    if not events:
        return {"observed_start": None, "observed_end": None, "total_seconds": 0.0, "interfaces": []}

    observed_start = min(e["timestamp"] for e in events)
    observed_end = max(e["timestamp"] for e in events)
    total_seconds = (observed_end - observed_start).total_seconds()

    interfaces = []
    for (device, interface), group in _group_by_interface(events).items():
        down_seconds = 0.0
        state, last_time = initial_state, observed_start
        for e in group:
            if state == "down":
                down_seconds += (e["timestamp"] - last_time).total_seconds()
            state, last_time = e["state"], e["timestamp"]
        if state == "down":
            down_seconds += (observed_end - last_time).total_seconds()
        uptime_pct = 1.0 - (down_seconds / total_seconds) if total_seconds > 0 else 1.0
        interfaces.append({
            "device": device, "interface": interface,
            "down_seconds": down_seconds, "uptime_pct": round(uptime_pct, 4),
        })
    interfaces.sort(key=lambda r: (r["device"], r["interface"]))
    return {
        "observed_start": observed_start.isoformat(), "observed_end": observed_end.isoformat(),
        "total_seconds": total_seconds, "interfaces": interfaces,
    }
