"""End-to-end test: the committed sample_macs.txt produces the committed results.json."""
import json
from pathlib import Path

from vendors import lookup_batch

HERE = Path(__file__).resolve().parent.parent


def test_committed_batch_matches_committed_results():
    macs = [line.strip() for line in (HERE / "sample_macs.txt").read_text().splitlines() if line.strip()]
    fresh = lookup_batch(macs)
    committed = json.loads((HERE / "results" / "results.json").read_text())
    assert fresh == committed
    assert len(fresh) == 8
    assert sum(1 for r in fresh if r["error"]) == 2
