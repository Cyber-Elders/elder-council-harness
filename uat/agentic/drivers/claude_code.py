# SPDX-License-Identifier: Apache-2.0
"""
Real Claude Code driver (agentic-UAT 'real' mode).

Drives the scenario through a headless `claude` run in the project where
`eldercouncil install claude-code` has wired the council. The agent hits the
pre-tool gate, runs the `/<council>` slash command, the lenses deliberate, and
the decision is recorded to `.council/` — the genuine end-to-end loop.

Requires the `claude` CLI on PATH and UAT_LLM_API_KEY. Raises DriverUnavailable
otherwise (run.py then falls back to the keyless mock driver).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import require


def drive(spec: dict, project: Path, env: dict) -> None:
    require("claude")
    prompt = (
        f"Convene the {spec['council']} council on this decision and record the result via the "
        f"audit_log MCP tool:\n\n{spec['question']}"
    )
    # Headless, non-interactive run, scoped to the project with the council installed.
    subprocess.run(
        ["claude", "-p", prompt, "--permission-mode", "acceptEdits"],
        cwd=str(project), env={**env}, timeout=600, capture_output=True, text=True,
    )
