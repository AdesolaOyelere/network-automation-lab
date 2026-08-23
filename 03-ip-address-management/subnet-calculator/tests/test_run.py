"""End-to-end test: the committed requirements.json allocates as expected —
a regression test for the committed results.json.
"""
import json
from pathlib import Path

from subnet_calc import allocate_vlsm

HERE = Path(__file__).resolve().parent.parent


def test_committed_requirements_all_fit():
    data = json.loads((HERE / "requirements.json").read_text())
    result = allocate_vlsm(data["supernet"], data["requirements"])
    assert result["fits"]
    assert len(result["allocations"]) == 5


def test_committed_results_match_a_fresh_run():
    data = json.loads((HERE / "requirements.json").read_text())
    fresh = allocate_vlsm(data["supernet"], data["requirements"])
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
