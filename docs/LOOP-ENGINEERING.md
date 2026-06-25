<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The decision loop — engineering plural scrutiny into the agent loop

> How Elder Council fits the way agentic systems actually run: as a **loop**. This is the conceptual
> bridge between "convene a council" and "a coding agent doing work, turn after turn." For the *why*
> read [CONCEPT.md](CONCEPT.md); for the code path read [ARCHITECTURE.md](ARCHITECTURE.md).

## Agentic systems run in a loop

An autonomous agent does not make one decision and stop. It runs an **engineering loop**: it observes
state, reasons about a next step, takes an action (edit a file, run a command, call a tool, answer a
question), observes the result, and goes round again. A long task is hundreds of these turns. The loop
is what makes agents useful — and it is also what makes a single model's weakness dangerous.

In a one-shot chatbot, a bad answer is **local**: one user, one weak reply. Inside a loop, the *same*
model decides every turn, so a blind spot is not a one-off — it is **repeated at machine speed**,
turn after turn, and its effects compound: a wrong assumption early becomes the ground truth the later
turns build on. The faster and more autonomous the loop, the less chance a human has to catch the turn
that mattered. This is the loop-level shape of the systemic, common-mode risk described in
[CONCEPT.md](CONCEPT.md).

The same shape applies **beyond a coding agent's tool loop**. An organisation that routes every
consequential call — a market move, a vendor choice, a bet-the-business commitment — through one model
embeds a single point of judgement in its *decision* loop just as surely. The risk gate and selective
plurality apply identically; only the lenses change (see [DOMAIN-ADAPTATION.md](DOMAIN-ADAPTATION.md)
and the executive [Business Decision council](COUNCILS.md#7-business-decision-council--business-decision--advisory)).

## Two failure pressures the loop creates

- **Compounding** — an error in turn *N* is carried, unquestioned, into turns *N+1 … N+k*. Self-review
  by the same model rarely catches it: the reviewer shares the blind spot of the author.
- **Velocity vs. oversight** — most turns are routine and should run at full speed; a few are
  consequential and irreversible. A loop that pauses for a human on *every* turn is unusable; a loop
  that pauses on *none* is unaccountable. The hard part is telling the two apart, automatically.

## How the council uses the loop

Elder Council does not replace the agent's loop and does not slow the routine turns. It is a **governance
overlay on the loop** that engages only on the turns that matter:

1. **Every turn passes the risk gate first.** A pre-tool gate scores the proposed action
   (impact × likelihood, 1–25). Below the convene threshold — the overwhelming majority of turns — the
   loop proceeds solo or with a deterministic tool; no council, no friction. A **moderate** turn
   (default 5–9) gets a lightweight **two-lens dual review**; only a **consequential** turn (10–15)
   fans out to the full council, and the highest-impact turns (16–25) add a named human. This is
   **selective plurality** applied per turn.
2. **A consequential turn convenes a council.** When a turn crosses the threshold, the loop pauses and
   fans out to **independent lenses** that reason *before* synthesis — breaking the compounding cycle,
   because the scrutiny comes from perspectives (and ideally models) that do **not** share the author's
   blind spot.
3. **A deterministic inner loop resolves it.** The non-deterministic deliberation is wrapped in a tight,
   pure loop: **gate → convene → consensus tally → control gates → disposition → hash-chained audit**.
   That inner loop is fully deterministic and offline — same votes + same council ⇒ same decision —
   so the only non-deterministic step (the model lenses) is isolated and testable.
4. **The outer loop resumes — with the decision on the record.** The verdict, the route (auto /
   developer / a named human), and the **preserved dissent** are written to a tamper-evident log before
   the agent's loop continues. The turn that mattered is now accountable; the rest never slowed down.

```
        the agent's engineering loop (fast, autonomous)
   observe ─▶ reason ─▶ [propose action] ─▶ act ─▶ observe ─▶ …
                              │
                       risk gate (1–25)
                       │              │
                  below thr.      at/above thr.
                       │              │
                   proceed     ┌──────▼───────────────────────────┐
                  (no council) │  convene → consensus → gates →    │  ← deterministic
                               │  disposition → audit (dissent)    │     inner loop
                               └──────┬───────────────────────────┘
                                      ▼
                          auto · developer · human  →  loop resumes
```

*The diagram collapses the convene side for clarity. The gate actually routes by band: **1–4** solo ·
**5–9** dual review (2 lenses) · **10–15** full council · **16–25** council + a named human.*

## Why this is "engineering," not ceremony

The loop framing is what keeps councils practical rather than bureaucratic:

- **Convene rarely.** Plurality is spent only where a single agent's baseline confidence is low or the
  cost of being wrong is high; on easy turns a second opinion is noise (see [FAQ.md](FAQ.md)).
- **Determinism where it counts.** Everything that decides *how* votes combine is pure and offline, so
  the governance layer is reproducible and unit-tested even though the lenses are not.
- **Accountability without a bottleneck.** Routine velocity is preserved; only the consequential turns
  carry the cost of human ownership and an audit entry.

## Honest limits

The loop overlay does not make the agent correct — it makes the consequential turns **scrutinised and
recorded**. Councils can be wrong; a council whose lenses share one base model shares one blind spot
(diversify — `eldercouncil models check` warns you); the audit is **tamper-evident, not tamper-proof**;
and the gate is a router, not an adjudicator — it is bypassable by obfuscation (see
[THREAT_MODEL.md](../THREAT_MODEL.md)). The goal is not a guaranteed decision. It is to stop the one
turn that mattered from depending on one unchallenged model.
