"""End-to-end test: the committed sample log triages as expected — a
regression test for the committed results.json.
"""
import json
from pathlib import Path

from syslog_triage import triage

HERE = Path(__file__).resolve().parent.parent


def test_committed_log_matches_expectations():
    lines = (HERE / "syslog_sample.log").read_text().splitlines()
    result = triage(lines)
    assert result["n_raw_lines"] == 26
    assert result["n_parsed"] == 25
    assert result["n_parse_errors"] == 1
    assert result["n_aggregated_entries"] == 16
    assert result["top_entries"][0]["count"] == 7
    assert result["top_entries"][0]["mnemonic"] == "UPDOWN"


def test_committed_results_match_a_fresh_run():
    lines = (HERE / "syslog_sample.log").read_text().splitlines()
    fresh = triage(lines)
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
