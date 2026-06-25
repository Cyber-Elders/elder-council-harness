# SPDX-License-Identifier: Apache-2.0
"""
Engine — the one non-deterministic seam, isolated behind an injected vote source.

`convene()` builds the deliberation tasks (pure), obtains votes from an injected
`vote_source`, then runs the PURE `consensus.tally`. Because the vote source is
injected, the whole tally -> route -> audit path is testable with mocked votes
and never touches a model or the network in tests.

Three vote sources:
  * tasks_only  (default)  -> returns the deliberation tasks for the host agent;
                              no model is run here, no tally (the host tallies).
  * demo_votes  (--demo)   -> deterministic, illustrative votes (keyless, CI-safe)
                              so `convene --demo` shows a real, contested verdict.
  * orchestrator (--orchestrate) -> the optional BYO-LLM runner ([orchestrator]).
"""

from __future__ import annotations

from . import audit, convene, gates
from .config import load_config
from .consensus import tally
from .models import ModelRegistry


def convene_with_votes(council, question: str, votes, registry: ModelRegistry,
                       *, lane: str = "frontier", risk: dict | None = None,
                       context: dict | None = None, do_audit: bool = True,
                       signals: dict | None = None, profile: str | None = None) -> dict:
    """Tally injected votes, run the deterministic control gates over the decision,
    and assemble a decision record (optionally persisted).

    The gates are a fail-closed layer AROUND the council: a gate can withhold an
    action the council voted to permit (the record's `disposition` is the most
    restrictive of the council route and the gate result)."""
    outcome = tally(votes, council)
    profile = profile or load_config().profile
    try:
        report = gates.evaluate(profile, signals or {}, action=question, target="",
                                outcome=outcome, council=council)
        gate_report = report.to_dict()
    except gates.GatePolicyError:
        gate_report = {"result": "escalate", "error": "gate policy unavailable — fail closed"}
    rec = audit.build_record(council.id, question, outcome, mode=council.mode,
                             risk=risk or {}, context=context or {},
                             gate_report=gate_report, profile=profile)
    if do_audit:
        try:
            audit.record(council.id, question, outcome, mode=council.mode,
                         risk=risk or {}, context=context or {},
                         gate_report=gate_report, profile=profile)
        except OSError:
            pass  # never let an audit-write failure swallow the verdict
    return rec


