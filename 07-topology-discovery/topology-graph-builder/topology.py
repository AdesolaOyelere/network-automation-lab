"""Build a topology graph from neighbor-discovery records and analyze it.

LLDP/CDP-style discovery typically reports adjacency reciprocally — device A
says it sees B, and device B separately says it sees A — as two directed
records for what is really one physical link. Building the graph with
symmetric set-based adjacency (`add_edge` inserts both directions) collapses
that automatically: whether a link is reported once, twice, or with swapped
local/remote port fields, it becomes exactly one edge in the graph.

`find_articulation_points` implements the standard DFS (Tarjan) algorithm:
a non-root node u is an articulation point if it has a child v in the DFS
tree with low[v] >= disc[u] (v's subtree has no back edge past u); the root
is an articulation point iff it has more than one DFS-tree child (removing it
would separate those subtrees).
"""
from __future__ import annotations

import sys


def build_graph(records: list[dict]) -> dict[str, set[str]]:
    """records: [{device, neighbor, local_port, remote_port}, ...] (port fields unused
    here — only device/neighbor establish the edge). Reciprocal/duplicate records
    collapse into one undirected edge because adjacency is stored as sets."""
    graph: dict[str, set[str]] = {}
    for r in records:
        a, b = r["device"], r["neighbor"]
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    return graph


def connected_components(graph: dict[str, set[str]]) -> list[set[str]]:
    """Each returned set is one island: a set of devices reachable from each
    other, with no path to devices in any other returned set."""
    seen: set[str] = set()
    components: list[set[str]] = []
    for start in graph:
        if start in seen:
            continue
        component: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(graph.get(node, ()))
        components.append(component)
        seen |= component
    return components


def find_articulation_points(graph: dict[str, set[str]]) -> set[str]:
    """Devices whose removal would split their component into more than one
    piece — single points of failure in the discovered topology."""
    disc: dict[str, int] = {}
    low: dict[str, int] = {}
    parent_of: dict[str, str | None] = {}
    articulation_points: set[str] = set()
    timer = 0

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, len(graph) * 4 + 100))
    try:
        def dfs(u: str) -> None:
            nonlocal timer
            disc[u] = low[u] = timer
            timer += 1
            children = 0
            for v in graph.get(u, ()):
                if v == parent_of.get(u):
                    continue
                if v in disc:
                    low[u] = min(low[u], disc[v])
                else:
                    children += 1
                    parent_of[v] = u
                    dfs(v)
                    low[u] = min(low[u], low[v])
                    is_root = parent_of.get(u) is None
                    if not is_root and low[v] >= disc[u]:
                        articulation_points.add(u)
                    if is_root and children > 1:
                        articulation_points.add(u)

        for node in graph:
            if node not in disc:
                parent_of[node] = None
                dfs(node)
    finally:
        sys.setrecursionlimit(old_limit)

    return articulation_points


def analyze(records: list[dict]) -> dict:
    graph = build_graph(records)
    components = connected_components(graph)
    articulation_points = find_articulation_points(graph)
    return {
        "n_devices": len(graph),
        "n_raw_records": len(records),
        "n_unique_edges": sum(len(neighbors) for neighbors in graph.values()) // 2,
        "n_components": len(components),
        "components": [sorted(c) for c in sorted(components, key=lambda c: (-len(c), sorted(c)))],
        "articulation_points": sorted(articulation_points),
    }
