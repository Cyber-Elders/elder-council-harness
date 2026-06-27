<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Choosing models for council roles

> Which model should play each lens? It depends on **what your coding agent can actually run** and on
> **how much you can keep local**. This guide maps the role archetypes in
> [`council-models.json`](../eldercouncil/council-models.json) to concrete, real models for three
> deployment styles — IDE-native, privacy-first (all local), and hybrid (local + cloud).
>
> **Model tags age fast.** Treat every specific tag below as an *example as of writing* — verify the
> current release and **re-pin quarterly** (`eldercouncil models check`). The harness ships only
> verified-real Anthropic tags as defaults; every open-weight and local lane ships as a
> `REPLACE_ME:<capability>` sentinel **you** pin. This guide is how to pin them well.

> ### Just want councils on your own models — step by step?
> - **Claude Code + Ollama (simplest, fully local):** → **[CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)** — copy-paste recipe; every lens runs on one local model.
> - **All-local *cross-family* (OpenCode):** → [recipe in §3](#recipe--all-local-cross-family-opencode) below.
> - **Hybrid (local + cloud):** → [recipe in §4](#recipe--hybrid-local--ollama-cloud) below.
>
> This page is the *why / which-model* reference behind those recipes. New to the whole thing? Start at
> [GET-STARTED.md](GET-STARTED.md).

## The one rule: diversify the council

A council's entire value is **plural scrutiny**. If every lens runs on the *same* model — or even the
same model *family* — they tend to share the same blind spot, and a confident wrong answer sails
through unanimously. That correlated failure is the exact thing a council exists to prevent (run
`eldercouncil convene <c> --demo --scenario monoculture` to watch it happen). So the goal when pinning
models is **spread the lenses across distinct model families/lineages**. `eldercouncil models check`
warns you when every frontier lens resolves to one provider.

## Role → capability → family

Each role needs a different strength. Assign families so that no two adjacent lenses share a lineage.

| Role (`role_key`) | Needs | Example open family |
|---|---|---|
| `strategic_risk_owner`, `ir_owner`, `arbitrator` | deep multi-step reasoning, judgement | Qwen, DeepSeek |
| `engineering_sme`, `detection_engineer` | code / log / SAST reasoning | Qwen-Coder |
| `security_sme` | adversarial / exploit-path reasoning | DeepSeek-R1, gpt-oss |
| `compliance_legal_sme` | long context (regulations, evidence) | Qwen (long-ctx) |
| `critic_challenge`, `adversary_redteam` | devil's-advocate, flaw-finding | Mistral (a *different* lineage) |
| `pragmatic_ops` | fast, cheap, "what's the safe next step" | Gemma, small Qwen |
| `synthesiser` | coherent integration, preserve dissent | Qwen, gpt-oss |
| `cross_family_critic` | **deliberately a different family** from all the others | gpt-oss (OpenAI lineage) |
| `deterministic_tool` | **not an LLM** — SAST / scan / tests as evidence | — |

## 1. Client journeys — what your IDE can actually run

This is the part most guides skip: **your IDE decides whether a cross-family council is even possible.**
Some agents lock every sub-agent in a session to one provider.

| Agent | Cross-family in one session? | How to get diversity |
|---|---|---|
| **Claude Code** | **No — single provider per session.** A sub-agent's `model:` accepts only Claude values (`opus` / `sonnet` / `haiku` / a full Claude id / `inherit`). You can point the **whole session** at a local/3rd-party backend via `ANTHROPIC_BASE_URL` (Ollama, LM Studio, OpenRouter, …), but that swaps *every* agent at once — per-agent providers aren't supported. | Vary the **tier** (Opus for the hard lenses, Haiku for `pragmatic_ops`) for cost — but accept it's one family. Get real diversity from the **deterministic Tool lens + the human owner**, from **separate sessions** each on a different backend, or from the **`--orchestrate` / MCP path** running your own mixed models. |
| **OpenCode** | **Yes — per agent.** Each agent sets `model: provider/model-id` (e.g. `anthropic/…`, `openai/…`, `ollama/qwen3-coder:30b`); different families run concurrently. | Assign each `role_key` a model from a different family directly. Best in-IDE fit for a true cross-family council. |
| **Cursor** | **Partly.** BYOK (OpenAI / Anthropic / Gemini / any OpenAI-compatible incl. local Ollama & LM Studio) works in **chat**, but **Agent mode doesn't take custom keys yet** — so the advisory/chat council can be cross-family; the autonomous agent is constrained. | Use the advisory council (Cursor is advisory-tier anyway) with BYOK models in chat; pin your mixed models there. |
| **GitHub Copilot** | **Yes — via BYOK.** Add providers (OpenAI, Anthropic, Gemini, OpenRouter, LM Studio, Ollama, any OpenAI-compatible) in Settings → Model Providers. | Pin each lens to a model from a different provider you've added. |
| **Kiro** | **Within its hosted catalog.** Closed, Kiro/AWS-hosted set spanning Claude plus several hosted open models — cross-family is possible but only from that catalog, and hosted-only (no local). | Pick lenses from different families in its catalog; no local/privacy option. |

> **Takeaway.** If you live in **Claude Code**, your in-session lenses are one family — lean on the Tool
> lens, the human, and `--orchestrate`/MCP for diversity. If you want a genuinely cross-family council
> *inside* one agent, **OpenCode** (or Copilot/Cursor via BYOK) is the smoother path.

## 2. Open-weight picks per role (Ollama / OpenCode / BYOK)

A worked **cross-family** assignment using current, openly-licensed models. The point isn't these exact
tags — it's that **five different lineages** are represented (Alibaba · DeepSeek · Mistral · Google ·
OpenAI), so the lenses don't fail together.

| Role | Example model (Ollama tag) | Family | Why |
|---|---|---|---|
| `strategic_risk_owner` / `arbitrator` | `qwen3:32b` | Alibaba | strong multi-step reasoning at a single-GPU size |
| `ir_owner` | `deepseek-r1:32b` | DeepSeek | put the second reasoning seat on a *different* family than the risk owner |
| `engineering_sme` / `detection_engineer` | `qwen3-coder:30b` | Alibaba (Coder) | code/SAST/log-trace reasoning |
| `security_sme` | `deepseek-r1:32b` | DeepSeek | explicit long chain-of-thought suits exploit-path / edge-case reasoning |
| `compliance_legal_sme` | `qwen3:32b` (long-context build) | Alibaba | long regulations/contracts/evidence in one pass |
| `critic_challenge` / `adversary_redteam` | `magistral:24b` | Mistral | a genuinely different lineage → surfaces flaws the others' shared training won't |
| `pragmatic_ops` | `gemma3:12b` (or `qwen3:8b`) | Google | fast, low-VRAM, yet another distinct family |
| `synthesiser` | `gpt-oss:20b` | OpenAI (open) | coherent integrator from a non-Qwen/non-DeepSeek voice |
| `cross_family_critic` | `gpt-oss:20b` (or `:120b`) | OpenAI (open) | **deliberately** a different lineage from every other seat |

**Quantization.** For dense 8–32B models, **Q4_K_M** is the quality/size sweet spot; step to Q5/Q6 on
the reasoning and arbitrator seats if you have the memory. `gpt-oss` ships natively low-bit (MXFP4), so
`gpt-oss:20b` fits ~16 GB and `gpt-oss:120b` needs a 64–80 GB box. **Licenses:** Qwen, Mistral, and
gpt-oss are Apache-2.0; DeepSeek-R1 is MIT; Gemma uses Google's Gemma license (not OSI-approved) — pick
Apache/MIT seats if you need clean commercial redistribution.

## 3. Privacy-first — run the whole council locally

Nothing leaves the device. On **Apple Silicon** use **MLX** (`mlx-lm`, models from the `mlx-community`
org) for the best speed/memory on Mac; Ollama also works and is easier to set up. On a **Windows/Linux
"AI PC"** use **Ollama** or **LM Studio** — and note the catch: today's **NPUs are not usefully usable**
for 20B-class models, so a real CUDA/ROCm dGPU (or a unified-memory APU) matters far more than the
NPU's TOPS number.

The constraint is **memory headroom**: the OS + runtime + KV-cache for real context eat roughly a third
of nominal RAM, so plan on weights using ~60–70% of it. The **MoE trick** is what makes 2026 work
locally — a 30B model with ~3B *active* params (an "A3B" MoE) gives ~30B-class quality at ~16 GB and
high tokens/sec, because only the active experts hit the GPU per token.

| Unified RAM | Realistically fits (4-bit) | Council posture | Keep local | Offload (hybrid/cloud) |
|---|---|---|---|---|
| **16 GB** | one 8–14B dense, *or* one 30B-A3B MoE at the edge | one shared small model for the light roles | `pragmatic_ops`, `synthesiser`, `critic` | reasoning, security, deep-code, long-context |
| **24 GB** | one 30B-A3B MoE (~16–17 GB) *or* `gpt-oss:20b` | most roles on a MoE workhorse + a small different-family critic | most roles | a heavier arbitrator (optional) |
| **48 GB** | a 30B-A3B MoE **plus** a second 12–20B model resident | **nearly the whole council, concurrently** | reasoning + code + a distinct-family critic + a fast model | only the giant (100B+) brains |

**Example local seats:** `qwen3:8b` / `gemma3:12b` (fast & light), `qwen3:30b` or `gpt-oss:20b`
(MoE workhorse for most roles), `qwen3-coder:30b` (code), `magistral:24b` or `gpt-oss:20b` (a
different-family critic). On 16 GB you mostly run **one** model and swap; 24 GB is the inflection where
a real multi-lens local council becomes practical; 48 GB holds several distinct-family models at once.

### Recipe — all-local *cross-family* (OpenCode)

For a genuinely cross-family council with **nothing leaving the device**, **OpenCode** is the smoothest
agent (it runs a different model per lens). On Claude Code you'd instead run every lens on one local
model — see [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md).

```console
# 1. Pull a few DIFFERENT-family models that fit your RAM (see the table above)
ollama pull gpt-oss:20b          # MoE workhorse for most roles
ollama pull magistral:24b        # a different lineage (Mistral) for the critic
ollama pull qwen3:8b             # fast/light for pragmatic_ops   (on 16 GB: pull one, swap)

# 2. Install Elder Council for OpenCode on the local lane
git clone https://github.com/Cyber-Elders/elder-council-harness && cd elder-council-harness
pip install -e .
eldercouncil install opencode --all --lane local

# 3. Pin each lens to a different family in .council/council-models.json (the `local` lane),
#    using OpenCode's provider/model form, then re-install to apply:
#      "security_sme":     { "local": "ollama/gpt-oss:20b" }
#      "critic_challenge":  { "local": "ollama/magistral:24b" }
#      "pragmatic_ops":     { "local": "ollama/qwen3:8b" }
eldercouncil install opencode --all --lane local
eldercouncil models check        # confirms diversity; flags a monoculture
```

Any lens you leave unpinned simply **inherits** your agent's default model — so you can pin only the
seats that matter (the critic + a couple of reasoning seats) and let the rest follow. That alone breaks
the worst monoculture.

## 4. Hybrid — local where it's cheap and private, cloud where it's hard

Keep the **small, frequent, sensitive** lenses local (free, on-device, no data egress); send only the
**heavy reasoning** lenses to the cloud. **Ollama Cloud** is the smoothest hybrid because cloud models
are called through the *same* local CLI/API — you just append a `-cloud` suffix (e.g.
`ollama run gpt-oss:120b-cloud`) after `ollama signin`, and your client code is unchanged.

| Tier | Cost | Concurrent cloud models | Good for |
|---|---|---|---|
| **Local only** | **$0** | — | privacy-first; everything on your own hardware |
| **Ollama Cloud Free** | **$0** | **1** | one heavy lens in the cloud, the rest local (lenses run sequentially) |
| **Ollama Cloud Pro** | **$20/mo** (≈$200/yr) | **3** | up to **3 heavy lenses in parallel** + larger models + private model upload |
| **Ollama Cloud Max** | **$100/mo** | **10** | large or many-council deployments |

**A practical hybrid split:**
- **Local (free, private):** `pragmatic_ops` and `synthesiser` — small, run constantly, latency-sensitive,
  and benefit from never leaving the device. Use ≤~9B models (e.g. `qwen3:8b`, `gemma3:12b`) so several
  co-reside; set `OLLAMA_KEEP_ALIVE=5m` so they don't pin memory.
- **Cloud (Ollama Pro, up to 3 in parallel):** the heavy lenses — `strategic_risk_owner`, `security_sme`,
  `critic_challenge` — on a large `:cloud` model (e.g. `gpt-oss:120b-cloud`).

> **Privacy caveat — load-bearing.** Cloud means **data leaves the device**: every prompt, code diff, log,
> or piece of evidence you send to a `:cloud` lens transits the provider's infrastructure (Ollama states
> its cloud doesn't retain data, but it still transits). For **regulated or sensitive** council inputs,
> keep those lenses **local-only** — that's exactly what the `local` lane in `council-models.json` is for.

### Recipe — hybrid (local + Ollama Cloud)

Small/frequent lenses stay local and private; the heavy reasoning lenses borrow a big cloud model —
both through the *same* Ollama, so your setup barely changes.

```console
# 1. Sign in to Ollama Cloud (Free = 1 cloud model; Pro $20/mo = 3 in parallel)
ollama signin

# 2. Pull the local (private) seats + reference a big `-cloud` model for the heavy seats
ollama pull qwen3:8b                      # local: pragmatic_ops, synthesiser
ollama run  gpt-oss:120b-cloud "ok"       # cloud: warms up the heavy model

# 3. Install on the local lane, then pin the heavy seats to the `-cloud` model in
#    .council/council-models.json (`local` lane) and re-install:
#      "strategic_risk_owner": { "local": "ollama/gpt-oss:120b-cloud" }
#      "security_sme":          { "local": "ollama/gpt-oss:120b-cloud" }
#      "pragmatic_ops":         { "local": "ollama/qwen3:8b" }      # stays on-device
eldercouncil install opencode --all --lane local
eldercouncil models check
```

Keep anything **regulated or sensitive** on a local-only seat (see the privacy caveat above) — only
non-sensitive lenses should point at a `-cloud` model.

## 5. Running a council: three ways

However you pin models, there are three ways to actually *run* a council — pick by what you're doing:

| Command | What it does | Use it when |
|---|---|---|
| `eldercouncil convene <c> --demo` | **Keyless illustration** — deterministic sample votes, instant, no models. | You just want to *see* a council decide (trying it out, demos, CI). |
| `eldercouncil convene <c>` *(no flag)* | Emits the **deliberation tasks** (JSON) for your **coding agent** to run on its own models — this is what the gate/slash-command flow uses inside your IDE. | Day-to-day, **inside an installed agent** (Claude Code, OpenCode, …). You normally trigger this with `/<council>`, not by hand. |
| `eldercouncil convene <c> --orchestrate` | The **harness itself** runs your **pinned** models and returns a real verdict — **no IDE needed**. Requires the optional runner (`pip install "eldercouncil[orchestrator]"`) and pinned model lanes; unpinned lenses report `unavailable`. | **Headless / CI / no coding agent** — scheduled audits, pipelines, scripts. |

> So: `--demo` to look, your agent (`/<council>`) for everyday use, `--orchestrate` to run councils
> without an IDE. Run `eldercouncil models check` before `--orchestrate` so every lens has a real model.

## Pinning, continuity, and fallback

- **Pin per lane.** Edit [`council-models.json`](../eldercouncil/council-models.json) (or the project copy
  in `.council/`) to replace each `REPLACE_ME:<capability>` with a real tag, then re-run
  `eldercouncil install <ide>` to re-pin every rendered role agent. `eldercouncil models check` lists
  what's still unpinned and warns on monoculture.
- **Re-pin quarterly.** Model tags age; the registry is the single place to update them.
- **Plan for cut-off.** An open-weight model from a single lab can become unavailable (export controls,
  sanctions, licensing). For critical councils, add a `fallback` list per role and keep a **local** lane
  pinned, so a provider going dark doesn't disable the process.
- **The deterministic Tool lens needs no model** — it runs SAST / dependency / secret scans / tests and
  feeds findings in as evidence. It's your most reliable non-model voice; lean on it, especially in
  single-provider IDEs.

See also: [LENSES.md](LENSES.md) (what each lens does) · [IDE-SUPPORT.md](IDE-SUPPORT.md) (per-IDE
install) · [THREAT_MODEL.md](../THREAT_MODEL.md) (why model diversity is a security property, not a
nicety).
