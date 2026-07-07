"""Tests for store/task_loop_contract.py and `task loop-contract` CLI surface.

Package 2: read-only Loop Contract render. Never mutates task state.
"""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.store import local_facts, task_loop_contract, tasks


# ── store: build_loop_contract ────────────────────────────────────


def test_build_loop_contract_returns_required_fields_with_defaults():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
        )
        contract = task_loop_contract.build(tid)
        for key in (
            "task_id", "workflow_id", "current_phase", "owner", "iteration",
            "delivery", "passed_checks", "failed_checks",
            "allowed_actions", "forbidden_actions",
            "next_required_output", "evidence_refs",
        ):
            assert key in contract, f"missing top-level field: {key}"
        assert contract["task_id"] == tid
        assert contract["iteration"] == 0
        assert contract["passed_checks"] == []
        assert contract["failed_checks"] == []
        assert contract["allowed_actions"] == []
        assert contract["forbidden_actions"] == []
        assert contract["evidence_refs"] == [f"task:{tid}"]
        for key in ("state", "inbox_local_id", "ack_required", "ack_state", "ack_deadline"):
            assert key in contract["delivery"], f"missing delivery.{key}"


def test_build_loop_contract_with_required_fix_populates_failed_checks():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 reject",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="missing_scope_confirmation",
            required_fix=["expand per-topic items to 9"],
            blocking_files=["items/T1.1.md"],
        )
        contract = task_loop_contract.build(tid)
        assert any("missing_scope_confirmation" in s for s in contract["failed_checks"])
        assert any("expand per-topic items to 9" in s for s in contract["failed_checks"])
        assert any("items/T1.1.md" in s for s in contract["failed_checks"])
        assert contract["workflow_id"] == "igcse-subject-launch"
        assert contract["current_phase"].startswith("curriculum")


def test_build_loop_contract_iteration_reads_loop_cycle_count():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 cycle",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000007",
            loop_status="repair_needed",
            loop_cycle_count=3,
            loop_stop_reason="review_rejected",
            loop_recommended_action="focus on q1-q3",
            loop_evidence_ref="loop_runs/L-000007/meta.json",
            actor="manager",
        )
        contract = task_loop_contract.build(tid)
        assert contract["iteration"] == 3
        assert "focus on q1-q3" in contract["allowed_actions"]
        assert any("review_rejected" in s for s in contract["failed_checks"])
        assert any("loop_runs/L-000007/meta.json" in s for s in contract["evidence_refs"])


def test_build_loop_contract_surfaces_delivery_ack_when_handoff_message_exists():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 handoff",
            stage="curriculum",
            owner="worker_course",
        )
        local_id = local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please repair section 2.1",
            priority="高",
            task_id=tid,
        )
        local_facts.record_message_ack(local_id, kind="accepted_task")
        contract = task_loop_contract.build(tid)
        delivery = contract["delivery"]
        assert delivery["inbox_local_id"] == local_id
        assert delivery["ack_required"] is True
        assert delivery["ack_state"] == "agent_acknowledged"
        # delivery_state should still be the default delivered_to_inbox
        assert delivery["state"] == "delivered_to_inbox"


def test_build_loop_contract_delivery_empty_when_no_handoff_message():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-handoff",
            stage="curriculum",
            owner="worker_course",
        )
        contract = task_loop_contract.build(tid)
        delivery = contract["delivery"]
        assert delivery["state"] == ""
        assert delivery["inbox_local_id"] == ""
        assert delivery["ack_required"] is False
        assert delivery["ack_state"] == ""


def test_build_loop_contract_picks_latest_handoff_when_multiple_messages():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 multi-handoff",
            stage="curriculum",
            owner="worker_course",
        )
        first = local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="first instruction",
            priority="高",
            task_id=tid,
        )
        latest = local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="second instruction",
            priority="高",
            task_id=tid,
        )
        contract = task_loop_contract.build(tid)
        assert contract["delivery"]["inbox_local_id"] == latest
        assert contract["delivery"]["inbox_local_id"] != first


def test_build_loop_contract_missing_task_returns_none():
    with isolated_env():
        assert task_loop_contract.build("T-does-not-exist") is None


# ── CLI: task loop-contract ────────────────────────────────────────


def test_cli_task_loop_contract_json_mode():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 cli",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            required_fix=["add syllabus section 2.1"],
        )
        rc, out, err = run_cli(["task", "loop-contract", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert "loop_contract" in payload
        contract = payload["loop_contract"]
        assert contract["task_id"] == tid
        assert contract["workflow_id"] == "igcse-subject-launch"
        assert any("add syllabus section 2.1" in s for s in contract["failed_checks"])


def test_cli_task_loop_contract_text_mode_includes_required_fields():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 text",
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
            required_fix=["fix q1 citation"],
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000099",
            loop_status="repair_needed",
            loop_cycle_count=1,
            loop_recommended_action="rerun q1-q3",
            actor="manager",
        )
        rc, out, err = run_cli(["task", "loop-contract", tid])
        assert rc == 0, err
        for needle in (
            "task_id:",
            "current_phase:",
            "iteration:",
            "failed_checks:",
            "next_required_output:",
            "allowed_actions:",
        ):
            assert needle in out, f"missing text field: {needle}"


def test_cli_task_loop_contract_unknown_task_returns_error():
    with isolated_env():
        rc, out, err = run_cli(["task", "loop-contract", "T-does-not-exist", "--json"])
        assert rc != 0
        assert "no such task" in err.lower() or "no such task" in out.lower()


def test_cli_task_loop_contract_does_not_mutate_task_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-mutate",
            stage="curriculum",
            owner="worker_course",
        )
        before = tasks.get(tid)
        run_cli(["task", "loop-contract", tid, "--json"])
        run_cli(["task", "loop-contract", tid])
        after = tasks.get(tid)
        # No field may have changed between calls
        for key in (
            "status", "stage", "verdict", "owner", "assignee",
            "review_reason", "required_fix", "blocking_files",
            "loop_status", "loop_cycle_count", "loop_stop_reason",
            "loop_recommended_action", "loop_evidence_ref",
        ):
            assert before.get(key) == after.get(key), (
                f"task.{key} mutated: {before.get(key)!r} -> {after.get(key)!r}"
            )