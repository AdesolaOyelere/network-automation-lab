"""Offline transport boundary and deterministic mock device."""

from pathlib import Path
from typing import Protocol


class DeviceTransport(Protocol):
    def run_command(self, command: str) -> str: ...


class MockDeviceTransport:
    """Return scripted ACL data and record requested commands."""

    def __init__(self, fixture_path: str | Path) -> None:
        self.fixture_path = Path(fixture_path)
        self.commands: list[str] = []

    def run_command(self, command: str) -> str:
        self.commands.append(command)
        if command != "show access-lists structured":
            raise ValueError(f"unsupported mock command: {command}")
        return self.fixture_path.read_text(encoding="utf-8")
