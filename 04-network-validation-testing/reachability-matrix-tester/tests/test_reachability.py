"""Unit tests for ACL evaluation and intent-vs-actual reachability testing."""
from reachability import evaluate_acl, evaluate_intent

RULES = [
    {"sequence": 10, "action": "permit", "protocol": "tcp", "source": "10.0.1.0/24", "destination": "10.0.0.0/24"},
    {"sequence": 20, "action": "deny", "protocol": "any", "source": "10.0.2.0/24", "destination": "10.0.0.0/24"},
    {"sequence": 30, "action": "permit", "protocol": "any", "source": "10.0.0.0/16", "destination": "10.0.0.0/24"},
]


def test_full_match_returns_the_matching_rules_action():
    outcome = evaluate_acl(RULES, "tcp", "10.0.1.0/24", "10.0.0.0/24")
    assert outcome == {"verdict": "permit", "matched_rule_seq": 10, "reason": None}


def test_first_match_wins_over_a_later_broader_rule():
    outcome = evaluate_acl(RULES, "any", "10.0.2.0/24", "10.0.0.0/24")
    assert outcome["verdict"] == "deny"
    assert outcome["matched_rule_seq"] == 20


def test_falls_through_to_a_later_broader_permit():
    # Not covered by rule 10 (protocol) or rule 20 (different source), but
    # covered by the broad rule 30.
    outcome = evaluate_acl(RULES, "udp", "10.0.3.0/24", "10.0.0.0/24")
    assert outcome["verdict"] == "permit"
    assert outcome["matched_rule_seq"] == 30


def test_no_matching_rule_is_implicit_deny():
    outcome = evaluate_acl(RULES, "tcp", "192.168.1.0/24", "10.0.0.0/24")
    assert outcome["verdict"] == "deny"
    assert outcome["matched_rule_seq"] is None
    assert "implicit deny" in outcome["reason"]


def test_partial_source_overlap_is_mixed_not_a_guess():
    # Query source is a /23 that only half-overlaps rule 10's /24 source.
    outcome = evaluate_acl(RULES, "tcp", "10.0.0.0/23", "10.0.0.0/24")
    assert outcome["verdict"] == "mixed"
    assert outcome["matched_rule_seq"] == 10


def test_partial_destination_overlap_is_also_mixed():
    outcome = evaluate_acl(RULES, "tcp", "10.0.1.0/24", "10.0.0.0/23")
    assert outcome["verdict"] == "mixed"


def test_query_supernet_of_source_with_no_overlap_falls_through_cleanly():
    # A query source range with zero overlap with rule 10/20's sources should
    # just skip them (not "partial") and fall to the broad rule 30.
    outcome = evaluate_acl(RULES, "any", "10.0.9.0/24", "10.0.0.0/24")
    assert outcome["verdict"] == "permit"
    assert outcome["matched_rule_seq"] == 30


def test_reachability_classifies_pass_violation_and_ambiguous():
    intent = [
        {"name": "expected-permit-and-is", "src": "10.0.1.0/24", "dst": "10.0.0.0/24",
         "protocol": "tcp", "expected": "permit"},
        {"name": "expected-deny-but-actually-permitted", "src": "10.0.9.0/24", "dst": "10.0.0.0/24",
         "protocol": "any", "expected": "deny"},
        {"name": "ambiguous-partial-overlap", "src": "10.0.0.0/23", "dst": "10.0.0.0/24",
         "protocol": "tcp", "expected": "permit"},
    ]
    result = evaluate_intent(intent, RULES)
    assert result["summary"] == {"total": 3, "pass": 1, "violation": 1, "ambiguous": 1}
    by_name = {r["name"]: r for r in result["results"]}
    assert by_name["expected-permit-and-is"]["status"] == "pass"
    assert by_name["expected-deny-but-actually-permitted"]["status"] == "violation"
    assert by_name["ambiguous-partial-overlap"]["status"] == "ambiguous"
