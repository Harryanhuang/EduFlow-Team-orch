"""P3: scheduler tick engine.

Tests tick/reconcile/backpressure for the D scheduler domain.
"""
from __future__ import annotations


import pytest

from helpers import isolated_env
from eduflow.runtime import paths
from eduflow.scheduling import engine
from eduflow.store import scheduled_tasks


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# ── tick basics ──────────────────────────────────────────────────────


def test_tick_creates_awaiting_manager_occurrence_for_due_rule():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="daily standup summary",
            artifact="summary.md",
            frequency="daily",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        result = engine.tick(_ms(2026, 7, 12, 8, 0))
        assert result["occurrences_created"] == [f"{did}:2026-07-12T08:00:00Z"]
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        assert occ["status"] == "awaiting_manager"
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == _utc(2026, 7, 13, 8, 0)


def test_tick_does_not_create_occurrence_before_due():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="daily standup summary",
            artifact="summary.md",
            frequency="daily",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        result = engine.tick(_ms(2026, 7, 12, 7, 59))
        assert result["occurrences_created"] == []
        assert scheduled_tasks.list_occurrences(rule_id=did) == []


def test_tick_is_idempotent():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="daily standup summary",
            artifact="summary.md",
            frequency="daily",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        result = engine.tick(_ms(2026, 7, 12, 8, 0))
        assert result["occurrences_created"] == []
        assert len(scheduled_tasks.list_occurrences(rule_id=did)) == 1


def test_tick_does_not_create_user_visible_t_tasks():
    with isolated_env():
        scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="once",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        assert not (paths.state_dir() / "tasks.json").exists()


def test_tick_appends_manager_notification():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        notifications = scheduled_tasks.list_notifications(rule_id=did)
        assert len(notifications) == 1
        assert notifications[0]["recipient"] == "manager"
        assert notifications[0]["kind"] == "occurrence_due"


# ── frequency advancement ────────────────────────────────────────────


def test_tick_advances_daily_rule():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == _utc(2026, 7, 13, 8, 0)


def test_tick_advances_weekly_rule():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="weekly",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == _utc(2026, 7, 19, 8, 0)


def test_tick_clears_next_due_for_once_rule():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="once",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == ""


# ── backpressure / cross-cycle behavior ──────────────────────────────


def test_tick_skips_new_cycle_when_previous_not_confirmed():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert result["skipped"] == [f"{did}:2026-07-13T08:00:00Z"]
        skipped = scheduled_tasks.get_occurrence(f"{did}:2026-07-13T08:00:00Z")
        assert skipped["status"] == "skipped"


def test_tick_blocks_new_cycle_when_previous_running():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        scheduled_tasks.update_occurrence(
            occ["id"], {"status": "running"}, expected_version=None
        )
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert result["blocked"] == [f"{did}:2026-07-13T08:00:00Z"]
        blocked = scheduled_tasks.get_occurrence(f"{did}:2026-07-13T08:00:00Z")
        assert blocked["status"] == "blocked"


def test_tick_transitions_rule_to_attention_required_when_capacity_exceeded():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
            capacity=1,
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Confirm the first occurrence so it is no longer awaiting_manager,
        # but keep it in confirmed state to occupy capacity.
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        scheduled_tasks.update_occurrence(
            occ["id"], {"status": "confirmed"}, expected_version=None
        )
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert did in result["attention_required"]
        rule = scheduled_tasks.get_rule(did)
        assert rule["status"] == "attention_required"


def test_tick_does_not_run_parallel_occurrences_by_default():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
            capacity=1,
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        scheduled_tasks.update_occurrence(
            f"{did}:2026-07-12T08:00:00Z",
            {"status": "running"},
            expected_version=None,
        )
        engine.tick(_ms(2026, 7, 13, 8, 0))
        assert len(scheduled_tasks.list_occurrences(rule_id=did, status="running")) == 1
        assert len(scheduled_tasks.list_occurrences(rule_id=did, status="blocked")) == 1


# ── heartbeat / cursor isolation ─────────────────────────────────────


def test_tick_records_scheduler_heartbeat():
    with isolated_env():
        scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        hb = scheduled_tasks.get_heartbeat()
        assert hb["last_tick_at"] > 0
        assert hb["error"] == ""


def test_tick_uses_scheduler_cursor_not_task_publish_cursor():
    with isolated_env():
        scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        assert paths.scheduler_cursor_file().exists()
        assert not paths.task_publish_cursor_file().exists()


# ── reconcile ────────────────────────────────────────────────────────


def test_reconcile_catches_missed_due_times():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        result = engine.reconcile(_ms(2026, 7, 15, 8, 0))
        # Cycles due on 7/12, 7/13, 7/14 and 7/15 are all <= now.
        assert len(result["missed_due_caught_up"]) == 4
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == _utc(2026, 7, 16, 8, 0)


def test_reconcile_replays_missed_notifications():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Simulate lost notification by clearing the ledger.
        paths.scheduler_notifications_file().write_text("", encoding="utf-8")
        result = engine.reconcile(_ms(2026, 7, 12, 8, 1))
        assert len(result["notifications_replayed"]) == 1
        notifications = scheduled_tasks.list_notifications(rule_id=did)
        assert len(notifications) == 1


def test_reconcile_does_not_guess_running_occurrence_complete():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        scheduled_tasks.update_occurrence(
            f"{did}:2026-07-12T08:00:00Z",
            {"status": "running"},
            expected_version=None,
        )
        engine.reconcile(_ms(2026, 7, 12, 8, 1))
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        assert occ["status"] == "running"


# ── scheduler_tick boundary ──────────────────────────────────────────


def test_scheduler_tick_runs_reconcile_and_tick():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        result = engine.scheduler_tick(_ms(2026, 7, 12, 8, 0))
        assert f"{did}:2026-07-12T08:00:00Z" in result["missed_due_caught_up"]
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        assert occ["status"] == "awaiting_manager"


def test_scheduler_tick_records_error_in_heartbeat_and_re_raises():
    with isolated_env():
        scheduled_tasks.create_rule(
            target="x",
            artifact="x.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc="not-a-date",
        )
        with pytest.raises(ValueError):
            engine.scheduler_tick(_ms(2026, 7, 12, 8, 0))
        hb = scheduled_tasks.get_heartbeat()
        assert "ValueError" in hb["error"]
