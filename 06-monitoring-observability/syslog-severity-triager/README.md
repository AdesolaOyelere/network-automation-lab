# Syslog Severity Triager

> Parse Cisco-IOS-style syslog into structured records, bucket by severity,
> and collapse a flapping interface's dozens of identical lines into one
> aggregated entry with a count — without silently merging unrelated
> recurrences of the same event.

**Category:** `06-monitoring-observability` · **Skills:** log parsing, syslog, Python

## Problem

A single flapping interface can produce dozens of identical syslog lines in
a burst, drowning out everything else in a log review. Triage needs to: (1)
parse the standard `%FACILITY-SEVERITY-MNEMONIC` format into structured
data, (2) classify by severity so critical entries aren't buried under
routine ones, and (3) collapse a repeat burst into one entry with a count,
rather than showing the same line 20 times.

## Approach

`syslog_triage.py`:

- **`parse_syslog(lines)`** matches each line against the standard format
  and returns `(records, errors)` — a malformed line or an out-of-range
  severity digit becomes an error entry, not a crash, so one bad line
  doesn't block triage of the rest.
- **`bucket(severity)`** maps 0-7 to `critical` (0-3), `warning` (4-5), or
  `info` (6-7).
- **`dedupe_and_aggregate(records)`** collapses a **consecutive run** of
  identical `(hostname, facility, mnemonic)` entries into one aggregated
  entry with `count`/`first_seen`/`last_seen`. This is deliberately
  consecutive-run collapsing, not a time-windowed dedup: if the same event
  recurs after something else was logged in between, it starts a fresh
  aggregated entry instead of merging with the earlier one. A real
  time-windowed correlator is a different, heavier tool — this one is
  honest about that limit rather than quietly approximating it.

## How to run

```bash
python -m pytest
python run.py --report   # triages the committed syslog_sample.log
```

No live device or log-shipping pipeline needed — this parses a committed
sample log.

## Sample output

26 raw lines, 25 parsed, 1 malformed (`results/results.json`):

```
raw=26 parsed=25 errors=1
aggregated entries: 16
buckets: {'critical': 15, 'warning': 7, 'info': 3}
```

The top aggregated entry is a flapping-interface burst on `dist-sw2`:
`%LINK-3-UPDOWN` for `GigabitEthernet0/3` logged 7 times in a row
(09:20:03 - 09:20:15), collapsed into one entry with `count: 7` — instead of
7 separate lines burying the rest of the log.

## What this demonstrates

- Structured log parsing with graceful, non-crashing handling of malformed
  input (a stated, tested error path, not an assumed-clean feed).
- A precisely scoped aggregation rule (consecutive-run only) with the
  limitation stated plainly rather than glossed over.
- Turning a noisy burst into one legible, countable signal — the actual
  point of triage.
