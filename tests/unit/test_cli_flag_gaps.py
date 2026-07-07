"""Tests for CLI flag coverage that closes the production-contract pilot gaps.

These two CLI surfaces were found missing during pilot T-122 (2026-07-07):

1. `task review --reject` did not accept `--required-fix` / `--blocking-file`
   repeatable flags. Without these, the read-model's `failed_checks` /
   `evidence_refs` are incomplete.

2. `eduflow send` did not accept `--task-id`. Without it, handoff
   messages were decoupled from the task they repaired; the read-model's
   `loop-contract.delivery` / `readiness-check.delivery` could not
   surface the handoff.

Both gaps are out of Package 0-7 scope but pilot-blocking. This test
file is the regression net for the small follow-up patches.
"""
from __future__ import annotations

from helpers import isolated_env, run_cli
from eduflow.store import local_facts, tasks


# ── task review --required-fix / --blocking-file ─────────────────


def _make_submitted_task():
    tid = tasks.create_flow(
        "worker_course",
        "review-flag-pilot",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.submit_for_review(tid, actor="worker_course")
    return tid


def test_task_review_accepts_required_fix_repeatable():
    with isolated_env():
        tid = _make_submitted_task()
        rc, out, err = run_cli([
            "task", "review", tid,
            "--actor", "review_course",
            "--reject",
            "--reason", "quality_not_met",
            "--required-fix", "expand per-topic items to 9",
            "--required-fix", "fix QQL-to-items mapping",
        ])
        assert rc == 0, err or out
        task = tasks.get(tid)
        av = task.get("latest_authoritative_verdict") or {}
        assert av.get("required_fix") == [
            "expand per-topic items to 9",
            "fix QQL-to-items mapping",
        ]
        assert task.get("required_fix") == [
            "expand per-topic items to 9",
            "fix QQL-to-items mapping",
        ]


def test_task_review_accepts_blocking_file_repeatable():
    with isolated_env():
        tid = _make_submitted_task()
        rc, out, err = run_cli([
            "task", "review", tid,
            "--actor", "review_course",
            "--reject",
            "--reason", "quality_not_met",
            "--blocking-file", "items/T1.1.md",
            "--blocking-file", "items/T1.2.md",
        ])
        assert rc == 0, err or out
        task = tasks.get(tid)
        av = task.get("latest_authoritative_verdict") or {}
        assert av.get("blocking_files") == ["items/T1.1.md", "items/T1.2.md"]
        assert task.get("blocking_files") == ["items/T1.1.md", "items/T1.2.md"]


def test_task_review_combines_required_fix_and_blocking_file():
    with isolated_env():
        tid = _make_submitted_task()
        rc, out, err = run_cli([
            "task", "review", tid,
            "--actor", "review_course",
            "--reject",
            "--reason", "quality_not_met",
            "--required-fix", "expand per-topic items to 9",
            "--blocking-file", "items/T1.1.md",
        ])
        assert rc == 0, err or out
        task = tasks.get(tid)
        av = task.get("latest_authoritative_verdict") or {}
        assert av.get("required_fix") == ["expand per-topic items to 9"]
        assert av.get("blocking_files") == ["items/T1.1.md"]


def test_task_review_no_fix_flags_still_works():
    """Sanity: rejection without --required-fix / --blocking-file still works."""
    with isolated_env():
        tid = _make_submitted_task()
        rc, out, err = run_cli([
            "task", "review", tid,
            "--actor", "review_course",
            "--reject",
            "--reason", "quality_not_met",
        ])
        assert rc == 0, err or out
        task = tasks.get(tid)
        assert task.get("verdict") == "rejected"
        av = task.get("latest_authoritative_verdict") or {}
        # No required_fix passed → store keeps it as []
        assert av.get("required_fix") == []


# ── eduflow send --task-id ───────────────────────────────────────


def test_send_accepts_task_id_flag():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "send-task-id-pilot",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        rc, out, err = run_cli([
            "send", "worker_course", "manager",
            "please repair section 2.1",
            "高",
            "--task-id", tid,
            "--no-inject",  # don't actually wake the pane
        ])
        assert rc == 0, err or out
        # Find the message we just sent
        msgs = [m for m in local_facts.list_all_messages() if m.get("to") == "worker_course"]
        assert msgs, "no message appended"
        latest = msgs[-1]
        assert latest.get("task_id") == tid


def test_send_without_task_id_has_empty_task_id():
    with isolated_env():
        tasks.create_flow("worker_course", "no-task-id-pilot", stage="curriculum", owner="worker_course")
        rc, out, err = run_cli([
            "send", "worker_course", "manager",
            "no task id here",
            "中",
            "--no-inject",
        ])
        assert rc == 0, err or out
        msgs = [m for m in local_facts.list_all_messages() if m.get("to") == "worker_course"]
        latest = msgs[-1]
        assert latest.get("task_id") == "" or latest.get("task_id") is None


def test_send_task_id_enables_loop_contract_delivery_lookup():
    """End-to-end: send --task-id should make loop-contract see the handoff."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "end-to-end-loop-contract",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="quality_not_met",
            required_fix=["fix q1"],
            blocking_files=["items/q1.md"],
        )
        # Send handoff with --task-id link
        rc, _, err = run_cli([
            "send", "worker_course", "manager",
            "repair q1",
            "高",
            "--task-id", tid,
            "--no-inject",
        ])
        assert rc == 0, err
        # Now loop-contract should see the handoff via task_id link
        from eduflow.store import task_loop_contract
        contract = task_loop_contract.build(tid)
        assert contract is not None
        delivery = contract["delivery"]
        assert delivery["inbox_local_id"] != "", (
            "send --task-id should populate delivery.inbox_local_id via task_id link"
        )
        assert delivery["ack_required"] is True