# SPDX-License-Identifier: Apache-2.0
"""
build_review() — turn a council + question into a BYO-LLM deliberation task.

Elder Council ships NO model clients and NO API keys. By default the host
agent's own runtime runs the deliberation: this module returns the per-role
prompts (lens + the shared deliberation protocol) with each role's model
resolved from the registry. The host agent fans out to its sub-agents, collects
the votes, and the deterministic `consensus.tally` combines them.

Pure: no model is called here.
"""

from __future__ import annotations

from . import models
from .models import ModelRegistry, UnpinnedError

# The shared deliberation protocol every lens answers in — keeps outputs
# structured and comparable, and makes disagreement visible.
PROTOCOL = (
    "Respond using this structure:\n"
    "  Position: <your one-line stance>\n"
    "  Analysis: <reasoning grounded in the evidence>\n"
    "  Risks/Concerns: <what could go wrong, edge cases, assumptions>\n"
    "  Vote: <one of: {outcomes}>\n"
    "  Confidence: <Low | Medium | High>"
)


def _role_prompt(council, role, question: str) -> str:
    if role.is_tool:
        return (
            f"You are the '{role.name}' lens of the {council.name}. You are NOT a reasoning model — "
            f"you run deterministic checks and report findings as evidence.\n"
            f"DECISION: {question}\n"
            f"Run the relevant checks (SAST, dependency scan, secret scan, tests, policy) and report "
            f"only what the tools found. Then cast a vote among {{{', '.join(council.decision_outcomes)}}} "
            f"based solely on tool findings, with a one-line justification."
        )
    return (
        f"You are the '{role.name}' lens of the {council.name}, an Elder Council convened because a "
        f"decision is consequential, uncertain, or adversarial. Reason INDEPENDENTLY from the other "
        f"lenses before any synthesis.\n\n"
        f"YOUR LENS: {role.lens.strip()}\n\n"
        f"DECISION UNDER REVIEW:\n{question}\n\n"
        f"{PROTOCOL.format(outcomes=', '.join(council.decision_outcomes))}"
    )


def build_review(council, question: str, registry: ModelRegistry, lane: str = "frontier") -> dict:
    """Return the deliberation task set for the host agent to execute."""
    tasks = []
    for role in council.roles:
        try:
            model = models.resolve(registry, role.role_key, role.variant or lane)
        except UnpinnedError:
            # Unpinned (REPLACE_ME) -> fall back to the host agent's own model.
            # An UNKNOWN role key (a typo) is NOT caught here — it propagates so a
            # misconfigured council surfaces loudly instead of silently collapsing
            # every lens onto one model.
            model = "inherit"
        tasks.append({
            "role": role.name,
            "role_key": role.role_key,
            "lens": role.lens.strip(),
            "model": model,
            "is_tool": role.is_tool,
            "arbitrator": role.arbitrator,
            "prompt": _role_prompt(council, role, question),
        })
    instructions = (
        f"Run each task with its assigned model (or your own lead model where model='inherit'), "
        f"collect one vote per lens, then combine them with `eldercouncil`'s consensus rules "
        f"(ties block; escalation wins; risk-acceptance and critical actions route to a human; "
        f"advisory councils recommend, a human decides). "
        f"This council is '{council.mode}'. Fail-closed rule: {council.fail_closed.strip()}"
    )
    return {
        "council": council.id,
        "name": council.name,
        "mode": council.mode,
        "question": question,
        "decision_outcomes": list(council.decision_outcomes),
        "fail_closed": council.fail_closed.strip(),
        "lane": lane,
        "tasks": tasks,
        "instructions": instructions,
    }