# --------------------------------------------------------------------------
# Deterministic demo votes — illustrative only. Each shows a *contested*
# decision so dissent is visible (the whole point of a council). These are NOT
# real model outputs; they are canned to demonstrate the machinery keylessly.
# --------------------------------------------------------------------------
_DEMO = {
    "code-council": [
        {"role": "Software Engineering SME", "model": "demo", "vote": "merge", "confidence": 0.6,
         "reason": "Clean structure, tests pass."},
        {"role": "AppSec SME", "model": "demo", "vote": "block", "confidence": 0.9, "severity": "HIGH",
         "reason": "Hardcoded secret + unparameterised SQL in the diff."},
        {"role": "Reliability / Operations SME", "model": "demo", "vote": "merge", "confidence": 0.55,
         "reason": "Rollback path exists."},
        # The CRITICAL comes from the deterministic TOOL lens (an authoritative scanner
        # finding), not a reasoning model — so it isn't a single injectable opinion.
        {"role": "Deterministic Tool Lens", "model": "tool", "vote": "block", "confidence": 0.95,
         "severity": "CRITICAL", "reason": "secret-scan: AWS key detected; SAST: SQLi sink."},
        {"role": "Critic / Challenge", "model": "demo", "vote": "request-changes", "confidence": 0.7,
         "reason": "Auth check is assumed, not verified, on the new route."},
    ],
    "threat-hunting": [
        {"role": "Threat Hunter / Security SME", "model": "demo", "vote": "contain", "confidence": 0.6,
         "reason": "Privileged login from a new ASN at 02:00 fits a credential-theft pattern."},
        {"role": "Detection Engineer", "model": "demo", "vote": "observe", "confidence": 0.5,
         "reason": "No corroborating EDR telemetry; could be travel."},
        {"role": "Platform / Infrastructure SME", "model": "demo", "vote": "observe", "confidence": 0.55,
         "reason": "This account does occasionally roam."},
        {"role": "Adversarial / Red-Team", "model": "demo", "vote": "contain", "confidence": 0.65,
         "reason": "If real, the next step is token theft + lateral movement."},
        {"role": "Incident Response Owner", "model": "demo", "vote": "escalate", "confidence": 0.7,
         "reason": "Cannot rule out compromise; impact is high — escalate to human IR."},
    ],
    "supply-chain": [
        {"role": "Software Engineering SME", "model": "demo", "vote": "approve-with-controls", "confidence": 0.6,
         "reason": "Useful library; pin the version."},
        {"role": "AppSec / Supply Chain SME", "model": "demo", "vote": "reject", "confidence": 0.85,
         "reason": "Maintainer changed last week; install hook fetches a remote script."},
        {"role": "Procurement / Vendor-Risk SME", "model": "demo", "vote": "defer", "confidence": 0.6,
         "reason": "No alternative vetted yet."},
        {"role": "Operations SME", "model": "demo", "vote": "approve-with-controls", "confidence": 0.5,
         "reason": "Deployable behind a flag."},
        {"role": "Critic / Challenge", "model": "demo", "vote": "reject", "confidence": 0.8,
         "reason": "Unexplained build change + unknown provenance — fail closed."},
    ],
    "compliance": [
        {"role": "Compliance / Privacy SME", "model": "demo", "vote": "escalate-to-counsel", "confidence": 0.7,
         "reason": "Residency rules conflict across the two jurisdictions in scope."},
        {"role": "Legal SME", "model": "demo", "vote": "escalate-to-counsel", "confidence": 0.65,
         "reason": "Transfer mechanism is legally uncertain — needs counsel."},
        {"role": "Data Architecture SME", "model": "demo", "vote": "proceed-with-controls", "confidence": 0.6,
         "reason": "Technically we can regionalise the store."},
        {"role": "Security SME", "model": "demo", "vote": "proceed-with-controls", "confidence": 0.55,
         "reason": "Encryption + access logging cover the security ask."},
        {"role": "Business Owner", "model": "demo", "vote": "defer", "confidence": 0.5,
         "reason": "Not worth the exposure this quarter."},
    ],
    "cyber-risk": [
        {"role": "Risk Owner", "model": "demo", "vote": "accept", "confidence": 0.6,
         "reason": "Within appetite if remediation is scheduled."},
        {"role": "Security SME", "model": "demo", "vote": "mitigate", "confidence": 0.8,
         "reason": "Exploit is public; patch now."},
        {"role": "Infrastructure / Application SME", "model": "demo", "vote": "mitigate", "confidence": 0.7,
         "reason": "Patch path is low-effort."},
        {"role": "Finance / Business SME", "model": "demo", "vote": "accept", "confidence": 0.5,
         "reason": "Remediation competes with the release."},
        {"role": "Critic / Audit", "model": "demo", "vote": "mitigate", "confidence": 0.75,
         "reason": "Acceptance here looks like scoring optimism."},
    ],
    "platform-architecture": [
        {"role": "Platform Architecture SME", "model": "demo", "vote": "recommend-with-guardrails", "confidence": 0.6,
         "reason": "Sound, if we abstract the vendor SDK."},
        {"role": "Security Architecture SME", "model": "demo", "vote": "recommend-with-guardrails", "confidence": 0.6,
         "reason": "OK with segmentation + scoped credentials."},
        {"role": "Operations / SRE SME", "model": "demo", "vote": "defer", "confidence": 0.55,
         "reason": "Observability story is thin."},
        {"role": "Data / Compliance SME", "model": "demo", "vote": "defer", "confidence": 0.5,
         "reason": "Residency implications unresolved."},
        {"role": "Pragmatic Implementation", "model": "demo", "vote": "recommend-with-guardrails", "confidence": 0.55,
         "reason": "Deliverable this quarter with the guardrails."},
    ],
    "business-decision": [
        {"role": "Strategy / Executive Owner", "model": "demo", "vote": "proceed-with-guardrails", "confidence": 0.6,
         "reason": "Strategic fit is real if we ring-fence the downside and stage the spend."},
        {"role": "Financial / Commercial", "model": "demo", "vote": "defer", "confidence": 0.7,
         "reason": "$40M is most of our runway; the case assumes best-case synergies."},
        {"role": "Legal / Compliance", "model": "demo", "vote": "proceed-with-guardrails", "confidence": 0.55,
         "reason": "Doable with reps, warranties, and regulatory clearance."},
        {"role": "Operations / Execution", "model": "demo", "vote": "defer", "confidence": 0.6,
         "reason": "We can't integrate two orgs and still ship the roadmap this year."},
        {"role": "Critic / Challenge", "model": "demo", "vote": "reject", "confidence": 0.75,
         "reason": "Anchored on a synergy number nobody has stress-tested."},
    ],
}


def demo_votes(council, scenario: str = "default") -> list[dict]:
    """Deterministic, illustrative votes for `convene --demo`.

    scenario="monoculture" returns the failure a council does NOT catch: every
    lens confidently agrees the SAME wrong way (a correlated blind spot — exactly
    what happens when your lenses share a base model / training data). It carries
    to a permissive auto-verdict precisely to make that limit visible and honest.
    """
    if scenario == "monoculture":
        # All lenses wrong the same way -> confident, unanimous, permissive.
        permissive = next((o for o in council.decision_outcomes
                           if o in ("merge", "approve", "recommend", "observe", "proceed-with-controls")),
                          council.decision_outcomes[0])
        return [{"role": r.name, "model": "demo", "vote": permissive, "confidence": 0.85,
                 "reason": "looks fine to me (shared blind spot — no lens sees the flaw)"}
                for r in council.roles]
    canned = _DEMO.get(council.id)
    if canned:
        return canned
    outs = list(council.decision_outcomes)
    return [
        {"role": r.name, "model": "demo", "vote": outs[i % min(2, len(outs))], "confidence": 0.6,
         "reason": "illustrative demo vote"}
        for i, r in enumerate(council.roles)
    ]
