<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Concept — why councils, and when

> Read this first. It explains the idea in five minutes. The full method is in
> [METHODOLOGY.md](METHODOLOGY.md); the terms are defined in [GLOSSARY.md](GLOSSARY.md).

## The metaphor

An **Elder Council** is a small group of disciplined perspectives — *lenses* — convened to scrutinise
a high-stakes decision before it is made. Each lens has a distinct job (technical, security, legal,
challenge, operations) and reasons independently before the group synthesises. The point is not
ceremony. The point is to stop an important decision from depending on one unchallenged viewpoint.

## The problem it addresses: single-model dependence as systemic risk

A traditional chatbot mistake is local: one user gets one weak answer. An AI model embedded across
your operational workflows is different. When the *same* model influences code review, threat triage,
dependency vetting, compliance interpretation, and risk scoring, a single flaw in its reasoning is
**repeated across many decisions, teams, and downstream systems at machine speed**. This is
**common-mode failure**: many processes failing together because they share one model, one vendor,
one assumption, one blind spot. Single-model dependence in key processes is a **systemic risk**, not
just an occasional bad answer.

The failure modes are familiar from model-risk management, amplified by autonomy and speed: bias and
representational blind spots, automation bias (people defer to a confident model), stale knowledge,
loss of local context, prompt injection, vendor and geopolitical dependency, and fragile audit trails
that preserve neither dissent nor uncertainty.

## The two ideas that make it practical

### 1. Selective plurality — *when* to convene

A council is **not** for every task. Convening one for routine, reversible, well-understood work adds
cost and bureaucracy without improving the decision. The discipline is:

> **Use the simplest reliable decision path, but do not let one model decide alone on something
> systemically important or expensive to get wrong.**

The mechanism is a **risk gate** (impact × likelihood, 1–25). Below the convene threshold, a single
agent or a deterministic tool handles the decision. At or above it, the council convenes. A second
opinion helps on a hard, adversarial diagnosis; on an easy one it just adds noise and a chance to
talk yourself out of the right call. *(Multi-agent research finds the same: plural deliberation helps
when a single agent's baseline accuracy is low, and can hurt when it is already high — see the
[FAQ](FAQ.md).)*

| Risk score | Path |
|---:|---|
| 1–4 | deterministic tool / single agent |
| 5–9 | a second opinion (dual review) |
| 10–15 | a full council |
| 16–25 | a council **plus** a named human approver |

### 2. Council mode — *how* the verdict is used

Councils come in two plain-English modes:

- **Advisory** — the council deliberates and a **human synthesises and decides**. Used where the
  decision is a human's to own: Compliance, Cyber Risk (risk acceptance), Platform Architecture.
- **Action-gate** — the council's verdict can **gate an action** behind the risk gate (allow it
  through, block it, or send it back). Used where a clear, auditable gate adds value: Code,
  Supply Chain. Even here, blocking verdicts and any critical change route to a human.

There are **no archetype codes to memorise** — just *advisory* (recommends; a human decides) versus
*action-gate* (can gate the action). The mode of each council is stated in [COUNCILS.md](COUNCILS.md).

## What a council produces

A verdict, the **independent vote of every lens**, the **preserved dissent** (the most valuable
signal — where lenses disagree), the outcome of the **control gates** (a deterministic, fail-closed
layer that can withhold an action the council voted to permit — see [GATES.md](GATES.md)), a final
**disposition** (auto / human / blocked), and a **hash-chained, tamper-evident** record under
`.council/`. Disagreement is kept visible instead of being hidden behind one polished answer.

## The honest ceiling

Elder Council makes decision risk **explicit, governable, and reviewable**. It does **not** eliminate
it. Councils can be wrong. A named human owns every critical and risk-acceptance decision — **risk
acceptance is never automated**. Council output is **model-generated and may be wrong or stale**, and
is **not legal advice**. The audit is **tamper-evident, not tamper-proof**. The tool **ships no keys** —
you bring your own LLM. These limits are features: they keep the tool honest about what plural
scrutiny can and cannot do.
