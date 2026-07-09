# SPDX-License-Identifier: Apache-2.0
"""
Audit trail — hash-chained, tamper-evident decision capture.

Three artifacts under `.council/`:
  * audit.jsonl          — append-only hash chain (one compact line per decision;
                           each carries `prev` + `hash`). `verify()` walks it.
  * decisions/<ts>-<id>.json — the full, human-readable decision record
                               (risk, all verdicts, dissent, route).
  * dissent/<ts>-<id>.json   — the dissent alone (the proprietary learning signal:
                               where lenses systematically disagree over time).

IMPORTANT (honest scope): this is tamper-EVIDENT, not tamper-PROOF. The chain
binds the FULL record — each decision entry carries `record_sha256` over the
persisted `decisions/<id>.json`, and `verify()` re-hashes those files, so editing
a vote/reason/dissent (not just the index) is caught. What a local chain alone
CANNOT catch is a full rewrite or tail-truncation: anyone with write access to
`.council/` can drop the last entries (+ their records) or recompute the whole
chain + `audit.head`. The defense is an off-box anchor: record the head hash +
entry count (`eldercouncil verify` prints them) and re-run
`verify --expect-head <h> --expect-count <n>`. See THREAT_MODEL.md.

The decision itself is deterministic (a content-addressed id); the audit event
adds a wall-clock timestamp — the per-event uniqueness the decision_id omits.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from . import detectors, paths

_GENESIS = "EC-GENESIS"
_SCHEMA = "eldercouncil/decision/v1"


def _redact_on() -> bool:
    from .config import load_config
    return load_config().redact


def _redact_record(rec: dict) -> dict:
    """Mask secrets/PII in the free-text fields of a decision record before it
    touches disk. The gates DETECT these patterns; without this step the audit
    would persist the very value the gate flagged (see THREAT_MODEL residual
    risk 1). Applied at persistence time only — the in-memory record (and the
    decision_id, computed earlier) are untouched."""
    out = dict(rec)
    for key in ("question", "rationale"):
        out[key] = detectors.redact(out.get(key, ""))
    # Redact EVERY free-text field of each vote/dissent dict (role and model can
    # carry host-supplied secrets/PII via the MCP audit_log path), not just reason.
    out["verdicts"] = [_redact_deep(v) for v in out.get("verdicts", [])]
    out["dissent"] = [_redact_deep(v) for v in out.get("dissent", [])]
    out["context"] = _redact_deep(out.get("context") or {})
    if out.get("approval"):
        out["approval"] = dict(out["approval"], basis=detectors.redact(out["approval"].get("basis", "")))
    return out


def _redact_deep(value):
    """Redact every string in an arbitrarily nested structure (the MCP path
    accepts host-supplied context of any shape)."""
    if isinstance(value, str):
        return detectors.redact(value)
    if isinstance(value, dict):
        return {k: _redact_deep(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_deep(v) for v in value]
    return value


def _jsonl_path() -> Path:
    return paths.council_dir() / "audit.jsonl"


def _head_path() -> Path:
    return paths.council_dir() / "audit.head"


def _entry_hash(event_without_hash: dict) -> str:
    canonical = json.dumps(event_without_hash, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def _sha256_file(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def read_events(path: str | Path | None = None) -> list[dict]:
    """Read the hash-chain index (skips malformed lines)."""
    p = Path(path) if path else _jsonl_path()
    if not p.exists():
        return []
    events = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _read_head() -> str:
    # The jsonl tail is the SOURCE OF TRUTH for the chain head; `audit.head` is only
    # an advisory cache. Preferring the tail means a stale/failed-to-write head file
    # never breaks the next append's `prev` link.
    events = read_events()
    if events:
        return events[-1].get("hash", _GENESIS)
    hp = _head_path()
    if hp.exists():
        try:
            h = hp.read_text(encoding="utf-8").strip()
            if h:
                return h
        except OSError:
            pass
    return _GENESIS


def head_hash() -> str:
    """Current chain head. Record this externally (out of `.council/`) to detect
    a full-chain rewrite that local `verify()` alone cannot catch."""
    return _read_head()


def anchor_state() -> dict:
    """The off-box anchor: the current chain head + entry count + capture time.
    Store it OUTSIDE `.council/` (a git commit, syslog, a WORM path, a webhook) so a
    later full-chain rewrite that local `verify()` alone cannot catch becomes
    detectable via `verify --expect-head/--expect-count`. Read-only; it is NEVER
    called inside `record()`, so it can't slow or fork the chain during a decision.
    It does not make the log immutable — it stays tamper-evident, not tamper-proof."""
    return {"head": head_hash(), "count": len(read_events()),
            "ts": datetime.now(timezone.utc).isoformat()}


def decision_id(council_id: str, question: str, outcome, gate_result: str = "") -> str:
    """Deterministic, content-addressed id. Same inputs -> same id, offline.
    The gate overall result is part of the id so a gate-changed disposition gets a
    distinct id."""
    votes = getattr(outcome, "votes", []) or []
    sig = "|".join(f"{v.get('role')}:{v.get('vote')}" for v in votes)
    payload = (f"{council_id}|{question}|{getattr(outcome, 'verdict', '')}|"
               f"{getattr(outcome, 'route', '')}|{gate_result}|{sig}").encode()
    return "EC-" + hashlib.sha256(payload).hexdigest()[:12]


def _disposition(outcome, gate_report: dict | None) -> str:
    """The EFFECTIVE disposition = most restrictive of (council route, gates).
    A gate can withhold an action the council would have permitted."""
    council_auto = getattr(outcome, "route", None) == "auto"
    gate_result = (gate_report or {}).get("result", "allow")
    if (gate_report or {}).get("hard_stopped"):
        return "blocked (hard stop)"
    if gate_result in ("block", "human_required"):
        return "blocked by gate"
    if not council_auto:
        return "human"          # council itself routed to a human
    if gate_result == "escalate":
        return "human"          # gate escalates a council-permitted action
    return "auto"


def build_record(council_id: str, question: str, outcome, *, mode: str = "",
                 risk: dict | None = None, context: dict | None = None,
                 gate_report: dict | None = None, profile: str = "",
                 diversity: dict | None = None, approval: dict | None = None) -> dict:
    """Assemble the deterministic decision record (no timestamp — that is added
    only when persisted). This is what `convene` returns and the determinism
    check compares. `diversity` and `approval` are recorded verbatim and are NOT
    part of the decision_id inputs (ids stay stable across their introduction)."""
    did = decision_id(council_id, question, outcome, (gate_report or {}).get("result", ""))
    return {
        "schema": _SCHEMA,
        "council": council_id,
        "mode": mode,
        "profile": profile,
        "question": question,
        "risk": risk or {},
        "verdict": getattr(outcome, "verdict", None),
        "route": getattr(outcome, "route", None),
        "rationale": getattr(outcome, "rationale", ""),
        "verdicts": list(getattr(outcome, "votes", []) or []),
        "dissent": list(getattr(outcome, "dissent", []) or []),
        "gate_report": gate_report or {},
        "diversity": diversity or {},
        "approval": approval or {},
        "disposition": _disposition(outcome, gate_report),
        "decision_id": did,
        "context": context or {},
    }


def record(council_id: str, question: str, outcome, *, mode: str = "",
           risk: dict | None = None, context: dict | None = None,
           gate_report: dict | None = None, profile: str = "",
           diversity: dict | None = None, approval: dict | None = None,
           demo: bool = False) -> str:
    """Persist a decision: full record file + dissent file + chained index line.
    Returns the decision_id. `demo=True` marks the chain entry `kind:"demo"` so the
    summary excludes illustrative `--demo` runs from the real decision counts."""
    rec = build_record(council_id, question, outcome, mode=mode, risk=risk, context=context,
                       gate_report=gate_report, profile=profile,
                       diversity=diversity, approval=approval)
    did = rec["decision_id"]
    ts = datetime.now(timezone.utc)
    # SUB-second stamp: the decision_id is content-based (time-independent), so two
    # IDENTICAL decisions must NOT share a file. The chain appends one entry per
    # record() call and each entry binds its OWN record file — a shared/overwritten
    # file would desync verify() (a false "chain BROKEN") and break audit-summary
    # reconciliation. Uniquify on any residual same-microsecond collision.
    stamp = ts.strftime("%Y%m%dT%H%M%S_%f")

    # Redact secrets/PII at the persistence boundary (decision_id was computed
    # over the ORIGINAL record above, so redaction never changes an id).
    persisted = _redact_record(rec) if _redact_on() else rec

    decisions = paths.decisions_dir()
    decisions.mkdir(parents=True, exist_ok=True)
    full = dict(persisted, ts=ts.isoformat(), **({"demo": True} if demo else {}))
    fname = f"{stamp}-{did[3:11]}.json"
    record_path = decisions / fname
    _n = 1
    while record_path.exists():
        fname = f"{stamp}-{did[3:11]}-{_n}.json"
        record_path = decisions / fname
        _n += 1
    record_path.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")
    # Bind the FULL record's bytes into the chain (hash the persisted file, not the
    # in-memory string, so newline translation etc. can't desync verify()). This is
    # what makes the audit tamper-evident over every vote/reason/dissent, not just
    # the chain index — editing decisions/<id>.json now fails verify().
    record_sha = _sha256_file(record_path)

    if persisted["dissent"]:
        dissent = paths.dissent_dir()
        dissent.mkdir(parents=True, exist_ok=True)
        (dissent / fname).write_text(
            json.dumps({"decision_id": did, "council": council_id, "dissent": persisted["dissent"]},
                       indent=2, ensure_ascii=False), encoding="utf-8")

    _append_chain({
        "ts": ts.isoformat(),
        "kind": "demo" if demo else "decision",
        "decision_id": did,
        "council": council_id,
        "mode": mode,
        "profile": profile,
        "verdict": rec["verdict"],
        "route": rec["route"],
        "disposition": rec["disposition"],
        "gate_result": (gate_report or {}).get("result"),
        "score": (risk or {}).get("score"),
        "record": fname,
        "record_sha256": record_sha,
    })
    return did


@contextlib.contextmanager
def _chain_lock():
    """Best-effort cross-platform mutex around read-head -> append -> write-head,
    so parallel agent tool-use (the norm) cannot fork the chain and produce false
    'tamper' reports. Lockfile via O_CREAT|O_EXCL; spins briefly, then proceeds."""
    lock = paths.council_dir() / "audit.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    lock_unsupported = False
    for _ in range(200):  # ~2s max
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.01)
        except OSError:
            lock_unsupported = True
            break  # locking unsupported here — proceed best-effort
    if fd is None and not lock_unsupported:
        raise OSError(f"could not acquire audit lock after 200 retries: {lock}")
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            with contextlib.suppress(OSError):
                lock.unlink()


def _append_chain(core: dict) -> str:
    """Add prev+hash to a chain-entry core, append it to audit.jsonl, update the
    head. Shared by council decisions and lightweight gate events. Returns hash."""
    jl = _jsonl_path()
    jl.parent.mkdir(parents=True, exist_ok=True)
    with _chain_lock():
        event = dict(core, prev=_read_head())   # read tail + append, under the lock
        event["hash"] = _entry_hash(event)
        with jl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        try:
            _head_path().write_text(event["hash"], encoding="utf-8")
        except OSError:
            pass
    return event["hash"]


def record_gate(action: str, target: str, score: int, route: str, verdict: str,
                context: dict | None = None) -> None:
    """Append a lightweight gate event (a routing decision, not a council
    decision) to the same hash chain — a trail of what the risk gate saw.
    The pre-tool hook feeds raw command lines through here, so the same
    redaction that protects decision records applies to `action`/`target`."""
    if _redact_on():
        action = detectors.redact(action)
        target = detectors.redact(target or "")
        context = _redact_deep(context or {})
    _append_chain({
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "gate",
        "action": action,
        "target": (target or "")[:200],
        "score": score,
        "route": route,
        "verdict": verdict,
        "context": context or {},
    })


def verify(path: str | Path | None = None, *, expected_head: str | None = None,
           expected_count: int | None = None) -> dict:
    """Walk the chain and confirm integrity. Returns {ok, entries, broken_at, reason, head}.

    Three layers, from cheapest to strongest:
      1. Chain links + per-entry hash  — detects any edit/insert/reorder WITHIN a line.
      2. Bound decision records        — re-hashes each decisions/<id>.json and compares
                                         to `record_sha256`, so editing a vote/reason/dissent
                                         in the full record (not just the index) is caught.
      3. Off-box anchor — the ONLY thing that catches a full-chain rewrite, since an attacker
         with write access can recompute the local chain + head. `expected_head` is the sound
         anchor: it pins the exact chain tip, so ANY rewrite (including an in-place substance
         edit + recompute) fails. `expected_count` only catches truncation/appended entries —
         an in-place rewrite preserves the count, so it is NOT a substitute for `expected_head`.
         Record the head (and optionally count) off `.council/` — the CLI prints both.
    """
    events = read_events(path)
    decisions_dir = (Path(path).parent / "decisions") if path else paths.decisions_dir()
    expected_prev = _GENESIS
    for i, e in enumerate(events, start=1):
        stored = e.get("hash")
        if stored is None:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "entry missing hash", "head": expected_prev}
        recomputed = _entry_hash({k: v for k, v in e.items() if k != "hash"})
        if recomputed != stored:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "content hash mismatch (entry altered)", "head": expected_prev}
        if e.get("prev") != expected_prev:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "broken link (entry inserted/removed/reordered)", "head": expected_prev}
        # Substance binding: a decision/demo entry MUST carry its bound-record hash,
        # and the record's bytes must match. Requiring the field (not just checking
        # it when present) closes the strip attack — dropping `record_sha256` and
        # recomputing the chain would otherwise skip the substance check silently.
        kind = e.get("kind", "decision")
        rsha, rfile = e.get("record_sha256"), e.get("record")
        if kind in ("decision", "demo"):
            if not (rsha and rfile):
                return {"ok": False, "entries": len(events), "broken_at": i,
                        "reason": "decision entry is missing its bound-record hash "
                                  "(record_sha256/record stripped) — substance binding removed",
                        "head": expected_prev}
            fp = decisions_dir / rfile
            if not fp.exists():
                return {"ok": False, "entries": len(events), "broken_at": i,
                        "reason": f"decision record missing ({rfile}) — deleted or renamed",
                        "head": expected_prev}
            if _sha256_file(fp) != rsha:
                return {"ok": False, "entries": len(events), "broken_at": i,
                        "reason": f"decision record altered ({rfile}) — substance hash mismatch",
                        "head": expected_prev}
        expected_prev = stored
    head = events[-1]["hash"] if events else _GENESIS
    if expected_count is not None and len(events) != expected_count:
        return {"ok": False, "entries": len(events), "broken_at": None,
                "reason": f"entry count {len(events)} != expected {expected_count} "
                          f"(truncated or appended off-anchor)", "head": head}
    if expected_head is not None and head != expected_head:
        return {"ok": False, "entries": len(events), "broken_at": None,
                "reason": "chain head does not match the recorded off-box anchor "
                          "(full rewrite or tail-truncation)", "head": head}
    return {"ok": True, "entries": len(events), "broken_at": None,
            "reason": "chain intact", "head": head}


def read_decisions() -> list[dict]:
    """Read all full decision records (sorted by filename = chronological)."""
    d = paths.decisions_dir()
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def summary(path: str | Path | None = None) -> dict:
    """Aggregate the decision log: verdict distribution, routes, dissent rate.
    A simple log utility — not a performance-KPI framework."""
    events = read_events(path)
    # Illustrative --demo runs (kind:"demo") and lightweight gate events are not real
    # council decisions — exclude them so the summary counts deliberated decisions only.
    decisions_only = [e for e in events if e.get("kind", "decision") == "decision"]
    demo_runs = sum(1 for e in events if e.get("kind") == "demo")
    by_verdict: dict[str, int] = {}
    by_route: dict[str, int] = {}
    by_council: dict[str, int] = {}
    for e in decisions_only:
        by_verdict[e.get("verdict", "?")] = by_verdict.get(e.get("verdict", "?"), 0) + 1
        by_route[e.get("route", "?")] = by_route.get(e.get("route", "?"), 0) + 1
        by_council[e.get("council", "?")] = by_council.get(e.get("council", "?"), 0) + 1
    decisions = [d for d in read_decisions() if not d.get("demo")]
    with_dissent = sum(1 for d in decisions if d.get("dissent"))
    # WHY decisions route to a human — an EXHAUSTIVE breakdown (the buckets sum to the
    # human-routed count, incl. an `other` residual), keyed on the deterministic rationale
    # from consensus.py. A persistently high tie-rate is a signal to investigate the
    # QUESTION (ambiguous / underspecified) — NOT a reason to tune lenses toward agreement,
    # which collapses the diversity the council exists for. See docs/METHODOLOGY.md
    # "Reading a high tie-rate".
    def _rat(d):
        return str(d.get("rationale", ""))
    _HUMAN_REASONS = (
        ("ties", lambda r: r.startswith("tie (")),
        ("critical", lambda r: "rated this critical" in r.lower()),
        ("escalation", lambda r: "voted to escalate" in r),
        ("human_reserved", lambda r: "human-accountability decision" in r),
        ("advisory", lambda r: "advisory council" in r),
        ("blocking_verdict", lambda r: "action withheld" in r),
        ("blocking_dissent", lambda r: "dissented to stop" in r),
        ("low_confidence", lambda r: "low confidence" in r),
        ("did_not_convene", lambda r: "did not convene" in r),
    )
    human_routing = {name: 0 for name, _ in _HUMAN_REASONS}
    human_routing["other"] = 0
    for d in (x for x in decisions if str(x.get("route")) == "human"):
        r = _rat(d)
        for name, pred in _HUMAN_REASONS:
            if pred(r):
                human_routing[name] += 1
                break
        else:
            human_routing["other"] += 1
    n = max(1, len(decisions))
    return {
        "total_decisions": len(decisions_only),
        "demo_runs_excluded": demo_runs,
        "by_verdict": by_verdict,
        "by_route": by_route,
        "by_council": by_council,
        "decisions_with_dissent": with_dissent,
        "tie_rate": round(human_routing["ties"] / n, 3),
        "human_routing": human_routing,   # sums to the human-routed count (see `guidance`)
        "guidance": "docs/METHODOLOGY.md — Reading a high tie-rate",
    }
