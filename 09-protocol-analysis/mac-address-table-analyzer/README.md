# MAC Address Table Analyzer

> Parse `show mac address-table`-style output from successive polls and
> detect MAC flapping — the same MAC learned on a different port within a
> short window, a classic sign of a bridging loop or a spoofed source MAC —
> without flagging a host that legitimately moved hours later.

**Category:** `09-protocol-analysis` · **Skills:** MAC table parsing, protocol analysis, Python

## Problem

A single MAC table snapshot can't show flapping — that's a change *over
time*. The real signal comes from polling the table repeatedly and diffing
consecutive observations per MAC: if the same address shows up on a
different port again within seconds, that's a loop or spoofing, not normal
network activity. But a host genuinely moved to a new port hours later looks
identical at the row level (same MAC, different port) and must not be
flagged the same way.

## Approach

`mac_table.py`:

- **`parse_mac_table(text, switch, timestamp)`** parses one poll's raw
  `Vlan / Mac Address / Type / Ports` table text into flat entries, skipping
  header and separator lines that don't match the row shape.
- **`detect_flapping(entries, window_seconds)`** groups entries by
  `(switch, vlan, mac)`, sorts each group by timestamp, and flags a
  consecutive port change only if the two observations fall within
  `window_seconds` of each other. A port change that happens well outside
  the window is a legitimate move and is deliberately not reported.

## How to run

```bash
python -m pytest
python run.py --report   # analyzes the committed 3-poll dataset (60s window)
```

No live device or SNMP polling infrastructure needed — this parses committed
poll text.

## Sample output

3 polls of `dist-sw1`, 9 entries total, 60-second flap window
(`results/results.json`):

```
entries=9 flaps=1
  dist-sw1 0011.2233.4455 Gi1/0/5 -> Gi1/0/7 in 15s
```

The dataset has two MACs that change ports across the polls, but only one is
a real flap: `0011.2233.4455` moves from `Gi1/0/5` to `Gi1/0/7` 15 seconds
apart (flagged). Two hours later it's seen back on `Gi1/0/5`, and a second
MAC (`0011.2233.4466`) moves to a new port in that same later poll — both of
those are outside the 60-second window and correctly not flagged, since
that's what a normal, slow relocation looks like rather than a loop.

## What this demonstrates

- Recognizing that flapping is inherently a time-series question, not
  something a single table snapshot can answer, and designing the input
  shape (a poll history, not one table) around that.
- A windowed comparison that distinguishes a real flap from a legitimate
  slow move — verified with a boundary-condition test at exactly the window
  edge, not just an "obviously inside/outside" case.
- Parsing real switch CLI output shape (headers, separators, fixed columns)
  robustly, skipping what doesn't match instead of assuming clean input.
