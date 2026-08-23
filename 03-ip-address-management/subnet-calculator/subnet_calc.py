"""IPv4 subnet math and a VLSM allocator.

`describe_subnet` inspects a single CIDR block (network/broadcast/usable range).
`allocate_vlsm` carves a supernet into right-sized subnets for a set of
{name, hosts} requirements, using the standard VLSM convention: allocate the
largest requirement first, packing blocks back-to-back from the start of the
supernet. That convention is what keeps every allocated block naturally
aligned without any extra bookkeeping — see the note in `allocate_vlsm`.

Built on the stdlib `ipaddress` module rather than reimplementing bit
arithmetic; the value-add here is the allocation algorithm and its edge cases,
not reinventing what the standard library already gets right.
"""
from __future__ import annotations

import ipaddress


def usable_hosts(prefixlen: int) -> int:
    """Usable host addresses for an IPv4 prefix length (network/broadcast reserved,
    except the RFC 3021 special cases /31 and /32)."""
    if prefixlen == 32:
        return 1
    if prefixlen == 31:
        return 2
    return 2 ** (32 - prefixlen) - 2


def describe_subnet(cidr: str) -> dict:
    """Inspect a single CIDR block. Raises ValueError if `cidr` has host bits
    set (i.e. it's a host address, not a network address) — a common real
    mistake, and one worth catching loudly rather than silently truncating."""
    net = ipaddress.IPv4Network(cidr, strict=True)
    prefixlen = net.prefixlen
    n_usable = usable_hosts(prefixlen)
    if prefixlen >= 31:
        first_usable, last_usable = net.network_address, net.broadcast_address
    else:
        first_usable, last_usable = net.network_address + 1, net.broadcast_address - 1
    return {
        "cidr": str(net),
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "netmask": str(net.netmask),
        "prefixlen": prefixlen,
        "num_addresses": net.num_addresses,
        "num_usable_hosts": n_usable,
        "first_usable": str(first_usable),
        "last_usable": str(last_usable),
    }


def required_prefix_for_hosts(hosts: int) -> int:
    """Smallest IPv4 prefix length whose usable-host count covers `hosts`.

    Reserves a network and broadcast address (the loop never considers /31 or
    /32, since a starting point of `hosts + 2` addresses-needed is always >= 3,
    which forces a block of at least 4 addresses, i.e. /30 or larger) — so this
    always returns a prefix <= 30. VLSM allocation with /31 point-to-point
    links is out of scope here; that's a deliberate, stated limit, not an
    oversight.
    """
    if hosts < 1:
        raise ValueError(f"hosts must be >= 1, got {hosts}")
    addresses_needed = hosts + 2
    size, prefix = 1, 32
    while size < addresses_needed:
        size *= 2
        prefix -= 1
    if prefix < 0:
        raise ValueError(f"{hosts} hosts exceeds the IPv4 address space")
    return prefix


def allocate_vlsm(supernet_cidr: str, requirements: list[dict]) -> dict:
    """Carve `supernet_cidr` into subnets sized for each {name, hosts} requirement.

    Allocates largest-first (descending host count, name as a deterministic
    tiebreak) and packs blocks back-to-back from the supernet's first address.
    This ordering is what guarantees every block lands on a correctly aligned
    boundary: at each step the next free address is a multiple of the current
    block's size (true initially, since the supernet's own base address is
    aligned to its own — larger — block size), and since block sizes are
    non-increasing and all powers of two, the current block size is always a
    multiple of the next one — so the next free address stays aligned to it
    too, all the way down.

    A requirement that doesn't fit in the remaining space is reported in
    `unallocated` rather than raising, so a partial plan is still visible.
    """
    supernet = ipaddress.IPv4Network(supernet_cidr, strict=True)
    ordered = sorted(requirements, key=lambda r: (-r["hosts"], r["name"]))

    next_addr = int(supernet.network_address)
    end_addr = int(supernet.broadcast_address)
    allocations: list[dict] = []
    unallocated: list[dict] = []

    for req in ordered:
        prefix = required_prefix_for_hosts(req["hosts"])
        block_size = 1 << (32 - prefix)
        if next_addr + block_size - 1 > end_addr:
            unallocated.append({
                "name": req["name"],
                "hosts": req["hosts"],
                "reason": "insufficient space remaining in supernet",
            })
            continue
        net = ipaddress.IPv4Network((next_addr, prefix), strict=True)
        allocations.append({
            "name": req["name"],
            "cidr": str(net),
            "hosts_requested": req["hosts"],
            "hosts_available": usable_hosts(prefix),
        })
        next_addr += block_size

    return {
        "supernet": str(supernet),
        "allocations": allocations,
        "unallocated": unallocated,
        "fits": len(unallocated) == 0,
    }
