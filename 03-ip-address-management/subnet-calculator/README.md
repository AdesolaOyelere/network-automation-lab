# Subnet Calculator

> CIDR subnet math and a VLSM allocator that carves a supernet into
> right-sized subnets for a set of host-count requirements — no overlaps, no
> misalignment, and an honest report when the requirements don't fit.

**Category:** `03-ip-address-management` · **Skills:** IP addressing, VLSM, Python

## Problem

Splitting a supernet into subnets sized to what each department/segment
actually needs (VLSM — Variable Length Subnet Masking) is routine, but easy
to get subtly wrong by hand: allocate in the wrong order and a block lands on
an unaligned boundary, or under/over-provision a block relative to its stated
host requirement. It's also useful to be able to describe an arbitrary CIDR
block (network/broadcast/usable range) as its own primitive.

## Approach

`subnet_calc.py`, built on the stdlib `ipaddress` module:

- **`describe_subnet(cidr)`** reports network/broadcast/netmask/usable range
  for a single block, correctly handling the RFC 3021 edge cases (`/31`
  point-to-point has no reserved addresses; `/32` is a single host route),
  and rejects a CIDR with host bits set (`10.0.0.5/24`) rather than silently
  truncating it.
- **`required_prefix_for_hosts(hosts)`** finds the smallest prefix whose
  usable-host count covers a requirement.
- **`allocate_vlsm(supernet, requirements)`** allocates **largest-first** and
  packs blocks back-to-back from the supernet's base address. That ordering
  is what keeps every block naturally aligned with no extra bookkeeping: the
  next free address starts aligned to the supernet's own block size, and
  because block sizes only shrink (powers of two, descending), each block
  size evenly divides the previous one — so alignment is preserved at every
  step. A requirement that doesn't fit is reported in `unallocated` with a
  reason, rather than the whole run failing.

## How to run

```bash
python -m pytest
python run.py --report   # allocates requirements.json against its supernet
```

No live device, network access, or dependency beyond the Python standard
library is needed — this is pure address arithmetic.

## Sample output

`10.0.0.0/24` split across five departments (`results/results.json`):

```
supernet: 10.0.0.0/24
fits: True
  engineering  10.0.0.0/26        requested=50   available=62
  sales        10.0.0.64/27       requested=20   available=30
  guest-wifi   10.0.0.96/28       requested=10   available=14
  management   10.0.0.112/29      requested=5    available=6
  core-link    10.0.0.120/30      requested=2    available=2
```

Requested in input order (engineering, sales, guest-wifi, management,
core-link) but allocated largest-first — the output happens to match input
order here only because the input was already sorted descending by host
count; `tests/test_subnet_calc.py::test_allocate_vlsm_largest_first_ordering`
covers the case where it isn't.

## What this demonstrates

- VLSM allocation with a stated, tested correctness argument (alignment via
  largest-first packing), not just "it produced some non-overlapping
  subnets."
- Honest handling of edge cases: RFC 3021 `/31`/`/32`, host-bits-set
  rejection, and a partial-fit report instead of a crash when requirements
  exceed the supernet.
- A domain-specific tool built on the right layer (stdlib `ipaddress` for the
  primitives, custom logic only where there's real value to add).
