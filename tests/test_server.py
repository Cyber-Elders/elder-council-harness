# SPDX-License-Identifier: Apache-2.0
"""MCP server — import + the advisory tool surface (skipped without [mcp])."""

import json

import pytest

pytest.importorskip("mcp", reason="MCP server needs the [mcp] extra")


def test_server_imports_and_exposes_tools():
    from eldercouncil import server
    assert server.mcp is not None
    # the four advisory tools exist as module functions
    for name in ("risk_gate", "convene_council", "audit_log", "audit_summary"):
        assert hasattr(server, name)


def test_audit_log_records_gate_report_and_disposition(council_dir):
    from eldercouncil import server
    verdicts = [
        {"role": "Software Engineering SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "AppSec SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "Reliability / Operations SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "Critic / Challenge", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
    ]
    result = server.audit_log(council="code-council", question="approve trivial doc fix", verdicts=verdicts)
    assert result["disposition"] == "auto"
    assert result["gate_report"]["result"] == "allow"
    assert result["verdict"] == "merge"
    # decision file includes gate evaluation
    decisions = list(council_dir.glob("decisions/*.json"))
    assert decisions
    rec = json.loads(decisions[0].read_text(encoding="utf-8"))
    assert rec["gate_report"]["result"] == "allow"
    assert rec["disposition"] == "auto"
    assert rec["profile"] == "standard"


def test_audit_log_detects_off_council_roles(council_dir):
    from eldercouncil import server
    verdicts = [
        {"role": "Software Engineering SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "AppSec SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "Reliability / Operations SME", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "Critic / Challenge", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "Mysterious Stranger", "model": "demo", "vote": "block", "confidence": 0.9, "reason": "x"},
    ]
    result = server.audit_log(council="code-council", question="x", verdicts=verdicts)
    assert result["off_council_roles"] == ["Mysterious Stranger"]


def test_audit_log_flags_host_reported_only_without_tool_role(council_dir):
    from eldercouncil import server
    verdicts = [
        {"role": "SME A", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
        {"role": "SME B", "model": "demo", "vote": "merge", "confidence": 0.8, "reason": "ok"},
    ]
    result = server.audit_log(council="business-decision", question="pick a color", verdicts=verdicts)
    decisions = list(council_dir.glob("decisions/*.json"))
    rec = json.loads(decisions[0].read_text(encoding="utf-8"))
    assert rec["context"].get("host_reported_only") is True
