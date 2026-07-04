"""Tests for the flow-task state machine in store/tasks.py."""
from __future__ import annotations

from helpers import attr_patch, isolated_env
from eduflow.store import tasks


def test_create_flow_task_defaults_to_queued_pending_verdict():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Build Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        row = tasks.get(tid)
        assert row["schema_version"] == 2
        assert row["stage"] == "curriculum"
        assert row["status"] == "queued"
        assert row["owner"] == "worker_course"
        assert row["creator"] == "manager"
        assert row["verdict"] == "pending"
        assert row["manager_action_type"] == ""
        assert row["review_reason"] == ""
        assert row["latest_turn_summary"] == "Task created and queued."
        assert row["completed_at"] is None


def test_set_loop_evidence_updates_only_loop_fields():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair runtime verifier",
            stage="builder",
            owner="worker_builder",
        )

        assert tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="repair_needed",
            loop_cycle_count=1,
            loop_stop_reason="",
            loop_recommended_action="send_builder_handoff",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        row = tasks.get(tid)
        assert row["loop_run_id"] == "L-000001"
        assert row["loop_status"] == "repair_needed"
        assert row["loop_cycle_count"] == 1
        assert row["loop_recommended_action"] == "send_builder_handoff"
        assert row["status"] == "queued"
        assert row["verdict"] == "pending"


def test_set_loop_evidence_rejects_unknown_status():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair",
            stage="builder",
            owner="worker_builder",
        )
        try:
            tasks.set_loop_evidence(
                tid,
                loop_run_id="L-1",
                loop_status="magic",
                actor="manager",
            )
        except ValueError as e:
            assert "invalid loop_status" in str(e)
        else:
            raise AssertionError("expected ValueError")


def test_loop_evidence_self_check_pass_does_not_count_as_review_or_closeout():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair",
            stage="builder",
            owner="worker_builder",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="passed",
            self_check_status="passed",
            review_check_status="pending",
            manager_closeout_status="blocked",
            actor="worker_builder",
        )

        row = tasks.get(tid)
        assert row["self_check_status"] == "passed"
        assert row["review_check_status"] == "pending"
        assert row["manager_closeout_status"] == "blocked"
        assert row["verdict"] == "pending"
        assert row["closeout_status"] == ""


def test_create_flow_task_rejects_invalid_stage_status_combo():
    with isolated_env():
        try:
            tasks.create_flow(
                "worker_qbank",
                "Import SAT set A",
                stage="qbank",
                owner="worker_qbank",
                status="submitted_for_review",
            )
        except ValueError as e:
            assert "invalid status" in str(e)
            assert "qbank" in str(e)
        else:
            raise AssertionError("expected ValueError for illegal stage/status combo")


def test_transition_flow_rejects_blocked_to_delivered():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair router restart loop",
            stage="builder",
            owner="worker_builder",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="blocked", actor="worker")
        try:
            tasks.transition_flow(tid, to_status="delivered", actor="manager")
        except ValueError as e:
            assert "blocked" in str(e)
            assert "delivered" in str(e)
        else:
            raise AssertionError("expected ValueError for blocked -> delivered")


def test_transition_flow_enforces_actor_permissions():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft topic notes",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        try:
            tasks.transition_flow(tid, to_status="delivered", actor="worker")
        except ValueError as e:
            assert "actor" in str(e)
            assert "worker" in str(e)
        else:
            raise AssertionError("expected ValueError for worker delivery")


def test_curriculum_task_cannot_be_delivered_by_manager_without_review_verdict():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 1",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        try:
            tasks.transition_flow(tid, to_status="delivered", actor="manager")
        except ValueError as e:
            assert "review verdict" in str(e)
        else:
            raise AssertionError("expected review gate to reject manager delivery")


def test_transition_flow_happy_path_sets_completed_at():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        row = tasks.get(tid)
        assert row["status"] == "delivered"
        assert row["verdict"] == "approved"
        assert row["completed_at"] is not None


def test_review_flow_reject_sets_in_progress_and_rejected_verdict():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.review_flow(tid, outcome="reject", actor="reviewer")
        row = tasks.get(tid)
        assert row["status"] == "in_progress"
        assert row["verdict"] == "rejected"
        assert row["review_reason"] == "changes_requested"
        assert row["latest_turn_summary"] == "Reviewer requested revisions and returned the task to in_progress."
        assert row["completed_at"] is None


def test_review_flow_manager_action_sets_blocked_and_manager_action_verdict():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.review_flow(tid, outcome="manager_action", actor="reviewer")
        row = tasks.get(tid)
        assert row["status"] == "blocked"
        assert row["verdict"] == "manager_action"
        assert row["needs_manager_action"] is True
        assert row["blocking_reason"] == "reviewer_requested_manager_action"
        assert row["manager_action_type"] == "manager_review_needed"
        assert row["review_reason"] == "reviewer_requested_manager_action"
        assert row["latest_turn_summary"] == "Reviewer requested manager action before the task can continue."
        assert row["completed_at"] is None


