<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Get started — install it, and actually use it

This is the plain-English, do-this-then-that guide. It assumes you're **not** a Python developer. By
the end you'll have a council installed in your coding agent and you'll know exactly what to do when it
asks you to convene one.

> **30-second taste, no setup:** if you just want to *see* a council decide before installing anything,
> jump to [the demo](#step-5--see-one-decide-first-no-keys) — it runs with no models and no keys.

## What a council is (in one breath)

Your coding agent (Claude Code, Cursor, …) usually decides things with **one** AI model. A **council**
asks **several independent perspectives** — "lenses" — to weigh a risky decision *before* it happens,
keeps the disagreement on the record, and leaves the final call to **you**. Elder Council only convenes
one when a decision is actually consequential — not for routine work.

| Word you'll see | What it means for you |
|---|---|
| **lens** | one AI perspective on the decision (e.g. a security view, a reliability view) |
| **council** | a small group of lenses convened for one kind of high-stakes decision |
| **convene** | run the council on the decision in front of you |
| **the gate** | a checkpoint that watches risky actions and *asks* you to convene the right council |
| **verdict / dissent** | the council's call, plus the lenses that disagreed (the disagreement is the valuable part) |
| **disposition** | who the final call goes to — often **you** (a named human) |
| **action-gate vs advisory** | an *action-gate* council can be auto-triggered by the gate; an *advisory* one you convene yourself |

## What you need first

1. **A coding agent already set up** — Claude Code, Cursor, OpenCode, or GitHub Copilot. Elder Council
   plugs *into* your agent; it isn't a standalone app.
2. **Python 3.11 or newer**, available in your terminal. (Check with `python3 --version`.)

> **Don't have a coding agent yet?** Set one up first — e.g. install **Claude Code** or **Cursor** and
> sign in — then come back here. If you've never used a terminal at all, pair with a developer for the
> one-time install below; using the councils afterward needs no terminal.

## Step 1 — install Elder Council

In a terminal:

```console
# alpha — not yet on PyPI, so install from source:
git clone https://github.com/Cyber-Elders/elder-council-harness && cd elder-council-harness
pip install -e .
```

This puts the `eldercouncil` command on your machine. It ships **no AI model and no API keys** — the
councils run on the model your coding agent already uses.

> **If the install command is refused:** on newer Macs/Linux, `pip` may say
> `externally-managed-environment`. Use `pipx install -e .` instead (or
> `python3 -m venv ~/.eldercouncil-env && ~/.eldercouncil-env/bin/pip install -e .`). And if a later
> step says `eldercouncil: command not found`, the command isn't on your PATH — `pipx` avoids this;
> with a venv, use its full path or activate it first.

## Step 2 — go to YOUR project, then wire the councils in

**This step matters:** `install` writes into the folder you run it from. Leave the harness download
and go to **your own project** — the folder you open in your coding agent — then install:

```console
cd /path/to/your/project
eldercouncil install claude-code --all      # or: cursor / opencode / copilot / kiro
```

*(Prefer to be asked? Run `eldercouncil init` and answer the prompts — every one has a sensible
default, so you can just press Enter.)*

## Step 3 — what just changed

`install` didn't install another app — it **wired councils into your agent's project**:
- your agent now has **council commands** it can run (e.g. `/code-council`);
- on **risky actions**, a **gate** will pause and *ask* you to convene the right council.

That's it. Nothing else to configure for the default setup (your agent's own model runs the lenses).

## Step 4 — how you actually use it

A council starts one of two ways:

**1. The gate asks you.** On a hard-block agent (Claude Code, OpenCode), when you're about to do
something risky the gate **pauses and asks you to convene**, naming whichever council best matches the
action — that can be any of the eight, advisory ones included. Run the command it names
(e.g. `/code-council`); the lenses weigh in and you see:

```
COUNCIL VERDICT: block   → route: human
dissent preserved: 3 lens(es) disagreed
DISPOSITION: human (the final call — a person decides)
```

