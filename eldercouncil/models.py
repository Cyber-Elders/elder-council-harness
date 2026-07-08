# SPDX-License-Identifier: Apache-2.0
"""
Model registry — role_key -> model resolution (BYO-LLM, role-based).

Council role files reference a ROLE KEY (e.g. "security_sme"), never a model
tag. This module resolves a role key + lane (frontier | open | local) against
`council-models.json`. The project-level `.council/council-models.json` (if
present) overrides the bundled default.

Model tags age. Keeping the mapping in ONE file — and re-pinning quarterly —
means the agent prompt bodies never carry a tag. Cross-family/open/local lanes
ship as `REPLACE_ME:<capability>` sentinels; `unresolved()` flags any that the
user has not pinned, and `eldercouncil models check` exits non-zero on them.

Pure, offline, stdlib-only. No model is called here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import paths

_SENTINEL_PREFIX = "REPLACE_ME"
_LANES = ("frontier", "open", "local")


class RegistryError(Exception):
    """Raised when the registry is missing, malformed, or a role is unknown."""


class UnpinnedError(RegistryError):
    """Raised when a known role's lane is still a REPLACE_ME sentinel. Distinct
    from RegistryError so callers can fall back to the host model for an UNPINNED
    lane while still surfacing an UNKNOWN role (a config typo) loudly."""


@dataclass(frozen=True)
class ModelRegistry:
    version: str
    roles: dict  # role_key -> {frontier, open, local, ...}
    source: str  # path it was loaded from
    verified_real: tuple = ()  # the registry's own list of tags vetted as real


def load_registry(path: str | Path | None = None) -> ModelRegistry:
    """Load the model registry. Resolution order: explicit path → project
    `.council/council-models.json` → bundled default."""
    if path is not None:
        p = Path(path)
    elif paths.project_models_path().exists():
        p = paths.project_models_path()
    else:
        p = paths.bundled_models_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"could not load model registry at {p}: {exc}") from exc
    roles = data.get("roles", {}) or {}
    if not isinstance(roles, dict):
        raise RegistryError("registry 'roles' must be an object")
    return ModelRegistry(version=str(data.get("version", "unknown")), roles=roles, source=str(p),
                         verified_real=tuple(data.get("verified_real", []) or ()))


def is_sentinel(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(_SENTINEL_PREFIX)


def resolve(reg: ModelRegistry, role_key: str, lane: str = "frontier") -> str:
    """Resolve a role key to a concrete model tag for the given lane.

    - Unknown role key -> RegistryError (fail loud; no silent guess).
    - `null` lane value -> "inherit" (use the host agent's own lead model;
      e.g. the deterministic_tool lens, which runs no model).
    - Unresolved `REPLACE_ME:` sentinel -> RegistryError (the user must pin a
      real model before use; we never invent or guess a tag).
    """
    if role_key not in reg.roles:
        raise RegistryError(f"unknown role key: {role_key!r} (not in {reg.source})")
    if lane not in _LANES:
        raise RegistryError(f"unknown lane: {lane!r} (expected one of {_LANES})")
    entry = reg.roles[role_key]
    value = entry.get(lane)
    # Fall back across lanes only among real (non-sentinel) values, then null->inherit.
    if value is None:
        for alt in _LANES:
            alt_val = entry.get(alt)
            if alt_val is not None and not is_sentinel(alt_val):
                return alt_val
        return "inherit"
    if is_sentinel(value):
        raise UnpinnedError(
            f"role {role_key!r} lane {lane!r} is unpinned ({value!r}); "
            f"edit {reg.source} to pin a real model, then re-run install"
        )
    return value


# model-name keyword -> provider FAMILY (the lineage whose blind spots correlate)
_FAMILIES = (
    ("claude", "anthropic"), ("anthropic", "anthropic"),
    ("qwen", "alibaba"),
    ("deepseek", "deepseek"),
    ("magistral", "mistral"), ("mixtral", "mistral"), ("mistral", "mistral"),
    ("gemma", "google"), ("gemini", "google"),
    ("gpt-oss", "openai"), ("gpt", "openai"), ("openai", "openai"),
    ("llama", "meta"), ("kimi", "moonshot"), ("glm", "zhipu"), ("phi", "microsoft"),
)


def provider_of(tag: str) -> str:
    """Best-effort provider FAMILY for a model tag (for diversity checks).

    Routing/label prefixes (`ollama/`, `openrouter/`, `anthropic:`…) are
    transport, not lineage — `ollama/qwen3:32b` and `qwen/qwen3-32b` are both
    the Alibaba family. `demo`/`tool` label non-model votes; `inherit` is the
    host session's (unknown) model."""
    t = (tag or "").strip().lower()
    if t in ("", "inherit"):
        return "host"
    if t in ("demo", "tool"):
        return t
    for prefix in ("ollama/", "openrouter/", "ollama:", "openrouter:", "anthropic:"):
        t = t.removeprefix(prefix)
    base = t.split("/", 1)[0] if "/" in t else t   # openrouter slug vendor segment
    for kw, family in _FAMILIES:
        if kw in base or (("/" in t) and kw in t):
            return family
    return "other"


