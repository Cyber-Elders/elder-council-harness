# SPDX-License-Identifier: Apache-2.0
"""
`eldercouncil install <ide>` — render councils into a harness, idempotently.

Councils are pure DATA; this renderer is generic — there is no per-council code
branch. For each selected council it renders the IDE-native files (slash command
/ role agents / spec / orchestrator), and once per install it wires the pre-tool
gate hook + the advisory MCP server. It never clobbers: JSON is merged, markdown
blocks are sentinel-guarded, and every change is printed. Safe to re-run — after
editing `.council/council-models.json`, re-running re-pins the role `model:`
lines without touching the prompt bodies.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import models, paths
from .catalog import load_councils
from .convene import PROTOCOL
from .schema import Council, Role

_MCP_ENTRY = {"command": "eldercouncil", "args": ["serve"]}
_OPENCODE_MCP_ENTRY = {"type": "local", "command": ["eldercouncil", "serve"], "enabled": True}

_CLAUDE_MATCHER = "Bash|Edit|Write|Read|MultiEdit|NotebookEdit|WebFetch|Task|mcp__.*"

_OPENCODE_PLUGIN_JS = """\
// eldercouncil — OpenCode pre-tool gate shim. Installed by `eldercouncil install opencode`.
// Scores the action; on ask/block it stops the call so the relevant council is convened.
import { spawnSync } from "node:child_process";

export const hooks = {
  "tool.execute.before": async (input) => {
    const payload = JSON.stringify({
      tool: input?.tool ?? input?.name ?? "",
      args: input?.args ?? input?.input ?? {},
    });
    const res = spawnSync("eldercouncil", ["gate", "opencode"], { input: payload, encoding: "utf-8" });
    let d = {};
    try { d = JSON.parse((res.stdout || "").trim() || "{}"); } catch (_) {}
    if (d.verdict === "block" || d.verdict === "ask") {
      throw new Error(`eldercouncil ${d.verdict}: ${d.reason || "convene the council"}`);
    }
    return input;
  },
  "tool.execute.after": async (input, output) => {
    const payload = JSON.stringify({ tool: input?.tool ?? "", args: input?.args ?? {} });
    spawnSync("eldercouncil", ["audit", "opencode"], { input: payload, encoding: "utf-8" });
    return output;
  },
};
"""

_KIRO_STEERING_MD = """\
---
inclusion: always
---
# Elder Council governance

