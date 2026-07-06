<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Changelog

All notable changes to Elder Council Harness are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.1.0] — unreleased (alpha)

First alpha. A local-first, multi-model **council** harness for high-stakes decisions — built for
cyber, general enough for any call too consequential to leave to one model alone. Selective plurality,
deterministic risk routing, a fail-closed consensus tally, and a tamper-evident audit.
Bring-your-own-LLM; ships no keys.

### Added

- **Eleven deterministic control gates + Lite/Standard/Regulated profiles** (`eldercouncil/gates.py`,
  `gate-policy.yaml`): a fail-closed control layer around the council — a gate can block or escalate an
  action even when the council voted to permit it (the recorded **disposition** is the most restrictive
  of the council route and the gate result). Offensive-cyber-misuse is a non-overridable **hard stop**.
  `eldercouncil gates list|check`, a `--profile` flag, and the pre-tool detector overlay. Decision
  records and the hash-chained audit now capture gate outcomes + profile.
- **Eight councils** (pure-data YAML, installable into every supported IDE): six cyber — Code, Threat
  Hunting, Supply Chain Audit, Multi-Jurisdictional Compliance, Cyber Risk, Platform Architecture —
  plus a general **Business Decision** council for high-stakes executive calls and an **Engineering
  Team** council (developer + analyst + QA + tool + critic) for everyday design/feature reviews.
- **Deterministic core:** `risk_gate` (impact × likelihood, 1–25 routing), `consensus` (minimum-
  governance fail-closed tally), `audit` (hash-chained, tamper-evident decision records + dissent),
  `schema`/`catalog` (council loading + validation), `models` (role→model registry resolution).
- **Six SME lenses** + specialised roles, with role-based model resolution (`council-models.json`,
  `frontier`/`open`/`local` lanes; verified-real defaults only — Anthropic on frontier, a
  cross-family open-weight set on open, local unpinned = inherit).
- **IDE adapters:** Claude Code, OpenCode (hard-block); Kiro (best-effort hard-block); Cursor, GitHub
  Copilot + any MCP client (advisory). Generic renderer — councils are data, no per-council code branches.
- **CLI:** `init`, `install`, `list`, `show`, `convene` (`--demo` / `--orchestrate`), `gate`, `audit`,
  `risk-gate`, `models`, `verify`, `audit-summary`, `serve`, `version`.
- **Advisory MCP server** (`[mcp]`): `risk_gate`, `convene_council`, `audit_log`, `audit_summary`.
- **Optional BYO-LLM orchestrator** (`[orchestrator]`): headless councils on your own Anthropic /
  OpenRouter / Ollama access (credentials from env).
- **Three-tier testing:** deterministic regression, clean-install UAT, and full agentic UAT (+ nightly
  agentic regression). CI honesty + leak + secret + determinism gates.
- Full docs suite, dual licensing (Apache-2.0 + CC BY 4.0), and governance.

### Security & honesty (external-review remediation)

An external review made substantive critiques; every one was verified against the code and fixed —
plus one more defect found by our own follow-up audit:

- **The "deterministic tool lens" now IS deterministic in `--orchestrate`.** It previously sent a
  prompt to an LLM asking it to act like a scanner. It now runs REAL checks — built-in
  secret/injection/PII detectors plus your `[tools]` commands from `.council/config.toml`
  (argv-parsed, timeout, fail-safe abstain; a clean scan abstains rather than approving). Votes carry
  **`provenance`** (`tool` / `host-asserted` / `demo`), and a CRITICAL's rationale states tool vs
  host-asserted provenance.
  Authority stays role-based (stripping host-run tool votes would fail open).
- **Out-of-the-box monoculture reduced + detected at decision time.** The **open lane now ships a
  verified-real cross-family default** (Alibaba / DeepSeek / Mistral / Google / OpenAI lineages,
  `ollama/` form). Every decision record carries a **`diversity`** field (which provider families
  actually voted) and the CLI warns at verdict time on a real single-family council — detection +
  warning, not enforcement. The local lane intentionally stays unpinned (= inherit, the on-device
  journey); `cross_family_critic.frontier` stays a sentinel (no verified-real non-Anthropic frontier
  tag to ship).
