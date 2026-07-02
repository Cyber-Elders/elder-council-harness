# SPDX-License-Identifier: Apache-2.0
"""Model registry — role resolution, sentinels, fail-loud on unknown roles,
the cross-family open-lane defaults, and the local-lane inherit constraint."""

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
    # Every concrete (non-sentinel, non-null) tag must be in the registry's own
    # verified_real list — and that list itself must never contain a sentinel or
    # a fabricated/banned shape (test_docs.py bans them repo-wide).
    real = set(reg.verified_real)
    assert real, "registry must declare its verified_real list"
    for role, entry in reg.roles.items():
        for lane in ("frontier", "open", "local"):
            v = entry.get(lane)
            if v is None or models.is_sentinel(v):
                continue
            assert v in real, f"{role}:{lane} ships a non-verified tag {v!r}"


def test_open_lane_ships_a_cross_family_council():
    # The monoculture critique fix: `--lane open` must resolve to MULTIPLE
    # provider families out of the box — measured over the roles that SHIPPED
    # COUNCILS ACTUALLY SEAT (a family pinned only on unseated roles never votes).
    from eldercouncil.catalog import load_councils
    reg = models.load_registry()
    seated = {r.role_key for c in load_councils().values() for r in c.roles if not r.is_tool}
    fams = set()
    for role in seated:
        try:
            fams.add(models.provider_of(models.resolve(reg, role, "open")))
        except RegistryError:
            continue
    fams.discard("host")
    assert len(fams) >= 5, f"open lane must seat >=5 families, got {sorted(fams)}"
    assert models.provider_of(models.resolve(reg, "critic_challenge", "open")) != \
           models.provider_of(models.resolve(reg, "strategic_risk_owner", "open"))
    assert models.monoculture(reg, "open") is None


def test_local_lane_stays_inherit_CONSTRAINT_PIN():
    # HARD CONSTRAINT: the local lane ships UNPINNED so `--lane local` makes every
    # lens inherit the host session model (the Claude Code + Ollama journey).
    # models.resolve's null-lane fallback returns the first REAL tag in any lane,
    # so these must stay REPLACE_ME sentinels — never null, never pinned.
    reg = models.load_registry()
    for role, entry in reg.roles.items():
        if entry.get("kind") == "tool":
            continue
        assert models.is_sentinel(entry.get("local")), \
            f"{role}:local must stay a REPLACE_ME sentinel (inherit) — see CLAUDE-CODE-OLLAMA.md"
        assert models.inherits(reg, role, "local"), role


def test_provider_of_family_table():
    cases = {
        "claude-opus-4-8": "anthropic", "ollama/qwen3:32b": "alibaba",
        "ollama/deepseek-r1:32b": "deepseek", "ollama/magistral:24b": "mistral",
        "ollama/gemma3:12b": "google", "ollama/gpt-oss:20b": "openai",
        "openrouter/qwen/qwen3-32b": "alibaba", "deepseek/deepseek-r1": "deepseek",
        "anthropic:claude-opus-4-8": "anthropic", "ollama:gemma3:12b": "google",
        "inherit": "host", "": "host", "demo": "demo", "tool": "tool",
    }
    for tag, family in cases.items():
        assert models.provider_of(tag) == family, f"{tag!r} -> {models.provider_of(tag)} != {family}"


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
    # frontier Anthropic lanes and the pinned open lane must NOT appear
    assert "security_sme:frontier" not in miss
    assert "security_sme:open" not in miss
