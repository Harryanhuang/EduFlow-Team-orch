"""P5: notification cadence for the D scheduled task domain.

Notification kinds allowed (per plan):
  * create              — when an occurrence first becomes awaiting_manager
  * supplement_confirm  — when the user supplements / confirms a draft
  * occurrence_started  — when manager dispatches (status -> running)
  * result_or_failure   — when worker reports done / failed

Cadence for reminders while an occurrence stays in awaiting_manager:
  * manager reminder: at most one per occurrence every 30 minutes
  * user notification: at most one per occurrence every 2 hours

Tick / wait / no-op reminders are forbidden: the only reminder kinds are
the two above, and they only fire when their cadence window has elapsed.

The module under test (`eduflow.scheduling.notifications`) is a pure
function over the scheduled_tasks store; tests pass an explicit `now_ms`
and rely on `isolated_env()` for state isolation.
"""
from __future__ import annotations

import pytest

from helpers import isolated_env

from eduflow.scheduling import notifications
from eduflow.store import scheduled_tasks


# ── helpers ──────────────────────────────────────────────────────────


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _awaiting_rule_and_key(*, next_due_utc: str, frequency: str = "daily"):
    """Create an active rule and tick once so an awaiting occurrence
    exists.  Returns (rule_id, occurrence_key)."""
    rid = scheduled_tasks.create_rule(
        target="x",
        artifact="x.md",
        frequency=frequency,
        timezone="UTC",
        next_due_utc=next_due_utc,
    )
    from eduflow.scheduling import engine
    due_ms = _ms_from_iso(next_due_utc)
    engine.tick(due_ms)
    return rid, f"{rid}:{next_due_utc}"


def _ms_from_iso(iso: str) -> int:
    from datetime import datetime, timezone
    text = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(text).timestamp() * 1000)


# ── cadence constants ──────────────────────────────────────────────


def test_cadence_constants_are_documented_values():
    assert notifications.MANAGER_REMINDER_INTERVAL_MS == 30 * 60 * 1000
    assert notifications.USER_NOTIFICATION_INTERVAL_MS == 2 * 60 * 60 * 1000


def test_allowed_notification_kinds_are_exactly_the_four():
    assert notifications.ALLOWED_KINDS == frozenset({
        "create",
        "supplement_confirm",
        "occurrence_started",
        "result_or_failure",
    })


def test_reminder_kinds_are_exactly_manager_and_user():
    assert notifications.REMINDER_KINDS == frozenset({
        "manager_reminder",
        "user_notification",
    })


# ── record_event (one-shot event notifications) ─────────────────────


def test_record_event_appends_a_single_notification():
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        record = notifications.record_event(
            rule_id=rid,
            occurrence_key=key,
            kind="supplement_confirm",
            recipient="user",
            payload={"note": "please confirm"},
        )
        assert record["kind"] == "supplement_confirm"
        # Filter by kind — the engine already appended occurrence_due from
        # the tick, so we only count the new record_event notification.
        rows = scheduled_tasks.list_notifications(rule_id=rid, kind="supplement_confirm")
        assert len(rows) == 1
        assert rows[0]["recipient"] == "user"
        assert rows[0]["kind"] == "supplement_confirm"


def test_record_event_rejects_unknown_kind():
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        with pytest.raises(ValueError):
            notifications.record_event(
                rule_id=rid,
                occurrence_key=key,
                kind="tick_spam",
                recipient="manager",
            )


# ── cadence: manager reminder 30 min ────────────────────────────────


def test_manager_reminder_fires_once_on_first_compute():
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 8, 30)
        actions = notifications.compute_reminder_actions(now_ms=t0)
        manager_actions = [
            a for a in actions
            if a["recipient"] == "manager" and a["kind"] == "manager_reminder"
            and a["occurrence_key"] == key
        ]
        assert len(manager_actions) == 1
        assert manager_actions[0]["rule_id"] == rid
        # Notification persisted to ledger.
        rows = scheduled_tasks.list_notifications(rule_id=rid, kind="manager_reminder")
        assert len(rows) == 1


def test_manager_reminder_does_not_re_fire_within_30_minutes():
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 8, 30)
        first = notifications.compute_reminder_actions(now_ms=t0)
        # Same window: re-call 5 minutes later, must NOT re-fire manager_reminder.
        t1 = _ms(2026, 7, 13, 8, 35)
        second = notifications.compute_reminder_actions(now_ms=t1)
        first_manager = [a for a in first if a["kind"] == "manager_reminder" and a["occurrence_key"] == key]
        second_manager = [a for a in second if a["kind"] == "manager_reminder" and a["occurrence_key"] == key]
        assert len(first_manager) == 1
        assert len(second_manager) == 0


def test_manager_reminder_re_fires_after_30_minute_window():
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 8, 30)
        notifications.compute_reminder_actions(now_ms=t0)
        # 31 minutes later — cadence window has elapsed, must re-fire.
        t1 = _ms(2026, 7, 13, 9, 1)
        actions = notifications.compute_reminder_actions(now_ms=t1)
        fired = [a for a in actions if a["kind"] == "manager_reminder" and a["occurrence_key"] == key]
        assert len(fired) == 1
        rows = scheduled_tasks.list_notifications(kind="manager_reminder")
        assert len(rows) == 2


# ── cadence: user notification 2 hours ──────────────────────────────


def test_user_notification_fires_once_on_first_compute():
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 10, 0)
        actions = notifications.compute_reminder_actions(now_ms=t0)
        user_actions = [
            a for a in actions
            if a["recipient"] == "user" and a["kind"] == "user_notification"
            and a["occurrence_key"] == key
        ]
        assert len(user_actions) == 1


