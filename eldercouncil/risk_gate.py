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

import re
from dataclasses import dataclass


def _compile(terms: tuple[str, ...]) -> re.Pattern:
    """Compile a keyword tuple into one alternation with word boundaries added
    only where a term starts/ends alphanumeric — so bare words stop matching
    INSIDE other words ('rm ' inside 'charm ', 'prod' inside 'reproduce',
    'token' inside 'tokenizer') while compound literals ('rm -', '--force',
    '| bash', 'git push') keep their exact semantics. Precision matters in both
    directions: an over-firing gate trains users to ignore it (cry-wolf); the
    under-firing direction stays the documented bypass limit."""
    parts = []
    for t in terms:
        p = re.escape(t)
        if t[0].isalnum():
            p = r"\b" + p
        if t[-1].isalnum():
            p = p + r"\b"
        parts.append(p)
    return re.compile("|".join(parts))


# Impact signals — verbs/contexts that raise the consequence of being wrong.
# Deliberately NOT bare "delete" / "-f " (too noisy on benign dev commands).
# DB-specific deletes are in _DATABASE. NOTE: "isolate" was removed — it is a
# legitimate threat-hunting OUTCOME (and containment verb), and an isolate VOTE
# already routes to a human via the consensus human-reserved rule.
_DESTRUCTIVE = _compile(("rm ", "rm -", "drop ", "destroy", "truncate", "overwrite",
                         "--force", "--hard", "format ", "mkfs", "fdisk", "dd if=",
                         "-delete", "chmod -r", "chmod 777", "chown -r", ":(){",
                         "revoke", "wipe", "purge"))
_PRODUCTION = _compile(("production", "prod", "deploy", "release", "kubectl apply", "terraform apply"))
_SECRETS = _compile(("credential", "secret", "api_key", "api-key", "apikey", "token", ".env",
                     "private key", "id_rsa", ".pem", ".npmrc"))
_DATABASE = _compile(("database", " db ", "dropdb", "drop table", "delete from", "alter table"))
_PUBLISH = _compile(("git push", "npm publish", "docker push", "pip upload", "twine upload", "kubectl apply"))
# Pipe-to-shell / remote code execution is an IMPACT signal (not just likelihood):
# piping a download straight into an interpreter runs arbitrary remote code.
_REMOTE_PIPE = _compile(("| bash", "| sh", "|bash", "|sh", "iex ", "invoke-expression", "powershell -enc"))

# Likelihood signals — things that make a bad outcome more likely to land.
_UNATTENDED = _compile(("--force", "--yes", " -y", "sudo", "--no-verify", "--hard"))
_REMOTE_EXEC = _compile(("curl ", "wget ", "| bash", "| sh", "iwr ", "iex ", "invoke-expression", "powershell -enc"))
_RECURSIVE = _compile(("-rf", "-r ", "--recursive", "/*", "rm -rf", "remove-item -recurse"))


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
    if _DESTRUCTIVE.search(text):
        impact += 3
    if _SECRETS.search(text):
        impact += 2
    if _PRODUCTION.search(text):
        impact += 2
    if _DATABASE.search(text):
        impact += 1
    if _PUBLISH.search(text):
        impact += 2  # publishing/deploying reaches users — a release is consequential
    if _REMOTE_PIPE.search(text):
        impact += 2  # piping a download into a shell executes arbitrary remote code
    return _clamp(impact)


def _likelihood_of(text: str) -> int:
    # An agent proposing an action is a moderate baseline; flags push it up.
    likelihood = 2
    if _UNATTENDED.search(text):
        likelihood += 1
    if _REMOTE_EXEC.search(text):
        likelihood += 1
    if _RECURSIVE.search(text):
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
