# MAC Vendor Lookup

> Normalize a MAC address in any common format, pull out its OUI, and look
> it up against a small embedded vendor table — single lookups or a batch
> from a file, with malformed entries reported, not fatal.

**Category:** `10-tooling` · **Skills:** MAC addressing, CLI tooling, Python

## Problem

A MAC address shows up in colon (`AA:BB:CC:DD:EE:FF`), dash
(`AA-BB-CC-DD-EE-FF`), or Cisco dot (`aabb.ccdd.eeff`) form depending on
where you copied it from, and identifying the manufacturer from its OUI
(the first three octets) is a routine step in tracking down an unknown
device on a switch's MAC table.

## Approach

`vendors.py`:

- **`normalize_mac(mac)`** strips `:`/`-`/`.` separators and validates the
  result is exactly 12 hex digits, accepting all three common input forms.
  Raises `ValueError` with a clear message for anything malformed.
- **`lookup_vendor(mac)`** normalizes, extracts the OUI, and looks it up in
  `OUI_TABLE` — a valid MAC whose OUI isn't in the table returns
  `"Unknown vendor"` (not an error); only a malformed MAC raises.
- **`lookup_batch(macs)`** looks up many at once, isolating a malformed entry
  into its own `error` field rather than aborting the whole batch — the same
  per-item failure isolation used elsewhere in this repo
  (`bulk-command-runner`).

**On the vendor table itself:** it's a small, illustrative sample of 11
well-known OUI assignments — mostly virtualization-platform prefixes (VMware,
VirtualBox, Hyper-V, Xen, QEMU/KVM), which are exceptionally stable and
widely cited in troubleshooting references, plus a few long-standing
real-hardware ones (Cisco, Raspberry Pi, Realtek, Parallels). It is **not** a
complete or authoritative IEEE registry — for a definitive lookup, query the
IEEE OUI database directly.

## How to run

```bash
python -m pytest
python run.py --mac 00:0C:29:3A:7B:11
python run.py --batch sample_macs.txt --report
```

## Sample output

8 sample entries, mixed formats (`results/results.json`):

```
8 entries: 6 valid, 5 matched a known vendor
```

| Input | OUI | Vendor / Error |
|---|---|---|
| `00:0C:29:3A:7B:11` | 000C29 | VMware, Inc. |
| `08-00-27-4C-91-02` | 080027 | PCS Systemtechnik GmbH (Oracle VirtualBox) |
| `0015.5d3f.8a01` | 00155D | Microsoft Corporation (Hyper-V) |
| `b8:27:eb:1a:2c:3d` | B827EB | Raspberry Pi Foundation |
| `AA:BB:CC:DD:EE:FF` | AABBCC | Unknown vendor |
| `00:0c:29` | — | error: not a valid MAC address |
| `52-54-00-12-34-56` | 525400 | QEMU/KVM virtual NIC |
| `not-a-mac-address` | — | error: not a valid MAC address |

## What this demonstrates

- Format-tolerant input normalization (three real-world MAC notations) with
  a validated, tested failure mode for genuinely malformed input.
- A clean distinction between "valid but unrecognized" (`Unknown vendor`,
  not an error) and "malformed" (`ValueError`) — conflating those two would
  make the tool lie about what it actually knows.
- Batch processing that isolates per-item failures instead of letting one
  bad line abort the whole run — honest about the vendor table being a
  sample, not a claim of complete IEEE coverage.
