<!-- SPDX-License-Identifier: Apache-2.0 -->
# Agentic UAT

The end-to-end truth test: drive each council through an agent and assert the **agentic loop actually
fired** — gate → convene → consensus → audit. Run by `.github/workflows/agentic-uat.yml` (dispatch +
nightly), and locally:

```console
python uat/agentic/run.py --scenario all --ide claude-code --mode mock
```

## Layout

```
uat/agentic/
├── run.py            # orchestrator: scaffold project → install → drive → assert
├── assertions.py     # structural invariants over .council/decisions/ (NOT exact text)
├── scenarios/<c>/    # scenario.json per council: question + expected invariants
└── drivers/          # headless agent drivers (claude_code, opencode) for --mode real
```

## Modes

- **`mock` (default, keyless, CI-safe):** the council is convened via `eldercouncil convene --demo`
  (deterministic sample votes). Exercises the real install → convene → audit → assert loop without a
  model or a key. This is what keeps the workflow green by default.
- **`real`:** a headless coding agent (Claude Code / OpenCode) drives the scenario in a project where
  `eldercouncil install` wired the council — the genuine end-to-end path. Needs the agent CLI on PATH
  and a CI-scoped key in `UAT_LLM_API_KEY`. Used **only** in this UAT — the shipped package still
  ships no keys. Falls back to `mock` when the agent/key is unavailable.

## Invariants (flake-tolerant)

LLM output is non-deterministic, so a scenario passes on **structure**, not text: the correct council
convened, a decision record exists with that council id, the verdict is in the expected *class*, the
route matches (auto / lead_dev / human), and dissent was preserved. The scenarios double as **agentic
regression** — a broken IDE adapter or a changed pre-tool contract is exactly what the nightly run
catches.
