# SPDX-License-Identifier: Apache-2.0
"""MCP server — import + the advisory tool surface (skipped without [mcp])."""

import pytest

pytest.importorskip("mcp", reason="MCP server needs the [mcp] extra")


def test_server_imports_and_exposes_tools():
    from eldercouncil import server
    assert server.mcp is not None
    # the four advisory tools exist as module functions
    for name in ("risk_gate", "convene_council", "audit_log", "audit_summary"):
        assert hasattr(server, name)
