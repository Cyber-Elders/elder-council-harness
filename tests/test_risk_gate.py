# SPDX-License-Identifier: Apache-2.0
"""Risk gate — scoring, clamps, and route boundaries."""

import pytest

from eldercouncil import risk_gate as rg


def test_score_product_and_clamp():
    assert rg.score(1, 1).score == 1
    assert rg.score(5, 5).score == 25
    assert rg.score(99, 99).score == 25       # clamped to 5x5
    assert rg.score(0, 0).score == 1          # clamped up to 1x1
    assert rg.score(3, 4).score == 12


@pytest.mark.parametrize("s,expected", [
    (1, "SOLO_ALLOW"), (4, "SOLO_ALLOW"),
    (5, "DUAL_REVIEW"), (9, "DUAL_REVIEW"),
    (10, "FULL_COUNCIL"), (15, "FULL_COUNCIL"),
    (16, "COUNCIL_PLUS_HUMAN"), (25, "COUNCIL_PLUS_HUMAN"),
    (0, "SOLO_ALLOW"), (99, "COUNCIL_PLUS_HUMAN"),   # clamped
])
def test_route_boundaries(s, expected):
    assert rg.route(s) == expected


@pytest.mark.parametrize("s,lvl", [(4, "low"), (9, "medium"), (15, "high"), (16, "critical"), (25, "critical")])
def test_levels(s, lvl):
    assert rg.level(s) == lvl


def test_escalation_not_default_for_routine_actions():
    # routine, low-impact actions stay below the convene threshold (SOLO_ALLOW)
    for action in ("ls", "cat README.md", "echo hi", "git status"):
        assert rg.route(rg.compute_risk_score(action)) == "SOLO_ALLOW", action


def test_high_stakes_actions_escalate():
    for action in ("rm -rf /", "git push --force origin main", "kubectl apply -f prod.yaml",
                   "npm publish", "terraform apply"):
        assert rg.compute_risk_score(action) >= 5, action
        assert rg.route(rg.compute_risk_score(action)) != "SOLO_ALLOW", action


def test_secrets_and_production_raise_impact():
    assert rg.assess("cat .env").score > rg.assess("cat notes.txt").score
    assert rg.assess("deploy to production").score >= 5


def test_assess_is_deterministic():
    a = rg.assess("git push --force origin main")
    b = rg.assess("git push --force origin main")
    assert (a.score, a.route, a.level) == (b.score, b.route, b.level)
