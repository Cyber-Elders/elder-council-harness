# SPDX-License-Identifier: Apache-2.0
"""
Shared deterministic detectors — secret / PII / prompt-injection regexes and
the redaction helper built on them.

One home for the patterns so the control gates (`gates`), the audit trail
(`audit`) and the deterministic tool lens (`toollens`) all see the SAME
definitions — a finding the gates can flag is a finding the audit will not
persist and the tool lens will report.

Honest scope: these are conservative, blatant-case regexes — a detector that
finds nothing is NOT evidence the text is clean. Pure, offline, stdlib-only.
"""

from __future__ import annotations

import re

SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{12,}|ASIA[0-9A-Z]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gho_[A-Za-z0-9]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,}"
    r"|(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*\S+", re.IGNORECASE)

PII_RE = re.compile(
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b|\b\d{13}\b|\b(?:\d[ -]?){15,16}\b"
    r"|passport\s*(?:no|number)|id\s*number", re.IGNORECASE)

INJECTION_RE = re.compile(
    r"ignore (?:all )?(?:the )?previous instructions|disregard (?:the )?(?:above|prior)"
    r"|you are now|new instructions:|reveal your (?:system )?(?:prompt|instructions)"
    r"|exfiltrate|send .* to https?://", re.IGNORECASE)


def redact(text: str) -> str:
    """Mask secret and PII matches in `text` for safe persistence.

    Secrets first (a credential often contains digit runs the PII pattern would
    also match); each match is replaced whole, so no fragment of the original
    value survives. Non-string input is returned unchanged.
    """
    if not isinstance(text, str) or not text:
        return text
    out = SECRET_RE.sub("[REDACTED:secret]", text)
    out = PII_RE.sub("[REDACTED:pii]", out)
    return out
