# Security Policy

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Preferred: use GitHub's **private vulnerability reporting** ("Report a vulnerability" under the
Security tab). Alternatively, email **support@cyberelders.com** with subject **"Elder Council:
Security"**.

We aim to acknowledge a report within **5 working days** and will keep you updated on remediation.

## Scope

Elder Council is a local-first harness that ships no keys and no model. Relevant classes of issue:

- A way to make the deterministic core non-deterministic, or to bypass a fail-closed rule so a council
  verdict that should route to a human is silently auto-allowed.
- A way for the install renderer to write outside the project, clobber unrelated config, or inject
  unintended commands into a generated hook.
- A leak of internal/private data into the public repo (covered by the leak + secret-scan CI guards).
- A secret-handling defect in the optional `[orchestrator]` extra.

## Out of scope (by design — see THREAT_MODEL.md)

- The audit is **tamper-evident, not tamper-proof**: a local attacker with write access to `.council/`
  can recompute the chain. This is documented, not a vulnerability.
- The risk gate is keyword-based and bypassable by obfuscation: it routes, it does not adjudicate.
- Council *quality* (the host's models'/SMEs' judgement) — the harness governs the process, not the
  correctness of the lenses.
