# SPDX-License-Identifier: Apache-2.0
"""Off-box audit anchor — capture the chain head so a later LOCAL rewrite is
detectable. The mechanism behind the honest "tamper-evident, not tamper-proof"
off-box requirement: a local adversary can still rewrite the local chain, but not
the head you captured somewhere they can't reach."""

import json

from conftest import mkcouncil, votes
from eldercouncil import audit, cli
from eldercouncil.consensus import tally


def _record(q="q"):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    return audit.record(c.id, q, tally(votes(("merge", 0.9),) * 3, c), mode=c.mode)


def test_anchor_state_returns_head_and_count(council_dir):
    _record(); _record("q2")
    st = audit.anchor_state()
    assert st["head"] == audit.head_hash()
    assert st["count"] == len(audit.read_events()) == 2
    assert st["ts"]


def test_anchor_expect_format_round_trips_into_verify(council_dir, capsys):
    _record()
    assert cli.main(["anchor", "--format", "expect"]) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("--expect-head ")
    parts = line.split()
    head = parts[parts.index("--expect-head") + 1]
    count = int(parts[parts.index("--expect-count") + 1])
    assert audit.verify(expected_head=head, expected_count=count)["ok"]


def test_captured_anchor_detects_a_full_local_rewrite(council_dir):
    _record()
    captured = audit.anchor_state()["head"]
    # a full local rewrite: wipe the chain + head cache and rebuild -> a new head
    (council_dir / "audit.jsonl").unlink()
    (council_dir / "audit.head").unlink(missing_ok=True)
    _record("rewritten")
    assert audit.head_hash() != captured
    assert not audit.verify(expected_head=captured)["ok"]   # the off-box anchor catches it


def test_anchor_run_pipes_to_a_configured_sink(council_dir, tmp_path, monkeypatch):
    _record()
    out = tmp_path / "offbox.log"
    from eldercouncil import config
    monkeypatch.setattr(config, "anchor_command", lambda path=None: f"sh -c 'cat >> \"{out}\"'")
    assert cli.main(["anchor", "--run"]) == 0
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["head"] == audit.head_hash()


def test_anchor_run_without_a_sink_is_a_clean_noop(council_dir):
    _record()
    # no [audit] anchor_command configured -> exit 1, a printed nudge, never raises
    assert cli.main(["anchor", "--run"]) == 1
