"""P4: scheduler manager/user/worker operations and authorization.

Tests the deterministic operation layer that sits between the scheduler
store and the manager skill / CLI.  All writes are explicit; natural
language cannot mutate store directly.  D lanes never produce user-visible
T tasks.
"""
from __future__ import annotations

import json

import pytest

from helpers import isolated_env, run_cli
from eduflow.runtime import paths
from eduflow.scheduling import engine, manager_ops
from eduflow.store import scheduled_tasks


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


# ── draft rule lifecycle (user) ──────────────────────────────────────


def test_create_draft_rule_persists_as_draft():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
            created_by="user",
        )
        rule = scheduled_tasks.get_rule(rid)
        assert rule["status"] == "draft"
        assert rule["created_by"] == "user"
        assert rule["version"] == 1


def test_user_can_confirm_own_draft():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        rule = manager_ops.confirm_draft_rule(rid, actor="alice", actor_role="user")
        assert rule["status"] == "active"
        assert rule["confirmed_by"] == "alice"
        assert rule["version"] == 2
        assert rule["confirmed_at"] is not None


def test_user_cannot_confirm_others_draft():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.confirm_draft_rule(rid, actor="bob", actor_role="user")


def test_manager_can_confirm_any_draft():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        rule = manager_ops.confirm_draft_rule(rid, actor="manager", actor_role="manager")
        assert rule["status"] == "active"
        assert rule["confirmed_by"] == "manager"


def test_worker_cannot_confirm_draft():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="user",
        )
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.confirm_draft_rule(rid, actor="worker_course", actor_role="worker")


# ── rule lifecycle authorization ───────────────────────────────────────


def test_user_can_pause_resume_cancel_own_rule():
    with isolated_env():
        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        manager_ops.confirm_draft_rule(rid, actor="alice", actor_role="user")

        manager_ops.pause_rule(rid, actor="alice", actor_role="user", expected_version=2)
        assert scheduled_tasks.get_rule(rid)["status"] == "paused"

        manager_ops.resume_rule(rid, actor="alice", actor_role="user", expected_version=3)
        assert scheduled_tasks.get_rule(rid)["status"] == "active"

        manager_ops.cancel_rule(rid, actor="alice", actor_role="user", expected_version=4)
        assert scheduled_tasks.get_rule(rid)["status"] == "cancelled"


def test_user_cannot_pause_others_rule():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.pause_rule(rid, actor="bob", actor_role="user", expected_version=1)


def test_manager_can_pause_any_rule():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        manager_ops.pause_rule(rid, actor="manager", actor_role="manager", expected_version=1)
        assert scheduled_tasks.get_rule(rid)["status"] == "paused"


def test_worker_cannot_pause_rule():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.pause_rule(rid, actor="worker_course", actor_role="worker", expected_version=1)


# ── occurrence confirmation (manager) ──────────────────────────────────


def test_manager_confirm_occurrence_binds_rule_version_and_key():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        occ = manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        rule = scheduled_tasks.get_rule(rid)
        assert occ["status"] == "confirmed"
        assert occ["confirmed_by"] == "manager"
        assert occ["confirmed_rule_version"] == rule["version"]
        assert occ["confirmed_at"] is not None


def test_worker_cannot_confirm_occurrence():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.confirm_occurrence(key, actor="worker_course", actor_role="worker")


# ── lane management ────────────────────────────────────────────────────


def test_manager_choose_lane_records_agent_dependencies_inputs_artifacts_evidence():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        lane = manager_ops.choose_lane(
            key,
            agent="worker_course",
            dependencies=[],
            inputs={"subject": "Physics"},
            artifacts=["report.md"],
            evidence={"source": "manual"},
            actor="manager",
            actor_role="manager",
        )
        assert lane["occurrence_key"] == key
        assert lane["agent"] == "worker_course"
        assert lane["dependencies"] == []
        assert lane["inputs"] == {"subject": "Physics"}
        assert lane["artifacts"] == ["report.md"]
        assert lane["evidence"] == {"source": "manual"}
        assert lane["status"] == "pending"


def test_choose_lanes_serial_adds_dependencies():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        lanes = manager_ops.choose_lanes(
            key,
            lanes=[
                {"agent": "worker_course"},
                {"agent": "review_course"},
                {"agent": "manager"},
            ],
            mode="serial",
            actor="manager",
            actor_role="manager",
        )
        assert len(lanes) == 3
        assert lanes[0]["dependencies"] == []
        assert lanes[1]["dependencies"] == [lanes[0]["id"]]
        assert lanes[2]["dependencies"] == [lanes[1]["id"]]


def test_choose_lanes_parallel_has_no_dependencies():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        lanes = manager_ops.choose_lanes(
            key,
            lanes=[
                {"agent": "worker_a"},
                {"agent": "worker_b"},
            ],
            mode="parallel",
            actor="manager",
            actor_role="manager",
        )
        assert len(lanes) == 2
        assert lanes[0]["dependencies"] == []
        assert lanes[1]["dependencies"] == []


# ── skip / re-dispatch / fail-pause ────────────────────────────────────


def test_manager_skip_occurrence():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        occ = manager_ops.skip_occurrence(key, actor="manager", actor_role="manager", reason="holiday")
        assert occ["status"] == "skipped"
        assert occ["skipped_reason"] == "holiday"


def test_re_dispatch_transitions_to_running_when_rule_active():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        manager_ops.choose_lane(key, agent="worker_course", actor="manager", actor_role="manager")
        result = manager_ops.re_dispatch(key, actor="manager", actor_role="manager")
        assert result["dispatched"] is True
        occ = scheduled_tasks.get_occurrence(key)
        rule = scheduled_tasks.get_rule(rid)
        assert occ["status"] == "running"
        assert occ["dispatched_by"] == "manager"
        assert occ["dispatched_rule_version"] == rule["version"]
        assert not (paths.state_dir() / "tasks.json").exists()


