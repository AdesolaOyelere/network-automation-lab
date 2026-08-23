"""Unit tests for syslog parsing, bucketing, and consecutive-run aggregation."""
from syslog_triage import bucket, dedupe_and_aggregate, parse_syslog, triage


def test_parse_single_valid_line():
    records, errors = parse_syslog([
        "Jan 15 09:20:03 dist-sw2 %LINK-3-UPDOWN: Interface GigabitEthernet0/3, changed state to down"
    ])
    assert errors == []
    assert len(records) == 1
    r = records[0]
    assert r["hostname"] == "dist-sw2"
    assert r["facility"] == "LINK"
    assert r["severity"] == 3
    assert r["severity_name"] == "error"
    assert r["mnemonic"] == "UPDOWN"
    assert r["message"] == "Interface GigabitEthernet0/3, changed state to down"


def test_malformed_line_becomes_a_parse_error_not_a_crash():
    records, errors = parse_syslog(["not a syslog line"])
    assert records == []
    assert len(errors) == 1
    assert errors[0]["line"] == "not a syslog line"


def test_out_of_range_severity_is_a_parse_error():
    records, errors = parse_syslog(["Jan 15 09:00:00 host1 %SYS-9-FOO: bad severity digit"])
    assert records == []
    assert len(errors) == 1
    assert "out of range" in errors[0]["reason"]


def test_bucket_boundaries():
    assert bucket(0) == "critical"
    assert bucket(3) == "critical"
    assert bucket(4) == "warning"
    assert bucket(5) == "warning"
    assert bucket(6) == "info"
    assert bucket(7) == "info"


def test_dedupe_collapses_only_consecutive_runs():
    lines = [
        "Jan 15 09:00:00 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:01 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:02 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:03 sw1 %SYS-6-OTHER: unrelated",
        "Jan 15 09:00:04 sw1 %LINK-3-UPDOWN: if down",  # same triple again, but not consecutive
    ]
    records, _ = parse_syslog(lines)
    aggregated = dedupe_and_aggregate(records)
    # 3-run, then the unrelated entry, then a fresh (non-merged) 4th UPDOWN entry
    assert len(aggregated) == 3
    assert aggregated[0]["count"] == 3
    assert aggregated[0]["first_seen"] == "Jan 15 09:00:00"
    assert aggregated[0]["last_seen"] == "Jan 15 09:00:02"
    assert aggregated[1]["mnemonic"] == "OTHER"
    assert aggregated[1]["count"] == 1
    assert aggregated[2]["mnemonic"] == "UPDOWN"
    assert aggregated[2]["count"] == 1  # not merged with the earlier run


def test_dedupe_requires_all_three_fields_to_match():
    lines = [
        "Jan 15 09:00:00 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:01 sw2 %LINK-3-UPDOWN: if down",  # different hostname
    ]
    records, _ = parse_syslog(lines)
    aggregated = dedupe_and_aggregate(records)
    assert len(aggregated) == 2


def test_triage_end_to_end_buckets_by_aggregated_count():
    lines = [
        "Jan 15 09:00:00 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:01 sw1 %LINK-3-UPDOWN: if down",
        "Jan 15 09:00:02 sw1 %SYS-6-OK: fine",
    ]
    result = triage(lines)
    assert result["n_raw_lines"] == 3
    assert result["n_parsed"] == 3
    assert result["n_parse_errors"] == 0
    assert result["buckets"] == {"critical": 2, "warning": 0, "info": 1}
    assert result["top_entries"][0]["count"] == 2
