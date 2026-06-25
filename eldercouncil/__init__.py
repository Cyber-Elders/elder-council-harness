# SPDX-License-Identifier: Apache-2.0
"""Elder Council — a local-first multi-model council harness for high-stakes
cyber decisions.

Convene a structured, multi-lens council when a decision is consequential,
uncertain, adversarial, or expensive to get wrong — and stay out of the way
otherwise. Deterministic risk-routing (impact x likelihood -> escalate or not),
a pure consensus tally honouring fail-closed minimum-governance rules, and a
hash-chained tamper-evident audit. Local, offline-capable, BYO-LLM (ships no
model and no API keys). OWASP-Agentic-aware, NIST-AI-RMF-aligned.

A council is a *decision-process* control, not a guarantee: councils can be
wrong, a named human owns every critical or risk-acceptance decision, and the
audit is tamper-evident, not tamper-proof.
"""

from .risk_gate import RiskScore, assess, compute_risk_score, route, score
from .consensus import Outcome, Vote, tally

__version__ = "0.1.0"

__all__ = [
    "compute_risk_score",
    "assess",
    "score",
    "route",
    "RiskScore",
    "tally",
    "Vote",
    "Outcome",
    "__version__",
]
