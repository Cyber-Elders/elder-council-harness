<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The councils

Six cyber councils plus a general **Business Decision** council for executive calls. Each council is
pure data (`eldercouncil/councils/<id>.yaml`) and installs into every supported IDE via the same
generic renderer. A council declares its **lenses**, its **decision outcomes**, its **fail-closed
rule**, and the **triggers** (with a minimum risk score) that should convene it.

**Lenses ≠ councils.** The six [lenses](LENSES.md) are reusable perspectives; a council is a *roster*
of lenses convened for one class of decision. The same lens (e.g. Security SME) appears in several
councils. **Mode** is either *advisory* (recommends; a human decides) or *action-gate* (the verdict
can gate the action behind the risk gate). See [CONCEPT.md](CONCEPT.md).

## Lens × council matrix

| Lens \ Council | Code | Threat Hunting | Supply Chain | Compliance | Cyber Risk | Platform Arch | Business |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Strategic / Risk Owner | | | ● | ● | ● | | ● |
| Engineering SME | ● | ● | ● | ● | ● | ● | |
| Security SME | ● | ● | ● | ● | ● | ● | |
| Compliance / Legal SME | | | | ● | | ● | ● |
| Critic / Challenge | ● | | ● | | ● | | ● |
| Pragmatic Operations | ● | | ● | | | ● | ● |
| *Detection Engineer* | | ● | | | | | |
| *Adversary / Red-Team* | | ● | | | | | |
| *Incident Response Owner* | | ● | | | | | |
| *Deterministic Tool* | ● | | | | | | |

*(Italic lenses are specialised roles that map to a canonical lens family for model assignment.)*

## Consensus rules (apply to every council)

Regardless of council, the deterministic tally honours these **minimum governance rules**:

- **Ties block** and route to a human.
- **No quorum blocks** (a majority of lenses must vote).
- **Escalation wins** — any "escalate" vote routes to a human.
- **Empty / abstention → conservative block.**
- **Critical actions and risk acceptance → a named human, never automated.**
- **Advisory councils** never auto-decide — they recommend; a human owns the call.
- **Low confidence** on a permissive verdict routes to a human.

---

## 1. Code Council — `code-council` · action-gate

**Convene for:** code changes where security, reliability, privacy, authentication, authorisation,
data flow, or production stability may be affected.

| Lens | Role |
|---|---|
| Software Engineering SME | correctness, maintainability, testability, architecture fit |
| AppSec SME | vulnerability classes, auth logic, secrets, injection, abuse cases (rates severity) |
| Reliability / Operations SME | deployment risk, rollback, observability, failure modes |
| Deterministic Tool Lens | runs SAST / dependency / secret scan / tests — evidence, not opinion |
| Critic / Challenge | edge cases, implicit trust, unsafe defaults, missed data paths |

**Outcomes:** `merge` · `request-changes` · `block` · `escalate`
**Fail-closed:** critical authentication, authorisation, cryptography, payment, privacy, or
production-control changes require explicit human approval; any CRITICAL finding blocks pending human
security review.

## 2. Threat Hunting Council — `threat-hunting` · advisory

**Convene for:** suspicious behaviour, uncertain signals, attacker patterns, possible compromise.

| Lens | Role |
|---|---|
| Threat Hunter / Security SME | interpret indicators, tactics, behavioural patterns |
| Detection Engineer | whether logs, rules, and telemetry actually support the finding |
| Platform / Infrastructure SME | what is normal vs abnormal in the real environment |
| Adversarial / Red-Team | how an attacker would evade, persist, or pivot |
| Incident Response Owner *(arbitrator)* | containment, escalation, evidence preservation, impact |

**Outcomes:** `observe` · `contain` · `escalate`
**Fail-closed:** if the council cannot distinguish a benign anomaly from a plausible compromise and
the impact is high, **escalate to human incident-response leadership** rather than dismiss the signal.
*(Containment in a live incident is a human call — this council is advisory.)*

## 3. Supply Chain Audit Council — `supply-chain` · action-gate

**Convene for:** third-party software, open-source packages, vendors, integrations, build pipelines,
dependency risk.

| Lens | Role |
|---|---|
| Software Engineering SME | dependency use, build impact, integration path |
| AppSec / Supply Chain SME | reputation, known vulns, maintainer risk, signing, provenance |
| Procurement / Vendor-Risk SME | supplier posture, contractual risk, criticality, alternatives |
| Operations SME | deployment, rollback, monitoring, continuity |
| Critic / Challenge | transitive deps, abandoned packages, typosquatting, weak evidence |

