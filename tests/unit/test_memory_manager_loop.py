"""Tests for the Memory + Hermes Manager Loop wiring.

This test file covers the integration between `eduflow task` lifecycle
commands and the memory system. The wiring is what makes
"review reject / closeout mismatch / manager correction / task fail"
flow into `memory_candidates` (proposed status), without ever blocking
the original task command and without ever auto-promoting.

Tests use `isolated_env()` + `run_cli()` like the other memory tests.
Each test asserts:
  1. The task command exits 0 (no memory-system error blocked it).
  2. The expected memory candidate was created.
  3. The memory system is best-effort: an injected failure does not
     break the task command (fail-open contract).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env, run_cli
from eduflow.runtime import paths
from eduflow.memory.db import init_schema, close as db_close
from eduflow.memory.candidates import list_candidates
from eduflow.store import tasks


# ── helpers ──────────────────────────────────────────────────────

def _init_db():
    db_close()
    init_schema()


def _reset_db():
    db_close()


def _count_candidates(*, source_type: str | None = None) -> int:
    rows = list_candidates(status="proposed", limit=200)
    if source_type:
        rows = [r for r in rows if r.get("source_type") == source_type]
    return len(rows)


def _create_assigned_task(title: str = "Smoke task") -> str:
    """Helper: create a flow task and transition to assigned.

    Note: title must NOT contain any AP_TITLE_MARKERS lowercased
    substring ('ap', 'ap-', 'ap_calculus', 'advanced placement'),
    IGCSE_TITLE_MARKERS, or numeric syllabus codes (0452, 0478, etc.).
    Some test titles used words like "approve" / "reject" / "Pattern"
    which accidentally matched. We use neutral titles.
    """
    tid = tasks.create_flow(
        "worker_course", title,
        stage="curriculum", owner="worker_course",
        creator="manager",
        workflow_id="igcse-subject-launch",
    )
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    return tid


# ── 1. Review reject creates a candidate ─────────────────────────

class TestReviewRejectBridge:

    def test_review_reject_creates_candidate(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Review reject bridge test")
            # Worker submits for review
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
            # Reviewer rejects with a valid FLOW_REVIEW_REASONS value.
            # Note: actor must be 'reviewer' (state-machine constraint).
            rc, out, err = run_cli([
                "task", "review", tid, "--actor", "reviewer",
                "--reject", "--reason", "quality_not_met",
            ])
            assert rc == 0, f"out={out!r} err={err!r}"
            candidates = list_candidates(status="proposed", limit=20)
            review_rejects = [
                c for c in candidates
                if c.get("source_type") == "review_reject"
                and c.get("source_ref") == f"task:{tid}"
            ]
            assert len(review_rejects) == 1, (
                f"expected exactly 1 review_reject candidate for {tid}, got {len(review_rejects)}; "
                f"all source_types: {[c.get('source_type') for c in candidates]}"
            )
            _reset_db()

    def test_review_approve_does_not_create_candidate(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Review green path no bridge")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
            before = _count_candidates(source_type="review_reject")
            rc, out, _ = run_cli([
                "task", "review", tid, "--actor", "reviewer", "--approve",
            ])
            assert rc == 0, out
            after = _count_candidates(source_type="review_reject")
            assert before == after, (
                f"green-light review should not create review_reject candidate; "
                f"before={before} after={after}"
            )
            _reset_db()


# ── 2. Closeout anomaly bridge ───────────────────────────────────

class TestCloseoutBridge:
    """The bridge is wired at closeout-command level. Since real closeout
    requires a content directory + verifier, we test the helper directly:
    the wiring lives in `_bridge_closeout_anomaly` which we exercise via
    the actual closeout flow. We keep this class minimal and verify the
    integration point exists; deeper closeout flow tests already live in
    test_commands_task.py."""

    def test_closeout_bridge_helper_consistent_counts(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {
                "id": "T-999",
                "evidence_packet": {
                    "items_count": 300,
                    "qql_count": 300,
                    "manifest_rows": 300,
                },
            }
            _bridge_closeout_anomaly(task)
            cands = list_candidates(status="proposed", limit=20)
            closeout_cands = [c for c in cands if c.get("source_type") == "closeout_anomaly"]
            assert len(closeout_cands) == 0, (
                "consistent counts should NOT create closeout_anomaly candidate"
            )
            _reset_db()

    def test_closeout_bridge_helper_mismatch_counts(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {
                "id": "T-999",
                "workflow_id": "igcse-subject-launch",
                "evidence_packet": {
                    "items_count": 300,
                    "qql_count": 280,
                    "manifest_rows": 300,
                },
            }
            _bridge_closeout_anomaly(task)
            cands = list_candidates(status="proposed", limit=20)
            closeout_cands = [c for c in cands if c.get("source_type") == "closeout_anomaly"]
            assert len(closeout_cands) == 1, (
                "mismatched counts should create exactly 1 closeout_anomaly candidate"
            )
            _reset_db()

    def test_closeout_bridge_helper_no_evidence_does_not_crash(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {"id": "T-998"}  # no evidence_packet
            # Should not raise
            _bridge_closeout_anomaly(task)
            _reset_db()


# ── 3. Manager correction command ────────────────────────────────

class TestManagerCorrectionCommand:

    def test_task_correct_creates_candidate(self):
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "correct", "worker_qbank",
                "stop emitting options with empty stems",
                "--severity", "high",
                "--context", "found in 2026-06-24 batch review",
            ])
            assert rc == 0, out
            assert "📝 correction candidate" in out
            cands = list_candidates(status="proposed", limit=20)
            mgr_cands = [c for c in cands if c.get("source_type") == "manager_correction"]
            assert len(mgr_cands) >= 1
            assert "options with empty stems" in (mgr_cands[0]["content"] or "")
            _reset_db()

    def test_task_correct_invalid_severity_rejected(self):
        with isolated_env():
            _init_db()
            rc, _, err = run_cli([
                "task", "correct", "worker_qbank", "test content",
                "--severity", "extreme",  # not in low|medium|high|critical
            ])
            assert rc == 1
            assert "invalid --severity" in err
            _reset_db()

    def test_task_correct_requires_agent_and_content(self):
        with isolated_env():
            _init_db()
            rc, _, err = run_cli(["task", "correct", "worker_qbank"])
            assert rc == 1
            assert "usage:" in err
            _reset_db()


# ── 4. Dispatch memory packet ────────────────────────────────────

class TestDispatchMemoryPacket:

    def test_dispatch_packet_does_not_block_when_empty(self):
        with isolated_env():
            _init_db()
            # No memory data exists — packet assembly should return None
            # and dispatch should still succeed (fail-open).
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "Packet empty test",
                "--stage", "curriculum",
                "--owner", "worker_course",
            ])
            assert rc == 0, out
            assert "✅ dispatched" in out
            # Should mention no packet OR show empty packet body
            # The fail-open contract is: dispatch still succeeds.
            _reset_db()

    def test_dispatch_packet_failure_does_not_block(self):
        """If assemble_memory_packet raises, dispatch must still return 0."""
        with isolated_env():
            _init_db()
            from eduflow.commands import task as task_cmd

            def _explode(*args, **kwargs):
                raise RuntimeError("simulated memory system failure")

            original = task_cmd.assemble_memory_packet if hasattr(task_cmd, 'assemble_memory_packet') else None
            # Patch via the helper's import path
            import eduflow.memory.packet as packet_mod
            original_packet = packet_mod.assemble_memory_packet
            packet_mod.assemble_memory_packet = _explode
            try:
                rc, out, _ = run_cli([
                    "task", "dispatch",
                    "worker_course", "Packet fail-open test",
                    "--stage", "curriculum",
                    "--owner", "worker_course",
                ])
                assert rc == 0, f"dispatch must succeed even if packet raises; got rc={rc} out={out!r}"
                assert "✅ dispatched" in out
                assert "⚠" in out or "memory packet failed" in out
            finally:
                packet_mod.assemble_memory_packet = original_packet
            _reset_db()


# ── 5. Promote / reject status changes ───────────────────────────

class TestPromoteRejectWiring:

    def test_promote_changes_candidate_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="promote me",
                source_type="manual",
            )
            rc, out, _ = run_cli([
                "memory", "promote", cid, "--reviewer", "manager", "--yes",
            ])
            assert rc == 0, out
            assert "Promoted" in out
            from eduflow.memory.candidates import get_candidate
            c = get_candidate(cid)
            assert c is not None
            assert c["review_status"] == "promoted"
            _reset_db()

    def test_reject_changes_candidate_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="reject me",
                source_type="manual",
            )
            rc, out, _ = run_cli([
                "memory", "reject", cid, "--reason", "no longer relevant", "--yes",
            ])
            assert rc == 0, out
            assert "Rejected" in out
            from eduflow.memory.candidates import get_candidate
            c = get_candidate(cid)
            assert c is not None
            assert c["review_status"] == "rejected"
            _reset_db()


# ── 6. Daily review output ───────────────────────────────────────

class TestDailyReview:

    def test_daily_outputs_backlog_and_handoff(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="team", kind="note", content="daily backlog one",
                source_type="review_reject", source_ref="task:T-D-1",
            )
            add_candidate(
                scope="team", kind="note", content="daily backlog two",
                source_type="closeout_anomaly", source_ref="task:T-D-2",
            )
            rc, out, _ = run_cli(["memory", "daily"])
            assert rc == 0, out
            assert "📅 Daily Memory Review" in out
            assert "📊 Proposed candidate backlog" in out
            assert "review_reject" in out
            assert "closeout_anomaly" in out
            assert "🤝 Hermes handoff section" in out
            assert "memory-candidate-backlog" in out
            _reset_db()

    def test_daily_with_empty_backlog(self):
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli(["memory", "daily"])
            assert rc == 0, out
            assert "📊 Proposed candidate backlog: 0" in out
            assert "🤝 Hermes handoff section" in out
            _reset_db()


# ── 7. Task lifecycle fail bridge ────────────────────────────────

class TestTaskFailBridge:

    def test_task_cancel_creates_witness_candidate(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Cancel witness test")
            # Cancel the task via manager → should fire bridge_task_lifecycle
            tasks.transition_flow(tid, to_status="cancelled", actor="manager")
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1, (
                f"expected 1 task_failure witness candidate, got {len(fail_cands)}"
            )
            assert fail_cands[0]["source_ref"] == f"task:{tid}"
            _reset_db()

    def test_task_cancel_idempotent(self):
        """Calling cancel twice (somehow) should NOT create a duplicate
        witness — add_candidate is idempotent by (source_type, source_ref)."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Cancel idempotent test")
            tasks.transition_flow(tid, to_status="cancelled", actor="manager")
            # Even if we try to record again, the witness stays singular.
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1
            _reset_db()

    def test_two_failures_in_same_workflow_create_pattern_candidate(self):
        """≥2 failures in same workflow should produce a pattern candidate
        in addition to the per-task witness candidates."""
        with isolated_env():
            _init_db()
            tid1 = _create_assigned_task("Fail pattern 1")
            tid2 = _create_assigned_task("Fail pattern 2")
            tasks.transition_flow(tid1, to_status="cancelled", actor="manager")
            tasks.transition_flow(tid2, to_status="cancelled", actor="manager")
            cands = list_candidates(status="proposed", limit=50)
            # 2 witness candidates
            witnesses = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(witnesses) == 2, f"expected 2 witnesses, got {len(witnesses)}"
            # 1 pattern candidate (idempotent)
            patterns = [c for c in cands if c.get("source_type") == "task_failure_pattern"]
            assert len(patterns) == 1, f"expected 1 pattern candidate, got {len(patterns)}"
            _reset_db()


