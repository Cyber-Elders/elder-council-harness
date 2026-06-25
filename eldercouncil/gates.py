# SPDX-License-Identifier: Apache-2.0
"""
Deterministic control gates — a fail-closed control layer AROUND the council.

A gate can BLOCK or ESCALATE an action even when the council voted to proceed.
Gates are deterministic policy (gate-policy.yaml) evaluated over SIGNALS:

  * computed_by: harness  — the engine derives the signal here (destructive-verb
                            scan, secret/PII/injection regex, budget, dissent).
  * computed_by: asserted — the host agent / tools / lenses must assert it
                            (evidence quality, calibration, legal clearance).

Honest scope: the harness applies the policy deterministically; it does not
detect everything. Unknown is never "allow" — on a high-impact action a gate
that requires affirmative evidence and gets none ESCALATES (fail-closed).

Pure, offline, stdlib + pyyaml. No model, no network, no clock.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from . import paths, risk_gate

# Gate results, least → most restrictive.
ALLOW = "allow"
ALLOW_WITH_CONTROLS = "allow_with_controls"
ESCALATE = "escalate"
BLOCK = "block"
HUMAN_REQUIRED = "human_required"
_SEVERITY = {ALLOW: 0, ALLOW_WITH_CONTROLS: 1, ESCALATE: 2, BLOCK: 3, HUMAN_REQUIRED: 4}

_HIGH_IMPACT_SCORE = 10          # risk_gate score at/above which an action is "high impact"
_CONFIDENCE_FLOOR = 0.6

# --- conservative built-in detectors (derived signals) ---------------------
_SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{12,}|ASIA[0-9A-Z]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gho_[A-Za-z0-9]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,}"
    r"|(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*\S+", re.IGNORECASE)
_PII_RE = re.compile(
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b|\b\d{13}\b|\b(?:\d[ -]?){15,16}\b"
    r"|passport\s*(?:no|number)|id\s*number", re.IGNORECASE)
_INJECTION_RE = re.compile(
    r"ignore (?:all )?(?:the )?previous instructions|disregard (?:the )?(?:above|prior)"
    r"|you are now|new instructions:|reveal your (?:system )?(?:prompt|instructions)"
    r"|exfiltrate|send .* to https?://", re.IGNORECASE)
# Narrow + generative-verb-gated, to avoid false-positives on DEFENSIVE discussion
# (a threat-hunting council legitimately discusses attacker TTPs). The asserted
# `offensive_intent` signal is the primary control; this is a blatant-case backstop.
_OFFENSIVE_RE = re.compile(
    r"(?:write|generate|build|create|give me|provide)\b[^.]*\b(?:working )?"
    r"(?:exploit|payload|reverse shell|ransomware|keylogger|c2 implant|backdoor)"
    r"|msfvenom|cobalt strike beacon|step-by-step (?:to )?(?:exploit|gain access|bypass auth)",
    re.IGNORECASE)
_CROSS_BORDER_RE = re.compile(r"cross-border|cross border|transfer .* (?:region|country|abroad|overseas)"
                              r"|move .* data .* (?:to|across)", re.IGNORECASE)


class GatePolicyError(Exception):
    pass


@dataclass(frozen=True)
class GateOutcome:
    gate: str
    result: str                  # one of the result constants
    escalation: str | None       # human tier
    reasons: list                # tripped conditions / missing-affirmative signals
    hard_stop: bool = False


@dataclass(frozen=True)
class GateReport:
    profile: str
    result: str                  # overall (most restrictive)
    outcomes: list               # GateOutcome for each gate that tripped/escalated
    passed: list                 # gate names that passed clean
    hard_stopped: bool = False
    controls: list = field(default_factory=list)  # regulated additional_controls in force

    @property
    def blocked(self) -> bool:
        return self.result in (BLOCK, HUMAN_REQUIRED)

    @property
    def escalated(self) -> bool:
        return self.result == ESCALATE

    def permits_action(self) -> bool:
        return self.result in (ALLOW, ALLOW_WITH_CONTROLS)

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "result": self.result,
            "hard_stopped": self.hard_stopped,
            "controls": list(self.controls),
            "gates": [{"gate": o.gate, "result": o.result, "escalation": o.escalation,
                       "reasons": o.reasons, "hard_stop": o.hard_stop} for o in self.outcomes],
            "passed": list(self.passed),
        }


def load_policy(path=None) -> dict:
    if path is not None:
        p = paths.Path(path)
    else:
        proj = paths.council_dir() / "gate-policy.yaml"
        p = proj if proj.exists() else (paths.package_dir() / "gate-policy.yaml")
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise GatePolicyError(f"could not load gate policy at {p}: {exc}") from exc
    return data


def _profile_gates(policy: dict, profile: str) -> tuple[list, list]:
    profiles = policy.get("profiles", {})
    if profile not in profiles:
        raise GatePolicyError(f"unknown profile {profile!r} (have: {', '.join(profiles)})")
    spec = profiles[profile]
    gates = list(spec.get("required_gates", []))
    inherit = spec.get("inherits")
    if inherit:
        gates = list(profiles.get(inherit, {}).get("required_gates", [])) + gates
    for g in policy.get("always_on", []):           # offensive_misuse, every profile
        if g not in gates:
            gates.append(g)
    controls = list(spec.get("additional_controls", []))
    return list(dict.fromkeys(gates)), controls


def _derived_signals(action: str, target: str, outcome, high_impact: bool, signals: dict) -> dict:
    text = f"{action} {target}"
    rs = risk_gate.assess(text)
    d: dict[str, bool] = {}
    # action_safety
    mutating = rs.impact >= 3 or rs.route != "SOLO_ALLOW"
    d["external_system_mutation_requested"] = mutating and not signals.get("read_only")
    d["irreversible_action"] = rs.impact >= 4
    d["high_impact_action_without_approval"] = high_impact and not signals.get("human_approver")
    # data_sensitivity
    d["secret_or_credential_detected"] = bool(_SECRET_RE.search(text))
    d["personal_information_detected_without_basis"] = bool(_PII_RE.search(text)) and not signals.get("pii_basis")
    d["cross_border_transfer_unclear"] = bool(_CROSS_BORDER_RE.search(text)) and not signals.get("transfer_mechanism")
    # tool_permission
    allow = signals.get("tool_allowlist")
    tool = signals.get("tool") or action
    d["tool_not_allowlisted"] = bool(allow) and tool not in allow
    # offensive_misuse (asserted primary + narrow backstop)
    d["payload_generation_requested"] = bool(signals.get("offensive_intent")) or bool(_OFFENSIVE_RE.search(text))
    # context_integrity
    d["prompt_injection_suspected"] = bool(_INJECTION_RE.search(target or ""))
    # model_disagreement (from the consensus outcome)
    dissent = bool(getattr(outcome, "dissent", None)) if outcome is not None else False
    d["material_disagreement_on_high_impact_decision"] = high_impact and dissent
    # production_change
    prod = bool(re.search(r"\bprod(?:uction)?\b|deploy|release|kubectl apply|terraform apply", text, re.I))
    d["production_mutation_without_change_record"] = prod and not signals.get("change_ticket")
    d["rollback_plan_missing"] = prod and not signals.get("rollback_plan")
    d["approval_missing"] = prod and not signals.get("human_approver")
    return d


def _affirmative_ok(req: str, signals: dict) -> bool:
    """Is an affirmative require_on_high_impact signal satisfied?"""
    if req == "evidence_provided":
        return bool(signals.get("evidence_provided") or signals.get("evidence_refs"))
    if req == "confidence_ok":
        c = signals.get("confidence")
        return c is not None and float(c) >= _CONFIDENCE_FLOOR
    if req == "legal_cleared_if_regulated":
        return (not signals.get("regulated_data")) or bool(signals.get("legal_cleared"))
    return bool(signals.get(req))


def evaluate(profile: str = "standard", signals: dict | None = None, *, action: str = "",
             target: str = "", outcome=None, council=None, policy: dict | None = None,
             only: list | None = None, affirmative: bool = True) -> GateReport:
    """Run the profile's gates over derived + asserted signals. Returns a GateReport.

    `only`: run exactly this subset of gates (used by the pre-tool overlay to run
    only the detector gates — offensive/secret/injection — without the decision-
    stage affirmative checks that need council context).
    `affirmative`: when False, skip the require_on_high_impact checks (those are
    decision-time affirmations the routing stage cannot yet have)."""
    signals = dict(signals or {})
    policy = policy or load_policy()
    gate_defs = policy.get("gates", {})
    if only is not None:
        gate_names = [g for g in only if g in gate_defs]
        controls: list = []
    else:
        gate_names, controls = _profile_gates(policy, profile)

    high_impact = bool(signals.get("high_impact")) or risk_gate.compute_risk_score(f"{action} {target}") >= _HIGH_IMPACT_SCORE
    derived = _derived_signals(action, target, outcome, high_impact, signals)

    def tripped(cond: str) -> bool:
        return bool(signals.get(cond)) or bool(derived.get(cond))

    outcomes: list[GateOutcome] = []
    passed: list[str] = []
    for name in gate_names:
        g = gate_defs.get(name, {})
        fc_reasons = [c for c in g.get("fail_closed_if", []) if tripped(c)]
        affirmations = g.get("require_on_high_impact", [])
        missing = ([f"{req}_missing" for req in affirmations if not _affirmative_ok(req, signals)]
                   if (high_impact and affirmative) else [])
        reasons = fc_reasons + missing
        if not reasons:
            passed.append(name)
            continue
        hard = bool(g.get("hard_stop"))
        # A control gate whose required affirmations are ALL satisfied is "approved
        # with controls" — the mutation it detected is allowed because approval +
        # rollback (etc.) are in place. Only an unmet affirmation or a non-affirmable
        # trip blocks/escalates.
        affirmations_met = bool(affirmations) and not missing
        if hard:
            result = HUMAN_REQUIRED       # non-overridable hard stop
        elif affirmations_met and not missing:
            result = ALLOW_WITH_CONTROLS
        elif g.get("blocks"):
            result = BLOCK
        else:
            result = ESCALATE
        outcomes.append(GateOutcome(name, result, g.get("escalation"), reasons, hard))

    if outcomes:
        worst = max(outcomes, key=lambda o: _SEVERITY[o.result])
        overall = worst.result
    else:
        overall = ALLOW
    hard_stopped = any(o.hard_stop for o in outcomes)
    return GateReport(profile=profile, result=overall, outcomes=outcomes, passed=passed,
                      hard_stopped=hard_stopped, controls=controls)
