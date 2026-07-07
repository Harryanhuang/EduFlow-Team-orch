"""Tests for store/operational_readiness.diagnostics() and the
`task readiness-check --diagnostics` CLI flag.

The diagnostics surface returns raw signal values behind the readiness
verdict so we can tune HEARTBEAT_FRESH_MS / PROGRESS_FRESH_MS /
DELIVERY_FRESH_MS after collecting real-world samples.
"""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.store import local_facts, operational_readiness, tasks


# ── store: diagnostics ───────────────────────────────────────────


def test_diagnostics_returns_none_for_unknown_task():
    with isolated_env():
        assert operational_readiness.diagnostics("T-does-not-exist") is None


def test_diagnostics_returns_thresholds_and_signals():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 diag",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.diagnostics(tid)
        assert result is not None
        for key in (
            "task_id", "thresholds",
            "delivery_signals", "productivity_signals", "source_signals",
        ):
            assert key in result, f"missing key: {key}"
        assert result["task_id"] == tid
        thresholds = result["thresholds"]
        assert thresholds["HEARTBEAT_FRESH_MS"] == 5 * 60 * 1000
        assert thresholds["PROGRESS_FRESH_MS"] == 30 * 60 * 1000
        assert thresholds["DELIVERY_FRESH_MS"] == 5 * 60 * 1000


def test_diagnostics_productivity_signals_without_heartbeat():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "no heartbeat",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.diagnostics(tid)
        ps = result["productivity_signals"]
        assert ps["heartbeat_present"] is False
        assert ps["heartbeat_age_ms"] is None
        assert ps["recent_log_count"] == 0


def test_diagnostics_productivity_signals_with_heartbeat_and_log():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "healthy worker",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.touch_heartbeat("worker_course")
        local_facts.append_log(agent="worker_course", kind="say", content="hi")
        result = operational_readiness.diagnostics(tid)
        ps = result["productivity_signals"]
        assert ps["heartbeat_present"] is True
        assert isinstance(ps["heartbeat_age_ms"], int)
        assert ps["heartbeat_age_ms"] >= 0
        assert ps["recent_log_count"] >= 1
        assert isinstance(ps["most_recent_log_age_ms"], int)


def test_diagnostics_delivery_signals_with_handoff():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "with handoff",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please fix q1",
            priority="高",
            task_id=tid,
        )
        result = operational_readiness.diagnostics(tid)
        ds = result["delivery_signals"]
        assert ds["handoff_count"] == 1
        assert ds["latest_handoff_priority"] == "高"
        assert ds["latest_handoff_ack_state"] == "pending"
        assert ds["latest_handoff_delivery_state"] == "delivered_to_inbox"


def test_diagnostics_source_signals_for_curriculum_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "no evidence curriculum",
            stage="curriculum",
            owner="worker_course",
        )
        result = operational_readiness.diagnostics(tid)
        ss = result["source_signals"]
        assert ss["stage"] == "curriculum"
        assert ss["has_evidence_packet"] is False
        assert ss["has_authoritative_verdict"] is False


def test_diagnostics_does_not_mutate_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "no-mutate",
            stage="curriculum",
            owner="worker_course",
        )
        before = tasks.get(tid)
        operational_readiness.diagnostics(tid)
        operational_readiness.diagnostics(tid)
        after = tasks.get(tid)
        for key in (
            "status", "stage", "verdict", "owner",
            "required_fix", "blocking_files",
            "loop_status", "loop_cycle_count",
        ):
            assert before.get(key) == after.get(key)


# ── CLI: readiness-check --diagnostics ───────────────────────────


def test_cli_readiness_check_diagnostics_json_includes_signals():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "cli diag",
            stage="curriculum",
            owner="worker_course",
        )
        local_facts.touch_heartbeat("worker_course")
        rc, out, err = run_cli([
            "task", "readiness-check", tid, "--json", "--diagnostics",
        ])
        assert rc == 0, err
        payload = json.loads(out)
        assert "readiness" in payload
        assert "readiness_diagnostics" in payload
        signals = payload["readiness_diagnostics"]
        assert signals["task_id"] == tid
        assert "thresholds" in signals
        assert "delivery_signals" in signals
        assert "productivity_signals" in signals
        assert "source_signals" in signals


def test_cli_readiness_check_without_diagnostics_omits_signals():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "cli no diag",
            stage="curriculum",
            owner="worker_course",
        )
        rc, out, err = run_cli(["task", "readiness-check", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        assert "readiness" in payload
        assert "readiness_diagnostics" not in payload


def test_cli_readiness_check_diagnostics_text_mode():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "cli diag text",
            stage="curriculum",
            owner="worker_course",
        )
        rc, out, err = run_cli([
            "task", "readiness-check", tid, "--diagnostics",
        ])
        assert rc == 0, err
        for needle in ("diagnostics:", "thresholds:", "delivery_signals:", "productivity_signals:", "source_signals:"):
            assert needle in out, f"missing diagnostics field: {needle}"