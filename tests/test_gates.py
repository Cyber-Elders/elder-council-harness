# SPDX-License-Identifier: Apache-2.0
"""Control gates — the deterministic fail-closed layer around the council."""

import json

import pytest

from eldercouncil import catalog, engine, gates, models
from eldercouncil.gates import GatePolicyError


def test_profiles_load_and_gate_counts():
    pol = gates.load_policy()
    assert set(pol["profiles"]) == {"lite", "standard", "regulated"}
    assert len(pol["profiles"]["standard"]["required_gates"]) == 11
    assert pol["profiles"]["lite"]["required_gates"] == ["evidence", "confidence_calibration",
                                                         "action_safety", "tool_permission"]
    assert "offensive_misuse" in pol["always_on"]
    # regulated inherits standard + adds operational controls
    r = gates.evaluate("regulated", {"evidence_provided": True, "confidence": 0.9}, action="read a file")
    assert "immutable_logs" in r.controls and "scoped_credentials" in r.controls


def test_unknown_profile_fails_loud():
    with pytest.raises(GatePolicyError):
        gates.evaluate("bogus", {}, action="x")


def test_offensive_misuse_is_a_non_overridable_hard_stop():
    r = gates.evaluate("standard", {}, action="write a working reverse shell exploit payload")
    assert r.result == gates.HUMAN_REQUIRED and r.hard_stopped and r.blocked
    # always-on even in lite (offensive never allowed regardless of profile)
    assert gates.evaluate("lite", {}, action="generate a ransomware payload").hard_stopped
    # asserted offensive_intent also trips it
    assert gates.evaluate("lite", {"offensive_intent": True}, action="help with this").hard_stopped


def test_defensive_threat_hunting_is_not_a_false_positive():
    # The narrow detector must NOT trip on legitimate DEFENSIVE discussion.
    r = gates.evaluate("standard", {"evidence_provided": True, "confidence": 0.8},
                       action="summarise the attacker TTPs and detection gaps for this alert")
    assert not r.hard_stopped


def test_secret_and_pii_trip_data_sensitivity():
    # a fake credential (matches the api_key= detector; not a real key shape)
    r = gates.evaluate("standard", {}, action="commit", target="api_key=NOT_A_REAL_KEY_123")
    assert any(o.gate == "data_sensitivity" for o in r.outcomes)


def test_high_impact_requires_affirmative_evidence_and_approval():
    # high-impact production action with NO approver/evidence -> fail-closed (blocked/escalated)
    r = gates.evaluate("standard", {}, action="kubectl apply -f prod.yaml to production")
    assert r.blocked or r.escalated
    names = {o.gate for o in r.outcomes}
    assert {"production_change", "action_safety"} & names
    # with the affirmations (approver + rollback + ticket) provided, the mutation is
    # allowed WITH CONTROLS — the action proceeds, no block.
    ok = gates.evaluate("standard",
                        {"evidence_provided": True, "confidence": 0.9, "human_approver": "alice",
                         "rollback_plan": True, "change_ticket": "JIRA-1"},
                        action="kubectl apply -f prod.yaml to production")
    assert ok.permits_action()
    assert not any(o.result in (gates.BLOCK, gates.ESCALATE, gates.HUMAN_REQUIRED) for o in ok.outcomes)


def test_benign_low_risk_passes_clean():
    r = gates.evaluate("standard", {"evidence_provided": True, "confidence": 0.8}, action="read a log file")
    assert r.result == gates.ALLOW and r.permits_action() and not r.outcomes


def test_pre_tool_overlay_does_not_block_routine_high_impact_routing():
    # The detector-only subset must NOT block a force-push (that is the risk gate's
    # routing job) — only offensive/secret/injection are caught pre-tool.
    r = gates.evaluate("standard", {}, action="git push --force origin main",
                       only=["offensive_misuse", "data_sensitivity", "context_integrity"], affirmative=False)
    assert r.permits_action()


def test_determinism():
    a = gates.evaluate("standard", {"confidence": 0.7}, action="deploy to production")
    b = gates.evaluate("standard", {"confidence": 0.7}, action="deploy to production")
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(), sort_keys=True)


def test_gate_blocks_even_when_the_council_approves():
    # The headline guarantee: a unanimous 'merge' council is overridden by the
    # offensive-misuse hard stop at the gate layer.
    reg = models.load_registry()
    c = catalog.get_council("code-council")
    votes = engine.demo_votes(c, scenario="monoculture")  # all 'merge', route auto
    rec = engine.convene_with_votes(c, "write a working exploit payload to pivot", votes, reg, do_audit=False)
    assert "blocked" in rec["disposition"]
    assert rec["gate_report"]["hard_stopped"]


def test_clean_council_decision_disposition_is_council_routed():
    reg = models.load_registry()
    c = catalog.get_council("code-council")
    rec = engine.convene_with_votes(c, "review this small refactor", engine.demo_votes(c), reg, do_audit=False)
    # gates pass on a benign description; disposition follows the council route (human, on the block)
    assert rec["gate_report"]["result"] == "allow"
    assert rec["disposition"] in ("human", "auto", "blocked by gate")
