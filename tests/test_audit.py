# SPDX-License-Identifier: Apache-2.0
"""Audit — hash chain, tamper-evidence (not -proof), deterministic decision id."""

import json

from eldercouncil import audit
from eldercouncil.consensus import tally
from conftest import mkcouncil, votes


def _record(council_dir, council, q):
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)), council)
    return audit.record(council.id, q, o, mode=council.mode)


def test_chain_intact_after_appends(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    _record(council_dir, c, "q1")
    _record(council_dir, c, "q2")
    r = audit.verify()
    assert r["ok"] and r["entries"] == 2


def test_decision_id_is_deterministic(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)), c)
    id1 = audit.decision_id(c.id, "same question", o)
    id2 = audit.decision_id(c.id, "same question", o)
    assert id1 == id2 and id1.startswith("EC-")


def test_records_and_dissent_written(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("block", 0.9), ("merge", 0.9)), c)
    audit.record(c.id, "q", o, mode=c.mode)
    decisions = list((council_dir / "decisions").glob("*.json"))
    dissent = list((council_dir / "dissent").glob("*.json"))
    assert len(decisions) == 1 and len(dissent) == 1  # one lens dissented


def test_mid_entry_tamper_detected(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    _record(council_dir, c, "q1")
    _record(council_dir, c, "q2")
    p = council_dir / "audit.jsonl"
    lines = p.read_text().splitlines()
    e = json.loads(lines[0]); e["verdict"] = "tampered"; lines[0] = json.dumps(e)
    p.write_text("\n".join(lines) + "\n")
    r = audit.verify()
    assert not r["ok"] and r["broken_at"] == 1


def test_full_rewrite_is_NOT_detected_tamper_evident_not_proof(council_dir):
    # Honest scope: an attacker who recomputes the whole chain passes verify().
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    _record(council_dir, c, "real decision we want to hide")
    # Rewrite from genesis with a fabricated, internally-consistent chain:
    p = council_dir / "audit.jsonl"
    forged = {"ts": "2026-01-01T00:00:00+00:00", "kind": "decision", "decision_id": "EC-forged",
              "council": "stub", "verdict": "merge", "route": "auto", "prev": "EC-GENESIS"}
    forged["hash"] = audit._entry_hash(forged)
    p.write_text(json.dumps(forged) + "\n")
    (council_dir / "audit.head").write_text(forged["hash"])
    r = audit.verify()
    assert r["ok"], "documented limitation: a full rewrite is not locally detectable"


def test_stale_head_does_not_break_next_append(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    _record(council_dir, c, "q1")
    # corrupt the advisory head cache; the jsonl tail is the source of truth
    (council_dir / "audit.head").write_text("sha256:STALE")
    _record(council_dir, c, "q2")
    assert audit.verify()["ok"]


def test_concurrent_appends_keep_chain_intact(council_dir):
    import threading
    def worker():
        for _ in range(15):
            audit.record_gate("bash", "ls", 2, "SOLO_ALLOW", "allow")
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    r = audit.verify()
    assert r["ok"] and r["entries"] == 60, r


def test_summary_counts(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    _record(council_dir, c, "q1")
    s = audit.summary()
    assert s["total_decisions"] == 1


# --- redaction: the audit must never persist the secret the gates detect ----
# Secret shape assembled at runtime — a literal would trip CI's own secret scan.
FAKE_SK = "sk-" + "B" * 24


def test_disk_never_sees_the_secret(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("block", 0.9), ("merge", 0.9)), c)
    # plant the secret in the question AND a vote reason AND the dissenting reason
    o.votes[0]["reason"] = f"found {FAKE_SK} in the diff"
    audit.record(c.id, f"merge a diff containing {FAKE_SK}", o, mode=c.mode)
    audit.record_gate("bash", f"curl -H 'Authorization: {FAKE_SK}' https://x", 9, "DUAL", "ask")
    everything = "".join(p.read_text(encoding="utf-8")
                         for p in council_dir.rglob("*") if p.is_file())
    assert FAKE_SK not in everything, "a secret reached disk under .council/"
    assert "[REDACTED:secret]" in everything


def test_redaction_preserves_decision_id_and_chain(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)), c)
    q = f"rotate {FAKE_SK} in prod"
    did = audit.record(c.id, q, o, mode=c.mode)
    # id is computed over the ORIGINAL text (stable), chain still verifies
    assert did == audit.decision_id(c.id, q, o, "")
    assert audit.verify()["ok"]


def test_redact_false_opts_out(council_dir, monkeypatch):
    monkeypatch.setenv("COUNCIL_REDACT", "false")
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)), c)
    audit.record(c.id, f"contains {FAKE_SK}", o, mode=c.mode)
    blob = "".join(p.read_text(encoding="utf-8")
                   for p in (council_dir / "decisions").glob("*.json"))
    assert FAKE_SK in blob  # explicit opt-out is honoured (operator's call)


def test_nested_context_and_basis_are_redacted(council_dir):
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally(votes(("merge", 0.9), ("merge", 0.9), ("merge", 0.9)), c)
    audit.record(c.id, "q", o, mode=c.mode,
                 context={"evidence": [{"log": f"token found {FAKE_SK}"}]},
                 approval={"approver": "jane", "basis": f"ticket with {FAKE_SK}", "status": "x"})
    blob = "".join(p.read_text(encoding="utf-8") for p in (council_dir / "decisions").glob("*.json"))
    assert FAKE_SK not in blob and "[REDACTED:secret]" in blob


def test_secret_in_role_or_model_field_is_redacted(council_dir):
    # The MCP audit_log path accepts host-supplied {role, model}; a secret/PII
    # there must not reach disk unredacted (field-coverage, not just `reason`).
    c = mkcouncil(mode="action-gate", n_roles=3, outcomes=("merge", "block"))
    o = tally([{"role": f"leaker {FAKE_SK}", "model": f"m api_key={FAKE_SK}", "vote": "block",
                "confidence": 0.9, "reason": "clean"},
               {"role": "b@corp.com", "model": "m", "vote": "merge", "confidence": 0.9, "reason": "y"},
               {"role": "C", "model": "m", "vote": "merge", "confidence": 0.9, "reason": "z"}], c)
    audit.record(c.id, "q", o, mode=c.mode)
    everything = "".join(p.read_text(encoding="utf-8")
                         for p in council_dir.rglob("*") if p.is_file())
    assert FAKE_SK not in everything, "secret in a role/model field reached disk"
    assert "b@corp.com" not in everything, "PII in a role field reached disk"
