"""Tests for store/evolution_packet.py and `task evolution-packet` CLI surface.

Package 4: read-only Evolution Packet candidate generator. NEVER writes
memory / flow-memory / skills. Only returns structured candidates when
the task has a recognized trigger.
"""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.store import evolution_packet, local_facts, loop_runs, tasks


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


def test_repair_cycle_ge2_reads_loop_meta():
    """V3 P2: repair_cycle_ge2 candidate reads loop run meta for richer
    evidence without writing memory.
    """
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 repair-cycle-meta",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        run = loop_runs.create_new(
            task_id=tid, spec="code-repair", max_cycles=5,
        )
        loop_runs.append_cycle(
            run["id"],
            checker_output="x",
            diff_text="x",
            preflight={},
            failed_commands=["pytest tests/unit"],
            passed_commands=[],
            failure_fingerprint="same_failure_repeated",
            status="repair_needed",
            stop_reason="same_failure_repeated",
        )
        loop_runs.append_cycle(
            run["id"],
            checker_output="x",
            diff_text="x",
            preflight={},
            failed_commands=["pytest tests/unit", "pytest tests/integration"],
            passed_commands=[],
            failure_fingerprint="same_failure_repeated",
            status="repair_needed",
            stop_reason="same_failure_repeated",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id=run["id"],
            loop_status="repair_needed",
            loop_cycle_count=2,
            loop_stop_reason="same_failure_repeated",
            loop_recommended_action="update loop spec",
            loop_evidence_ref=loop_runs.evidence_ref(run["id"]),
            actor="manager",
        )
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_event"] == "repair_cycle_ge2"
        assert c["loop_id"] == run["id"]
        assert c["cycle_count"] == 2
        assert c["loop_status"] == "repair_needed"
        assert c["stop_reason"] == "same_failure_repeated"
        assert c["latest_failure_fingerprint"] == "same_failure_repeated"
        assert "pytest tests/unit" in c["recent_failed_commands"]
        assert c["suggested_update_surface"] == "loop_spec"
        assert "loop_spec" in c["reuse_reason"]
        assert c["confidence"] == "medium"
        assert f"loop:{run['id']}" in c["evidence_refs"]


def test_repair_cycle_ge2_missing_loop_meta_low_confidence():
    """Without loop meta the packet stays thin and confidence drops to low."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 repair-cycle-thin",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000099",
            loop_status="repair_needed",
            loop_cycle_count=2,
            loop_stop_reason="one_off_local_failure",
            actor="manager",
        )
        result = evolution_packet.build(tid)
        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["source_event"] == "repair_cycle_ge2"
        assert c["confidence"] == "low"
        assert c["suggested_update_surface"] == "no_reuse"
        assert c["recent_failed_commands"] == []
        assert c["latest_failure_fingerprint"] == ""


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


def _setup_loop_repair_task():
    """Helper: create a flow task with a 2-cycle code-repair loop run."""
    tid = tasks.create_flow(
        "worker_course",
        "IGCSE Accounting 0452 propose",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    run = loop_runs.create_new(task_id=tid, spec="code-repair", max_cycles=5)
    loop_runs.append_cycle(
        run["id"],
        checker_output="x", diff_text="x", preflight={},
        failed_commands=["pytest tests/unit"],
        passed_commands=[],
        failure_fingerprint="same_failure_repeated",
        status="repair_needed", stop_reason="same_failure_repeated",
    )
    loop_runs.append_cycle(
        run["id"],
        checker_output="x", diff_text="x", preflight={},
        failed_commands=["pytest tests/unit"],
        passed_commands=[],
        failure_fingerprint="same_failure_repeated",
        status="repair_needed", stop_reason="same_failure_repeated",
    )
    tasks.set_loop_evidence(
        tid,
        loop_run_id=run["id"],
        loop_status="repair_needed",
        loop_cycle_count=2,
        loop_stop_reason="same_failure_repeated",
        loop_evidence_ref=loop_runs.evidence_ref(run["id"]),
        actor="manager",
    )
    return tid, run["id"]


def test_cli_evolution_propose_creates_loop_repair_candidate():
    with isolated_env():
        from eduflow.memory import db
        from eduflow.memory.candidates import list_candidates
        tid, loop_id = _setup_loop_repair_task()
        before = tasks.get(tid)
        db.init_schema()

        rc, out, err = run_cli(["task", "evolution-propose", tid, "--yes"])
        assert rc == 0, err
        assert "Proposed candidate" in out or "Proposed candidate" in err

        after = tasks.get(tid)
        for key in ("status", "stage", "loop_status", "loop_cycle_count"):
            assert before.get(key) == after.get(key), f"task.{key} mutated"

        cands = list_candidates(source_type="loop_repair_cycle")
        assert len(cands) == 1
        c = cands[0]
        assert c["source_ref"] == f"loop:{loop_id}"
        assert c["review_status"] == "proposed"
        assert c["proposed_kind"] == "workflow_rule"


def test_cli_evolution_propose_is_idempotent():
    with isolated_env():
        from eduflow.memory import db
        from eduflow.memory.candidates import list_candidates
        tid, loop_id = _setup_loop_repair_task()
        db.init_schema()

        run_cli(["task", "evolution-propose", tid, "--yes"])
        run_cli(["task", "evolution-propose", tid, "--yes"])

        cands = list_candidates(source_type="loop_repair_cycle")
        assert len(cands) == 1
        assert cands[0]["source_ref"] == f"loop:{loop_id}"


def test_cli_evolution_propose_skips_low_confidence():
    with isolated_env():
        from eduflow.memory import db
        from eduflow.memory.candidates import list_candidates
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 propose-thin",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000099",
            loop_status="repair_needed",
            loop_cycle_count=2,
            loop_stop_reason="one_off_local_failure",
            actor="manager",
        )
        db.init_schema()

        rc, out, err = run_cli(["task", "evolution-propose", tid, "--yes"])
        assert rc == 0, err
        assert "lacks enough evidence" in out

        cands = list_candidates(source_type="loop_repair_cycle")
        assert len(cands) == 0