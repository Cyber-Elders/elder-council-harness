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


def test_demo_lane_note_only_on_explicit_lane(tmp_path, capsys, monkeypatch):
    # Regression: the "--lane has no effect with --demo" note must fire ONLY when the
    # user actually typed --lane. It used to fire on EVERY --demo (the project lane
    # always fills args.lane by then), which both mislabels the run AND poisons
    # `convene --demo 2>&1 | grep -q …` pipelines -> BrokenPipeError/exit 120 (the CI
    # break this test guards). Plain demo: silent. Explicit --lane demo: noted.
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    assert cli.main(["convene", "code-council", "--demo", "--no-audit", "--question", "x"]) == 0
    assert "no effect with --demo" not in capsys.readouterr().err
    assert cli.main(["convene", "code-council", "--demo", "--lane", "local", "--no-audit", "--question", "x"]) == 0
    assert "no effect with --demo" in capsys.readouterr().err


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


def test_gate_generic_action_target_payload(capsys, monkeypatch):
    # The DOCUMENTED generic verify form {"action":..,"target":..} must actually
    # exercise the gate on every hard-block IDE (it used to be silently dropped
    # and return a confident "allow" — a no-op verification).
    _stdin(monkeypatch, '{"action":"bash","target":"git push --force origin main"}')
    assert cli.main(["gate", "claude-code"]) == 0
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecision"] in ("ask", "deny")
    _stdin(monkeypatch, '{"action":"bash","target":"git push --force origin main"}')
    assert cli.main(["gate", "opencode"]) == 2
    _stdin(monkeypatch, '{"action":"bash","target":"git push --force origin main"}')
    assert cli.main(["gate", "kiro"]) == 2


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


# ---- convene --signals contract ----

def test_convene_signals_plumbed_and_recorded(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    rc = cli.main(["convene", "code-council", "--demo", "--json", "--no-audit", "--question", "x",
                   "--signals", '{"human_approver":"jane","rollback_plan":true}'])
    assert rc == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["approval"]["approver"] == "jane"           # asserted approval is recorded...
    assert "unverified" in rec["approval"]["status"]       # ...and honestly labeled


def test_convene_malformed_signals_fails_closed(tmp_path, capsys, monkeypatch):
    _install(tmp_path, monkeypatch)
    capsys.readouterr()
    rc = cli.main(["convene", "code-council", "--demo", "--no-audit", "--question", "x",
                   "--signals", '{not json'])
    assert rc == 2                                          # malformed must NOT become "no signals"
    rc = cli.main(["convene", "code-council", "--demo", "--no-audit", "--question", "x",
                   "--signals", '["a","list"]'])
    assert rc == 2                                          # a non-object is rejected too


def test_convene_defaults_to_configured_lane(tmp_path, capsys, monkeypatch):
    # A local-lane project's convene must resolve the LOCAL lane (inherit), not
    # silently fall back to frontier Claude tags.
    _install(tmp_path, monkeypatch, "claude-code", "--lane", "local")
    capsys.readouterr()
    assert cli.main(["convene", "code-council", "--no-audit", "--question", "x"]) == 0
    pack = json.loads(capsys.readouterr().out)
    models = {t["model"] for t in pack["tasks"]}
    assert models == {"inherit"}, models


def test_risk_gate_does_not_fail_open_on_alt_payload_schemas(monkeypatch):
    # A destructive command carried in a NON-{action,target} JSON object (e.g. the
    # harness's own {tool_name,tool_input}/{tool,args} hook payloads) must still
    # route conservatively — never score empty -> SOLO_ALLOW (fail-open).
    for payload in ('{"tool_name":"bash","tool_input":{"command":"rm -rf / --no-preserve-root --force"}}',
                    '{"tool":"bash","args":"rm -rf /prod --force"}',
                    '{"foo":"rm -rf / --force destroy production drop database"}'):
        assert cli.main(["risk-gate", payload]) == 2, payload
    # a benign object still proceeds
    assert cli.main(["risk-gate", '{"note":"read a file"}']) == 0
