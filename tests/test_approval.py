# SPDX-License-Identifier: Apache-2.0
"""Approval provenance — verified, honestly-unverified, or stripped (fail-closed)."""

import sys

from eldercouncil import approval


def test_no_assertion_no_record():
    signals, rec = approval.check_approval({"rollback_plan": True})
    assert rec == {} and signals == {"rollback_plan": True}


def test_unverified_assertion_is_labeled_and_passes_through(monkeypatch):
    monkeypatch.setattr(approval, "approval_verify_command", lambda: None)
    signals, rec = approval.check_approval({"human_approver": "jane", "approval_basis": "CAB-42"})
    assert signals.get("human_approver") == "jane"          # passes through (current behavior)
    assert rec["status"] == approval.UNVERIFIED             # ...but is labeled honestly
    assert rec["approver"] == "jane" and rec["basis"] == "CAB-42"


def test_verified_when_command_exits_zero(monkeypatch):
    monkeypatch.setattr(approval, "approval_verify_command",
                        lambda: f'"{sys.executable}" -c "import os,sys; sys.exit(0 if os.environ.get(\'ELDERCOUNCIL_APPROVER\')==\'jane\' else 1)"')
    signals, rec = approval.check_approval({"human_approver": "jane"})
    assert rec["status"] == approval.VERIFIED
    assert signals.get("human_approver") == "jane"


def test_failed_verification_strips_the_assertion_fail_closed(monkeypatch):
    monkeypatch.setattr(approval, "approval_verify_command",
                        lambda: f'"{sys.executable}" -c "import sys; sys.exit(1)"')
    signals, rec = approval.check_approval({"human_approver": "mallory", "approval_basis": "?",
                                            "rollback_plan": True})
    assert "human_approver" not in signals and "approval_basis" not in signals
    assert signals.get("rollback_plan") is True             # other signals untouched
    assert "FAILED" in rec["status"] and "fail-closed" in rec["status"]


def test_missing_verifier_binary_fails_closed(monkeypatch):
    monkeypatch.setattr(approval, "approval_verify_command",
                        lambda: "no-such-approval-verifier-xyz --check")
    signals, rec = approval.check_approval({"human_approver": "jane"})
    assert "human_approver" not in signals and "FAILED" in rec["status"]


def test_whitespace_verifier_command_fails_closed(monkeypatch):
    monkeypatch.setattr(approval, "approval_verify_command", lambda: "   ")
    signals, rec = approval.check_approval({"human_approver": "jane"})
    assert "human_approver" not in signals and "FAILED" in rec["status"]