- **Audit redacts what the built-in detectors flag.** Secrets/PII are redacted at persistence time by
  default (`[audit] redact`, shared detector regexes) across decision records, dissent files, and
  gate events — decision ids and the hash chain are unaffected. Redaction is conservative (common
  credential/PII shapes), not a guarantee — see THREAT_MODEL.md.
- **Human approval is provenance-checked.** `human_approver` is recorded as `asserted — unverified`
  by default; an optional `[signals] approval_verify_command` verifies it (non-zero/timeout strips
  the assertion → the gates escalate, fail-closed). `convene --signals '<json>'` plumbs asserted
  signals from the CLI (malformed → exit 2).
- **Vote parsing hardened.** Markdown-bolded protocol lines, "my vote is …", numeric/percent
  confidence, and spaced multi-word outcomes now parse; ambiguous containment resolves to the MOST
  RESTRICTIVE outcome (never permissively).
- **Risk-gate keyword precision.** Word-boundary matching (no more `rm ` inside `charm `, `prod`
  inside `reproduce`); `isolate` removed from the destructive list (it is a threat-hunting outcome);
  the cry-wolf failure mode is now documented alongside the bypass limit.
- **Provider routing fixed (found by our own audit).** `ollama/<tag>` mis-routed to OpenRouter in
  `--orchestrate` (the generic `/` rule matched first) and explicit Ollama pins could fall back to
  Anthropic; both fixed, with prefix stripping on both clients.

### Fixed

- **`--lane local` / `--lane open` now actually select the lane.** Every role defaulted to
  `variant: "frontier"`, which silently overrode the install/convene `--lane` flag — so the local and
  open model lanes were unreachable. `Role.variant` now defaults to `None` (follow `--lane`); a role
  may still pin its own lane explicitly. `eldercouncil install <ide> --all --lane local` now makes
  every lens **inherit** your agent's own model — the basis of the local/Ollama recipe. Regression
  tests added.

### Tests

- **Full-journey coverage at both layers.** A coverage audit enumerated every supported user journey
  and found many were exercised only at the engine/function layer. Closed the gap: `test_cli_journeys.py`
  asserts each CLI subcommand's exit-code + output contract in-process (models list/resolve, every
  convene run-mode incl. `--orchestrate` fail-closed and `--profile`, `gate`/`audit` per IDE, `gates`,
  `risk-gate` routing, usage errors, `init` defaults, `serve`); and `uat.yml` (clean-install, 3 OS)
  now runs **every** journey — install per IDE × lane, lane-aware `models check`, all run-modes, the
  gate fail-closed guard, and `verify`. **223 tests**; UAT green on Ubuntu / macOS / Windows.

### Added (post-review)

- **Engineering Team council (`eng-team`)** — the everyday design/feature review: Full-Stack
  Developer + Business/Requirements Analyst + Test/QA + Deterministic Tool + Critic, advisory
  (the feature owner decides). `eldercouncil convene eng-team --demo` shows a contested design review.
