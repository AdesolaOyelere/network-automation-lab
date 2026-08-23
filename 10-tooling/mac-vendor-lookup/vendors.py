"""Normalize a MAC address in any common format and look up its OUI vendor.

The OUI table below is a small, illustrative sample — mostly well-known,
widely-documented virtualization-platform OUIs (they're exceptionally stable
and frequently cited in troubleshooting guides, which is why they're a safe
set to hardcode) plus a few long-standing real-hardware assignments. It is
NOT a complete or authoritative IEEE registry; for a definitive lookup, query
the IEEE OUI database directly. Say so plainly rather than implying coverage
this table doesn't have.
"""
from __future__ import annotations

import re

OUI_TABLE: dict[str, str] = {
    "00000C": "Cisco Systems, Inc",
    "000C29": "VMware, Inc.",
    "005056": "VMware, Inc.",
    "080027": "PCS Systemtechnik GmbH (Oracle VirtualBox)",
    "00155D": "Microsoft Corporation (Hyper-V)",
    "00163E": "Xensource, Inc.",
    "525400": "QEMU/KVM virtual NIC",
    "B827EB": "Raspberry Pi Foundation",
    "DCA632": "Raspberry Pi Trading Ltd",
    "001C42": "Parallels, Inc.",
    "00E04C": "Realtek Semiconductor Corp.",
}

_HEX_ONLY = re.compile(r"^[0-9A-F]{12}$")


def normalize_mac(mac: str) -> str:
    """Accept colon-, dash-, or Cisco dot-separated MAC forms; return 12 uppercase
    hex chars with no separators. Raises ValueError for anything else."""
    stripped = re.sub(r"[:\-.]", "", mac).upper()
    if not _HEX_ONLY.match(stripped):
        raise ValueError(f"{mac!r} is not a valid MAC address (need 12 hex digits)")
    return stripped


def get_oui(normalized_mac: str) -> str:
    return normalized_mac[:6]


def lookup_vendor(mac: str) -> dict:
    """Normalize + look up one MAC. Never raises for an unknown-but-valid OUI —
    that's reported as 'Unknown vendor', a different outcome from a malformed
    MAC, which raises ValueError."""
    normalized = normalize_mac(mac)
    oui = get_oui(normalized)
    return {
        "input": mac,
        "normalized": normalized,
        "oui": oui,
        "vendor": OUI_TABLE.get(oui, "Unknown vendor"),
        "error": None,
    }


def lookup_batch(macs: list[str]) -> list[dict]:
    """Look up many MACs; a malformed entry is reported with an `error` field
    rather than aborting the whole batch."""
    results = []
    for mac in macs:
        try:
            results.append(lookup_vendor(mac))
        except ValueError as exc:
            results.append({"input": mac, "normalized": None, "oui": None, "vendor": None, "error": str(exc)})
    return results
