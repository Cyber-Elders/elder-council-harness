# SPDX-License-Identifier: Apache-2.0
"""
Human-approval provenance — verify or honestly label the asserted approver.

`human_approver` / `approval_basis` are SIGNALS the host asserts; the harness
cannot authenticate a person by itself. This module makes that honest and
optionally verifiable:

  * no `[signals] approval_verify_command` configured -> the assertion passes
    through unchanged but is RECORDED as "asserted — unverified".
  * command configured -> it runs (shlex argv, never a shell, 10s timeout) with
    `ELDERCOUNCIL_APPROVER` / `ELDERCOUNCIL_BASIS` in the environment (e.g. a
    script that checks a ticket system or an approvals API). Non-zero exit,
    timeout, or error STRIPS the approval signals before the gates run — the
    gates then escalate exactly as if no approval existed (fail-closed).

This runs in the engine (not in `gates`, which stays pure/offline/deterministic).
Authentication of the person remains the operator's job; see THREAT_MODEL.md.
"""

from __future__ import annotations

import os
import shlex
import subprocess

from .config import approval_verify_command

_TIMEOUT = 10  # seconds

VERIFIED = "verified"
UNVERIFIED = "asserted — unverified (no approval_verify_command configured)"
FAILED = "verification FAILED — assertion stripped; gates treat approval as absent (fail-closed)"


def check_approval(signals: dict) -> tuple[dict, dict]:
    """Return (signals_for_gates, approval_record).

    The record is empty when no approval was asserted. On verification failure
    the returned signals are a COPY with the approval keys removed."""
    approver = signals.get("human_approver")
    if not approver:
        return signals, {}
    basis = str(signals.get("approval_basis", ""))
    cmd = approval_verify_command()
    if not cmd:
        return signals, {"approver": str(approver), "basis": basis, "status": UNVERIFIED}
    try:
        argv = shlex.split(cmd)
        if not argv:
            raise ValueError("empty approval_verify_command")
        env = dict(os.environ, ELDERCOUNCIL_APPROVER=str(approver), ELDERCOUNCIL_BASIS=basis)
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT, env=env)
        ok = proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        ok = False
    if ok:
        return signals, {"approver": str(approver), "basis": basis, "status": VERIFIED}
    stripped = {k: v for k, v in signals.items() if k not in ("human_approver", "approval_basis")}
    return stripped, {"approver": str(approver), "basis": basis, "status": FAILED}
