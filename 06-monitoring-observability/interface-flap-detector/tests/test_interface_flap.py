"""Unit tests for the sliding-window flap detector and uptime calculator.

The sliding-window logic is the load-bearing correctness claim: total
transition count alone must NOT be enough to flag flapping — only a cluster
within the window should.
"""
from datetime import datetime

from interface_flap import compute_uptime, detect_flapping, max_transitions_in_window


def test_max_transitions_in_window_clustered():
    ts = [datetime(2026, 1, 1, 10, 0, s) for s in (0, 8, 15, 22, 30, 40)]
    assert max_transitions_in_window(ts, window_seconds=60) == 6


def test_max_transitions_in_window_spread_out():
    ts = [
        datetime(2026, 1, 1, 9, 0, 0), datetime(2026, 1, 1, 9, 0, 5),
        datetime(2026, 1, 1, 10, 30, 0), datetime(2026, 1, 1, 10, 30, 5),
        datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5),
    ]
    assert max_transitions_in_window(ts, window_seconds=60) == 2


def test_detect_flapping_flags_clustered_not_spread_out():
    events = [
        {"timestamp": "2026-01-01T10:00:00", "device": "sw1", "interface": "Gi0/1", "state": "down"},
        {"timestamp": "2026-01-01T10:00:08", "device": "sw1", "interface": "Gi0/1", "state": "up"},
        {"timestamp": "2026-01-01T10:00:15", "device": "sw1", "interface": "Gi0/1", "state": "down"},
        {"timestamp": "2026-01-01T10:00:22", "device": "sw1", "interface": "Gi0/1", "state": "up"},
        {"timestamp": "2026-01-01T10:00:30", "device": "sw1", "interface": "Gi0/1", "state": "down"},
        {"timestamp": "2026-01-01T10:00:40", "device": "sw1", "interface": "Gi0/1", "state": "up"},
        {"timestamp": "2026-01-01T09:00:00", "device": "sw2", "interface": "Gi0/2", "state": "down"},
        {"timestamp": "2026-01-01T09:00:05", "device": "sw2", "interface": "Gi0/2", "state": "up"},
        {"timestamp": "2026-01-01T10:30:00", "device": "sw2", "interface": "Gi0/2", "state": "down"},
        {"timestamp": "2026-01-01T10:30:05", "device": "sw2", "interface": "Gi0/2", "state": "up"},
        {"timestamp": "2026-01-01T12:00:00", "device": "sw2", "interface": "Gi0/2", "state": "down"},
        {"timestamp": "2026-01-01T12:00:05", "device": "sw2", "interface": "Gi0/2", "state": "up"},
    ]
    result = detect_flapping(events, window_seconds=60, threshold=4)
    by_iface = {(r["device"], r["interface"]): r for r in result["interfaces"]}
    assert by_iface[("sw1", "Gi0/1")]["flapping"] is True
    assert by_iface[("sw1", "Gi0/1")]["n_transitions"] == 6
    assert by_iface[("sw2", "Gi0/2")]["flapping"] is False
    assert by_iface[("sw2", "Gi0/2")]["n_transitions"] == 6  # same total count, not flapping


def test_compute_uptime_single_down_period():
    # With only this interface's events in the log, the observed period is
    # exactly bounded by its own down->up bracket (09:00:00 to 09:15:00), so
    # from the observer's perspective it was down for the entire window: 0%
    # uptime. That's a real edge case of "observed period = min/max event
    # timestamp across the whole log," not a bug.
    events = [
        {"timestamp": "2026-01-01T09:00:00", "device": "sw1", "interface": "Gi0/1", "state": "down"},
        {"timestamp": "2026-01-01T09:15:00", "device": "sw1", "interface": "Gi0/1", "state": "up"},
    ]
    result = compute_uptime(events)
    iface = result["interfaces"][0]
    assert iface["down_seconds"] == 900.0
    assert iface["uptime_pct"] == 0.0


def test_compute_uptime_extends_final_down_state_to_observed_end():
    events = [
        {"timestamp": "2026-01-01T09:00:00", "device": "sw1", "interface": "Gi0/1", "state": "up"},
        {"timestamp": "2026-01-01T09:00:00", "device": "sw2", "interface": "Gi0/9", "state": "down"},
        {"timestamp": "2026-01-01T11:00:00", "device": "sw1", "interface": "Gi0/1", "state": "down"},
    ]
    result = compute_uptime(events)
    by_iface = {(r["device"], r["interface"]): r for r in result["interfaces"]}
    # sw1/Gi0/1: up until 11:00:00 (2h), then down until observed_end (11:00:00) -> 0s down
    assert by_iface[("sw1", "Gi0/1")]["down_seconds"] == 0.0
    # sw2/Gi0/9: down at t=0, stays down through the whole observed period (2h = 7200s)
    assert by_iface[("sw2", "Gi0/9")]["down_seconds"] == 7200.0
    assert by_iface[("sw2", "Gi0/9")]["uptime_pct"] == 0.0


def test_compute_uptime_empty_events():
    result = compute_uptime([])
    assert result["interfaces"] == []
    assert result["observed_start"] is None
