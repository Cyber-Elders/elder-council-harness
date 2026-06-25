<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Worked examples

A narrated, end-to-end council run — the machine record and the human ledger side by side.

## `code-council/` — a push that should be blocked

A developer asks to push a diff that hardcodes an AWS key and builds a SQL query by string
concatenation on user input.

- **[decision.json](code-council/decision.json)** — the machine-readable decision record exactly as
  `eldercouncil` writes it to `.council/decisions/`: every lens's vote, the verdict, the route, and
  the preserved dissent. Reproduce it with:

  ```console
  eldercouncil convene code-council --demo --json \
    --question "Review before push: adds a hardcoded AWS key in config.py and builds a SQL query by string concatenation on a user-supplied id."
  ```

- **[ledger.md](code-council/ledger.md)** — the human-readable twin (the
  [council decision record template](../templates/council-decision-record.md) filled in).

The verdict is **block → human**: a lens rated the finding CRITICAL, so per the Code council's
fail-closed rule the push is withheld pending human security review — and the three lenses that wanted
to merge or only request changes are **kept on the record as dissent**, not averaged away.

*(These use `--demo` deterministic sample votes so they reproduce keylessly. A real run uses your own
models via your coding agent.)*
