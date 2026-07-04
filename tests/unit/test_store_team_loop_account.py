from helpers import isolated_env
from eduflow.store import tasks, team_loop_account


def test_team_loop_account_derives_repair_phase_from_review_reject():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="reject", actor="review_course")

        account = team_loop_account.build(tid)
        assert account["workflow_id"] == "igcse-subject-launch"
        assert account["phase"] == "team_repair_needed"
        assert account["cycle_count"] == 1
        assert account["next_owner"] == "worker_course"
        assert account["recommended_action"] == "send_repair_handoff"


def test_team_loop_account_keeps_check_layers_separate():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair runtime",
            stage="builder",
            owner="worker_builder",
            workflow_id="igcse-subject-launch",
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

        account = team_loop_account.build(tid)
        assert account["agent_loop"]["status"] == "passed"
        assert account["self_check_status"] == "passed"
        assert account["review_check_status"] == "pending"
        assert account["manager_closeout_status"] == "blocked"
        assert account["phase"] != "closed"


def test_team_loop_account_event_contract_counts_reject_events_only():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="reject", actor="review_course")
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="repair_needed",
            actor="manager",
        )

        events = tasks.list_task_events(task_id=tid, limit=20)
        assert any(
            event.get("event_type") == "status_changed"
            and event.get("after", {}).get("verdict") == "rejected"
            for event in events
        )
        assert team_loop_account.build(tid)["cycle_count"] == 1


def test_team_loop_account_event_contract_requires_review_fields():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="reject", actor="review_course")

        event = tasks.list_task_events(task_id=tid, limit=20)[-1]
        assert event["task_id"] == tid
        assert event["event_type"] == "status_changed"
        assert event["actor"] == "review_course"
        assert event["before"]["verdict"] == "pending"
        assert event["after"]["verdict"] == "rejected"
        assert event["after"]["review_reason"] == "changes_requested"
        assert "verdict" in event["meaningful_changes"]
        assert "review_reason" in event["meaningful_changes"]