def test_resubmit_for_review_resets_verdict_to_pending():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.review_flow(tid, outcome="reject", actor="reviewer")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        row = tasks.get(tid)
        assert row["status"] == "submitted_for_review"
        assert row["verdict"] == "pending"
        assert row["needs_manager_action"] is False
        assert row["blocking_reason"] == ""
        assert row["completed_at"] is None


def test_worker_blocked_sets_default_blocking_reason():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair router loop",
            stage="builder",
            owner="worker_builder",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_builder")
        tasks.transition_flow(tid, to_status="blocked", actor="worker_builder")
        row = tasks.get(tid)
        assert row["status"] == "blocked"
        assert row["blocking_reason"] == "worker_blocked"
        assert row["needs_manager_action"] is False


def test_submit_for_review_moves_worker_task_into_review_queue():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.submit_for_review(tid, actor="worker")
        row = tasks.get(tid)
        assert row["status"] == "submitted_for_review"
        assert row["verdict"] == "pending"
        assert row["completed_at"] is None


def test_list_review_queue_returns_only_submitted_tasks():
    with isolated_env():
        t1 = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        t2 = tasks.create_flow(
            "worker_admissions",
            "Write visa checklist",
            stage="admissions",
            owner="worker_admissions",
        )
        tasks.transition_flow(t1, to_status="assigned", actor="manager")
        tasks.transition_flow(t1, to_status="in_progress", actor="worker")
        tasks.submit_for_review(t1, actor="worker")
        tasks.transition_flow(t2, to_status="assigned", actor="manager")
        rows = tasks.list_review_queue()
        assert [row["id"] for row in rows] == [t1]


def test_assign_reviewer_persists_on_flow_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        row = tasks.get(tid)
        assert row["reviewer"] == "reviewer_amy"


def test_submit_for_review_auto_assigns_default_reviewer_for_igcse_course_workflow():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
            stage="course",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        row = tasks.get(tid)
        assert row["stage"] == "curriculum"
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        row = tasks.get(tid)
        assert row["status"] == "submitted_for_review"
        assert row["reviewer"] == "review_course"
        assert "default reviewer review_course assigned by workflow" in row["latest_turn_summary"]


def test_manager_closeout_rejects_batch_package_scope():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="Batch pass.",
            evidence_packet={"files_sampled": ["Q-1.md"], "path_naming_result": "pass"},
        )
        try:
            tasks.manager_closeout_subject(tid, actor="manager", skip_subject_verifier=True)
        except ValueError as e:
            assert "batch-closeout" in str(e)
        else:
            raise AssertionError("expected ValueError for batch/package manager-closeout")


def test_batch_closeout_marks_package_without_subject_rollover():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="Batch pass.",
            evidence_packet={"files_sampled": ["Q-1.md"], "path_naming_result": "pass"},
        )
        assert tasks.batch_closeout(tid, actor="manager")
        row = tasks.get(tid)
        assert row["closeout_status"] == "batch_closeout_completed"
        gate = tasks.workflow_gate_status(row)
        assert gate["gate"] == "batch_closeout_gate"
        assert gate["gate_status"] == "passed"


def test_review_flow_rejects_non_assigned_reviewer():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        try:
            tasks.review_flow(tid, outcome="approve", actor="reviewer_bob")
        except ValueError as e:
            assert "assigned reviewer" in str(e)
        else:
            raise AssertionError("expected ValueError for mismatched reviewer")


def test_create_flow_emits_created_event():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Build Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        events = tasks.list_task_events()
        assert len(events) == 1
        ev = events[0]
        assert ev["task_id"] == tid
        assert ev["kind"] == "created"
        assert ev["event_type"] == "task_created"
        assert ev["schema_version"] == 2
        assert ev["correlation_id"] == tasks.get(tid)["correlation_id"]
        assert ev["lane"] == "curriculum"
        assert ev["to_status"] == "queued"
        assert ev["to_stage"] == "curriculum"
        assert ev["after"]["status"] == "queued"
        assert ev["before"] is None


def test_transition_flow_emits_diff_event():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        events = tasks.list_task_events()
        assert len(events) == 2
        ev = events[-1]
        assert ev["task_id"] == tid
        assert ev["kind"] == "transition"
        assert ev["event_type"] == "status_changed"
        assert ev["actor"] == "manager"
        assert ev["from_status"] == "queued"
        assert ev["to_status"] == "assigned"
        assert ev["from_owner"] == "worker_course"
        assert ev["to_owner"] == "worker_course"
        assert ev["before"]["status"] == "queued"
        assert ev["after"]["status"] == "assigned"
        assert ev["changes"]["status"] == {"before": "queued", "after": "assigned"}
        assert ev["meaningful_changes"]["status"] == {"before": "queued", "after": "assigned"}


