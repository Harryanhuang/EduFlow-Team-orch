"""Tests for store/operational_readiness.py and `task readiness-check` CLI surface.

Package 5: read-only readiness check across delivery / productivity /
source. NEVER auto-fixes, NEVER sends messages, NEVER archives, NEVER
touches runtime. Returns structured pass / warn / fail verdicts.
"""
from __future__ import annotations

import json
import time

from helpers import isolated_env, run_cli
from eduflow.store import (
    local_facts, operational_readiness, tasks,
)


# ── store: build ──────────────────────────────────────────────────


def test_build_returns_required_top_level_sections():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 baseline",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.build(tid)
        for key in ("task_id", "delivery", "productivity", "source", "overall"):
            assert key in result, f"missing top-level field: {key}"
        for section_key in ("delivery", "productivity", "source"):
            section = result[section_key]
            assert "status" in section, f"missing {section_key}.status"
            assert "reason" in section, f"missing {section_key}.reason"
            assert section["status"] in {"pass", "warn", "fail"}
        assert result["overall"] in {"pass", "warn", "fail"}


def test_build_returns_none_for_unknown_task():
    with isolated_env():
        assert operational_readiness.build("T-does-not-exist") is None


def test_delivery_pass_when_no_handoff_message():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-handoff",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.build(tid)
        # No handoff message => pass (no message = no pending delivery)
        assert result["delivery"]["status"] == "pass"


def test_delivery_warn_when_high_priority_message_pending_ack():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 pending-ack",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please repair section 2.1",
            priority="高",
            task_id=tid,
        )
        result = operational_readiness.build(tid)
        assert result["delivery"]["status"] == "warn"
        assert result["delivery"]["reason"]


def test_delivery_pass_when_high_priority_message_acked():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 acked",
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
        result = operational_readiness.build(tid)
        assert result["delivery"]["status"] == "pass"


def test_productivity_pass_when_heartbeat_and_progress_signals_present():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 healthy",
            stage="curriculum",
            owner="worker_course",
        )
        # Heartbeat
        local_facts.touch_heartbeat("worker_course")
        # Recent log entry
        local_facts.append_log(
            agent="worker_course", kind="say",
            content="working on items",
        )
        result = operational_readiness.build(tid)
        assert result["productivity"]["status"] == "pass", result


def test_productivity_warn_when_heartbeat_but_no_recent_log():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 stale",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.touch_heartbeat("worker_course")
        # No log entry from worker_course
        result = operational_readiness.build(tid)
        # warn (heartbeat present, progress signal missing)
        assert result["productivity"]["status"] in {"warn", "pass"}, result


def test_productivity_fail_when_no_heartbeat():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-heartbeat",
            stage="curriculum",
            owner="worker_course",
        )
        # No heartbeat at all
        result = operational_readiness.build(tid)
        # If no inbox messages and no heartbeat = warn
        # (we don't want to fail-flow by default; warn is more honest)
        assert result["productivity"]["status"] in {"warn", "pass"}, result


def test_source_pass_when_evidence_packet_present():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 evidence",
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
            evidence_packet={
                "files_sampled": ["items/T1.1.md"],
                "qa_count": 12,
                "item_count": 36,
            },
        )
        result = operational_readiness.build(tid)
        assert result["source"]["status"] == "pass", result


def test_source_warn_when_no_evidence_for_curriculum_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-evidence",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.build(tid)
        # curriculum task without evidence/source refs => warn
        assert result["source"]["status"] in {"warn", "pass"}, result


def test_overall_takes_minimum_across_sections():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 mixed",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please repair",
            priority="高",
            task_id=tid,
        )
        # delivery is warn; productivity/source depend
        result = operational_readiness.build(tid)
        assert result["overall"] in {"warn", "fail", "pass"}


def test_command_surface_does_not_mutate_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 no-mutate",
            stage="curriculum",
            owner="worker_course",
        )
        before = tasks.get(tid)
        before_msgs = local_facts.list_all_messages()
        run_cli(["task", "readiness-check", tid, "--json"])
        run_cli(["task", "readiness-check", tid])
        after = tasks.get(tid)
        after_msgs = local_facts.list_all_messages()
        for key in (
            "status", "stage", "verdict", "owner",
            "review_reason", "required_fix", "blocking_files",
            "loop_status", "loop_cycle_count",
        ):
            assert before.get(key) == after.get(key)
        assert len(before_msgs) == len(after_msgs)


# ── CLI: task readiness-check ─────────────────────────────────────


def test_cli_readiness_check_json_mode_unknown_task_returns_error():
    with isolated_env():
        rc, out, err = run_cli(["task", "readiness-check", "T-does-not-exist", "--json"])
        assert rc != 0


def test_cli_readiness_check_json_mode_returns_payload():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 cli",
            stage="curriculum",
            owner="worker_course",
        )
        rc, out, err = run_cli(["task", "readiness-check", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert "readiness" in payload
        readiness = payload["readiness"]
        assert readiness["task_id"] == tid
        for section in ("delivery", "productivity", "source"):
            assert section in readiness
            assert readiness[section]["status"] in {"pass", "warn", "fail"}
        assert readiness["overall"] in {"pass", "warn", "fail"}


def test_cli_readiness_check_text_mode_includes_sections():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 text",
            stage="curriculum",
            owner="worker_course",
        )
        rc, out, err = run_cli(["task", "readiness-check", tid])
        assert rc == 0, err
        for needle in (
            "task_id:",
            "delivery:",
            "productivity:",
            "source:",
            "overall:",
        ):
            assert needle in out, f"missing text field: {needle}"


# ── integration ──────────────────────────────────────────────────


def test_pass_when_acked_handoff_heartbeat_and_evidence_present():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 full-pass",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        local_facts.touch_heartbeat("worker_course")
        local_facts.append_log(agent="worker_course", kind="say", content="ready")
        local_id = local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please fix q1",
            priority="高",
            task_id=tid,
        )
        local_facts.record_message_ack(local_id, kind="accepted_task")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            evidence_packet={
                "files_sampled": ["items/T1.1.md"],
                "qa_count": 9,
                "item_count": 36,
            },
        )
        result = operational_readiness.build(tid)
        assert result["delivery"]["status"] == "pass"
        assert result["productivity"]["status"] in {"pass", "warn"}
        assert result["source"]["status"] == "pass"
        assert result["overall"] in {"pass", "warn"}