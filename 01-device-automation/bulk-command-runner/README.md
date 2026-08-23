# Bulk Command Runner

> Run one command across a device fleet, extract a specific field from each
> reply, and flag which devices have drifted from an expected baseline — the
> "which switches are NOT on the expected image" NOC report.

**Category:** `01-device-automation` · **Skills:** bulk operations, regex extraction, Python

## Problem

Checking whether a fleet is on a consistent software version means running
`show version` on every device and comparing the output — tedious by hand,
and a naive script that chokes on the first unreachable device hides exactly
the information you need (which devices you *couldn't even check*).

## Approach

`transport.py` is a mock device transport: `send_command(device, command)`
returns canned raw CLI text, or raises `ConnectionError` for an unreachable
device — the same shape and failure mode a real SSH transport has.

`bulk_runner.py`:

- **`extract_version(raw_output)`** regexes the version token out of a
  `show version`-style banner.
- **`run_bulk(devices, command, transport, extractor)`** runs the command
  across every device, catching a transport failure per-device so one
  unreachable box doesn't abort the whole run — it shows up as its own
  `reachable: False` entry instead of silently vanishing from the report.
- **`compare_to_baseline(results, baseline)`** buckets every device into
  matched / drifted / unreachable, keeping an extraction failure
  (`extracted: None`) from ever accidentally comparing equal to a real
  baseline string.

## How to run

```bash
python -m pytest
python run.py --report   # runs `show version` across the committed fleet
```

## Sample output

10-device fleet, baseline `15.2(4)E7` (`results/results.json`):

```
baseline: 15.2(4)E7
10 devices: 6 matched, 3 drifted, 1 unreachable
```

| Device | Extracted version |
|---|---|
| `sw4` | 15.0(2)SE11 |
| `sw7` | 15.0(2)SE11 |
| `sw10` | 15.2(3)E3 |

`sw9` is unreachable and reported as its own entry, not dropped from the count.

## What this demonstrates

- Per-device failure isolation in a bulk operation — a report that silently
  loses unreachable devices is a worse failure mode than a slow one.
- A concrete, tested edge case: extraction failure (`None`) must never be
  treated as a baseline match just because both are falsy-adjacent.
- The flagship real NOC task (fleet-wide version drift) built on a
  transport interface that would swap cleanly for Netmiko/NAPALM.
