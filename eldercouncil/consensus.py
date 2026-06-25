# SPDX-License-Identifier: Apache-2.0
"""
Consensus — combine council votes into a verdict, honouring the methodology's
*minimum governance rules*.

The council votes are non-deterministic (they come from LLM lenses and/or human
SMEs). This module is the deterministic, pure boundary that combines them: feed
it a list of votes + the council definition and it returns a verdict and a route
(who decides next). Same votes + same council -> same Outcome. No model, no
network, no clock.

Minimum governance rules (applied uniformly, from the public methodology):
  * Empty / no quorum            -> conservative block.
  * Too many lenses unavailable  -> 'inconclusive' (the council did NOT convene),
                                    routed to a human — never a deliberated-looking block.
  * Ties                         -> most-restrictive outcome, routed to a human.
  * Escalation wins              -> any 'escalate*' vote routes to a human.
  * CRITICAL (authoritative)     -> a CRITICAL finding from a deterministic-tool
                                    lens (or any lens if the council has none) blocks.
  * Risk-acceptance / irreversible -> route to a human, never auto.
  * Advisory councils            -> never auto-decide; a human owns the call.
  * Permissive + any blocking dissent present -> route to a human (a lens that
                                    wants to stop is never silently outvoted into auto).
  * Low confidence on a permissive verdict -> route to a human.
  * Unknown vote tokens          -> treated as a conservative abstention.

`route` is who decides next: "auto" (verdict stands, action proceeds),
"lead_dev" (developer review), or "human" (a named human must decide/approve).
`permits_action()` is True only when route == "auto" and the verdict is permissive.

NOTE on severity (honest limit): `severity` is a lens-ASSERTED signal, not an
authenticated one. A council with a deterministic-tool lens only honours CRITICAL
from that lens (so a prompt-injected reasoning lens cannot unilaterally force a
block); a council without one honours any CRITICAL (fail-closed). The ABSENCE of
a severity field does NOT mean "not critical" — see THREAT_MODEL.md.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# Outcomes that mean "stop / do not proceed".
_BLOCKING = {"block", "reject", "defer"}
# Outcome that routes to developer review rather than a full human-owner sign-off.
_DEV_REVIEW = {"request-changes"}
# Outcomes that must ALWAYS be a human decision (risk acceptance / irreversible).
_HUMAN_RESERVED = {"accept", "isolate"}
# Lens could not be reached / declined to vote — counted, but not as a verdict.
_ABSTAIN = {"abstain", "unavailable", "n/a", "none", ""}

# Word confidences the deliberation protocol asks lenses to emit.
_CONF_WORDS = {"low": 0.3, "medium": 0.6, "high": 0.9}

# Restrictiveness ranking for conservative tie-breaks. PRINCIPLE: higher = more
# cautious / more withholding; a tie resolves to the most cautious tied outcome.
# Ordered from "stop / escalate" down through "proceed with conditions" to
# "proceed freely". (Risk-acceptance 'accept' is low here — accepting risk is the
# least cautious treatment — but it is human-reserved and always routes to a human
# regardless of this value.)
_RESTRICTIVENESS = {
    "escalate-to-counsel": 99, "escalate": 98, "isolate": 96, "block": 94, "reject": 92,
    "avoid": 80, "defer": 78, "request-changes": 70, "mitigate": 55, "transfer": 50,
    "approve-with-controls": 45, "contain": 40, "recommend-with-guardrails": 35,
    "monitor": 30, "proceed-with-controls": 28, "observe": 22, "recommend": 18,
    "accept": 15, "approve": 12, "merge": 10, "allow": 10,
}

_PERMISSIVE_CONFIDENCE_FLOOR = 0.5


@dataclass(frozen=True)
class Vote:
    role: str
    model: str
    vote: str                    # one of the council's decision_outcomes (or 'abstain')
    confidence: float = 0.5      # 0.0-1.0
    reason: str = ""
    severity: str | None = None  # optional, lens-asserted (e.g. CRITICAL|HIGH|MEDIUM|LOW)


@dataclass(frozen=True)
class Outcome:
    verdict: str                 # the chosen decision outcome
    route: str                   # auto | lead_dev | human
    rationale: str
    dissent: list = field(default_factory=list)   # votes that differ from the verdict
    votes: list = field(default_factory=list)

    def permits_action(self) -> bool:
        """True only when the verdict lets an action proceed automatically."""
        return self.route == "auto" and self.verdict not in (
            _BLOCKING | _DEV_REVIEW | _HUMAN_RESERVED | {"escalate", "inconclusive"}
        )

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "route": self.route,
            "rationale": self.rationale,
            "dissent": list(self.dissent),
            "votes": list(self.votes),
        }


def _restrictiveness(outcome: str) -> int:
    return _RESTRICTIVENESS.get(outcome, 75)  # unknown -> cautious (errs toward withholding)


def _coerce_confidence(value) -> float:
    """Tolerant confidence parse: the protocol asks for Low/Medium/High words,
    but a numeric is also accepted. Clamp to [0,1]; default 0.5 on anything odd."""
    if isinstance(value, str):
        w = value.strip().lower()
        if w in _CONF_WORDS:
            return _CONF_WORDS[w]
        try:
            value = float(w)
        except ValueError:
            return 0.5
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def _is_escalation(token: str) -> bool:
    return token == "escalate" or token.startswith("escalate")


def _normalize(votes, valid: set[str]) -> list[Vote]:
    """Build Votes, coerce confidence, lowercase tokens, and map any token that
    is not one of the council's declared outcomes (and not an abstention or an
    escalation) to a conservative 'abstain' — an unknown token never wins or
    auto-permits."""
    norm: list[Vote] = []
    for v in votes or []:
        if isinstance(v, Vote):
            role, model, vote, conf, reason, sev = v.role, v.model, v.vote, v.confidence, v.reason, v.severity
            conf = _coerce_confidence(conf)
        elif isinstance(v, dict):
            role = str(v.get("role", "?"))
            model = str(v.get("model", "?"))
            vote = str(v.get("vote", "abstain"))
            conf = _coerce_confidence(v.get("confidence", 0.5))
            reason = str(v.get("reason", ""))
            sev = v.get("severity")
        else:
            continue
        token = (vote or "").strip().lower()
        if valid and token not in valid and token not in _ABSTAIN and not _is_escalation(token):
            reason = (f"[unrecognised vote {token!r} → abstain] " + reason).strip()
            token = "abstain"
        norm.append(Vote(role, model, token, conf, reason, sev))
    return norm


def _dissent(norm: list[Vote], verdict: str) -> list[dict]:
    return [
        {"role": v.role, "vote": v.vote, "confidence": v.confidence, "reason": v.reason}
        for v in norm if v.vote != verdict
    ]


def _restrictive_valid(valid: set[str], fallback: str = "block") -> str:
    """The most-restrictive of a council's declared outcomes (for CRITICAL /
    inconclusive verdicts that must be a valid token)."""
    if valid:
        return max(valid, key=_restrictiveness)
    return fallback


def tally(votes, council) -> Outcome:
    """Combine votes into an Outcome for the given council.

    `council` may be a `schema.Council` or any object exposing `.mode`,
    `.roles`, and `.decision_outcomes` (a duck-typed stub is fine for tests).
    """
    mode = getattr(council, "mode", "action-gate")
    roles = getattr(council, "roles", ()) or ()
    n_roles = len(roles)
    valid = {str(o).strip().lower() for o in (getattr(council, "decision_outcomes", ()) or ())}
    tool_roles = {getattr(r, "name", "") for r in roles if getattr(r, "is_tool", False)}

    norm = _normalize(votes, valid)
    all_votes = [
        {"role": v.role, "model": v.model, "vote": v.vote, "confidence": v.confidence,
         "reason": v.reason, **({"severity": v.severity} if v.severity else {})}
        for v in norm
    ]

    # --- conservative default: nothing to combine ---------------------------
    if not norm:
        return Outcome("block", "human", "no votes — conservative default", [], [])

    # --- CRITICAL severity from an AUTHORITATIVE lens blocks outright -------
    # If the council has a deterministic-tool lens, only its CRITICAL is honoured
    # (a reasoning lens cannot unilaterally force a block / be injection-steered);
    # otherwise any lens's CRITICAL is honoured (fail-closed).
    crit = next((v for v in norm if (v.severity or "").upper() == "CRITICAL"
                 and (not tool_roles or v.role in tool_roles)), None)
    if crit:
        # "block" if the council has it (CRITICAL = stop); else its most-restrictive outcome.
        verdict = "block" if "block" in valid else _restrictive_valid(valid)
        return Outcome(verdict, "human",
                       f"a lens rated this CRITICAL ({crit.role}) — blocked pending human review",
                       _dissent(norm, verdict), all_votes)

    # --- escalation wins ----------------------------------------------------
    esc = next((v.vote for v in norm if _is_escalation(v.vote)), None)
    if esc:
        return Outcome(esc, "human", "a lens voted to escalate — routed to a human",
                       _dissent(norm, esc), all_votes)

    # --- reachability: abstentions/outages are NOT votes --------------------
    reachable = [v for v in norm if v.vote not in _ABSTAIN]
    unavailable = len(norm) - len(reachable)
    if not reachable:
        return Outcome("inconclusive", "human",
                       f"the council did not convene ({unavailable} lens(es) unavailable/abstained)",
                       _dissent(norm, "inconclusive"), all_votes)
    if n_roles:
        quorum = (n_roles // 2) + 1
        if len(reachable) < quorum:
            return Outcome("inconclusive", "human",
                           f"the council did not convene ({len(reachable)}/{n_roles} lenses reached, "
                           f"need {quorum}; {unavailable} unavailable) — not a deliberated verdict",
                           _dissent(norm, "inconclusive"), all_votes)

    # --- plurality (conservative tie-break over reachable votes) ------------
    counts = Counter(v.vote for v in reachable)
    top = counts.most_common()
    winner_count = top[0][1]
    winners = [outcome for outcome, c in top if c == winner_count]
    tie = len(winners) > 1
    verdict = max(winners, key=_restrictiveness) if tie else winners[0]

    mean_conf = (sum(v.confidence for v in reachable if v.vote == verdict)
                 / max(1, sum(1 for v in reachable if v.vote == verdict)))
    blocking_dissent = [v for v in reachable
                        if v.vote != verdict and (v.vote in _BLOCKING or v.vote in _HUMAN_RESERVED)]

    # --- route (who decides next) ------------------------------------------
    if tie:
        route, why = "human", f"tie ({' / '.join(sorted(winners))}) — most restrictive, routed to a human"
    elif verdict in _HUMAN_RESERVED:
        route, why = "human", f"'{verdict}' is a human-accountability decision — never automated"
    elif mode == "advisory":
        route, why = "human", f"advisory council — recommends '{verdict}', a human decides"
    elif verdict in _BLOCKING:
        route, why = "human", f"'{verdict}' under '{mode}' — action withheld, human review"
    elif verdict in _DEV_REVIEW:
        route, why = "lead_dev", f"'{verdict}' — returned to the developer"
    elif blocking_dissent:
        names = ", ".join(sorted({v.vote for v in blocking_dissent}))
        route, why = "human", (f"'{verdict}' would carry, but {len(blocking_dissent)} lens(es) "
                               f"dissented to stop ({names}) — routed to a human, not auto")
    elif mean_conf < _PERMISSIVE_CONFIDENCE_FLOOR:
        route, why = "human", f"'{verdict}' but low confidence ({mean_conf:.2f}) — routed to a human"
    else:
        suffix = f" ({unavailable} lens(es) unavailable)" if unavailable else ""
        route, why = "auto", f"'{verdict}' carries under '{mode}' ({winner_count}/{len(reachable)} votes){suffix}"

    return Outcome(verdict, route, why, _dissent(norm, verdict), all_votes)
