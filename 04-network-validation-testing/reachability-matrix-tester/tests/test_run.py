"""End-to-end test: the committed intent matrix tests as expected against the
committed ACL — a regression test for the committed results.json.
"""
import json
from pathlib import Path

from reachability import evaluate_intent

HERE = Path(__file__).resolve().parent.parent


def test_committed_policy_matches_expectations():
    data = json.loads((HERE / "policy.json").read_text())
    result = evaluate_intent(data["intent"], data["acl_rules"])
    assert result["summary"] == {"total": 5, "pass": 3, "violation": 1, "ambiguous": 1}


def test_committed_results_match_a_fresh_run():
    data = json.loads((HERE / "policy.json").read_text())
    fresh = evaluate_intent(data["intent"], data["acl_rules"])
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
