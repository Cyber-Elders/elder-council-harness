<!-- Thanks for contributing to Elder Council Harness. -->

## What & why

<!-- What does this change and why? Link any issue. -->

## Type

- [ ] Bug fix
- [ ] New / changed council definition (data only)
- [ ] Feature
- [ ] Docs
- [ ] Refactor / chore

## Checklist

- [ ] `python -m pytest tests/ -q` passes
- [ ] New behaviour has tests
- [ ] **Honesty kept** — no overclaims (compliant/certified/guaranteed/AI-powered/tamper-proof/blocks attacks/covers all 10/best decision); `python tools/honesty_check.py` is clean
- [ ] **No internal references** — no private hosts/IPs/paths/person names/project codenames (the leak guard + secret-scan pass)
- [ ] The deterministic core stayed pure (no model/network/clock/randomness in risk_gate/consensus/audit/schema/catalog/models)
- [ ] If a fail-safe changed or a bypass was found: `THREAT_MODEL.md` + `tests/test_known_bypasses.py` updated
- [ ] SPDX header on new source files; commits signed off (`git commit -s`)

## Standards impact

<!-- Does this change what STANDARDS-MAP.md or THREAT_MODEL.md should say? -->
