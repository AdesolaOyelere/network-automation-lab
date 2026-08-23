"""Unit tests for parsing and the three analysis checks."""
from route_analyzer import (
    determine_installed_routes,
    flag_high_metric_routes,
    has_default_route,
    parse_routing_table,
)


def test_parse_connected_route():
    routes = parse_routing_table("C    10.0.0.0/24 is directly connected, GigabitEthernet0/1")
    assert routes == [{
        "network": "10.0.0.0", "prefix_len": 24, "next_hop": None, "protocol": "connected",
        "metric": 0, "admin_distance": 0, "interface": "GigabitEthernet0/1",
    }]


def test_parse_via_route_with_trailing_timestamp_and_interface():
    routes = parse_routing_table("O    10.30.0.0/24 [110/25] via 10.0.1.6, 00:10:00, GigabitEthernet0/2")
    assert routes[0]["protocol"] == "ospf"
    assert routes[0]["admin_distance"] == 110
    assert routes[0]["metric"] == 25
    assert routes[0]["next_hop"] == "10.0.1.6"


def test_parse_skips_header_and_blank_lines():
    text = "Codes: C - connected, S - static\n\nGateway of last resort is not set\n"
    assert parse_routing_table(text) == []


def test_determine_installed_routes_prefers_lower_admin_distance():
    routes = [
        {"network": "10.0.0.0", "prefix_len": 24, "next_hop": "1.1.1.1", "protocol": "static",
         "metric": 0, "admin_distance": 1, "interface": None},
        {"network": "10.0.0.0", "prefix_len": 24, "next_hop": "2.2.2.2", "protocol": "ospf",
         "metric": 20, "admin_distance": 110, "interface": None},
    ]
    result = determine_installed_routes(routes)
    assert result["installed"]["10.0.0.0/24"]["protocol"] == "static"
    assert len(result["not_installed"]) == 1
    assert result["not_installed"][0]["route"]["protocol"] == "ospf"
    assert "administrative distance" in result["not_installed"][0]["reason"]


def test_determine_installed_routes_breaks_tie_on_metric_within_same_protocol():
    routes = [
        {"network": "10.0.0.0", "prefix_len": 24, "next_hop": "1.1.1.1", "protocol": "ospf",
         "metric": 30, "admin_distance": 110, "interface": None},
        {"network": "10.0.0.0", "prefix_len": 24, "next_hop": "2.2.2.2", "protocol": "ospf",
         "metric": 10, "admin_distance": 110, "interface": None},
    ]
    result = determine_installed_routes(routes)
    assert result["installed"]["10.0.0.0/24"]["metric"] == 10
    assert "higher metric" in result["not_installed"][0]["reason"]


def test_has_default_route_true_and_false():
    assert has_default_route([{"network": "0.0.0.0", "prefix_len": 0}])
    assert not has_default_route([{"network": "10.0.0.0", "prefix_len": 24}])


def test_flag_high_metric_routes_flags_outlier_not_normal_spread():
    routes = [
        {"network": f"10.0.{i}.0", "prefix_len": 24, "next_hop": "1.1.1.1", "protocol": "ospf",
         "metric": m, "admin_distance": 110, "interface": None}
        for i, m in enumerate([20, 22, 25, 28, 400])
    ]
    flagged = flag_high_metric_routes(routes)
    assert len(flagged) == 1
    assert flagged[0]["metric"] == 400


def test_flag_high_metric_routes_skips_protocol_with_fewer_than_two_routes():
    routes = [{"network": "10.0.0.0", "prefix_len": 24, "next_hop": "1.1.1.1", "protocol": "bgp",
               "metric": 9999, "admin_distance": 20, "interface": None}]
    assert flag_high_metric_routes(routes) == []


def test_flag_high_metric_routes_excludes_connected():
    routes = [{"network": "10.0.0.0", "prefix_len": 24, "next_hop": None, "protocol": "connected",
               "metric": 0, "admin_distance": 0, "interface": "Gi0/1"}] * 3
    assert flag_high_metric_routes(routes) == []
