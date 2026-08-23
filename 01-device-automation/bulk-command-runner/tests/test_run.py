"""End-to-end test: the committed fleet.json produces the committed results.json."""
import json
from pathlib import Path

from bulk_runner import compare_to_baseline, run_bulk
from transport import MockTransport

HERE = Path(__file__).resolve().parent.parent


def test_committed_fleet_matches_committed_results():
    data = json.loads((HERE / "fleet.json").read_text())
    transport = MockTransport(data["fixtures"], unreachable=set(data["unreachable"]))
    results = run_bulk(data["devices"], data["command"], transport)
    fresh = compare_to_baseline(results, data["baseline_version"])
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
    assert fresh["n_devices"] == 10
    assert fresh["n_matched"] == 6
    assert fresh["n_drifted"] == 3
    assert fresh["n_unreachable"] == 1
