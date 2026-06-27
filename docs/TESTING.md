<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Testing

Council votes are non-deterministic (they come from LLM lenses). The strategy keeps every primitive
pure and tests the engine with **mocked votes**, so the decision path is verified without a model or
the network. Three tiers.

## Tier 1 — Deterministic regression (every PR, in-repo, keyless)

`pytest tests/` — **126 tests across the files below**, all keyless. Runs on Ubuntu ×
Python 3.11/3.12/3.13, and (gated to main) on macOS + Windows.

| File | Covers |
|---|---|
| `test_risk_gate.py` | 1–25 scoring, clamps, route boundaries, escalation-not-default |
| `test_consensus.py` | every minimum-governance rule (ties/quorum/escalation/empty/human-reserved/low-confidence/word-confidence/CRITICAL/abstain) + per-council outcomes |
| `test_gates.py` | the 11 control gates, profiles, the offensive-misuse hard stop, fail-closed defaults, and a **gate blocking even when the council approved** |
| `test_orchestrator.py` | BYO-LLM vote parsing — garbled/ambiguous replies abstain (never guess) |
| `test_audit.py` | hash chain, mid-entry tamper detected, **full rewrite NOT detected** (tamper-evident-not-proof), stale-head recovery, concurrency, determinism |
| `test_councils.py` | all seven councils validate; malformed council fails closed |
| `test_registry.py` | role resolution, only-verified-real defaults, unpinned sentinels flagged, fail-loud on unknown role |
| `test_install.py` | per-IDE × per-council render, idempotency, re-pin changes only the model line, fail-safes |
| `test_engine.py` | mocked-vote fan-out → tally → audit; same votes+council → identical record |
| `test_journeys.py` | real `python -m eldercouncil.cli` journeys + the **cp1252 Windows-console** regression |
| `test_docs.py` | doc-as-test + the internal-leak guard + the no-fabricated-model-tags guard |
| `test_server.py` | the advisory MCP tool surface (skipped without `[mcp]`) |
| `test_known_bypasses.py` | the documented residual limits, pinned so they stay honest |

## Tier 2 — Clean-install UAT (dispatch, per OS, keyless)

`.github/workflows/uat.yml`: build the wheel → install it into a **fresh venv** (not editable) → run a
real `eldercouncil` CLI journey on Ubuntu / macOS / Windows (version → list → show → install → convene
`--demo` → verify). This catches packaging, entry-point, and encoding bugs the editable-install
regression cannot see.

## Tier 3 — Full agentic UAT + agentic regression (dispatch + nightly)

`.github/workflows/agentic-uat.yml`: a **real headless coding agent** (Claude Code / OpenCode) runs in
an ephemeral sandbox, `eldercouncil install`s a council, and is driven through a scripted high-stakes
action. We assert the **agentic loop actually fires** — gate → convene → consensus → audit — per
council, via structural **invariants** (the right council convened; a decision record with the right
id; the correct verdict *class*; the action gated for action-gate councils; dissent captured). LLM
output is non-deterministic, so we assert invariants, not exact text, and retry before flagging.

Per-council scenarios live in `uat/agentic/scenarios/<council>/` (fixture + driver prompt + expected
invariants); `uat/agentic/assertions.py` checks them over `.council/decisions/`. The agent's model
comes from a **CI-scoped secret** or a local Ollama — used only in this workflow; **the package still
ships no keys**. The scenarios re-run nightly as **agentic regression**: a broken IDE adapter or a
changed pre-tool contract is exactly the class clean-install UAT cannot catch.

## Sandboxes

| Use | Tool |
|---|---|
| Canonical cross-OS CI/UAT (release gate) | GitHub Actions |
| Isolated execution for action-gate councils that trigger real tools; keyless local-Ollama runs | `.devcontainer/` + Daytona cloud microVM (`docs/testing/`) |
| Local Windows cp1252 / path pre-flight before spending Windows CI minutes | Windows Sandbox (`tools/win-sandbox/eldercouncil.wsb`) |

## Honesty & determinism gates (in `ci.yml`)

- **offline-determinism** — the same mocked votes + council produce a byte-identical decision record.
- **honesty** — forbids overclaims (compliant/certified/guaranteed/AI-powered/tamper-proof/…) and the
  stale OWASP agentic taxonomy; requires the honest caveats (councils-can-be-wrong, not-legal-advice,
  tamper-evident-not-tamper-proof, ships-no-keys, selective plurality, continuity). Scans docs **and**
  the bundled councils/templates/lenses.
- **secret-scan** — gitleaks over the tree.
- **build** — the wheel bundles the councils, lens roster, registry, and schema.
- **self-audit** — `pip-audit` on our own dependency tree.
