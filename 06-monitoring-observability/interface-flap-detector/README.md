# Interface Flap Detector

> Detect flapping interfaces with a real sliding time-window transition
> counter — six state changes in forty seconds is a problem; six spread
> across three hours isn't the same thing, even though the raw count is
> identical.

**Category:** `06-monitoring-observability` · **Skills:** monitoring, sliding-window algorithms, Python

## Problem

An interface state-change log is chronological but interleaved across every
device and interface in the fleet, not grouped. Counting "how many
transitions did this interface have" is easy and also the wrong question —
what actually matters operationally is whether those transitions *clustered*
within a short window, which needs real windowing logic, not a total count.

## Approach

`interface_flap.py`:

- **`max_transitions_in_window(timestamps, window_seconds)`** — a sliding
  two-pointer scan over one interface's sorted event timestamps, returning
  the largest number of transitions found inside any window of that width.
- **`detect_flapping(events, window_seconds=60, threshold=4)`** groups the
  interleaved log by (device, interface), then flags an interface as
  flapping only if its max-in-window count exceeds `threshold` — the
  defaults are a reasonable illustrative threshold for this dataset, not an
  asserted industry standard.
- **`compute_uptime(events)`** computes each interface's uptime % over the
  observed period (the min/max event timestamp across the *entire* log, not
  just that interface's own events), assuming each interface was `up` before
  its first logged event — a stated assumption, not a claim of ground truth
  from before the log started. A real edge case worth knowing: if an
  interface's own events happen to define the observed period exactly (i.e.
  it's the only interface in the log, or its own down->up bracket coincides
  with the log's start/end), uptime can come out to 0% for what looks like a
  brief blip — because it's being measured against an observation window
  that IS that blip. `tests/test_interface_flap.py` covers this directly.

## How to run

```bash
python -m pytest
python run.py --report   # analyzes events.json with the default window/threshold
```

## Sample output

4 interfaces, 16 interleaved events (`results/results.json`):

```
4 interfaces, 1 flapping
```

| Device | Interface | Transitions | Max in window | Flapping | Uptime |
|---|---|---|---|---|---|
| sw1 | Gi0/1 | 2 | 2 | False | 99.97% |
| sw1 | Gi0/4 | 6 | 2 | False | 99.90% |
| sw2 | Gi0/3 | 6 | 6 | **True** | 99.84% |
| sw3 | Gi0/1 | 2 | 1 | False | 94.12% |

`sw1/Gi0/4` and `sw2/Gi0/3` have the **same** total transition count (6) —
only `Gi0/3` flags, because its six transitions land inside one 40-second
span instead of being spread across three hours. And `Gi0/3` is flapping
despite having *higher* uptime than the non-flapping `sw3/Gi0/1` — flapping
is about instability/frequency, not total downtime, and a fast-flapping link
can look fine on an uptime dashboard while still being an active problem.

## What this demonstrates

- Real sliding-window logic (not a total-count shortcut), with a direct test
  proving identical transition counts produce different flapping verdicts
  depending on clustering.
- A stated modeling assumption (pre-log state) instead of a silently implied
  one, plus a documented edge case in the uptime metric found by actually
  running the code — not asserted from a hand-computed guess, which was
  wrong on the first attempt here.
- Two complementary metrics (flap frequency vs. total uptime) that can and
  do disagree, which is itself the operationally useful insight.
