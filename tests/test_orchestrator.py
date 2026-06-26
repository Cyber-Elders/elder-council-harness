# SPDX-License-Identifier: Apache-2.0
"""Orchestrator vote parsing — garbled/ambiguous replies abstain (never guess)."""

from eldercouncil.orchestrator.client import parse_vote

OUTCOMES = ["mitigate", "transfer", "avoid", "monitor", "accept"]  # cyber-risk (accept last)


def test_explicit_vote_line_is_parsed():
    vote, conf, _ = parse_vote("Position: patch now.\nVote: mitigate\nConfidence: High", OUTCOMES)
    assert vote == "mitigate" and conf == 0.9


def test_garbled_reply_abstains_never_defaults_to_accept():
    # Regression: a reply with no clean vote must NOT fall through to the last
    # outcome (which for cyber-risk is the high-stakes 'accept').
    for reply in ("I'm not sure what to do here.", "", "It depends on many factors."):
        vote, _, _ = parse_vote(reply, OUTCOMES)
        assert vote == "abstain", reply


def test_ambiguous_multi_outcome_reply_abstains():
    vote, _, _ = parse_vote("We could mitigate or transfer or just monitor.", OUTCOMES)
    assert vote == "abstain"


def test_negation_is_not_misread_as_a_vote():
    # "this is not a block" must not be parsed as block (it has no Vote: line).
    vote, _, _ = parse_vote("This is definitely not a block, the code is fine.", ["merge", "block"])
    assert vote == "abstain"
