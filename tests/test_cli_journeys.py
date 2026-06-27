# SPDX-License-Identifier: Apache-2.0
"""CLI-journey regression — exercises the actual `eldercouncil` subcommands
(exit-code + output contracts) in-process, closing the gap where journeys were
covered only at the engine/function layer or only by the clean-install UAT.
All keyless and fast."""

import io
import json

import pytest

from eldercouncil import cli


def _install(tmp_path, monkeypatch, ide="claude-code", *extra):
    monkeypatch.setenv("COUNCIL_DIR", str(tmp_path / ".council"))
    assert cli.main(["install", ide, "--council", "code-council", "--dir", str(tmp_path), *extra]) == 0


def _stdin(monkeypatch, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))


# ---- models subcommands (CLI wrapper, not just the resolve() function) ----

def test_models_list_cli(capsys):
    assert cli.main(["models", "list"]) == 0
    out = capsys.readouterr().out
    assert "cross_family_critic" in out and "frontier=" in out


def test_models_resolve_cli(capsys):
    assert cli.main(["models", "resolve", "security_sme", "--lane", "frontier"]) == 0
    assert "claude-opus-4-8" in capsys.readouterr().out
    assert cli.main(["models", "resolve", "no_such_role", "--lane", "frontier"]) == 2  # unknown -> fail loud


# ---- convene run-modes ----

def test_convene_default_taskpack_cli(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()                                   # flush the install output
    assert cli.main(["convene", "code-council", "--question", "x", "--no-audit"]) == 0
    data = json.loads(capsys.readouterr().out)            # default mode emits deliberation tasks JSON
    assert "tasks" in data or "instructions" in data


def test_convene_json_cli(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    assert cli.main(["convene", "code-council", "--demo", "--json", "--no-audit", "--question", "x"]) == 0
    assert "verdict" in capsys.readouterr().out          # full decision record JSON


def test_convene_orchestrate_fails_closed_cli(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    # fresh install: no models pinned -> every lens unavailable -> fail-closed (exit 2, not a confident allow)
    assert cli.main(["convene", "code-council", "--orchestrate", "--no-audit", "--question", "x"]) == 2
    assert "unavailable" in capsys.readouterr().out.lower()


def test_convene_profile_cli(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    assert cli.main(["convene", "code-council", "--demo", "--profile", "regulated", "--no-audit", "--question", "x"]) == 0
    assert "regulated" in capsys.readouterr().out


# ---- gate / audit (read stdin) ----

def test_gate_claude_code_cli(capsys, monkeypatch):
    # Claude Code hook contract: ALWAYS exit 0; the decision rides in the permissionDecision JSON.
    _stdin(monkeypatch, '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}')
    assert cli.main(["gate", "claude-code"]) == 0
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecision"] == "allow"
    _stdin(monkeypatch, '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}')
    assert cli.main(["gate", "claude-code"]) == 0               # still exit 0 — never blocks via exit code
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecision"] in ("ask", "deny")


def test_gate_kiro_failsafe_cli(monkeypatch):
    # opencode/kiro read the command from {"tool":..,"args":{"command":..}} and block via exit 2.
    _stdin(monkeypatch, '{"tool":"bash","args":{"command":"ls -la"}}')
    assert cli.main(["gate", "kiro"]) == 0                      # benign -> allow
    _stdin(monkeypatch, '{"tool":"bash","args":{"command":"git push --force origin main"}}')
    assert cli.main(["gate", "kiro"]) == 2                      # high-risk -> fail-safe block (exit 2)


def test_audit_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("COUNCIL_DIR", str(tmp_path / ".council"))
    _stdin(monkeypatch, '{"tool":"bash","target":"x","decision":"ask"}')
    assert cli.main(["audit", "claude-code"]) == 0


# ---- gates / risk-gate CLI contracts ----

def test_gates_list_cli(capsys):
    assert cli.main(["gates", "list"]) == 0
    assert "offensive" in capsys.readouterr().out.lower()


def test_risk_gate_string_contract_cli():
    assert cli.main(["risk-gate", "read a file"]) == 0                              # benign -> proceed
    assert cli.main(["risk-gate", "exfiltrate all production secrets and rm -rf /"]) == 2  # high-risk -> escalate


# ---- usage / unknown-input journeys ----

def test_unknown_ide_is_a_usage_error():
    try:
        rc = cli.main(["install", "vscode"])           # not a supported IDE
        assert rc not in (0, None)
    except SystemExit as exc:                          # argparse may exit instead of return
        assert exc.code not in (0, None)


def test_unknown_council_exits_one():
    assert cli.main(["show", "no-such-council"]) == 1


# ---- guided init + serve ----

def test_init_uses_defaults_on_eof(tmp_path, monkeypatch):
    # `eldercouncil init` is interactive; with no input (EOF) every prompt must fall back to a
    # sensible default and still complete a working install — not hang or crash.
    monkeypatch.setenv("COUNCIL_DIR", str(tmp_path / ".council"))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert cli.main(["init", "claude-code", "--dir", str(tmp_path)]) == 0
    assert (tmp_path / ".council" / "config.toml").exists()


def test_serve_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        cli.main(["serve", "--help"])
    assert exc.value.code == 0