def test_review_flow_persists_explicit_manager_semantics():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            latest_turn_summary="Reviewer needs manager to confirm scope before rewrite.",
            manager_action_type="clarify_scope",
        )
        row = tasks.get(tid)
        assert row["manager_action_type"] == "clarify_scope"
        assert row["review_reason"] == "missing_scope_confirmation"
        assert row["latest_turn_summary"] == "Reviewer needs manager to confirm scope before rewrite."
        event = tasks.list_task_events(task_id=tid)[-1]
        assert event["meaningful_changes"]["manager_action_type"] == {
            "before": "",
            "after": "clarify_scope",
        }
        assert event["meaningful_changes"]["review_reason"] == {
            "before": "",
            "after": "missing_scope_confirmation",
        }
        assert event["meaningful_changes"]["latest_turn_summary"] == {
            "before": "Worker submitted the latest turn for review.",
            "after": "Reviewer needs manager to confirm scope before rewrite.",
        }


def test_review_flow_persists_scope_and_evidence_packet():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        evidence = {
            "files_sampled": ["Q-3.2-01.md", "Q-3.2-08.md"],
            "items_mapping_count": 9,
            "q_ids_checked": ["Q-3.2-01", "Q-3.2-08"],
            "calculation_or_concept_checks": ["offsetting compensating error verified"],
            "path_naming_result": "pass",
        }
        assert tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="Review passed with evidence packet.",
            scope_topic="Accounting 3.2",
            scope_files=["Q-3.2-01.md", "Q-3.2-08.md"],
            verdict_target="Accounting 3.2 revised QA",
            evidence_packet=evidence,
        )
        row = tasks.get(tid)
        assert row["scope_topic"] == "Accounting 3.2"
        assert row["scope_files"] == ["Q-3.2-01.md", "Q-3.2-08.md"]
        assert row["verdict_target"] == "Accounting 3.2 revised QA"
        assert row["evidence_packet"] == evidence
        event = tasks.list_task_events(task_id=tid)[-1]
        assert event["meaningful_changes"]["evidence_packet"]["after"] == evidence


def test_subject_closeout_gate_rejects_artifact_or_worker_completion_without_review():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Expected 300 QA / 25 items",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        row = tasks.get(tid)
        gate = tasks.subject_closeout_status(row)
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"
        assert gate["review_status"] == "not_approved"
        assert gate["recommended_action"] == "wait_for_review_approval"


def test_subject_closeout_gate_blocks_missing_evidence_packet():
    with isolated_env():
        tid = _approved_subject_task(evidence={})
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["closeout_status"] == "closeout_blocked_missing_evidence"
        assert gate["recommended_action"] == "request_review_evidence_packet"


def test_subject_closeout_gate_blocks_count_out_of_range():
    with isolated_env():
        tid_low = _approved_subject_task(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 25,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 25,
        })
        low = tasks.subject_closeout_status(tasks.get(tid_low))
        assert low["closeout_status"] == "closeout_blocked_count_out_of_range"
        assert low["qa_count"] == 299

        tid_high = _approved_subject_task(title="IGCSE Chemistry 0620", evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 501,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 501,
            "item_count": 501,
        })
        high = tasks.subject_closeout_status(tasks.get(tid_high))
        assert high["closeout_status"] == "closeout_blocked_count_out_of_range"
        assert high["item_count"] == 501


def test_subject_quality_standard_and_qbank_readiness_are_derived_from_evidence():
    with isolated_env():
        tid = _approved_subject_task(evidence={
            "files_sampled": ["Q-1.md", "Q-2.md"],
            "items_mapping_count": 320,
            "q_ids_checked": ["Q-1", "Q-2"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 320,
            "item_count": 320,
            "sampled_topic_count": 12,
            "missing_topic_count": 0,
            "qbank_readiness": "qbank_ready",
        })
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["qa_standard"] == "qa_standard_met"
        assert gate["qa_min"] == 300
        assert gate["qa_max"] == 500
        assert gate["qbank_readiness"] == "qbank_ready"
        assert gate["recommended_qbank_action"] == "approve_subject_for_qbank_seed"


def test_subject_qbank_readiness_distinguishes_low_volume_and_missing_mapping():
    with isolated_env():
        low = _approved_subject_task(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 299,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 299,
            "qbank_readiness": "qbank_ready",
        })
        low_gate = tasks.subject_closeout_status(tasks.get(low))
        assert low_gate["qbank_readiness"] == "qbank_blocked_low_volume"
        assert low_gate["recommended_qbank_action"] == "request_worker_course_expand_qa"

        missing_mapping = _approved_subject_task(
            title="IGCSE Chemistry 0620",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
                "sampled_topic_count": 8,
                "missing_topic_count": 1,
            },
        )
        mapping_gate = tasks.subject_closeout_status(tasks.get(missing_mapping))
        assert mapping_gate["qbank_readiness"] == "qbank_blocked_missing_mapping"
        assert mapping_gate["recommended_qbank_action"] == "request_review_course_file_evidence"


