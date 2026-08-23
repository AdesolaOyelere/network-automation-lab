"""End-to-end test: the committed routing_table.txt produces the committed results.json."""
import json
from pathlib import Path

from route_analyzer import (
    determine_installed_routes,
    flag_high_metric_routes,
    has_default_route,
    parse_routing_table,
)

HERE = Path(__file__).resolve().parent.parent


def test_committed_table_matches_committed_results():
    text = (HERE / "routing_table.txt").read_text()
    routes = parse_routing_table(text)
    installed_result = determine_installed_routes(routes)
    fresh = {
        "n_routes": len(routes),
        "has_default_route": has_default_route(routes),
        "not_installed": installed_result["not_installed"],
        "flagged_high_metric": flag_high_metric_routes(routes),
    }
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
    assert fresh["n_routes"] == 13
    assert fresh["has_default_route"] is False
    assert len(fresh["not_installed"]) == 1
    assert len(fresh["flagged_high_metric"]) == 1
