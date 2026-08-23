"""End-to-end test: the committed inventory filters and runs as expected — a
regression test for the committed results.json.
"""
import json
from pathlib import Path

from task_runner import filter_inventory, run_task
from transport import get_version

HERE = Path(__file__).resolve().parent.parent


def test_committed_inventory_prod_filter_and_run():
    inventory = json.loads((HERE / "inventory.json").read_text())
    filtered = filter_inventory(inventory, tags=["prod"])
    results = run_task(filtered, get_version)

    assert len(inventory) == 8
    assert len(filtered) == 7  # lab-sw1 is tagged "lab", not "prod"
    by_name = {r["device"]: r for r in results}
    assert by_name["sfo-edge1"]["success"] is False
    assert by_name["nyc-core1"]["result"] == "15.2(4)E7"


def test_committed_results_match_a_fresh_run():
    inventory = json.loads((HERE / "inventory.json").read_text())
    filtered = filter_inventory(inventory, tags=["prod"])
    fresh_results = run_task(filtered, get_version)
    fresh = {"n_inventory": len(inventory), "n_filtered": len(filtered), "results": fresh_results}
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
