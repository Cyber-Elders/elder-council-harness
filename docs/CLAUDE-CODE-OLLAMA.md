<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Run councils on your own local models — Claude Code + Ollama

A copy-paste recipe to run Elder Council on local models on **your own machine**: Claude Code driving
models served by **[Ollama](https://ollama.com)** — no cloud model calls and no API keys. With the
local lane below, **the council's model traffic stays on your machine** (keep every lens local and
avoid `:cloud` models and network tools for a genuinely closed setup). Written for a non-developer;
every command is copy-pasteable.

> **Why this works:** Ollama can speak Claude Code's API locally, and Elder Council's `--lane local`
> makes every council voice run on *your* model. The steps below are from
> [Ollama's own docs](https://docs.ollama.com/integrations/claude-code).

## Step 1 — install Ollama and pull a model

Install Ollama (ollama.com/download). On macOS and Windows it runs as a desktop app and **serves
automatically** at `http://localhost:11434`. Then pull a model and confirm its exact tag:

```console
ollama pull qwen3                 # any current tool-capable model; pick one that fits your RAM
ollama list                       # note the EXACT name:tag (e.g. qwen3:latest) — you'll need it
```

Use a model with **tool-calling** support and a decent context window (set **64k+** for real repos).
For which models suit which lens and what fits 16 / 24 / 48 GB of RAM, see
[MODEL-GUIDANCE.md](MODEL-GUIDANCE.md).

## Step 2 — point Claude Code at Ollama

**Easiest (Ollama's launcher)** — pulls the model if needed, sets the wiring, and opens Claude Code on
your local model:

```console
ollama launch claude --model qwen3
```

**Or do it manually** (Ollama's documented environment block — note `ANTHROPIC_BASE_URL` is the bare
host:port, *no* `/v1`):

```console
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_AUTH_TOKEN=ollama     # required, but Ollama doesn't check the value
export ANTHROPIC_API_KEY=""            # clear it so the auth-token path is used
claude --model qwen3
```

You're now running Claude Code on a local model — your prompts go to your local Ollama, not a cloud
provider.

## Step 3 — install Elder Council on the **local lane**

This is the one important flag. `--lane local` makes **every council voice run on your model** — there's
**no model file to edit and no Claude tag to alias**. *(A "lane" is just which pool of models the lenses
draw from; `local` means your own.)*

```console
git clone https://github.com/Cyber-Elders/elder-council-harness && cd elder-council-harness
pip install -e .
eldercouncil install claude-code --all --lane local
```

*(Why the flag matters: a normal install pins the lenses to hosted Claude models, which your local
Ollama doesn't have — they'd error. `--lane local` makes every lens **inherit** (reuse) your
Claude-Code-on-Ollama model instead.)*

> **One trade-off to know before you trust a unanimous verdict:** running every lens on one local model
> is a **monoculture** — the voices share that model's blind spots. See
> [the honest note below](#honest-note--one-model-means-one-set-of-blind-spots).

## Step 4 — use it

In your Claude-Code-on-Ollama session, when the gate asks you to convene (or any time), run the council:

```
/code-council
```

Every lens runs on your local model; you get the verdict and the preserved dissent, all on-device. (New
to the verdict/dissent output? See [GET-STARTED.md](GET-STARTED.md).)

## Honest note — one model means one set of blind spots

Running all the lenses on your **single** local model is a **monoculture**: the voices share that
model's blind spots, so they can be confidently wrong *together* — the very thing a council exists to
prevent. It still helps (the deterministic **Tool lens** runs real scans, and **you** make the final
call — both independent of the model), but you get the most value when the voices can genuinely
disagree. To add a truly different voice, run a council on a **second** local model, or pin one lens to
a hosted/cross-family model (see [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md)). `eldercouncil models check`
will flag a single-model setup.

## Troubleshooting (from Ollama's docs)

| Symptom | Fix |
|---|---|
| **`model "…" not found` / 404** | The tag must match `ollama list` *exactly*, including the `:tag`. Pass that exact value to `--model`. |
| Background tasks 404 on a Claude name | If you *didn't* use `--lane local`, Ollama can't find the pinned Claude tags — either re-install with `--lane local`, or alias them per Ollama's docs: `ollama cp qwen3 claude-opus-4-8` (repeat for each). `--lane local` avoids this entirely. |
| First run hangs / times out | Large models are slow to cold-load — pre-warm once: `ollama run qwen3 "hi"`, then launch. |
| Lenses give poor/garbled answers | Use a stronger tool-capable model and raise the context window (64k+). |

> **Feature limits (Ollama's Anthropic shim):** tool-calling, streaming, system prompts, vision, and
> extended thinking work; `tool_choice`, prompt caching, token-counting, and PDFs do not — none of
> which Elder Council needs.

Running fully local? **Star the repo** and tell us which models you paired ([open an issue](https://github.com/Cyber-Elders/elder-council-harness/issues)) —
local model pairings are among the most useful things you can share.

Related: [GET-STARTED.md](GET-STARTED.md) · [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md) (local/hybrid model
choices) · [IDE-SUPPORT.md](IDE-SUPPORT.md).
