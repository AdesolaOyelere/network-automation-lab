"""Unit tests for MAC normalization and vendor lookup."""
import pytest
from vendors import get_oui, lookup_batch, lookup_vendor, normalize_mac


def test_normalize_mac_accepts_colon_dash_and_cisco_dot_forms():
    assert normalize_mac("00:0C:29:3A:7B:11") == "000C293A7B11"
    assert normalize_mac("00-0C-29-3A-7B-11") == "000C293A7B11"
    assert normalize_mac("000c.293a.7b11") == "000C293A7B11"


def test_normalize_mac_rejects_wrong_length():
    with pytest.raises(ValueError):
        normalize_mac("00:0C:29")


def test_normalize_mac_rejects_non_hex_characters():
    with pytest.raises(ValueError):
        normalize_mac("GG:HH:II:JJ:KK:LL")


def test_get_oui_is_first_three_octets():
    assert get_oui("000C293A7B11") == "000C29"


def test_lookup_vendor_known_oui():
    result = lookup_vendor("00:0C:29:3A:7B:11")
    assert result["vendor"] == "VMware, Inc."
    assert result["error"] is None


def test_lookup_vendor_unknown_oui_is_not_an_error():
    result = lookup_vendor("AA:BB:CC:DD:EE:FF")
    assert result["vendor"] == "Unknown vendor"
    assert result["error"] is None


def test_lookup_vendor_malformed_mac_raises():
    with pytest.raises(ValueError):
        lookup_vendor("not-a-mac")


def test_lookup_batch_isolates_malformed_entries():
    results = lookup_batch(["00:0C:29:3A:7B:11", "bad-input", "52-54-00-12-34-56"])
    assert len(results) == 3
    assert results[0]["vendor"] == "VMware, Inc."
    assert results[1]["error"] is not None
    assert results[1]["vendor"] is None
    assert results[2]["vendor"] == "QEMU/KVM virtual NIC"
