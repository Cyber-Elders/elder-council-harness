<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Start here

Elder Council convenes a structured, multi-lens **council** when a decision is too consequential to
leave to one model alone — built for cyber (where it runs deepest), and general enough for any
high-stakes call, including executive business decisions. It stays out of the way otherwise. Pick your path.

| I am a… | Go to | Time |
|---|---|---|
| **anyone — just show me a council decide** | run `eldercouncil convene code-council --demo` (keyless) | 5 min |
| **security analyst / threat hunter** | [CONCEPT](docs/CONCEPT.md) → [Threat Hunting council](docs/COUNCILS.md#2-threat-hunting-council--threat-hunting--advisory) → [install](docs/IDE-SUPPORT.md) | 15 min |
| **developer rolling councils into your agent** | [IDE-SUPPORT](docs/IDE-SUPPORT.md) → [Code council](docs/COUNCILS.md#1-code-council--code-council--action-gate) | 20 min |
| **risk / compliance owner** | [METHODOLOGY](docs/METHODOLOGY.md) (routing + governance) → [Compliance](docs/COUNCILS.md#4-multi-jurisdictional-compliance-council--compliance--advisory--scheduled) / [Cyber Risk](docs/COUNCILS.md#5-cyber-risk-council--cyber-risk--advisory) | 30 min |
| **security owner / skeptic** | [THREAT_MODEL](THREAT_MODEL.md) → [STANDARDS-MAP](docs/STANDARDS-MAP.md) | 20 min |
| **executive / leadership (a high-stakes business call)** | try `eldercouncil convene business-decision --demo` → [Business Decision council](docs/COUNCILS.md#7-business-decision-council--business-decision--advisory) | 10 min |
| **non-technical** | [For non-developers](#for-non-developers) — ask your coding agent to set it up | 10 min |

## The 5-minute path

```console
# Not yet on PyPI (alpha) — install from source for now:
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

Elder Council is a developer tool — it runs in a terminal and plugs into a **coding agent**. It runs
deepest for cyber and code, but the same machinery handles any high-stakes call — which is why the
example below convenes the Business Decision council, not a code review. To use it you need two things
first: a coding agent already set up (e.g. Claude Code, Cursor, Copilot), and Python 3.11+ available to it. If you have those, you don't have to touch the terminal yourself — paste
this to your coding agent:

> *"Check that Python 3.11+ is installed, then install Elder Council from source
> (github.com/Cyber-Elders/elder-council-harness), run `eldercouncil install <my agent>`, and show me
> the output of `eldercouncil convene business-decision --demo`."*

If you don't have a coding agent at all, this tool isn't usable for you yet — ask a colleague to show
you the `convene … --demo` output (it needs no keys and no setup beyond the install above).

## Reading order

1. [README](README.md) — what it is, the councils, how it compares.
2. [docs/CONCEPT.md](docs/CONCEPT.md) — the *why*: systemic risk + selective plurality (5 min).
3. [docs/LOOP-ENGINEERING.md](docs/LOOP-ENGINEERING.md) — how a council fits an agent's turn-by-turn loop.
4. [docs/COUNCILS.md](docs/COUNCILS.md) — the councils; pick yours.
5. [docs/IDE-SUPPORT.md](docs/IDE-SUPPORT.md) — install into your agent.
6. [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the full method, for depth (not the front door).

## Honest by design

Councils are **decision support, not a guarantee** — they can be wrong, a named human owns every
critical and risk-acceptance call, the audit is **tamper-evident, not tamper-proof**, and the harness
**ships no keys** (bring your own LLM). See [THREAT_MODEL.md](THREAT_MODEL.md).
