"""Tests for store/tasks.py — local task store."""
from __future__ import annotations


from helpers import isolated_env
from eduflow.store import tasks


# ── create ────────────────────────────────────────────────────────


def test_create_returns_task_id_and_persists():
    with isolated_env():
        tid = tasks.create("worker", "do thing")
        assert tid == "T-1"
        rows = tasks.list_tasks()
        assert len(rows) == 1
        assert rows[0]["title"] == "do thing"
        assert rows[0]["status"] == "待处理"


def test_ids_increment_across_creates():
    with isolated_env():
        a = tasks.create("x", "first")
        b = tasks.create("y", "second")
        assert a == "T-1" and b == "T-2"


def test_create_with_metadata_persists_creator_and_description():
    with isolated_env():
        tid = tasks.create("worker", "fix X",
                           description="root cause is Y",
                           creator="manager")
        t = tasks.get(tid)
        assert t["creator"] == "manager"
        assert t["description"] == "root cause is Y"


def test_create_empty_title_rejects():
    with isolated_env():
        try:
            tasks.create("worker", "   ")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError on empty title")


# ── update ────────────────────────────────────────────────────────


def test_update_status_advances_state():
    with isolated_env():
        tid = tasks.create("w", "task")
        assert tasks.update(tid, status="进行中") is True
        assert tasks.get(tid)["status"] == "进行中"


def test_update_invalid_status_rejects():
    with isolated_env():
        tid = tasks.create("w", "task")
        try:
            tasks.update(tid, status="not-a-status")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_update_missing_task_returns_false():
    with isolated_env():
        assert tasks.update("T-99", status="已完成") is False


def test_update_terminal_status_sets_completed_at():
    with isolated_env():
        tid = tasks.create("w", "x")
        tasks.update(tid, status="已完成")
        t = tasks.get(tid)
        assert t["completed_at"] is not None


def test_update_back_from_terminal_clears_completed_at():
    with isolated_env():
        tid = tasks.create("w", "x")
        tasks.update(tid, status="已完成")
        tasks.update(tid, status="进行中")
        assert tasks.get(tid)["completed_at"] is None


def test_update_only_changes_specified_fields():
    with isolated_env():
        tid = tasks.create("w1", "title-1", description="d-1", creator="c-1")
        tasks.update(tid, status="进行中")
        t = tasks.get(tid)
        # other fields untouched
        assert t["assignee"] == "w1"
        assert t["title"] == "title-1"
        assert t["description"] == "d-1"
        assert t["creator"] == "c-1"


def test_update_can_reassign_and_retitle():
    with isolated_env():
        tid = tasks.create("w1", "old", description="old-d")
        tasks.update(tid, assignee="w2", title="new", description="new-d")
        t = tasks.get(tid)
        assert (t["assignee"], t["title"], t["description"]) == ("w2", "new", "new-d")


# ── list/get ──────────────────────────────────────────────────────


def test_list_filters_by_status():
    with isolated_env():
        a = tasks.create("w", "a")
        b = tasks.create("w", "b")
        tasks.update(a, status="已完成")
        only_done = tasks.list_tasks(status="已完成")
        only_open = tasks.list_tasks(status="待处理")
        assert [t["id"] for t in only_done] == [a]
        assert [t["id"] for t in only_open] == [b]


def test_list_filters_by_assignee():
    with isolated_env():
        tasks.create("alice", "task-a")
        tasks.create("bob", "task-b")
        tasks.create("alice", "task-a2")
        out = tasks.list_tasks(assignee="alice")
        assert {t["title"] for t in out} == {"task-a", "task-a2"}


def test_list_returns_empty_when_store_missing():
    with isolated_env():
        assert tasks.list_tasks() == []


def test_get_returns_none_for_unknown_id():
    with isolated_env():
        assert tasks.get("T-doesnotexist") is None


def test_list_sorted_by_id():
    with isolated_env():
        for i in range(5):
            tasks.create(f"w{i}", f"task {i}")
        rows = tasks.list_tasks()
        assert [t["id"] for t in rows] == ["T-1", "T-2", "T-3", "T-4", "T-5"]


# ── package 5: subject inventory extension ────────────────────────