This project convenes multi-model Elder Councils for high-stakes decisions. A
pre-tool gate scores each action (impact x likelihood, 1-25); at or above the
convene threshold it asks you to convene the relevant council (.kiro/agents or
.kiro/specs) before proceeding. Councils can be wrong and are decision SUPPORT,
not a guarantee: risk acceptance and critical actions are always a human's call,
and council output is model-generated, not legal advice. Do not bypass the gate;
surface its reason to the user.
"""


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _project_dir(target_dir: str | None) -> Path:
    return Path(target_dir).resolve() if target_dir else Path.cwd()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return {}


def _write_json(path: Path, data: dict, changes: list[str], label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.read_text(encoding="utf-8") if path.exists() else None
    text = json.dumps(data, indent=2) + "\n"
    if before == text:
        changes.append(f"= {path} ({label}, unchanged)")
    else:
        path.write_text(text, encoding="utf-8")
        changes.append(f"{'~' if before is not None else '+'} {path} ({label})")


def _write_text(path: Path, text: str, changes: list[str], label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.read_text(encoding="utf-8") if path.exists() else None
    if before == text:
        changes.append(f"= {path} ({label}, unchanged)")
    else:
        path.write_text(text, encoding="utf-8")
        changes.append(f"{'~' if before is not None else '+'} {path} ({label})")


def _append_block(path: Path, council_id: str, content: str, changes: list[str]) -> None:
    """Sentinel-guarded markdown append — idempotent per council."""
    start, end = f"<!-- eldercouncil:{council_id} START -->", f"<!-- eldercouncil:{council_id} END -->"
    block = f"{start}\n{content.rstrip()}\n{end}\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.DOTALL)
    if pattern.search(existing):
        new = pattern.sub(block, existing)
        if new == existing:
            changes.append(f"= {path} (council block unchanged)")
        else:
            path.write_text(new, encoding="utf-8")
            changes.append(f"~ {path} (updated {council_id} block)")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        sep = "" if (not existing or existing.endswith("\n\n")) else ("\n" if existing.endswith("\n") else "\n\n")
        path.write_text(existing + sep + block, encoding="utf-8")
        changes.append(f"{'~' if existing else '+'} {path} ({council_id} council block)")


def _register_mcp(path: Path, key: str, entry: dict, changes: list[str]) -> None:
    data = _load_json(path)
    servers = data.setdefault(key, {})
    if servers.get("eldercouncil") == entry:
        changes.append(f"= {path} (MCP server already registered)")
        return
    servers["eldercouncil"] = entry
    _write_json(path, data, changes, "registered MCP server 'eldercouncil'")


def _model_for(reg, role: Role, lane: str) -> str:
    try:
        return models.resolve(reg, role.role_key, role.variant or lane)
    except models.UnpinnedError:
        return "inherit"  # unpinned (REPLACE_ME) — host agent's own model
    # an UNKNOWN role key (models.RegistryError) propagates -> install fails loudly


def _role_body(council: Council, role: Role) -> str:
    outcomes = ", ".join(council.decision_outcomes)
    if role.is_tool:
        return (
            f"You are the **{role.name}** lens of the {council.name}. You are NOT a reasoning model — "
            f"run deterministic checks (SAST, dependency/secret scan, tests, policy) and report findings "
            f"as evidence, then vote among {{{outcomes}}} based only on what the tools found."
        )
    return (
        f"You are the **{role.name}** lens of the {council.name}. Reason INDEPENDENTLY from the other "
        f"lenses.\n\n## Your lens\n{role.lens.strip()}\n\n## Protocol\n"
        + PROTOCOL.format(outcomes=outcomes)
        + f"\n\nFail-closed rule for this council: {council.fail_closed.strip()}"
    )


# --------------------------------------------------------------------------
# Claude Code
# --------------------------------------------------------------------------
def _render_claude_council(root: Path, c: Council, reg, lane: str, changes: list[str]) -> None:
    role_agents = [f"@{c.id}-{_slug(r.name)}" for r in c.roles]
    cmd = (
        f"---\ndescription: Convene the {c.name} on the decision/context provided.\n---\n"
        f"Convene the **{c.name}** ({c.mode}). Fan out IN PARALLEL via the Task tool to these lenses, "
        f"each given the current decision/context (e.g. `git diff`, the alert, the dependency):\n"
        + "".join(f"{i+1}. {a}\n" for i, a in enumerate(role_agents))
        + f"\nEach lens votes among: {{{', '.join(c.decision_outcomes)}}}. Combine the votes under "
        f"Elder Council consensus (ties block; escalation wins; risk-acceptance & critical actions and "
        f"advisory councils route to a human). Fail-closed: {c.fail_closed.strip()}\n"
        f"Record all votes + dissent by calling the `audit_log` MCP tool with council=\"{c.id}\". "
        f"Do not proceed on a blocking verdict.\n"
    )
    _write_text(root / ".claude" / "commands" / f"{c.id}.md", cmd, changes, f"{c.id} slash command")
    for r in c.roles:
        body = (
            f"---\nname: {c.id}-{_slug(r.name)}\n"
            f"description: {r.name} lens of the {c.name}.\n"
            f"tools: Read, Grep, Glob, Bash\nmodel: {_model_for(reg, r, lane)}\n---\n"
            + _role_body(c, r) + "\n"
        )
        _write_text(root / ".claude" / "agents" / f"{c.id}-{_slug(r.name)}.md", body, changes, f"{c.id} role agent")
    block = (
        f"## Elder Council — {c.name} (active)\n"
        f"Purpose: {c.purpose.strip()}\n\n"
        f"Convene `/{c.id}` when the gate asks (risk score >= the convene threshold) or a trigger fires: "
        f"{'; '.join(t.condition for t in c.triggers) or 'a high-stakes decision in this domain'}. "
        f"Mode: {c.mode}. Fail-closed: {c.fail_closed.strip()}"
    )
    _append_block(root / "CLAUDE.md", c.id, block, changes)


def _wire_claude_hooks(root: Path, changes: list[str]) -> None:
    settings = root / ".claude" / "settings.json"
    data = _load_json(settings)
    hooks = data.setdefault("hooks", {})
    for evt, cmd in (("PreToolUse", "eldercouncil gate claude-code"), ("PostToolUse", "eldercouncil audit claude-code")):
        entries = hooks.setdefault(evt, [])
        already = any(any(h.get("command") == cmd for h in e.get("hooks", [])) for e in entries if isinstance(e, dict))
        if already:
            changes.append(f"= {settings} ({evt} hook already present)")
        else:
            entries.append({"matcher": _CLAUDE_MATCHER, "hooks": [{"type": "command", "command": cmd}]})
    _write_json(settings, data, changes, "gate + audit hooks")
    _register_mcp(root / ".mcp.json", "mcpServers", _MCP_ENTRY, changes)


# --------------------------------------------------------------------------
# OpenCode
# --------------------------------------------------------------------------
def _render_opencode_council(root: Path, c: Council, reg, lane: str, changes: list[str]) -> None:
    for r in c.roles:
        body = (
            f"---\ndescription: {r.name} lens of the {c.name}.\nmodel: {_model_for(reg, r, lane)}\n---\n"
            + _role_body(c, r) + "\n"
        )
        _write_text(root / ".opencode" / "agents" / f"{c.id}-{_slug(r.name)}.md", body, changes, f"{c.id} role agent")
    data = _load_json(root / "opencode.json")
    agents = data.setdefault("agents", {})
    mentions = " ".join(f"@{c.id}-{_slug(r.name)}" for r in c.roles)
    orch = {
        "description": f"Orchestrates the {c.name} ({c.mode}).",
        "system": (
            f"You orchestrate the {c.name}. Fan out in parallel to {mentions} with the decision/context. "
            f"Each votes among {{{', '.join(c.decision_outcomes)}}}. Apply Elder Council consensus "
            f"(ties block; escalation wins; risk-acceptance/critical/advisory route to a human). "
            f"Fail-closed: {c.fail_closed.strip()} "
            f"Record votes + dissent via the audit_log MCP tool (council=\"{c.id}\")."
        ),
    }
    if agents.get(f"{c.id}-orchestrator") != orch:
        agents[f"{c.id}-orchestrator"] = orch
        _write_json(root / "opencode.json", data, changes, f"{c.id} orchestrator agent")
    else:
        changes.append(f"= {root / 'opencode.json'} ({c.id} orchestrator unchanged)")


def _wire_opencode_hooks(root: Path, changes: list[str]) -> None:
    _write_text(root / ".opencode" / "plugins" / "eldercouncil.js", _OPENCODE_PLUGIN_JS, changes, "gate plugin")
    _register_mcp(root / "opencode.json", "mcp", _OPENCODE_MCP_ENTRY, changes)


# --------------------------------------------------------------------------
# Kiro (best-effort)
# --------------------------------------------------------------------------
def _render_kiro_council(root: Path, c: Council, reg, lane: str, changes: list[str]) -> None:
    if c.mode == "action-gate":
        agent = {
            "name": c.id,
            "description": f"{c.name} — {c.purpose.strip()[:120]}",
            "parallel_agents": [
                {"role": _slug(r.name), "model": _model_for(reg, r, lane), "lens": r.lens.strip()}
                for r in c.roles
            ],
            "decision_outcomes": list(c.decision_outcomes),
            "fail_closed": c.fail_closed.strip(),
            "hooks": {"pre_action": "eldercouncil gate kiro", "post_decision": "eldercouncil audit kiro"},
        }
        _write_json(root / ".kiro" / "agents" / f"{c.id}.json", agent, changes, f"{c.id} agent (command mode)")
    else:
        roles_md = "".join(f"- {r.name} ({r.role_key}): {r.lens.strip()}\n" for r in c.roles)
        spec = (
            f"# {c.name} (advisory)\n\n## Purpose\n{c.purpose.strip()}\n\n"
            f"## Lenses\n{roles_md}\n## Decision outcomes\n{', '.join(c.decision_outcomes)}\n\n"
            f"## Output\nWrite `{c.output_path}` and call the audit_log MCP tool (council=\"{c.id}\") with each "
            f"lens's vote + reasoning and the synthesised recommendation, preserving dissent.\n\n"
            f"## Fail-closed\n{c.fail_closed.strip()}\n"
        )
        _write_text(root / ".kiro" / "specs" / f"{c.id}.md", spec, changes, f"{c.id} spec (advisory)")
    if c.schedule:
        cli = root / ".kiro" / "settings" / "cli.json"
        data = _load_json(cli)
        sched = data.setdefault("scheduled_agents", [])
        entry = {"name": c.id, "cron": c.schedule, "spec": f".kiro/specs/{c.id}.md", "notify_on_complete": True}
        if not any(s.get("name") == c.id for s in sched):
            sched.append(entry)
            _write_json(cli, data, changes, f"{c.id} scheduled audit")
        else:
            changes.append(f"= {cli} ({c.id} schedule already present)")


def _wire_kiro_hooks(root: Path, changes: list[str]) -> None:
    _write_text(root / ".kiro" / "steering" / "eldercouncil.md", _KIRO_STEERING_MD, changes, "steering")
    _register_mcp(root / ".kiro" / "settings" / "mcp.json", "mcpServers", _MCP_ENTRY, changes)
    changes.append("! Kiro adapter is best-effort, pending live-harness verification — see docs/IDE-SUPPORT.md")


# --------------------------------------------------------------------------
# Cursor (advisory)
# --------------------------------------------------------------------------
def _render_cursor_council(root: Path, c: Council, reg, lane: str, changes: list[str]) -> None:
    rule = (
        f"---\ndescription: Elder Council — {c.name} (advisory).\nalwaysApply: true\n---\n"
        f"# {c.name} (advisory)\n\nCursor has no blocking pre-tool hook, so this is advisory. "
        f"Before a high-stakes action in this domain ({'; '.join(t.condition for t in c.triggers) or c.purpose.strip()[:80]}), "
        f"call the `risk_gate` MCP tool; if it routes to a council, call `convene_council` "
        f"(council=\"{c.id}\"), run the lenses, and honour the verdict. Outcomes: "
        f"{', '.join(c.decision_outcomes)}. Fail-closed: {c.fail_closed.strip()} "
        f"Record the result with `audit_log`. Councils can be wrong; risk acceptance and critical "
        f"actions are a human's call. Do not bypass the gate.\n"
    )
    _write_text(root / ".cursor" / "rules" / f"{c.id}.mdc", rule, changes, f"{c.id} advisory rule")


def _wire_cursor_hooks(root: Path, changes: list[str]) -> None:
    _register_mcp(root / ".cursor" / "mcp.json", "mcpServers", _MCP_ENTRY, changes)
    changes.append("! Cursor is ADVISORY only (no hard pre-tool block) — see docs/IDE-SUPPORT.md")


# --------------------------------------------------------------------------
# GitHub Copilot (advisory — VS Code / JetBrains / Visual Studio agent mode)
# --------------------------------------------------------------------------
def _render_copilot_council(root: Path, c: Council, reg, lane: str, changes: list[str]) -> None:
    # Copilot agent mode has no blocking pre-tool hook, so guidance is advisory and
    # lives in the repo-wide custom-instructions file (one sentinel block per council).
    block = (
        f"### Elder Council — {c.name} ({c.mode}, advisory)\n"
        f"Before a high-stakes action in this domain "
        f"({'; '.join(t.condition for t in c.triggers) or c.purpose.strip()[:80]}), call the "
        f"`risk_gate` MCP tool; if it routes to a council, call `convene_council` (council=\"{c.id}\"), "
        f"run the lenses, and honour the verdict. Outcomes: {', '.join(c.decision_outcomes)}. "
        f"Fail-closed: {c.fail_closed.strip()} Record the result with `audit_log`. Councils can be "
        f"wrong; risk acceptance and critical actions are a human's call. Do not bypass the gate."
    )
    _append_block(root / ".github" / "copilot-instructions.md", c.id, block, changes)


def _wire_copilot_hooks(root: Path, changes: list[str]) -> None:
    # VS Code uses the top-level key "servers" (NOT "mcpServers"); requires agent mode.
    _register_mcp(root / ".vscode" / "mcp.json", "servers", _MCP_ENTRY, changes)
    changes.append("! Copilot agent mode is ADVISORY only (no hard pre-tool block in the editor); "
                   "Copilot CLI/cloud can hard-block via a preToolUse hook — see docs/IDE-SUPPORT.md")


_RENDERERS = {
    "claude-code": (_render_claude_council, _wire_claude_hooks),
    "opencode": (_render_opencode_council, _wire_opencode_hooks),
    "kiro": (_render_kiro_council, _wire_kiro_hooks),
    "cursor": (_render_cursor_council, _wire_cursor_hooks),
    "copilot": (_render_copilot_council, _wire_copilot_hooks),
}


def _ensure_project_config(root: Path, lane: str, tier: str, profile: str, changes: list[str]) -> None:
    cdir = root / ".council"
    cfg = cdir / "config.toml"
    if not cfg.exists():
        body = (
            "# Elder Council Harness — project config\n"
            f"[governance]\ntier = \"{tier}\"\nmode = \"enforce\"\nprofile = \"{profile}\"  # lite | standard | regulated\n\n"
            f"[council]\nlane = \"{lane}\"\nconvene_threshold = 5\n"
        )
        cdir.mkdir(parents=True, exist_ok=True)
        cfg.write_text(body, encoding="utf-8")
        changes.append(f"+ {cfg} (project config)")
    else:
        changes.append(f"= {cfg} (config already present)")
    # Drop a copy of the default model registry the user can pin.
    dest = cdir / "council-models.json"
    if not dest.exists():
        shutil.copyfile(paths.bundled_models_path(), dest)
        changes.append(f"+ {dest} (model registry — pin your cross-family/open/local lanes here)")
    else:
        changes.append(f"= {dest} (model registry already present)")
    # Drop the control-gate policy (the fail-closed gate layer; editable per project).
    gp = cdir / "gate-policy.yaml"
    if not gp.exists():
        shutil.copyfile(paths.package_dir() / "gate-policy.yaml", gp)
        changes.append(f"+ {gp} (control-gate policy — profile: {profile})")
    else:
        changes.append(f"= {gp} (gate policy already present)")


def install(ide: str, councils: list[str] | None = None, target_dir: str | None = None,
            lane: str = "frontier", tier: str = "practitioner", all_councils: bool = False,
            profile: str = "standard") -> int:
    if ide not in _RENDERERS:
        print(f"unknown IDE: {ide} (expected: {', '.join(_RENDERERS)})")
        return 1
    available = load_councils()
    if all_councils or not councils:
        selected = list(available.values())
    else:
        selected = []
        for cid in councils:
            if cid not in available:
                print(f"unknown council: {cid} (have: {', '.join(sorted(available))})")
                return 1
            selected.append(available[cid])

    root = _project_dir(target_dir)
    reg = models.load_registry(root / ".council" / "council-models.json"
                               if (root / ".council" / "council-models.json").exists() else None)
    changes: list[str] = []
    _ensure_project_config(root, lane, tier, profile, changes)
    render, wire = _RENDERERS[ide]
    for c in selected:
        render(root, c, reg, lane, changes)
    wire(root, changes)

    print(f"Elder Council installed for {ide} in {root}")
    print(f"  councils: {', '.join(c.id for c in selected)}")
    for line in changes:
        print(f"  {line}")
    print("\nLegend: + created · ~ modified · = unchanged")
    unresolved = models.unresolved(reg)
    if lane != "frontier" or any(r.variant != "frontier" for c in selected for r in c.roles):
        print(f"Model lanes still unpinned (REPLACE_ME): {len(unresolved)} — run `eldercouncil models check`.")
    if ide in ("claude-code", "opencode", "kiro"):  # hard-block IDEs have a `gate <ide>` target
        print(f"Verify:  echo '{{\"action\":\"bash\",\"target\":\"git push --force\"}}' | eldercouncil gate {ide}")
    else:  # cursor / copilot are advisory — no pre-tool gate; verify the advisory wiring instead
        print("Verify:  eldercouncil convene code-council --demo   (advisory IDE — no pre-tool gate; the agent is asked to convene)")
    return 0


def guided_init(ide: str | None = None, target_dir: str | None = None) -> int:
    print("Elder Council Harness — guided setup\n")

    def ask(prompt: str, default: str) -> str:
        try:
            ans = input(f"{prompt} [{default}]: ").strip()
        except EOFError:
            ans = ""
        return ans or default

    if ide is None:
        ide = ask("Which coding agent? (claude-code / opencode / kiro = hard-block · cursor / copilot = advisory)", "claude-code")
    if ide not in _RENDERERS:
        print(f"unknown IDE: {ide}")
        return 1
    available = sorted(load_councils())
    print("\nCouncils: " + ", ".join(available))
    sel = ask("Which councils to install? (comma-separated ids, or 'all')", "all")
    councils = None if sel.strip().lower() == "all" else [s.strip() for s in sel.split(",") if s.strip()]
    lane = ask("Model lane (frontier / open / local)", "frontier")
    tier = ask("Governance tier (explorer / practitioner / governed / operator)", "practitioner")
    profile = ask("Control-gate profile (lite = 4 gates / standard = 11 / regulated = 11 + controls)", "standard")
    return install(ide, councils=councils, target_dir=target_dir, lane=lane, tier=tier,
                   all_councils=(councils is None), profile=profile)
