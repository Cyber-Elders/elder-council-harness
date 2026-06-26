# SPDX-License-Identifier: Apache-2.0
"""Consensus tally — the minimum-governance fail-closed rules + per-council outcomes."""

from eldercouncil.consensus import Vote, tally
from conftest import mkcouncil, votes


# --- conservative defaults --------------------------------------------------
def test_empty_votes_block_to_human():
    o = tally([], mkcouncil())
    assert o.verdict == "block" and o.route == "human"


def test_no_quorum_is_inconclusive_not_a_deliberated_block():
    # 5 roles, only 2 reachable -> quorum 3 not met -> 'inconclusive' (the council did
    # not convene), routed to a human. Honest: distinct from a deliberated block.
    o = tally(votes(("merge", 0.9), ("merge", 0.9)), mkcouncil(n_roles=5, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "inconclusive" and o.route == "human"
    assert not o.permits_action()


def test_outage_abstentions_are_inconclusive_not_block():
    # 3 of 5 lenses unavailable -> council did not convene -> inconclusive/human.
    vs = votes(("merge", 0.9), ("merge", 0.9))
    vs += [{"role": f"r{i}", "model": "x", "vote": "unavailable", "confidence": 0.0} for i in range(3)]
    o = tally(vs, mkcouncil(n_roles=5, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "inconclusive" and o.route == "human"


def test_escalation_wins():
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("escalate", 0.6)),
              mkcouncil(n_roles=3, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "escalate" and o.route == "human"


def test_escalate_to_counsel_is_escalation():
    o = tally(votes(("proceed-with-controls", 0.7), ("proceed-with-controls", 0.7), ("escalate-to-counsel", 0.7)),
              mkcouncil(mode="advisory", n_roles=3,
                        outcomes=("proceed-with-controls", "block", "escalate-to-counsel")))
    assert o.verdict == "escalate-to-counsel" and o.route == "human"


def test_critical_severity_blocks_outright():
    # The Code council's fail-closed rule: any CRITICAL finding blocks pending human review,
    # even if the plurality would otherwise merge.
    vs = votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9))
    vs.append({"role": "appsec", "model": "t", "vote": "block", "confidence": 0.9, "severity": "CRITICAL"})
    o = tally(vs, mkcouncil(mode="action-gate", n_roles=4, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "block" and o.route == "human"
    assert "CRITICAL" in o.rationale


def test_tie_routes_to_human_most_restrictive():
    o = tally(votes(("merge", 0.9), ("block", 0.9)), mkcouncil(n_roles=2, outcomes=("merge", "block")))
    assert o.verdict == "block" and o.route == "human"
    assert "tie" in o.rationale


# --- action-gate behaviour --------------------------------------------------
def test_action_gate_permissive_high_confidence_auto():
    o = tally(votes(("merge", 0.9), ("merge", 0.8), ("merge", 0.9)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "merge" and o.route == "auto"
    assert o.permits_action()


def test_action_gate_blocking_goes_to_human():
    o = tally(votes(("block", 0.9), ("block", 0.8), ("merge", 0.6)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "block" and o.route == "human"
    assert not o.permits_action()


def test_low_confidence_permissive_routes_to_human():
    o = tally(votes(("merge", 0.3), ("merge", 0.3), ("merge", 0.3)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert o.verdict == "merge" and o.route == "human"
    assert not o.permits_action()


def test_request_changes_routes_to_lead_dev():
    o = tally(votes(("request-changes", 0.8), ("request-changes", 0.7), ("merge", 0.6)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "request-changes", "block")))
    assert o.verdict == "request-changes" and o.route == "lead_dev"


# --- advisory + human-reserved ---------------------------------------------
def test_advisory_always_routes_to_human():
    o = tally(votes(("recommend", 0.9), ("recommend", 0.9), ("recommend", 0.9)),
              mkcouncil(mode="advisory", n_roles=3, outcomes=("recommend", "defer")))
    assert o.verdict == "recommend" and o.route == "human"
    assert not o.permits_action()


def test_risk_acceptance_never_automated():
    # even a clear 'accept' majority must route to a human
    o = tally(votes(("accept", 0.9), ("accept", 0.9), ("mitigate", 0.6)),
              mkcouncil(mode="advisory", n_roles=3, outcomes=("accept", "mitigate", "monitor")))
    assert o.verdict == "accept" and o.route == "human"


def test_dissent_preserved():
    o = tally(votes(("merge", 0.9), ("merge", 0.8), ("block", 0.9)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert len(o.dissent) == 1 and o.dissent[0]["vote"] == "block"


def test_word_confidence_is_parsed_not_crashed():
    # The deliberation protocol asks lenses for Low/Medium/High — must not crash.
    vs = [{"role": f"r{i}", "model": "m", "vote": "merge", "confidence": "High"} for i in range(3)]
    o = tally(vs, mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert o.verdict == "merge" and o.route == "auto"  # High confidence clears the floor
    lo = [{"role": f"r{i}", "model": "m", "vote": "merge", "confidence": "Low"} for i in range(3)]
    assert tally(lo, mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))).route == "human"


def test_confidence_clamped():
    vs = [{"role": f"r{i}", "model": "m", "vote": "merge", "confidence": 5.0} for i in range(3)]
    # an out-of-range confidence must not defeat the low-confidence rule via inflation
    o = tally(vs, mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert all(0.0 <= v["confidence"] <= 1.0 for v in o.votes)


def test_unknown_vote_token_becomes_abstain_never_auto():
    # A token outside the council's outcomes must never win or auto-permit.
    vs = [{"role": f"r{i}", "model": "m", "vote": "approved-yolo", "confidence": 0.9} for i in range(3)]
    o = tally(vs, mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "inconclusive" and not o.permits_action()


def test_permissive_cannot_auto_when_a_lens_dissents_blocking():
    # 3 merge vs 2 block (quorum met, merge is plurality) — but a lens wants to STOP,
    # so the permissive winner must NOT auto-proceed; it routes to a human.
    vs = votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9), ("block", 0.9), ("block", 0.9))
    o = tally(vs, mkcouncil(mode="action-gate", n_roles=5, outcomes=("merge", "block", "escalate")))
    assert o.verdict == "merge" and o.route == "human" and not o.permits_action()


def test_tool_lens_critical_is_authoritative_reasoning_lens_is_not():
    from types import SimpleNamespace
    roles = [SimpleNamespace(name="appsec", arbitrator=False, is_tool=False),
             SimpleNamespace(name="tool", arbitrator=False, is_tool=True),
             SimpleNamespace(name="eng", arbitrator=False, is_tool=False)]
    council = SimpleNamespace(mode="action-gate", roles=roles, decision_outcomes=["merge", "block", "escalate"], id="c")
    # a reasoning lens flagging CRITICAL does NOT unilaterally force a block (injection-safe):
    reasoning_crit = [{"role": "appsec", "model": "m", "vote": "merge", "confidence": 0.9, "severity": "CRITICAL"},
                      {"role": "tool", "model": "t", "vote": "merge", "confidence": 0.9},
                      {"role": "eng", "model": "m", "vote": "merge", "confidence": 0.9}]
    assert tally(reasoning_crit, council).verdict == "merge"
    # the deterministic-tool lens flagging CRITICAL DOES block:
    tool_crit = [{"role": "appsec", "model": "m", "vote": "merge", "confidence": 0.9},
                 {"role": "tool", "model": "t", "vote": "block", "confidence": 0.95, "severity": "CRITICAL"},
                 {"role": "eng", "model": "m", "vote": "merge", "confidence": 0.9}]
    o = tally(tool_crit, council)
    assert o.verdict == "block" and o.route == "human"


def test_restrictiveness_map_covers_every_bundled_outcome():
    from eldercouncil import catalog
    from eldercouncil.consensus import _RESTRICTIVENESS
    for c in catalog.load_councils().values():
        for outcome in c.decision_outcomes:
            o = outcome.strip().lower()
            assert o in _RESTRICTIVENESS or o.startswith("escalate"), f"{c.id}:{outcome} unmapped"


def test_vote_dataclass_accepted():
    o = tally([Vote("r1", "m", "merge", 0.9), Vote("r2", "m", "merge", 0.9), Vote("r3", "m", "merge", 0.9)],
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert o.verdict == "merge"
