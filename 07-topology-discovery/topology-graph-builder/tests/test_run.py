"""End-to-end test: the committed adjacency.json analyzes as expected — a
regression test for the committed results.json.
"""
import json
from pathlib import Path

from topology import analyze

HERE = Path(__file__).resolve().parent.parent


def test_committed_adjacency_matches_expectations():
    records = json.loads((HERE / "adjacency.json").read_text())
    result = analyze(records)
    assert result["n_devices"] == 8
    assert result["n_raw_records"] == 11
    assert result["n_unique_edges"] == 7
    assert result["n_components"] == 2
    assert result["articulation_points"] == ["agg1", "core1"]


def test_committed_results_match_a_fresh_run():
    records = json.loads((HERE / "adjacency.json").read_text())
    fresh = analyze(records)
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
