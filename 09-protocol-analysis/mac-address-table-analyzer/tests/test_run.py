"""End-to-end test: the committed polls.json detects exactly the expected
flap — a regression test for the committed results.json.
"""
import json
from pathlib import Path

from mac_table import detect_flapping, parse_mac_table

HERE = Path(__file__).resolve().parent.parent


def _entries_from_committed_polls():
    polls = json.loads((HERE / "polls.json").read_text())
    entries = []
    for p in polls:
        entries.extend(parse_mac_table(p["text"], p["switch"], p["timestamp"]))
    return entries


def test_committed_polls_detect_exactly_one_flap():
    entries = _entries_from_committed_polls()
    assert len(entries) == 9
    flaps = detect_flapping(entries, window_seconds=60)
    assert len(flaps) == 1
    assert flaps[0]["mac"] == "0011.2233.4455"
    assert flaps[0]["from_port"] == "Gi1/0/5"
    assert flaps[0]["to_port"] == "Gi1/0/7"


def test_committed_results_match_a_fresh_run():
    entries = _entries_from_committed_polls()
    flaps = detect_flapping(entries, window_seconds=60)
    fresh = {"n_entries": len(entries), "n_flaps": len(flaps), "flaps": flaps}
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
