"""End-to-end test: the committed events.json produces the committed results.json."""
import json
from pathlib import Path

from interface_flap import compute_uptime, detect_flapping

HERE = Path(__file__).resolve().parent.parent


def test_committed_events_match_committed_results():
    events = json.loads((HERE / "events.json").read_text())
    fresh = {"flapping": detect_flapping(events), "uptime": compute_uptime(events)}
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed

    flapping_ifaces = [i for i in fresh["flapping"]["interfaces"] if i["flapping"]]
    assert len(flapping_ifaces) == 1
    assert flapping_ifaces[0]["interface"] == "Gi0/3"
