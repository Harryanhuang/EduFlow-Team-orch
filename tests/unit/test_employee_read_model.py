"""Tests for the employee read model."""
from __future__ import annotations

from helpers import attr_patch, isolated_env
from eduflow.store import employee_read_model, local_facts, tasks
from eduflow.runtime import tunables


def _patch_now(module, when_ms: int):
    """Patch ``module.now_ms`` to return a fixed value."""
    return attr_patch(module, now_ms=lambda: when_ms)


# ── display verdict classification ─────────────────────────────────


def test_heartbeat_fresh_but_status_stale_is_stale_display():
    with isolated_env():
        base = 1_000_000
        stale_now = base + employee_read_model.STATUS_STALE_MS + 60_000

        # Status was written long ago.
        with _patch_now(local_facts, base):
            local_facts.upsert_status("worker_course", "进行中", "old task")

        # Heartbeat is fresh relative to the read-model "now".
        with _patch_now(local_facts, stale_now - 60_000):
            local_facts.touch_heartbeat("worker_course")

        with _patch_now(employee_read_model, stale_now):
            snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["display_verdict"] == "stale_display"
        assert "status stale" in snap["staleness_reason"]


def test_high_priority_unread_is_waiting_inbox():
    with isolated_env():
        local_facts.upsert_status("worker_course", "待命", "ready")
        local_facts.append_message(
            "worker_course", "manager", "urgent request", priority="高"
        )

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["display_verdict"] == "waiting_inbox"
        assert snap["unread_high_priority_count"] == 1
        assert "Consume" in snap["recommended_next_action"]


def test_explicit_stopped_status_is_stopped():
    with isolated_env():
        local_facts.upsert_status("worker_course", "已停止", "agent stopped")
        local_facts.touch_heartbeat("worker_course")

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["display_verdict"] == "stopped"
        assert "restart" in snap["recommended_next_action"]


def test_blocker_present_is_blocked():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course", "进行中", "task", blocker="API key missing"
        )
        local_facts.touch_heartbeat("worker_course")

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["display_verdict"] == "blocked"
        assert snap["blocker"] == "API key missing"
        assert "API key missing" in snap["recommended_next_action"]


def test_ready_with_no_unread_is_idle():
    with isolated_env():
        local_facts.upsert_status("worker_course", "待命", "ready")
        local_facts.touch_heartbeat("worker_course")

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["display_verdict"] == "idle"
        assert snap["unread_high_priority_count"] == 0
        assert "Awaiting" in snap["recommended_next_action"]


# ── task / workflow wiring ─────────────────────────────────────────


def test_flow_task_surfaces_workflow_gate_and_next_action():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
            status="in_progress",
        )

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["current_task_id"] == tid
        assert snap["current_task_title"] == "IGCSE Physics 0625"
        assert snap["current_task_status"] == "in_progress"
        assert snap["workflow_id"] == "igcse-subject-launch"
        assert snap["workflow_gate"] != ""
        assert snap["workflow_gate_status"] != ""
        assert snap["workflow_next_action"] != ""


# ── residency integration ──────────────────────────────────────────


def test_warm_residency_agent_does_not_become_stopped():
    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlow"

[team.residency]
default_mode = "warm"
resident_agents = ["manager"]
warm_idle_timeout_s = 600
handoff_buffer_s = 300
wake_timeout_s = 60

[team.agents.manager]
cli = "claude-code"
role = "manager"

[team.agents.worker_course]
cli = "claude-code"
role = "course"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        tunables.reset_cache()

        local_facts.upsert_status("worker_course", "待命", "ready")
        local_facts.touch_heartbeat("worker_course")

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["residency_label"] == "温备"
        assert snap["policy_mode"] == "warm"
        assert snap["display_verdict"] != "stopped"
        assert snap["display_verdict"] == "idle"


def test_resident_agent_has_resident_policy():
    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlow"

[team.residency]
default_mode = "warm"
resident_agents = ["manager"]
warm_idle_timeout_s = 600
handoff_buffer_s = 300
wake_timeout_s = 60

[team.agents.manager]
cli = "claude-code"
role = "manager"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        tunables.reset_cache()

        local_facts.upsert_status("manager", "进行中", "dispatching")
        local_facts.touch_heartbeat("manager")

        snap = employee_read_model.build_employee_snapshot("manager")

        assert snap["residency_label"] == "常驻"
        assert snap["policy_mode"] == "resident"
        assert snap["sleep_decision"] == "keep_resident"


# ── team snapshot ──────────────────────────────────────────────────


def test_team_snapshot_includes_all_agents_with_status_or_heartbeat():
    with isolated_env():
        local_facts.upsert_status("alice", "待命", "ready")
        local_facts.touch_heartbeat("bob")

        rows = employee_read_model.build_team_snapshot()
        agents = {r["agent"] for r in rows}

        assert agents == {"alice", "bob"}


# ── wake failure evidence ──────────────────────────────────────────


def test_wake_failure_evidence_surfaces_in_snapshot():
    with isolated_env() as tmp:
        (tmp / "runtime_config.json").write_text(
            '{"chat_id": "oc_test", "lark_profile": ""}',
            encoding="utf-8",
        )
        from eduflow.commands import wake_alert
        wake_alert.fire_wake_failure_alert(
            target_agent="worker_course",
            failure_kind="ready_marker_timeout",
            wake_timeout_s=60.0,
            chat_id="oc_test",
            send_card=lambda *a, **kw: {"message_id": "om_test"},
        )

        snap = employee_read_model.build_employee_snapshot("worker_course")

        assert snap["wake_status"] == "wake_failed"
