# SPDX-License-Identifier: Apache-2.0
"""
Risk gate — deterministic Impact x Likelihood scoring + escalation routing.

This is the *selective-plurality* control (the methodology's core principle):
most work never reaches a council. An action is scored 1-25 and routed:

    score 1-4   -> SOLO_ALLOW          deterministic tool / single agent
    score 5-9   -> DUAL_REVIEW         a second opinion (2-lens mini-council)
    score 10-15 -> FULL_COUNCIL        convene the full council
    score 16-25 -> COUNCIL_PLUS_HUMAN  council + a named human approves

A council convenes only at or above the configured threshold (default 5) — the
escalation-not-default rule. Below it, convening a council would add cost and
noise without improving the decision.

Two ways to score:
  * `score(impact, likelihood)` — the paper's model from explicit 1-5 ratings.
  * `compute_risk_score(action)` — a keyword heuristic for the pre-tool hook,
    where only a command/target string is available. The heuristic is
    deliberately conservative and bypassable by obfuscation (documented in the
    threat model); it routes, it does not adjudicate.

Pure, offline, zero-dependency (stdlib only). No LLM, no network, no I/O.
Same input always produces the same score, level, and route.
"""

from __future__ import annotations

from dataclasses import dataclass

# Impact signals — verbs/contexts that raise the consequence of being wrong.
# Deliberately NOT bare "delete" / "-f " (too noisy on benign dev commands — the
# gate over-firing trains users to ignore it). DB-specific deletes are in _DATABASE.
_DESTRUCTIVE = ("rm ", "rm -", "drop ", "destroy", "truncate", "overwrite",
                "--force", "--hard", "format ", "mkfs", "revoke", "isolate", "wipe", "purge")
_PRODUCTION = ("production", "prod", "deploy", "release", "kubectl apply", "terraform apply")
_SECRETS = ("credential", "secret", "api_key", "api-key", "apikey", "token", ".env",
            "private key", "id_rsa", ".pem", ".npmrc")
_DATABASE = ("database", " db ", "dropdb", "drop table", "delete from", "alter table")
_PUBLISH = ("git push", "npm publish", "docker push", "pip upload", "twine upload", "kubectl apply")

# Likelihood signals — things that make a bad outcome more likely to land.
_UNATTENDED = ("--force", "--yes", " -y", "sudo", "--no-verify", "--hard")
_REMOTE_EXEC = ("curl ", "wget ", "| bash", "| sh", "iwr ", "iex ", "invoke-expression", "powershell -enc")
_RECURSIVE = ("-rf", "-r ", "--recursive", "/*", "rm -rf", "remove-item -recurse")


def _clamp(value: int, low: int = 1, high: int = 5) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


@dataclass(frozen=True)
class RiskScore:
    impact: int        # 1-5
    likelihood: int    # 1-5
    score: int         # impact * likelihood, 1-25
    level: str         # low | medium | high | critical
    route: str         # SOLO_ALLOW | DUAL_REVIEW | FULL_COUNCIL | COUNCIL_PLUS_HUMAN
    reasoning: str


# (max_score, level, route) — the methodology's routing table.
_TIERS = [
    (4, "low", "SOLO_ALLOW"),
    (9, "medium", "DUAL_REVIEW"),
    (15, "high", "FULL_COUNCIL"),
    (25, "critical", "COUNCIL_PLUS_HUMAN"),
]


def level(score: int) -> str:
    score = max(1, min(25, int(score)))
    for max_score, lvl, _ in _TIERS:
        if score <= max_score:
            return lvl
    return "critical"


def route(score: int) -> str:
    """Map a 1-25 score to a decision path."""
    score = max(1, min(25, int(score)))
    for max_score, _, r in _TIERS:
        if score <= max_score:
            return r
    return "COUNCIL_PLUS_HUMAN"


def score(impact: int, likelihood: int, reasoning: str = "") -> RiskScore:
    """Score from explicit impact and likelihood ratings (1-5 each)."""
    impact = _clamp(impact)
    likelihood = _clamp(likelihood)
    s = impact * likelihood
    if not reasoning:
        reasoning = f"impact {impact} x likelihood {likelihood} = {s} ({level(s)})"
    return RiskScore(impact, likelihood, s, level(s), route(s), reasoning)


def _impact_of(text: str) -> int:
    impact = 1
    if any(h in text for h in _DESTRUCTIVE):
        impact += 3
    if any(h in text for h in _SECRETS):
        impact += 2
    if any(h in text for h in _PRODUCTION):
        impact += 2
    if any(h in text for h in _DATABASE):
        impact += 1
    if any(h in text for h in _PUBLISH):
        impact += 2  # publishing/deploying reaches users — a release is consequential
    return _clamp(impact)


def _likelihood_of(text: str) -> int:
    # An agent proposing an action is a moderate baseline; flags push it up.
    likelihood = 2
    if any(h in text for h in _UNATTENDED):
        likelihood += 1
    if any(h in text for h in _REMOTE_EXEC):
        likelihood += 1
    if any(h in text for h in _RECURSIVE):
        likelihood += 1
    return _clamp(likelihood)


def assess(action: str) -> RiskScore:
    """Heuristically score a free-text action/target string (the hook path)."""
    text = (action or "").lower()
    impact = _impact_of(text)
    likelihood = _likelihood_of(text)
    s = impact * likelihood
    return RiskScore(
        impact, likelihood, s, level(s), route(s),
        f"heuristic: impact {impact} x likelihood {likelihood} = {s} ({level(s)})",
    )


def compute_risk_score(action: str) -> int:
    """Convenience: just the 1-25 score for a free-text action (hook path)."""
    return assess(action).score
