# SPDX-License-Identifier: Apache-2.0
"""
Branded PDF generator (needs the [pdf] extra: reportlab==4.5.1, pinned).

Produces byte-stable, brand-consistent PDFs under docs/pdf/. ReportLab's
`invariant` mode strips timestamps/ids so the output is reproducible — the
docs-collateral CI job asserts the committed copies match a fresh build.
"""

from __future__ import annotations

from pathlib import Path

from reportlab import rl_config

rl_config.invariant = 1  # deterministic output (no embedded dates/ids)

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).resolve().parents[1] / "docs" / "pdf"
INDIGO = HexColor("#3730a3")
SLATE = HexColor("#334155")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("ECTitle", parent=ss["Title"], textColor=INDIGO, fontSize=26, leading=30))
    ss.add(ParagraphStyle("ECTag", parent=ss["Normal"], textColor=SLATE, fontSize=13, leading=18, spaceAfter=14))
    ss.add(ParagraphStyle("ECH2", parent=ss["Heading2"], textColor=INDIGO, fontSize=14, leading=18, spaceBefore=10))
    ss.add(ParagraphStyle("ECBody", parent=ss["Normal"], fontSize=10.5, leading=15, spaceAfter=6))
    return ss


def _doc(name: str, flow):
    OUT.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(OUT / name), pagesize=A4,
                      leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm, bottomMargin=20 * mm,
                      title="Elder Council Harness", author="Cyber Elders Pty Ltd").build(flow)


def overview(ss):
    s = []
    s += [Paragraph("Elder Council Harness", ss["ECTitle"])]
    s += [Paragraph("Don't let one model decide alone.", ss["ECTag"])]
    for h, b in [
        ("The problem",
         "When one model reviews your code, triages your alerts, vets your dependencies, scores "
         "your risk — and weighs your bet-the-business calls — its blind spots stop being an isolated "
         "bad answer and become a repeatable pattern inside your decision infrastructure — a systemic "
         "single point of failure."),
        ("The response: selective plurality",
         "Use a single agent or a deterministic tool where that is enough; convene a structured, "
         "multi-lens council only when a decision is consequential, uncertain, adversarial, or "
         "expensive to get wrong. A risk gate (impact x likelihood, 1-25) decides when."),
        ("Seven councils",
         "Six cyber — Code, Threat Hunting, Supply Chain Audit, Multi-Jurisdictional Compliance, Cyber "
         "Risk, Platform Architecture — plus a general Business Decision council for executive calls. "
         "Each convenes independent lenses, combines their votes under fail-closed rules, preserves "
         "dissent, and records a tamper-evident audit entry."),
        ("Honest by design",
         "A council is decision support, not a guarantee. Councils can be wrong. A named human owns "
         "every critical and risk-acceptance decision. The audit is tamper-evident, not tamper-proof. "
         "The harness ships no keys — bring your own LLM. Council output is model-generated and is not "
         "legal, regulatory, or compliance advice."),
    ]:
        s += [Paragraph(h, ss["ECH2"]), Paragraph(b, ss["ECBody"])]
    s += [Spacer(1, 10), Paragraph("Apache-2.0 (code) + CC BY 4.0 (docs). © 2026 Cyber Elders Pty Ltd.", ss["ECBody"])]
    return s


def quickstart(ss):
    s = []
    s += [Paragraph("Elder Council — Quickstart", ss["ECTitle"])]
    s += [Paragraph("Convene the council. Keep the dissent. Own the decision.", ss["ECTag"])]
    for h, b in [
        ("1. Install", "pip install eldercouncil &nbsp; (ships no keys — bring your own LLM)"),
        ("2. See a council decide (keyless)",
         "eldercouncil convene code-council --demo --question \"merge a diff with a hardcoded AWS key\""),
        ("3. Wire it into your agent",
         "eldercouncil init &nbsp; (guided), or eldercouncil install claude-code --all"),
        ("4. What you get",
         "A pre-tool gate that asks you to convene the right council on high-risk actions; the councils "
         "run on your agent's own models; every verdict, vote, and dissent is recorded to .council/."),
    ]:
        s += [Paragraph(h, ss["ECH2"]), Paragraph(b, ss["ECBody"])]
    return s


def main():
    ss = _styles()
    _doc("Elder-Council-Overview.pdf", overview(ss))
    _doc("Elder-Council-Quickstart.pdf", quickstart(ss))
    print(f"wrote PDFs to {OUT}")


if __name__ == "__main__":
    main()