**Outcomes:** `approve` · `approve-with-controls` · `defer` · `reject` · `escalate`
**Fail-closed:** unknown provenance, suspicious maintainership, unexplained build changes, or a
high-privilege integration **block approval until reviewed by a human**.

## 4. Multi-Jurisdictional Compliance Council — `compliance` · advisory · scheduled

**Convene for:** decisions affected by multiple regulatory regimes, data-residency rules, privacy
obligations, sector requirements, or contractual commitments. (Can run on a schedule.)

| Lens | Role |
|---|---|
| Compliance / Privacy SME *(arbitrator)* | applicable obligations + evidence requirements |
| Legal SME | interpretation risk, notification duties, contractual constraints |
| Data Architecture SME | data flows, residency, transfers, retention, access paths |
| Security SME | safeguards, breach implications, control effectiveness |
| Business Owner | operational need, customer impact, accountable decision |

**Outcomes:** `proceed-with-controls` · `defer` · `block` · `escalate-to-counsel`
**Fail-closed:** if legal interpretation and technical reality conflict, **do not average it away** —
surface the conflict and escalate to the accountable human owner or counsel.

> **Not legal advice.** Any named regulation in this council is **illustrative** — configure for your
> own jurisdiction and have qualified counsel verify current obligations. Output is model-generated
> and may be wrong or stale.

## 5. Cyber Risk Council — `cyber-risk` · advisory

**Convene for:** cyber risks affecting business priorities, investment, control gaps, risk
acceptance, insurance, board reporting, or remediation sequencing.

| Lens | Role |
|---|---|
| Risk Owner *(arbitrator)* | business impact, risk appetite, accountable acceptance |
| Security SME | threat, vulnerability, control strength, likelihood |
| Infrastructure / Application SME | exposure, dependencies, technical remediation |
| Finance / Business SME | cost, priority, budget, operational trade-offs |
| Critic / Audit | scoring inflation, missing evidence, control optimism |

**Outcomes:** `mitigate` · `transfer` · `avoid` · `monitor` · `accept`
**Fail-closed:** **no material risk is accepted by an AI system alone.** Risk acceptance is always a
human accountability decision supported by the council's analysis.

## 6. Platform Architecture Council — `platform-architecture` · advisory · MADR output

**Convene for:** architecture decisions shaping security, resilience, scalability, data flow, or the
long-term operating model.

| Lens | Role |
|---|---|
| Platform Architecture SME *(arbitrator)* | coherence, dependency structure, scalability |
| Security Architecture SME | identity, segmentation, secrets, encryption, logging |
| Operations / SRE SME | reliability, observability, deployment, support burden |
| Data / Compliance SME | classification, residency, retention, governance |
| Pragmatic Implementation | can this be delivered safely with the skills and time we have? |

**Outcomes:** `recommend` · `recommend-with-guardrails` · `defer`
**Fail-closed:** decisions that create long-lived exposure, irreversible lock-in, or unclear
ownership are **deferred until the accountable owner accepts the trade-off**. Produces a versioned
decision record (MADR) with the deliberation as its provenance.

## 7. Business Decision Council — `business-decision` · advisory

**Convene for:** business-critical, high-stakes, or hard-to-reverse executive decisions — strategic
commitments, major spend, M&A, market entry, reorganisations, vendor lock-in, pricing, or
reputational exposure. A general (non-cyber) council for the calls a leadership team should not make
on one voice alone.

| Lens | Role |
|---|---|
| Strategy / Executive Owner *(arbitrator)* | strategic fit, the bet being made, horizon, accountability |
| Financial / Commercial | cost, ROI, runway impact, downside exposure, opportunity cost |
| Legal / Compliance | regulatory, contractual, and governance obligations (illustrative, not legal advice) |
| Operations / Execution | can this actually be delivered with the people, time, and capacity we have? |
| Critic / Challenge | hidden assumptions, optimism bias, anchoring, unnamed failure modes |

**Outcomes:** `proceed` · `proceed-with-guardrails` · `defer` · `reject` · `escalate`
**Fail-closed:** no business-critical, irreversible, or material-commitment decision is finalized by
an AI system — the council informs; a named, accountable executive owns and makes the call.

> **Not professional advice.** Council output is model-generated and may be wrong or stale; the
> Legal/Compliance lens is illustrative, not legal, financial, or regulatory advice.

---

## Add your own / adapt

The council pattern is domain-general — see [DOMAIN-ADAPTATION.md](DOMAIN-ADAPTATION.md). Drop a YAML
file in `.council/councils/` (validated against `eldercouncil/councils/council.schema.json`) to add
or override a council. Keep the method stable; change the lenses, outcomes, thresholds, and owners.
