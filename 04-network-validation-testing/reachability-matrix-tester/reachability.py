"""Test declared reachability intent against an actual ACL's evaluation order.

A query is a *subnet-to-subnet* reachability question (not a single host
pair), so matching a rule requires care: a rule only gives a clean,
unambiguous answer for the query if the rule's source and destination ranges
each **fully cover** the queried subnet. If a rule's range only *partially*
overlaps the queried subnet, part of that subnet's traffic would match the
rule and part wouldn't — the query itself is ambiguous at the granularity
asked, and this reports that plainly as `mixed` rather than guessing which
side wins. This is deliberately scoped to L3 (protocol + source/destination
subnet); L4 ports are out of scope here.

ACL rules are evaluated in `sequence` order, first full match wins — the same
first-match-wins semantics a real ACL uses. No matching rule falls through to
an implicit deny.
"""
from __future__ import annotations

import ipaddress


def _coverage(rule_range: str, query_range: str) -> str:
    """'full' if the entire query range is covered by the rule's range,
    'partial' if they overlap but the query isn't fully covered, 'none' if
    they don't overlap at all."""
    rule_net = ipaddress.ip_network(rule_range)
    query_net = ipaddress.ip_network(query_range)
    if not rule_net.overlaps(query_net):
        return "none"
    if query_net.subnet_of(rule_net) or query_net == rule_net:
        return "full"
    return "partial"


def _protocol_matches(rule_protocol: str, query_protocol: str) -> bool:
    """'any' is a wildcard only on the RULE side (standard ACL semantics: a rule
    declaring protocol 'any' applies to all protocols). A query's protocol is
    expected to be concrete (e.g. 'tcp') — a query literally passing 'any' is
    not treated as "match every rule regardless of its protocol"; it only
    matches rules that are themselves declared 'any', same as any other exact
    string would. Making the query side a wildcard too would silently answer a
    different, broader question than what was asked (whether ALL protocols
    agree), which this module does not attempt to determine."""
    return rule_protocol == "any" or rule_protocol == query_protocol


def evaluate_acl(rules: list[dict], protocol: str, src: str, dst: str) -> dict:
    """rules: [{sequence, action: permit|deny, protocol, source, destination}, ...].
    Returns {verdict: permit|deny|mixed, matched_rule_seq, reason}."""
    for rule in sorted(rules, key=lambda r: r["sequence"]):
        if not _protocol_matches(rule["protocol"], protocol):
            continue
        src_coverage = _coverage(rule["source"], src)
        dst_coverage = _coverage(rule["destination"], dst)
        if src_coverage == "none" or dst_coverage == "none":
            continue
        if src_coverage == "partial" or dst_coverage == "partial":
            return {
                "verdict": "mixed",
                "matched_rule_seq": rule["sequence"],
                "reason": f"rule {rule['sequence']} only partially overlaps the queried range",
            }
        return {"verdict": rule["action"], "matched_rule_seq": rule["sequence"], "reason": None}
    return {"verdict": "deny", "matched_rule_seq": None, "reason": "implicit deny (no rule matched)"}


def evaluate_intent(intent: list[dict], rules: list[dict]) -> dict:
    """intent: [{src, dst, protocol, expected: permit|deny}, ...].
    Compares each entry's actual ACL verdict against its declared expectation."""
    results = []
    for item in intent:
        outcome = evaluate_acl(rules, item["protocol"], item["src"], item["dst"])
        if outcome["verdict"] == "mixed":
            status = "ambiguous"
        elif outcome["verdict"] == item["expected"]:
            status = "pass"
        else:
            status = "violation"
        results.append({**item, **outcome, "status": status})

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "violation": sum(1 for r in results if r["status"] == "violation"),
        "ambiguous": sum(1 for r in results if r["status"] == "ambiguous"),
    }
    return {"summary": summary, "results": results}
