<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The six lenses

A **lens** is a disciplined perspective with a distinct job. It can be played by an AI model, a human
subject-matter expert, or a tool-supported analyst. Each lens reasons **independently** before the
council synthesises — that independence is what surfaces blind spots a single viewpoint would miss.

Councils reference lenses by `role_key`. The key resolves to a model through
`.council/council-models.json` (see [model resolution](#model-resolution)) — a council file **never**
names a model tag directly.

## The canonical six

| Lens (`role_key`) | Played by | Responsibility | Typical question |
|---|---|---|---|
| **Strategic / Risk Owner** (`strategic_risk_owner`) | business/risk/product/control owner | connects the decision to business impact, risk appetite, accountability | "What is the consequence if this is wrong?" |
| **Engineering SME** (`engineering_sme`) | platform/cloud/software/network engineer | is the recommendation technically accurate, feasible, safe, compatible? | "Will this work in our actual architecture?" |
| **Security SME** (`security_sme`) | threat hunter, AppSec, IR, security architect, SOC lead | adversarial behaviour, attack paths, controls, detection, containment | "How could this be exploited or missed?" |
| **Compliance / Legal SME** (`compliance_legal_sme`) | privacy/compliance/legal/audit specialist | jurisdictional obligations, evidence standards, contractual constraints — **illustrative, not legal advice** | "What obligations apply, and what must a human verify?" |
| **Critic / Challenge** (`critic_challenge`) | devil's advocate, red-team/model-risk/audit reviewer | hidden assumptions, weak evidence, bias, overconfidence, failure modes | "What are we assuming that may be false?" |
| **Pragmatic Operations** (`pragmatic_ops`) | service owner, ops lead, implementation owner | what can be done safely now with the access, people, time, and tools we have | "What is the safest practical next step?" |

Not every council needs every lens. A council is small enough to use and diverse enough to catch the
failure modes that matter.

## Specialised lenses

Task-specific roles used by particular councils; each maps to a canonical family for model assignment:

| Lens (`role_key`) | Family | Used by | Job |
|---|---|---|---|
| Detection Engineer (`detection_engineer`) | engineering | Threat Hunting | do our detections actually see this? |
| Adversarial / Red-Team (`adversary_redteam`) | security | Threat Hunting | how would an attacker evade, persist, pivot? |
| Incident Response Owner (`ir_owner`) | security | Threat Hunting | what to contain, preserve, escalate — and who owns it |
| Cross-Family Critic (`cross_family_critic`) | critic | *(opt-in)* | an independent reviewer from a **different model family** — disagreement is signal |
| Arbitrator (`arbitrator`) | strategic | *(opt-in)* | proposes the final recommendation; never overrides a fail-closed rule |
| Synthesiser (`synthesiser`) | strategic | advisory councils | integrates the lenses into one record, preserving dissent |
| Deterministic Tool (`deterministic_tool`) | engineering | Code | **not an LLM** — runs SAST/scans/tests and feeds findings as evidence |

## Model resolution

A role resolves to a model by **role key + lane**:

```
role_key (e.g. security_sme)  ──▶  council-models.json[role][lane]  ──▶  a model tag
```

- **Lanes:** `frontier` (hosted frontier models), `open` (open-weight), `local` (on-device/offline).
- The shipped default pins **only verified-real Anthropic tags** on the `frontier` lane; every
  cross-family, open-weight, and local lane ships as a `REPLACE_ME:<capability>` sentinel for you to
  pin. `eldercouncil models check` flags any unpinned lane.
- **Cross-family diversity matters.** Independent reviewers drawn from *different* model families
  catch failure modes a same-family panel shares. The `cross_family_critic` lens exists for exactly
  this; pin it to a non-Anthropic model.
- **Model tags age.** Re-pin quarterly. Because a provider can become unavailable (export controls,
  sanctions, licensing changes), add a `fallback` list per role for critical councils and keep a
  `local` lane for sensitive workloads.

The deliberation protocol every lens answers in (Position / Analysis / Risks / Vote / Confidence) is
shared across councils so outputs are comparable and disagreement is visible.
