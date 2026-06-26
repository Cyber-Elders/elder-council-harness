# Multi-Jurisdictional Compliance Council (advisory)

## Purpose
Analyse decisions affected by multiple regulatory regimes, data-residency rules, privacy obligations, sector requirements, or contractual commitments.

## Lenses
- Compliance / Privacy SME (compliance_legal_sme): Identify applicable obligations and evidence requirements for the data and processes in scope. Illustrative frameworks only (e.g. POPIA, GDPR, NIS2, DORA, ISO/IEC 27001) — not legal advice; flag what a human must verify.
- Legal SME (compliance_legal_sme): Review interpretation risk, notification duties, contractual constraints, and privilege. Where is the legal reading genuinely uncertain?
- Data Architecture SME (engineering_sme): Map data flows, residency, transfers, retention, and access paths against the obligations in scope.
- Security SME (security_sme): Review safeguards, breach implications, and control effectiveness.
- Business Owner (strategic_risk_owner): Balance operational need, customer impact, and accountable decision-making.

## Decision outcomes
proceed-with-controls, defer, block, escalate-to-counsel

## Output
Write `.council/decisions/compliance-{ts}.json` and call the audit_log MCP tool (council="compliance") with each lens's vote + reasoning and the synthesised recommendation, preserving dissent.

## Fail-closed
If legal interpretation and technical reality conflict, do not average the conflict away — surface it and escalate to the accountable human owner or counsel. This council does not provide legal, regulatory, or compliance advice.
