"""Unit tests for MAC table parsing and flap detection."""
from mac_table import detect_flapping, parse_mac_table

SAMPLE_TABLE = """          Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
  10    0011.2233.4455    DYNAMIC     Gi1/0/5
  20    0011.2233.4477    DYNAMIC     Gi1/0/12
"""


def test_parse_mac_table_skips_header_and_separator_lines():
    entries = parse_mac_table(SAMPLE_TABLE, "sw1", "2026-01-15T09:00:00")
    assert len(entries) == 2
    assert entries[0] == {
        "timestamp": "2026-01-15T09:00:00",
        "switch": "sw1",
        "vlan": 10,
        "mac": "0011.2233.4455",
        "port": "Gi1/0/5",
    }


def test_parse_mac_table_lowercases_mac():
    entries = parse_mac_table("  10    AABB.CCDD.EEFF    DYNAMIC     Gi1/0/1\n", "sw1", "t")
    assert entries[0]["mac"] == "aabb.ccdd.eeff"


def test_no_change_is_not_a_flap():
    entries = [
        {"timestamp": "2026-01-15T09:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
        {"timestamp": "2026-01-15T09:00:10", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
    ]
    assert detect_flapping(entries) == []


def test_port_change_within_window_is_a_flap():
    entries = [
        {"timestamp": "2026-01-15T09:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
        {"timestamp": "2026-01-15T09:00:10", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/2"},
    ]
    flaps = detect_flapping(entries, window_seconds=60)
    assert len(flaps) == 1
    assert flaps[0]["from_port"] == "Gi1/0/1"
    assert flaps[0]["to_port"] == "Gi1/0/2"
    assert flaps[0]["delta_seconds"] == 10.0


def test_port_change_outside_window_is_not_a_flap():
    entries = [
        {"timestamp": "2026-01-15T09:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
        {"timestamp": "2026-01-15T11:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/2"},
    ]
    assert detect_flapping(entries, window_seconds=60) == []


def test_flapping_is_scoped_per_switch_and_vlan():
    # Same MAC, same port-change pattern, but on different switches/VLANs —
    # these must not be conflated into one group.
    entries = [
        {"timestamp": "2026-01-15T09:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
        {"timestamp": "2026-01-15T09:00:05", "switch": "sw2", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/9"},
    ]
    assert detect_flapping(entries) == []  # different switch, so no "change" to compare


def test_exactly_one_boundary_check_at_the_window_edge():
    entries = [
        {"timestamp": "2026-01-15T09:00:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/1"},
        {"timestamp": "2026-01-15T09:01:00", "switch": "sw1", "vlan": 10, "mac": "aa.bb.cc", "port": "Gi1/0/2"},
    ]
    assert len(detect_flapping(entries, window_seconds=60)) == 1  # exactly at the boundary, inclusive
