"""Offline transport boundary and deterministic mock network device."""

import json
from pathlib import Path
from typing import Protocol


class ConfigTransport(Protocol):
    def get_running_config(self) -> str: ...


class MockConfigTransport:
    """Load synthetic running configuration and record collection calls."""

    def __init__(self, fixture_path: str | Path) -> None:
        self.fixture_path = Path(fixture_path)
        self.commands: list[str] = []

    def get_running_config(self) -> str:
        self.commands.append("show running-config")
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        return payload["running_config"]

    @property
    def hostname(self) -> str:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))["hostname"]
