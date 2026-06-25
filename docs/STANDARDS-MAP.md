<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Standards map

> **The honest ceiling.** Elder Council is **OWASP-Agentic-2026-aware** and **aligned to the NIST AI
> RMF** four-function structure. It is a **decision-process control, not a control set** — it is **not
> compliant, not certified**, and claims neither. Most of what it does is **improve** (add multi-model
> + human scrutiny) or **audit** (record the decision and its dissent). The only thing it **enforces**
> is the deterministic risk-gate *routing* and the fail-closed consensus rules.

This product is a deliberation orchestrator, so its honest ceiling is **lower** than a deterministic
policy engine's: a council cannot *enforce* an OWASP item — it can surface it, challenge it, and
record the decision. We map only the two frameworks above, and we map them honestly. We do **not** map
this tool to ISO/IEC 42001, ISO/IEC 27001, POPIA, GDPR, NIS2, or DORA — mapping a deliberation aid to
a certifiable management-system standard or a statute would imply a compliance it cannot provide.

## OWASP Top 10 for Agentic Applications (2026)

Legend: **improve** = adds plural scrutiny / human review · **audit** = records the decision ·
**route** = the deterministic gate's enforce surface · **out** = structurally out of scope here.

| # | Title | Coverage | How |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | improve | adversarial + critic lenses challenge whether the action serves the stated goal; injection is a named residual (THREAT_MODEL) |
| ASI02 | Tool Misuse | route + improve | the risk gate routes high-impact tool actions to a council; Code/Supply-Chain lenses review them |
| ASI03 | Identity & Privilege Abuse | improve | security + architecture lenses review privilege and access in Code / Platform councils |
| ASI04 | Agentic Supply Chain Vulnerabilities | improve + audit | the Supply Chain council reasons about provenance, maintainership, typosquatting beyond CVE scanners |
| ASI05 | Unexpected Code Execution | route + improve | remote-exec patterns raise the gate score; the Code council's deterministic-tool lens runs SAST |
| ASI06 | Memory & Context Poisoning | out | a council does not protect agent memory; pair with a memory-integrity control |
| ASI07 | Insecure Inter-Agent Communication | out | the harness does not secure the transport between agents |
| ASI08 | Cascading Failures | improve | the systemic-risk thesis itself — cross-model diversity reduces common-mode failure at the decision point |
| ASI09 | Human-Agent Trust Exploitation | improve | preserved dissent + human-owned critical calls counter over-trust in one confident answer |
| ASI10 | Rogue Agents | out | detection/containment of a rogue agent is out of scope; this governs decisions, not agent runtime |

**Where a council structurally cannot help:** ASI06 (memory), ASI07 (inter-agent comms), and ASI10
(rogue-agent runtime) are not decision-process problems — ceding them is what keeps the rest credible.
Use a memory-integrity control, secure transport, and runtime monitoring respectively.

## NIST AI RMF — function alignment

| Function | How Elder Council aligns |
|---|---|
| **GOVERN** | the methodology (risk routing, council charters, fail-closed minimum-governance rules) operationalises governance *at the decision point* |
| **MAP** | the risk gate maps each decision to impact × likelihood and a decision path |
| **MEASURE** | the hash-chained decision log + `audit-summary` make verdicts, routes, and dissent reviewable over time |
| **MANAGE** | escalation, human-owned critical/risk-acceptance decisions, and fail-closed defaults manage the residual |

## Claims discipline

References to OWASP, NIST, and any regulation in this repo are **illustrative and for alignment
framing only** — they do **not** imply endorsement by, affiliation with, or compliance with those
bodies or laws. The CI honesty gate forbids "compliant/certified" claims and the stale (pre-2026)
OWASP agentic taxonomy.
