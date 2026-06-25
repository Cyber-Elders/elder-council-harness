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


def verify_wiring(ide: str, project, council: str) -> tuple[bool, str]:
    """Confirm `install` actually produced the IDE's pre-tool gate wiring + the
    council's rendered files — so a BROKEN adapter fails the UAT instead of passing
    on a zero install exit code alone (the install return code is only a smoke test)."""
    p = Path(project)
    if ide == "claude-code":
        settings = p / ".claude" / "settings.json"
        if not settings.exists():
            return False, ".claude/settings.json missing"
        hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
        cmds = [h.get("command") for e in hooks.get("PreToolUse", []) for h in e.get("hooks", [])]
        if "eldercouncil gate claude-code" not in cmds:
            return False, "PreToolUse gate hook not wired"
        if not (p / ".claude" / "commands" / f"{council}.md").exists():
            return False, f"/{council} command not rendered"
        if not (p / ".mcp.json").exists():
            return False, ".mcp.json (advisory MCP) missing"
        return True, "wired"
    if ide == "opencode":
        if not (p / ".opencode" / "plugins" / "eldercouncil.js").exists():
            return False, "gate plugin missing"
        oc = json.loads((p / "opencode.json").read_text(encoding="utf-8")) if (p / "opencode.json").exists() else {}
        if "eldercouncil" not in oc.get("mcp", {}):
            return False, "MCP server not registered"
        return True, "wired"
    return True, "wiring check skipped (advisory IDE)"


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
    if expect.get("dissent"):
        diss = rec.get("dissent") or []
        if not diss:
            return False, "expected preserved dissent, found none"
        # Substantive, not tautological: every preserved dissent must carry its reasoning
        # and a vote that actually differs from the verdict (where lenses disagree is the signal).
        if any(not str(d.get("reason", "")).strip() for d in diss):
            return False, "a preserved-dissent entry has no reasoning"
        if any(d.get("vote") == rec.get("verdict") for d in diss):
            return False, "a 'dissent' entry agrees with the verdict (not real dissent)"
    return True, f"convened · verdict={rec.get('verdict')} route={rec.get('route')} dissent={len(rec.get('dissent', []))} id={rec.get('decision_id')}"
