import json
from pathlib import Path

from acl_auditor import audit_device
from transport import MockDeviceTransport

HERE = Path(__file__).resolve().parent.parent


def test_mock_tracks_the_device_command():
    transport = MockDeviceTransport(HERE / "mock_device.json")
    audit_device(transport)
    assert transport.commands == ["show access-lists structured"]


def test_committed_fixture_matches_committed_results():
    fresh = audit_device(MockDeviceTransport(HERE / "mock_device.json"))
    committed = json.loads((HERE / "results" / "results.json").read_text(encoding="utf-8"))
    assert fresh == committed


def test_committed_aggregate_counts():
    result = audit_device(MockDeviceTransport(HERE / "mock_device.json"))
    assert result["acl_count"] == 2
    assert result["rule_count"] == 7
    assert result["finding_count"] == 5
    assert result["findings_by_type"] == {"any-any-permit": 1, "shadowed": 2, "unused": 2}
