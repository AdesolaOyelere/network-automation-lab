from drift_detector import compare_configs, normalize_config


def test_volatile_lines_comments_blanks_and_duplicates_are_ignored():
    config = """
Building configuration...
! Last configuration change at 01:02 UTC
!
hostname edge-01
hostname edge-01

"""
    assert [item.command for item in normalize_config(config)] == ["hostname edge-01"]


def test_hierarchical_context_prevents_identical_commands_colliding():
    config = """
interface GigabitEthernet0/1
 no shutdown
interface GigabitEthernet0/2
 no shutdown
"""
    statements = normalize_config(config)
    shutdowns = [item for item in statements if item.command == "no shutdown"]
    assert [item.context for item in shutdowns] == [
        "interface GigabitEthernet0/1",
        "interface GigabitEthernet0/2",
    ]


def test_value_change_is_paired_instead_of_double_counted():
    golden = "interface GigabitEthernet0/1\n description Users\n"
    running = "interface GigabitEthernet0/1\n description Guests\n"
    result = compare_configs(golden, running)
    assert result["summary"] == {"changed": 1, "missing": 0, "unexpected": 0}
    assert result["changed"][0]["expected"] == "description Users"
    assert result["changed"][0]["actual"] == "description Guests"


def test_router_id_change_is_paired_within_routing_context():
    golden = "router ospf 10\n router-id 10.0.0.1\n"
    running = "router ospf 10\n router-id 10.0.0.2\n"
    result = compare_configs(golden, running)
    assert result["summary"] == {"changed": 1, "missing": 0, "unexpected": 0}
    assert result["changed"] == [
        {
            "context": "router ospf 10",
            "expected": "router-id 10.0.0.1",
            "actual": "router-id 10.0.0.2",
        }
    ]


def test_missing_and_unexpected_exact_statements_are_reported():
    result = compare_configs(
        "hostname edge-01\nntp server 192.0.2.10\n",
        "hostname edge-01\nlogging host 192.0.2.50\n",
    )
    assert result["missing"] == [{"context": "global", "command": "ntp server 192.0.2.10"}]
    assert result["unexpected"] == [{"context": "global", "command": "logging host 192.0.2.50"}]


def test_equivalent_config_is_in_sync_despite_order_and_noise():
    golden = "hostname edge-01\nservice timestamps log datetime msec\n"
    running = "!\nservice timestamps log datetime msec\nhostname edge-01\n"
    result = compare_configs(golden, running)
    assert result["in_sync"]
    assert result["summary"] == {"changed": 0, "missing": 0, "unexpected": 0}
