"""A deterministic mock device transport, keyed by (device, command).

Real bulk-command tooling (Netmiko/NAPALM-style) sends a command string to a
device over SSH and gets back raw CLI text. This mock reproduces exactly that
shape — `send_command(device, command) -> str` — from a canned fixture, and
raises `ConnectionError` for a device that isn't reachable, so callers exercise
the same failure path a real timeout/auth-failure would trigger.
"""
from __future__ import annotations


class ConnectionError(Exception):
    pass


class MockTransport:
    def __init__(self, fixtures: dict[str, dict[str, str]], unreachable: set[str] = frozenset()):
        self._fixtures = fixtures
        self._unreachable = set(unreachable)

    def send_command(self, device: str, command: str) -> str:
        if device in self._unreachable:
            raise ConnectionError(f"{device}: connection timed out")
        try:
            return self._fixtures[device][command]
        except KeyError as exc:
            raise ConnectionError(f"{device}: no output for command {command!r}") from exc
