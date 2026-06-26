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


def parse_vote(text: str, outcomes: list[str]) -> tuple[str, float, str]:
    """Extract (vote, confidence, reason) from a lens reply.

    Only an EXPLICIT `Vote: <outcome>` line counts. If the reply has no clean,
    unambiguous vote, return 'abstain' — never guess (a guessed vote silently
    corrupts the tally; an abstain is counted honestly as "lens did not decide").
    """
    low = (text or "").lower()
    vote = "abstain"
    m = re.search(r"vote\s*[:\-]\s*([a-z][a-z0-9 \-]*)", low)
    if m:
        token = m.group(1).strip().split("\n")[0].strip()
        # exact-match an outcome first; only then a unique containment match
        exact = [o for o in outcomes if token == o.lower()]
        contained = [o for o in outcomes if o.lower() in token or token in o.lower()]
        if exact:
            vote = exact[0]
        elif len(contained) == 1:
            vote = contained[0]
        # ambiguous / unrecognised -> stays 'abstain'
    conf = 0.5
    cm = re.search(r"confidence\s*[:\-]\s*(low|medium|high)", low)
    if cm:
        conf = _CONF[cm.group(1)]
    rm = re.search(r"position\s*[:\-]\s*(.+)", text or "", re.IGNORECASE)
    reason = (rm.group(1).strip().split("\n")[0][:200] if rm else (text or "").strip()[:200])
    return vote, conf, reason
