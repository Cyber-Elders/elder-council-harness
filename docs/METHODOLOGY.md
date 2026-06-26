<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The Elder Council methodology

> The reference. For the five-minute version, read [CONCEPT.md](CONCEPT.md). This document is the
> source of truth for the routing table and the minimum governance rules.

## Premise: single-model dependence is systemic risk

AI models are increasingly embedded in operational workflows — drafting findings, interpreting
alerts, reviewing code, summarising threat intelligence, recommending containment, assessing vendor
risk, generating compliance positions, supporting architecture decisions. This creates value and
changes the risk profile. A traditional model error is local. An agentic model embedded in a workflow
creates **systemic error propagation**: one flawed reasoning pattern, repeated across many decisions,
tools, teams, and downstream systems.

The risk becomes systemic when the model **influences key processes repeatedly**, **operates near
authority** (its output triggers action, approval, escalation, or blocking), **handles local
context**, **faces adversarial input**, and **shapes governance evidence**. The better question is
not "can the model answer?" but: *should this process depend on one model's answer without structured
challenge?*

### Single-model risks (and how a council helps)

| Risk | How it shows up | Why a council helps |
|---|---|---|
| Bias / representational blind spots | under-recognises threats, users, tech, or sectors thin in training data | diverse lenses + SMEs test the answer against the real environment |
| Automation bias | people defer to a confident model on incomplete evidence | council disagreement makes uncertainty visible |
| Stale knowledge | misses current vulns, tradecraft, regulatory interpretation | live evidence + deterministic tools + SME review can be required |
| Context loss | misses local architecture, constraints, compensating controls | local + SME lenses force the real operating environment in |
| Prompt injection | malicious content in tickets/logs/docs/packages steers the model | independent checks + hard rules reduce reliance on one path |
| Model monoculture | one model/vendor across many processes → common-mode failure | cross-model, cross-role, human diversity reduces shared blind spots |
| Vendor / geopolitical dependency | access, pricing, export controls, jurisdiction change | bring-your-own-model + fallback + local options |
| Unclear accountability | a model recommends, a team follows, ownership blurs | council charters assign decision and escalation owners |
| Audit fragility | one answer preserves no dissent, uncertainty, or alternatives | council logs capture reasoning, disagreement, confidence, rationale |

The council pattern does not eliminate these risks. It makes them **explicit, governable, and
reviewable**.

## Grounding

| Idea | Relevance |
|---|---|
| Model risk management | a model used in decisions can harm when biased, mis-calibrated, misapplied, or unmonitored |
| Common-mode failure | processes fail together when they share a model, vendor, data source, or assumption |
| Automation bias | users over-trust fluent, fast, confident outputs |
| Socio-technical systems | cyber decisions combine people, tools, infrastructure, incentives, policy |
| Adversarial reasoning | security decisions are made against intelligent opposition |
| Defence in depth | no single control is trusted absolutely — apply that to *judgement* itself |

The practical conclusion: when AI becomes part of important processes, you need controls over the
**decision process**, not only over the model. A council is one such control — structured challenge,
SME review, evidence capture, escalation, and accountability *at the point the decision is made*.

## The principle

> **Use the simplest reliable decision path, but do not let one model decide alone on something
> systemically important or expensive to get wrong.**

1. **Do not overuse councils.** Low-risk, repeatable, deterministic, or well-understood tasks should
   use checklists, scanners, rules, or a single agent.
2. **Do not under-govern key processes.** High-consequence decisions need structured challenge —
   especially when they touch production, security, compliance, architecture, supply chain, or
   enterprise risk.

## The routing model

```
Impact (1-5) × Likelihood (1-5) = Risk Score (1-25)
```

| Risk score | Decision path | Typical use |
|---:|---|---|
| 1–4 | deterministic tool, checklist, or solo agent | low-risk, reversible, routine |
| 5–9 | dual review / second opinion | moderate-risk where a second view helps |
| 10–15 | a full council | high-impact or uncertain decisions |
| 16–25 | a council **plus** a named human approver | critical, irreversible, regulated, or destructive |

