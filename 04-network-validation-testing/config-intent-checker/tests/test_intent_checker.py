"""Unit tests for hierarchical parsing and both intent-check types."""
from intent_checker import check_intent, parse_config


def test_parse_config_groups_sub_lines_under_top_level_block():
    text = (
        "interface Gi0/1\n switchport mode access\n switchport access vlan 20\n"
        "interface Gi0/2\n switchport mode trunk\n"
    )
    blocks = parse_config(text)
    assert len(blocks) == 2
    assert blocks[0] == {
        "line": "interface Gi0/1",
        "sub_lines": ["switchport mode access", "switchport access vlan 20"],
    }
    assert blocks[1] == {"line": "interface Gi0/2", "sub_lines": ["switchport mode trunk"]}


def test_parse_config_skips_blank_lines():
    text = "hostname sw1\n\n\ninterface Gi0/1\n switchport mode access\n"
    blocks = parse_config(text)
    assert len(blocks) == 2


def test_parse_config_ignores_leading_indented_line_before_any_block():
    blocks = parse_config(" orphan sub-line\nhostname sw1\n")
    assert blocks == [{"line": "hostname sw1", "sub_lines": []}]


def test_interface_access_vlan_pass():
    blocks = parse_config("interface Gi0/1\n switchport mode access\n switchport access vlan 20\n")
    result = check_intent({"type": "interface_access_vlan", "interface": "Gi0/1", "vlan": 20}, blocks)
    assert result["passed"] is True
    assert result["reason"] is None


def test_interface_access_vlan_wrong_vlan():
    blocks = parse_config("interface Gi0/1\n switchport mode access\n switchport access vlan 30\n")
    result = check_intent({"type": "interface_access_vlan", "interface": "Gi0/1", "vlan": 20}, blocks)
    assert result["passed"] is False
    assert result["reason"] == "found switchport access vlan 30, expected 20"


def test_interface_access_vlan_trunk_mode_fails():
    blocks = parse_config("interface Gi0/1\n switchport mode trunk\n")
    result = check_intent({"type": "interface_access_vlan", "interface": "Gi0/1", "vlan": 20}, blocks)
    assert result["passed"] is False
    assert "not in access mode" in result["reason"]


def test_interface_access_vlan_interface_missing():
    blocks = parse_config("interface Gi0/1\n switchport mode access\n")
    result = check_intent({"type": "interface_access_vlan", "interface": "Gi0/99", "vlan": 20}, blocks)
    assert result["passed"] is False
    assert "not found" in result["reason"]


def test_interface_access_vlan_access_mode_but_no_vlan_line():
    blocks = parse_config("interface Gi0/1\n switchport mode access\n")
    result = check_intent({"type": "interface_access_vlan", "interface": "Gi0/1", "vlan": 20}, blocks)
    assert result["passed"] is False
    assert "no switchport access vlan configured" in result["reason"]


def test_line_present_pass_and_fail():
    blocks = parse_config("hostname sw1\nip domain-name example.com\n")
    ok = check_intent({"type": "line_present", "pattern": r"^hostname\s+sw1$"}, blocks)
    assert ok["passed"] is True
    missing = check_intent({"type": "line_present", "pattern": r"^ntp server "}, blocks)
    assert missing["passed"] is False
    assert "no line matching pattern" in missing["reason"]


def test_line_present_only_checks_top_level_lines_not_sub_lines():
    blocks = parse_config("interface Gi0/1\n switchport mode access\n")
    result = check_intent({"type": "line_present", "pattern": r"switchport mode access"}, blocks)
    assert result["passed"] is False


def test_unknown_intent_type_raises():
    import pytest

    with pytest.raises(ValueError):
        check_intent({"type": "nonexistent_check"}, [])