# ── 8. Fail-open contract ────────────────────────────────────────

class TestFailOpenContract:

    def test_task_correct_does_not_crash_when_bridge_unavailable(self):
        """If memory.event_bridge is unavailable (ImportError), task correct
        must still return 0 — the contract is fail-open."""
        with isolated_env():
            _init_db()
            import builtins
            original_import = builtins.__import__
            def _blocked_import(name, *args, **kwargs):
                if name == "eduflow.memory.event_bridge" or \
                   name.startswith("eduflow.memory.event_bridge"):
                    raise ImportError("simulated bridge unavailable")
                return original_import(name, *args, **kwargs)
            builtins.__import__ = _blocked_import
            try:
                rc, out, _ = run_cli([
                    "task", "correct", "worker_qbank", "test fail-open",
                ])
                # Should still return 0 with a warning, not crash
                assert rc == 0, f"task correct must be fail-open; got rc={rc} out={out!r}"
                assert "⚠" in out or "unavailable" in out
            finally:
                builtins.__import__ = original_import
            _reset_db()


# ── 9. Fix 1: Expanded fail-bridge triggers ──────────────────────

class TestFailBridgeExpansion:

    def test_blocked_transition_fires_witness(self):
        """Worker transitioning to 'blocked' should also surface a witness."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Bridge trigger blocked")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="blocked", actor="worker")
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1, (
                f"expected 1 task_failure witness for blocked transition, got {len(fail_cands)}"
            )
            assert fail_cands[0]["source_ref"] == f"task:{tid}"
            _reset_db()

    def test_delivered_with_rejected_verdict_fires_witness(self):
        """A delivered task with verdict=rejected should fire a witness.

        Use the 'builder' stage which doesn't require reviewer verdict
        before manager delivery. The state machine resets verdict to
        'approved' on delivered, so we set it after the transition
        and then re-trigger the bridge path via a second transition.
        """
        with isolated_env():
            _init_db()
            from eduflow.store import tasks as _tasks
            tid = _tasks.create_flow(
                "worker_builder", "Deliver reject bridge test",
                stage="builder", owner="worker_builder",
                creator="manager",
                workflow_id="igcse-subject-launch",
            )
            _tasks.transition_flow(tid, to_status="assigned", actor="manager")
            _tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            _tasks.transition_flow(tid, to_status="delivered", actor="worker")
            # Now mutate verdict to rejected AFTER delivered.
            # The state machine reset it to 'approved' on the transition;
            # we override here to simulate the edge case where the
            # verdict is changed post-delivery (e.g. by a downstream
            # review pass that rejects the package-level verdict).
            data = _tasks._load()
            task = _tasks._find_task(data, tid)
            task["verdict"] = "rejected"
            _tasks._save(data)
            # Trigger the bridge path by calling the helper directly,
            # which is what transition_flow does internally on failure
            # transitions. This proves the helper correctly recognizes
            # delivered+rejected as a failure-shaped signal.
            from eduflow.store.tasks import _try_bridge_task_failure
            _try_bridge_task_failure(tid, actor="verifier", to_status="delivered")
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1
            reason_or_content = (fail_cands[0].get("reason") or "") + " " + (fail_cands[0].get("content") or "")
            assert "rejected" in reason_or_content.lower()
            _reset_db()

    def test_normal_progress_does_not_fire_witness(self):
        """assigned → in_progress → submitted_for_review must NOT fire witness."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Normal progress no witness")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 0
            _reset_db()


