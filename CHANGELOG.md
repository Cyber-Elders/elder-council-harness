<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Changelog

All notable changes to Elder Council Harness are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.1.0] — unreleased (alpha)

First alpha. A local-first, multi-model **council** harness for high-stakes cyber decisions —
selective plurality, deterministic risk routing, a fail-closed consensus tally, and a tamper-evident
audit. Bring-your-own-LLM; ships no keys.

### Added

- **Eleven deterministic control gates + Lite/Standard/Regulated profiles** (`eldercouncil/gates.py`,
  `gate-policy.yaml`): a fail-closed control layer around the council — a gate can block or escalate an
  action even when the council voted to permit it (the recorded **disposition** is the most restrictive
  of the council route and the gate result). Offensive-cyber-misuse is a non-overridable **hard stop**.
  `eldercouncil gates list|check`, a `--profile` flag, and the pre-tool detector overlay. Decision
  records and the hash-chained audit now capture gate outcomes + profile.
- **Seven councils** (pure-data YAML, installable into every supported IDE): six cyber — Code, Threat
  Hunting, Supply Chain Audit, Multi-Jurisdictional Compliance, Cyber Risk, Platform Architecture —
  plus a general **Business Decision** council for high-stakes, non-cyber executive calls.
- **Deterministic core:** `risk_gate` (impact × likelihood, 1–25 routing), `consensus` (minimum-
  governance fail-closed tally), `audit` (hash-chained, tamper-evident decision records + dissent),
  `schema`/`catalog` (council loading + validation), `models` (role→model registry resolution).
- **Six SME lenses** + specialised roles, with role-based model resolution (`council-models.json`,
  `frontier`/`open`/`local` lanes; ships only verified-real Anthropic tags, the rest as `REPLACE_ME`
  sentinels).
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

### Honesty

Councils are decision support, not a guarantee — they can be wrong; a named human owns every critical
and risk-acceptance decision; the audit is tamper-evident, not tamper-proof; the harness ships no keys.