- **Ollama journeys for every agent, honestly.** `install opencode --lane open` now **auto-wires
  OpenCode's Ollama provider block** (localhost:11434, exactly the pinned models) so the cross-family
  default runs without hand-written config; a per-agent Ollama matrix documents the rest — Copilot
  via the official Ollama extension (chat only; VS Code's built-in provider is deprecated), **Cursor
  cannot reach a localhost endpoint** (custom-key requests route through Cursor's servers), Kiro has
  no local option.
- **Realtime council visibility.** `--orchestrate` now streams each lens's vote as it completes and
  writes every voice's FULL deliberation (redacted) to `.council/last-run/<lens>.md`;
  `tools/watch-council.sh <council> "<question>"` opens a tmux view — one live pane per lens — while
  the harness still runs the fail-closed tally and hash-chained audit.

### Fixed (guides & collateral QA sweep)

A 37-agent adversarially-verified QA pass over every guide, template, example, and visual asset
(33 confirmed findings, all remediated):

- **watch-council panes actually update now.** The runner unlinked+recreated transcripts (new inode),
  so a watcher's `tail -f` stayed frozen on the placeholder forever; transcripts now truncate in
  place and the script uses `tail -F` (+ a pane-id fix for non-zero pane-base-index). Wording
  softened honestly: each voice appears as its lens completes, not token-by-token.
- **`convene` honors the project's configured lane** — a local/open-lane project no longer silently
  resolves frontier Claude tags when `--lane` is omitted.
- **Demo collateral re-synced with the CLI**: the README/GIF decision id had been stale since launch
  (a pre-squash relic) and the GIF's GATES/rationale lines were truncated — regenerated.
- Gate-vs-advisory docs corrected (the gate CAN name an advisory council; "advisory" governs who
  decides, not whether it's suggested); the §3 recipe's missing `qwen3-coder:30b` pull; the example
  ledger's CRITICAL was mis-attributed to AppSec (it belongs to the tool lens) and is refilled from
  the current template incl. gates/disposition/diversity/audit; stale counts and module lists across
  pyproject/ARCHITECTURE/GLOSSARY/CONCEPT/DOMAIN-ADAPTATION/templates/adapters/CONTRIBUTING/
  GOVERNANCE/CODEOWNERS/BRAND/STANDARDS-MAP/METHODOLOGY.

### Fixed (final adversarial pass)

A closing devil's-advocate sweep (three independent break-it lenses, each finding reproduced or
refuted before it counted) found two real fail-open/leak paths and two lower-severity issues — all
fixed with reproductions and regression tests:

- **Audit no longer persists a secret hidden in a `role`/`model` field.** Redaction only scrubbed the
  `reason` of each verdict/dissent entry, so a secret or PII placed in the host-supplied `role` or
  `model` field (e.g. via the MCP `audit_log` tool) reached disk unredacted. Records now redact the
  **whole** verdict/dissent object; decision ids and the hash chain are unaffected.
- **Risk-gate no longer fails open on unrecognised JSON payloads.** A pre-tool payload that was a JSON
  object with neither `action` nor `target` (e.g. `{"tool_name":…,"tool_input":…}`) scored as empty →
  `SOLO_ALLOW` (exit 0) even when it carried a destructive command; the whole raw payload is now scored
  when those keys are absent, so the destructive content still routes to a human.
- **Non-participation is no longer counted as dissent.** An `unavailable`/`abstain` lens was recorded
  in the preserved-dissent list; the tally now excludes non-votes from dissent (they remain non-votes
  in the quorum math, unchanged).
- **`convene --lane` with `--demo`** notes — **only when you actually pass `--lane`** — that the demo
  output is lane-invariant (canned votes), so `--lane` there is a no-op. (A follow-up fixed a
  regression where that note fired on *every* demo: the late stderr write could race a
  `convene --demo … | grep -q` pipeline closing → `BrokenPipeError` / exit 120, which surfaced only on
  the macOS CI runner. `uat.yml` now guards it.) The demo collateral (GIF/PNG) header command matches
  the printed decision id exactly.

### Security (second external review — audit binding + fail-closed gates)

A second external security review (static analysis) raised eight critical/high findings plus mediums.
Every mechanical claim was reproduced by **running the code**, then fixed; the honest limits that
remain are stated plainly in THREAT_MODEL.md rather than papered over. (+17 regression tests pinning
each, `tests/test_review_findings.py`.)

- **The hash chain now binds the FULL decision record, not just the index.** Each decision entry
  carries `record_sha256` over the persisted `decisions/<id>.json`, and `verify()` re-hashes those
  files — so editing a **vote / confidence / reason / dissent / risk** in the full record (previously
  invisible to `verify()`) is caught, as is deleting a bound record. `eldercouncil verify` prints the
  head **and count**, and `verify --expect-head/--expect-count` checks them against an off-box anchor —
  the only thing that catches a full rewrite or tail-truncation.
- **Confidence coercion no longer fails open.** `nan`/`inf` were coerced to **1.0** (full confidence),
  silently defeating the low-confidence floor; they now resolve to `0.0` (the conservative direction).
  The floor is now `<=`, so an omitted `Confidence:` (which defaults to the floor) routes to a human
  instead of auto-proceeding.
- **The pre-tool gate fails CLOSED on a policy error.** The detector overlay caught every exception and
  returned **allow**, dropping the "non-overridable" offensive-misuse hard stop (the base risk gate has
  no offensive vocabulary). It now runs the offensive detector **directly** as a policy-independent
  backstop (hard-stops offensive content even with a corrupt policy), degrades a flagged secret/injection
  to *ask*, and a profile that references an **undefined** gate now **raises** (a truncated `gates:`
  section can no longer silently ALLOW).
- **The MCP `audit_log` path re-runs the deterministic tool lens server-side.** A host agent can no
  longer omit or forge the authoritative tool `CRITICAL` — any host-reported vote carrying the tool role
  is replaced by the genuine server-run finding. Reported lenses that aren't part of the council are
  recorded (`off_council_roles`). Reasoning votes on this path remain host-reported (documented).
- **Env-var policy downgrades leave a trace.** Active `COUNCIL_*` overrides (`observe` mode, `lite`
  profile, raised threshold, redaction off) are recorded in the audit (`policy_overrides`).
- **`--demo` no longer pollutes the real decision log.** Demo runs are chained as `kind:"demo"` and
  excluded from `audit-summary`'s decision counts.

A follow-up **adversarial self-review** (independent skeptics trying to break each fix) then closed two
ways the fixes themselves could be bypassed: **stripping `record_sha256`** from a decision entry (the
substance check is now *required* on every decision/demo entry, so removing it is itself flagged), and a
**neutered offensive gate body** (`fail_closed_if: []`, `hard_stop: false` — the offensive hard stop is
now enforced independently of the policy gate body). Also: a giant-integer confidence no longer crashes
the tally (`OverflowError` → 0.0); `--expect-count` is documented as truncation/append detection only
(**`--expect-head` is the sound anchor** for an in-place rewrite); and THREAT_MODEL.md spells out the two
honest limits of the MCP tool lens (it judges the decision **text**, not the working tree; only councils
that seat a tool lens get the server-run check).

### Fixed (multi-SME end-to-end review)

A full end-to-end review across user journeys, UX, documentation, and implementation closed the
remaining P1/P2 gaps from the external review and added regression coverage for every fix.

- **Consensus coercion no longer crashes on non-string `severity`/`provenance`.** A host or model vote
  carrying an integer/object in these fields used to hit `AttributeError` during normalization and abort
  the tally; they are now coerced to strings before comparison. Regression tests cover both.
- **Control-gate `allow_with_controls` is bounded correctly.** It now applies only to **high-impact**
  actions whose required affirmations are **all** satisfied; a missing affirmation or a low-impact
  fail-closed trip escalates instead of being silently permitted. The gate report carries the active
  `profile`.
- **Engine gate evaluation fails closed on any exception.** Any unexpected error during gate evaluation
  now returns an `escalate` verdict with the error details, rather than bubbling up and leaving the caller
  to decide. The decision record stores the profile and the gate report.
- **Audit chain lock exhaustion now raises.** If the cross-process lock cannot be acquired after retries,
  `audit.record()` raises `OSError` instead of proceeding unlocked and risking a forked/tampered chain.
- **OpenCode pre-tool gate accepts the documented fallback shapes.** The handler now reads `tool`/`args`,
  `tool_name`/`tool_input`, and `action`/`input`, so older or differently-shaped host events still score
  the action rather than falling through as empty.
- **Claude Code install keeps Anthropic-lineage tags under any prefix.** The eligibility check moved from
  `startswith("claude")` to `provider_of(model) != "anthropic"`, so tags like `anthropic/claude-...` or
  `openrouter/anthropic/claude-...` are recognised as runnable in Claude Code instead of being downgraded
  to `inherit`.
- **MCP `audit_log` records gate evaluation + disposition + provenance limits.** The advisory server path
  now writes the gate report, effective disposition, off-council role warnings, and a `host_reported_only`
  flag (for councils without a deterministic tool lens) into the decision record.
- **`models check` distinguishes intentional sentinels from real misconfigurations.** The local lane's
  `REPLACE_ME` entries are reported as intentional inherit; `cross_family_critic.frontier` is flagged as
  an optional sentinel rather than a hard failure; only genuinely unpinned frontier roles exit non-zero.
- **Docs aligned across the user journey.** README quick-start now warns about `pipx`/PATH; GET-STARTED
  explains bare `convene`, `--expect-count`, and the `show` command; AGENT-SETUP notes the monoculture
  warning; OPENROUTER's example uses the correct engineering role; METHODOLOGY/GATES/DESIGN-REVIEW/
  GLOSSARY/THREAT_MODEL language and examples were tightened (e.g., "ties block", `allow_with_controls`,
  three common confusions).
- **Risk gate escalates plaintext destructive commands (post-review QA).** Several unobfuscated destroyers
  (`find … -delete`, `dd if=…`, `chmod -R 777`, fork bombs, `curl … | bash`) scored below the convene
  threshold; the impact heuristic now recognises them and treats pipe-to-shell as an impact signal, so
  they route to a council instead of `SOLO_ALLOW`. `THREAT_MODEL.md` wording corrected: the under-escalation
  limit covers plaintext commands, not only obfuscated ones.

+18 regression tests added across the review-closure and QA passes (consensus, gates, engine, audit,
install, server, CLI journeys, risk gate); total suite now **241 tests**.

### Docs & UX

- **New [OPENROUTER](docs/OPENROUTER.md)** — the cross-family-with-one-key journey: headless
  `--orchestrate`, OpenCode per-agent, Cursor/Copilot BYOK — and the honest limit that Claude Code
  cannot use OpenRouter in-session (Anthropic Messages API vs OpenAI schema).
- **New [AGENT-SETUP](docs/AGENT-SETUP.md)** — a machine-followable guide your coding agent reads to
  understand the harness, elicit your needs, install with the right flags, customise councils/models/
  config, and report back in plain language (one paste-able prompt for the user).
- **Prerequisites stated up front** in every journey doc (what you need — and what you don't).
- **New [GET-STARTED](docs/GET-STARTED.md)** — a task-oriented, non-developer walkthrough: install →
  what changed → how you actually *use* a council (the gate asks → run `/<council>` → read the verdict
  and preserved dissent → you decide). Linked as the front door from the README and START-HERE.
- **New [CLAUDE-CODE-OLLAMA](docs/CLAUDE-CODE-OLLAMA.md)** — a copy-paste recipe to run every council
  on your own local models (Claude Code + Ollama, fully offline), grounded in Ollama's own docs.
- **[MODEL-GUIDANCE](docs/MODEL-GUIDANCE.md)** gains runnable recipes (all-local cross-family on
  OpenCode; hybrid local + Ollama Cloud) and a "three ways to run a council" table that defines
  `--demo`, the in-agent default, and `--orchestrate`.
- **`eldercouncil models check` is lane-aware** — a local-lane (BYO/on-device) project now reads as a
  healthy "every lens inherits your model" setup instead of "✗ unpinned"; the monoculture warning
  names the configured lane.
- **`install` prints per-agent next steps** — hard-block vs advisory guidance, the local-models pointer,
  and a link to GET-STARTED. START-HERE's "For non-developers" path no longer dead-ends.

### Honesty

Councils are decision support, not a guarantee — they can be wrong; a named human owns every critical
and risk-acceptance decision; the audit is tamper-evident, not tamper-proof; the harness ships no keys.