The score is a **routing aid**, not an adjudication. Any lens or SME may **escalate** if it identifies
higher risk than the score suggests. **Escalation goes up, not down.** *(`eldercouncil`'s heuristic
gate keys on visible tokens and is bypassable by obfuscation — it routes, it does not adjudicate; see
[THREAT_MODEL.md](../THREAT_MODEL.md).)*

## Cost & tokenomics

A council does not have to be expensive. Treat cost as part of the architecture:

| Lever | Effect |
|---|---|
| Selective invocation | most low-risk work never reaches a council |
| Deterministic tools first | scanners, rules, tests answer known questions without LLM deliberation |
| Small / local screening | local or smaller models triage routine decisions before escalation |
| Open-weight models | self-hosted models support routine lenses without per-token premium pricing |
| Hybrid routing | open-weight for first-pass; reserve frontier models for synthesis or critical escalation |
| Reusable evidence | prior council records and standard mappings reduce repeated analysis |
| Short structured outputs | lenses answer Position / Analysis / Risks / Vote / Confidence, not essays |

Match the economic design to the risk design: spend more reasoning only where the decision justifies
it. The `frontier` / `open` / `local` model lanes exist to make this concrete.

## Minimum governance rules (enforced in code)

The deterministic tally (`eldercouncil/consensus.py`) applies these to **every** council:

- **Ties block** for high-risk actions.
- **No quorum blocks** where a council requires multiple views.
- **Escalation votes win** when a lens identifies higher risk.
- **Empty / abstention → conservative block.**
- **Critical actions require human approval.**
- **Risk acceptance is always a human accountability decision** — never automated.
- **Deterministic tools run first** where available.
- **Advisory councils never auto-decide** — they recommend; a human owns the call.
- **Critical councils keep fallback models and a local/offline lane** for continuity if a provider,
  model, or region becomes unavailable.

## Control gates & profiles

Consensus decides what the council *recommends*; **control gates** decide what may actually *proceed*.
Eleven deterministic, fail-closed gates run around the council — a gate can block or escalate an action
even when the council voted to permit it; the recorded **disposition** is the most restrictive of the
council route and the gate result. The gates: Evidence, Confidence/Calibration, Action-Safety,
Data-Sensitivity, Tool-Permission, Legal/Compliance, **Offensive-Cyber-Misuse (a non-overridable hard
stop)**, Context-Integrity, Model-Disagreement, Cost/Latency, Production-Change. **Unknown is never
"allow."** Full detail + the policy-as-code: [GATES.md](GATES.md).

Adopt at the maturity you can sustain:

| Profile | Gates | For |
|---|---|---|
| **Lite** | 4 foundational + the always-on hard stop | getting started (a checklist; no policy-as-code) |
| **Standard** | all 11 | routine enterprise use |
| **Regulated** | all 11 + operational controls (immutable logs, signed runbooks, authenticated approval, scoped credentials, …) | high-assurance / regulated sectors — a **posture**, not a certification |

## Separation of duties

Above the Lite profile these are non-negotiable: a **generator may not be the sole approver** of a
high-impact action from its own recommendation; a **planner may not execute** a mutation without
passing the action-safety and tool-permission gates; a **synthesiser may not approve its own
synthesis** as final; **legal/compliance findings may not be overridden** by technical roles; the
**audit store is append-only** and not writable by the roles it logs. (Advisory councils already
enforce the first of these — they never auto-decide.)

## Human escalation ladder

Escalation is a runtime control, not a ceremony. A tripped gate routes to a tier — analyst → senior
council chair → legal/compliance → incident-response lead → executive risk owner → external specialist
— and each escalation carries a compact **evidence packet**: the requested decision, the risk tier and
gate outcomes, the evidence (and what's missing), every lens's output + confidence + dissent, the data
classification, the proposed action + rollback plan, and the audit id. Hard stops (offensive misuse,
illegal action, unauthorised access) are **non-overridable** by any tier.

## Honesty

Council output is **model-generated and may be wrong or stale**, and is **not legal, regulatory, or
compliance advice**. Councils **can be wrong**. The audit is **tamper-evident, not tamper-proof**. The
harness **ships no keys**. These are stated plainly so the method is not mistaken for a guarantee.
Standards posture: [STANDARDS-MAP.md](STANDARDS-MAP.md). Honest limits: [THREAT_MODEL.md](../THREAT_MODEL.md).
