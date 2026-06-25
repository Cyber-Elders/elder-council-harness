# SPDX-License-Identifier: Apache-2.0
"""Known limitations, pinned as tests so they stay documented and honest.

These assert that the documented residual risks in THREAT_MODEL.md hold. They
are NOT failures to fix silently — they are the honest boundary of the tool. If
one of these starts behaving differently, update THREAT_MODEL.md deliberately.
"""

from eldercouncil import risk_gate as rg
from eldercouncil.consensus import tally
from conftest import mkcouncil, votes


def test_risk_gate_is_keyword_based_and_bypassable_by_obfuscation():
    # Honest limit: the heuristic gate keys on visible tokens. A base64-encoded
    # destructive payload (the decoded bytes are "rm -rf /") has no visible
    # destructive keyword, so it scores low. The gate routes; it does not
    # adjudicate. (The string below is inert test data — nothing is executed.)
    plain = rg.compute_risk_score("rm -rf /")
    obfuscated = rg.compute_risk_score("decode_and_run('cm0gLXJmIC8=')")
    assert plain >= 5
    assert obfuscated < plain  # the encoded form evades the keyword heuristic


def test_council_quality_is_only_as_good_as_its_votes():
    # Honest limit: if every lens is wrong-but-confident, the tally faithfully
    # reflects that. The harness governs the *process*, not the lenses' judgement.
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)),
              mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block")))
    assert o.verdict == "merge" and o.permits_action()


def test_advisory_verdict_is_a_recommendation_not_enforcement():
    # Honest limit: advisory councils (and advisory IDEs) never enforce — they
    # route to a human. The verdict is decision support, not a hard block.
    o = tally(votes(("recommend", 0.9), ("recommend", 0.9), ("recommend", 0.9)),
              mkcouncil(mode="advisory", n_roles=3, outcomes=("recommend", "defer")))
    assert o.route == "human" and not o.permits_action()
