# SPDX-License-Identifier: Apache-2.0
"""
MCP server (FastMCP) — the ADVISORY path.

Exposes council tools any MCP-capable harness (Cursor, Claude Code, OpenCode,
Kiro, ...) can call. Advisory: the agent may call these and ignore the result.
Hard enforcement lives in the per-harness pre-tool gate hook (see install.py).

Elder Council ships NO model and NO keys: `convene_council` returns a BYO-LLM
deliberation task for the agent's OWN model(s) to run; the agent reports the
votes back via `audit_log`, which tallies them deterministically and records the
decision.

Requires the optional dependency: pip install 'eldercouncil[mcp]'
"""

from __future__ import annotations

from . import audit, gates, models
from .audit import _disposition
from .catalog import get_council
from .config import load_config
from .consensus import coerce_host_provenance, tally
from .convene import build_review
from .models import load_registry
from .risk_gate import assess
from .schema import SchemaError

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise ImportError("MCP server requires the [mcp] extra: pip install 'eldercouncil[mcp]'") from exc

mcp = FastMCP("eldercouncil")


@mcp.tool()
def risk_gate(action: str, target: str = "") -> dict:
    """Score a proposed action (impact x likelihood, 1-25) and route it.

    Returns {score, level, route}. route is SOLO_ALLOW (no council),
    DUAL_REVIEW / FULL_COUNCIL (convene a council), or COUNCIL_PLUS_HUMAN
    (council + a named human approves). Advisory — convene only at/above the
    threshold; do not convene a council for routine work.
    """
    rs = assess(f"{action} {target}")
    return {"score": rs.score, "level": rs.level, "route": rs.route, "reasoning": rs.reasoning}


@mcp.tool()
def convene_council(council_id: str, question: str, lane: str = "") -> dict:
    """Return a BYO-LLM deliberation task for a named council — your model runs it.

    Pick `council_id` from: code-council, threat-hunting, supply-chain,
    compliance, cyber-risk, platform-architecture, business-decision, eng-team. Run each lens task
    with your own model(s), collect one vote per lens, then call `audit_log` with the
    votes to get the tallied verdict and record the decision. Ships no keys.
    """
    try:
        council = get_council(council_id)
    except SchemaError as exc:
        return {"error": str(exc)}
    reg = load_registry()
    lane = lane or load_config().lane
    return build_review(council, question, reg, lane)


@mcp.tool()
def audit_log(council: str, question: str, verdicts: list, context: dict | None = None) -> dict:
    """Tally reported council votes, record the decision, and return the verdict.

    `verdicts` is a list of {role, model, vote, confidence, reason} — one per
    lens. Applies Elder Council consensus (ties block; escalation wins;
    risk-acceptance/critical/advisory route to a human) and writes a
    hash-chained decision record + dissent to `.council/`.

    On this HOST-REPORTED path the harness cannot authenticate the reported
    votes, so it (a) coerces any claimed tool/demo provenance to host-asserted,
    (b) RE-RUNS the deterministic tool lens itself (the host cannot omit or forge
    the authoritative tool finding — its detectors run server-side over the
    question + configured [tools]), (c) records any roles that do not match the
    council's declared lenses (a forged/renamed lens is then evident), and (d)
    verifies (or honestly labels "asserted — unverified") any host-asserted
    `human_approver` via the SAME fail-closed check as the engine, so a
    self-asserted approval cannot silently relax a gate-blocked action.
    """
    try:
        c = get_council(council)
    except SchemaError as exc:
        return {"error": str(exc)}
    votes = coerce_host_provenance(verdicts)
    # (b) The tool lens is deterministic — compute it here rather than trust the
    # host's self-reported tool vote. Replace any host vote carrying the tool
    # role with the genuine server-run finding.
    tool_role = next((r.name for r in c.roles if getattr(r, "is_tool", False)), None)
    if tool_role:
        from .toollens import run_tool_lens
        votes = [v for v in votes
                 if not (isinstance(v, dict) and str(v.get("role")) == tool_role)]
        votes.append(run_tool_lens(tool_role, question, list(c.decision_outcomes)))
    # (c) Flag reported lenses that are not part of this council.
    expected = {r.name for r in c.roles}
    reported = {str(v.get("role")) for v in (verdicts or []) if isinstance(v, dict)}
    off_council = sorted(reported - expected)
    ctx = dict(context or {})
    if off_council:
        ctx["off_council_roles"] = off_council
    # Councils without a deterministic tool lens cannot authenticate any reasoning
    # votes on this host-reported path — record that limit honestly.
    if tool_role is None:
        ctx["host_reported_only"] = True
    outcome = tally(votes, c)
    diversity = models.diversity_of(outcome.votes)
    # Apply the same fail-closed control gates as the engine/orchestrate paths so
    # the MCP path's disposition is the most restrictive of council route and gate
    # result. Gate failures escalate (fail closed).
    profile = load_config().profile
    # (d) Verify (or honestly label) any host-asserted human approval BEFORE the
    # gates see it — the SAME fail-closed check the engine path runs. The MCP host
    # cannot authenticate a person: with an approval_verify_command configured, a
    # failed check STRIPS the assertion so the gates escalate as if no approval
    # existed; with none configured, it passes through but is RECORDED as
    # "asserted — unverified". Without this, a client could self-assert human_approver
    # and silently relax a gate-blocked destructive action with no trace.
    from .approval import check_approval
    signals, approval = check_approval(ctx.get("signals", {}) or {})
    if "signals" in ctx:
        ctx["signals"] = signals  # record the signals the gates actually saw (stripped on failed verification)
    try:
        report = gates.evaluate(profile, signals, action=question, target="",
                                outcome=outcome, council=c)
        gate_report = report.to_dict()
    except Exception as exc:  # noqa: BLE001
        gate_report = {"result": "escalate",
                       "error": f"gate evaluation error — fail closed ({type(exc).__name__}: {exc})"}
    disposition = _disposition(outcome, gate_report)
    did = audit.record(c.id, question, outcome, mode=c.mode, context=ctx, diversity=diversity,
                       gate_report=gate_report, profile=profile, approval=approval)
    return {"decision_id": did, "verdict": outcome.verdict, "route": outcome.route,
            "rationale": outcome.rationale, "dissent": outcome.dissent,
            "diversity": diversity, "disposition": disposition, "gate_report": gate_report,
            **({"approval": approval} if approval else {}),
            **({"off_council_roles": off_council} if off_council else {})}


@mcp.tool()
def audit_summary() -> dict:
    """Aggregate the council decision log (verdicts, routes, dissent rate)."""
    return audit.summary()


def run() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    run()