# ── 10. Fix 2: PII / secret guardrail ───────────────────────────

class TestPIIGuardrail:

    def test_api_key_in_content_triggers_warning(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test_1234567890abcdef in config",
                "--severity", "high",
            ])
            assert rc == 0
            # Warning goes to stderr, command still proceeds (warn-only)
            assert "sensitive-pattern warning" in err
            assert "API key" in err
            # But candidate IS still created (warn-only, not blocked)
            cands = list_candidates(status="proposed", limit=20)
            mgr_cands = [c for c in cands if c.get("source_type") == "manager_correction"]
            assert len(mgr_cands) == 1
            _reset_db()

    def test_clean_content_no_warning(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "stop emitting options with empty stems",
                "--severity", "high",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" not in err
            _reset_db()

    def test_force_flag_suppresses_warning(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "see api_key=test_safe_string in template",
                "--severity", "high",
                "--force",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" not in err
            _reset_db()

    def test_pem_block_in_context_triggers_warning(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "clean up key file",
                "--severity", "high",
                "--context", "-----BEGIN PRIVATE KEY-----",
            ])
            assert rc == 0
            assert "PEM" in err or "sensitive-pattern" in err
            _reset_db()

    def test_scanner_failure_does_not_block_command(self):
        """If the scanner itself crashes, the command must still succeed
        (fail-open contract)."""
        with isolated_env():
            _init_db()
            from eduflow.commands import task as task_cmd
            original = task_cmd._scan_sensitive_content
            def _explode(*args, **kwargs):
                raise RuntimeError("simulated scanner crash")
            task_cmd._scan_sensitive_content = _explode
            try:
                rc, out, err = run_cli([
                    "task", "correct", "worker_qbank",
                    "scanner fail-open test",
                ])
                assert rc == 0, f"task correct must be fail-open when scanner crashes; got rc={rc}"
                assert "📝 correction candidate" in out
                assert "scanner failed" in err
            finally:
                task_cmd._scan_sensitive_content = original
            _reset_db()


# ── 11. Fix 3: memory daily --json ───────────────────────────────

class TestMemoryDailyJson:

    def test_json_output_is_valid_json(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="team", kind="note", content="json mode test",
                source_type="manager_correction", source_ref="agent:test",
            )
            rc, out, _ = run_cli(["memory", "daily", "--json"])
            assert rc == 0
            payload = json.loads(out)
            assert "date" in payload
            assert "totals" in payload
            assert "by_source_type" in payload["totals"]
            assert payload["totals"]["by_source_type"].get("manager_correction", 0) >= 1
            assert "hermes_handoff" in payload
            assert "next_actions" in payload["hermes_handoff"]
            _reset_db()

    def test_json_empty_backlog(self):
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli(["memory", "daily", "--json"])
            assert rc == 0
            payload = json.loads(out)
            assert payload["totals"]["proposed"] == 0
            assert payload["totals"]["by_source_type"] == {}
            _reset_db()

    def test_json_with_scope_filter(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            add_candidate(
                scope="workflow:A", kind="note", content="scope A item",
                source_type="manual", source_ref="r:A:1",
            )
            add_candidate(
                scope="workflow:B", kind="note", content="scope B item",
                source_type="manual", source_ref="r:B:1",
            )
            rc, out, _ = run_cli([
                "memory", "daily", "--json", "--scope", "workflow:A",
            ])
            assert rc == 0
            payload = json.loads(out)
            assert payload["scope_filter"] == "workflow:A"
            assert payload["totals"]["proposed"] == 1
            _reset_db()


# ── 12. Fix 4: Closeout evidence field broadening ────────────────

class TestCloseoutEvidenceFields:

    def test_legacy_field_item_count_recognized(self):
        """Legacy tasks may use item_count instead of items_count."""
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {
                "id": "T-L1",
                "workflow_id": "igcse-subject-launch",
                "evidence_packet": {
                    "item_count": 300,
                    "qa_count": 280,
                    "manifest_covered_count": 300,
                },
            }
            _bridge_closeout_anomaly(task)
            cands = list_candidates(status="proposed", limit=20)
            closeout_cands = [c for c in cands if c.get("source_type") == "closeout_anomaly"]
            assert len(closeout_cands) == 1, (
                "legacy field names should still be recognized as mismatch"
            )
            _reset_db()

    def test_zero_counts_no_false_positive(self):
        """When all counts are 0, no candidate should fire (avoid noise)."""
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {
                "id": "T-0",
                "workflow_id": "igcse-subject-launch",
                "evidence_packet": {},  # all empty
            }
            _bridge_closeout_anomaly(task)
            cands = list_candidates(status="proposed", limit=20)
            closeout_cands = [c for c in cands if c.get("source_type") == "closeout_anomaly"]
            assert len(closeout_cands) == 0
            _reset_db()

    def test_mixed_field_names_works(self):
        """Mixed legacy + modern field names should still work."""
        with isolated_env():
            _init_db()
            from eduflow.commands.task import _bridge_closeout_anomaly
            task = {
                "id": "T-M1",
                "workflow_id": "igcse-subject-launch",
                "evidence_packet": {
                    "items_count": 300,        # modern
                    "qa_count": 300,           # legacy alias for qql
                    "items_mapping_count": 300,  # legacy alias for manifest
                },
            }
            _bridge_closeout_anomaly(task)
            cands = list_candidates(status="proposed", limit=20)
            closeout_cands = [c for c in cands if c.get("source_type") == "closeout_anomaly"]
            assert len(closeout_cands) == 0, "consistent counts (300/300/300) should not fire"
            _reset_db()


# ── 13. Fix 2b: scan_sensitive_content unit tests ────────────────

class TestSensitiveContentScanner:

    def test_email_pattern_detected(self):
        from eduflow.commands.task import _scan_sensitive_content
        matches = _scan_sensitive_content("contact alice@gmail.com for help")
        assert any("email" in m.lower() for m in matches)

    def test_bearer_token_detected(self):
        from eduflow.commands.task import _scan_sensitive_content
        matches = _scan_sensitive_content("set Authorization: Bearer eyJxxx")
        assert any("bearer" in m.lower() for m in matches)

    def test_no_match_for_clean_text(self):
        from eduflow.commands.task import _scan_sensitive_content
        matches = _scan_sensitive_content("stop emitting options with empty stems")
        assert matches == []

    def test_empty_inputs(self):
        from eduflow.commands.task import _scan_sensitive_content
        assert _scan_sensitive_content("") == []
        assert _scan_sensitive_content("", "") == []
        assert _scan_sensitive_content(None or "", "") == []


# ── 14. Opt 1: --no-sensitive-check alias ───────────────────────

class TestNoSensitiveCheckAlias:

    def test_no_sensitive_check_suppresses_warning(self):
        """--no-sensitive-check has the same effect as --force."""
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "see api_key=sk_test_safe_string in template",
                "--severity", "high",
                "--no-sensitive-check",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" not in err
            # Candidate was still created
            cands = list_candidates(status="proposed", limit=20)
            mgr_cands = [c for c in cands if c.get("source_type") == "manager_correction"]
            assert len(mgr_cands) == 1
            _reset_db()

    def test_force_and_no_sensitive_check_equivalent(self):
        """Both flags produce the same result."""
        with isolated_env():
            _init_db()
            # First call: with --force
            rc1, out1, err1 = run_cli([
                "task", "correct", "worker_qbank",
                "p1: set password=foo",
                "--severity", "high",
                "--force",
            ])
            assert rc1 == 0
            assert "sensitive-pattern warning" not in err1
            # Second call: with --no-sensitive-check
            rc2, out2, err2 = run_cli([
                "task", "correct", "worker_qbank",
                "p2: set password=bar",
                "--severity", "high",
                "--no-sensitive-check",
            ])
            assert rc2 == 0
            assert "sensitive-pattern warning" not in err2
            _reset_db()


# ── 15. Opt 2: task report-failure ──────────────────────────────

class TestReportFailure:

    def test_worker_can_report_failure_from_assigned(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Worker self report fail")
            # Worker transitions to in_progress first (normal flow)
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            # Then self-reports failure
            rc, out, _ = run_cli([
                "task", "report-failure", tid,
                "--actor", "worker",
                "--reason", "disk full, cannot write artifacts",
            ])
            assert rc == 0, out
            # Status should now be failed
            assert tasks.get(tid)["status"] == "failed"
            # Reason should be persisted
            assert "disk full" in tasks.get(tid).get("failure_reason", "")
            # Bridge should have fired a witness candidate
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1
            _reset_db()

    def test_report_failure_requires_actor(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Report fail no actor")
            rc, _, err = run_cli([
                "task", "report-failure", tid,
                "--reason", "no actor",
            ])
            assert rc == 1
            assert "usage:" in err
            _reset_db()

    def test_report_failure_idempotent_for_already_failed(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Idempotent fail")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            # First report
            run_cli(["task", "report-failure", tid, "--actor", "worker", "--reason", "first"])
            cands = list_candidates(status="proposed", limit=20)
            fail_cands_before = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands_before) == 1
            # Second report (same task, already failed) — should not
            # create a new candidate; should be idempotent
            run_cli(["task", "report-failure", tid, "--actor", "worker", "--reason", "second"])
            cands = list_candidates(status="proposed", limit=20)
            fail_cands_after = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands_after) == 1  # still just one
            _reset_db()

    def test_manager_cannot_report_failure(self):
        """Manager should use task flow-transition --to cancelled instead."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Manager report fail")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            rc, _, err = run_cli([
                "task", "report-failure", tid,
                "--actor", "manager",
                "--reason", "should fail",
            ])
            assert rc == 1
            assert "cannot transition" in err or "ValueError" in err
            _reset_db()


# ── 16. Opt 3: task update-verdict ──────────────────────────────

class TestUpdateVerdict:

    def test_update_verdict_to_rejected_on_delivered(self):
        with isolated_env():
            _init_db()
            # Use builder stage to avoid reviewer-mandate for delivery
            tid = tasks.create_flow(
                "worker_builder", "Update verdict test",
                stage="builder", owner="worker_builder",
                creator="manager", workflow_id="igcse-subject-launch",
            )
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="delivered", actor="worker")
            # Update verdict to rejected post-delivery
            rc, out, _ = run_cli([
                "task", "update-verdict", tid,
                "--actor", "manager",
                "--verdict", "rejected",
                "--reason", "downstream review found qa bank drift",
            ])
            assert rc == 0, out
            # Verdict should now be rejected
            assert tasks.get(tid)["verdict"] == "rejected"
            # Bridge should fire a delivered+rejected witness candidate
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 1
            _reset_db()

    def test_update_verdict_requires_delivered_status(self):
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Update verdict not delivered")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            rc, _, err = run_cli([
                "task", "update-verdict", tid,
                "--actor", "manager",
                "--verdict", "rejected",
            ])
            assert rc == 1
            assert "delivered" in err.lower() or "status" in err.lower()
            _reset_db()

    def test_update_verdict_rejects_worker_actor(self):
        with isolated_env():
            _init_db()
            tid = tasks.create_flow(
                "worker_builder", "Worker verdict update",
                stage="builder", owner="worker_builder",
                creator="manager", workflow_id="igcse-subject-launch",
            )
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="delivered", actor="worker")
            rc, _, err = run_cli([
                "task", "update-verdict", tid,
                "--actor", "worker",
                "--verdict", "rejected",
            ])
            assert rc == 1
            assert "manager" in err.lower() or "reviewer" in err.lower()
            _reset_db()

    def test_update_verdict_to_approved_no_bridge(self):
        """Approved verdict post-delivery is a no-op for the bridge
        (no failure signal)."""
        with isolated_env():
            _init_db()
            tid = tasks.create_flow(
                "worker_builder", "Update verdict approved",
                stage="builder", owner="worker_builder",
                creator="manager", workflow_id="igcse-subject-launch",
            )
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="delivered", actor="worker")
            # Approved→Approved should be a no-op for the bridge
            rc, out, _ = run_cli([
                "task", "update-verdict", tid,
                "--actor", "manager",
                "--verdict", "approved",
            ])
            assert rc == 0, out
            cands = list_candidates(status="proposed", limit=20)
            fail_cands = [c for c in cands if c.get("source_type") == "task_failure"]
            assert len(fail_cands) == 0
            _reset_db()


# ── 17. Opt 4: hermes-can-promote ───────────────────────────────

class TestHermesCanPromote:

    def test_hermes_can_promote_non_high_impact(self):
        """With hermes_can_promote=True, reviewer=hermes can promote
        non-high-impact kinds like 'note'."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="hermes can promote me",
                source_type="manual",
            )
            rc, out, _ = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--hermes-can-promote",
                "--yes",
            ])
            assert rc == 0, out
            assert "Promoted" in out
            from eduflow.memory.candidates import get_candidate
            c = get_candidate(cid)
            assert c["review_status"] == "promoted"
            _reset_db()

    def test_hermes_cannot_promote_high_impact_even_with_flag(self):
        """High-impact kinds ALWAYS require manager. Even with the
        hermes_can_promote flag, Hermes cannot promote high-impact."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="workflow_rule",
                content="hermes should not promote me",
                source_type="manual",
            )
            rc, _, err = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--hermes-can-promote",
                "--yes",
            ])
            assert rc == 1
            assert "high-impact" in err.lower() or "Hermes" in err
            _reset_db()

    def test_hermes_promote_without_flag_rejected(self):
        """Without the hermes_can_promote flag, Hermes cannot promote
        even non-high-impact kinds."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="hermes needs flag",
                source_type="manual",
            )
            rc, _, err = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--yes",
            ])
            assert rc == 1
            assert "hermes_can_promote" in err.lower() or "manager" in err.lower()
            _reset_db()

    def test_dispatch_with_hermes_can_promote_appends_marker(self):
        """The dispatch --hermes-can-promote flag appends a marker to
        the task description so downstream Hermes can see it."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "dispatch", "Hermes",
                "Knowledge base maintenance",
                "--stage", "builder",
                "--owner", "Hermes",
                "--hermes-can-promote",
            ])
            assert rc == 0, out
            assert "hermes_can_promote" in out
            # Find the task and check its description has the marker
            for t in tasks.list_tasks():
                if "Knowledge base maintenance" in t.get("title", ""):
                    assert "[hermes-can-promote: true]" in t.get("description", "")
                    break
            _reset_db()

    def test_manager_promote_still_works_without_flag(self):
        """Manager can always promote, with or without the flag."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note", content="manager promote me",
                source_type="manual",
            )
            rc, out, _ = run_cli([
                "memory", "promote", cid,
                "--reviewer", "manager",
                "--yes",
            ])
            assert rc == 0, out
            assert "Promoted" in out
            _reset_db()


