# SPDX-License-Identifier: Apache-2.0
"""
Invariant checks for agentic UAT — structural, not text-exact.

A scenario passes when the agentic loop demonstrably fired:
  * the CORRECT council convened (a decision record exists with that id),
  * the verdict is in the expected CLASS (not an exact string),
  * the route matches (auto / lead_dev / human),
  * dissent was preserved when the scenario expects disagreement.
"""

from __future__ import annotations

import json
from pathlib import Path


def _decisions(council_dir: Path, council_id: str) -> list[dict]:
    d = council_dir / "decisions"
    out = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if rec.get("council") == council_id:
            out.append(rec)
    return out


def check(spec: dict, council_dir: Path) -> tuple[bool, str]:
    council = spec["council"]
    expect = spec.get("expect", {})
    recs = _decisions(council_dir, council)
    if not recs:
        return False, f"no decision record for council '{council}' (loop did not fire)"
    rec = recs[-1]

    if "route" in expect and rec.get("route") != expect["route"]:
        return False, f"route {rec.get('route')!r} != expected {expect['route']!r}"
    if "verdicts" in expect and rec.get("verdict") not in expect["verdicts"]:
        return False, f"verdict {rec.get('verdict')!r} not in {expect['verdicts']}"
    if expect.get("dissent") and not rec.get("dissent"):
        return False, "expected preserved dissent, found none"
    return True, f"convened · verdict={rec.get('verdict')} route={rec.get('route')} dissent={len(rec.get('dissent', []))} id={rec.get('decision_id')}"
