"""Unit tests for subnet math and the VLSM allocator.

The allocator's alignment argument (see subnet_calc.py's docstring) is the
load-bearing correctness claim, so it's checked directly — every allocated
block must be non-overlapping and each must actually satisfy strict=True
construction (which raises if the address isn't a valid network base for
that prefix, i.e. if alignment were ever violated).
"""
import ipaddress

import pytest
from subnet_calc import allocate_vlsm, describe_subnet, required_prefix_for_hosts, usable_hosts


def test_usable_hosts_standard_and_edge_prefixes():
    assert usable_hosts(24) == 254
    assert usable_hosts(30) == 2
    assert usable_hosts(31) == 2  # RFC 3021 point-to-point
    assert usable_hosts(32) == 1  # host route


def test_describe_subnet_basic():
    d = describe_subnet("192.168.1.0/24")
    assert d["network"] == "192.168.1.0"
    assert d["broadcast"] == "192.168.1.255"
    assert d["num_usable_hosts"] == 254
    assert d["first_usable"] == "192.168.1.1"
    assert d["last_usable"] == "192.168.1.254"


def test_describe_subnet_slash_31_has_no_reserved_addresses():
    d = describe_subnet("10.0.0.0/31")
    assert d["num_usable_hosts"] == 2
    assert d["first_usable"] == "10.0.0.0"
    assert d["last_usable"] == "10.0.0.1"


def test_describe_subnet_rejects_host_address_not_network_address():
    with pytest.raises(ValueError):
        describe_subnet("10.0.0.5/24")  # host bits set — not a network address


def test_required_prefix_for_hosts_matches_usable_hosts_inverse():
    for hosts, expected_prefix in [(1, 30), (2, 30), (3, 29), (6, 29), (7, 28), (50, 26), (100, 25)]:
        prefix = required_prefix_for_hosts(hosts)
        assert prefix == expected_prefix
        assert usable_hosts(prefix) >= hosts


def test_required_prefix_for_hosts_rejects_zero_or_negative():
    with pytest.raises(ValueError):
        required_prefix_for_hosts(0)
    with pytest.raises(ValueError):
        required_prefix_for_hosts(-5)


def test_allocate_vlsm_all_blocks_are_disjoint_and_within_supernet():
    requirements = [
        {"name": "a", "hosts": 50},
        {"name": "b", "hosts": 20},
        {"name": "c", "hosts": 10},
        {"name": "d", "hosts": 5},
        {"name": "e", "hosts": 2},
    ]
    result = allocate_vlsm("10.0.0.0/24", requirements)
    assert result["fits"]
    assert len(result["allocations"]) == 5

    supernet = ipaddress.IPv4Network("10.0.0.0/24")
    nets = [ipaddress.IPv4Network(a["cidr"]) for a in result["allocations"]]
    for net in nets:
        assert net.subnet_of(supernet)
    for i, a in enumerate(nets):
        for b in nets[i + 1 :]:
            assert not a.overlaps(b)


def test_allocate_vlsm_gives_each_block_enough_hosts():
    requirements = [{"name": "x", "hosts": 50}, {"name": "y", "hosts": 3}]
    result = allocate_vlsm("10.0.0.0/24", requirements)
    by_name = {a["name"]: a for a in result["allocations"]}
    assert by_name["x"]["hosts_available"] >= 50
    assert by_name["y"]["hosts_available"] >= 3


def test_allocate_vlsm_largest_first_ordering():
    # Even given in ascending order, allocation should proceed largest-first
    # (the requirement that would otherwise force misalignment for a
    # smallest-first ordering).
    requirements = [{"name": "small", "hosts": 2}, {"name": "big", "hosts": 50}]
    result = allocate_vlsm("10.0.0.0/24", requirements)
    assert [a["name"] for a in result["allocations"]] == ["big", "small"]
    assert result["allocations"][0]["cidr"] == "10.0.0.0/26"


def test_allocate_vlsm_reports_unallocated_when_supernet_too_small():
    requirements = [{"name": "huge", "hosts": 200}, {"name": "also-huge", "hosts": 200}]
    result = allocate_vlsm("10.0.0.0/24", requirements)  # /24 has only 254 usable hosts total
    assert not result["fits"]
    assert len(result["allocations"]) == 1  # the first (largest, tie broken by name) fits
    assert len(result["unallocated"]) == 1
    assert result["unallocated"][0]["reason"] == "insufficient space remaining in supernet"


def test_allocate_vlsm_rejects_host_bits_set_supernet():
    with pytest.raises(ValueError):
        allocate_vlsm("10.0.0.5/24", [{"name": "a", "hosts": 5}])