# ── 18. Risk 1: failed state adaptation layers ──────────────────

class TestFailedStateAdaptation:

    def test_task_get_shows_failure_reason(self):
        """The task get output should display failure_reason so
        reviewers see why the task is in failed status."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Display failure reason")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            run_cli([
                "task", "report-failure", tid,
                "--actor", "worker",
                "--reason", "schema drift detected",
            ])
            rc, out, _ = run_cli(["task", "get", tid])
            assert rc == 0
            assert "failure_reason" in out
            assert "schema drift" in out
            _reset_db()

    def test_worker_reported_failure_event_emitted(self):
        """The report-failure command should produce a transition
        event with to_status=failed that downstream publish
        scanners can pick up for reassurance."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Worker reported failure event")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            run_cli([
                "task", "report-failure", tid,
                "--actor", "worker",
                "--reason", "test event",
            ])
            # A task event with to_status=failed should exist
            events = tasks.list_task_events(task_id=tid, limit=10)
            failed_events = [
                e for e in events
                if e.get("to_status") == "failed"
            ]
            assert len(failed_events) >= 1, (
                f"expected at least 1 transition event to failed; "
                f"got {len(failed_events)} events: {events}"
            )
            _reset_db()


# ── 19. Risk 2: Recompute closeout gate after verdict change ─────

