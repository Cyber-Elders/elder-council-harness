# SPDX-License-Identifier: Apache-2.0
"""Install — per-IDE rendering, idempotency, and fail-safes."""

import json

from eldercouncil import install


def test_install_claude_code_renders_all_artifacts(tmp_path):
    rc = install.install("claude-code", target_dir=str(tmp_path), all_councils=True)
    assert rc == 0
    # 7 slash commands, 35 role agents (7 councils x 5 lenses), hooks, MCP, config
    assert len(list((tmp_path / ".claude" / "commands").glob("*.md"))) == 7
    assert len(list((tmp_path / ".claude" / "agents").glob("*.md"))) == 35
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert (tmp_path / ".mcp.json").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".council" / "config.toml").exists()
    assert (tmp_path / ".council" / "council-models.json").exists()
    assert (tmp_path / ".council" / "gate-policy.yaml").exists()   # control-gate policy dropped in


def test_role_agents_resolve_real_models(tmp_path):
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))
    appsec = (tmp_path / ".claude" / "agents" / "code-council-appsec-sme.md").read_text(encoding="utf-8")
    assert "model: claude-opus-4-8" in appsec
    # no fabricated/sentinel tags leak into a rendered file
    assert "REPLACE_ME" not in appsec


def test_claude_hooks_wired(tmp_path):
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    cmds = [h["hooks"][0]["command"] for h in data["hooks"].get("PreToolUse", []) + data["hooks"].get("PostToolUse", [])]
    assert "eldercouncil gate claude-code" in cmds
    assert "eldercouncil audit claude-code" in cmds


def test_kiro_mode_split(tmp_path):
    install.install("kiro", target_dir=str(tmp_path), all_councils=True)
    # action-gate -> agents/*.json ; advisory -> specs/*.md
    assert (tmp_path / ".kiro" / "agents" / "code-council.json").exists()
    assert (tmp_path / ".kiro" / "agents" / "supply-chain.json").exists()
    assert (tmp_path / ".kiro" / "specs" / "compliance.md").exists()
    # compliance is scheduled
    cli = json.loads((tmp_path / ".kiro" / "settings" / "cli.json").read_text())
    assert any(s["name"] == "compliance" for s in cli["scheduled_agents"])


def test_cursor_advisory_rule(tmp_path):
    install.install("cursor", councils=["code-council"], target_dir=str(tmp_path))
    rule = (tmp_path / ".cursor" / "rules" / "code-council.mdc").read_text(encoding="utf-8")
    assert "advisory" in rule.lower() and "alwaysApply: true" in rule


def test_copilot_advisory(tmp_path):
    install.install("copilot", councils=["code-council"], target_dir=str(tmp_path))
    instr = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "advisory" in instr.lower() and "code-council" in instr.lower()
    # VS Code MCP uses the top-level "servers" key (not "mcpServers")
    mcp = json.loads((tmp_path / ".vscode" / "mcp.json").read_text())
    assert "eldercouncil" in mcp["servers"]


def test_opencode_plugin_and_orchestrator(tmp_path):
    install.install("opencode", councils=["code-council"], target_dir=str(tmp_path))
    assert (tmp_path / ".opencode" / "plugins" / "eldercouncil.js").exists()
    oc = json.loads((tmp_path / "opencode.json").read_text())
    assert "code-council-orchestrator" in oc["agents"]
    assert "eldercouncil" in oc["mcp"]


def test_idempotent_rerun(tmp_path, capsys):
    install.install("claude-code", target_dir=str(tmp_path), all_councils=True)
    capsys.readouterr()
    install.install("claude-code", target_dir=str(tmp_path), all_councils=True)
    out = capsys.readouterr().out
    assert "unchanged" in out
    # re-run must not duplicate the PreToolUse hook
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    gate = [h for h in data["hooks"]["PreToolUse"]]
    assert len(gate) == 1


def test_repin_changes_only_model_line(tmp_path):
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))
    agent = tmp_path / ".claude" / "agents" / "code-council-appsec-sme.md"
    body_before = agent.read_text(encoding="utf-8").split("---", 2)[2]
    # repin the security_sme frontier model in the project registry
    reg_path = tmp_path / ".council" / "council-models.json"
    reg = json.loads(reg_path.read_text())
    reg["roles"]["security_sme"]["frontier"] = "claude-opus-4-8-pinned"
    reg_path.write_text(json.dumps(reg))
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))
    text = agent.read_text(encoding="utf-8")
    assert "model: claude-opus-4-8-pinned" in text
    assert text.split("---", 2)[2] == body_before  # body unchanged


def test_local_lane_makes_every_lens_inherit(tmp_path):
    # --lane local must switch EVERY lens to the local lane → all REPLACE_ME → inherit,
    # so a user on a local backend (e.g. Claude Code on Ollama) runs every lens on their
    # own session model with no pinned Claude tag to 404 on. (Regression: role.variant
    # used to default to "frontier" and silently override --lane.)
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path), lane="local")
    bodies = [a.read_text(encoding="utf-8") for a in (tmp_path / ".claude" / "agents").glob("*.md")]
    assert bodies and all("model: inherit" in b for b in bodies), "every lens should inherit on --lane local"
    assert not any("model: claude-" in b for b in bodies), "no Claude tag may be pinned on the local lane"


def test_frontier_lane_still_pins_claude(tmp_path):
    # the DEFAULT (frontier) path is unchanged — real Claude tags still render.
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))  # lane defaults to frontier
    appsec = (tmp_path / ".claude" / "agents" / "code-council-appsec-sme.md").read_text(encoding="utf-8")
    assert "model: claude-opus-4-8" in appsec


def test_unknown_ide_and_council_fail(tmp_path):
    assert install.install("emacs", target_dir=str(tmp_path)) == 1
    assert install.install("claude-code", councils=["nope"], target_dir=str(tmp_path)) == 1


def test_files_are_utf8(tmp_path):
    install.install("claude-code", councils=["code-council"], target_dir=str(tmp_path))
    # CLAUDE.md and a role agent must be valid UTF-8 (Windows cp1252 trap)
    (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
