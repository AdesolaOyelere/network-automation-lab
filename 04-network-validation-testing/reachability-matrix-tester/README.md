# Reachability Matrix Tester

> Test a declared reachability intent matrix ("engineering should reach the
> servers over tcp", "guest wifi should not") against how an ACL actually
> evaluates — and flag it honestly when a subnet-level query isn't fully
> covered by a single rule, instead of guessing.

**Category:** `04-network-validation-testing` · **Skills:** network validation, ACL evaluation, Python

## Problem

A network design has *declared intent* — which subnets should reach which,
over which protocol — and an ACL that's supposed to implement it. The two
drift apart: a broad catch-all rule can accidentally permit traffic a
narrower, more specific intent meant to deny. Manually reading an ACL
top-to-bottom to check every declared intent doesn't scale and misses this
kind of gap.

This is scoped to L3: protocol plus source/destination subnet. L4 ports are
out of scope.

## Approach

`reachability.py`:

- **`evaluate_acl(rules, protocol, src, dst)`** walks the ACL in `sequence`
  order (first match wins, same as a real ACL) and returns the verdict for a
  *subnet-to-subnet* query. Because the query is a whole subnet, not a
  single host, a rule only gives a clean answer if its source **and**
  destination ranges each fully cover the queried subnet
  (`ipaddress`-based containment). If a rule's range only partially overlaps
  the query, part of that subnet's traffic would match and part wouldn't —
  reported as `mixed` rather than picking a side.
- `"any"` is a wildcard only on the **rule** side, matching standard ACL
  semantics. A query's protocol is expected to be concrete; passing `"any"`
  as a query protocol does not silently match every rule regardless of its
  declared protocol — that would answer a different, broader question (do
  *all* protocols agree?) than what was asked.
- **`evaluate_intent(intent, rules)`** compares each declared
  `{src, dst, protocol, expected}` entry's actual ACL verdict against its
  expectation: `pass`, `violation` (they disagree), or `ambiguous` (the
  query hit a partially-covering rule).

## How to run

```bash
python -m pytest
python run.py --report   # tests the committed intent matrix against policy.json
```

No live device or network access needed — this evaluates a committed ACL and
intent matrix.

## Sample output

5 declared intents against a 4-rule ACL (`results/results.json`):

```
{"total": 5, "pass": 3, "violation": 1, "ambiguous": 1}
```

| Intent | Expected | Verdict | Status | Reason |
|---|---|---|---|---|
| `engineering-to-servers-tcp` | permit | permit | pass | — |
| `guest-to-servers-blocked` | deny | deny | pass | — |
| `unlisted-subnet-should-be-denied` | deny | permit | **violation** | — |
| `engineering-to-specific-server-tcp` | permit | permit | pass | — |
| `broad-engineering-supernet-query` | permit | mixed | ambiguous | rule 10 only partially overlaps the queried range |

The violation is the real find: a broad `permit any 10.20.0.0/16 ->
10.20.0.0/24` catch-all rule (meant to cover general corporate traffic to
the server subnet) accidentally permits a subnet the design explicitly
intended to keep denied — exactly the kind of drift this tool exists to
catch. The `ambiguous` row is querying reachability for a `/23` supernet
that only half-overlaps the `/24` a specific rule was written for; the tool
says so plainly instead of guessing which half's answer to report.

## What this demonstrates

- Turning an ACL's evaluation order into a testable pass/violation report
  against declared intent, catching a real class of "the broad rule quietly
  overrides the narrow one" policy drift.
- Honest handling of the containment edge case a naive subnet-vs-subnet
  overlap check would get wrong (partial overlap is not full overlap) rather
  than silently reporting a possibly-incorrect verdict for half the queried
  range.
- A caught, real bug worth naming: the first draft treated a query's
  `protocol: "any"` as a wildcard on *both* sides, and a hand-picked test
  fixture used an invalid CIDR (`10.0.1.0/23`, which has host bits set) —
  both were caught by actually running the code, not by review.
