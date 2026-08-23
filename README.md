# Network Automation Lab

A working portfolio of network automation, administration, and tooling — plus the
Python that supports it. Everything here is original, open source, and reproducible.

I build the scripts, validators, and CLIs that keep a network manageable: config
automation and drift detection, IP address management, compliance auditing, topology
discovery, monitoring/log parsing, and the tooling that ties it together.

**Author:** Adesola Oyelere
**License:** MIT · **Language:** Python 3.11+

---

## What this shows

| Skill area | Where to look |
|---|---|
| Device automation (SSH/API, bulk ops) | [`01-device-automation/`](01-device-automation/) |
| Config management & drift detection | [`02-config-management/`](02-config-management/) |
| IP address management & subnetting | [`03-ip-address-management/`](03-ip-address-management/) |
| Network validation & change testing | [`04-network-validation-testing/`](04-network-validation-testing/) |
| Security & compliance auditing | [`05-security-compliance/`](05-security-compliance/) |
| Monitoring, logs & observability | [`06-monitoring-observability/`](06-monitoring-observability/) |
| Topology discovery & inventory | [`07-topology-discovery/`](07-topology-discovery/) |
| Automation frameworks & orchestration | [`08-automation-frameworks/`](08-automation-frameworks/) |
| Protocol & routing analysis | [`09-protocol-analysis/`](09-protocol-analysis/) |
| Tooling, CLIs & mini-apps | [`10-tooling/`](10-tooling/) |

The full roadmap of projects lives in [`PROJECTS.md`](PROJECTS.md).

---

## How this repo is built

Every project is self-contained and follows the same shape:

```
<category>/<project>/
  README.md      problem -> approach -> how to run -> sample output -> skill shown
  meta.json      machine-readable metadata (feeds the index)
  <code>         runnable Python, small and focused
  tests/         unit tests on the deterministic core
  results/       committed sample output so it is viewable without running anything
```

Design rules that keep the portfolio consistent:

- **Reproducible offline, no lab required.** Any project that would otherwise touch a
  real device or network sits behind a small transport/client interface with a
  deterministic mock (a virtual device with scripted command output and state), so
  tests and CI never need real hardware, a lab VM, or credentials. Real sample output
  against the mock is committed.
- **The core is pure Python and tested.** Parsing, validation, diffing, and scoring
  logic is unit-tested; the device connection is the thin, swappable part.
- **Never commit real credentials or device inventory.** Sample inventories and
  configs are synthetic (`.gitignore` also blocks common secret-shaped filenames as a
  second layer, not a substitute for care).
- **One system.** A shared README template and a metadata-driven index generator keep
  every folder looking and reading the same way.

---

## Quick start

```bash
git clone https://github.com/AdesolaOyelere/network-automation-lab
cd network-automation-lab

# dev tooling (ruff + pytest) via uv
uv sync

# run any project's tests
cd 01-device-automation/<project>
python -m pytest
```

Every project runs fully offline against its committed mock device/data by default.

---

## Rebuilding the index

Project tables in this README and `PROJECTS.md` are generated from each project's
`meta.json`:

```bash
python scripts/gen_index.py
```

<!-- INDEX:SUMMARY:START -->
**3** projects tracked · ✅ 3 done · 🔨 0 in progress · ⬜ 0 planned
<!-- INDEX:SUMMARY:END -->
