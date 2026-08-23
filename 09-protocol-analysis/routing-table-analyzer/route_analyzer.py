"""Parse a Cisco `show ip route`-style dump and analyze it for real route-table
correctness issues: which candidate route is actually installed, whether a
default route exists at all, and metrics that look like an outlier.

Grading generated routing config/output by *executing real route-preference
rules* rather than string-matching is the point here — the same spirit as
grading generated SQL by running it, not diffing its text.
"""
from __future__ import annotations

import re
import statistics
from collections import defaultdict

CODE_MAP = {"C": "connected", "S": "static", "O": "ospf", "B": "bgp"}

_CONNECTED_RE = re.compile(
    r"^([A-Z])\*?\s+(\d+\.\d+\.\d+\.\d+)/(\d+)\s+is directly connected,\s+(\S+)"
)
_VIA_RE = re.compile(
    r"^([A-Z])\*?\s+(\d+\.\d+\.\d+\.\d+)/(\d+)\s+\[(\d+)/(\d+)\]\s+via\s+(\d+\.\d+\.\d+\.\d+)"
)


def parse_routing_table(text: str) -> list[dict]:
    """Parse route lines; non-route lines (headers, blanks) are skipped."""
    routes = []
    for line in text.splitlines():
        m = _CONNECTED_RE.match(line)
        if m:
            code, network, prefix_len, interface = m.groups()
            routes.append({
                "network": network, "prefix_len": int(prefix_len), "next_hop": None,
                "protocol": CODE_MAP.get(code, code), "metric": 0, "admin_distance": 0,
                "interface": interface,
            })
            continue
        m = _VIA_RE.match(line)
        if m:
            code, network, prefix_len, ad, metric, next_hop = m.groups()
            routes.append({
                "network": network, "prefix_len": int(prefix_len), "next_hop": next_hop,
                "protocol": CODE_MAP.get(code, code), "metric": int(metric),
                "admin_distance": int(ad), "interface": None,
            })
    return routes


def determine_installed_routes(routes: list[dict]) -> dict:
    """Group routes by destination prefix; the lowest admin_distance wins,
    metric only breaks a tie within the same protocol/AD. A tie in both AD and
    metric (true ECMP) is not modeled — the first route in input order wins
    arbitrarily; that's a stated scope limit, not a hidden one."""
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in routes:
        groups[(r["network"], r["prefix_len"])].append(r)

    installed: dict[str, dict] = {}
    not_installed: list[dict] = []
    for (network, prefix_len), group in groups.items():
        best = min(group, key=lambda r: (r["admin_distance"], r["metric"]))
        installed[f"{network}/{prefix_len}"] = best
        for r in group:
            if r is not best:
                if r["admin_distance"] != best["admin_distance"]:
                    reason = (
                        f"administrative distance {r['admin_distance']} loses to "
                        f"installed route's AD {best['admin_distance']} ({best['protocol']})"
                    )
                else:
                    reason = f"higher metric ({r['metric']}) than installed route's metric ({best['metric']})"
                not_installed.append({"route": r, "reason": reason})
    return {"installed": installed, "not_installed": not_installed}


def has_default_route(routes: list[dict]) -> bool:
    return any(r["network"] == "0.0.0.0" and r["prefix_len"] == 0 for r in routes)


def flag_high_metric_routes(routes: list[dict], multiplier: float = 3.0) -> list[dict]:
    """Flag a route whose metric is more than `multiplier` times its protocol's
    median metric. Connected routes (metric always 0) are excluded — the
    heuristic isn't meaningful for them. A protocol with fewer than 2 routes is
    also skipped, since "3x the median of one sample" can't flag anything
    honestly."""
    by_protocol: dict[str, list[dict]] = defaultdict(list)
    for r in routes:
        if r["protocol"] != "connected":
            by_protocol[r["protocol"]].append(r)

    flagged = []
    for group in by_protocol.values():
        if len(group) < 2:
            continue
        median = statistics.median(r["metric"] for r in group)
        threshold = median * multiplier
        if threshold <= 0:
            continue
        for r in group:
            if r["metric"] > threshold:
                flagged.append({**r, "protocol_median_metric": median, "threshold": threshold})
    return flagged
