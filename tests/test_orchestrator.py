# SPDX-License-Identifier: Apache-2.0
"""Orchestrator vote parsing — garbled/ambiguous replies abstain (never guess) —
and provider routing (an explicit ollama/ pin must never reach OpenRouter)."""

from eldercouncil.orchestrator.client import parse_vote
from eldercouncil.orchestrator.providers import (AnthropicClient, OllamaClient,
                                                 OpenRouterClient, select_client)

OUTCOMES = ["mitigate", "transfer", "avoid", "monitor", "accept"]  # cyber-risk (accept last)


# --- provider routing ---------------------------------------------------------

def test_ollama_prefix_routes_to_ollama_never_openrouter(monkeypatch):
    # Regression: the generic "/" rule used to grab ollama/<tag> first, and the
    # default chain used to send explicit ollama pins to Anthropic when keyed.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "present")
    assert isinstance(select_client("ollama/qwen3:32b"), OllamaClient)
    assert isinstance(select_client("ollama/gpt-oss:120b-cloud"), OllamaClient)


def test_openrouter_slug_and_prefix_route_to_openrouter():
    assert isinstance(select_client("deepseek/deepseek-r1"), OpenRouterClient)
    assert isinstance(select_client("openrouter/qwen/qwen3-32b"), OpenRouterClient)


def test_claude_and_inherit_routing(monkeypatch):
    assert isinstance(select_client("claude-opus-4-8"), AnthropicClient)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(select_client("inherit"), OllamaClient)   # keyless default
    monkeypatch.setenv("ANTHROPIC_API_KEY", "present")
    assert isinstance(select_client("inherit"), AnthropicClient)
    assert isinstance(select_client("gemma3:12b"), OllamaClient)  # bare local tag


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


# --- hardening: ordinary model output shapes must not silently abstain ---------

def test_markdown_bolded_vote_parses():
    vote, conf, _ = parse_vote("**Vote:** mitigate\n**Confidence:** High", OUTCOMES)
    assert vote == "mitigate" and conf == 0.9


def test_my_vote_is_phrase_parses():
    vote, _, _ = parse_vote("Analysis done. My vote is mitigate.", OUTCOMES)
    assert vote == "mitigate"
    vote, _, _ = parse_vote("vote is monitor", OUTCOMES)
    assert vote == "monitor"


def test_numeric_and_percent_confidence():
    _, conf, _ = parse_vote("Vote: mitigate\nConfidence: 0.8", OUTCOMES)
    assert conf == 0.8
    _, conf, _ = parse_vote("Vote: mitigate\nConfidence: 85%", OUTCOMES)
    assert abs(conf - 0.85) < 1e-9
    _, conf, _ = parse_vote("Vote: mitigate\nConfidence: 7", OUTCOMES)  # >1 -> /100
    assert abs(conf - 0.07) < 1e-9


def test_spaced_multiword_outcome_matches_hyphenated_id():
    # "approve with controls" must resolve to approve-with-controls, NEVER to the
    # more permissive bare "approve".
    outcomes = ["approve", "approve-with-controls", "reject"]
    vote, _, _ = parse_vote("Vote: approve with controls", outcomes)
    assert vote == "approve-with-controls"


def test_ambiguous_containment_resolves_restrictively():
    # A token containing several outcomes resolves to the MOST RESTRICTIVE one —
    # parsing ambiguity must never widen permission.
    outcomes = ["merge", "block"]
    vote, _, _ = parse_vote("Vote: block then merge", outcomes)
    assert vote == "block"


def test_hf_co_namespace_routes_to_ollama_not_openrouter(monkeypatch):
    # hf.co/... is Ollama's HuggingFace pull namespace — routing it through the
    # generic "/" rule would send the deliberation PROMPT to OpenRouter.
    monkeypatch.setenv("OPENROUTER_API_KEY", "present")
    assert isinstance(select_client("hf.co/TheBloke/some-model-GGUF"), OllamaClient)
    assert isinstance(select_client("huggingface.co/org/model"), OllamaClient)
