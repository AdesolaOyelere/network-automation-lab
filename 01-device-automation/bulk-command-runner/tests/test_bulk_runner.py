"""Unit tests for extraction, bulk execution, and baseline comparison."""
from bulk_runner import compare_to_baseline, extract_version, run_bulk
from transport import MockTransport


def test_extract_version_strips_trailing_comma():
    raw = "Cisco IOS Software, C2960X Software, Version 15.2(4)E7, RELEASE SOFTWARE (fc3)"
    assert extract_version(raw) == "15.2(4)E7"


def test_extract_version_missing_returns_none():
    assert extract_version("no version token in here") is None


def test_run_bulk_reports_unreachable_device_without_dropping_it():
    fixtures = {"a": {"cmd": "Version 1.0,"}}
    transport = MockTransport(fixtures, unreachable={"b"})
    results = run_bulk(["a", "b"], "cmd", transport)
    assert len(results) == 2
    by_device = {r["device"]: r for r in results}
    assert by_device["a"]["reachable"] and by_device["a"]["extracted"] == "1.0"
    assert not by_device["b"]["reachable"]
    assert by_device["b"]["error"] is not None
    assert by_device["b"]["extracted"] is None


def test_run_bulk_missing_fixture_entry_is_also_unreachable():
    transport = MockTransport(fixtures={}, unreachable=set())
    results = run_bulk(["ghost"], "cmd", transport)
    assert not results[0]["reachable"]


def test_compare_to_baseline_buckets_correctly():
    results = [
        {"device": "a", "reachable": True, "extracted": "1.0", "raw_output": "x", "error": None},
        {"device": "b", "reachable": True, "extracted": "2.0", "raw_output": "x", "error": None},
        {"device": "c", "reachable": False, "extracted": None, "raw_output": None, "error": "down"},
    ]
    summary = compare_to_baseline(results, baseline="1.0")
    assert summary["n_matched"] == 1 and summary["matched"] == ["a"]
    assert summary["n_drifted"] == 1 and summary["drifted"] == [{"device": "b", "extracted": "2.0"}]
    assert summary["n_unreachable"] == 1 and summary["unreachable"] == ["c"]


def test_compare_to_baseline_extraction_failure_counts_as_drift_not_match():
    # extracted=None (regex found nothing) must never accidentally equal a real baseline string
    results = [{"device": "a", "reachable": True, "extracted": None, "raw_output": "x", "error": None}]
    summary = compare_to_baseline(results, baseline="1.0")
    assert summary["n_drifted"] == 1
    assert summary["drifted"][0]["extracted"] is None