def diversity_of(votes) -> dict:
    """Decision-time diversity: which provider families voted, how many DISTINCT
    ones, and whether the reasoning lenses were UNANIMOUS.

    Considers model lenses only (the deterministic tool lens is not a model voice;
    an unavailable lens never voted). Returns
    {families, distinct, lenses, monoculture, unanimous, note}:
      * `monoculture` names the one family when EVERY model lens resolved to it
        (the correlated-blind-spot condition).
      * `distinct` / `lenses` grade partial homogeneity — provider diversity is a
        weak proxy for reasoning diversity, so a low distinct-count is a caution
        even when it isn't a full monoculture.
      * `unanimous` flags when every counted lens cast the SAME vote. Agreement is
        NOT verification: a shared blind spot shows up as confident consensus, and
        for the adversarial cases a council is for, unanimity is exactly where that
        shared blind spot hides. Detection + honest surfacing, not enforcement."""
    fams: list[str] = []
    cast: list[str] = []
    for v in votes or []:
        if (v.get("provenance") or "") == "tool" or str(v.get("model", "")) == "tool":
            continue
        if str(v.get("vote", "")) == "unavailable":
            continue  # an unreachable lens never voted — it is an outage, not a voice
        fams.append(provider_of(str(v.get("model", ""))))
        cast.append(str(v.get("vote", "")))
    families = sorted(set(fams))
    lenses = len(cast)
    unanimous = (len(set(cast)) == 1) if lenses >= 2 else None
    base = {"families": families, "lenses": lenses, "distinct": 0, "unanimous": unanimous}
    if not families:
        return {**base, "monoculture": None, "note": "no model lenses voted"}
    if families == ["demo"]:
        return {**base, "monoculture": None, "note": "illustrative demo votes — no real models ran"}
    if families == ["host"]:
        return {**base, "monoculture": None,
                "note": "every lens inherited the host model — diversity unknown (single session)"}
    real = [f for f in families if f not in ("demo", "host")]
    distinct = len(set(real))
    base["distinct"] = distinct
    mono = real[0] if (len(real) == 1 and families == real) else None
    if mono:
        note = (f"every model lens resolves to one provider family ('{mono}') — "
                f"correlated blind spots; for cross-family diversity use OpenRouter (one key, "
                f"docs/OPENROUTER.md) or repin per docs/MODEL-GUIDANCE.md")
        if unanimous:
            note += " — and all lenses agreed (agreement is not verification)"
    else:
        note = f"{distinct} provider families across {lenses} lenses ({', '.join(real)})"
        if unanimous:
            note += (" — but all agreed: agreement is not verification (a shared blind spot can show up "
                     "as confident cross-family consensus) → a named human still owns this call")
    return {**base, "monoculture": mono, "note": note}


def monoculture(reg: ModelRegistry, lane: str = "frontier") -> str | None:
    """If every resolvable (non-null, non-sentinel) role on a lane maps to a
    single provider family, return that family (a correlated-blind-spot risk);
    else None. Used to warn that an all-one-vendor council undercuts the very
    premise of plural review."""
    providers = set()
    for role_key in reg.roles:
        try:
            tag = resolve(reg, role_key, lane)
        except RegistryError:
            continue
        fam = provider_of(tag)
        if fam != "host":
            providers.add(fam)
    return next(iter(providers)) if len(providers) == 1 else None


def inherits(reg: ModelRegistry, role_key: str, lane: str = "frontier") -> bool:
    """True if this role falls back to inheriting the host model on `lane` — i.e. the
    lane is unpinned (REPLACE_ME sentinel) or explicitly null/`inherit`. This is the
    intended BYO/on-device state (e.g. `--lane local` → run every lens on your session
    model), not necessarily a misconfiguration."""
    try:
        return resolve(reg, role_key, lane) == "inherit"
    except RegistryError:
        return True


def fallback_chain(reg: ModelRegistry, role_key: str, lane: str = "frontier") -> list[str]:
    """Optional per-role `fallback` list (continuity: provider cut-off). Returns
    the real (non-sentinel) fallback tags, in order; empty if none configured."""
    entry = reg.roles.get(role_key, {})
    chain = entry.get("fallback", []) or []
    return [m for m in chain if isinstance(m, str) and not is_sentinel(m)]


def unresolved(reg: ModelRegistry) -> list[str]:
    """Return `role_key:lane` for every lane still pinned to a REPLACE_ME
    sentinel. Cross-family/open/local lanes are expected to need pinning."""
    out: list[str] = []
    for role_key, entry in sorted(reg.roles.items()):
        for lane in _LANES:
            if is_sentinel(entry.get(lane)):
                out.append(f"{role_key}:{lane}")
    return out
