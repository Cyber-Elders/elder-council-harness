# SPDX-License-Identifier: Apache-2.0
"""End-to-end CLI journeys via the real `python -m eldercouncil.cli` entry point,
including the Windows cp1252 console regression."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args, cwd, extra_env=None, stdin=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["NO_COLOR"] = "1"
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, "-m", "eldercouncil.cli", *args],
                          cwd=str(cwd), env=env, input=stdin,
                          capture_output=True, text=True)


def test_version_list_show(tmp_path):
    assert _run(["version"], tmp_path).stdout.strip() == "0.1.0"
    out = _run(["list"], tmp_path).stdout
    assert "code-council" in out and "cyber-risk" in out
    assert "Code Council" in _run(["show", "code-council"], tmp_path).stdout


def test_install_and_convene_journey(tmp_path):
    r = _run(["install", "claude-code", "--dir", str(tmp_path)], tmp_path)
    assert r.returncode == 0
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert (tmp_path / ".council" / "council-models.json").exists()

    env = {"COUNCIL_DIR": str(tmp_path / ".council")}
    # code-council demo -> block on the CRITICAL finding. --demo is an illustration,
    # so it exits 0 (not a gate); the verdict + dissent still show in the output.
    r = _run(["convene", "code-council", "--demo", "--question", "merge a hardcoded secret"], tmp_path, env)
    assert r.returncode == 0, r.stdout
    assert "block" in r.stdout and "dissent" in r.stdout

    # audit chain intact afterwards
    r = _run(["verify"], tmp_path, env)
    assert r.returncode == 0 and "intact" in r.stdout


def test_gate_journey(tmp_path):
    r = _run(["gate", "opencode"], tmp_path, stdin='{"tool":"bash","args":{"command":"ls -la"}}')
    assert r.returncode == 0 and "allow" in r.stdout
    r = _run(["gate", "opencode"], tmp_path, stdin='{"tool":"bash","args":{"command":"git push --force origin main"}}')
    assert r.returncode == 2 and "ask" in r.stdout


def test_empty_stdin_gate_fails_safe(tmp_path):
    # An empty pre-tool event must NOT be a silent allow.
    r = _run(["gate", "opencode"], tmp_path, stdin="")
    assert r.returncode == 2


def test_monoculture_demo_warns(tmp_path):
    env = {"COUNCIL_DIR": str(tmp_path / ".council")}
    r = _run(["convene", "code-council", "--demo", "--scenario", "monoculture",
              "--question", "ship it", "--no-audit"], tmp_path, env)
    assert r.returncode == 0
    assert "does NOT catch" in r.stderr  # the honest warning banner


def test_models_check_journey(tmp_path):
    r = _run(["models", "check"], tmp_path)
    assert r.returncode == 2  # cross-family/open/local lanes ship unpinned by design
    assert "configured lane: frontier" in r.stdout


def test_models_check_honours_local_lane(tmp_path):
    # A --lane local project runs every lens on the host model (inherit) — `models check`
    # must reflect that as a healthy BYO/on-device setup (exit 0), not "✗ unpinned" (exit 2).
    _run(["install", "claude-code", "--council", "code-council", "--lane", "local",
          "--dir", str(tmp_path)], tmp_path)
    env = {"COUNCIL_DIR": str(tmp_path / ".council")}
    r = _run(["models", "check"], tmp_path, env)
    assert r.returncode == 0
    assert "configured lane: local" in r.stdout
    assert "inherit your agent's own model" in r.stdout


def test_cp1252_console_does_not_crash(tmp_path):
    """The Windows console-encoding trap: printing verdict glyphs (✓ ✗ →) under
    cp1252 must not raise UnicodeEncodeError (cli._force_utf8 reconfigures stdout)."""
    env = {"PYTHONIOENCODING": "cp1252", "COUNCIL_DIR": str(tmp_path / ".council")}
    for args in (["verify"], ["models", "check"],
                 ["convene", "supply-chain", "--demo", "--question", "x", "--no-audit"]):
        r = _run(args, tmp_path, env)
        assert "UnicodeEncodeError" not in (r.stderr or ""), (args, r.stderr)