def test_re_dispatch_cancel_wins_when_rule_cancelled():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        rule = scheduled_tasks.get_rule(rid)
        manager_ops.cancel_rule(rid, actor="manager", actor_role="manager", expected_version=rule["version"])
        result = manager_ops.re_dispatch(key, actor="manager", actor_role="manager")
        assert result["dispatched"] is False
        assert result["reason"] == "rule_cancelled_or_paused"
        occ = scheduled_tasks.get_occurrence(key)
        assert occ["status"] == "cancelled"
        assert not (paths.state_dir() / "tasks.json").exists()


def test_re_dispatch_cancel_wins_when_rule_paused():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        rule = scheduled_tasks.get_rule(rid)
        manager_ops.pause_rule(rid, actor="manager", actor_role="manager", expected_version=rule["version"])
        result = manager_ops.re_dispatch(key, actor="manager", actor_role="manager")
        assert result["dispatched"] is False
        occ = scheduled_tasks.get_occurrence(key)
        assert occ["status"] == "cancelled"
        assert not (paths.state_dir() / "tasks.json").exists()


def test_fail_pause_occurrence_marks_failed_and_attention_required():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.fail_pause_occurrence(key, actor="manager", actor_role="manager", reason="worker blocked")
        occ = scheduled_tasks.get_occurrence(key)
        assert occ["status"] == "failed"
        assert occ["failure_reason"] == "worker blocked"
        rule = scheduled_tasks.get_rule(rid)
        assert rule["status"] == "attention_required"


# ── worker report-back ─────────────────────────────────────────────────


def test_worker_report_back_updates_lane_status_and_evidence():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        lane = manager_ops.choose_lane(
            key, agent="worker_course", actor="manager", actor_role="manager",
        )
        updated = manager_ops.report_back(
            key, lane["id"],
            status="done",
            evidence={"artifact": "report.md", "checksum": "abc"},
            actor="worker_course",
            actor_role="worker",
        )
        assert updated["status"] == "done"
        assert updated["evidence"] == {"artifact": "report.md", "checksum": "abc"}


def test_worker_cannot_dispatch_or_skip():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.skip_occurrence(key, actor="worker_course", actor_role="worker")
        with pytest.raises(manager_ops.AuthorizationError):
            manager_ops.re_dispatch(key, actor="worker_course", actor_role="worker")


# ── CLI entry points ───────────────────────────────────────────────────


def test_cli_schedule_create_draft_and_confirm():
    with isolated_env():
        rc, out, err = run_cli([
            "task", "schedule", "create-draft",
            "--target", "weekly report",
            "--artifact", "report.md",
            "--frequency", "weekly",
            "--timezone", "Asia/Shanghai",
            "--due", _utc(2026, 7, 13, 10, 0),
            "--as", "user",
        ])
        assert rc == 0, err
        assert "created draft D-1" in out

        rc, out, err = run_cli([
            "task", "schedule", "confirm-draft", "D-1",
            "--as", "user",
        ])
        assert rc == 0, err
        assert "confirmed D-1" in out
        rule = scheduled_tasks.get_rule("D-1")
        assert rule["status"] == "active"


def test_cli_schedule_lifecycle_pause_resume_cancel():
    with isolated_env():
        run_cli([
            "task", "schedule", "create-draft",
            "--target", "x",
            "--artifact", "x.md",
            "--frequency", "daily",
            "--timezone", "UTC",
            "--due", _utc(2026, 7, 12, 8, 0),
            "--as", "user",
        ])
        run_cli(["task", "schedule", "confirm-draft", "D-1", "--as", "user"])

        rc, out, err = run_cli(["task", "schedule", "pause", "D-1", "--as", "user"])
        assert rc == 0, err
        assert scheduled_tasks.get_rule("D-1")["status"] == "paused"

        rc, out, err = run_cli(["task", "schedule", "resume", "D-1", "--as", "user"])
        assert rc == 0, err
        assert scheduled_tasks.get_rule("D-1")["status"] == "active"

        rc, out, err = run_cli(["task", "schedule", "cancel", "D-1", "--as", "user"])
        assert rc == 0, err
        assert scheduled_tasks.get_rule("D-1")["status"] == "cancelled"


def test_cli_schedule_occurrence_confirm_skip_dispatch_report():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"

        rc, out, err = run_cli([
            "task", "schedule", "confirm-occurrence", key,
            "--as", "manager",
        ])
        assert rc == 0, err
        assert scheduled_tasks.get_occurrence(key)["status"] == "confirmed"

        rc, out, err = run_cli([
            "task", "schedule", "add-lane", key,
            "--agent", "worker_course",
            "--as", "manager",
        ])
        assert rc == 0, err
        lane_id = out.strip().split()[-1]

        rc, out, err = run_cli([
            "task", "schedule", "dispatch", key,
            "--as", "manager",
        ])
        assert rc == 0, err
        assert scheduled_tasks.get_occurrence(key)["status"] == "running"

        rc, out, err = run_cli([
            "task", "schedule", "report", key,
            "--lane", lane_id,
            "--status", "done",
            "--evidence-json", json.dumps({"artifact": "report.md"}),
            "--as", "worker",
        ])
        assert rc == 0, err
        lane = scheduled_tasks.get_lane(lane_id)
        assert lane["status"] == "done"
        assert not (paths.state_dir() / "tasks.json").exists()


def test_cli_schedule_rejects_worker_doing_manager_action():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        rc, _, err = run_cli([
            "task", "schedule", "confirm-occurrence", key,
            "--as", "worker",
        ])
        assert rc == 1
        assert "not authorized" in err
