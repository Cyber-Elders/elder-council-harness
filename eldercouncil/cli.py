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
    mode = rec.get("mode", "")
    mode_label = {"advisory": "advisory · a human decides",
                  "action-gate": "action-gate · can block automatically"}.get(mode, mode)
    print(_c("1", f"\n  {rec.get('council')}  —  {mode_label}"))
    # Column widths sized to the actual data so long role names / verdicts (e.g.
    # 'Infrastructure / Application SME', 'recommend-with-guardrails') don't shove
    # the confidence column out of alignment.
    rows = rec.get("verdicts", [])
    rw = max(30, *(len(v.get("role", "")) for v in rows)) if rows else 30
    vw = max(16, *(len(v.get("vote", "")) for v in rows)) if rows else 16
    for v in rows:
        vc = _VERDICT_COLOR.get(v.get("vote"), "32")
        conf = v.get("confidence", "")
        vote = v.get("vote", "")
        sev = f"[{v['severity']}]" if v.get("severity") else ""
        # Pad on the PLAIN vote length, THEN colorize — ANSI codes must not be
        # counted in the column width (else colored output mis-aligns in a TTY).
        # Severity gets its own fixed-width slot so non-severity rows line up.
        vote_cell = _c(vc, vote) + " " * max(1, vw - len(vote))
        reason = v.get("reason", "")
        reason = (reason[:65].rstrip() + "…") if len(reason) > 66 else reason  # ellipsis = intentional cut, not a broken line
        print(f"    {v.get('role',''):<{rw}} {vote_cell}{sev:<11} ({conf:>4})  {reason}")
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
        # When nothing tripped, say so — a bare "allow" between two human-routing
        # lines otherwise reads as a contradiction to a non-technical reader.
        note = "" if tripped else _c("2", "  — no safety gate tripped; the council sets the routing")
        print(_c("1", f"  GATES ({gr.get('profile','?')}): {_c(gc, gres)}") + note
              + (f"  ⛔ HARD STOP" if gr.get("hard_stopped") else ""))
        for g in tripped:
            print(f"    ✗ {g['gate']:22} {g['result']:14} → {g.get('escalation','')}  ({', '.join(g['reasons'])})")
    disp = rec.get("disposition", "")
    dc = "31" if "block" in disp else ("33" if disp == "human" else "32")
    disp_legend = (" (the final call — a person decides)" if disp == "human"
                   else " (final — proceeds automatically)" if disp == "auto"
                   else " (final — action withheld)" if "block" in disp else "")
    print(_c("1", f"  DISPOSITION: {_c(dc, disp)}") + _c("2", disp_legend))
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
                "    together. Diversify your model lanes — see THREAT_MODEL.md.\n"))
        if args.orchestrate and not args.json:
            verdicts = rec.get("verdicts", [])
            unavail = [v for v in verdicts if v.get("vote") == "unavailable"]
            if verdicts and len(unavail) == len(verdicts):
                sys.stderr.write(_c("33",
                    "\n  hint: no model lanes resolved — run `eldercouncil models check` and pin a real\n"
                    "        model per lane in .council/council-models.json before --orchestrate.\n"))
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
        sys.stderr.write(_c("1",
            "\n  These are the deliberation tasks for your coding agent to run on your own models — "
            "not the verdict itself.\n"))
        sys.stderr.write(
            f"  • Just want to SEE a council decide right now (keyless)?   eldercouncil convene {c.id} --demo\n"
            "  • Inside your coding agent, you normally trigger this with the council's slash command.\n"
            "  • No agent / headless? add --orchestrate to run your own pinned models now "
            "(check them first: eldercouncil models check).\n\n")
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
        except json.JSONDecodeError as exc:
            # Fail closed: don't evaluate an empty action on malformed JSON.
            sys.stderr.write(f"invalid action JSON: {exc}\n")
            return 2
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
            except json.JSONDecodeError as exc:
                # Fail closed: malformed JSON must NOT evaluate as an empty (allowed) action.
                sys.stderr.write(f"invalid signals JSON: {exc}\n")
                return 2
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
    from .models import load_registry, resolve, unresolved, monoculture, inherits as _inherits, RegistryError
    try:
        reg = load_registry()
    except RegistryError as exc:
        print(exc); return 2
    if args.models_cmd == "list":
        print(f"registry {reg.version} ({reg.source})")
        for role, entry in sorted(reg.roles.items()):
            if entry.get("kind") == "tool":
                print(f"  {role:22} (tool — deterministic checks, no model)")
            else:
                print(f"  {role:22} frontier={entry.get('frontier')}  open={entry.get('open')}  local={entry.get('local')}")
        return 0
    if args.models_cmd == "check":
        from .config import load_config
        cfg_lane = load_config().lane          # check the lane THIS project actually uses
        miss = unresolved(reg)
        mono = monoculture(reg, cfg_lane)
        # How many lenses will inherit the host model on this lane (sentinel/null → inherit)?
        inheriting = sum(
            1 for rk, e in reg.roles.items()
            if e.get("kind") != "tool" and _inherits(reg, rk, cfg_lane)
        )
        print(f"configured lane: {cfg_lane}")
        if mono:
            # The whole premise is plural review — an all-one-provider council has
            # correlated blind spots. Warn, but don't fail (a user may intend it).
            print(_c("33", f"⚠ monoculture: every pinned lens on the '{cfg_lane}' lane maps to '{mono}'. "
                            f"The voices share one model's blind spots — the deterministic Tool lens and your "
                            f"final decision stay independent, but pin a different-family voice (esp. "
                            f"cross_family_critic) for real plural review. See THREAT_MODEL.md."))
        if cfg_lane in ("local", "open") and inheriting:
            # On a BYO/local lane, unpinned means "inherit your agent's own model" — that's the
            # intended setup (e.g. Claude Code on Ollama), not a misconfiguration. One model =
            # one set of blind spots, so still nudge toward a second voice.
            print(_c("36", f"✓ lane '{cfg_lane}': {inheriting} lens(es) inherit your agent's own model "
                           f"(BYO / on-device — nothing to pin). All on one model = one set of blind "
                           f"spots; add a second/different-family voice for genuine disagreement."))
            return 0
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


