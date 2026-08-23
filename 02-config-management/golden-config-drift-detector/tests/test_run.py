import json
from pathlib import Path

from drift_detector import audit_device
from transport import MockConfigTransport

HERE = Path(__file__).resolve().parent.parent


def test_mock_records_collection_command():
    transport = MockConfigTransport(HERE / "mock_device.json")
    audit_device(transport, HERE / "golden_config.txt")
    assert transport.commands == ["show running-config"]


def test_committed_fixture_matches_committed_results():
    fresh = audit_device(MockConfigTransport(HERE / "mock_device.json"), HERE / "golden_config.txt")
    committed = json.loads((HERE / "results" / "results.json").read_text(encoding="utf-8"))
    assert fresh == committed


def test_committed_aggregate_counts():
    result = audit_device(MockConfigTransport(HERE / "mock_device.json"), HERE / "golden_config.txt")
    assert not result["in_sync"]
    assert result["summary"] == {"changed": 2, "missing": 0, "unexpected": 5}
