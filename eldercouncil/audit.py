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

IMPORTANT (honest scope): this is tamper-EVIDENT against careless edits, not
tamper-PROOF. Anyone with write access to `.council/` can delete an entry and
recompute the whole chain + `audit.head`, and `verify()` would then pass. There
is no external anchor. To detect a full rewrite, record the head hash off-box
(`eldercouncil verify` prints it). See THREAT_MODEL.md.

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

from . import paths

_GENESIS = "EC-GENESIS"
_SCHEMA = "eldercouncil/decision/v1"


def _jsonl_path() -> Path:
    return paths.council_dir() / "audit.jsonl"


def _head_path() -> Path:
    return paths.council_dir() / "audit.head"


def _entry_hash(event_without_hash: dict) -> str:
    canonical = json.dumps(event_without_hash, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


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
                 gate_report: dict | None = None, profile: str = "") -> dict:
    """Assemble the deterministic decision record (no timestamp — that is added
    only when persisted). This is what `convene` returns and the determinism
    check compares."""
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
        "disposition": _disposition(outcome, gate_report),
        "decision_id": did,
        "context": context or {},
    }


def record(council_id: str, question: str, outcome, *, mode: str = "",
           risk: dict | None = None, context: dict | None = None,
           gate_report: dict | None = None, profile: str = "") -> str:
    """Persist a decision: full record file + dissent file + chained index line.
    Returns the decision_id."""
    rec = build_record(council_id, question, outcome, mode=mode, risk=risk, context=context,
                       gate_report=gate_report, profile=profile)
    did = rec["decision_id"]
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%dT%H%M%S")
    fname = f"{stamp}-{did[3:11]}.json"

    decisions = paths.decisions_dir()
    decisions.mkdir(parents=True, exist_ok=True)
    full = dict(rec, ts=ts.isoformat())
    (decisions / fname).write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")

    if rec["dissent"]:
        dissent = paths.dissent_dir()
        dissent.mkdir(parents=True, exist_ok=True)
        (dissent / fname).write_text(
            json.dumps({"decision_id": did, "council": council_id, "dissent": rec["dissent"]},
                       indent=2, ensure_ascii=False), encoding="utf-8")

    _append_chain({
        "ts": ts.isoformat(),
        "kind": "decision",
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
    for _ in range(200):  # ~2s max
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(0.01)
        except OSError:
            break  # locking unsupported here — proceed best-effort
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
    decision) to the same hash chain — a trail of what the risk gate saw."""
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


def verify(path: str | Path | None = None) -> dict:
    """Walk the chain and confirm integrity.
    Returns {ok, entries, broken_at, reason}."""
    events = read_events(path)
    expected_prev = _GENESIS
    for i, e in enumerate(events, start=1):
        stored = e.get("hash")
        if stored is None:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "entry missing hash"}
        recomputed = _entry_hash({k: v for k, v in e.items() if k != "hash"})
        if recomputed != stored:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "content hash mismatch (entry altered)"}
        if e.get("prev") != expected_prev:
            return {"ok": False, "entries": len(events), "broken_at": i,
                    "reason": "broken link (entry inserted/removed/reordered)"}
        expected_prev = stored
    return {"ok": True, "entries": len(events), "broken_at": None, "reason": "chain intact"}


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
    by_verdict: dict[str, int] = {}
    by_route: dict[str, int] = {}
    by_council: dict[str, int] = {}
    for e in events:
        by_verdict[e.get("verdict", "?")] = by_verdict.get(e.get("verdict", "?"), 0) + 1
        by_route[e.get("route", "?")] = by_route.get(e.get("route", "?"), 0) + 1
        by_council[e.get("council", "?")] = by_council.get(e.get("council", "?"), 0) + 1
    decisions = read_decisions()
    with_dissent = sum(1 for d in decisions if d.get("dissent"))
    return {
        "total_decisions": len(events),
        "by_verdict": by_verdict,
        "by_route": by_route,
        "by_council": by_council,
        "decisions_with_dissent": with_dissent,
    }
