<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Verdict-quality eval (tier A)

Almost every test in this repo checks the **machinery** (fail-closed routing, audit
binding, redaction) or the **structure** (the right council convened). None ask the
product's actual thesis question: **does convening a council catch what one vote
alone would wave through?**

This eval answers a precise, deterministic slice of that — with **no model in the
loop and no LLM-judge circularity**.

## What it measures (and what it does NOT)

- **Grader:** `Outcome.permits_action()` — the shipped boolean for "did the action
  proceed automatically." No LLM grades anything.
- **Labels:** construct-known. Each `should_stop` fixture has a **planted defect**
  (a hardcoded secret, a missing authz check, a malicious install hook…); each
  `should_proceed` fixture is authored clean. "Correct" is defined purely by route:
  a `should_stop` is *caught* iff the council did **not** auto-permit it; a
  `should_proceed` is a *false block* iff the council withheld a clean action.
- **Baseline:** each reasoning lens deciding **alone** (a single model has no
  deterministic tool lens, so the tool vote is excluded from the baseline).

**This is consensus-MACHINERY lift on a named fixture set.** It is **not** evidence
that diverse *models* beat one model — that is the non-deterministic **tier B**
(`eval/run.py --real`, local Ollama, out of CI), which is **not built here**. Every
number is scoped to `eval/fixtures/`, nothing wider.

## Why it isn't rigged

The `should_proceed` fixtures are the safeguard: a should-stop-only set could
manufacture lift. Because a single cautious lens routes the whole council to a human
(`blocking_dissent -> human`), the council's **false-block rate can exceed** a single
model's on clean cases — so the metric can show the council **over-escalating**. It
is not tilted in the council's favour.

## Run it

```console
python eval/run.py          # prints the table, writes eval/_results/lift.json
```

`tests/test_eval.py` runs the same computation as a **deterministic regression
guard**: it pins that the machinery catches every planted defect, keeps catch-lift
≥ 0 over the fixture set, and does not over-block the clean cases. A change that
weakened the consensus rules would drop those numbers and fail CI.

## What today's fixture set shows

On the bundled fixtures the council auto-permits **none** of the planted defects,
while the average single lens catches only a minority; and the council over-blocks
**none** of the clean cases. The honest reading is narrow: *the shipped consensus
rules turn a vote-set into a more cautious decision than trusting one vote, on this
set* — **not** *"councils make better decisions."*