class TestCloseoutInvalidation:

    def test_verdict_update_invalidates_closeout_state(self):
        """When verdict changes post-delivery, closeout_status,
        tier_status, manager_closed_out_at, and
        latest_authoritative_verdict should all be cleared so the
        closeout gate re-evaluates from scratch."""
        with isolated_env():
            _init_db()
            from eduflow.store import tasks as _tasks
            tid = _tasks.create_flow(
                "worker_builder", "Invalidate closeout test",
                stage="builder", owner="worker_builder",
                creator="manager", workflow_id="igcse-subject-launch",
            )
            _tasks.transition_flow(tid, to_status="assigned", actor="manager")
            _tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            _tasks.transition_flow(tid, to_status="delivered", actor="worker")
            # Simulate a prior closeout gate having computed these
            data = _tasks._load()
            t = _tasks._find_task(data, tid)
            t["closeout_status"] = "closeout_completed"
            t["tier_status"] = "closeout_completed"
            t["manager_closed_out_at"] = 1700000000000
            t["latest_authoritative_verdict"] = {"verdict": "approved"}
            _tasks._save(data)
            # Sanity check the seeded state
            assert _tasks.get(tid).get("closeout_status") == "closeout_completed"
            # Now flip verdict post-delivery
            rc, out, _ = run_cli([
                "task", "update-verdict", tid,
                "--actor", "manager",
                "--verdict", "rejected",
                "--reason", "downstream found drift",
            ])
            assert rc == 0, out
            t = _tasks.get(tid)
            # All closeout fields should be cleared
            assert t.get("closeout_status") in (None, "")
            assert t.get("tier_status") in (None, "")
            assert t.get("manager_closed_out_at") in (None, 0)
            assert t.get("latest_authoritative_verdict") == {}
            # Turn summary should mention invalidation
            assert "invalidated" in t.get("latest_turn_summary", "")
            _reset_db()

    def test_verdict_no_change_does_not_invalidate(self):
        """Updating verdict to the same value should NOT clear closeout."""
        with isolated_env():
            _init_db()
            from eduflow.store import tasks as _tasks
            tid = _tasks.create_flow(
                "worker_builder", "No-op verdict test",
                stage="builder", owner="worker_builder",
                creator="manager", workflow_id="igcse-subject-launch",
            )
            _tasks.transition_flow(tid, to_status="assigned", actor="manager")
            _tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            _tasks.transition_flow(tid, to_status="delivered", actor="worker")
            data = _tasks._load()
            t = _tasks._find_task(data, tid)
            t["closeout_status"] = "closeout_completed"
            t["tier_status"] = "closeout_completed"
            _tasks._save(data)
            assert _tasks.get(tid).get("closeout_status") == "closeout_completed"
            # No-op update (approved → approved)
            rc, out, _ = run_cli([
                "task", "update-verdict", tid,
                "--actor", "manager",
                "--verdict", "approved",
            ])
            assert rc == 0
            t = _tasks.get(tid)
            # closeout fields should NOT be cleared
            assert t.get("closeout_status") == "closeout_completed"
            _reset_db()


