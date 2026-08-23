import pytest
from acl_auditor import audit_acl


def rule(sequence=10, **overrides):
    item = {
        "sequence": sequence,
        "action": "permit",
        "protocol": "tcp",
        "source": "192.0.2.0/24",
        "destination": "10.0.0.0/24",
        "destination_port": "443",
        "hit_count": 1,
        "days_since_hit": 0,
    }
    item.update(overrides)
    return item


def test_any_any_permit_but_not_terminal_deny_is_flagged():
    findings = audit_acl(
        "EDGE",
        [
            rule(protocol="any", source="0.0.0.0/0", destination="0.0.0.0/0", destination_port="any"),
            rule(
                sequence=20,
                action="deny",
                protocol="any",
                source="0.0.0.0/0",
                destination="0.0.0.0/0",
                destination_port="any",
            ),
        ],
    )
    assert [finding["type"] for finding in findings] == ["any-any-permit", "shadowed"]
    assert findings[1]["severity"] == "high"


def test_narrower_same_service_rule_is_shadowed_by_earlier_supernet():
    findings = audit_acl(
        "WEB",
        [
            rule(source="192.0.2.0/24"),
            rule(sequence=20, source="192.0.2.128/25"),
        ],
    )
    assert findings == [
        {
            "acl": "WEB",
            "sequence": 20,
            "type": "shadowed",
            "severity": "medium",
            "detail": "Fully covered by sequence 10 (permit)",
        }
    ]


def test_different_port_is_not_shadowed():
    findings = audit_acl("WEB", [rule(), rule(sequence=20, destination_port="80")])
    assert findings == []


def test_unused_threshold_is_inclusive_and_only_applies_to_permits():
    findings = audit_acl(
        "OLD",
        [
            rule(hit_count=0, days_since_hit=60),
            rule(sequence=20, action="deny", hit_count=0, days_since_hit=90, destination_port="80"),
        ],
    )
    assert [finding["type"] for finding in findings] == ["unused"]


def test_duplicate_sequence_and_negative_threshold_are_rejected():
    with pytest.raises(ValueError, match="duplicate sequence"):
        audit_acl("BAD", [rule(), rule()])
    with pytest.raises(ValueError, match="non-negative"):
        audit_acl("BAD", [], unused_after_days=-1)


def test_missing_field_and_host_bits_are_rejected():
    incomplete = rule()
    del incomplete["protocol"]
    with pytest.raises(ValueError, match="missing fields"):
        audit_acl("BAD", [incomplete])
    with pytest.raises(ValueError):
        audit_acl("BAD", [rule(source="192.0.2.4/24")])
