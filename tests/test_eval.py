# SPDX-License-Identifier: Apache-2.0
"""Verdict-quality eval — a DETERMINISTIC regression guard on the consensus rules.

Grades `Outcome.permits_action()` over fixed vote-records (no model, no network),
so it is CI-safe. It pins that the shipped consensus machinery (1) catches every
planted defect in the should_stop fixtures, (2) does so at least as often as a
single lens deciding alone (lift >= 0), and (3) does not over-block the clean
should_proceed fixtures. A change that weakened e.g. `blocking_dissent -> human`
would drop the measured catch-rate and fail here. This is NOT a claim about real
models — see eval/README.md."""

import importlib.util
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval" / "run.py"


def _load_eval():
    spec = importlib.util.spec_from_file_location("ec_eval_run", _EVAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_eval_fixture_set_has_both_labels():
    # BOTH labels must be present — a should_stop-only set cannot measure false-block
    # and would be rigged in the council's favour. The clean set is what keeps it honest.
    fx = _load_eval().load_fixtures()
    labels = {f["label"] for f in fx}
    assert labels == {"should_stop", "should_proceed"}, labels
    assert sum(f["label"] == "should_stop" for f in fx) >= 5
    assert sum(f["label"] == "should_proceed" for f in fx) >= 3


def test_consensus_machinery_catches_every_planted_defect():
    m = _load_eval().compute_metrics()
    assert m["council_catch_rate"] == 1.0, m["stop_detail"]   # auto-permits NONE of the planted defects


def test_council_catch_lift_over_single_lens_is_nonnegative():
    m = _load_eval().compute_metrics()
    # Deterministic lift bound: the shipped rules do at least as well as one lens on this set.
    assert m["council_catch_rate"] >= m["mean_single_catch_rate"]
    assert m["catch_lift"] >= 0.0


def test_council_does_not_over_block_clean_cases():
    m = _load_eval().compute_metrics()
    assert m["council_false_block_rate"] == 0.0, m["proceed_detail"]
    assert m["council_false_block_rate"] <= m["mean_single_false_block_rate"] + 1e-9
