"""End-to-end test: the committed config + intents produce the committed results.json."""
import json
from pathlib import Path

from intent_checker import parse_config, run_intents

HERE = Path(__file__).resolve().parent.parent


def test_committed_intents_match_committed_results():
    blocks = parse_config((HERE / "device_config.txt").read_text())
    intents = json.loads((HERE / "intents.json").read_text())
    fresh = run_intents(intents, blocks)
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
    assert sum(1 for r in fresh if r["passed"]) == 4
    assert len(fresh) == 8
