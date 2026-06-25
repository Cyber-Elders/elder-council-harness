<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Threat model & honest limits

Elder Council makes decision risk **explicit, governable, and reviewable**. It does **not** eliminate
it. This document states the trust boundary and the residual risks plainly. If a behaviour here
changes, this file should change deliberately — the pinned tests in `tests/test_known_bypasses.py`
keep these limits honest.

## What it is

A local-first harness that (1) **routes** decisions with a deterministic risk gate, (2) **convenes**
multi-lens councils on the consequential ones, (3) **combines** their votes with a deterministic,
fail-closed consensus tally, and (4) **records** the verdict and dissent to a hash-chained audit. It
ships **no model and no API keys** — councils run on the user's own LLM(s).

## What it does NOT do

- **It does not guarantee a correct decision.** A council is decision support. Councils can be wrong.
  The verdict's quality is bounded by the lenses' (the host's models'/SMEs') judgement.
- **It does not accept risk or make the final critical call.** Risk acceptance and critical actions
  always route to a **named human** — never automated.
- **It does not provide legal, regulatory, or compliance advice.** Council output is **model-generated
  and may be wrong or stale.** The Compliance council's regulatory references are illustrative.
- **It is not tamper-proof.** The audit is **tamper-evident, not tamper-proof** (see below).
- **It does not enforce on advisory tiers.** On Cursor / MCP / Kiro-advisory, the verdict is a
  suggestion the agent may ignore.

## Residual risks (the honest edges)

1. **Audit records contain user data.** `.council/decisions/*.json` records the action, the votes, the
   reasoning, and the dissent. If you convene a council on sensitive material, that material is written
   to disk in plaintext. `.council/` is git-ignored by default — **do not commit it**, and treat it as
   user data.
2. **BYO-LLM means prompts leave your boundary.** The harness ships no keys, but when you run a council
   (via your agent or the optional orchestrator), prompts go to **your configured provider**.
   Data-sovereignty is your responsibility — use the `local` lane for sensitive workloads. The harness
   cannot stop a misconfigured cloud lane from sending sensitive context off-box.
3. **Councils reviewing attacker-controlled content are injectable.** A council reading logs, tickets,
   dependency manifests, or incident evidence can be steered by malicious content. Hard gates (the risk
   gate, fail-closed rules) live *outside* the prompt and reduce — but do not remove — this risk.
4. **The risk gate is keyword-based and bypassable by obfuscation.** It keys on visible tokens to
   *route* (escalate or not). An encoded or obfuscated destructive command can score low. The gate
   routes; it does not adjudicate. Pair it with deterministic tools and human judgement for high blast
   radius.
5. **On hard-block IDEs the gate enforces escalation, not council quality.** It can stop an action and
   require a council; it cannot make the host model reason well or run every lens faithfully.
6. **Correlated error — the limit that matters most.** A council reduces *single*-model risk, not
   *correlated* error. If your lenses share a base model or training lineage, they share blind spots
   and can be confidently wrong together — the exact failure the tool exists to mitigate. The shipped
   default pins only one provider (Anthropic) on the frontier slot, so an out-of-the-box council is a
   **monoculture** until you diversify it. `eldercouncil models check` warns when every lens resolves
   to one provider, and `convene <council> --demo --scenario monoculture` demonstrates the failure.
   **Pin at least one lens (e.g. the cross-family critic) to a different model family.** The consensus
   tally has no way to detect lens diversity — that is your responsibility.
7. **Severity is lens-asserted, not authenticated.** A `CRITICAL` finding can force a block. To limit
   abuse (a prompt-injected or over-eager reasoning lens forcing a denial-of-service), a council that
   has a deterministic-tool lens honours `CRITICAL` **only** from that lens; a council without one
   honours any lens's `CRITICAL` (fail-closed). Note the asymmetry: the *absence* of a severity field
   does **not** mean "not critical" — it just means no lens asserted one.
8. **Outage is reported as `inconclusive`, not a verdict.** If too many lenses are unreachable, the
   council returns `inconclusive` (routed to a human), never a deliberated-looking `block`/`allow` — so
   an infrastructure failure is not mistaken for a decision. Distinguishing the two is the honest design.
9. **A malformed project council fails the whole catalog closed.** One invalid YAML in
   `.council/councils/` makes `load_councils` raise, so *no* council loads (the pre-tool gate still
   works). This is fail-closed by intent, but a single typo disables every council until fixed.

## Self-protection & audit integrity

The audit is an append-only, hash-chained JSONL (`.council/audit.jsonl`): each entry carries `prev`
(the previous entry's hash) and `hash` (sha256 over the entry incl. `prev`). `eldercouncil verify`
walks the chain and detects an **altered, reordered, inserted, or dropped** entry.

This is **tamper-evident, not tamper-proof.** Anyone (or any compromised agent) with write access to
`.council/` can delete an entry and recompute the entire chain plus `audit.head`, and `verify()` would
then pass. There is no external anchor. To detect a **full local rewrite**, record the chain head
off-box — `eldercouncil verify` prints it. (`tests/test_audit.py` includes a test asserting a full
rewrite is *not* locally detectable, so this limit stays documented.)

## Threats to the governance system itself

A governance layer is only as trustworthy as its own integrity. These are the adversarial threats to
Elder Council *as a control system* — and what the harness does vs. what is the operator's
responsibility (much of this is deployment posture, especially at the `regulated` profile).

| # | Threat | What it achieves | Harness controls / operator responsibility |
|---|---|---|---|
| 1 | **Policy tampering** | weaken gate conditions / allowlists / thresholds so controls look active but don't enforce | version-control `gate-policy.yaml` + `councils/` + `council-models.json` with reviewed, signed commits (operator); CODEOWNERS protects the load-bearing files; the gate policy is data the operator must protect |
| 2 | **Eval / calibration poisoning** | skew confidence calibration so bad decisions read as safe | provenance-label any eval corpus; human review before use; keep a hold-out set (operator) — the harness ships no learned calibration, so there is nothing to poison out of the box |
| 3 | **Compromised escalation path** | a blocked action appears human-approved | approvals must be authenticated (SSO/MFA), out-of-band, time-bound — the `authenticated_approval_api` control in the `regulated` profile is a *requirement on the operator*, not something the harness provides |
| 4 | **Model-router abuse** | route sensitive context to an untrusted/rogue endpoint | role→model resolution is data the operator version-controls; `models check` flags monoculture; the operator pins endpoints + enforces data-class routing |
| 5 | **Fake human approval** | an automated process forges an approval token | approvals are an operator-owned, authenticated step; the harness records `human_approver`/`approval_basis` in the audit but cannot itself authenticate the human |
| 6 | **Audit-log tampering** | hide a gate bypass or override | the hash chain is **tamper-evident** (see above) — full off-box replication / immutability is the `regulated` profile's operator requirement |
| 7 | **Credential misuse** | an over-scoped credential exfiltrates or mutates beyond scope | the `tool_permission` gate flags over-broad scope *when the scope is asserted to it*; least-privilege, scoped, rotated credentials are an operator responsibility |
| 8 | **Governance bypass via prompt injection** | untrusted content makes the agent skip gates / self-approve | the `context_integrity` gate flags injection; gate decisions are made by this **deterministic engine outside the model's control**, not by the LLM in-prompt — but an advisory-tier IDE cannot force the agent to consult it |

The honest throughline: Elder Council provides the **deterministic gate logic and a tamper-evident
record**; it does **not** provide authentication, immutable off-box storage, or credential management.
Those are deployment controls — required (not optional) for the `regulated` profile, and the harness
will not pretend to enforce what it cannot.

## Trust boundary

Elder Council trusts: the local Python runtime, the policy/council/registry files in the package and
`.council/`, and the user's own model access. It does **not** trust: tool inputs, fetched content,
dependency manifests, or the contents of files it is asked to review. It assumes the operator wants
the gate enforced — a user with write access to `.council/` can change the councils, the registry, or
the audit, by design (it is their project).

## Reporting

Security issues: see [SECURITY.md](SECURITY.md) — please use a private advisory, not a public issue.
