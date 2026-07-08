# SPDX-License-Identifier: Apache-2.0
"""
Config loader — reads `.council/config.toml` (stdlib tomllib, no dependency).

Holds the governance tier, the enforce/observe mode, the default model lane
(frontier | open | local), and the convene threshold (the risk score at or
above which a council is convened — the escalation-not-default control).
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import paths


@dataclass(frozen=True)
class Config:
    tier: str = "practitioner"          # explorer | practitioner | governed | operator
    mode: str = "enforce"               # enforce | observe (observe = log/advise, never block)
    lane: str = "frontier"              # default model lane: frontier | open | local
    convene_threshold: int = 5          # risk score >= this convenes a council (selective plurality)
    profile: str = "standard"           # gate profile: lite | standard | regulated
    redact: bool = True                 # [audit] redact secrets/PII before persisting records


def load_config(path: str | Path | None = None) -> Config:
    p = Path(path) if path else paths.config_path()
    data: dict = {}
    if p.exists():
        try:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            data = {}
    gov = data.get("governance", {}) or {}
    council = data.get("council", {}) or {}
    audit = data.get("audit", {}) or {}

    mode = os.environ.get("COUNCIL_MODE") or gov.get("mode", "enforce")
    lane = os.environ.get("COUNCIL_LANE") or council.get("lane", "frontier")
    profile = os.environ.get("COUNCIL_PROFILE") or gov.get("profile", "standard")
    try:
        threshold = int(os.environ.get("COUNCIL_THRESHOLD") or council.get("convene_threshold", 5))
    except (TypeError, ValueError):
        threshold = 5
    lane = lane if lane in ("frontier", "open", "local") else "frontier"
    profile = profile if profile in ("lite", "standard", "regulated") else "standard"
    # Redaction defaults ON; only an explicit false disables it (fail-safe).
    redact_raw = os.environ.get("COUNCIL_REDACT")
    if redact_raw is None:
        redact_raw = audit.get("redact", True)
    redact = str(redact_raw).strip().lower() not in ("false", "0", "no", "off")
    return Config(
        tier=str(gov.get("tier", "practitioner")),
        mode="observe" if str(mode).lower() == "observe" else "enforce",
        lane=lane,
        convene_threshold=max(1, min(25, threshold)),
        profile=profile,
        redact=redact,
    )


_POLICY_ENV = ("COUNCIL_MODE", "COUNCIL_PROFILE", "COUNCIL_THRESHOLD", "COUNCIL_LANE", "COUNCIL_REDACT")


def env_overrides() -> dict:
    """Which security knobs are being set by ENVIRONMENT VARIABLE right now.

    Env vars override config.toml (useful for a one-off `COUNCIL_MODE=observe` run),
    but a silent downgrade (observe / lite profile / raised threshold / redaction off)
    should leave a TRACE. The gate + decision records include this map so an audit
    reader can see enforcement was operator-downgraded at the environment layer —
    e.g. an injected `.envrc` or wrapper script. Values are recorded verbatim."""
    return {k: os.environ[k] for k in _POLICY_ENV if os.environ.get(k) is not None}


# Fixed allowlist of [tools] KEYS the tool lens honours (unknown keys are ignored).
# The command CONTENT is operator-controlled — config.toml is code; see THREAT_MODEL.
_TOOL_KEYS = ("secret_scan_cmd", "sast_cmd", "dependency_scan_cmd", "test_cmd", "policy_cmd")


def tool_commands(path: str | Path | None = None) -> dict[str, str]:
    """The optional `[tools]` section — real, operator-configured commands the
    deterministic tool lens executes (e.g. `secret_scan_cmd = "gitleaks detect ..."`).
    Returns {} when unset; only allowlisted keys are honoured."""
    p = Path(path) if path else paths.config_path()
    if not p.exists():
        return {}
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    tools = data.get("tools", {}) or {}
    return {k: str(v) for k, v in tools.items() if k in _TOOL_KEYS and v}


def approval_verify_command(path: str | Path | None = None) -> str | None:
    """The optional `[signals] approval_verify_command` — when set, a human_approver
    assertion is only accepted after this command exits 0 (see approval.py)."""
    p = Path(path) if path else paths.config_path()
    if not p.exists():
        return None
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    cmd = (data.get("signals", {}) or {}).get("approval_verify_command")
    return str(cmd) if cmd else None


def anchor_command(path: str | Path | None = None) -> str | None:
    """The optional `[audit] anchor_command` — when set, `eldercouncil anchor --run`
    pipes the chain head + count (JSON on stdin; EC_HEAD/EC_COUNT in the env) to it,
    so an operator can capture the anchor off-box (syslog, a webhook, a WORM path, a
    signed git commit). Operator-controlled allowlisted command, same trust model as
    `approval_verify_command` — `config.toml` is code."""
    p = Path(path) if path else paths.config_path()
    if not p.exists():
        return None
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    cmd = (data.get("audit", {}) or {}).get("anchor_command")
    return str(cmd) if cmd else None
