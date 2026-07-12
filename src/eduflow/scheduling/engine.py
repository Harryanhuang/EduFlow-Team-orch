"""Scheduler tick engine for D-ID scheduled tasks.

`tick(now_ms)` detects due rules and creates `awaiting_manager`
occurrences.  It never dispatches.  `reconcile(now_ms)` handles restart
mid-state, missed notifications and missed due times.

The scheduler uses its own cursor and heartbeat files and must not
reuse the normal task-publish cursor.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from eduflow.runtime import paths
from eduflow.store import scheduled_tasks
from eduflow.util import read_json, write_json


_ACTIVE_OCCURRENCE_STATUSES = frozenset({
    "awaiting_manager",
    "confirmed",
    "running",
    "blocked",
})


def _utc_to_ms(iso: str) -> int:
    """Convert an ISO 8601 UTC string to epoch milliseconds."""
    text = str(iso or "").replace("Z", "+00:00")
    if not text:
        return 0
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _ms_to_utc(ms: int) -> str:
    """Convert epoch milliseconds to ISO 8601 UTC string ending in Z."""
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_next_due(frequency: str, current_due_utc: str) -> str:
    """Return the next due time in UTC for a supported frequency."""
    text = str(current_due_utc or "").replace("Z", "+00:00")
    if not text:
        return ""
    current = datetime.fromisoformat(text)
    if frequency == "once":
        return ""
    if frequency == "daily":
        nxt = current + timedelta(days=1)
    elif frequency == "weekly":
        nxt = current + timedelta(weeks=1)
    else:
        return ""
    return nxt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_cursor() -> dict:
    return read_json(paths.scheduler_cursor_file(), {"last_tick_at": 0, "last_reconcile_at": 0})


def _save_cursor(cursor: dict) -> None:
    write_json(paths.scheduler_cursor_file(), cursor)


def _active_unfinished_occurrences(rule_id: str) -> list[dict]:
    return [
        o for o in scheduled_tasks.list_occurrences(rule_id=rule_id)
        if o.get("status") in _ACTIVE_OCCURRENCE_STATUSES
    ]


def _handle_due_rule(rule: dict, result: dict) -> None:
    """Process one due cycle for a rule and advance its next_due_utc.

    Idempotent: if an occurrence for this scheduled_at already exists,
    the cycle is only advanced.
    """
    rule_id = rule["id"]
    scheduled_at = str(rule.get("next_due_utc") or "")
    key = f"{rule_id}:{scheduled_at}"
    capacity = int(rule.get("capacity") or 1)
    version = rule.get("version", 1)

    existing = scheduled_tasks.get_occurrence(key)
    if existing is not None:
        # Already processed this cycle; just advance the rule schedule.
        if rule.get("frequency") == "once":
            scheduled_tasks.update_rule(rule_id, {"next_due_utc": ""}, expected_version=version)
        else:
            nxt = _compute_next_due(rule["frequency"], scheduled_at)
            if nxt:
                scheduled_tasks.update_rule(rule_id, {"next_due_utc": nxt}, expected_version=version)
                result.setdefault("next_due_updated", []).append(
                    {"rule_id": rule_id, "next_due_utc": nxt}
                )
        return

    active = _active_unfinished_occurrences(rule_id)
    has_running = any(o.get("status") == "running" for o in active)
    has_awaiting = any(o.get("status") == "awaiting_manager" for o in active)

    if has_running:
        scheduled_tasks.create_occurrence(
            rule_id, scheduled_at, status="blocked",
            context={"reason": "blocked_by_previous_run"},
        )
        result.setdefault("blocked", []).append(key)
    elif has_awaiting:
        scheduled_tasks.create_occurrence(
            rule_id, scheduled_at, status="skipped",
            context={"reason": "previous_occurrence_not_confirmed"},
        )
        result.setdefault("skipped", []).append(key)
    elif len(active) >= capacity:
        scheduled_tasks._transition_rule_status(rule_id, version, "attention_required")
        result.setdefault("attention_required", []).append(rule_id)
        return
    else:
        scheduled_tasks.create_occurrence(rule_id, scheduled_at, status="awaiting_manager")
        scheduled_tasks.append_notification(
            rule_id, "manager", "occurrence_due",
            occurrence_key=key,
            payload={"scheduled_at_utc": scheduled_at},
        )
        result.setdefault("occurrences_created", []).append(key)

    if rule.get("frequency") == "once":
        scheduled_tasks.update_rule(rule_id, {"next_due_utc": ""}, expected_version=version)
    else:
        nxt = _compute_next_due(rule["frequency"], scheduled_at)
        if nxt:
            scheduled_tasks.update_rule(rule_id, {"next_due_utc": nxt}, expected_version=version)
            result.setdefault("next_due_updated", []).append(
                {"rule_id": rule_id, "next_due_utc": nxt}
            )


def tick(now_ms: int) -> dict:
    """Detect due rules and create `awaiting_manager` occurrences.

    Does not dispatch.  Updates the scheduler cursor and heartbeat.
    """
    result = {
        "ticked_at": now_ms,
        "occurrences_created": [],
        "skipped": [],
        "blocked": [],
        "attention_required": [],
        "next_due_updated": [],
    }

    for rule in scheduled_tasks.list_rules(status="active"):
        if not rule.get("next_due_utc"):
            continue
        due_ms = _utc_to_ms(rule["next_due_utc"])
        if due_ms > now_ms:
            continue
        _handle_due_rule(rule, result)

    cursor = _load_cursor()
    cursor["last_tick_at"] = now_ms
    _save_cursor(cursor)
    scheduled_tasks.touch_heartbeat(lag_ms=0, error="")
    return result


def reconcile(now_ms: int) -> dict:
    """Handle restart mid-state, missed notifications and missed due times."""
    result: dict[str, Any] = {
        "reconciled_at": now_ms,
        "missed_due_caught_up": [],
        "notifications_replayed": [],
    }

    for rule in scheduled_tasks.list_rules(status="active"):
        while True:
            if not rule.get("next_due_utc"):
                break
            due_ms = _utc_to_ms(rule["next_due_utc"])
            if due_ms > now_ms:
                break
            before_key = f"{rule['id']}:{rule['next_due_utc']}"
            _handle_due_rule(rule, result)
            result["missed_due_caught_up"].append(before_key)
            refreshed_rule = scheduled_tasks.get_rule(rule["id"])
            if refreshed_rule is None:
                break
            rule = refreshed_rule

    # Replay notifications for occurrences that should have been notified
    # but have no ledger record (e.g. after a crash between state write and
    # notification append).
    for occ in scheduled_tasks.list_occurrences(status="awaiting_manager"):
        rule_id = occ["rule_id"]
        key = occ["id"]
        notifications = scheduled_tasks.list_notifications(rule_id=rule_id, kind="occurrence_due")
        if not any(n.get("occurrence_key") == key for n in notifications):
            scheduled_tasks.append_notification(
                rule_id, "manager", "occurrence_due",
                occurrence_key=key,
                payload={"scheduled_at_utc": occ.get("scheduled_at_utc", ""), "replayed": True},
            )
            result["notifications_replayed"].append(key)

    cursor = _load_cursor()
    cursor["last_reconcile_at"] = now_ms
    _save_cursor(cursor)
    return result


def scheduler_tick(now_ms: int) -> dict:
    """Run reconcile then tick, recording heartbeat and error state."""
    try:
        reconcile_result = reconcile(now_ms)
        tick_result = tick(now_ms)
        merged = {
            "ticked_at": now_ms,
            "occurrences_created": tick_result.get("occurrences_created", []),
            "skipped": tick_result.get("skipped", []),
            "blocked": tick_result.get("blocked", []),
            "attention_required": tick_result.get("attention_required", []),
            "next_due_updated": tick_result.get("next_due_updated", []),
            "missed_due_caught_up": reconcile_result.get("missed_due_caught_up", []),
            "notifications_replayed": reconcile_result.get("notifications_replayed", []),
        }
        cursor = _load_cursor()
        cursor["last_tick_at"] = now_ms
        cursor["last_reconcile_at"] = now_ms
        _save_cursor(cursor)
        scheduled_tasks.touch_heartbeat(lag_ms=0, error="")
        return merged
    except Exception as exc:
        scheduled_tasks.touch_heartbeat(lag_ms=0, error=f"{type(exc).__name__}: {exc}")
        raise