def test_subject_closeout_gate_ready_and_manager_closeout_completed():
    with isolated_env():
        tid = _approved_subject_task(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 300,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 300,
            "item_count": 300,
        })
        ready = tasks.subject_closeout_status(tasks.get(tid))
        assert ready["closeout_status"] == "closeout_ready"
        assert ready["recommended_action"] == "manager_formal_closeout"

        assert tasks.manager_closeout_subject(
            tid, actor="manager", skip_subject_verifier=True,
        )
        done = tasks.subject_closeout_status(tasks.get(tid))
        assert done["closeout_status"] == "closeout_completed"
        assert done["closeout_status"] == tasks.get(tid)["closeout_status"]
        assert tasks.get(tid)["manager_closed_out_at"] is not None


def test_subject_inventory_orders_next_candidates_after_completed_subject():
    with isolated_env():
        done_id = _approved_subject_task(
            title="IGCSE Business Studies 0450",
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
        tasks.manager_closeout_subject(done_id, actor="manager", skip_subject_verifier=True)
        tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        rows = tasks.subject_inventory()
        by_subject = {row["subject_name"]: row for row in rows}
        assert by_subject["IGCSE Business Studies 0450"]["closeout_status"] == "closeout_completed"
        assert by_subject["IGCSE Accounting 0452"]["next_candidate_rank"] == 1


def _approved_subject_task(title="IGCSE Business Studies 0450", evidence=None):
    tid = tasks.create_flow(
        "worker_course",
        title,
        stage="curriculum",
        owner="worker_course",
        creator="manager",
        description="Subject final batch 正式完成",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    tasks.review_flow(
        tid,
        outcome="approve",
        actor="review_course",
        review_reason="approved_for_delivery",
        latest_turn_summary="全部 10 批次正式完成，review approved.",
        evidence_packet=evidence or {},
        scope_topic=title,
        verdict_target=title,
    )
    return tid


def test_review_flow_rejects_invalid_manager_action_type():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        try:
            tasks.review_flow(
                tid,
                outcome="manager_action",
                actor="reviewer_amy",
                manager_action_type="invented_taxonomy",
            )
        except ValueError as e:
            assert "invalid manager_action_type" in str(e)
        else:
            raise AssertionError("expected ValueError for invalid manager_action_type")


def test_review_flow_rejects_invalid_review_reason():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        try:
            tasks.review_flow(
                tid,
                outcome="reject",
                actor="reviewer_amy",
                review_reason="rewrite_more",
            )
        except ValueError as e:
            assert "invalid review_reason" in str(e)
        else:
            raise AssertionError("expected ValueError for invalid review_reason")


def test_review_flow_reject_outcome_disallows_manager_action_type():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        try:
            tasks.review_flow(
                tid,
                outcome="reject",
                actor="reviewer_amy",
                manager_action_type="clarify_scope",
            )
        except ValueError as e:
            assert "manager_action_type is only allowed" in str(e)
        else:
            raise AssertionError("expected ValueError for reject with manager_action_type")


def test_flow_events_get_unique_ids_even_same_millisecond():
    with isolated_env(), attr_patch(tasks, now_ms=lambda: 1781770380002):
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        events = tasks.list_task_events()
        assert len(events) == 2
        assert events[0]["created_at"] == events[1]["created_at"]
        assert events[0]["event_id"] != events[1]["event_id"]


def test_legacy_task_update_does_not_emit_flow_event():
    with isolated_env():
        tid = tasks.create("worker", "legacy task")
        tasks.update(tid, status="进行中")
        assert tasks.list_task_events() == []


def test_assign_reviewer_emits_reviewer_assigned_event():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        ev = tasks.list_task_events()[-1]
        assert ev["event_type"] == "reviewer_assigned"
        assert ev["meaningful_changes"]["reviewer"] == {
            "before": "",
            "after": "reviewer_amy",
        }


def test_get_preserves_legacy_semantic_values_on_read():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        with tasks._locked():
            data = tasks._load()
            row = next(task for task in data["tasks"] if task["id"] == tid)
            row["manager_action_type"] = "legacy_manager_phrase"
            row["review_reason"] = "legacy_review_phrase"
            tasks._save(data)
        reloaded = tasks.get(tid)
        assert reloaded is not None
        assert reloaded["manager_action_type"] == "legacy_manager_phrase"
        assert reloaded["review_reason"] == "legacy_review_phrase"
