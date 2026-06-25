# SPDX-License-Identifier: Apache-2.0
"""
eldercouncil CLI.

  eldercouncil init [<ide>]                 guided install wizard
  eldercouncil install <ide> [--council …]  wire councils into a harness
  eldercouncil list                         list installed councils
  eldercouncil show <council>               show a council's resolved roster
  eldercouncil convene <council> [--demo]   run / preview a council deliberation
  eldercouncil gate <ide>                   pre-tool gate (hook target; stdin)
  eldercouncil audit <ide>                  post-tool audit (hook target; stdin)
  eldercouncil risk-gate [<action>]         score + route an action (1-25)
  eldercouncil models {list,check,resolve}  model-registry management
  eldercouncil verify                       verify the audit hash-chain
  eldercouncil audit-summary                aggregate the decision log
  eldercouncil serve                        run the advisory MCP server ([mcp])
  eldercouncil version
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__


# --- small ANSI helper (respects NO_COLOR / non-tty) -----------------------
def _c(code: str, text: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


_VERDICT_COLOR = {"block": "31", "reject": "31", "escalate": "33", "defer": "33",
                  "request-changes": "33", "accept": "36"}


def _read(arg: str | None) -> str:
    return (arg if arg else sys.stdin.read()).strip()


# --------------------------------------------------------------------------
def cmd_init(args) -> int:
    from .install import guided_init
    return guided_init(ide=args.ide, target_dir=args.dir)


def cmd_install(args) -> int:
    from .install import install
    councils = args.council.split(",") if args.council else None
    return install(args.ide, councils=[c.strip() for c in councils] if councils else None,
                   target_dir=args.dir, lane=args.lane, tier=args.tier, all_councils=args.all,
                   profile=args.profile)


def cmd_list(args) -> int:
    from .catalog import list_councils
    for c in list_councils():
        print(f"  {c.id:24} {c.mode:12} {len(c.roles)} lenses  — {c.name}")
    return 0


def cmd_show(args) -> int:
    from .catalog import get_council
    from .models import load_registry, resolve, RegistryError, UnpinnedError
    from .schema import SchemaError
    try:
        c = get_council(args.council)
        reg = load_registry()
    except (SchemaError, RegistryError) as exc:
        print(exc); return 1
    print(_c("1", f"{c.name}  [{c.id}]"))
    print(f"  mode: {c.mode}   outcomes: {', '.join(c.decision_outcomes)}")
    print(f"  purpose: {c.purpose.strip()}")
    print("  lenses:")
    for r in c.roles:
        try:
            model = resolve(reg, r.role_key, r.variant or args.lane)
        except UnpinnedError:
            model = _c("33", "UNPINNED (REPLACE_ME)")
        except RegistryError:
            model = _c("31", "UNKNOWN ROLE KEY")
        star = " *arbitrator" if r.arbitrator else (" (tool)" if r.is_tool else "")
        print(f"    - {r.name:32} {r.role_key:22} {args.lane}: {model}{star}")
    print(f"  fail-closed: {c.fail_closed.strip()}")
    return 0


def _print_decision(rec: dict) -> None:
    verdict = rec.get("verdict", "?")
    color = _VERDICT_COLOR.get(verdict, "32")
    print(_c("1", f"\n  {rec.get('council')}  —  {rec.get('mode')}"))
    for v in rec.get("verdicts", []):
        vc = _VERDICT_COLOR.get(v.get("vote"), "32")
        conf = v.get("confidence", "")
        vote = v.get("vote", "")
        sev = f"[{v['severity']}]" if v.get("severity") else ""
        # Pad on the PLAIN vote length, THEN colorize — ANSI codes must not be
        # counted in the column width (else colored output mis-aligns in a TTY).
        # Severity gets its own fixed-width slot so non-severity rows line up.
        vote_cell = _c(vc, vote) + " " * max(1, 16 - len(vote))
        print(f"    {v.get('role',''):<30} {vote_cell}{sev:<11} ({conf:>4})  {v.get('reason','')[:66]}")
    print(_c("1", f"\n  COUNCIL VERDICT: {_c(color, verdict)}   → route: {_c('36', rec.get('route','?'))}"))
    print(f"  {rec.get('rationale','')}")
    if rec.get("dissent"):
        print(_c("33", f"  dissent preserved: {len(rec['dissent'])} lens(es) disagreed"))
    gr = rec.get("gate_report") or {}
    if gr:
        tripped = gr.get("gates", [])
        gres = gr.get("result", "allow")
        gc = _VERDICT_COLOR.get("block" if gres in ("block", "human_required") else
                                "escalate" if gres == "escalate" else "merge", "32")
        print(_c("1", f"  GATES ({gr.get('profile','?')}): {_c(gc, gres)}")
              + (f"  ⛔ HARD STOP" if gr.get("hard_stopped") else ""))
        for g in tripped:
            print(f"    ✗ {g['gate']:22} {g['result']:14} → {g.get('escalation','')}  ({', '.join(g['reasons'])})")
    disp = rec.get("disposition", "")
    dc = "31" if "block" in disp else ("33" if disp == "human" else "32")
    print(_c("1", f"  DISPOSITION: {_c(dc, disp)}"))
    print(f"  decision {rec.get('decision_id')}\n")


def cmd_convene(args) -> int:
    from .catalog import get_council
    from .convene import build_review
    from .models import load_registry, RegistryError
    from .schema import SchemaError
    from . import engine
    try:
        c = get_council(args.council)
        reg = load_registry()
    except (SchemaError, RegistryError) as exc:
        print(exc); return 1
    question = _read(args.question) or f"(no decision text supplied for {c.id})"

    if args.demo or args.orchestrate:
        try:
            if args.orchestrate:
                from .orchestrator import get_runner
                review = build_review(c, question, reg, args.lane)
                votes = get_runner()(review)
            else:
                votes = engine.demo_votes(c, scenario=args.scenario)
            rec = engine.convene_with_votes(c, question, votes, reg, lane=args.lane,
                                            do_audit=not args.no_audit, profile=args.profile)
        except RegistryError as exc:
            print(exc); return 1
        if args.json:
            print(json.dumps(rec, indent=2))
        else:
            _print_decision(rec)
        if args.scenario == "monoculture":
            sys.stderr.write(_c("33",
                "\n  ⚠ This is the failure a council does NOT catch: when your lenses share a\n"
                "    blind spot (e.g. all one model/provider), they can be confidently wrong\n"
                "    together. Diversify your model lanes — see docs/THREAT_MODEL.md.\n"))
        # `--demo` is an illustration, not a gate → always exit 0. Real runs
        # (`--orchestrate`) gate on the DISPOSITION (council route ∧ gate result).
        if args.demo:
            return 0
        return 0 if rec.get("disposition") == "auto" else 2

    # default (no --demo/--orchestrate): emit the BYO-LLM deliberation tasks for
    # the host agent's own runtime to run.
    try:
        review = build_review(c, question, reg, args.lane)
    except RegistryError as exc:
        print(exc); return 1
    if sys.stdout.isatty():
        sys.stderr.write(
            "# preview: the BYO-LLM tasks for your agent to run. Add --demo to see a sample\n"
            "# verdict (keyless), or --orchestrate to run your own models.\n")
    print(json.dumps(review, indent=2))
    return 0


def cmd_gate(args) -> int:
    from .harness import run_gate
    return run_gate(args.ide, sys.stdin.read())


def cmd_audit(args) -> int:
    from .harness import run_audit
    return run_audit(args.ide, sys.stdin.read())


def cmd_risk_gate(args) -> int:
    from .risk_gate import assess
    raw = _read(args.action)
    action, target = raw, ""
    if raw.startswith("{"):
        try:
            d = json.loads(raw)
            action, target = d.get("action", ""), d.get("target", "")
        except json.JSONDecodeError:
            pass
    rs = assess(f"{action} {target}".strip())
    print(json.dumps({"score": rs.score, "level": rs.level, "route": rs.route, "reasoning": rs.reasoning}))
    return 0 if rs.route == "SOLO_ALLOW" else 2


def cmd_gates(args) -> int:
    from . import gates
    from .gates import GatePolicyError
    if args.gates_cmd == "list":
        try:
            policy = gates.load_policy()
        except GatePolicyError as exc:
            print(exc); return 2
        for prof, spec in policy.get("profiles", {}).items():
            eff, controls = gates._profile_gates(policy, prof)
            inh = spec.get("inherits")
            print(f"  {prof:10} {len(eff)} gates"
                  + (f" (inherits {inh})" if inh else "")
                  + (f" + controls: {', '.join(controls)}" if controls else ""))
        print("  always-on (every profile): " + ", ".join(policy.get("always_on", [])) + "  [hard stop]")
        return 0
    if args.gates_cmd == "check":
        raw = _read(args.signals)
        signals, action = {}, ""
        if raw.startswith("{"):
            try:
                d = json.loads(raw)
                signals = d.get("signals", d)
                action = d.get("action", "")
            except json.JSONDecodeError:
                pass
        else:
            action = raw
        try:
            report = gates.evaluate(args.profile, signals, action=action)
        except GatePolicyError as exc:
            print(exc); return 2
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(_c("1", f"gates ({report.profile}): {report.result}")
                  + ("  ⛔ HARD STOP" if report.hard_stopped else ""))
            for o in report.outcomes:
                print(f"  ✗ {o.gate:22} {o.result:14} → {o.escalation}  ({', '.join(o.reasons)})")
            if not report.outcomes:
                print("  ✓ all gates passed")
        return 0 if report.permits_action() else 2
    return 1


def cmd_models(args) -> int:
    from .models import load_registry, resolve, unresolved, monoculture, RegistryError
    try:
        reg = load_registry()
    except RegistryError as exc:
        print(exc); return 2
    if args.models_cmd == "list":
        print(f"registry {reg.version} ({reg.source})")
        for role, entry in sorted(reg.roles.items()):
            print(f"  {role:22} frontier={entry.get('frontier')}  open={entry.get('open')}  local={entry.get('local')}")
        return 0
    if args.models_cmd == "check":
        miss = unresolved(reg)
        mono = monoculture(reg, "frontier")
        if mono:
            # The whole premise is plural review — an all-one-provider council has
            # correlated blind spots. Warn, but don't fail (a user may intend it).
            print(_c("33", f"⚠ monoculture: every resolvable frontier lens maps to '{mono}'. "
                            f"Diversify (esp. cross_family_critic) — see docs/THREAT_MODEL.md."))
        if not miss:
            print("✓ all model lanes are pinned")
            return 0
        print(f"✗ {len(miss)} unpinned lane(s) — pin a real model in {reg.source}:")
        for m in miss:
            print(f"    {m}")
        return 2
    if args.models_cmd == "resolve":
        try:
            print(resolve(reg, args.role_key, args.lane))
            return 0
        except RegistryError as exc:
            print(exc); return 2
    return 1


def cmd_verify(args) -> int:
    from .audit import head_hash, verify
    r = verify(args.path)
    if r["ok"]:
        print(f"✓ audit chain intact — {r['entries']} entr{'y' if r['entries']==1 else 'ies'}")
        print(f"  head: {head_hash()}")
        print("  (record the head externally — a full local rewrite is not detectable alone; see THREAT_MODEL.md)")
        return 0
    print(f"✗ audit chain BROKEN at entry {r['broken_at']} of {r['entries']}: {r['reason']}")
    return 2


def cmd_audit_summary(args) -> int:
    from .audit import summary
    print(json.dumps(summary(args.path), indent=2))
    return 0


def cmd_serve(args) -> int:
    try:
        from .server import run
    except ImportError:
        sys.stderr.write("MCP server requires the [mcp] extra: pip install 'eldercouncil[mcp]'\n")
        return 1
    run()
    return 0


def cmd_version(args) -> int:
    print(__version__)
    return 0


_IDES = ["claude-code", "opencode", "kiro", "cursor"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eldercouncil",
                                description="Elder Council — local-first multi-model council harness for high-stakes cyber decisions.")
    sub = p.add_subparsers(dest="command", required=True)

    n = sub.add_parser("init", help="guided install (interactive)")
    n.add_argument("ide", nargs="?", choices=_IDES)
    n.add_argument("--dir")
    n.set_defaults(func=cmd_init)

    i = sub.add_parser("install", help="wire councils into a harness")
    i.add_argument("ide", choices=_IDES)
    i.add_argument("--council", help="comma-separated council ids (default: all)")
    i.add_argument("--all", action="store_true", help="install all councils")
    i.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"])
    i.add_argument("--tier", default="practitioner")
    i.add_argument("--profile", default="standard", choices=["lite", "standard", "regulated"])
    i.add_argument("--dir")
    i.set_defaults(func=cmd_install)

    sub.add_parser("list", help="list installed councils").set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="show a council's resolved roster")
    sh.add_argument("council")
    sh.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"])
    sh.set_defaults(func=cmd_show)

    cv = sub.add_parser("convene", help="run (--demo/--orchestrate) or preview a council")
    cv.add_argument("council")
    cv.add_argument("--question", help="the decision under review (or pipe on stdin)")
    cv.add_argument("--demo", action="store_true", help="deterministic sample votes (keyless, CI-safe)")
    cv.add_argument("--scenario", default="default", choices=["default", "monoculture"],
                    help="'monoculture' shows the failure a council does NOT catch (shared blind spot)")
    cv.add_argument("--orchestrate", action="store_true", help="run with your own models ([orchestrator] extra)")
    cv.add_argument("--profile", default="standard", choices=["lite", "standard", "regulated"],
                    help="control-gate profile (default: standard)")
    cv.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"])
    cv.add_argument("--json", action="store_true", help="emit the decision record as JSON")
    cv.add_argument("--no-audit", action="store_true", help="do not write an audit record")
    cv.set_defaults(func=cmd_convene)

    g = sub.add_parser("gate", help="pre-tool gate (hook target; reads stdin)")
    g.add_argument("ide", choices=["claude-code", "opencode", "kiro"])
    g.set_defaults(func=cmd_gate)

    a = sub.add_parser("audit", help="post-tool audit (hook target; reads stdin)")
    a.add_argument("ide", choices=["claude-code", "opencode", "kiro"])
    a.set_defaults(func=cmd_audit)

    rg = sub.add_parser("risk-gate", help="score + route an action (1-25)")
    rg.add_argument("action", nargs="?", help="action string or {\"action\":..,\"target\":..} (or stdin)")
    rg.set_defaults(func=cmd_risk_gate)

    gt = sub.add_parser("gates", help="control-gate policy + evaluation")
    gtsub = gt.add_subparsers(dest="gates_cmd", required=True)
    gtsub.add_parser("list", help="show profiles + gates")
    gc = gtsub.add_parser("check", help="evaluate the gates over a signals JSON / action")
    gc.add_argument("signals", nargs="?", help='{"action":..,"signals":{..}} or an action string (or stdin)')
    gc.add_argument("--profile", default="standard", choices=["lite", "standard", "regulated"])
    gc.add_argument("--json", action="store_true")
    gt.set_defaults(func=cmd_gates)

    m = sub.add_parser("models", help="model-registry management")
    msub = m.add_subparsers(dest="models_cmd", required=True)
    msub.add_parser("list", help="show the registry")
    msub.add_parser("check", help="flag unpinned (REPLACE_ME) lanes")
    mr = msub.add_parser("resolve", help="resolve a role key to a model")
    mr.add_argument("role_key")
    mr.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"])
    m.set_defaults(func=cmd_models)

    vf = sub.add_parser("verify", help="verify the audit hash-chain")
    vf.add_argument("--path")
    vf.set_defaults(func=cmd_verify)

    s = sub.add_parser("audit-summary", help="aggregate the decision log")
    s.add_argument("--path")
    s.set_defaults(func=cmd_audit_summary)

    sub.add_parser("serve", help="run the advisory MCP server").set_defaults(func=cmd_serve)
    sub.add_parser("version", help="print version").set_defaults(func=cmd_version)
    return p


def _force_utf8() -> None:
    """Windows consoles default to cp1252, which can't encode the verdict glyphs
    (✓ ✗ → ·) — printing them would raise UnicodeEncodeError and crash the CLI."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
