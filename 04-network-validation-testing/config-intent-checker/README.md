# Config Intent Checker

> Parse hierarchical device config into a structured block model and check
> declarative intents against it — "is `Gi0/1` actually in access mode on
> VLAN 20," not just "does this line of text exist somewhere."

**Category:** `04-network-validation-testing` · **Skills:** config validation, parsing, Python

## Problem

Checking a specific structural fact about a device's config — "is this
interface in access mode, and is it on the right VLAN" — needs to know which
sub-lines belong to which interface block, not just whether some line exists
anywhere in the file. `golden-config-drift-detector` (elsewhere in this
repo) treats config as a flat line multiset, which is right for "did
anything change" but wrong for this: two different interfaces can share an
identical sub-line (`switchport mode access`), and a flat diff can't tell
you *which* interface has the problem.

## Approach

`intent_checker.py`:

- **`parse_config(text)`** builds a block model: each non-indented
  ("top-level") line owns the indented lines that follow it, up to the next
  top-level line. Blank lines are skipped.
- **`interface_access_vlan`** intents (`{interface, vlan}`) find that
  interface's block, confirm it's in access mode (not trunk), and confirm
  its `switchport access vlan` sub-line matches — with a distinct failure
  reason for each way it can fail: interface not found, not in access mode,
  no VLAN configured at all, or the wrong VLAN.
- **`line_present`** intents (`{pattern}`) check whether any *top-level* line
  matches a regex — deliberately not sub-lines, since a sub-line's meaning
  depends on which block it's under.

## How to run

```bash
python -m pytest
python run.py --report   # checks intents.json against device_config.txt
```

## Sample output

8 intents against a 3-interface device config (`results/results.json`):

```
4/8 intents passed
```

| Intent | Passed | Reason |
|---|---|---|
| `Gi0/1` access vlan 20 | True | — |
| `Gi0/3` access vlan 30 | True | — |
| `Gi0/3` access vlan 10 | False | found switchport access vlan 30, expected 10 |
| `Gi0/2` access vlan 10 | False | interface GigabitEthernet0/2 is not in access mode |
| `Gi0/9` access vlan 5 | False | interface GigabitEthernet0/9 not found in config |
| hostname line present | True | — |
| domain-name line present | True | — |
| ntp server line present | False | no line matching pattern found |

## What this demonstrates

- Structural (block-aware) config checking as a distinct, complementary
  technique to flat-line diffing — same repo, deliberately different
  approach, applied where the block structure actually matters.
- Every failure mode returns a specific, actionable reason instead of a bare
  `False` — the difference between a checker and a checker you can actually
  use to fix something.
- A test set that's honestly mixed (4 pass, 4 fail across all four distinct
  failure reasons) rather than a dataset where everything trivially passes.