def _make_approved_subject(title, evidence=None):
    """Helper: create an approved curriculum subject task.

    Package 3: passes a `verdict_target` matching the title so the
    derived verdict_scope = "full_subject" — required for subject
    closeout to be authorized.

    Package 7 (Revision-First Gate): merges the caller's evidence
    with the REQUIRED_EVIDENCE_PACKET_FIELDS defaults so that tests
    using this helper can still close out subjects under the new
    evidence packet gate. Callers can override any field.
    """
    tid = tasks.create_flow(
        "worker_course", title,
        stage="curriculum", owner="worker_course", creator="manager",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    packet = {
        "workflow_id": "igcse-subject-launch",
        "task_id": tid,
        "batch_range": "1-3",
        "items_count": 300,
        "qql_count": 300,
        "manifest_evidence": "manifest_covered",
    }
    if evidence:
        packet.update(evidence)
    tasks.review_flow(
        tid,
        outcome="approve",
        actor="review_course",
        review_reason="approved_for_delivery",
        evidence_packet=packet,
        verdict_target=title,
    )
    return tid


def _closeout_subject_for_test(tid):
    """Close out a subject in unit tests (no real content dir exists)."""
    return tasks.manager_closeout_subject(
        tid, actor="manager", skip_subject_verifier=True,
    )


def test_subject_inventory_includes_outline_and_manifest_counts():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            evidence_packet={
                "sampled_topic_count": 8,
                "items_mapping_count": 150,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
            },
        )
        inventory = tasks.subject_inventory_extended()
        assert len(inventory) == 1
        row = inventory[0]
        assert row["outline_topic_count"] == 8
        assert row["manifest_covered_count"] == 150


def test_subject_inventory_outline_zero_when_missing():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="approve", actor="review_course", evidence_packet={})
        inventory = tasks.subject_inventory_extended()
        row = inventory[0]
        assert row["outline_topic_count"] == 0
        assert row["manifest_covered_count"] == 0


# ── package 5: next_batch_continuation_gate ────────────────────────


def test_next_batch_continuation_gate_recommends_next_batch_when_subject_incomplete():
    """Latest batch delivered + subject not closeout_completed → recommend next batch."""
    with isolated_env():
        tid = _make_approved_subject(
            "IGCSE Physics 0625 Batch 1",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 50,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 50,
                "item_count": 50,
            },
        )
        tasks.batch_closeout(tid, actor="manager")
        gate = tasks.next_batch_continuation_gate(tid)
        assert gate["should_continue"] is True
        assert gate["reason"] == "latest_batch_delivered_subject_incomplete"
        assert gate["subject_id"] == tid
        assert gate["recommended_action"] == "continue_next_batch"


