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

    mode = os.environ.get("COUNCIL_MODE") or gov.get("mode", "enforce")
    lane = os.environ.get("COUNCIL_LANE") or council.get("lane", "frontier")
    profile = os.environ.get("COUNCIL_PROFILE") or gov.get("profile", "standard")
    try:
        threshold = int(os.environ.get("COUNCIL_THRESHOLD") or council.get("convene_threshold", 5))
    except (TypeError, ValueError):
        threshold = 5
    lane = lane if lane in ("frontier", "open", "local") else "frontier"
    profile = profile if profile in ("lite", "standard", "regulated") else "standard"
    return Config(
        tier=str(gov.get("tier", "practitioner")),
        mode="observe" if str(mode).lower() == "observe" else "enforce",
        lane=lane,
        convene_threshold=max(1, min(25, threshold)),
        profile=profile,
    )
