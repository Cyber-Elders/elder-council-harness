<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Glossary

The canonical home for Elder Council terms and the two disambiguations newcomers trip on.

## Two things people conflate

- **Lenses ≠ councils.** A **lens** is a single perspective (Security SME, Critic, …). A **council**
  is a *roster of lenses* convened for one class of decision. The same lens appears in several
  councils. There are six lens archetypes and eight councils — don't conflate the two.
- **Advisory (council mode) ≠ advisory (enforcement tier).** The same word covers two things: an
  *advisory council* never auto-decides (a human synthesises), while an *advisory IDE tier* (Cursor /
  Copilot / MCP) means the agent is *asked* to consult the gate and can decline. A hard-block IDE can
  still run advisory councils, and vice versa.
- **Council mode ≠ risk routing.** **Mode** (advisory vs action-gate) is *how a council's verdict is
  used*. **Risk routing** (the 1–25 score) is *whether a council is convened at all*. One is about the
  output; the other is about the trigger.

## Terms

**Action-gate (council mode)** — a council whose verdict can gate an action behind the risk gate
(allow it, block it, send it back). Even so, blocking verdicts and critical changes route to a human.
Used by Code and Supply Chain. Contrast: *advisory*.

**Advisory (council mode)** — a council that deliberates and recommends; a **human synthesises and
decides**. Used by Threat Hunting, Compliance, Cyber Risk, Platform Architecture, Business
Decision, and Engineering Team. It never auto-decides.

**Approval status** — how an asserted `human_approver` was treated: `verified` (your configured
`approval_verify_command` confirmed it), `asserted — unverified` (recorded but not confirmed — the
default when no verifier is configured; see [GATES.md](GATES.md)), or `verification FAILED` (the
assertion was stripped and the gates escalated, fail-closed). None of these authenticates the person.

**Arbitrator** — the lens designated as the decision owner for a council (e.g. the Incident Response
Owner). It proposes the final recommendation but never overrides a fail-closed rule.

**Audit (hash chain)** — the append-only, hash-chained record of decisions in `.council/audit.jsonl`,
with full records in `.council/decisions/`. **Tamper-evident, not tamper-proof.**

**BYO-LLM (bring your own LLM)** — the harness ships **no** model and **no** API keys; councils run on
the model(s) your coding agent already uses (or that you pin per lane in `council-models.json`).

**Consensus tally** — the deterministic, pure function that combines lens votes into a verdict and a
route, applying the minimum-governance rules. Same votes + same council → same outcome.

**Convene threshold** — the risk score (default 5) at or above which a council is convened. Below it,
a single agent or a deterministic tool handles the decision.

**Council** — a roster of lenses convened for one class of high-stakes decision. Eight ship by
default (six cyber + business decision + engineering team); see [COUNCILS.md](COUNCILS.md).

**Decision outcomes** — the set of verdicts a council can return (e.g. Code: merge / request-changes
/ block / escalate). Declared per council in its YAML.

**Deterministic tool lens** — the council seat that is *not* an LLM. In `--orchestrate` the harness
itself runs real checks (built-in detectors + your `[tools]` commands); in-IDE your agent is
instructed to run real tools. See *provenance*.

**Dissent** — lens votes that differ from the verdict. Preserved (in `.council/dissent/`) because
where lenses disagree is the most valuable signal.

**Diversity (decision-time)** — a field in every decision record listing which model **provider
families** actually voted. A warning prints when every model lens resolved to one family (see
*monoculture*). Detection + warning, not enforcement.

**Fail-closed rule** — each council's stated rule for the uncertain/high-impact case, always
resolving toward caution (block / escalate / human). Encoded so a malformed or empty council degrades
to a human ask, never a silent allow.

**Lane (model)** — `frontier` (hosted frontier), `open` (open-weight), or `local` (on-device). A role
resolves to a model via its lane in `council-models.json`.

**Lens** — a disciplined, independent perspective in a council; see [LENSES.md](LENSES.md).

**MCP (Model Context Protocol)** — a standard way a coding agent connects to external tools. An MCP
client gets **advisory** enforcement (the agent is asked to call the gate and honour it), not a hard
block.

**Minimum governance rules** — the fail-closed rules applied to every council: ties block; no-quorum
blocks; escalation wins; empty/abstain → block; critical actions & risk acceptance → human; advisory
never auto-decides.

**Monoculture** — every lens running on one model (or one model *family*): the voices share that
lineage's blind spots and can be confidently wrong together — the exact failure councils exist to
prevent. How to diversify: [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md).

**Orchestrate (`--orchestrate`)** — the headless run mode: the harness itself calls your pinned
models (and runs the real tool-lens checks) and returns a verdict with no IDE involved. Needs
`pip install -e ".[orchestrator]"` from your clone. Contrast: the default in-IDE mode, where your
coding agent runs the lenses.

**Pre-tool hook** — a checkpoint a coding agent runs *before* it executes an action, so a council can
intervene first. On Claude Code / OpenCode this enables a **hard block**; elsewhere enforcement is
advisory.

**Provenance (vote)** — who actually produced a vote: `tool` (the harness ran deterministic checks),
`host-asserted` (your agent reported running tools — the harness cannot verify it), `demo`
(illustrative sample votes), or unlabeled (an ordinary model lens). A CRITICAL's rationale states
tool vs host-asserted.

**Risk gate / risk routing** — the deterministic impact × likelihood score (1–25) that decides whether
(and how) to convene. The *selective-plurality* control.

**Role key** — the key a council role uses to reference a lens/model (e.g. `security_sme`), resolved
through `council-models.json`. A council file never names a model tag directly.

**Route** — who decides next on a verdict: `auto` (verdict stands, action proceeds), `lead_dev`
(developer review), or `human` (a named human must decide/approve).

**Seat** — informal for one lens position in a council's roster ("pin a different family on the
critic's seat").

**Signals** — facts asserted to the control gates (e.g. `human_approver`, `rollback_plan`,
`evidence_provided`) via `convene --signals '<json>'` or the MCP path. On a high-impact action, a
required signal that was never asserted counts as missing → the gates escalate (fail-closed). See
[GATES.md](GATES.md).

**Selective plurality** — the core principle: convene a council only for consequential, uncertain, or
adversarial decisions; use the simplest reliable path otherwise.

**Systemic risk (single-model dependence)** — the danger that one model's blind spots, embedded across
many processes, propagate as common-mode failure at machine speed. The problem councils address.

**`REPLACE_ME` sentinel** — a model-registry placeholder for a lane you must pin to a real model.
`eldercouncil models check` flags any that remain.
