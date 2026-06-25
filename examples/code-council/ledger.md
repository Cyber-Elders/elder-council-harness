<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Council Decision Record

## Decision
Approve pushing a change that adds a hardcoded AWS access key in `config.py` and builds a SQL query by
string concatenation on a user-supplied id.

## Council type
Code Council (action-gate)

## Risk score
- Impact: 5 · Likelihood: 3 · Score: 15 → route: council
- (a `git push` of secret-bearing, injectable code)

## Lenses consulted
- Software Engineering SME — *merge* (0.6): clean structure, tests pass
- AppSec SME — *block* **[CRITICAL]** (0.9): hardcoded secret + unparameterised SQL in the diff
- Reliability / Operations SME — *merge* (0.55): rollback path exists
- Deterministic Tool Lens — *block* (0.95): secret-scan flagged an AWS key; SAST flagged a SQLi sink
- Critic / Challenge — *request-changes* (0.7): auth check is assumed, not verified, on the new route

## Evidence considered
secret-scan output (AWS key), SAST output (SQL injection sink), the diff, the test run.

## Disagreements / uncertainty
Two lenses would have merged and one asked only for changes. Their dissent is preserved — the block is
driven by the CRITICAL finding, not unanimity.

## Decision
**block** — withheld pending human security review (Code council fail-closed: any CRITICAL finding
blocks; critical security changes are a human decision).

## Owner
&lt;named security reviewer&gt;

## Review date
On re-submission of the corrected diff.
