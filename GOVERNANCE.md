# Governance

## Stewardship

Elder Council Harness is maintained by **ZenBlue Pty Ltd t/a Cyber Elders**. It currently runs on a lightweight
"benevolent maintainer" model: a single accountable maintainer reviews and merges, and we actively
seek co-maintainers as the project grows.

## Decision-making

- **Routine changes** (bug fixes, new tests, doc improvements, a new council definition that fits the
  schema and honesty rules) — normal PR review by a maintainer.
- **Load-bearing changes** (the risk gate, the consensus tally, the audit chain, the council schema,
  the model registry, the standards map, the threat model, the CI gates) — require maintainer review
  per [CODEOWNERS](CODEOWNERS) and a short rationale in the PR. These are the files the tool's
  guarantees rest on.
- **Breaking changes** (CLI surface, council schema, decision-record format) — a brief RFC in an issue
  first, so adopters can weigh in.

## Non-negotiables

These are not up for casual change; altering them is a deliberate, reviewed decision:

- Honesty over hype (the honest ceiling; the CI honesty gate).
- The deterministic core stays pure, offline, and reproducible.
- Bring-your-own-LLM — the project ships no keys, no bundled model, no telemetry.
- A named human owns every critical and risk-acceptance decision.
- No internal/private references in the public repo.

## Releases

Versioned per [CHANGELOG.md](CHANGELOG.md) (single source of truth: `pyproject.toml`). A release is
cut only when CI is green, including the clean-install UAT and the agentic UAT.

## Contact

General: open an issue. Security: [SECURITY.md](SECURITY.md) (private advisory). Conduct:
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
