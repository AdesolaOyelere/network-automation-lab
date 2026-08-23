"""Filter a device inventory by criteria, then run a task across the filtered
set with real bounded thread-pool concurrency.

`run_task` uses a genuine `concurrent.futures.ThreadPoolExecutor` — not a
sequential loop dressed up as concurrent — so results can complete in any
order. Determinism for tests comes from two deliberate choices: the task
function must be pure (no shared mutable state), and results are sorted by
device name before being returned, so output never depends on which thread
happened to finish first.
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor


def filter_inventory(inventory: list[dict], **criteria) -> list[dict]:
    """Filter by exact match on any given field, plus a `tags` criterion that
    matches if the device has ANY of the given tags."""
    tags_filter = criteria.pop("tags", None)
    if tags_filter is not None:
        tags_filter = set(tags_filter)

    matched = []
    for device in inventory:
        if not all(device.get(key) == value for key, value in criteria.items()):
            continue
        if tags_filter is not None and not (tags_filter & set(device.get("tags", ()))):
            continue
        matched.append(device)
    return matched


def _run_one(device: dict, task_fn: Callable[[dict], object]) -> dict:
    try:
        value = task_fn(device)
    except Exception as exc:  # noqa: BLE001 - a device failure must not crash the batch
        return {"device": device["name"], "success": False, "result": None, "error": str(exc)}
    return {"device": device["name"], "success": True, "result": value, "error": None}


def run_task(devices: list[dict], task_fn: Callable[[dict], object], max_workers: int = 4) -> list[dict]:
    """Run task_fn(device) across `devices` with bounded thread-pool concurrency.
    One device's failure is captured as its own result, not raised — the batch
    always returns one entry per input device."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda d: _run_one(d, task_fn), devices))
    return sorted(results, key=lambda r: r["device"])
