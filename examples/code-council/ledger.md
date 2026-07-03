<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Council Decision Record

## Decision
Approve pushing a change that adds a hardcoded AWS access key in `config.py` and builds a SQL query by
string concatenation on a user-supplied id.

## Council type
Code Council (action-gate)

## Risk score
- Impact: 5 · Likelihood: 3 · Score: 15 → route: council
- *(a separately-run `eldercouncil risk-gate` assessment of the push — `convene` itself does not
  score the question, which is why `decision.json` has `"risk": {}`)*

## Lenses consulted
- Software Engineering SME — *merge* (0.6): clean structure, tests pass
- AppSec SME — *block* **[HIGH]** (0.9): hardcoded secret + unparameterised SQL in the diff
- Reliability / Operations SME — *merge* (0.55): rollback path exists
- Deterministic Tool Lens — *block* **[CRITICAL]** (0.95): secret-scan flagged an AWS key; SAST flagged a SQLi sink
- Critic / Challenge — *request-changes* (0.7): auth check is assumed, not verified, on the new route

## Evidence considered
secret-scan output (AWS key), SAST output (SQL injection sink), the diff, the test run.

## Disagreements / uncertainty
Two lenses would have merged and one asked only for changes. Their dissent is preserved — the block is
driven by the **tool lens's CRITICAL** (an authoritative scanner finding, the only lens whose CRITICAL
this council honours), not by unanimity.

## Control gates (standard profile)
All 11 gates passed — no safety gate tripped; the council's own routing stands.

## Disposition
**human** — the most restrictive of the council route (human) and the gate result (allow). The final
call is a person's.

## Decision
**block** — withheld pending human security review (Code council fail-closed: any CRITICAL tool
finding blocks; critical security changes are a human decision).

## Diversity
Families that voted: *demo* (illustrative sample votes — no real models ran; a real run records the
actual provider families here).

## Owner
&lt;named security reviewer&gt;

## Review date
On re-submission of the corrected diff.

## Audit
decision `EC-d024c9991b31` *(matches [decision.json](decision.json))* · profile: standard · vote
provenance: demo (the tool lens's CRITICAL is canned here; a real `--orchestrate` run records
`provenance: tool`) · chain head recorded in `.council/audit.head`.
