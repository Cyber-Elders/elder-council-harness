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
  gate fail-closed guard, and `verify`. **199 tests**; UAT green on Ubuntu / macOS / Windows.

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
