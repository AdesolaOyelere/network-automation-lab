"""Unit tests for graph building and articulation-point detection.

Each analytically-obvious graph shape (bowtie, path, cycle) pins the exact
expected articulation-point set — these are the textbook cases the algorithm
must get right.
"""
from topology import analyze, build_graph, connected_components, find_articulation_points


def edges(pairs):
    return [{"device": a, "neighbor": b, "local_port": "x", "remote_port": "y"} for a, b in pairs]


def test_build_graph_dedupes_reciprocal_records():
    records = edges([("A", "B"), ("B", "A"), ("B", "C")])
    graph = build_graph(records)
    assert graph == {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}


def test_connected_components_finds_islands():
    graph = build_graph(edges([("A", "B"), ("C", "D")]))
    components = connected_components(graph)
    assert {frozenset(c) for c in components} == {frozenset({"A", "B"}), frozenset({"C", "D"})}


def test_bowtie_shared_vertex_is_the_only_articulation_point():
    # Two triangles sharing exactly one vertex: A-B-C-A and C-D-E-C.
    graph = build_graph(edges([("A", "B"), ("B", "C"), ("C", "A"), ("C", "D"), ("D", "E"), ("E", "C")]))
    assert find_articulation_points(graph) == {"C"}


def test_path_graph_internal_nodes_are_articulation_points_endpoints_are_not():
    graph = build_graph(edges([("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]))
    assert find_articulation_points(graph) == {"B", "C", "D"}


def test_cycle_has_no_articulation_points():
    graph = build_graph(edges([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]))
    assert find_articulation_points(graph) == set()


def test_single_isolated_edge_has_no_articulation_points():
    graph = build_graph(edges([("A", "B")]))
    assert find_articulation_points(graph) == set()


def test_disconnected_graph_finds_articulation_points_per_component():
    # A cycle (no APs) plus a separate path (internal node is an AP).
    graph = build_graph(edges([("A", "B"), ("B", "C"), ("C", "A"), ("X", "Y"), ("Y", "Z")]))
    assert find_articulation_points(graph) == {"Y"}


def test_analyze_end_to_end_on_a_small_pendant_topology():
    # core triangle with a pendant branch (agg -> dist1, dist2) hanging off core1,
    # plus a fully separate two-node island.
    records = edges([
        ("core1", "core2"), ("core2", "core3"), ("core3", "core1"),
        ("agg1", "core1"), ("dist1", "agg1"), ("dist2", "agg1"),
        ("island1", "island2"),
    ])
    result = analyze(records)
    assert result["n_devices"] == 8
    assert result["n_components"] == 2
    assert set(result["articulation_points"]) == {"agg1", "core1"}