def test_next_batch_continuation_gate_no_action_when_subject_closeout_completed():
    """Subject already closeout_completed → no continuation needed."""
    with isolated_env():
        tid = _make_approved_subject(
            "IGCSE Physics 0625 300 QA 正式完成",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        _closeout_subject_for_test(tid)
        gate = tasks.next_batch_continuation_gate(tid)
        assert gate["should_continue"] is False
        assert gate["reason"] == "subject_closeout_completed"


def test_next_batch_continuation_gate_no_action_for_non_subject():
    """Non-subject task → not_subject, no continuation."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder", "Fix Router",
            stage="builder", owner="worker_builder", creator="manager",
        )
        gate = tasks.next_batch_continuation_gate(tid)
        assert gate["should_continue"] is False
        assert gate["reason"] == "not_subject"


# ── package 5: select_next_subject ─────────────────────────────────


def test_select_next_subject_excludes_closeout_completed():
    """Already completed subjects should not be selected."""
    with isolated_env():
        done_tid = _make_approved_subject(
            "IGCSE Physics 0625 正式完成",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        _closeout_subject_for_test(done_tid)
        next_tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        result = tasks.select_next_subject()
        assert result is not None
        assert result["subject_id"] == next_tid
        # New subject has no assets yet, so reason reflects fallback/first candidate
        assert "reason" in result


def test_select_next_subject_prefers_subjects_with_assets():
    """Subjects with existing evidence should be preferred over empty ones."""
    with isolated_env():
        empty_tid = tasks.create_flow(
            "worker_course", "IGCSE Biology 0610",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        with_assets_tid = _make_approved_subject(
            "IGCSE Chemistry 0620 Batch 1",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 50,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 50,
                "item_count": 50,
            },
        )
        tasks.batch_closeout(with_assets_tid, actor="manager")
        result = tasks.select_next_subject()
        assert result is not None
        assert result["subject_id"] == with_assets_tid


def test_select_next_subject_avoids_recent_repetition():
    """If the same subject was just worked on, it should be deprioritized."""
    with isolated_env():
        physics_tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 Batch 3",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow(physics_tid, to_status="assigned", actor="manager")
        tasks.transition_flow(physics_tid, to_status="in_progress", actor="worker_course")

        chemistry_tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        # Physics is in_progress (most recent), Chemistry is queued
        result = tasks.select_next_subject()
        assert result is not None
        # Should prefer Chemistry since Physics is the most recently active
        assert result["subject_id"] == chemistry_tid


def test_select_next_subject_returns_none_when_all_completed():
    """When all subjects are closeout_completed, return None."""
    with isolated_env():
        tid = _make_approved_subject(
            "IGCSE Physics 0625 正式完成",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        _closeout_subject_for_test(tid)
        result = tasks.select_next_subject()
        assert result is None


def test_select_next_subject_returns_none_when_no_subjects():
    """When there are no subjects at all, return None."""
    with isolated_env():
        result = tasks.select_next_subject()
        assert result is None


def test_select_next_subject_auditable_explanation():
    """Result should include why selected and why others were not."""
    with isolated_env():
        done_tid = _make_approved_subject(
            "IGCSE Physics 0625 正式完成",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        _closeout_subject_for_test(done_tid)
        next_tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        result = tasks.select_next_subject()
        assert result is not None
        assert "selected" in result
        assert "skipped" in result
        # Skipped should mention Physics was closeout_completed
        skipped_ids = [s["subject_id"] for s in result["skipped"]]
        assert done_tid in skipped_ids


# ── package 7 (Revision-First Gate): revision_priority helpers ────


def test_revision_priority_default_is_empty():
    """New task has revision_priority == '' or absent."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        t = tasks.get(tid)
        assert t.get("revision_priority", "") == ""


def test_set_revision_priority_minor_on_reject_verdict():
    """When a task transitions to verdict=rejected via the review helper,
    revision_priority becomes 'minor'."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
        )
        t = tasks.get(tid)
        assert t["verdict"] == "rejected"
        assert t.get("revision_priority") == "minor"


def test_set_revision_priority_manager_on_manager_action():
    """verdict=manager_action → revision_priority='manager'."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="review_course",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        t = tasks.get(tid)
        assert t["verdict"] == "manager_action"
        assert t.get("revision_priority") == "manager"


def test_clear_revision_priority_requires_ack():
    """revision_priority can only be cleared when an explicit
    clear_revision_priority call is made — not auto-cleared on
    status change."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
        )
        # After reject verdict, revision_priority should be set
        t = tasks.get(tid)
        assert t.get("revision_priority") == "minor"

        # Transition to a different status — revision_priority must
        # persist (not auto-cleared). Use a legal transition path
        # (in_progress -> blocked) to verify persistence.
        tasks.transition_flow(tid, to_status="blocked", actor="worker_course")
        t = tasks.get(tid)
        assert t.get("revision_priority") == "minor"

        # Only the explicit clear_revision_priority call clears it
        tasks.clear_revision_priority(tid, actor="worker_course")
        t = tasks.get(tid)
        assert t.get("revision_priority", "") == ""


def test_workflow_gate_status_returns_revision_first_when_set():
    """workflow_gate_status() returns gate='revision_first' with a clear
    next_action when revision_priority is set."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
        )
        t = tasks.get(tid)
        # Confirm revision_priority is set (prerequisite)
        assert t.get("revision_priority") == "minor"

        gate = tasks.workflow_gate_status(t)
        assert gate["gate"] == "revision_first"
        assert "next_action" in gate
        assert gate["next_action"]  # must be non-empty
        assert gate.get("revision_priority") == "minor"
