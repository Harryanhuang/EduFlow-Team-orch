"""Tests for auto candidate generation: candidate_gen + event_hooks +
CLI --source/--expire + Obsidian candidates export.

Covers the user spec's 12 test points:
  1. promote_candidate → confirmed memory_item, candidate status=promoted
  2. reject_candidate → status=rejected, no memory_item created
  3. expire_stale_candidates → expired candidates marked rejected
  4. on_review_rejected → correct scope/kind/reason/risk_flags
  5. on_closeout_anomaly → scope=workflow:X, kind=workflow_rule
  6. on_manager_correction → severity=high → layer=core, kind=role_rule
  7. on_task_failure_pattern → failure_count<2 → None, ≥2 → candidate
  8. _infer_scope_kind_layer → various context combinations
  9. CLI: candidates --source, --expire; promote; reject
 10. Obsidian export: candidates/ dir with correct frontmatter
 11. Idempotency: same (source_type, source_ref) → no duplicate
 12. End-to-end: review_reject → candidate → promote → memory_item → export
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


def _backdate_expires(candidate_id: str, days_ago: int = 1) -> None:
    """Set a candidate's expires_at into the past for expire tests."""
    from eduflow.memory.db import get_conn
    past = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    get_conn().execute(
        "UPDATE memory_candidates SET expires_at = ? WHERE candidate_id = ?",
        (past, candidate_id),
    )
    get_conn().commit()


# ── 1. promote_candidate ─────────────────────────────────────────

class TestPromoteCandidate:
    def test_promote_creates_confirmed_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import (
                add_candidate, promote_candidate, get_candidate,
            )
            from eduflow.memory.items import get_memory
            cid = add_candidate(
                scope="team", kind="note", content="promote me",
                source_type="manual",
            )
            mid = promote_candidate(cid, reviewer="manager")
            assert mid.startswith("MI-")
            m = get_memory(mid)
            assert m is not None
            assert m["status"] == "confirmed"
            assert m["content"] == "promote me"
            cand = get_candidate(cid)
            assert cand["review_status"] == "promoted"
            assert cand["reviewed_by"] == "manager"
            _reset_db()

    def test_promote_copies_evidence_refs(self):
        """Evidence from candidate should flow into the memory item."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import (
                add_candidate, promote_candidate,
            )
            from eduflow.memory.items import get_memory
            cid = add_candidate(
                scope="team", kind="note", content="with evidence",
                evidence_refs=["task:T1", "review:T1"],
            )
            mid = promote_candidate(cid, reviewer="manager")
            m = get_memory(mid)
            evidence = json.loads(m["evidence_refs"])
            assert evidence == ["task:T1", "review:T1"]
            _reset_db()


# ── 2. reject_candidate ──────────────────────────────────────────

class TestRejectCandidate:
    def test_reject_sets_status_no_memory_created(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import (
                add_candidate, reject_candidate, get_candidate,
            )
            from eduflow.memory.items import list_memories
            cid = add_candidate(
                scope="team", kind="note", content="reject me",
            )
            ok = reject_candidate(cid, reviewer="manager", reason="duplicate")
            assert ok is True
            c = get_candidate(cid)
            assert c["review_status"] == "rejected"
            assert c["reviewed_by"] == "manager"
            # No memory_item created
            memories = list_memories(status=None, limit=100)
            assert not any(m["id"].startswith("MI-") for m in memories
                          if m.get("content") == "reject me")
            _reset_db()


# ── 3. expire_stale_candidates ───────────────────────────────────

class TestExpireStaleCandidates:
    def test_expire_marks_past_candidates_rejected(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import (
                add_candidate, expire_stale_candidates, get_candidate,
            )
            # Create 2 candidates, backdate one past expiry
            c_old = add_candidate(
                scope="team", kind="note", content="old candidate",
                source_type="manual", idempotent=False,
            )
            c_new = add_candidate(
                scope="team", kind="note", content="new candidate",
                source_type="manual", idempotent=False,
            )
            _backdate_expires(c_old, days_ago=1)
            count = expire_stale_candidates()
            assert count == 1
            assert get_candidate(c_old)["review_status"] == "rejected"
            assert get_candidate(c_new)["review_status"] == "proposed"
            _reset_db()

    def test_expire_does_not_touch_reviewed(self):
        """Already-promoted/rejected candidates should be left alone."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import (
                add_candidate, reject_candidate, expire_stale_candidates,
                get_candidate,
            )
            cid = add_candidate(
                scope="team", kind="note", content="already rejected",
            )
            reject_candidate(cid, reviewer="manager", reason="n/a")
            _backdate_expires(cid, days_ago=1)
            count = expire_stale_candidates()
            assert count == 0
            assert get_candidate(cid)["review_status"] == "rejected"
            _reset_db()


# ── 4. on_review_rejected ────────────────────────────────────────

