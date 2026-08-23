# ACL Rule Auditor

> Audits structured ACLs from a deterministic mock device for overly permissive,
> shadowed, and unused rules.

**Category:** `05-security-compliance` · **Skills:** ACL analysis, security auditing, mock transports, Python

## Problem

Long ACLs accumulate broad exceptions, unreachable entries, and permits that no
longer receive traffic. Text diffs alone miss the packet-matching relationships
that make those rules risky or redundant.

## Approach

`transport.py` defines a minimal read-only device interface. Its deterministic
mock returns synthetic structured ACL output and records commands, so the project
never connects to real equipment. `acl_auditor.py` validates every rule, compares
IPv4 network containment plus protocol and destination-port scope, and reports:

- permit any/any rules as critical;
- rules fully covered by an earlier rule as shadowed, distinguishing same-action
  redundancy from conflicting actions;
- zero-hit permit rules whose last hit meets a configurable age threshold.

This intentionally models IPv4 ACLs with a single destination port. Port ranges,
object groups, IPv6, and live device parsing are outside this focused example.

## How to run

```bash
python3 -m pytest
python3 run.py --report
```

Everything runs offline using `mock_device.json`; no hardware, VPN, credentials,
or network access is used. JSON and Markdown output are written under `results/`.

## Sample output

The committed mock run inspected 2 ACLs and 7 rules:

```text
device: edge-fw-01
acls: 2  rules: 7
findings: 5
  any-any-permit   1
  shadowed         2
  unused           2
```

The five detailed findings and their severities are committed in
`results/results.json` and `results/results.md`.

## What this demonstrates

- A device boundary that can later accept a vendor adapter without coupling
  transport concerns to audit policy.
- Structural ACL analysis using address containment, protocol, port, ordering,
  action, and hit-count age.
- Defensive validation, focused edge-case tests, and a reproducible end-to-end
  result pinned to a deterministic synthetic fixture.
