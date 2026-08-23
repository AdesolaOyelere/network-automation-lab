# Golden Config Drift Detector

> Compares normalized running configuration from a deterministic mock device
> against a golden baseline and classifies semantic drift.

**Category:** `02-config-management` · **Skills:** configuration normalization, drift detection, mock transports, Python

## Problem

Raw text diffs are noisy: timestamps and comments change without affecting intent,
while a value change often appears as two unrelated removed/added lines. Engineers
need a concise report that preserves interface and routing-process context.

## Approach

`transport.py` defines the device boundary. The deterministic mock loads synthetic
running configuration, returns it for `show running-config`, and records collection
calls. No real device or network connection is made.

`drift_detector.py` removes blank, comment, duplicate, and explicitly volatile
lines; associates child commands with their interface or routing context; and gives
mutually exclusive settings such as descriptions, IP addresses, and helper
addresses stable keys. It then classifies drift as:

- **changed** when the same setting has a different value;
- **missing** when a golden statement is absent;
- **unexpected** when the running configuration adds a statement.

The focused parser targets hierarchical IOS-style text. Vendor-specific grammar,
secrets, and automatic remediation are intentionally out of scope.

## How to run

```bash
python3 -m pytest
python3 run.py --report
```

Both commands work fully offline with the committed synthetic fixture. The runner
writes reproducible JSON output and, with `--report`, a Markdown report.

## Sample output

The executed mock audit produced:

```text
device: branch-rtr-01
in sync: False
  changed    2
  missing    0
  unexpected 5
```

The two changes are a WAN description and DHCP helper-address value. The five
unexpected statements represent a temporary interface and an extra OSPF network;
the complete executed result is under `results/`.

## What this demonstrates

- Separation of configuration collection from deterministic comparison logic.
- Context-aware normalization and semantic pairing of changed settings.
- Edge-case tests plus an end-to-end regression pinned to committed real output.
