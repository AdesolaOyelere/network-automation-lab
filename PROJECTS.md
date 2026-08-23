# Projects

The full roadmap. Target is a set of focused, self-contained projects across ten skill
areas of network automation and administration. Quality over count — nothing is
padding.

**Legend:** ✅ done · 🔨 in progress · ⬜ planned

The table below is generated from each project's `meta.json` (run
`python scripts/gen_index.py`). The checklist under it is the hand-maintained backlog.

<!-- INDEX:TABLE:START -->
| Project | Category | Status | Summary |
|---|---|---|---|
| [Bulk Command Runner](01-device-automation/bulk-command-runner/) | `01-device-automation` | ✅ | Runs one command across a device fleet via a mock transport, extracts a field with regex, and flags devices that drift from an expected baseline value. |
| [Config Template Renderer](02-config-management/config-template-renderer/) | `02-config-management` | ✅ | Render deterministic IOS-style device configurations from reusable text templates and validated structured JSON data. |
| [Golden Config Drift Detector](02-config-management/golden-config-drift-detector/) | `02-config-management` | ✅ | Compare mocked device running configuration against a golden baseline and report normalized missing, unexpected, and changed configuration. |
| [Subnet Calculator](03-ip-address-management/subnet-calculator/) | `03-ip-address-management` | ✅ | CIDR subnet math and a VLSM allocator that carves a supernet into subnets sized to host-count requirements without overlap, allocating largest-first to keep every block naturally aligned. |
| [Reachability Matrix Tester](04-network-validation-testing/reachability-matrix-tester/) | `04-network-validation-testing` | ✅ | Tests a declared reachability intent matrix against actual ACL evaluation order, reporting violations (intent and policy disagree) and honestly flagging subnet-level queries a rule only partially covers. |
| [ACL Rule Auditor](05-security-compliance/acl-rule-auditor/) | `05-security-compliance` | ✅ | Audit mocked device ACLs for overly permissive, shadowed, and unused rules using structural network and service matching. |
| [Syslog Severity Triager](06-monitoring-observability/syslog-severity-triager/) | `06-monitoring-observability` | ✅ | Parses Cisco-IOS-style syslog lines into structured records, buckets them by severity, and collapses consecutive repeats (e.g. a flapping interface) into aggregated counts. |
| [Topology Graph Builder](07-topology-discovery/topology-graph-builder/) | `07-topology-discovery` | ✅ | Builds an undirected adjacency graph from LLDP/CDP-style neighbor records, finds isolated components, and locates articulation points (Tarjan's algorithm) that are single points of failure. |
| [Inventory-Driven Task Runner](08-automation-frameworks/inventory-driven-task-runner/) | `08-automation-frameworks` | ✅ | Filters a device inventory by field/tag criteria and runs a task across the filtered set with real bounded thread-pool concurrency, isolating per-device failures. |
| [MAC Address Table Analyzer](09-protocol-analysis/mac-address-table-analyzer/) | `09-protocol-analysis` | ✅ | Parses per-switch MAC address tables and detects MAC flapping — the same MAC address learned on different ports within a short window, a sign of a loop or spoofing. |
| [MAC Vendor Lookup](10-tooling/mac-vendor-lookup/) | `10-tooling` | ✅ | Normalizes a MAC address in any common format, extracts its OUI, and looks it up against a small embedded vendor table. |
<!-- INDEX:TABLE:END -->

---

## Backlog

### 01 · Device Automation

- ⬜ `ssh-config-pusher` — push config snippets to a mocked multi-vendor device over SSH
- ✅ `bulk-command-runner` — run a show/config command across many devices, aggregate results
- ⬜ `config-backup-scheduler` — pull and version running-configs on a schedule
- ⬜ `multi-vendor-cli-abstraction` — normalize IOS/Junos/EOS command syntax behind one interface
- ⬜ `interface-bounce-automation` — safely shut/no-shut interfaces with pre/post state checks
- ⬜ `firmware-upgrade-orchestrator` — staged upgrade workflow with rollback on health-check failure
- ⬜ `credential-vault-integration` — pull device creds from a mocked secrets store, never hardcoded

### 02 · Config Management

- ✅ `golden-config-drift-detector` — diff running config against a golden template, flag drift
- ✅ `config-template-renderer` — templating engine for device configs from structured data
- ⬜ `config-rollback-manager` — snapshot + rollback with a safe-apply diff preview
- ⬜ `acl-diff-tool` — structural diff of ACL rule sets, order-aware
- ⬜ `vlan-consistency-checker` — cross-device VLAN definition consistency audit
- ⬜ `config-linter` — static checks for common config mistakes (dup IPs, missing descriptions)
- ⬜ `multi-vendor-config-normalizer` — parse vendor-specific config into one normalized model

### 03 · IP Address Management

- ✅ `subnet-calculator` — CIDR/VLSM subnetting calculator with a supernet/host-count solver
- ⬜ `ip-allocation-tracker` — track subnet allocations, detect overlaps, find free blocks
- ⬜ `vlsm-planner` — allocate variable-length subnets to satisfy host-count requirements
- ⬜ `dhcp-scope-auditor` — detect DHCP scope overlaps and exhaustion risk
- ⬜ `ipam-import-export` — normalize IPAM data between CSV/JSON/YAML formats
- ⬜ `dns-ptr-consistency-checker` — forward/reverse DNS consistency audit for a subnet
- ⬜ `ip-conflict-scanner` — detect duplicate/conflicting static IP assignments from inventory

### 04 · Network Validation & Testing

- ⬜ `pre-post-change-validator` — snapshot device state before/after a change, diff and flag regressions
- ✅ `reachability-matrix-tester` — test expected reachability between subnets against ACL/routing rules
- ⬜ `config-intent-checker` — assert a config satisfies a declared intent (e.g. "port X = access vlan Y")
- ⬜ `change-window-risk-scorer` — score a planned change's blast radius from the topology graph
- ⬜ `synthetic-traffic-test-harness` — scripted ping/traceroute-style checks against a mock topology
- ⬜ `rollback-safety-verifier` — verify a rollback config actually restores prior state exactly
- ⬜ `maintenance-window-scheduler` — conflict-check overlapping maintenance windows across devices

### 05 · Security & Compliance

- ✅ `acl-rule-auditor` — flag overly permissive ACL rules (any-any, unused, shadowed)
- ⬜ `cis-benchmark-checker` — check device config against a CIS-style hardening benchmark subset
- ⬜ `password-policy-auditor` — audit local user/auth config against a password/complexity policy
- ⬜ `unused-rule-detector` — find ACL/firewall rules with zero recent hit-count (from mock logs)
- ⬜ `port-exposure-scanner` — flag management-plane services exposed on the wrong interface
- ⬜ `ssh-hardening-checker` — verify SSH config (version, ciphers, timeouts) against a baseline
- ⬜ `change-approval-audit-trail` — verify every applied config change has a linked approval record

### 06 · Monitoring & Observability

- ✅ `syslog-severity-triager` — parse syslog streams, classify severity, dedupe/aggregate repeats
- ⬜ `snmp-threshold-alerter` — evaluate polled metrics against thresholds, alert with hysteresis
- ⬜ `interface-flap-detector` — detect flapping interfaces from a state-change log
- ⬜ `netflow-top-talkers` — summarize top talkers/conversations from mock flow records
- ⬜ `log-anomaly-baseline` — build a baseline log-rate profile and flag deviations
- ⬜ `alert-dedup-and-correlation` — correlate related alerts from multiple devices into one incident
- ⬜ `capacity-trend-reporter` — trend interface utilization and project time-to-exhaustion

### 07 · Topology Discovery

- ⬜ `lldp-cdp-neighbor-parser` — parse neighbor discovery output into a normalized adjacency list
- ✅ `topology-graph-builder` — build a network graph from discovered adjacencies, detect loops/islands
- ⬜ `inventory-auto-generator` — generate a device inventory from discovery output
- ⬜ `single-point-of-failure-finder` — find topology cut-vertices (graph articulation points)
- ⬜ `vlan-topology-mapper` — map VLAN presence across the discovered topology
- ⬜ `path-trace-simulator` — compute the expected forwarding path between two hosts over the graph
- ⬜ `topology-diff-over-time` — diff two topology snapshots to show what changed

### 08 · Automation Frameworks

- ✅ `inventory-driven-task-runner` — run a task function across a filtered device inventory
- ⬜ `idempotent-playbook-engine` — apply declarative desired-state configs idempotently
- ⬜ `task-retry-and-backoff` — retry policy wrapper for flaky device operations
- ⬜ `parallel-execution-throttler` — bounded-concurrency executor for bulk device operations
- ⬜ `dry-run-diff-preview` — compute and show the diff a playbook *would* apply, without applying it
- ⬜ `inventory-group-resolver` — resolve nested device groups/tags into a flat execution set
- ⬜ `execution-audit-logger` — structured, replayable log of every automation run

### 09 · Protocol & Routing Analysis

- ⬜ `routing-table-analyzer` — parse a routing table dump, find suboptimal/missing routes
- ⬜ `bgp-state-parser` — parse BGP neighbor/session state, flag down or flapping sessions
- ⬜ `ospf-adjacency-checker` — verify OSPF adjacency state matches expected topology
- ✅ `mac-address-table-analyzer` — parse MAC tables, detect MAC flapping across ports
- ⬜ `packet-capture-summarizer` — summarize a pcap-like log into protocol/conversation stats
- ⬜ `arp-table-consistency-checker` — cross-device ARP table consistency audit
- ⬜ `route-flap-damping-simulator` — simulate route flap damping behavior over an event stream

### 10 · Tooling, CLIs & Mini-Apps

- ⬜ `subnet-calculator-cli` — CLI wrapper for the subnetting core
- ⬜ `config-backup-cli` — CLI to snapshot and version device configs to local storage
- ✅ `mac-vendor-lookup` — OUI-prefix to vendor lookup CLI from a local table
- ⬜ `port-scan-lite` — authorized, rate-limited TCP reachability checker for owned/lab hosts
- ⬜ `inventory-validator-cli` — validate an inventory file against a schema before automation runs
- ⬜ `config-diff-cli` — side-by-side config diff viewer
- ⬜ `report-generator` — assemble a markdown/HTML report from any project's JSON results
