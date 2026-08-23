"""Unit tests for inventory filtering and the thread-pool task runner."""
from task_runner import filter_inventory, run_task
from transport import get_version

INVENTORY = [
    {"name": "a", "site": "nyc", "role": "core", "tags": ["core", "prod"]},
    {"name": "b", "site": "nyc", "role": "edge", "tags": ["prod", "edge"]},
    {"name": "c", "site": "sfo", "role": "core", "tags": ["core", "prod"]},
    {"name": "d", "site": "sfo", "role": "edge", "tags": ["lab"]},
]


def test_filter_by_exact_field():
    assert [d["name"] for d in filter_inventory(INVENTORY, site="nyc")] == ["a", "b"]
    assert [d["name"] for d in filter_inventory(INVENTORY, role="core")] == ["a", "c"]


def test_filter_by_multiple_exact_fields_is_and():
    assert [d["name"] for d in filter_inventory(INVENTORY, site="sfo", role="core")] == ["c"]


def test_filter_by_tags_matches_any_given_tag():
    assert [d["name"] for d in filter_inventory(INVENTORY, tags=["lab"])] == ["d"]
    assert [d["name"] for d in filter_inventory(INVENTORY, tags=["core", "lab"])] == ["a", "c", "d"]


def test_filter_combines_field_and_tag_criteria():
    result = filter_inventory(INVENTORY, site="nyc", tags=["prod"])
    assert [d["name"] for d in result] == ["a", "b"]


def test_filter_no_match_returns_empty():
    assert filter_inventory(INVENTORY, site="lon") == []


def test_run_task_isolates_a_single_device_failure():
    def flaky(device):
        if device["name"] == "b":
            raise RuntimeError("boom")
        return f"ok-{device['name']}"

    results = run_task(INVENTORY, flaky)
    assert len(results) == 4  # every device gets an entry, none dropped
    by_name = {r["device"]: r for r in results}
    assert by_name["b"]["success"] is False
    assert by_name["b"]["error"] == "boom"
    assert by_name["a"]["success"] is True
    assert by_name["a"]["result"] == "ok-a"


def test_run_task_results_are_sorted_by_device_name():
    results = run_task(list(reversed(INVENTORY)), lambda d: d["name"])
    assert [r["device"] for r in results] == ["a", "b", "c", "d"]


def test_run_task_is_deterministic_across_repeated_runs():
    r1 = run_task(INVENTORY, lambda d: d["name"], max_workers=8)
    r2 = run_task(INVENTORY, lambda d: d["name"], max_workers=8)
    assert r1 == r2


def test_get_version_raises_for_unreachable_device():
    import pytest
    from transport import DeviceUnreachable

    with pytest.raises(DeviceUnreachable):
        get_version({"name": "no-such-device"})


def test_get_version_returns_string_for_known_device():
    assert isinstance(get_version({"name": "nyc-core1"}), str)
