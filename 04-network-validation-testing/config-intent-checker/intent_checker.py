"""Parse hierarchical device config into a structured block model, and check
declarative "intents" against it, each with a specific pass/fail reason.

`golden-config-drift-detector` (elsewhere in this repo) diffs config as a flat
line multiset — good for "did anything change," bad for "is this interface
actually in access mode on the right VLAN," which needs the block structure
(a top-level line like `interface GigabitEthernet0/1` owns the indented
sub-lines under it). This is that complementary technique.
"""
from __future__ import annotations

import re


def parse_config(text: str) -> list[dict]:
    """Top-level (non-indented) lines each own the indented sub-lines that
    follow them, up to the next top-level line. Blank lines are skipped."""
    blocks: list[dict] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        if raw_line[0].isspace():
            if not blocks:
                continue  # a stray indented line before any top-level line; ignore
            blocks[-1]["sub_lines"].append(raw_line.strip())
        else:
            blocks.append({"line": raw_line.strip(), "sub_lines": []})
    return blocks


def _find_interface_block(blocks: list[dict], interface: str) -> dict | None:
    for b in blocks:
        if b["line"] == f"interface {interface}":
            return b
    return None


_ACCESS_VLAN_RE = re.compile(r"^switchport access vlan (\d+)$")


def _check_interface_access_vlan(intent: dict, blocks: list[dict]) -> tuple[bool, str | None]:
    interface, expected_vlan = intent["interface"], intent["vlan"]
    block = _find_interface_block(blocks, interface)
    if block is None:
        return False, f"interface {interface} not found in config"
    if "switchport mode trunk" in block["sub_lines"] or "switchport mode access" not in block["sub_lines"]:
        return False, f"interface {interface} is not in access mode"
    actual_vlan = None
    for sub in block["sub_lines"]:
        m = _ACCESS_VLAN_RE.match(sub)
        if m:
            actual_vlan = int(m.group(1))
            break
    if actual_vlan is None:
        return False, f"no switchport access vlan configured on {interface}, expected {expected_vlan}"
    if actual_vlan != expected_vlan:
        return False, f"found switchport access vlan {actual_vlan}, expected {expected_vlan}"
    return True, None


def _check_line_present(intent: dict, blocks: list[dict]) -> tuple[bool, str | None]:
    pattern = re.compile(intent["pattern"])
    for b in blocks:
        if pattern.search(b["line"]):
            return True, None
    return False, f"no line matching pattern {intent['pattern']!r} found in config"


_CHECKERS = {
    "interface_access_vlan": _check_interface_access_vlan,
    "line_present": _check_line_present,
}


def check_intent(intent: dict, blocks: list[dict]) -> dict:
    checker = _CHECKERS.get(intent["type"])
    if checker is None:
        raise ValueError(f"unknown intent type: {intent['type']!r}")
    passed, reason = checker(intent, blocks)
    return {"intent": intent, "passed": passed, "reason": reason}


def run_intents(intents: list[dict], blocks: list[dict]) -> list[dict]:
    return [check_intent(intent, blocks) for intent in intents]
