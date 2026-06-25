# SPDX-License-Identifier: Apache-2.0
"""
Agentic UAT runner.

For each scenario: scaffold a throwaway project, `eldercouncil install <ide>`,
drive the scenario through the agent, then assert the agentic-loop invariants
over `.council/decisions/`. Asserts structural invariants (which council
convened, the verdict CLASS, the route, dissent present) — never exact text,
because LLM output is non-deterministic.

Modes:
  mock  — keyless, CI-safe; convenes via `eldercouncil convene --demo`. Exercises
          the real install -> convene -> audit -> assert loop deterministically.
  real  — drives a headless coding agent (uat/agentic/drivers/<ide>); needs a
          CI-scoped key. Falls back to mock if the agent/key is unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "_results"


def _load_scenarios(which: str) -> list[dict]:
    specs = []
    for sd in sorted((HERE / "scenarios").glob("*/scenario.json")):
        spec = json.loads(sd.read_text(encoding="utf-8"))
        specs.append(spec)
    if which and which != "all":
        specs = [s for s in specs if s["council"] == which]
    return specs


def _cli(args, cwd, env):
    e = dict(os.environ); e["PYTHONPATH"] = str(ROOT) + os.pathsep + e.get("PYTHONPATH", ""); e["NO_COLOR"] = "1"
    e.update(env)
    return subprocess.run([sys.executable, "-m", "eldercouncil.cli", *args],
                          cwd=str(cwd), env=e, capture_output=True, text=True)


def _drive(mode: str, ide: str, spec: dict, project: Path) -> None:
    env = {"COUNCIL_DIR": str(project / ".council")}
    if mode == "real":
        try:
            from drivers import load_driver  # type: ignore
            load_driver(ide).drive(spec, project, env)
            return
        except Exception as exc:  # noqa: BLE001 — real driver unavailable -> fall back to mock
            print(f"  real driver unavailable ({exc}); falling back to mock")
    # mock: the agent convenes the council (deterministic sample votes)
    _cli(["convene", spec["council"], "--demo", "--question", spec["question"]], project, env)


def run(scenario: str, ide: str, mode: str) -> int:
    sys.path.insert(0, str(HERE))
    from assertions import check  # local import after path setup

    RESULTS.mkdir(parents=True, exist_ok=True)
    specs = _load_scenarios(scenario)
    if not specs:
        print(f"no scenarios matched {scenario!r}"); return 1
    failures = 0
    for spec in specs:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            inst = _cli(["install", ide, "--council", spec["council"], "--dir", str(project)], project, {})
            if inst.returncode != 0:
                print(f"✗ {spec['council']}: install failed\n{inst.stdout}\n{inst.stderr}"); failures += 1; continue
            _drive(mode, ide, spec, project)
            ok, detail = check(spec, project / ".council")
            (RESULTS / f"{spec['council']}.json").write_text(
                json.dumps({"scenario": spec["council"], "ide": ide, "mode": mode, "ok": ok, "detail": detail},
                           indent=2), encoding="utf-8")
            print(f"{'✓' if ok else '✗'} {spec['council']:24} {detail}")
            failures += 0 if ok else 1
    print(f"\n{len(specs) - failures}/{len(specs)} agentic scenarios passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="all")
    p.add_argument("--ide", default="claude-code")
    p.add_argument("--mode", default="mock", choices=["mock", "real"])
    a = p.parse_args()
    raise SystemExit(run(a.scenario, a.ide, a.mode))
