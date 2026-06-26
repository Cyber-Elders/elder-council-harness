# SPDX-License-Identifier: Apache-2.0
"""
Headless council runner — the [orchestrator] vote source.

Runs a council's deliberation tasks concurrently against the user's OWN models
(via providers.py), parses each reply into a vote, and returns the votes for the
deterministic `consensus.tally`. A per-lens failure becomes a conservative
abstention (recorded), never a crash — fail-closed all the way through.

Ships no keys. Heavy import (asyncio/providers) stays out of the core.
"""

from __future__ import annotations

import asyncio

from .client import parse_vote
from .providers import ProviderError, select_client


def _run_one(task: dict, outcomes: list[str]) -> dict:
    model = task.get("model", "inherit")
    try:
        client = select_client(model)
        system = "You are an independent council lens. Be concise, structured, and decisive."
        text = client.query(model if model != "inherit" else "", system, task["prompt"])
        vote, conf, reason = parse_vote(text, outcomes)
        return {"role": task["role"], "model": client.name + ":" + (model or "inherit"),
                "vote": vote, "confidence": conf, "reason": reason}
    except Exception as exc:  # noqa: BLE001 — any failure -> honest 'unavailable', not a fake block
        # An outage must be distinguishable from a deliberated block: the tally
        # treats 'unavailable' as a non-vote (and returns 'inconclusive' if too
        # many lenses are unreachable), never a council verdict.
        return {"role": task["role"], "model": model, "vote": "unavailable",
                "confidence": 0.0, "reason": f"lens unavailable ({type(exc).__name__})"}


async def _gather(review: dict) -> list[dict]:
    outcomes = review.get("decision_outcomes", [])
    loop = asyncio.get_event_loop()
    return await asyncio.gather(*[
        loop.run_in_executor(None, _run_one, t, outcomes) for t in review["tasks"]
    ])


def run_council(review: dict) -> list[dict]:
    """Synchronous entry point used as engine.convene's vote_source."""
    return asyncio.run(_gather(review))
