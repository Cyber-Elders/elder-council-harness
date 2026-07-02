# SPDX-License-Identifier: Apache-2.0
"""Shared detectors — the secret/PII patterns + redaction used by gates, audit,
and the deterministic tool lens. Secret-shaped fixtures are ASSEMBLED AT RUNTIME
so no literal credential pattern exists in the repo (the CI secret-scan greps
this file too)."""

from eldercouncil import detectors

FAKE_SK = "sk-" + "A" * 24                 # OpenAI-style key shape
FAKE_AKIA = "AKIA" + "0" * 14              # AWS access key shape
FAKE_SLACK = "xoxb-" + "1" * 12


def test_secret_patterns_detect_common_shapes():
    for s in (FAKE_SK, FAKE_AKIA, FAKE_SLACK, "api_key = hunter2secret"):
        assert detectors.SECRET_RE.search(s), s


def test_redact_masks_whole_secret():
    out = detectors.redact(f"merge a diff containing {FAKE_SK} into main")
    assert FAKE_SK not in out
    assert "[REDACTED:secret]" in out
    # no fragment of the key survives
    assert "A" * 10 not in out


def test_redact_masks_pii():
    out = detectors.redact("customer email alice@example.com and card 4111 1111 1111 1111")
    assert "alice@example.com" not in out
    assert "[REDACTED:pii]" in out


def test_redact_leaves_clean_text_alone():
    clean = "merge the refactor of the parser module"
    assert detectors.redact(clean) == clean
    assert detectors.redact("") == ""
    assert detectors.redact(None) is None  # non-string passthrough


def test_gates_reuse_shared_patterns():
    # gates must see the SAME patterns (one definition, no drift)
    from eldercouncil import gates
    assert gates._SECRET_RE is detectors.SECRET_RE
    assert gates._PII_RE is detectors.PII_RE
    assert gates._INJECTION_RE is detectors.INJECTION_RE
