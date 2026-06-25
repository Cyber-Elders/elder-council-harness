# SPDX-License-Identifier: Apache-2.0
"""
Honesty gate — no marketing overclaims; the honest caveats present; correct
OWASP-2026 taxonomy; named regulations only in an illustrative context.

Pure stdlib, no install needed. Operates on whitespace-NORMALISED text per file
so a claim wrapped across lines (or a negation on the previous line) is judged
correctly. Run by CI (`python tools/honesty_check.py`) and by tests/test_docs.py.

Exit 0 = clean; exit 1 = a violation (printed). This is the authoritative honesty
gate; the brand voice rules live in docs/BRAND.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Claim surfaces scanned for FORBIDDEN overclaims.
CLAIM_FILES = [
    "README.md", "START-HERE.md", "THREAT_MODEL.md", "CHANGELOG.md",
    "docs/CONCEPT.md", "docs/METHODOLOGY.md", "docs/COUNCILS.md", "docs/LENSES.md",
    "docs/IDE-SUPPORT.md", "docs/STANDARDS-MAP.md", "docs/FAQ.md", "docs/DOMAIN-ADAPTATION.md",
    "docs/ARCHITECTURE.md", "docs/LICENSING.md", "docs/BRAND.md", "docs/TESTING.md",
    "docs/DESIGN-REVIEW.md", "docs/GLOSSARY.md", "docs/GATES.md",
]
# Bundled data that ships to users — also scanned (named-regulation discipline).
DATA_GLOBS = ["eldercouncil/councils/*.yaml", "eldercouncil/lenses.yaml"]

# Meta-docs that describe the policy itself (they enumerate the banned terms and
# the gate by design) — excluded from the overclaim scan, still leak/required-checked.
META_DOCS = {"docs/BRAND.md", "docs/DESIGN-REVIEW.md", "docs/TESTING.md"}

# Affirmative overclaims. A match is a violation UNLESS an allow-word appears in
# the preceding window (negation, or meta-discussion of the policy itself).
FORBIDDEN = re.compile(
    r"\b(?:"
    r"(?:nist|owasp|popia|gdpr|nis2|dora|iso)[ -]*(?:compliant|certified)"
    r"|ai[- ]powered|guarantees?|guaranteed|ensures? (?:correct|compliance)"
    r"|audit[- ]ready|blocks? (?:all )?(?:attacks|prompt injection)|prevents breaches"
    r"|covers all (?:10|ten)|councils are always right|eliminates bias"
    r"|(?:best|optimal|correct) decision|replaces (?:counsel|the analyst)|fully autonomous"
    r")\b",
    re.IGNORECASE,
)
ALLOW_WORDS = (
    "not", "no ", "never", "isn't", "is not", "aware", "aligned", "illustrative",
    "reduce", "selective", "may be wrong", "can be wrong", "forbid", "overclaim",
    "claim discipline", "must not", "do not", "does not", "out of scope", "banned",
    "without warranty", "no lock", "not a ", "no guarantee", "tamper-evident",
)

REQUIRED = [
    r"councils can be wrong",
    r"not legal, regulatory, or compliance advice",
    r"tamper-evident, not tamper-proof",
    r"ships no keys|bring your own llm",
    r"risk acceptance is (?:never|always)|risk acceptance.*human|human.*risk acceptance",
    r"selective plurality",
    r"model-generated",
    r"does not do|out of scope",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _violations() -> list[str]:
    out: list[str] = []
    files = [ROOT / f for f in CLAIM_FILES if f not in META_DOCS and (ROOT / f).exists()]
    for g in DATA_GLOBS:
        files += sorted(ROOT.glob(g))

    # FORBIDDEN overclaims (with preceding-window allow check)
    for p in files:
        norm = _norm(p.read_text(encoding="utf-8"))
        for m in FORBIDDEN.finditer(norm):
            window = norm[max(0, m.start() - 60):m.start()]
            if not any(w in window for w in ALLOW_WORDS):
                out.append(f"overclaim in {p.relative_to(ROOT)}: …{norm[max(0,m.start()-30):m.end()+10]}…")

    # 'tamper-proof' only in the negated form
    for p in files:
        norm = _norm(p.read_text(encoding="utf-8"))
        for m in re.finditer(r"tamper.?proof", norm):
            if "not " not in norm[max(0, m.start() - 16):m.start()]:
                out.append(f"bare 'tamper-proof' in {p.relative_to(ROOT)}")

    # stale (pre-2026) OWASP agentic taxonomy
    for p in (ROOT / "docs").glob("*.md"):
        t = p.read_text(encoding="utf-8")
        if re.search(r"ASI09.*Improper Error Handling|ASI10.*Unbounded Consumption", t):
            out.append(f"stale OWASP taxonomy in {p.relative_to(ROOT)}")

    # REQUIRED honest caveats present somewhere across the claim surfaces
    blob = " ".join(_norm((ROOT / f).read_text(encoding="utf-8")) for f in CLAIM_FILES if (ROOT / f).exists())
    for req in REQUIRED:
        if not re.search(req, blob):
            out.append(f"missing required honest caveat: /{req}/")

    # named regulations must sit near an illustrative / not-legal-advice marker (per file)
    for p in files:
        norm = _norm(p.read_text(encoding="utf-8"))
        if re.search(r"\b(popia|gdpr|nis2|dora)\b", norm) and not any(
            w in norm for w in ("illustrative", "example", "not legal advice", "verify", "configure for your")):
            out.append(f"regulation named without an illustrative/not-legal-advice caveat: {p.relative_to(ROOT)}")

    if not (ROOT / "THREAT_MODEL.md").exists():
        out.append("THREAT_MODEL.md missing")
    return out


def main() -> int:
    viol = _violations()
    if viol:
        print("Honesty gate FAILED:")
        for v in viol:
            print(f"  - {v}")
        return 1
    print("Honesty gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
