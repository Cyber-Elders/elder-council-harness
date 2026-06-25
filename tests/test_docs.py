# SPDX-License-Identifier: Apache-2.0
"""
Doc-as-test + the anti-leak / honesty / no-fabricated-tags guards.

These are the safety net for a public, marketing-grade repo: documentation can't
drift from the CLI, no internal/private reference leaks in, no fabricated model
tag ships, and the honest caveats stay present.
"""

import re
from pathlib import Path

from eldercouncil import catalog, engine, models
from eldercouncil.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
_SELF = Path(__file__).name
_SCAN_EXT = {".md", ".py", ".toml", ".yaml", ".yml", ".json", ".js", ".mdc", ".txt"}
# Extensionless config/legal files that still ship publicly — scanned by name so a
# leak in .gitignore / CODEOWNERS / NOTICE can't slip past the suffix filter.
_SCAN_NAMES = {".gitignore", ".dockerignore", "CODEOWNERS", "LICENSE", "LICENSE-DOCS", "NOTICE", "Dockerfile"}
_EXCLUDE = {".venv", ".uatenv", ".git", "dist", "build", "__pycache__", ".council",
            ".scratch", ".scratch_ref", "_results", ".pytest_cache"}


def _files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.name == _SELF:
            continue
        if p.suffix not in _SCAN_EXT and p.name not in _SCAN_NAMES:
            continue
        if _EXCLUDE & set(p.relative_to(ROOT).parts):
            continue
        yield p


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Anti-leak guard — no internal/private references in the public repo.
# (Brand terms "Elder Mind", "Elder Council", "Cyber Elders" are intentional.)
# --------------------------------------------------------------------------
_FORBIDDEN = re.compile(
    r"192\.168\.|157\.90\.24|\bds9\b|\bds10\b|jarvis|hetzner|gitea|:2222|:4444|:3333"
    r"|/Users/|kovnaidoo|\bKovelin\b|\bNaidoo\b|\bCLIFIX\b|TutorYash|ElderTerm|eldermind-gate"
    r"|platform-agent|infrastructure-monitor|methodology-v8|sentineldecoy|\beldernats\b"
    r"|agentgate|agentblack|\bMsty\b|cost portal|advocatus|cio-agent|Sovereign Override"
    r"|\bNATS\b|\bmTLS\b|ELDER_COUNCIL_PROFILE|Engineering-Loops|Nadella"
    # upstream-research source-doc names / internal working artifacts (must never ship):
    r"|vNext|suite-tracker|Engineering-Loops-in-Agentic-AI-v5|Use-Cases-Harness-Configs|cyber-elder-councils"
    # actual-secret shapes (the literal regex strings in ci.yml's secret-scan job do
    # not match these because the key chars are followed by a regex bracket, not [0-9A-Z]):
    r"|ASIA[0-9A-Z]{12,}|AKIA[0-9A-Z]{12,}|gho_[A-Za-z0-9]{20,}",
    re.IGNORECASE,
)


def test_no_internal_private_references():
    offenders = []
    for p in _files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if _FORBIDDEN.search(line):
                offenders.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:80]}")
    assert not offenders, "internal/private references leaked:\n" + "\n".join(offenders)


# --------------------------------------------------------------------------
# No fabricated model tags ship — only verified-real Anthropic tags appear.
# --------------------------------------------------------------------------
_FABRICATED = re.compile(
    r"claude-opus-4[.\-]7|deepseek-v4|kimi-k2|glm-5[.\-]|minimax-m3|gemini-3[.\-]"
    r"|qwen3-coder:480b|gemma4\b",
    re.IGNORECASE,
)


def test_no_fabricated_model_tags():
    offenders = []
    for p in _files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if _FABRICATED.search(line):
                offenders.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:80]}")
    assert not offenders, "fabricated/speculative model tag found:\n" + "\n".join(offenders)


# --------------------------------------------------------------------------
# The ci.yml secret-scan grep runs over the whole tree (incl. .github/) on every
# push/PR. A token written as a bare literal (no regex metachar) in its
# alternation would match the workflow file itself and fail the scan on a clean
# repo — and that only surfaces on a real GitHub run. This mirror runs the
# *actual* pattern from ci.yml locally so any self-matching token (or a real
# secret) is caught here.
# --------------------------------------------------------------------------
def test_secret_scan_pattern_has_no_self_match():
    ci = _read(".github/workflows/ci.yml")
    m = re.search(r'grep -rniE "([^"]+)"', ci)
    assert m, "could not locate the secret-scan grep pattern in ci.yml"
    pat = re.compile(m.group(1), re.IGNORECASE)  # grep -i
    offenders = []
    for p in _files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                offenders.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:80]}")
    assert not offenders, (
        "ci.yml secret-scan pattern matches the tree (self-match or real secret) — "
        "this would fail CI on a clean repo:\n" + "\n".join(offenders)
    )


