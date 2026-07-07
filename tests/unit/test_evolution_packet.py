"""Tests for store/evolution_packet.py and `task evolution-packet` CLI surface.

Package 4: read-only Evolution Packet candidate generator. NEVER writes
memory / flow-memory / skills. Only returns structured candidates when
the task has a recognized trigger.
"""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.store import evolution_packet, local_facts, tasks


# ── store: build ──────────────────────────────────────────────────


def test_build_returns_empty_when_no_trigger_present():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 clean",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        result = evolution_packet.build(tid)
        assert result == {"candidates": []}


def test_build_returns_empty_for_unknown_task():
    with isolated_env():
        assert evolution_packet.build("T-does-not-exist") == {"candidates": []}


def test_review_rejected_triggers_candidate():
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
            review_reason="quality_not_met",
            required_fix=["expand per-topic items to 9"],
            blocking_files=["items/T1.1.md"],
        )
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_task_id"] == tid
        assert c["source_event"] == "review_rejected"
        assert "review rejected" in c["trigger_reason"].lower()
        assert c["scope"] == "workflow:igcse-subject-launch"
        assert c["kind"] == "workflow_rule"
        assert f"task:{tid}" in c["evidence_refs"]
        # content should reference the required_fix item
        assert "expand per-topic items to 9" in c["content"]


def test_manager_action_triggers_candidate():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 manager-action",
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
            outcome="manager_action",
            actor="review_course",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_event"] == "manager_action"
        assert c["kind"] == "agent_skill"
        assert "clarify_scope" in c["content"] or "missing_scope_confirmation" in c["content"]


def test_repair_cycle_ge2_triggers_candidate():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 repair-cycle",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000010",
            loop_status="repair_needed",
            loop_cycle_count=2,
            loop_stop_reason="missing_blocking_files",
            loop_recommended_action="rerun q1-q3",
            actor="manager",
        )
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_event"] == "repair_cycle_ge2"
        assert "loop" in c["content"].lower() or "repair" in c["content"].lower()
        assert c["kind"] == "workflow_rule"


def test_repair_cycle_lt2_does_not_trigger():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 repair-cycle-lt2",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000011",
            loop_status="repair_needed",
            loop_cycle_count=1,
            actor="manager",
        )
        result = evolution_packet.build(tid)
        assert result == {"candidates": []}


def test_runtime_incident_failed_triggers_candidate():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 failed",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.report_flow_failure(tid, actor="worker_course", reason="qoder_credits_exhausted")
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_event"] == "runtime_incident"
        assert c["kind"] == "workflow_rule"


def test_review_approved_does_not_trigger():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 approved",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
        )
        result = evolution_packet.build(tid)
        assert result == {"candidates": []}


def test_multiple_triggers_pick_highest_severity_only():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 multi",
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
            review_reason="quality_not_met",
            required_fix=["fix q1"],
            blocking_files=["items/q1.md"],
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000020",
            loop_status="repair_needed",
            loop_cycle_count=3,
            loop_stop_reason="review_rejected",
            actor="manager",
        )
        result = evolution_packet.build(tid)
        # Should pick review_rejected (highest) over repair_cycle_ge2
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["source_event"] == "review_rejected"


def test_candidate_includes_evidence_refs():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 evidence-refs",
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
            review_reason="quality_not_met",
            required_fix=["fix q1"],
            blocking_files=["items/q1.md"],
            verdict_target="items only",
        )
        result = evolution_packet.build(tid)
        c = result["candidates"][0]
        assert f"task:{tid}" in c["evidence_refs"]
        assert any("items only" in r for r in c["evidence_refs"])


def test_confidence_is_determined_by_required_fix_and_blocking_files():
    with isolated_env():
        # high: both required_fix AND blocking_files
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 high",
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
        result = evolution_packet.build(tid)
        assert result["candidates"][0]["confidence"] == "high"
        assert result["candidates"][0]["recommended_action"] == "remember"


def test_no_trigger_for_legacy_non_flow_task():
    """Legacy non-flow tasks have no schema_version=2 fields; no trigger fires."""
    with isolated_env():
        tid = tasks.create("worker", "plain legacy task")
        result = evolution_packet.build(tid)
        assert result == {"candidates": []}


def test_candidate_scope_falls_back_to_agent_when_workflow_missing():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "no-workflow-id",
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
        result = evolution_packet.build(tid)
        c = result["candidates"][0]
        assert c["scope"].startswith("agent:") or c["scope"].startswith("workflow:")


# ── CLI: task evolution-packet ────────────────────────────────────


def test_cli_evolution_packet_json_mode_returns_empty_when_no_trigger():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 cli-clean",
            stage="curriculum",
            owner="worker_course",
        )
        rc, out, err = run_cli(["task", "evolution-packet", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert payload == {"candidates": []}


def test_cli_evolution_packet_json_mode_returns_candidate_on_reject():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 cli-reject",
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
            review_reason="quality_not_met",
            required_fix=["fix q1"],
            blocking_files=["items/q1.md"],
        )
        rc, out, err = run_cli(["task", "evolution-packet", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert len(payload["candidates"]) == 1
        c = payload["candidates"][0]
        assert c["source_event"] == "review_rejected"


def test_cli_evolution_packet_unknown_task_returns_empty_payload():
    with isolated_env():
        rc, out, err = run_cli(["task", "evolution-packet", "T-does-not-exist", "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert payload == {"candidates": []}


def test_cli_evolution_packet_does_not_mutate_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-mutate",
            stage="curriculum",
            owner="worker_course",
        )
        before = tasks.get(tid)
        before_msgs = local_facts.list_all_messages()
        run_cli(["task", "evolution-packet", tid, "--json"])
        run_cli(["task", "evolution-packet", tid])
        after = tasks.get(tid)
        after_msgs = local_facts.list_all_messages()
        for key in (
            "status", "stage", "verdict", "owner",
            "review_reason", "required_fix", "blocking_files",
            "loop_status", "loop_cycle_count",
        ):
            assert before.get(key) == after.get(key), (
                f"task.{key} mutated"
            )
        assert len(before_msgs) == len(after_msgs)