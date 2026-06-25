<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Beyond cyber — adapting the council pattern

Cyber is the natural starting point because it combines adversarial behaviour, heavy local context,
asymmetric downside, and regulatory exposure. But the council pattern is a **general method for
governing high-stakes, AI-supported judgement**. The adaptation rule is simple:

> **Keep the council method stable. Change the lenses, evidence sources, thresholds, and escalation
> owners to fit the domain.**

The discipline that must carry over to any domain: independent reasoning before synthesis, explicit
escalation, evidence capture, preserved dissent, and an accountable human decision owner.

| Domain | Example councils | Typical lenses |
|---|---|---|
| **Finance** | investment-risk, credit-risk, treasury-risk, financial-control | portfolio manager · risk analyst · macro lens · compliance SME · critic |
| **Business operations** | operational-resilience, vendor-decision, process-change | operations owner · process SME · finance lens · risk owner · implementation |
| **Revenue operations** | pricing, account-risk, forecast-quality, deal-desk | sales owner · RevOps SME · finance SME · legal/commercial · customer-impact |
| **Procurement** | supplier-risk, outsourcing, SaaS-approval | procurement SME · security SME · legal SME · business owner · continuity |
| **Product & platform** | product-risk, launch-readiness, architecture | product owner · engineering SME · security SME · customer-impact · operations |
| **Legal & compliance ops** | contract-risk, regulatory-change, policy-exception | legal SME · compliance SME · business owner · data-governance · critic |

A finance council should not use the same lenses as a threat-hunting council — but both preserve
independent reasoning, explicit escalation, evidence capture, and accountable ownership.

## How to adapt in this harness

1. Copy a shipped council YAML from `eldercouncil/councils/` as a template.
2. Rewrite `roles` (lenses), `decision_outcomes`, `triggers` (and `min_risk_score`), and the
   `fail_closed` rule for your domain.
3. Drop it in `.council/councils/` (it overrides/extends the bundled set; validated against
   `council.schema.json`).
4. Map any new `role_key`s in `.council/council-models.json`.

The same risk gate, consensus tally, and tamper-evident audit apply unchanged. Keep the same honest
ceiling: councils are decision support, a human owns the accountable call, and any regulatory framing
is illustrative — not advice.

*(For launch, the shipped councils are cyber-first. Domain councils are a supported extension, not a
v0.1 deliverable.)*
