# SPDX-License-Identifier: Apache-2.0
"""
Headless council runner — the [orchestrator] vote source.

Runs a council's deliberation tasks concurrently against the user's OWN models
(via providers.py), parses each reply into a vote, and returns the votes for the
deterministic `consensus.tally`. A per-lens failure becomes a conservative
abstention (recorded), never a crash — fail-closed all the way through.

Realtime visibility: each lens's FULL deliberation (redacted like every other
persisted artifact) is written to `.council/last-run/<role>.md` as it completes,
and an optional `progress` callback fires per vote — so the CLI can stream
per-lens status live, and `tools/watch-council.sh` can show every voice
deliberating in its own tmux pane while the harness still tallies and audits.

Ships no keys. Heavy import (asyncio/providers) stays out of the core.
"""

from __future__ import annotations

import asyncio
import contextlib
import re

from .. import detectors, paths
from ..config import load_config
from ..toollens import run_tool_lens
from .client import parse_vote
from .providers import ProviderError, select_client


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "lens").lower()).strip("-")


def _transcript_dir():
    return paths.council_dir() / "last-run"


def _write_transcript(vote: dict, raw: str | None) -> None:
    """Persist one lens's full deliberation (best-effort — a transcript failure
    must never affect the run). Redacted under the same [audit] rule as every
    other persisted artifact; `.council/` is git-ignored user data."""
    with contextlib.suppress(Exception):
        d = _transcript_dir()
        d.mkdir(parents=True, exist_ok=True)
        body = raw if raw is not None else vote.get("reason", "")
        if load_config().redact:
            body = detectors.redact(body)
        sev = f" [{vote['severity']}]" if vote.get("severity") else ""
        (d / f"{_slug(vote.get('role', ''))}.md").write_text(
            f"# {vote.get('role', '?')}\n"
            f"model: {vote.get('model', '?')}\n"
            f"vote: {vote.get('vote', '?')}{sev} (confidence {vote.get('confidence', '?')})\n\n"
            f"{body}\n",
            encoding="utf-8")


def _reset_transcripts(review: dict) -> None:
    with contextlib.suppress(Exception):
        d = _transcript_dir()
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.md"):
            old.unlink()
        for t in review.get("tasks", []):
            (d / f"{_slug(t.get('role', ''))}.md").write_text(
                f"# {t.get('role', '?')}\n\n⋯ deliberating\n", encoding="utf-8")


def _run_one(task: dict, outcomes: list[str], question: str = "") -> dict:
    if task.get("is_tool"):
        # The deterministic tool lens runs REAL checks (built-in detectors +
        # configured [tools] commands) — it is never sent to a model. This is
        # what makes its CRITICAL an authoritative finding rather than one more
        # injectable opinion.
        vote = run_tool_lens(task["role"], question, outcomes)
        _write_transcript(vote, None)
        return vote
    model = task.get("model", "inherit")
    try:
        client = select_client(model)
        system = "You are an independent council lens. Be concise, structured, and decisive."
        text = client.query(model if model != "inherit" else "", system, task["prompt"])
        vote, conf, reason = parse_vote(text, outcomes)
        v = {"role": task["role"], "model": client.name + ":" + (model or "inherit"),
             "vote": vote, "confidence": conf, "reason": reason}
        _write_transcript(v, text)
        return v
    except Exception as exc:  # noqa: BLE001 — any failure -> honest 'unavailable', not a fake block
        # An outage must be distinguishable from a deliberated block: the tally
        # treats 'unavailable' as a non-vote (and returns 'inconclusive' if too
        # many lenses are unreachable), never a council verdict.
        v = {"role": task["role"], "model": model, "vote": "unavailable",
             "confidence": 0.0, "reason": f"lens unavailable ({type(exc).__name__})"}
        _write_transcript(v, None)
        return v


async def _gather(review: dict, progress=None) -> list[dict]:
    outcomes = review.get("decision_outcomes", [])
    question = review.get("question", "")
    loop = asyncio.get_running_loop()

    async def one(task: dict) -> dict:
        vote = await loop.run_in_executor(None, _run_one, task, outcomes, question)
        if progress is not None:
            with contextlib.suppress(Exception):
                progress(vote)   # a display failure must never affect the votes
        return vote

    return await asyncio.gather(*[one(t) for t in review["tasks"]])


def run_council(review: dict, progress=None) -> list[dict]:
    """Synchronous entry point used as engine.convene's vote_source.

    `progress(vote)` (optional) fires as each lens completes, in completion
    order; the returned list keeps task order for the deterministic tally."""
    _reset_transcripts(review)
    return asyncio.run(_gather(review, progress))
