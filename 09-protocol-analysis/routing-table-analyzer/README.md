# Routing Table Analyzer

> Parse a `show ip route`-style dump and analyze it with real route-preference
> rules — which candidate route is actually installed, whether a default
> route exists, and which metrics look like an outlier.

**Category:** `09-protocol-analysis` · **Skills:** routing, administrative distance, parsing, Python

## Problem

A routing table often has more than one candidate route to the same
destination (a static route and a dynamically-learned one, say), and only
administrative distance — not "which protocol sounds more authoritative" —
decides which one is actually installed. Getting that wrong when reasoning
about a route table by eye is an easy, common mistake.

## Approach

`route_analyzer.py`:

- **`parse_routing_table(text)`** parses Cisco-IOS-style connected
  (`C ... is directly connected, ...`) and via-based (`S/O/B ... [AD/metric]
  via ...`) route lines into structured records.
- **`determine_installed_routes(routes)`** groups routes by destination
  prefix and picks the lowest administrative distance as installed — metric
  only breaks a tie *within the same protocol/AD*. True ECMP (an exact AD
  and metric tie) isn't modeled; the first route in input order wins
  arbitrarily. That's a stated scope limit, not a hidden one.
- **`has_default_route(routes)`** flags whether `0.0.0.0/0` is present at
  all.
- **`flag_high_metric_routes(routes)`** flags a route whose metric exceeds
  3x its protocol's median metric — computed per-protocol (comparing an OSPF
  cost to a BGP MED would be meaningless), skipping connected routes (metric
  is always 0) and any protocol with fewer than 2 routes (a "3x the median
  of one sample" flag can't mean anything honestly).

## How to run

```bash
python -m pytest
python run.py --report   # analyzes routing_table.txt
```

## Sample output

13 parsed routes (`results/results.json`):

```
routes parsed: 13
has default route: False
not-installed candidates: 1
metric outliers: 1
```

- `10.20.0.0/24` has both a static route (AD 1) and an OSPF route (AD 110) —
  the static route is installed; the OSPF one is reported as not-installed
  with the reason.
- No `0.0.0.0/0` route exists in the table — flagged.
- `10.60.0.0/24`'s OSPF metric of 400 is well past 3x the OSPF group's
  median (25) — flagged as worth a look.

## What this demonstrates

- Grading/analyzing routing state by actually applying the real
  administrative-distance preference rule, not by string-matching or
  guessing which protocol "looks more important."
- A stated, tested scope limit (no ECMP modeling) instead of a silent gap.
- A per-protocol statistical heuristic (median-relative outlier) that's
  careful not to fire on too little data.
