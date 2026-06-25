# SPDX-License-Identifier: Apache-2.0
"""Council definitions — all load, validate, and fail closed when malformed."""

import pytest

from eldercouncil import catalog
from eldercouncil.schema import SchemaError, parse_council

# Six cyber councils + one general business council.
COUNCILS = {"code-council", "threat-hunting", "supply-chain", "compliance", "cyber-risk",
            "platform-architecture", "business-decision"}


def test_all_councils_load_and_validate():
    cs = catalog.load_councils()
    assert set(cs) == COUNCILS, set(cs)
    for c in cs.values():
        assert c.mode in ("advisory", "action-gate")
        assert len(c.roles) >= 1
        assert c.decision_outcomes
        assert c.fail_closed.strip()


def test_each_role_references_a_role_key():
    for c in catalog.load_councils().values():
        for r in c.roles:
            assert r.role_key, f"{c.id}:{r.name} missing role_key"
            assert r.variant in ("frontier", "open", "local")


def test_at_most_one_arbitrator():
    for c in catalog.load_councils().values():
        assert sum(1 for r in c.roles if r.arbitrator) <= 1, c.id


def test_action_gate_vs_advisory_split():
    cs = catalog.load_councils()
    assert cs["code-council"].mode == "action-gate"
    assert cs["supply-chain"].mode == "action-gate"
    assert cs["cyber-risk"].mode == "advisory"
    assert cs["compliance"].mode == "advisory"
    assert cs["business-decision"].mode == "advisory"  # exec decisions never auto-decided


def test_cyber_risk_has_accept_outcome():
    # the human-reserved 'accept' outcome must exist so the never-auto rule applies
    assert "accept" in catalog.load_councils()["cyber-risk"].decision_outcomes


def test_compliance_is_scheduled():
    assert catalog.load_councils()["compliance"].schedule  # cron present


def test_malformed_council_fails_closed():
    with pytest.raises(SchemaError):
        parse_council({"id": "x", "name": "X"})  # missing mode/roles/outcomes/fail_closed/purpose
    with pytest.raises(SchemaError):
        parse_council({"id": "x", "name": "X", "purpose": "p", "mode": "bogus",
                       "roles": [{"name": "r", "lens": "l", "role_key": "k"}],
                       "decision_outcomes": ["a"], "fail_closed": "f"})
    with pytest.raises(SchemaError):
        parse_council({"id": "x", "name": "X", "purpose": "p", "mode": "advisory",
                       "roles": [], "decision_outcomes": ["a"], "fail_closed": "f"})


def test_get_unknown_council_raises():
    with pytest.raises(SchemaError):
        catalog.get_council("does-not-exist")


def test_council_id_must_be_a_safe_slug():
    # id becomes a filename + slash-command + sentinel-comment token: reject traversal
    # and comment-breakout ids (security: path traversal / CLAUDE.md injection).
    base = {"name": "X", "purpose": "p", "mode": "advisory",
            "roles": [{"name": "r", "lens": "l", "role_key": "security_sme"}],
            "decision_outcomes": ["a"], "fail_closed": "f"}
    for bad in ("../../etc/passwd", "x -->", "Code_Council", "evil/../x", "a b"):
        with pytest.raises(SchemaError):
            parse_council({**base, "id": bad})
    parse_council({**base, "id": "ok-slug-1"})  # valid


def test_role_key_must_be_a_safe_token():
    base = {"id": "c", "name": "X", "purpose": "p", "mode": "advisory",
            "decision_outcomes": ["a"], "fail_closed": "f"}
    with pytest.raises(SchemaError):
        parse_council({**base, "roles": [{"name": "r", "lens": "l", "role_key": "bad key!"}]})
