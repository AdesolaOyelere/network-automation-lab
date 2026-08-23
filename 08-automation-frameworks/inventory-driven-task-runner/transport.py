"""Mock device transport: a canned version table standing in for a real
SSH/API call. One device (`sfo-edge1`) is deliberately absent from the
table to simulate an unreachable device — `get_version` raises for it,
exactly the way a real connection timeout or auth failure would.
"""
from __future__ import annotations


class DeviceUnreachable(Exception):
    pass


_VERSIONS = {
    "nyc-core1": "15.2(4)E7",
    "nyc-core2": "15.2(4)E7",
    "nyc-dist1": "15.2(4)E6",
    "nyc-edge1": "17.3.4a",
    "sfo-core1": "9.3(7)",
    "sfo-dist1": "9.3(7)",
    "lab-sw1": "15.2(4)E7",
}


def get_version(device: dict) -> str:
    name = device["name"]
    if name not in _VERSIONS:
        raise DeviceUnreachable(f"{name}: connection timed out")
    return _VERSIONS[name]
