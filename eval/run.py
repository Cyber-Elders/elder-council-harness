# SPDX-License-Identifier: Apache-2.0
"""
Verdict-quality eval (tier A) — does the consensus MACHINERY turn a vote-set into
a better *decision* than trusting one vote?

Deterministic, keyless, no model in the loop, and no LLM-judge circularity: the
grader is `Outcome.permits_action()` and the labels are construct-known (we planted
the defect in each `should_stop` fixture and authored each `should_proceed` clean
case). The single-model baseline = each reasoning lens deciding ALONE; the council
decision = the shipped `consensus.tally` over the whole vote-set.

SCOPE (read eval/README.md): this measures consensus-machinery lift on a NAMED
fixture set. It does NOT prove "diverse models beat one model" — that is the
non-deterministic tier B (`--real`, local-Ollama, out of CI), not built here. The
clean `should_proceed` fixtures keep it honest: they test that the council does not
over-block, and a council can still over-escalate on a single cautious lens by
design (fail-closed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

_HERE = Path(__file__).resolve().parent
_FIXTURE_DIR = _HERE / "fixtures"
sys.path.insert(0, str(_HERE.parent))  # repo root — import eldercouncil without an install

from eldercouncil.catalog import get_council  # noqa: E402
from eldercouncil.consensus import tally  # noqa: E402


def load_fixtures() -> list:
    fx: list = []
    for f in sorted(_FIXTURE_DIR.glob("*.json")):
        fx.extend(json.loads(f.read_text(encoding="utf-8")))
    return fx


def _bind_votes(council, specs):
    """Bind per-position vote specs to the council's REAL roles, marking the tool
    role so the deterministic-tool-lens semantics apply. Returns [(vote_dict, is_tool)]."""
    roles = list(council.roles)
    if len(specs) != len(roles):
        raise ValueError(f"{council.id}: fixture has {len(specs)} votes but council has {len(roles)} roles")
    bound = []
    for role, s in zip(roles, specs):
        is_tool = bool(getattr(role, "is_tool", False))
        v = {"role": role.name, "model": "tool" if is_tool else "m",
             "vote": s["vote"], "confidence": s.get("confidence", 0.7)}
        if s.get("severity"):
            v["severity"] = s["severity"]
        if is_tool:
            v["provenance"] = "tool"
        bound.append((v, is_tool))
    return bound


def _single_stub(council, role_name):
    """A one-lens council in the SAME mode — models 'you asked one model'."""
    return SimpleNamespace(mode=council.mode,
                           roles=[SimpleNamespace(name=role_name, arbitrator=False, is_tool=False)],
                           decision_outcomes=list(council.decision_outcomes), id="single")


def _grade(fx):
    """Return (council_permits, [single_lens_permits...]) — the single-model baseline
    excludes the deterministic tool lens (a single model has no such lens)."""
    council = get_council(fx["council"])
    bound = _bind_votes(council, fx["votes"])
    council_permits = tally([v for v, _ in bound], council).permits_action()
    single = [tally([v], _single_stub(council, v["role"])).permits_action()
              for v, is_tool in bound if not is_tool]
    return council_permits, single


def _mean(xs) -> float:
    xs = list(xs)
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def compute_metrics(fixtures=None) -> dict:
    fixtures = fixtures if fixtures is not None else load_fixtures()
    council_catch, single_catch, stop_detail = [], [], []
    council_fb, single_fb, proceed_detail = [], [], []
    for fx in fixtures:
        cp, single = _grade(fx)
        if fx["label"] == "should_stop":
            council_catch.append(0 if cp else 1)                       # catch = did NOT auto-permit a defect
            per_lens = [0 if s else 1 for s in single]
            single_catch.extend(per_lens)
            stop_detail.append({"id": fx["id"], "council_caught": (not cp),
                                "single_catch_rate": _mean(per_lens)})
        elif fx["label"] == "should_proceed":
            council_fb.append(0 if cp else 1)                          # false block = did NOT permit a clean case
            per_lens = [0 if s else 1 for s in single]
            single_fb.extend(per_lens)
            proceed_detail.append({"id": fx["id"], "council_false_block": (not cp),
                                   "single_false_block_rate": _mean(per_lens)})
        else:
            raise ValueError(f"fixture {fx['id']}: unknown label {fx['label']!r}")
    ccr, scr = _mean(council_catch), _mean(single_catch)
    return {
        "n_should_stop": len(council_catch),
        "n_should_proceed": len(council_fb),
        "council_catch_rate": ccr,
        "mean_single_catch_rate": scr,
        "catch_lift": round(ccr - scr, 4),
        "council_false_block_rate": _mean(council_fb),
        "mean_single_false_block_rate": _mean(single_fb),
        "stop_detail": stop_detail,
        "proceed_detail": proceed_detail,
    }


def main() -> int:
    m = compute_metrics()
    print("Verdict-quality eval (tier A) — consensus-machinery lift on the bundled fixture set")
    print(f"  fixtures: {m['n_should_stop']} should_stop, {m['n_should_proceed']} should_proceed\n")
    print(f"  catch-rate    council {m['council_catch_rate']:.2f}  vs  mean single-lens "
          f"{m['mean_single_catch_rate']:.2f}   (lift +{m['catch_lift']:.2f})")
    print(f"  false-block   council {m['council_false_block_rate']:.2f}  vs  mean single-lens "
          f"{m['mean_single_false_block_rate']:.2f}")
    print("\n  NOTE: consensus-MACHINERY lift over a NAMED fixture set — NOT a claim that diverse")
    print("        models beat one model (that is the non-deterministic tier B, not run here). The")
    print("        clean should_proceed fixtures test that the council does not over-block; a council")
    print("        can still over-escalate on one cautious lens by design (fail-closed).")
    out = _HERE / "_results"
    out.mkdir(exist_ok=True)
    (out / "lift.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"\n  wrote {out / 'lift.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