def test_user_notification_does_not_re_fire_within_2_hours():
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 10, 0)
        notifications.compute_reminder_actions(now_ms=t0)
        # 1 hour later — within the 2-hour cadence window.
        t1 = _ms(2026, 7, 13, 11, 0)
        actions = notifications.compute_reminder_actions(now_ms=t1)
        user_actions = [
            a for a in actions
            if a["kind"] == "user_notification" and a["occurrence_key"] == key
        ]
        assert user_actions == []


def test_user_notification_re_fires_after_2_hour_window():
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 10, 0)
        notifications.compute_reminder_actions(now_ms=t0)
        # 2 hours 1 minute later — cadence window has elapsed.
        t1 = _ms(2026, 7, 13, 12, 1)
        actions = notifications.compute_reminder_actions(now_ms=t1)
        fired = [a for a in actions if a["kind"] == "user_notification" and a["occurrence_key"] == key]
        assert len(fired) == 1


def test_manager_and_user_cadence_are_independent():
    """Manager cadence (30 min) and user cadence (2 h) are independent.
    A manager re-fire at 30 min must NOT cause a user re-fire."""
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        # First round: fire both.
        t0 = _ms(2026, 7, 13, 9, 0)
        notifications.compute_reminder_actions(now_ms=t0)
        # Second round: manager window elapsed (30 min), user window not (still < 2 h since first user).
        t1 = _ms(2026, 7, 13, 9, 35)
        actions = notifications.compute_reminder_actions(now_ms=t1)
        kinds = sorted({a["kind"] for a in actions if a["occurrence_key"] == key})
        assert "manager_reminder" in kinds
        assert "user_notification" not in kinds


# ── no tick / wait spam ────────────────────────────────────────────


def test_no_actions_for_occurrences_not_in_awaiting_state():
    """Confirmed / running / skipped / failed / cancelled occurrences
    must NOT produce any reminder actions, regardless of cadence."""
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        # Confirm the occurrence (no longer awaiting_manager).
        scheduled_tasks.update_occurrence(key, {"status": "confirmed"})
        actions = notifications.compute_reminder_actions(
            now_ms=_ms(2026, 7, 13, 9, 0)
        )
        matching = [a for a in actions if a["occurrence_key"] == key]
        assert matching == []


def test_no_duplicate_reminders_across_two_computes_at_same_now():
    """Idempotency: calling compute twice at the same `now_ms` must not
    double-fire reminders (it appends only one per window)."""
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        t0 = _ms(2026, 7, 13, 9, 0)
        a = notifications.compute_reminder_actions(now_ms=t0)
        b = notifications.compute_reminder_actions(now_ms=t0)
        first = [x for x in a if x["occurrence_key"] == key]
        second = [x for x in b if x["occurrence_key"] == key]
        assert len(first) == 2  # one manager, one user
        assert len(second) == 0  # cadence already satisfied


# ── multiple occurrences are independent ────────────────────────────


def test_two_awaiting_occurrences_have_independent_cadence():
    """Each occurrence has its own cadence clock.  Manager reminder for
    occ A at t0 must NOT prevent manager reminder for occ B at t0+5min."""
    with isolated_env():
        rid_a, key_a = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        # Second rule due an hour later.
        rid_b, key_b = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 9, 0))
        t0 = _ms(2026, 7, 13, 8, 30)
        first = notifications.compute_reminder_actions(now_ms=t0)
        # Both occurrences are awaiting_manager at t0 (both due < t0).
        manager_for_a = [a for a in first if a["kind"] == "manager_reminder" and a["occurrence_key"] == key_a]
        manager_for_b = [a for a in first if a["kind"] == "manager_reminder" and a["occurrence_key"] == key_b]
        assert len(manager_for_a) == 1
        assert len(manager_for_b) == 1


def test_occurrence_due_creation_is_recorded_as_create_notification():
    """P3 engine already records `occurrence_due` for the create event.
    Reminder module must not duplicate that — it only appends
    manager_reminder / user_notification, never create."""
    with isolated_env():
        rid, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        # tick already appended occurrence_due as create-kind.
        rows_before = scheduled_tasks.list_notifications(rule_id=rid, kind="occurrence_due")
        assert len(rows_before) == 1
        actions = notifications.compute_reminder_actions(now_ms=_ms(2026, 7, 13, 9, 0))
        # Reminder module MUST NOT re-emit occurrence_due as a reminder.
        assert all(a["kind"] != "occurrence_due" for a in actions)
        # Only manager_reminder and user_notification should appear.
        kinds = {a["kind"] for a in actions if a["occurrence_key"] == key}
        assert kinds <= notifications.REMINDER_KINDS


# ── dispatch callback never produces reminders ─────────────────────


def test_no_reminders_after_occurrence_dispatched():
    """Once an occurrence leaves awaiting_manager, reminders stop, even
    if cadence would otherwise be due."""
    with isolated_env():
        _, key = _awaiting_rule_and_key(next_due_utc=_utc(2026, 7, 13, 8, 0))
        # First compute fires reminders.
        notifications.compute_reminder_actions(now_ms=_ms(2026, 7, 13, 9, 0))
        # Occurrence gets dispatched (running) — no more reminders.
        scheduled_tasks.update_occurrence(key, {"status": "running"})
        actions = notifications.compute_reminder_actions(now_ms=_ms(2026, 7, 13, 10, 0))
        matching = [a for a in actions if a["occurrence_key"] == key]
        assert matching == []