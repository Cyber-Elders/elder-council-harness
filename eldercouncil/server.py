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

from . import audit
from .catalog import get_council
from .config import load_config
from .consensus import tally
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
    compliance, cyber-risk, platform-architecture. Run each lens task with your
    own model(s), collect one vote per lens, then call `audit_log` with the
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
    """
    try:
        c = get_council(council)
    except SchemaError as exc:
        return {"error": str(exc)}
    outcome = tally(verdicts, c)
    did = audit.record(c.id, question, outcome, mode=c.mode, context=context or {})
    return {"decision_id": did, "verdict": outcome.verdict, "route": outcome.route,
            "rationale": outcome.rationale, "dissent": outcome.dissent}


@mcp.tool()
def audit_summary() -> dict:
    """Aggregate the council decision log (verdicts, routes, dissent rate)."""
    return audit.summary()


def run() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    run()
