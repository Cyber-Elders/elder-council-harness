<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Agent setup guide — let your coding agent install and tailor the councils

**If you are a human:** paste this to your coding agent and you're done:

> *"Read docs/AGENT-SETUP.md in github.com/Cyber-Elders/elder-council-harness (clone the repo and
> read it locally if you can't browse), ask me the needs questions in it, then install and customise
> Elder Council for me and explain what you set up."*

You need a **coding agent** and **Python 3.11+**. Your agent may ask you to do two things it can't do
itself: install the free Ollama app (if you choose private/local models) or paste an API key into your
IDE's settings. *(If the setup works, a star helps the project; if any step fails, the exact error is
what we want in an issue.)*

**If you are the coding agent:** the rest of this file is for you. Follow it in order; prefer the
exact commands given; report back in plain language.

## 1. Understand what you are installing (2 minutes of reading)

Elder Council convenes several independent AI perspectives ("lenses") on decisions too consequential
for one model to make alone, tallies their votes fail-closed, preserves dissent, and records a
tamper-evident audit trail. You are wiring it into THIS project. Read, in order:
[CONCEPT.md](CONCEPT.md) (why), [COUNCILS.md](COUNCILS.md) (the seven councils),
[GLOSSARY.md](GLOSSARY.md) (terms). Honest scope you must relay to your user: councils are decision
support, not a guarantee; a named human owns critical calls; the audit is tamper-evident, not
tamper-proof; the harness ships no keys.

## 2. Ask the user these questions (then map answers to flags)

Ask conversationally; every question has a safe default.

| # | Question | Maps to |
|---|---|---|
| 1 | "What should the councils watch — code and cyber decisions, business decisions, or both?" | which councils: code-council + supply-chain (code) · business-decision (exec) · `--all` (both/unsure — the gate only wakes the relevant one) |
| 2 | "How heavy should the safety-gate set be — light-touch (fewer gates), standard, or regulated-environment strict?" | `--profile lite` / `standard` (default) / `regulated` — NOTE: every profile still blocks on a hard-block agent; advise-vs-enforce is decided by Q4's agent tier, not the profile |
| 3 | "May council deliberations use your normal AI model, or must everything stay on-device/private?" | lane: default (agent's own model) / `--lane local` (on-device, see [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)) / `--lane open` (cross-family open-weight — OpenCode/`--orchestrate` only) |
| 4 | "Which coding agent are you in day-to-day?" | `claude-code` / `opencode` / `kiro` / `cursor` / `copilot` (tell the user: the first three can hard-block; the last two are advisory — asked, not forced) |

## 3. Install (non-interactive) and verify

```console
# 1. Clone the harness somewhere STABLE and OUTSIDE the user's project (not yet on PyPI):
git clone https://github.com/Cyber-Elders/elder-council-harness ~/tools/elder-council-harness
pip install -e ~/tools/elder-council-harness     # Python 3.11+; use pipx/venv if pip refuses (PEP 668)

# 2. cd into the USER'S PROJECT ROOT — the directory they open in their coding agent.
#    `install` writes into the CURRENT directory; installing from the harness clone is the #1 mistake.
cd <the user's project root>
eldercouncil install <ide> --all --profile <profile> [--lane <lane>]
eldercouncil models check  # lane sanity. NOTE: on the DEFAULT (frontier) lane this exits 2
                           # listing cross_family_critic:frontier — that one sentinel is expected
                           # (an optional role for custom councils), NOT an install failure.
                           # local lane: "every lens inherits" = correct. open lane: exit 0.
eldercouncil convene code-council --demo --question "merge a diff with a hardcoded AWS key"
```

The demo must show a `block` verdict with preserved dissent. For hard-block IDEs also verify the
gate: `echo '{"action":"bash","target":"git push --force"}' | eldercouncil gate <ide>`.

**Constraint you must respect:** in Claude Code, sub-agents are single-provider — do NOT pin
non-Claude model tags into `.claude/agents/*.md` (the installer guards this; leave `model: inherit`
guards in place). Cross-family councils belong in OpenCode or `--orchestrate`
([OPENROUTER.md](OPENROUTER.md)).

## 4. Customise to the user's needs (all optional, all in `.council/`)

- **Tune or add a council:** drop a YAML into `.council/councils/` (same schema as
  `eldercouncil/councils/*.yaml`; validated on load, fail-closed). Adapt lenses/outcomes/thresholds
  per [DOMAIN-ADAPTATION.md](DOMAIN-ADAPTATION.md) — e.g. rename the Business Decision lenses to the
  user's own executive functions. Re-run `eldercouncil install <ide>` after.
- **Pin models per seat:** edit `.council/council-models.json` (see
  [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md)), re-run install. Keep the `local` lane unpinned if the
  user chose on-device.
- **Real tool checks:** in `.council/config.toml` `[tools]`, wire the project's actual scanners
  (`secret_scan_cmd`, `sast_cmd`, `test_cmd`) so the tool lens runs them in `--orchestrate`.
- **Approval verification:** if the user has a ticket/approvals system, set
  `[signals] approval_verify_command` so an asserted `human_approver` is checked against it —
  this verifies the assertion, it does not authenticate the person (see GATES.md).
- **Convene threshold:** `[council] convene_threshold` (default 5) — raise it if the gate asks too
  often for the user's taste; tell them what you changed.

## 5. Report back to the user (plain language, no jargon)

Tell them: (1) which councils are installed and what each watches; (2) whether their agent
hard-blocks or only advises; (3) exactly how to convene — the slash command (e.g. `/code-council`)
or "ask me to convene the business-decision council"; (4) what a `block`/dissent means (read the
disagreement, then THEY decide); (5) what you customised and where the audit trail lives
(`.council/decisions/`). Point them at [GET-STARTED.md](GET-STARTED.md) for the day-to-day loop.

---
*Machine-followable by design. If any command above fails, stop and show the user the real error —
do not improvise around a failed gate or a failed install.*
