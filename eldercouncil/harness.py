# SPDX-License-Identifier: Apache-2.0
"""
Per-harness translation for the pre-tool gate path.

`eldercouncil gate <ide>` reads the harness's native pre-tool event on stdin,
scores the action with the risk gate, and emits the harness's native verdict +
exit code. This is the *selective-plurality* control: it decides whether a
council is needed, it does not run the council (that is the slash command /
orchestrator agent the install wired up).

  score 1-4   -> allow  (proceed; no council)
  score 5-15  -> ask    (convene the relevant council before proceeding)
  score 16-25 -> block  (council + a named human must approve)

`eldercouncil audit <ide>` records a lightweight post-tool gate event.

Verdict -> exit code: allow -> 0 (proceed), ask/block -> 2 (stop). Claude Code
carries the decision in JSON and exits 0 (its documented contract). Fail-safe:
an unparseable event blocks (exit 2), never a silent allow.
"""

from __future__ import annotations

import json
import sys

from . import audit
from .config import load_config
from .risk_gate import assess

_TOOL_ALIASES = {
    "bash": "bash", "shell": "bash", "execute_bash": "bash",
    "edit": "edit", "multiedit": "edit", "write": "write", "fs_write": "write",
    "read": "read", "fs_read": "read", "webfetch": "webfetch",
    "powershell": "powershell", "pwsh": "powershell", "cmd": "cmd",
}

# Keyword -> the council a human should convene for this class of action.
_SUGGEST = [
    (("git push", "npm publish", "docker push", "kubectl apply", "deploy", "release", "merge"), "code-council"),
    (("npm install", "pip install", "add dependency", "cargo add", "go get", "yarn add", "vendor"), "supply-chain"),
    (("alert", "siem", "edr", "suspicious", "login", "compromise", "incident"), "threat-hunting"),
    (("data residency", "cross-region", "transfer", "gdpr", "popia", "retention"), "compliance"),
    (("accept risk", "risk acceptance", "vulnerability", "remediation"), "cyber-risk"),
    (("architecture", "redesign", "platform", "migration", "adr"), "platform-architecture"),
]


def _normalize_tool(name: str) -> str:
    return _TOOL_ALIASES.get((name or "").lower(), (name or "").lower())


def _target_from_input(tool_input) -> str:
    if not isinstance(tool_input, dict):
        return str(tool_input)
    for key in ("command", "file_path", "path", "filePath", "target", "cmd", "url", "content"):
        if key in tool_input and tool_input[key]:
            return str(tool_input[key])
    return json.dumps(tool_input, ensure_ascii=False)


def _suggest_council(text: str) -> str:
    t = (text or "").lower()
    for keys, council in _SUGGEST:
        if any(k in t for k in keys):
            return council
    return "code-council"


def _verdict_for(route: str) -> str:
    if route == "SOLO_ALLOW":
        return "allow"
    if route == "COUNCIL_PLUS_HUMAN":
        return "block"
    return "ask"  # DUAL_REVIEW | FULL_COUNCIL


_ORDER = {"allow": 0, "ask": 1, "block": 2}


def _more_restrictive(a: str, b: str) -> str:
    return a if _ORDER[a] >= _ORDER[b] else b


def _gate_overlay(action: str, target: str, cfg) -> tuple[str, str, bool]:
    """Run the control gates pre-tool. Returns (gate_verdict, note, hard_stop).
    Maps the gate result to allow/ask/block; offensive-misuse is a hard stop."""
    try:
        from . import gates
        # Pre-tool runs only the DETECTOR gates (offensive hard-stop, secrets,
        # injection) — the decision-stage affirmative gates (action-safety etc.)
        # need council context and would otherwise collapse routing into block.
        report = gates.evaluate(cfg.profile, {}, action=action, target=target,
                                only=["offensive_misuse", "data_sensitivity", "context_integrity"],
                                affirmative=False)
    except Exception:  # noqa: BLE001 — gate policy issues must never crash the hook
        return "allow", "", False
    if report.hard_stopped:
        return "block", " ⛔ hard stop: offensive-cyber-misuse gate", True
    if report.result in ("block", "human_required"):
        names = ", ".join(o.gate for o in report.outcomes if o.result in ("block", "human_required"))
        return "block", f" control gate blocked: {names}", False
    if report.result == "escalate":
        names = ", ".join(o.gate for o in report.outcomes)
        return "ask", f" control gate flagged: {names}", False
    return "allow", "", False


