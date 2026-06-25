# SPDX-License-Identifier: Apache-2.0
"""
Council definition schema — frozen dataclasses + validation.

A council is pure data (a YAML file). This module parses one into a validated
`Council`. Validation is strict and fails LOUD: `catalog.load_councils` turns a
schema error into a fail-closed state (the council is unusable, never silently
half-loaded). No model, no network — pure parse/validate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_MODES = ("advisory", "action-gate")
_FORMATS = ("json", "madr", "markdown")
_LANES = ("frontier", "open", "local")

# A council id becomes a filename and a slash-command name → strict slug only.
# (Prevents path traversal and breaking out of the CLAUDE.md sentinel comment.)
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_ROLE_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


class SchemaError(Exception):
    """Raised when a council definition is malformed."""


@dataclass(frozen=True)
class Role:
    name: str
    lens: str            # human description of the perspective (becomes the system prompt)
    role_key: str        # key into council-models.json (never a model tag)
    variant: str = "frontier"
    arbitrator: bool = False
    is_tool: bool = False  # deterministic_tool lens — runs checks, not a model


@dataclass(frozen=True)
class Trigger:
    condition: str
    min_risk_score: int = 5


@dataclass(frozen=True)
class Council:
    id: str
    name: str
    purpose: str
    mode: str                              # advisory | action-gate
    roles: tuple[Role, ...]
    decision_outcomes: tuple[str, ...]
    fail_closed: str
    triggers: tuple[Trigger, ...]
    output_path: str
    output_format: str                     # json | madr | markdown
    description: str = ""
    schedule: str | None = None            # optional cron (e.g. Compliance scheduled audit)

    @property
    def arbitrator(self) -> Role | None:
        for r in self.roles:
            if r.arbitrator:
                return r
        return None


def _require(d: dict, key: str, where: str) -> object:
    if key not in d or d[key] in (None, "", [], {}):
        raise SchemaError(f"{where}: missing required field {key!r}")
    return d[key]


def parse_role(d: dict, where: str) -> Role:
    if not isinstance(d, dict):
        raise SchemaError(f"{where}: role must be a mapping")
    name = str(_require(d, "name", where))
    lens = str(_require(d, "lens", where))
    role_key = str(_require(d, "role_key", where))
    if not _ROLE_KEY_RE.match(role_key):
        raise SchemaError(f"{where}: role_key {role_key!r} must match ^[a-z0-9][a-z0-9_]*$")
    variant = str(d.get("variant", "frontier"))
    if variant not in _LANES:
        raise SchemaError(f"{where}: role {name!r} has invalid variant {variant!r}")
    return Role(
        name=name,
        lens=lens,
        role_key=role_key,
        variant=variant,
        arbitrator=bool(d.get("arbitrator", False)),
        is_tool=bool(d.get("is_tool", False)),
    )


def parse_council(data: dict) -> Council:
    """Parse + validate one council definition dict into a Council."""
    if not isinstance(data, dict):
        raise SchemaError("council definition must be a mapping")
    cid = str(_require(data, "id", "council"))
    if not _ID_RE.match(cid):
        # id becomes a filename + slash-command + a sentinel-comment token; a lax id
        # would allow path traversal or breaking out of the CLAUDE.md comment block.
        raise SchemaError(f"council id {cid!r} must match ^[a-z0-9][a-z0-9-]*$ (lowercase slug)")
    where = f"council[{cid}]"

    mode = str(_require(data, "mode", where))
    if mode not in _MODES:
        raise SchemaError(f"{where}: invalid mode {mode!r} (expected one of {_MODES})")

    roles_raw = _require(data, "roles", where)
    if not isinstance(roles_raw, list) or not roles_raw:
        raise SchemaError(f"{where}: 'roles' must be a non-empty list")
    roles = tuple(parse_role(r, f"{where}.roles[{i}]") for i, r in enumerate(roles_raw))
    if sum(1 for r in roles if r.arbitrator) > 1:
        raise SchemaError(f"{where}: at most one role may be the arbitrator")

    outcomes_raw = _require(data, "decision_outcomes", where)
    if not isinstance(outcomes_raw, list) or not outcomes_raw:
        raise SchemaError(f"{where}: 'decision_outcomes' must be a non-empty list")

    triggers_raw = data.get("triggers", []) or []
    triggers: list[Trigger] = []
    for i, t in enumerate(triggers_raw):
        if not isinstance(t, dict) or "condition" not in t:
            raise SchemaError(f"{where}.triggers[{i}]: needs a 'condition'")
        try:
            mrs = int(t.get("min_risk_score", 5))
        except (TypeError, ValueError):
            raise SchemaError(f"{where}.triggers[{i}]: min_risk_score must be an int")
        triggers.append(Trigger(condition=str(t["condition"]), min_risk_score=max(1, min(25, mrs))))

    out = data.get("output", {}) or {}
    out_format = str(out.get("format", "json"))
    if out_format not in _FORMATS:
        raise SchemaError(f"{where}: output.format {out_format!r} invalid (expected one of {_FORMATS})")
    out_path = str(out.get("path", ".council/decisions/{id}-{ts}.json"))

    return Council(
        id=cid,
        name=str(_require(data, "name", where)),
        purpose=str(_require(data, "purpose", where)),
        mode=mode,
        roles=roles,
        decision_outcomes=tuple(str(o) for o in outcomes_raw),
        fail_closed=str(_require(data, "fail_closed", where)),
        triggers=tuple(triggers),
        output_path=out_path,
        output_format=out_format,
        description=str(data.get("description", "")),
        schedule=(str(data["schedule"]) if data.get("schedule") else None),
    )
