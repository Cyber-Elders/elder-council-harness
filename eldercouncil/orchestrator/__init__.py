# SPDX-License-Identifier: Apache-2.0
"""
Optional BYO-LLM orchestrator ([orchestrator] extra).

The default product is IDE-native and keyless: the host agent runs the council.
This optional runner lets you convene a council HEADLESS (CI, scheduled audits,
MCP) using YOUR OWN model access. It ships NO keys — every provider reads its
credential from the environment (ANTHROPIC_API_KEY, OPENROUTER_API_KEY,
OLLAMA_HOST). If a role's model is "inherit"/unpinned, the runner falls back to
the configured default provider.

Import lazily so the deterministic core never depends on this extra.
"""

from __future__ import annotations


def get_runner():
    try:
        from .runner import run_council
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "the orchestrator needs the [orchestrator] extra: pip install 'eldercouncil[orchestrator]'"
        ) from exc
    return run_council