def _decide(action: str, target: str) -> dict:
    rs = assess(f"{action} {target}")
    real = _verdict_for(rs.route)          # what the gate would do in enforce mode
    cfg = load_config()
    gate_verdict, gate_note, hard_stop = _gate_overlay(action, target, cfg)
    real = _more_restrictive(real, gate_verdict)
    council = _suggest_council(f"{action} {target}")
    base_reason = (
        f"risk {rs.score}/25 ({rs.level}) → {rs.route}.{gate_note} "
        + ("proceed (below the convene threshold)." if real == "allow"
           else f"convene the {council} council before proceeding." if real == "ask"
           else f"council + named-human approval required; convene the {council} council.")
    )
    # A hard stop is non-overridable — it blocks even in observe mode.
    if cfg.mode == "observe" and real != "allow" and not hard_stop:
        verdict = "allow"
        reason = f"[observe mode — not enforced] would {real}: {base_reason}"
    else:
        verdict, reason = real, base_reason
    return {"verdict": verdict, "observed": real, "reason": reason, "hard_stop": hard_stop,
            "council": council, "risk": {"score": rs.score, "level": rs.level, "route": rs.route}}


def _safe_gate_audit(action, target, d):
    # Record the OBSERVED (real) verdict so observe-mode entries are not misleading.
    try:
        audit.record_gate(action, target, d["risk"]["score"], d["risk"]["route"],
                          d.get("observed", d["verdict"]),
                          context={"reason": d.get("reason", ""), "enforced": d["verdict"]})
    except OSError:
        pass


def _gate_claude_code(event: dict) -> int:
    action = _normalize_tool(event.get("tool_name", ""))
    target = _target_from_input(event.get("tool_input", {}))
    d = _decide(action, target)
    _safe_gate_audit(action, target, d)
    perm = {"allow": "allow", "ask": "ask", "block": "deny"}[d["verdict"]]
    out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": perm}}
    if perm != "allow":
        out["hookSpecificOutput"]["permissionDecisionReason"] = f"Elder Council: {d['reason']}"
    print(json.dumps(out))
    return 0  # JSON carries the decision


def _gate_opencode(event: dict) -> int:
    action = _normalize_tool(event.get("tool", event.get("action", "")))
    raw = event.get("args", event.get("tool_input", {}))
    target = raw if isinstance(raw, str) else _target_from_input(raw)
    d = _decide(action, target)
    _safe_gate_audit(action, target, d)
    print(json.dumps(d))
    return 0 if d["verdict"] == "allow" else 2


def _gate_kiro(event: dict) -> int:
    action = _normalize_tool(event.get("tool_name", event.get("tool", "")))
    raw = event.get("tool_input", event.get("input", event.get("args", {})))
    target = raw if isinstance(raw, str) else _target_from_input(raw)
    d = _decide(action, target)
    _safe_gate_audit(action, target, d)
    print(json.dumps(d))
    if d["verdict"] != "allow":
        sys.stderr.write(f"Elder Council: {d['reason']}\n")
        return 2
    return 0


_GATES = {"claude-code": _gate_claude_code, "opencode": _gate_opencode, "kiro": _gate_kiro}


def _failsafe(ide: str, msg: str) -> int:
    """No usable event -> fail safe: ask (Claude Code, via JSON) / block (exit 2)."""
    if ide == "claude-code":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "ask",
            "permissionDecisionReason": f"Elder Council: {msg}"}}))
        return 0
    sys.stderr.write(f"Elder Council: {msg}\n")
    return 2


def run_gate(ide: str, stdin_text: str) -> int:
    handler = _GATES.get(ide)
    if handler is None:
        sys.stderr.write(f"unknown harness: {ide}\n")
        return 1
    text = (stdin_text or "").strip()
    if not text:
        # An empty pre-tool event is a failure mode, not a benign action — fail safe.
        return _failsafe(ide, "empty pre-tool event; failing safe (no action context)")
    try:
        event = json.loads(text)
    except json.JSONDecodeError:
        return _failsafe(ide, "could not parse harness event; failing safe")
    return handler(event)


def run_audit(ide: str, stdin_text: str) -> int:
    """Post-tool: record a lightweight gate event for the action just taken."""
    text = (stdin_text or "").strip()
    try:
        event = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return 0  # post-tool logging is best-effort; never fail the turn
    action = _normalize_tool(event.get("tool_name", event.get("tool", "")))
    raw = event.get("tool_input", event.get("args", {}))
    target = raw if isinstance(raw, str) else _target_from_input(raw)
    rs = assess(f"{action} {target}")
    try:
        audit.record_gate(action, target, rs.score, rs.route, "executed", context={"agent": ide, "phase": "post"})
    except OSError:
        pass
    return 0
