# Topology Graph Builder

> Build an undirected topology graph from LLDP/CDP-style neighbor records,
> find isolated islands, and locate articulation points — devices whose
> failure would split the network — with a real Tarjan's-algorithm
> implementation, not a shortcut.

**Category:** `07-topology-discovery` · **Skills:** graph algorithms, topology discovery, Python

## Problem

Neighbor discovery (LLDP/CDP) reports adjacency reciprocally — device A says
it sees B, and B separately says it sees A — for what is really one physical
link, so building a clean graph means deduplicating that first. Once built,
the graph answers two operational questions: is anything unreachable
(isolated islands), and is there a single device whose failure would
partition the network (a single point of failure)?

## Approach

`topology.py`:

- **`build_graph(records)`** inserts each `{device, neighbor}` pair
  symmetrically into a `dict[str, set[str]]`. Reciprocal and duplicate
  records collapse automatically — set insertion is idempotent, so no
  separate dedup pass is needed.
- **`connected_components(graph)`** finds islands via iterative DFS.
- **`find_articulation_points(graph)`** implements the standard DFS
  (Tarjan) algorithm: track discovery order and low-link values, and mark a
  non-root node `u` as an articulation point if some DFS-tree child `v` has
  `low[v] >= disc[u]` (its subtree has no back edge past `u`); the root is an
  articulation point iff it has more than one DFS-tree child.

## How to run

```bash
python -m pytest
python run.py --report   # analyzes the committed adjacency.json
```

No live device or network access needed — this is pure graph analysis over
committed discovery records.

## Sample output

8 devices from 11 raw (reciprocal) records, 7 unique edges after dedup
(`results/results.json`):

```
devices: 8  components: 2
articulation points: ['agg1', 'core1']
```

The topology is a redundant `core1-core2-core3` triangle with a pendant
branch (`agg1` -> `dist1`, `dist2`) hanging off `core1`, plus a fully
separate two-device island (`island1`-`island2`) with no path to the rest.
Both `agg1` (the only link into the pendant branch) and `core1` (the only
link from the triangle into that branch) are correctly flagged as single
points of failure — `core2` and `core3` are not, since the triangle keeps
them mutually reachable if either is removed.

The algorithm itself is pinned against three textbook shapes in
`tests/test_topology.py`: a bowtie (two triangles sharing one vertex — only
the shared vertex is an articulation point), a path graph (every internal
node is one, endpoints aren't), and a cycle (none at all).

## What this demonstrates

- A correct, from-scratch articulation-points implementation (DFS discovery
  + low-link values), verified against known graph shapes rather than
  eyeballed.
- Recognizing and handling the reciprocal-record dedup issue that real
  LLDP/CDP discovery data has, instead of assuming clean input.
- Turning a graph algorithm into an operationally useful answer (which
  device is a SPOF) rather than stopping at the raw algorithm.
