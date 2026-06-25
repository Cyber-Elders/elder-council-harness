# SPDX-License-Identifier: Apache-2.0
"""
Real OpenCode driver (agentic-UAT 'real' mode).

Drives the scenario through a headless `opencode run` in the project where
`eldercouncil install opencode` has wired the council orchestrator + the
pre-tool plugin. Requires the `opencode` CLI on PATH and UAT_LLM_API_KEY.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import require


def drive(spec: dict, project: Path, env: dict) -> None:
    require("opencode")
    prompt = (
        f"@{spec['council']}-orchestrator Convene the {spec['council']} council on this decision and "
        f"record the result via the audit_log MCP tool:\n\n{spec['question']}"
    )
    subprocess.run(
        ["opencode", "run", prompt],
        cwd=str(project), env={**env}, timeout=600, capture_output=True, text=True,
    )
