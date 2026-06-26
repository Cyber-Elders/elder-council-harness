# SPDX-License-Identifier: Apache-2.0
"""Engine — mocked-vote fan-out -> tally -> audit, and determinism."""

import json

from eldercouncil import catalog, engine, models


def _reg():
    return models.load_registry()


def test_every_council_produces_a_verdict_with_demo_votes():
    reg = _reg()
    for cid, council in catalog.load_councils().items():
        rec = engine.convene_with_votes(council, "demo q", engine.demo_votes(council), reg, do_audit=False)
        assert rec["verdict"], cid
        assert rec["route"] in ("auto", "human", "lead_dev"), cid
        assert rec["decision_id"].startswith("EC-")


def test_demo_decisions_are_contested():
    # The point of a council is visible disagreement — every demo has dissent.
    reg = _reg()
    for cid, council in catalog.load_councils().items():
        rec = engine.convene_with_votes(council, "q", engine.demo_votes(council), reg, do_audit=False)
        assert rec["dissent"], f"{cid} demo should show dissent"


def test_same_votes_same_council_identical_record(council_dir):
    reg = _reg()
    c = catalog.get_council("code-council")
    a = engine.convene_with_votes(c, "merge q", engine.demo_votes(c), reg, do_audit=False)
    b = engine.convene_with_votes(c, "merge q", engine.demo_votes(c), reg, do_audit=False)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_code_council_demo_blocks_on_critical():
    reg = _reg()
    c = catalog.get_council("code-council")
    rec = engine.convene_with_votes(c, "merge diff with hardcoded key", engine.demo_votes(c), reg, do_audit=False)
    assert rec["verdict"] == "block" and rec["route"] == "human"


def test_cyber_risk_demo_routes_to_human():
    reg = _reg()
    c = catalog.get_council("cyber-risk")
    rec = engine.convene_with_votes(c, "accept a critical vuln", engine.demo_votes(c), reg, do_audit=False)
    assert rec["route"] == "human"  # advisory + risk acceptance is never automated


def test_monoculture_scenario_shows_the_uncaught_failure():
    # The honest counter-demo: shared-blind-spot lenses confidently agree the wrong
    # way and the action carries — the failure a council does NOT catch.
    reg = _reg()
    c = catalog.get_council("code-council")
    rec = engine.convene_with_votes(c, "ship it", engine.demo_votes(c, scenario="monoculture"),
                                    reg, do_audit=False)
    assert rec["verdict"] == "merge" and rec["route"] == "auto"
    assert not rec["dissent"]  # the point: no lens dissents — they share the blind spot


def test_convene_persists_when_audit_enabled(council_dir):
    reg = _reg()
    c = catalog.get_council("supply-chain")
    engine.convene_with_votes(c, "add dep", engine.demo_votes(c), reg, do_audit=True)
    assert list((council_dir / "decisions").glob("*.json"))
