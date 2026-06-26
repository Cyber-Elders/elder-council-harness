# SPDX-License-Identifier: Apache-2.0
"""Model registry — role resolution, sentinels, fail-loud on unknown roles."""

import pytest

from eldercouncil import models
from eldercouncil.models import RegistryError


def test_frontier_lane_resolves_real_anthropic_tags():
    reg = models.load_registry()
    assert models.resolve(reg, "security_sme", "frontier") == "claude-opus-4-8"
    assert models.resolve(reg, "engineering_sme", "frontier") == "claude-sonnet-4-6"
    assert models.resolve(reg, "pragmatic_ops", "frontier") == "claude-haiku-4-5"


def test_only_verified_real_tags_shipped_as_defaults():
    reg = models.load_registry()
    # Every concrete (non-sentinel, non-null) tag in the registry must be a real Anthropic tag.
    real = set(["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"])
    for role, entry in reg.roles.items():
        for lane in ("frontier", "open", "local"):
            v = entry.get(lane)
            if v is None or models.is_sentinel(v):
                continue
            assert v in real, f"{role}:{lane} ships a non-verified tag {v!r}"


def test_unknown_role_fails_loud():
    reg = models.load_registry()
    with pytest.raises(RegistryError):
        models.resolve(reg, "no_such_role", "frontier")


def test_unpinned_sentinel_raises_not_guesses():
    reg = models.load_registry()
    with pytest.raises(RegistryError):
        models.resolve(reg, "cross_family_critic", "frontier")  # ships unpinned by design


def test_null_lane_falls_back_to_inherit_or_real():
    reg = models.load_registry()
    # deterministic_tool has all-null lanes -> inherit (host model; it runs tools, not an LLM)
    assert models.resolve(reg, "deterministic_tool", "frontier") == "inherit"


def test_unresolved_reports_sentinels():
    reg = models.load_registry()
    miss = models.unresolved(reg)
    assert "cross_family_critic:frontier" in miss
    assert all(":" in m for m in miss)
    # frontier Anthropic lanes are pinned, so they must NOT appear
    assert "security_sme:frontier" not in miss
