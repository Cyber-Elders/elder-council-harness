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


# --- decision-time diversity ---------------------------------------------------

def test_diversity_field_present_and_demo_never_warns(council_dir):
    from eldercouncil.catalog import load_councils
    from eldercouncil.models import load_registry
    c = load_councils()["code-council"]
    rec = engine.convene_with_votes(c, "q", engine.demo_votes(c), load_registry(), do_audit=False)
    div = rec["diversity"]
    assert div["monoculture"] is None                       # demo must not false-warn
    assert div["families"] == ["demo"]
    assert "demo" in div["note"]


def test_diversity_flags_real_single_family(council_dir):
    from eldercouncil.catalog import load_councils
    from eldercouncil.models import load_registry
    c = load_councils()["code-council"]
    fake = [{"role": r.name, "model": "anthropic:claude-opus-4-8", "vote": "merge",
             "confidence": 0.8, "reason": ""} for r in c.roles if not r.is_tool]
    rec = engine.convene_with_votes(c, "q", fake, load_registry(), do_audit=False)
    assert rec["diversity"]["monoculture"] == "anthropic"


def test_diversity_cross_family_is_clean(council_dir):
    from eldercouncil.catalog import load_councils
    from eldercouncil.models import load_registry
    c = load_councils()["code-council"]
    tags = ["ollama:qwen3:32b", "ollama:deepseek-r1:32b", "ollama:magistral:24b",
            "ollama:gemma3:12b", "ollama:gpt-oss:20b"]
    fake = [{"role": r.name, "model": tags[i % len(tags)], "vote": "merge",
             "confidence": 0.8, "reason": ""} for i, r in enumerate(c.roles) if not r.is_tool]
    rec = engine.convene_with_votes(c, "q", fake, load_registry(), do_audit=False)
    div = rec["diversity"]
    assert div["monoculture"] is None and len(div["families"]) >= 3


def test_all_inherit_reports_diversity_unknown(council_dir):
    from eldercouncil.catalog import load_councils
    from eldercouncil.models import load_registry
    c = load_councils()["code-council"]
    fake = [{"role": r.name, "model": "inherit", "vote": "merge",
             "confidence": 0.8, "reason": ""} for r in c.roles if not r.is_tool]
    rec = engine.convene_with_votes(c, "q", fake, load_registry(), do_audit=False)
    div = rec["diversity"]
    assert div["families"] == ["host"] and div["monoculture"] is None
    assert "diversity unknown" in div["note"]
