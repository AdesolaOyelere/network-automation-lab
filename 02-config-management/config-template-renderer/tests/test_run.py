import json

from run import HERE, render_files


def test_committed_inputs_match_rendered_configuration():
    fresh = render_files(HERE / "ios_config.template", HERE / "device_data.json")
    committed = (HERE / "results" / "rendered_config.txt").read_text(encoding="utf-8")
    assert fresh == committed


def test_committed_summary_matches_rendered_configuration():
    rendered = render_files(HERE / "ios_config.template", HERE / "device_data.json")
    summary = json.loads((HERE / "results" / "results.json").read_text(encoding="utf-8"))
    assert summary["lines"] == len(rendered.splitlines())
    assert summary["bytes"] == len(rendered.encode())
