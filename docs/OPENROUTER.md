<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# One key, many model families — councils via OpenRouter

The whole point of a council is that the voices **don't share one brain**. The easiest way to get a
genuinely cross-family council — DeepSeek arguing with Qwen arguing with Mistral — is
**[OpenRouter](https://openrouter.ai)**: one account, one API key, hundreds of models from different
labs behind one endpoint. Written for a non-developer; every command is copy-pasteable.

## What you need

- **An OpenRouter account + API key** — sign up at openrouter.ai, create a key, and set it:
  `export OPENROUTER_API_KEY=<your key>` (Windows PowerShell:
  `$env:OPENROUTER_API_KEY="<your key>"`). You pay OpenRouter per use; Elder Council itself ships
  **no keys and no models**.
- **Words used below:** a **seat** is one voice in a council; **pinning** means writing a model id
  into that seat; a **lane** is which pool of models the seats draw from (`open` here); **headless**
  means no coding agent involved — the harness itself calls the models.
- **Python 3.11+** and Elder Council installed **with the orchestrator extra**:
  ```console
  git clone https://github.com/Cyber-Elders/elder-council-harness && cd elder-council-harness
  pip install -e ".[orchestrator]"
  ```
- **Model ids:** OpenRouter ids look like `vendor/model` (e.g. `deepseek/…`, `qwen/…`,
  `mistralai/…`). **Copy the exact id from [openrouter.ai/models](https://openrouter.ai/models)** —
  ids change as models are released, so this guide deliberately ships none.
- *(Journey B only)* **OpenCode** set up as your coding agent.

## Journey A — headless: run a cross-family council with no IDE at all

`--orchestrate` makes the harness itself call your models — good for scripts, CI, scheduled audits,
or just trying a real council from a terminal.

**Step 1 — pin a different family per voice.** Open `.council/council-models.json` in your project
(run `eldercouncil install <your-agent> --council code-council` once from your project folder if it
doesn't exist yet — that materialises `.council/`) and put an OpenRouter id on the `open` lane of the
seats you care about — pick each from a **different vendor** on openrouter.ai/models:

```jsonc
"security_sme":         { "open": "<a-deepseek-id-from-openrouter>" },
"critic_challenge":     { "open": "<a-mistral-id-from-openrouter>" },
"strategic_risk_owner": { "open": "<a-qwen-or-other-id>" }
```

*(The shipped open-lane defaults are cross-family already but run on **local Ollama** models — any
seat you don't repin keeps that local default. Repin every seat you want in the cloud; for an
all-OpenRouter council, repin all of them.)*

**Step 2 — convene on the open lane:**

```console
export OPENROUTER_API_KEY=<your key>
eldercouncil convene code-council --lane open --orchestrate \
  --question "merge the auth-change diff currently on this branch"
```

You get a real verdict: each lens runs on its pinned model, the Code council's deterministic tool
lens runs **real built-in checks** (not a model — other councils don't seat a tool lens), the votes
are tallied fail-closed, dissent is preserved, and the record lands in `.council/decisions/`. `eldercouncil models check` first confirms your pins;
`eldercouncil verify` checks the audit chain after. Each lens's vote streams live as it lands, and
the full deliberations land in `.council/last-run/` — `tools/watch-council.sh` shows every voice in
its own tmux pane while the run happens.

## Journey B — inside OpenCode: a different family per lens, in your IDE

OpenCode runs **each sub-agent on its own model**, so a council can be cross-family *inside* your
coding session:

```console
eldercouncil install opencode --all --lane open
```

The shipped open lane already assigns five families (Alibaba / DeepSeek / Mistral / Google / OpenAI
lineages) via local **Ollama** tags. To route seats through **OpenRouter** instead, pin
`openrouter/<vendor>/<model>` (or the bare `vendor/model` id) on the `open` lane in
`.council/council-models.json` and re-run the install — OpenCode then calls those models with your
key. Convene the way your OpenCode session exposes the council (the installed orchestrator agent /
council agents), or headless via Journey A.

## Journey C — Cursor / GitHub Copilot (bring your own key)

Both are **advisory** agents (no hard gate), and both accept OpenRouter as a model provider in their
own settings — Cursor under *Settings → Models* (OpenAI-compatible base URL), Copilot under
*Settings → Model Providers*. Add OpenRouter there with your key, pick your models, and
`eldercouncil install cursor` / `install copilot` wires the advisory council instructions; the agent
is *asked* to convene and honour verdicts (it can decline — see [IDE-SUPPORT.md](IDE-SUPPORT.md)).

> ### Honest limit — Claude Code cannot use OpenRouter in-session
> Claude Code speaks the **Anthropic Messages API**; OpenRouter exposes the **OpenAI-style**
> `/api/v1/chat/completions` schema. Pointing `ANTHROPIC_BASE_URL` at OpenRouter does **not** work.
> If you live in Claude Code: run local models via [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)
> (one family, honestly labeled), and get cross-family scrutiny from **Journey A** alongside it —
> the two compose.

## Troubleshooting

| Symptom | Fix |
|---|---|
| A lens reports `lens unavailable (ProviderError)` | Usually the key isn't set in THIS shell (`export OPENROUTER_API_KEY=<key>`; PowerShell `$env:OPENROUTER_API_KEY="<key>"`) or the model id doesn't exist — copy the exact id from openrouter.ai/models, then `eldercouncil models check`. |
| Verdict warns about **monoculture** | Your pinned seats resolve to one vendor family — spread them across different vendors (that warning is the product working). |
| HTTP 402 / quota errors | OpenRouter account needs credit; each lens call is one model request. |

Running cross-family? **Star the repo** and [open an issue](https://github.com/Cyber-Elders/elder-council-harness/issues)
with the family pairings that argued best — real pairing reports are the most useful thing you can share.

Related: [GET-STARTED.md](GET-STARTED.md) · [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md) (which family per
seat) · [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md) (fully local instead) · [AGENT-SETUP.md](AGENT-SETUP.md)
(let your coding agent set all this up for you).
