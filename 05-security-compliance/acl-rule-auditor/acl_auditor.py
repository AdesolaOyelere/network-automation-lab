"""Structural ACL audit logic, independent of device connectivity."""

import ipaddress
import json
from typing import Any

from transport import DeviceTransport

Rule = dict[str, Any]
REQUIRED = {
    "sequence",
    "action",
    "protocol",
    "source",
    "destination",
    "destination_port",
    "hit_count",
    "days_since_hit",
}


def validate_rule(rule: Rule) -> None:
    missing = REQUIRED - rule.keys()
    if missing:
        raise ValueError(f"rule missing fields: {', '.join(sorted(missing))}")
    if rule["action"] not in {"permit", "deny"}:
        raise ValueError(f"unsupported action: {rule['action']}")
    ipaddress.ip_network(rule["source"], strict=True)
    ipaddress.ip_network(rule["destination"], strict=True)
    if rule["hit_count"] < 0 or rule["days_since_hit"] < 0:
        raise ValueError("hit counters and age must be non-negative")


def _covers(earlier: Rule, later: Rule) -> bool:
    return (
        (earlier["protocol"] == "any" or earlier["protocol"] == later["protocol"])
        and (earlier["destination_port"] == "any" or earlier["destination_port"] == later["destination_port"])
        and ipaddress.ip_network(later["source"]).subnet_of(ipaddress.ip_network(earlier["source"]))
        and ipaddress.ip_network(later["destination"]).subnet_of(ipaddress.ip_network(earlier["destination"]))
    )


def _finding(name: str, rule: Rule, kind: str, severity: str, detail: str) -> dict:
    return {"acl": name, "sequence": rule["sequence"], "type": kind, "severity": severity, "detail": detail}


def audit_acl(name: str, rules: list[Rule], unused_after_days: int = 60) -> list[dict]:
    """Find overly permissive, shadowed, and stale unused permit rules."""
    if unused_after_days < 0:
        raise ValueError("unused_after_days must be non-negative")
    ordered = sorted(rules, key=lambda rule: rule["sequence"])
    findings: list[dict] = []
    sequences: set[int] = set()
    for index, rule in enumerate(ordered):
        validate_rule(rule)
        if rule["sequence"] in sequences:
            raise ValueError(f"duplicate sequence {rule['sequence']} in ACL {name}")
        sequences.add(rule["sequence"])
        if (
            rule["action"] == "permit"
            and rule["protocol"] == "any"
            and rule["source"] == "0.0.0.0/0"
            and rule["destination"] == "0.0.0.0/0"
            and rule["destination_port"] == "any"
        ):
            findings.append(_finding(name, rule, "any-any-permit", "critical", "Permits all IPv4 traffic"))
        shadow = next((prior for prior in ordered[:index] if _covers(prior, rule)), None)
        if shadow is not None:
            severity = "high" if shadow["action"] != rule["action"] else "medium"
            findings.append(
                _finding(
                    name,
                    rule,
                    "shadowed",
                    severity,
                    f"Fully covered by sequence {shadow['sequence']} ({shadow['action']})",
                )
            )
        if rule["action"] == "permit" and rule["hit_count"] == 0 and rule["days_since_hit"] >= unused_after_days:
            findings.append(_finding(name, rule, "unused", "low", f"No hits for {rule['days_since_hit']} days"))
    return findings


def audit_device(transport: DeviceTransport, unused_after_days: int = 60) -> dict:
    payload = json.loads(transport.run_command("show access-lists structured"))
    findings: list[dict] = []
    rule_count = 0
    for acl in payload["acls"]:
        rule_count += len(acl["rules"])
        findings.extend(audit_acl(acl["name"], acl["rules"], unused_after_days))
    kinds = ("any-any-permit", "shadowed", "unused")
    severities = ("critical", "high", "medium", "low")
    return {
        "hostname": payload["hostname"],
        "collected_at": payload["collected_at"],
        "acl_count": len(payload["acls"]),
        "rule_count": rule_count,
        "finding_count": len(findings),
        "findings_by_type": {kind: sum(item["type"] == kind for item in findings) for kind in kinds},
        "findings_by_severity": {
            severity: sum(item["severity"] == severity for item in findings) for severity in severities
        },
        "findings": findings,
    }