**2. You convene it yourself.** Anytime, for any council — just tell your agent *"convene the
business-decision council on this,"* or run its command (e.g. `/business-decision`). **What "advisory"
means:** an advisory *council* (Business Decision, Threat Hunting, Eng Team…) never auto-decides — its
verdict always goes to a human, however it was convened; an advisory *agent* (Cursor, Copilot) is
*asked* to convene and honour verdicts but **can decline**. Everything is still recorded.
([Which agents enforce vs only advise →](IDE-SUPPORT.md))

Either way, you read the result and decide:

- **`block` / `human`** → don't proceed automatically; **read the dissent** (it tells you *why* lenses
  disagreed) and decide: fix it, get a second human, or accept the risk on the record.
- **`allow` / auto** → low-risk; carry on.
- The council never overrides you — **a named human owns every consequential call.**

## Step 5 — see one decide first (no keys)

You don't have to wait for the gate to try it. Run:

```console
eldercouncil convene code-council --demo --question "merge a diff with a hardcoded AWS key"
```

You'll see five lenses vote, a verdict, and the **preserved dissent** — all keyless (deterministic
sample votes). That's exactly what a real run looks like; the only difference is a real run uses *your*
agent's model on *your* decision. **Not a cyber person?** Try
`eldercouncil convene business-decision --demo` — same machinery, on a $40M business call. **A
developer?** `eldercouncil convene eng-team --demo` reviews a feature design with a dev + analyst +
QA + critic panel. (Both are **advisory** — whether the gate suggests them or you convene them, their
verdict always goes to a human.)

## Common questions

- **"After install, is it done?"** Yes — your agent has the council commands and the gate. You'll see
  it work the next time you do something risky.
- **"Do I need API keys?"** No keys for the demo. For real runs, the councils use **whatever model your
  coding agent already runs** — so if your agent works, the councils work.
- **"It said `block`. Now what?"** Read the dissenting lenses' reasons, then decide. `block` routes to a
  human (you) on purpose — it's not a dead end, it's a "look before you leap." To proceed anyway *on
  the record*, assert the approval signals — see [GATES.md](GATES.md) → "Asserting signals".
- **"It printed `approval: … asserted — unverified`. Is that a problem?"** No — it means you asserted
  an approver and the harness recorded it without confirming it (nothing is configured to check). To
  have it actually checked against your ticket system, see [GATES.md](GATES.md).
- **"Where do the decisions go — and can I tell if the log was tampered with?"** Every decision is
  written to `.council/decisions/` and chained in a tamper-evident log. Run **`eldercouncil verify`** to
  check it's intact (it re-hashes each full record, so a changed vote/reason is caught) and to print the
  chain **head** — record that head somewhere off the machine and re-run `eldercouncil verify
  --expect-head <hash>` to also catch a wholesale rewrite. It's tamper-**evident**, not tamper-proof —
  see [THREAT_MODEL.md](../THREAT_MODEL.md).
- **"Which model setup should I pick?"**

  | You want | Pick | Trade-off |
  |---|---|---|
  | Private & simplest | [Ollama local](CLAUDE-CODE-OLLAMA.md) | one model family (monoculture — the CLI will say so) |
  | Real cross-vendor argument, one paid key | [OpenRouter](OPENROUTER.md) | prompts go to a hosted service |
  | Free cross-vendor, all local | open lane + OpenCode ([MODEL-GUIDANCE.md](MODEL-GUIDANCE.md)) | needs ~24 GB+ RAM and OpenCode |
- **"Can I run it on my own local models (Ollama, etc.)?"** Yes — [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)
  is a copy-paste, fully-local recipe; [OPENROUTER.md](OPENROUTER.md) gets you a genuinely
  **cross-family** council with one API key; [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md) is the
  which-model-per-seat reference.
- **"Can my coding agent just set this up for me?"** Yes — paste it the one-line prompt at the top of
  [AGENT-SETUP.md](AGENT-SETUP.md); it asks you a few plain questions, installs, customises, and
  reports back.

## Worked? Two things help a lot

If a council caught something — or even just made the dissent visible — **star the repo**, and **open an
issue** with the kind of decision you'd want a council for. Hit a snag in install? File it — rough edges
there are exactly what we want to hear.

Next: [the councils](COUNCILS.md) · [per-agent install detail](IDE-SUPPORT.md) ·
[choosing models](MODEL-GUIDANCE.md) · [the honest edges](../THREAT_MODEL.md).
