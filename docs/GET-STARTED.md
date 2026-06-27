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

## Step 2 — wire the councils into your agent

```console
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

**1. The gate asks you.** On a hard-block agent (Claude Code, OpenCode) when you're about to do
something risky that an **action-gate** council covers (like **Code** — pushing, deploying, adding a
dependency, changing auth), the gate **pauses and asks you to convene**. Run the command it names
(e.g. `/code-council`); the lenses weigh in and you see:

```
COUNCIL VERDICT: block   → route: human
dissent preserved: 3 lens(es) disagreed
DISPOSITION: human (the final call — a person decides)
```

**2. You convene it yourself.** Advisory councils (like **Business Decision** or **Threat Hunting**) —
and any council on an advisory agent (Cursor, Copilot) — are *not* popped up by the gate; you start
them deliberately. Just tell your agent *"convene the business-decision council on this,"* or run its
command (e.g. `/business-decision`). On an advisory agent the agent is *asked* to convene and honour
the verdict but **can decline** — everything is still recorded.
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
`eldercouncil convene business-decision --demo` — same machinery, on a $40M business call. (Business
Decision is **advisory** — you convene it yourself; the gate won't pop it up for you.)

## Common questions

- **"After install, is it done?"** Yes — your agent has the council commands and the gate. You'll see
  it work the next time you do something risky.
- **"Do I need API keys?"** No keys for the demo. For real runs, the councils use **whatever model your
  coding agent already runs** — so if your agent works, the councils work.
- **"It said `block`. Now what?"** Read the dissenting lenses' reasons, then decide. `block` routes to a
  human (you) on purpose — it's not a dead end, it's a "look before you leap."
- **"Can I run it on my own local models (Ollama, etc.)?"** Yes — [CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)
  is a copy-paste, fully-local recipe; [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md) covers mixing models
  (cross-family / hybrid).

## Worked? Two things help a lot

If a council caught something — or even just made the dissent visible — **star the repo**, and **open an
issue** with the kind of decision you'd want a council for. Hit a snag in install? File it — rough edges
there are exactly what we want to hear.

Next: [the councils](COUNCILS.md) · [per-agent install detail](IDE-SUPPORT.md) ·
[choosing models](MODEL-GUIDANCE.md) · [the honest edges](../THREAT_MODEL.md).
