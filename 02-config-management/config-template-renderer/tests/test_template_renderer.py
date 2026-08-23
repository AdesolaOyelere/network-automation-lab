import pytest
from template_renderer import TemplateError, render_template


def test_renders_scalars_dotted_values_and_repeated_sections():
    template = "{{site}}\n{{#ports}}{{name}} {{ipv4.address}} at {{site}}\n{{/ports}}"
    data = {
        "site": "branch-a",
        "ports": [
            {"name": "Gi0/1", "ipv4": {"address": "10.0.0.1"}},
            {"name": "Gi0/2", "ipv4": {"address": "10.0.1.1"}},
        ],
    }
    assert render_template(template, data) == (
        "branch-a\nGi0/1 10.0.0.1 at branch-a\nGi0/2 10.0.1.1 at branch-a\n"
    )


def test_nested_sections_use_inner_and_parent_contexts():
    template = "{{#interfaces}}{{name}}:{{#helpers}} {{address}}/{{name}}{{/helpers}}\n{{/interfaces}}"
    data = {"interfaces": [{"name": "Gi0/1", "helpers": [{"address": "10.0.0.10"}]}]}
    assert render_template(template, data) == "Gi0/1: 10.0.0.10/Gi0/1\n"


def test_empty_section_renders_nothing():
    assert render_template("before{{#items}}x{{/items}}after", {"items": []}) == "beforeafter"


@pytest.mark.parametrize(
    ("template", "data", "message"),
    [
        ("{{missing}}", {}, "missing template value"),
        ("{{#items}}x", {"items": []}, "unclosed section"),
        ("{{/items}}", {"items": []}, "unexpected closing section"),
        ("{{#items}}x{{/items}}", {"items": "wrong"}, "section value must be a list"),
        ("{{item}}", {"item": {}}, "template value must be scalar"),
    ],
)
def test_invalid_templates_and_data_fail_loudly(template, data, message):
    with pytest.raises(TemplateError, match=message):
        render_template(template, data)
