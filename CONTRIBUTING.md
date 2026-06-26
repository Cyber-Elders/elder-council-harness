# Contributing to Elder Council Harness

Thank you for considering a contribution. Elder Council is a governance tool, so it holds itself to
the standards it advocates: honesty, determinism, and a clear trust boundary.

## Non-negotiables (enforced in CI)

1. **Honesty over hype.** No "compliant / certified / guaranteed / AI-powered / tamper-proof / blocks
   attacks / covers all 10 / best decision" claims. The honest caveats (councils can be wrong, not
   legal advice, tamper-evident not tamper-proof, ships no keys, selective plurality, continuity)
   must stay present. The `honesty` CI job enforces both lists.
2. **The deterministic core stays pure.** `risk_gate`, `consensus`, `audit`, `schema`, `catalog`,
   `models`, and `convene.build_review` must not call a model, the network, the clock (beyond the
   audit timestamp), or randomness. Same inputs → same decision record + decision id.
3. **Bring-your-own-LLM — ship no keys.** No API keys, no bundled model, no telemetry. Providers read
   credentials from the environment only (and only in the optional `[orchestrator]` extra).
4. **Councils are data.** Add or change a council by editing/adding a YAML file in
   `eldercouncil/councils/` (validated against `council.schema.json`). No per-council code branches in
   the renderer or engine.
5. **No internal references.** No private hostnames, IPs, paths, person names, or internal project
   codenames anywhere in the repo. The `test_no_internal_private_references` and `secret-scan` guards
   enforce this; do not weaken them.
6. **New limits are documented.** If you change a fail-safe or discover a bypass, update
   `THREAT_MODEL.md` and `tests/test_known_bypasses.py` deliberately.

## Development

```console
python -m venv .venv && . .venv/bin/activate    # Python 3.11+
pip install -e ".[mcp,dev]"
python -m pytest tests/ -q
```

Run the honesty + leak guards locally before opening a PR: `python -m pytest tests/test_docs.py -q`.

## Pull requests

- Sign your commits (DCO): `git commit -s`.
- Keep changes focused; add or update tests for new behaviour.
- New SPDX header on every new source file (`Apache-2.0` for code, `CC-BY-4.0` for docs).
- Fill in the PR checklist (tests pass, honesty kept, threat model updated if limits changed, no
  internal references).

## Reporting security issues

Please use a private advisory — see [SECURITY.md](SECURITY.md). Do not open a public issue for a
vulnerability.
