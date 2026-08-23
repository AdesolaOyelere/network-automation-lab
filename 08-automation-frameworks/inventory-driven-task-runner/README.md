# Inventory-Driven Task Runner

> Filter a device inventory by field or tag, then run a task across the
> filtered set with real bounded thread-pool concurrency — one unreachable
> device fails on its own, without dropping or blocking the rest.

**Category:** `08-automation-frameworks` · **Skills:** automation framework, concurrency, Python

## Problem

Bulk operations (pull a version, push a command) need to run against a
*subset* of the fleet selected by criteria like site, role, or tag — and
they need real concurrency, not one device at a time, or a large fleet takes
forever. But concurrency raises its own problem: one device timing out or
erroring must not crash the batch or silently drop from the results.

## Approach

- **`filter_inventory(inventory, **criteria)`** in `task_runner.py` matches
  exact fields (`site="nyc"`) and a `tags` criterion that matches if the
  device has *any* of the given tags — both combine as AND.
- **`run_task(devices, task_fn, max_workers)`** runs `task_fn` across the
  filtered devices with a real `concurrent.futures.ThreadPoolExecutor`, not
  a sequential loop pretending to be concurrent. Each call is wrapped so an
  exception becomes `{success: False, error: str(exc)}` instead of
  propagating and aborting the batch — every input device gets exactly one
  output entry. Results are sorted by device name before returning, so
  output is identical run to run regardless of which thread happens to
  finish first (verified directly, not assumed).
- **`transport.py`** is the mock device layer: a canned per-device version
  table, with one device deliberately absent to simulate an unreachable
  device raising `DeviceUnreachable`.

## How to run

```bash
python -m pytest
python run.py --report   # runs get_version across the prod-tagged inventory
```

No live device or network access needed — `transport.py` is a canned mock.

## Sample output

8-device inventory, filtered to the 7 tagged `prod` (`results/results.json`):

```
inventory=8 filtered=7 success=6/7
```

`sfo-edge1` is deliberately unreachable in the mock transport; its result
entry is `{"success": false, "error": "sfo-edge1: connection timed out"}` —
present in the output, not missing — while the other 6 devices' results are
unaffected.

## What this demonstrates

- Real thread-pool concurrency, not a sequential loop dressed up as
  concurrent — and a test that proves determinism despite genuine
  multithreading (two runs, identical sorted output) rather than assuming it.
- Per-device failure isolation: one bad device becomes a `success: False`
  entry, not a crashed batch or a silently missing result.
- Flexible inventory filtering (exact-field AND tag-membership) as the entry
  point most automation frameworks (Nornir, Ansible) actually use.