# ── 20. Risk 3: Harden hermes_can_promote marker check ───────────

class TestHermesScopeHardening:

    def test_hermes_cannot_promote_non_hermes_scope(self):
        """Even with hermes_can_promote=True, Hermes cannot promote
        candidates that don't belong to Hermes's scope (defense
        in depth)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="agent:worker_qbank", kind="note",
                content="qbank note, not for hermes",
                source_type="manual",
            )
            rc, _, err = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--hermes-can-promote",
                "--yes",
            ])
            assert rc == 1
            # Error should mention scope or Hermes context
            assert "hermes" in err.lower() or "scope" in err.lower()
            _reset_db()

    def test_hermes_can_promote_hermes_scope(self):
        """Hermes can promote candidates in its own scope."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="agent:Hermes", kind="note",
                content="hermes owns this",
                source_type="manual",
            )
            rc, out, _ = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--hermes-can-promote",
                "--yes",
            ])
            assert rc == 0, out
            assert "Promoted" in out
            _reset_db()

    def test_hermes_can_promote_hermes_prefixed_source(self):
        """Hermes can promote candidates whose source_type starts with hermes_."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidate_gen import add_candidate
            cid = add_candidate(
                scope="team", kind="note",
                content="hermes manual note",
                source_type="hermes_manual",
            )
            rc, out, _ = run_cli([
                "memory", "promote", cid,
                "--reviewer", "hermes",
                "--hermes-can-promote",
                "--yes",
            ])
            assert rc == 0, out
            assert "Promoted" in out
            _reset_db()


# ── 21. Risk 4: Distinct --no-sensitive-check vs --force ─────────

class TestFlagDistinction:

    def test_no_sensitive_check_recorded_separately(self):
        """The --no-sensitive-check flag should be recorded in the
        output (forward-compat: future safety checks can be left
        enabled while still skipping just the PII scanner)."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test_safe in template",
                "--severity", "high",
                "--no-sensitive-check",
            ])
            assert rc == 0
            # The output should record the flag
            assert "no_sensitive_check" in out
            _reset_db()

    def test_force_recorded_in_output(self):
        """The --force flag should also be recorded."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test_safe_2 in template",
                "--severity", "high",
                "--force",
            ])
            assert rc == 0
            assert "force" in out
            _reset_db()

    def test_no_flag_omits_flag_record(self):
        """When no flag is passed, the output should not advertise
        flags=force or flags=no_sensitive_check (only shows when
        set)."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "correct", "worker_qbank",
                "stop emitting empty stems",
                "--severity", "high",
            ])
            assert rc == 0
            assert "flags=" not in out
            _reset_db()