class TestOnReviewRejected:
    def test_basic(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_review_rejected
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_review_rejected({
                "task_id": "T-001",
                "worker_name": "worker_course",
                "reject_reason": "QTL mismatch",
                "workflow_id": "wf_publish",
            })
            assert cid is not None
            assert cid.startswith("CAND-")
            c = get_candidate(cid)
            assert c["source_type"] == "review_reject"
            assert c["source_ref"] == "task:T-001"
            assert c["proposed_scope"] == "workflow:wf_publish"
            assert c["proposed_kind"] == "mistake"  # no process-flaw signal
            assert c["proposed_layer"] == "episode"
            assert "review rejected: QTL mismatch" in c["reason"]
            # "QTL" in reason → data_integrity flag
            risk = json.loads(c["risk_flags"])
            assert "data_integrity" in risk
            _reset_db()

    def test_skip_on_empty_task_id(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_review_rejected
            assert on_review_rejected({"reject_reason": "x"}) is None
            _reset_db()

    def test_process_flaw_upgrades_kind(self):
        """Reject reason mentioning 'process' → workflow_rule instead of mistake."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_review_rejected
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_review_rejected({
                "task_id": "T-002",
                "reject_reason": "missing step in workflow",
                "workflow_id": "wf_publish",
            })
            c = get_candidate(cid)
            assert c["proposed_kind"] == "workflow_rule"
            _reset_db()


# ── 5. on_closeout_anomaly ───────────────────────────────────────

class TestOnCloseoutAnomaly:
    def test_basic(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_closeout_anomaly
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_closeout_anomaly({
                "task_id": "T-003",
                "anomaly_type": "items_mismatch",
                "expected_value": "10",
                "actual_value": "8",
                "workflow_id": "wf_publish",
            })
            assert cid is not None
            c = get_candidate(cid)
            assert c["source_type"] == "closeout_anomaly"
            assert c["proposed_scope"] == "workflow:wf_publish"
            assert c["proposed_kind"] == "workflow_rule"
            assert c["proposed_layer"] == "decision"
            assert "closeout anomaly: items_mismatch" in c["reason"]
            risk = json.loads(c["risk_flags"])
            assert "closeout_gate" in risk
            _reset_db()

    def test_skip_without_workflow(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_closeout_anomaly
            # workflow_id required for scope resolution
            assert on_closeout_anomaly({
                "task_id": "T-004", "anomaly_type": "x",
            }) is None
            _reset_db()


# ── 6. on_manager_correction ─────────────────────────────────────

class TestOnManagerCorrection:
    def test_high_severity_layer_core(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_manager_correction
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_manager_correction({
                "target_agent": "worker_course",
                "correction_content": "never skip the verification gate",
                "severity": "high",
                "context": "after T-005 closeout",
            })
            assert cid is not None
            c = get_candidate(cid)
            assert c["proposed_scope"] == "agent:worker_course"
            assert c["proposed_kind"] == "role_rule"
            assert c["proposed_layer"] == "core"
            assert "manager correction:" in c["reason"]
            _reset_db()

    def test_normal_severity_is_decision(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_manager_correction
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_manager_correction({
                "target_agent": "worker_course",
                "correction_content": "prefer this phrasing",
                "severity": "low",
            })
            c = get_candidate(cid)
            assert c["proposed_kind"] == "workflow_rule"
            assert c["proposed_layer"] == "decision"
            _reset_db()

    def test_no_target_agent_uses_team_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_manager_correction
            cid = on_manager_correction({
                "correction_content": "all workers must X",
            })
            # No target → no agent scope → falls through to team
            assert cid is None  # our hook requires target_agent
            _reset_db()


# ── 7. on_task_failure_pattern ───────────────────────────────────

class TestOnTaskFailurePattern:
    def test_below_threshold_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_task_failure_pattern
            assert on_task_failure_pattern({
                "workflow_id": "wf_publish",
                "failure_count": 1,
            }) is None
            _reset_db()

    def test_at_threshold_creates_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_task_failure_pattern
            from eduflow.memory.candidate_gen import get_candidate
            cid = on_task_failure_pattern({
                "workflow_id": "wf_publish",
                "failure_count": 3,
                "failure_reasons": ["format error", "format error"],
                "task_ids": ["T1", "T2", "T3"],
            })
            assert cid is not None
            c = get_candidate(cid)
            assert c["source_type"] == "task_failure_pattern"
            assert c["proposed_scope"] == "workflow:wf_publish"
            assert c["proposed_layer"] == "decision"
            risk = json.loads(c["risk_flags"])
            assert "recurring_failure" in risk
            assert "pattern detected: 3 failures" in c["reason"]
            _reset_db()

    def test_no_workflow_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_task_failure_pattern
            assert on_task_failure_pattern({"failure_count": 5}) is None
            _reset_db()


# ── 8. _infer_scope_kind_layer ───────────────────────────────────

class TestInferScopeKindLayer:
    def test_review_reject_defaults(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "review_reject", {"task_id": "T1", "workflow_id": "W1"},
        )
        assert scope == "workflow:W1"
        assert kind == "mistake"
        assert layer == "episode"

    def test_closeout_anomaly_defaults(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "closeout_anomaly", {"workflow_id": "W1", "task_id": "T1"},
        )
        assert scope == "workflow:W1"
        assert kind == "workflow_rule"
        assert layer == "decision"

    def test_manager_correction_high_severity(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "manager_correction",
            {"target_agent": "worker_a", "severity": "high"},
        )
        assert scope == "agent:worker_a"
        assert kind == "role_rule"
        assert layer == "core"

    def test_task_failure_pattern_defaults(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "task_failure_pattern", {"workflow_id": "W1"},
        )
        assert scope == "workflow:W1"
        # Default is "mistake" — failures are worker errors unless
        # failure_reasons contain process-flaw signals.
        assert kind == "mistake"
        assert layer == "decision"

    def test_explicit_override_wins(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "review_reject",
            {"scope": "team", "kind": "decision", "layer": "core"},
        )
        assert scope == "team"
        assert kind == "decision"
        assert layer == "core"

    def test_agent_only_scope(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer(
            "manager_correction", {"target_agent": "worker_x"},
        )
        assert scope == "agent:worker_x"

    def test_unknown_source_type_fallback(self):
        from eduflow.memory.candidate_gen import infer_scope_kind_layer
        scope, kind, layer = infer_scope_kind_layer("bogus_type", {})
        assert scope == "team"
        assert kind == "note"
        assert layer == "episode"


# ── 9. CLI ───────────────────────────────────────────────────────

class TestCLI:
    def test_candidates_list(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="team", kind="note", content="cli-test-1",
                source_type="review_reject", source_ref="task:T1",
            )
            rc, out, err = run_cli(["memory", "candidates"])
            assert rc == 0
            assert "cli-test-1" in out
            assert "review_reject" in out
            _reset_db()

    def test_candidates_filter_by_source(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="team", kind="note", content="review one",
                source_type="review_reject", source_ref="task:T1",
            )
            add_candidate(
                scope="team", kind="note", content="closeout one",
                source_type="closeout_anomaly", source_ref="task:T2",
            )
            rc, out, err = run_cli([
                "memory", "candidates", "--source", "review_reject",
            ])
            assert rc == 0
            assert "review one" in out
            assert "closeout one" not in out
            _reset_db()

    def test_candidates_expire_flag(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="old",
                source_type="manual", idempotent=False,
            )
            _backdate_expires(cid, days_ago=1)
            rc, out, err = run_cli(["memory", "candidates", "--expire"])
            assert rc == 0
            assert "Expired" in out
            assert "1" in out
            _reset_db()

    def test_cli_promote_and_reject(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            from eduflow.memory.candidate_gen import add_candidate
            c1 = add_candidate(
                scope="team", kind="note", content="promote-me",
                source_type="manual",
            )
            c2 = add_candidate(
                scope="team", kind="note", content="reject-me",
                source_type="manual",
            )
            rc, out, err = run_cli([
                "memory", "promote", c1, "--reviewer", "manager",
            ])
            assert rc == 0
            assert "Promoted" in out

            rc, out, err = run_cli([
                "memory", "reject", c2, "--reason", "n/a",
            ])
            assert rc == 0
            assert "Rejected" in out
            _reset_db()


# ── 10. Obsidian export ──────────────────────────────────────────

class TestObsidianExport:
    def test_candidates_dir_populated(self):
        with isolated_env() as tmp:
            _init_db()
            obs_root = tmp / "obsidian"
            obs_root.mkdir()
            from tests.helpers import env_patch
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="team", kind="note", content="exported candidate",
                source_type="review_reject", source_ref="task:T10",
            )
            with env_patch(EDUFLOW_OBSIDIAN_ROOT=str(obs_root)):
                from eduflow.memory.obsidian_export import export_all
                counts = export_all()
            assert counts["candidates"] == 1
            cands_dir = obs_root / "_memory-exports" / "candidates"
            assert cands_dir.exists()
            files = list(cands_dir.glob("*.md"))
            assert len(files) == 1
            content = files[0].read_text(encoding="utf-8")
            assert "candidate_id:" in content
            # _yaml_frontmatter quotes strings, so look for either form
            assert "source_type:" in content and "review_reject" in content
            assert "proposed_scope:" in content
            assert "exported candidate" in content
            # Index mentions candidates count
            idx = (obs_root / "_memory-exports" / "index.md").read_text(encoding="utf-8")
            assert "待审核候选" in idx
            _reset_db()

    def test_candidates_cleanup_after_promote(self):
        """After promote, the candidate no longer shows as proposed; export
        should still include it but as promoted status (it's still in the DB)."""
        with isolated_env() as tmp:
            _init_db()
            obs_root = tmp / "obsidian"
            obs_root.mkdir()
            from tests.helpers import env_patch
            from eduflow.memory.candidate_gen import (
                add_candidate, promote_candidate,
            )
            cid = add_candidate(
                scope="team", kind="note", content="promoted-cand",
                source_type="manual",
            )
            promote_candidate(cid, reviewer="manager")
            with env_patch(EDUFLOW_OBSIDIAN_ROOT=str(obs_root)):
                from eduflow.memory.obsidian_export import export_all
                counts = export_all()
            # Candidate exists (as promoted) and should still be exported
            assert counts["candidates"] == 1
            _reset_db()


# ── 11. Idempotency ──────────────────────────────────────────────

class TestIdempotency:
    def test_same_event_no_duplicate(self):
        """Firing the same hook twice with the same source_ref returns
        the same candidate_id (no duplicate row)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_review_rejected
            ctx = {
                "task_id": "T-DUP",
                "reject_reason": "mismatch",
                "workflow_id": "wf_X",
            }
            c1 = on_review_rejected(ctx)
            c2 = on_review_rejected(ctx)
            assert c1 is not None
            assert c1 == c2
            # Verify only one row in DB
            from eduflow.memory.candidate_gen import list_candidates
            all_cands = list_candidates(status=None, limit=100)
            matching = [c for c in all_cands if c.get("source_ref") == "task:T-DUP"]
            assert len(matching) == 1
            _reset_db()

    def test_manual_candidates_not_deduped(self):
        """Manual adds with source_type='manual' skip the dedup check —
        a human adding the same note twice is deliberate."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            c1 = add_candidate(
                scope="team", kind="note", content="same",
                source_type="manual", source_ref="ref:X",
            )
            c2 = add_candidate(
                scope="team", kind="note", content="same",
                source_type="manual", source_ref="ref:X",
            )
            assert c1 != c2
            _reset_db()

    def test_distinct_source_refs_distinct_candidates(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_hooks import on_review_rejected
            c1 = on_review_rejected({
                "task_id": "T-A",
                "reject_reason": "format",
                "workflow_id": "wf_X",
            })
            c2 = on_review_rejected({
                "task_id": "T-B",
                "reject_reason": "format",
                "workflow_id": "wf_X",
            })
            assert c1 != c2
            _reset_db()


# ── 12. End-to-end ───────────────────────────────────────────────

class TestEndToEnd:
    def test_full_flow_review_reject_to_export(self):
        """review_reject → candidate → promote → memory_item → Obsidian export."""
        with isolated_env() as tmp:
            _init_db()
            obs_root = tmp / "obsidian"
            obs_root.mkdir()

            # 1. Hook fires
            from eduflow.memory.event_hooks import on_review_rejected
            cid = on_review_rejected({
                "task_id": "T-E2E",
                "worker_name": "worker_course",
                "reject_reason": "QTL count mismatch",
                "workflow_id": "wf_publish",
                "review_content": "Found 8 items but manifest says 10",
            })
            assert cid is not None

            # 2. Candidate exists in queue
            from eduflow.memory.candidate_gen import (
                get_candidate, promote_candidate,
            )
            c = get_candidate(cid)
            assert c["review_status"] == "proposed"
            assert c["proposed_scope"] == "workflow:wf_publish"
            assert c["proposed_kind"] == "mistake"

            # 3. Manager promotes
            mid = promote_candidate(cid, reviewer="manager")
            assert mid.startswith("MI-")

            # 4. Memory item confirmed with right content
            from eduflow.memory.items import get_memory
            m = get_memory(mid)
            assert m["status"] == "confirmed"
            assert "T-E2E" in m["content"]
            assert m["scope"] == "workflow:wf_publish"

            # 5. Export includes both the memory item and the (now-promoted) candidate
            from tests.helpers import env_patch
            with env_patch(EDUFLOW_OBSIDIAN_ROOT=str(obs_root)):
                from eduflow.memory.obsidian_export import export_all
                counts = export_all()
            assert counts["items"] >= 1
            assert counts["candidates"] >= 1
            cands_dir = obs_root / "_memory-exports" / "candidates"
            cand_file = cands_dir / f"{cid}.md"
            assert cand_file.exists()
            cand_text = cand_file.read_text(encoding="utf-8")
            assert "promoted" in cand_text

            # Memory item file also exists. kind="mistake" (inferred from
            # review_reject) → exported under mistakes/ not decisions/.
            mistakes_dir = obs_root / "_memory-exports" / "mistakes"
            mi_files = list(mistakes_dir.glob("*.md"))
            assert any(mid in f.stem for f in mi_files)
            _reset_db()
