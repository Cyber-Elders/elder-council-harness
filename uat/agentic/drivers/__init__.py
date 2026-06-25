# SPDX-License-Identifier: Apache-2.0
"""
Headless agent drivers for the 'real' agentic-UAT mode.

A driver runs a scenario through a real coding agent (Claude Code / OpenCode)
in the project, so the council convenes via the agent's OWN runtime (the genuine
end-to-end path). It needs a CI-scoped LLM key (UAT_LLM_API_KEY) and the agent
CLI on PATH. When either is missing, the driver raises and run.py falls back to
the keyless 'mock' driver.

This is the extension point for live-agent verification. The mock path already
exercises the full install -> convene -> audit -> assert loop deterministically.
"""

from __future__ import annotations

import importlib
import os
import shutil


class DriverUnavailable(RuntimeError):
    pass


def load_driver(ide: str):
    mod = importlib.import_module(f"drivers.{ide.replace('-', '_')}")
    return mod


def require(cli_name: str) -> None:
    if not os.environ.get("UAT_LLM_API_KEY"):
        raise DriverUnavailable("UAT_LLM_API_KEY not set")
    if not shutil.which(cli_name):
        raise DriverUnavailable(f"{cli_name} CLI not found on PATH")