_IDES = ["claude-code", "opencode", "kiro", "cursor", "copilot"]


class _Parser(argparse.ArgumentParser):
    """Usage/parse errors exit 64 (EX_USAGE), NOT 2 — so a CI/hook script can tell a
    *policy* stop (exit 2 = blocked/escalated) from a *usage* mistake (bad flag/choice)."""
    def error(self, message: str):  # noqa: D401
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(64)


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="eldercouncil",
                description="Elder Council — local-first multi-model council harness for "
                            "high-stakes decisions: built for cyber, general enough for any "
                            "call too consequential to leave to one model alone.")
    sub = p.add_subparsers(dest="command", required=True)

    n = sub.add_parser("init", help="guided install (interactive)")
    n.add_argument("ide", nargs="?", choices=_IDES, help="target coding agent / IDE (prompted if omitted)")
    n.add_argument("--dir", help="project directory to install into (default: cwd)")
    n.set_defaults(func=cmd_init)

    i = sub.add_parser("install", help="wire councils into a harness")
    i.add_argument("ide", choices=_IDES, help="target coding agent / IDE to wire councils into")
    i.add_argument("--council", help="comma-separated council ids (default: all)")
    i.add_argument("--all", action="store_true", help="install all councils")
    i.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"],
                    help="model lane to resolve: frontier (hosted) / open (open-weight) / local (on-device)")
    i.add_argument("--tier", default="practitioner",
                   help="maturity tier written to .council/config.toml (explorer/practitioner/governed/operator)")
    i.add_argument("--profile", default="standard", choices=["lite", "standard", "regulated"])
    i.add_argument("--dir")
    i.set_defaults(func=cmd_install)

    sub.add_parser("list", help="list installed councils").set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="show a council's resolved roster")
    sh.add_argument("council", help="council id (see `eldercouncil list`)")
    sh.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"],
                    help="model lane to resolve: frontier (hosted) / open (open-weight) / local (on-device)")
    sh.set_defaults(func=cmd_show)

    cv = sub.add_parser("convene", help="run (--demo/--orchestrate) or preview a council")
    cv.add_argument("council", help="council id (see `eldercouncil list`)")
    cv.add_argument("--question", help="the decision under review (or pipe on stdin)")
    cv.add_argument("--demo", action="store_true", help="deterministic sample votes (keyless, CI-safe)")
    cv.add_argument("--scenario", default="default", choices=["default", "monoculture"],
                    help="'monoculture' shows the failure a council does NOT catch (shared blind spot)")
    cv.add_argument("--orchestrate", action="store_true", help="run with your own models ([orchestrator] extra)")
    cv.add_argument("--profile", default="standard", choices=["lite", "standard", "regulated"],
                    help="control-gate profile (default: standard)")
    cv.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"],
                    help="model lane to resolve: frontier (hosted) / open (open-weight) / local (on-device)")
    cv.add_argument("--json", action="store_true", help="emit the decision record as JSON")
    cv.add_argument("--no-audit", action="store_true", help="do not write an audit record")
    cv.set_defaults(func=cmd_convene)

    g = sub.add_parser("gate", help="pre-tool gate (hook target; reads stdin)")
    g.add_argument("ide", choices=["claude-code", "opencode", "kiro"], help="the hard-block IDE whose pre-tool payload is on stdin")
    g.set_defaults(func=cmd_gate)

    a = sub.add_parser("audit", help="post-tool audit (hook target; reads stdin)")
    a.add_argument("ide", choices=["claude-code", "opencode", "kiro"], help="the hard-block IDE whose post-tool payload is on stdin")
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
    msub.add_parser("check", help="flag unpinned (REPLACE_ME) lanes",
                    description="Flag unpinned (REPLACE_ME) model lanes. Exit 0 = all lanes pinned; "
                                "exit 2 = unpinned lanes remain (expected on a fresh BYO-LLM install — "
                                "pin real models in council-models.json); exit 1 = registry error.")
    mr = msub.add_parser("resolve", help="resolve a role key to a model")
    mr.add_argument("role_key")
    mr.add_argument("--lane", default="frontier", choices=["frontier", "open", "local"],
                    help="model lane to resolve: frontier (hosted) / open (open-weight) / local (on-device)")
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
