"""Normalize hierarchical IOS-style configuration and detect semantic drift."""

from dataclasses import dataclass
from pathlib import Path

from transport import ConfigTransport

VOLATILE_PREFIXES = ("! Last configuration change", "Building configuration", "Current configuration")


@dataclass(frozen=True)
class Statement:
    context: str
    command: str
    key: str


def normalize_config(config: str) -> list[Statement]:
    """Return meaningful statements with parent context and stable comparison keys."""
    statements: list[Statement] = []
    context = "global"
    seen: set[tuple[str, str]] = set()
    for raw_line in config.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped == "!" or stripped.startswith(VOLATILE_PREFIXES):
            continue
        indented = raw_line[:1].isspace()
        if not indented:
            context = stripped if stripped.startswith(("interface ", "router ")) else "global"
        statement_context = context if indented else "global"
        item = Statement(statement_context, stripped, _command_key(statement_context, stripped))
        identity = (item.context, item.command)
        if identity not in seen:
            statements.append(item)
            seen.add(identity)
    return statements


def _command_key(context: str, command: str) -> str:
    """Identify mutually exclusive commands so value changes pair as changed drift."""
    words = command.split()
    if context.startswith("interface "):
        if words[:1] == ["description"]:
            return "description"
        if words[:2] == ["ip", "address"]:
            return "ip address"
        if words[:2] == ["ip", "helper-address"]:
            return "ip helper-address"
    if words[:1] == ["hostname"]:
        return "hostname"
    if words[:1] == ["router-id"]:
        return "router-id"
    return command


def compare_configs(golden: str, running: str) -> dict:
    """Classify changed, missing, and unexpected normalized statements."""
    expected = normalize_config(golden)
    actual = normalize_config(running)
    expected_by_key = {(item.context, item.key): item for item in expected}
    actual_by_key = {(item.context, item.key): item for item in actual}
    changed = []
    for identity in expected_by_key.keys() & actual_by_key.keys():
        before, after = expected_by_key[identity], actual_by_key[identity]
        if before.command != after.command:
            changed.append({"context": before.context, "expected": before.command, "actual": after.command})
    changed_keys = {(item["context"], _command_key(item["context"], item["expected"])) for item in changed}
    missing = [
        {"context": item.context, "command": item.command}
        for item in expected
        if (item.context, item.key) not in actual_by_key and (item.context, item.key) not in changed_keys
    ]
    unexpected = [
        {"context": item.context, "command": item.command}
        for item in actual
        if (item.context, item.key) not in expected_by_key and (item.context, item.key) not in changed_keys
    ]
    changed.sort(key=lambda item: (item["context"], item["expected"]))
    return {
        "in_sync": not (changed or missing or unexpected),
        "summary": {"changed": len(changed), "missing": len(missing), "unexpected": len(unexpected)},
        "changed": changed,
        "missing": missing,
        "unexpected": unexpected,
    }


def audit_device(transport: ConfigTransport, golden_path: str | Path) -> dict:
    result = compare_configs(Path(golden_path).read_text(encoding="utf-8"), transport.get_running_config())
    hostname = getattr(transport, "hostname", "unknown")
    return {"hostname": hostname, **result}
