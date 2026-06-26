# SPDX-License-Identifier: Apache-2.0
"""Shared test fixtures + helpers."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest


def mkcouncil(mode="action-gate", n_roles=5, outcomes=("merge", "block", "escalate"), arbitrator_at=None):
    """A duck-typed council stub for testing consensus.tally in isolation."""
    roles = []
    for i in range(n_roles):
        roles.append(SimpleNamespace(name=f"role{i}", arbitrator=(i == arbitrator_at), is_tool=False))
    return SimpleNamespace(mode=mode, roles=roles, decision_outcomes=list(outcomes), id="stub")


def votes(*specs):
    """specs: (vote, confidence) or (vote, confidence, role)."""
    out = []
    for i, s in enumerate(specs):
        vote = s[0]
        conf = s[1] if len(s) > 1 else 0.7
        role = s[2] if len(s) > 2 else f"role{i}"
        out.append({"role": role, "model": "test", "vote": vote, "confidence": conf, "reason": ""})
    return out


@pytest.fixture
def council_dir(tmp_path, monkeypatch):
    """Point .council/ at a temp dir for audit/install tests."""
    d = tmp_path / ".council"
    monkeypatch.setenv("COUNCIL_DIR", str(d))
    return d
