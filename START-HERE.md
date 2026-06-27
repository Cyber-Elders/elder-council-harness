<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Start here

Elder Council convenes a structured, multi-lens **council** when a decision is too consequential to
leave to one model alone — built for cyber (where it runs deepest), and general enough for any
high-stakes call, including executive business decisions. It stays out of the way otherwise. Pick your path.

| I am a… | Go to | Time |
|---|---|---|
| **anyone — just show me a council decide** | run `eldercouncil convene code-council --demo` (keyless) | 5 min |
| **security analyst / threat hunter** | [CONCEPT](docs/CONCEPT.md) → [Threat Hunting council](docs/COUNCILS.md#2-threat-hunting-council--threat-hunting--advisory) → [install](docs/IDE-SUPPORT.md) | 15 min |
| **developer rolling councils into your agent** | [IDE-SUPPORT](docs/IDE-SUPPORT.md) → [MODEL-GUIDANCE](docs/MODEL-GUIDANCE.md) → [Code council](docs/COUNCILS.md#1-code-council--code-council--action-gate) | 20 min |
| **risk / compliance owner** | [METHODOLOGY](docs/METHODOLOGY.md) (routing + governance) → [Compliance](docs/COUNCILS.md#4-multi-jurisdictional-compliance-council--compliance--advisory--scheduled) / [Cyber Risk](docs/COUNCILS.md#5-cyber-risk-council--cyber-risk--advisory) | 30 min |
| **security owner / skeptic** | [THREAT_MODEL](THREAT_MODEL.md) → [STANDARDS-MAP](docs/STANDARDS-MAP.md) | 20 min |
| **executive / leadership (a high-stakes business call)** | try `eldercouncil convene business-decision --demo` → [Business Decision council](docs/COUNCILS.md#7-business-decision-council--business-decision--advisory) | 10 min |
| **new here / not a developer** | [**GET-STARTED**](docs/GET-STARTED.md) — install → what changed → how you actually use a council, in plain English | 10 min |

## The 5-minute path — see it decide first

The fastest taste needs **no keys and no model** — a one-time install from source (alpha; not yet on
PyPI), then the keyless demo:

```console
git clone https://github.com/Cyber-Elders/elder-council-harness && cd elder-council-harness
pip install -e .
eldercouncil convene code-council --demo --question "merge a diff with a hardcoded AWS key"
```

You'll see five independent lenses vote, a verdict, the **preserved dissent**, and a decision id — all
keyless. Then wire it into your agent:

```console
eldercouncil init                       # guided: pick your agent + councils
eldercouncil install claude-code --all  # or non-interactive
```

## For non-developers

You don't need to be a developer to *use* the councils day-to-day — the one-time install uses a
terminal, but after that you just talk to your coding agent. Elder Council plugs into a **coding agent**;
it runs deepest for cyber and code, but the same machinery handles any high-stakes call (which is why
the example below convenes the Business Decision council, not a code review). The plain-English
walkthrough is **[docs/GET-STARTED.md](docs/GET-STARTED.md)** — start there.

You need two things first: a **coding agent** already set up (e.g. Claude Code, Cursor, or GitHub
Copilot) and **Python 3.11+**. If you have them, you don't have to touch the terminal yourself — paste
this to your coding agent (replace `claude-code` with whichever you use — `cursor`, `opencode`,
`copilot`):

> *"Check that Python 3.11+ is installed, then install Elder Council from source
> (github.com/Cyber-Elders/elder-council-harness), run `eldercouncil install claude-code`, and show me
> the output of `eldercouncil convene business-decision --demo`."*

**Does your agent run on local models (e.g. Claude Code on Ollama)?** Tell it to add `--lane local` to
that install, or it'll error — see [docs/CLAUDE-CODE-OLLAMA.md](docs/CLAUDE-CODE-OLLAMA.md). Then read
[GET-STARTED.md](docs/GET-STARTED.md) → *"How you actually use it"* so you know how to convene a council
(Business Decision is advisory — you convene it deliberately) and read its verdict.

**No coding agent yet?** Get one first — e.g. **Claude Code** (claude.com/claude-code) or **Cursor**
(cursor.com) — sign in, then come back to [GET-STARTED](docs/GET-STARTED.md). Either way, the keyless
`eldercouncil convene business-decision --demo` works on its own if you just want to *see* a council
decide right now.

## Reading order

1. [README](README.md) — what it is, the councils, how it compares.
2. [docs/CONCEPT.md](docs/CONCEPT.md) — the *why*: systemic risk + selective plurality (5 min).
3. [docs/LOOP-ENGINEERING.md](docs/LOOP-ENGINEERING.md) — how a council fits an agent's turn-by-turn loop.
4. [docs/COUNCILS.md](docs/COUNCILS.md) — the councils; pick yours.
5. [docs/MODEL-GUIDANCE.md](docs/MODEL-GUIDANCE.md) — choose which model plays each lens; avoid a single-provider monoculture (the failure councils exist to prevent). Read *before* installing — some IDEs (notably Claude Code) lock a whole session to one provider.
6. [docs/IDE-SUPPORT.md](docs/IDE-SUPPORT.md) — install into your agent.
7. [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the full method, for depth (not the front door).

## Honest by design

Councils are **decision support, not a guarantee** — they can be wrong, a named human owns every
critical and risk-acceptance call, the audit is **tamper-evident, not tamper-proof**, and the harness
**ships no keys** (bring your own LLM). See [THREAT_MODEL.md](THREAT_MODEL.md).