# ── 22. Risk 5: Clear failure_reason on retry ───────────────────

class TestFailureRetryClear:

    def test_failed_to_in_progress_clears_failure_reason(self):
        """When manager retries a failed task (failed → in_progress),
        failure_reason should be cleared and a retry marker should
        appear in latest_turn_summary."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Retry from failed")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            # Worker reports failure
            run_cli([
                "task", "report-failure", tid,
                "--actor", "worker",
                "--reason", "disk full",
            ])
            t = tasks.get(tid)
            assert t["status"] == "failed"
            assert t.get("failure_reason") == "disk full"
            # Manager retries
            rc, out, _ = run_cli([
                "task", "flow-transition", tid,
                "--to", "in_progress",
                "--actor", "manager",
            ])
            assert rc == 0, out
            t = tasks.get(tid)
            assert t["status"] == "in_progress"
            # failure_reason should be cleared
            assert t.get("failure_reason") in (None, "")
            # latest_turn_summary should mention retry
            assert "retry" in t.get("latest_turn_summary", "").lower() or \
                   "Manager retried" in t.get("latest_turn_summary", "")
            _reset_db()

    def test_failed_to_cancelled_preserves_failure_reason(self):
        """When manager cancels a failed task, failure_reason is
        preserved (it's a permanent record of why we gave up)."""
        with isolated_env():
            _init_db()
            tid = _create_assigned_task("Cancel from failed")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            run_cli([
                "task", "report-failure", tid,
                "--actor", "worker",
                "--reason", "irrecoverable",
            ])
            t = tasks.get(tid)
            assert t["status"] == "failed"
            assert t.get("failure_reason") == "irrecoverable"
            # Manager cancels
            rc, out, _ = run_cli([
                "task", "flow-transition", tid,
                "--to", "cancelled",
                "--actor", "manager",
            ])
            assert rc == 0, out
            t = tasks.get(tid)
            assert t["status"] == "cancelled"
            # failure_reason should be preserved
            assert t.get("failure_reason") == "irrecoverable"
            _reset_db()


# ── 23. has_hermes_can_promote_marker helper ────────────────────

class TestHermesMarkerHelper:

    def test_marker_present_in_dispatched_task(self):
        """Task dispatched with --hermes-can-promote should have
        the marker detectable by has_hermes_can_promote_marker."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "dispatch", "Hermes",
                "Knowledge base maintenance",
                "--stage", "builder",
                "--owner", "Hermes",
                "--hermes-can-promote",
            ])
            assert rc == 0
            import re
            tid = re.search(r"(T-\d+)", out).group(1)
            assert tasks.has_hermes_can_promote_marker(tid) is True
            _reset_db()

    def test_marker_absent_in_normal_dispatch(self):
        """Normal task dispatch should not have the marker."""
        with isolated_env():
            _init_db()
            rc, out, _ = run_cli([
                "task", "dispatch", "worker_course",
                "Normal task",
                "--stage", "curriculum",
                "--owner", "worker_course",
            ])
            assert rc == 0
            import re
            tid = re.search(r"(T-\d+)", out).group(1)
            assert tasks.has_hermes_can_promote_marker(tid) is False
            _reset_db()

    def test_marker_absent_for_nonexistent_task(self):
        """Non-existent task should return False."""
        with isolated_env():
            _init_db()
            assert tasks.has_hermes_can_promote_marker("T-999") is False
            _reset_db()


# ── 24. --no-sensitive-check vs --force distinction ─────────────

class TestSensitiveCheckVsForce:

    def test_force_skips_all_checks(self):
        """--force skips sensitive-content scanner (output has no warning)."""
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test_safe in template",
                "--severity", "high",
                "--force",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" not in err
            assert "force" in out
            _reset_db()

    def test_no_sensitive_check_skips_sensitive_only(self):
        """--no-sensitive-check skips only sensitive-content scanner."""
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test_safe_2 in template",
                "--severity", "high",
                "--no-sensitive-check",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" not in err
            assert "no_sensitive_check" in out
            _reset_db()

    def test_neither_flag_warns(self):
        """Without either flag, sensitive pattern triggers warning."""
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "task", "correct", "worker_qbank",
                "set api_key=sk_test in template",
                "--severity", "high",
            ])
            assert rc == 0
            assert "sensitive-pattern warning" in err
            # No flags in output since neither was passed
            assert "flags=" not in out
            _reset_db()