# --------------------------------------------------------------------------
# Doc-as-test — docs cannot drift from the product.
# --------------------------------------------------------------------------
SIX = ["code-council", "threat-hunting", "supply-chain", "compliance", "cyber-risk", "platform-architecture"]


def test_all_six_councils_documented():
    councils = _read("docs/COUNCILS.md")
    for cid in SIX:
        assert cid in councils, f"{cid} missing from docs/COUNCILS.md"
    # and the YAML set matches the documented set
    assert set(catalog.load_councils()) == set(SIX)


def test_readme_and_councils_consistent():
    readme = _read("README.md")
    for name in ("Code", "Threat Hunting", "Supply Chain", "Compliance", "Cyber Risk", "Platform Architecture"):
        assert name in readme


def test_documented_cli_commands_exist():
    parser = build_parser()
    # subcommand names registered on the parser
    sub = [a for a in parser._subparsers._group_actions if hasattr(a, "choices")][0].choices
    for cmd in ("init", "install", "convene", "list", "show", "gate", "audit", "verify", "models", "version"):
        assert cmd in sub, f"README documents `{cmd}` but the CLI has no such subcommand"


def test_routing_table_in_methodology():
    m = _read("docs/METHODOLOGY.md")
    assert "Impact" in m and "Likelihood" in m
    assert "16" in m and "25" in m  # the critical band
    assert "council" in m.lower() and "human" in m.lower()


def test_readme_demo_reproduces():
    # README claims code-council --demo blocks on the CRITICAL finding.
    c = catalog.get_council("code-council")
    rec = engine.convene_with_votes(c, "merge a hardcoded key", engine.demo_votes(c),
                                    models.load_registry(), do_audit=False)
    assert rec["verdict"] == "block" and rec["route"] == "human"


# --------------------------------------------------------------------------
# Honesty — required caveats present; no bare overclaims. (CI's grep is the
# authoritative gate; this is the python mirror that runs on every PR.)
# --------------------------------------------------------------------------
def test_required_honesty_phrases_present():
    raw = " ".join(_read(f) for f in ("README.md", "START-HERE.md", "THREAT_MODEL.md",
                                      "docs/CONCEPT.md", "docs/METHODOLOGY.md")).lower()
    blob = re.sub(r"\s+", " ", raw)  # collapse line-wraps so phrases match across newlines
    for phrase in ("councils can be wrong", "not legal, regulatory, or compliance advice",
                   "tamper-evident", "ships no keys", "selective plurality", "model-generated"):
        assert phrase in blob, f"missing required honesty phrase: {phrase!r}"
    assert "tamper-evident, not tamper-proof" in blob


# The SA-specific deployment lens we deliberately did NOT port. (POPIA/GDPR may
# still appear as ILLUSTRATIVE examples with a 'not legal advice' caveat — the
# honesty gate enforces that — so they are not forbidden here.)
_REGULATORY = re.compile(r"\bKing IV\b|\bKing 4\b|\bSARB\b|Prudential Authority", re.IGNORECASE)


def test_no_jurisdiction_specific_regulatory_claims():
    # Decision: the harness stays jurisdiction-neutral — no SA-specific deployment
    # lens (King IV / SARB). Illustrative regulation mentions with caveats are fine.
    offenders = []
    for p in _files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if _REGULATORY.search(line):
                offenders.append(f"{p.relative_to(ROOT)}:{i}")
    assert not offenders, "jurisdiction-specific regulatory claims leaked (keep neutral):\n" + "\n".join(offenders)


def test_gates_documented():
    g = _read("docs/GATES.md").lower()
    for profile in ("lite", "standard", "regulated"):
        assert profile in g, f"GATES.md missing profile {profile}"
    for gate in ("evidence", "action-safety", "offensive", "production-change", "data-sensitivity"):
        assert gate in g, f"GATES.md missing gate {gate}"
    assert "hard stop" in g and "not compliant" in g


def test_honesty_gate_passes():
    # the authoritative honesty gate (tools/honesty_check.py) must be clean
    import importlib.util
    spec = importlib.util.spec_from_file_location("honesty_check", ROOT / "tools" / "honesty_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0, "honesty gate reported violations"


def test_no_bare_overclaims_in_readme():
    readme = re.sub(r"\s+", " ", _read("README.md").lower())
    # 'tamper-proof' only ever appears in the negated form
    for m in re.finditer(r"(.{0,16})tamper.?proof", readme):
        assert "not " in m.group(1), "bare 'tamper-proof' claim in README"
    assert "ai-powered" not in readme
    assert "tamper-evident, not tamper-proof" in readme
