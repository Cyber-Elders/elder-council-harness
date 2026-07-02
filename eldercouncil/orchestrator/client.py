# SPDX-License-Identifier: Apache-2.0
"""
LLM client protocol + a deterministic vote parser.

A client maps (model, system, prompt) -> raw text. Providers live in
providers.py. Parsing the structured deliberation reply into a vote is shared
and pure, so it is unit-testable without any network.
"""

from __future__ import annotations

import re
from typing import Protocol


class LLMClient(Protocol):
    name: str

    def query(self, model: str, system: str, prompt: str) -> str:
        ...


_CONF = {"low": 0.3, "medium": 0.6, "high": 0.9}

# Markdown emphasis models routinely add around the protocol lines (**Vote:** …).
_EMPHASIS = re.compile(r"[*_`]+")


def _norm(token: str) -> str:
    """Case/space/hyphen-insensitive form so `approve with controls` matches the
    outcome id `approve-with-controls`."""
    return re.sub(r"[\s\-]+", "-", token.strip().lower())


def parse_vote(text: str, outcomes: list[str]) -> tuple[str, float, str]:
    """Extract (vote, confidence, reason) from a lens reply.

    Only an EXPLICIT vote declaration counts (`Vote: <outcome>` or
    `my vote is <outcome>`). If the reply has no clean vote, return 'abstain' —
    never guess (a guessed vote silently corrupts the tally; an abstain is
    counted honestly as "lens did not decide"). When a declared token matches
    MORE than one outcome, resolve to the MOST RESTRICTIVE candidate — parsing
    ambiguity must never widen permission ("approve with controls" may not
    collapse to "approve").
    """
    low = _EMPHASIS.sub("", (text or "").lower())   # strip **bold** / _em_ / `code`
    vote = "abstain"
    m = (re.search(r"vote\s*[:\-]\s*([a-z][a-z0-9 \-]*)", low)
         or re.search(r"(?:my\s+)?vote\s+is\s+([a-z][a-z0-9 \-]*)", low))
    if m:
        token = _norm(m.group(1).split("\n")[0])
        by_norm = {_norm(o): o for o in outcomes}
        if token in by_norm:
            vote = by_norm[token]
        else:
            contained = [o for o in outcomes
                         if _norm(o) in token or token in _norm(o)]
            if contained:
                from ..consensus import restrictiveness
                vote = max(contained, key=restrictiveness)
        # unrecognised -> stays 'abstain'
    conf = 0.5
    cm = re.search(r"confidence\s*[:\-]\s*(low|medium|high|\d+(?:\.\d+)?\s*%?)", low)
    if cm:
        raw = cm.group(1).strip()
        if raw in _CONF:
            conf = _CONF[raw]
        else:
            num = float(raw.rstrip("%").strip())
            if raw.endswith("%") or num > 1:
                num /= 100.0
            conf = max(0.0, min(1.0, num))
    rm = re.search(r"position\s*[:\-]\s*(.+)", text or "", re.IGNORECASE)
    reason = (rm.group(1).strip().split("\n")[0][:200] if rm else (text or "").strip()[:200])
    return vote, conf, reason
