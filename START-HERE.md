<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Start here

Elder Council convenes a structured, multi-lens **council** for high-stakes cyber decisions — and
stays out of the way otherwise. Pick your path.

| I am a… | Go to | Time |
|---|---|---|
| **anyone — just show me a council decide** | run `eldercouncil convene code-council --demo` (keyless) | 5 min |
| **security analyst / threat hunter** | [CONCEPT](docs/CONCEPT.md) → [Threat Hunting council](docs/COUNCILS.md#2-threat-hunting-council--threat-hunting--advisory) → [install](docs/IDE-SUPPORT.md) | 15 min |
| **developer rolling councils into your agent** | [IDE-SUPPORT](docs/IDE-SUPPORT.md) → [Code council](docs/COUNCILS.md#1-code-council--code-council--action-gate) | 20 min |
| **risk / compliance owner** | [METHODOLOGY](docs/METHODOLOGY.md) (routing + governance) → [Compliance](docs/COUNCILS.md#4-multi-jurisdictional-compliance-council--compliance--advisory--scheduled) / [Cyber Risk](docs/COUNCILS.md#5-cyber-risk-council--cyber-risk--advisory) | 30 min |
| **security owner / skeptic** | [THREAT_MODEL](THREAT_MODEL.md) → [STANDARDS-MAP](docs/STANDARDS-MAP.md) | 20 min |
| **non-technical** | ask your coding agent to install it: *"install eldercouncil for this project"* | 10 min |

## The 5-minute path

```console
pip install eldercouncil
eldercouncil convene code-council --demo --question "merge a diff with a hardcoded AWS key"
```

You'll see five independent lenses vote, a verdict, the **preserved dissent**, and a decision id — all
keyless. Then wire it into your agent:

```console
eldercouncil init                       # guided: pick your agent + councils
eldercouncil install claude-code --all  # or non-interactive
```

## Reading order

1. [README](README.md) — what it is, the councils, how it compares.
2. [docs/CONCEPT.md](docs/CONCEPT.md) — the *why*: systemic risk + selective plurality (5 min).
3. [docs/COUNCILS.md](docs/COUNCILS.md) — the councils; pick yours.
4. [docs/IDE-SUPPORT.md](docs/IDE-SUPPORT.md) — install into your agent.
5. [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the full method, for depth (not the front door).

## Honest by design

Councils are **decision support, not a guarantee** — they can be wrong, a named human owns every
critical and risk-acceptance call, the audit is **tamper-evident, not tamper-proof**, and the harness
**ships no keys** (bring your own LLM). See [THREAT_MODEL.md](THREAT_MODEL.md).
