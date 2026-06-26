<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Council Decision Record

> The human-readable ledger. The machine-readable twin is written automatically to
> `.council/decisions/<timestamp>-<id>.json`. Preserve dissent — do not average it away.

## Decision
<!-- What is being decided? -->

## Council type
<!-- Code / Threat Hunting / Supply Chain Audit / Multi-Jurisdictional Compliance / Cyber Risk / Platform Architecture -->

## Risk score
- Impact (1–5):
- Likelihood (1–5):
- Score (= Impact × Likelihood):
- Route: <!-- solo / dual review / council / council + human -->

## Lenses consulted
- <!-- lens — position / vote / confidence -->
- <!-- lens — position / vote / confidence -->

## Evidence considered
- <!-- tool output, ticket, log, document, test result, SME input -->

## Disagreements / uncertainty
<!-- Preserve dissent. This is the most valuable part of the record. -->

## Control gates (profile: lite | standard | regulated)
<!-- One row per gate: result is allow / allow-with-controls / escalate / block / human_required. -->

| Gate | Result | Reason / escalation tier |
|---|---|---|
| Evidence | | |
| Confidence / Calibration | | |
| Action-Safety | | |
| Data-Sensitivity | | |
| Tool-Permission | | |
| Legal / Compliance | | |
| Offensive-Cyber-Misuse | | hard stop — non-overridable |
| Context-Integrity | | |
| Model-Disagreement | | |
| Cost / Latency | | |
| Production-Change | | |

## Disposition
<!-- auto / human / blocked — the MOST RESTRICTIVE of the council route and the gate result. -->

## Owner
<!-- The named accountable human. Risk acceptance and critical actions are ALWAYS a human's decision. -->

## Review date
<!-- When the outcome will be reviewed. -->

## Audit
<!-- decision_id · profile · model versions · prompt/tool-arg hashes · human_approver + approval_basis · chain hash -->

