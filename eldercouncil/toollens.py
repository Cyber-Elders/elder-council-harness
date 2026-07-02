# SPDX-License-Identifier: Apache-2.0
"""
Deterministic tool lens — REAL checks, never a prompted model.

The council's tool lens exists so a CRITICAL finding can come from an
authoritative scanner rather than an injectable reasoning lens. In the
`--orchestrate` path this module IS that lens: it runs

  * the built-in detectors (secret / prompt-injection / PII regexes shared with
    the control gates) over the decision text (the convene question), and
  * any operator-configured `[tools]` commands from `.council/config.toml`
    (e.g. `secret_scan_cmd = "gitleaks detect --no-banner -s ."`) — executed
    with `shlex` argument parsing (never a shell), a hard timeout, and a
    fail-safe: an unavailable or timed-out tool ABSTAINS, it does not vote.

Honest scope: a clean scan is reported as an ABSTENTION, not approval — a regex
or scanner finding nothing is not evidence the change is merge-worthy. Votes
from this module carry `provenance: "tool"`; the consensus rationale labels
them as deterministic findings.
"""

from __future__ import annotations

import shlex
import subprocess

from . import detectors
from .config import tool_commands
from .consensus import restrictiveness

_TIMEOUT = 120  # seconds per configured command


def _builtin_findings(text: str) -> list[tuple[str, str]]:
    """(severity, message) findings from the shared deterministic detectors."""
    found = []
    if detectors.SECRET_RE.search(text or ""):
        found.append(("CRITICAL", "secret-scan (built-in): credential-shaped value detected"))
    if detectors.INJECTION_RE.search(text or ""):
        found.append(("HIGH", "injection-scan (built-in): prompt-injection pattern detected"))
    if detectors.PII_RE.search(text or ""):
        found.append(("HIGH", "pii-scan (built-in): personal-data pattern detected"))
    return found


def _run_command(name: str, cmd: str) -> tuple[str, str] | None:
    """Run one configured check. Returns a (severity, message) finding, None when
    clean, or raises ToolUnavailable for anything that prevents a real answer."""
    argv = shlex.split(cmd)
    if not argv:
        raise ValueError("empty command")
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT)
    if proc.returncode == 0:
        return None  # scanner convention: exit 0 = no findings
    tail = ((proc.stdout or "") + (proc.stderr or "")).strip()[-160:]
    return ("HIGH", f"{name}: exit {proc.returncode} — {tail or 'findings reported'}")


def run_tool_lens(role_name: str, question: str, outcomes: list[str]) -> dict:
    """Produce the tool lens's vote from REAL deterministic checks.

    Findings -> the council's most restrictive outcome (severity = worst
    finding). No findings -> abstain (honest: absence of findings is not
    approval). Tool unavailable/timeout -> abstain, fail-safe, reason says so.
    """
    findings = _builtin_findings(question)
    unavailable: list[str] = []
    for name, cmd in tool_commands().items():
        try:
            f = _run_command(name, cmd)
            if f:
                findings.append(f)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as exc:
            unavailable.append(f"{name} unavailable ({type(exc).__name__})")

    if findings:
        severity = "CRITICAL" if any(s == "CRITICAL" for s, _ in findings) else "HIGH"
        verdict = max(outcomes, key=restrictiveness) if outcomes else "block"
        return {"role": role_name, "model": "tool", "vote": verdict, "confidence": 0.9,
                "severity": severity, "provenance": "tool",
                "reason": "; ".join(m for _, m in findings)[:200]}
    if unavailable:
        return {"role": role_name, "model": "tool", "vote": "abstain", "confidence": 0.0,
                "provenance": "tool",
                "reason": ("; ".join(unavailable) + " — abstaining (fail-safe)")[:200]}
    return {"role": role_name, "model": "tool", "vote": "abstain", "confidence": 0.5,
            "provenance": "tool",
            "reason": "deterministic checks found nothing — a clean scan is not evidence of "
                      "merge-worthiness; the reasoning lenses decide"}
