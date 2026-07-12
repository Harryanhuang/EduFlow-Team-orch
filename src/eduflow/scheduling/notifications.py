"""Notification cadence for the D scheduled task domain.

Per P5 plan, only these event kinds generate notifications:

  * create              — when an occurrence first becomes awaiting_manager
                          (already emitted by P3 engine as `occurrence_due`)
  * supplement_confirm  — when the user supplements / confirms a draft
  * occurrence_started  — when manager dispatches (status -> running)
  * result_or_failure   — when worker reports done / failed

Cadence for reminders while an occurrence stays in awaiting_manager:

  * manager reminder: at most one per occurrence every 30 minutes
  * user notification: at most one per occurrence every 2 hours

Tick / wait / no-op reminders are forbidden: only `manager_reminder` and
`user_notification` may be appended by `compute_reminder_actions`, and
they only fire when their cadence window has elapsed since the last
same-kind + same-occurrence notification.
"""
from __future__ import annotations

from typing import Iterable

from eduflow.store import scheduled_tasks


# 30 minutes and 2 hours, in milliseconds.
MANAGER_REMINDER_INTERVAL_MS = 30 * 60 * 1000
USER_NOTIFICATION_INTERVAL_MS = 2 * 60 * 60 * 1000

# Event kinds that produce a one-shot notification per emission.
ALLOWED_KINDS = frozenset({
    "create",
    "supplement_confirm",
    "occurrence_started",
    "result_or_failure",
})

# Reminder kinds that are cadence-controlled.
REMINDER_KINDS = frozenset({
    "manager_reminder",
    "user_notification",
})

# Statuses for which reminders are still meaningful.
AWAITING_STATUS = "awaiting_manager"


def _validate_kind(kind: str) -> str:
    if kind not in ALLOWED_KINDS:
        raise ValueError(
            f"notification kind {kind!r} not allowed "
            f"(allowed: {sorted(ALLOWED_KINDS)})"
        )
    return kind


def _latest_at(rows: Iterable[dict], *, occurrence_key: str, kind: str) -> int:
    """Return the largest cadence `now_ms` (ms) across rows matching
    occurrence_key and kind, or 0 if none.  Reads from
    `payload["now_ms"]` so cadence checks are deterministic against the
    caller-supplied clock, not wall-clock `created_at`."""
    latest = 0
    for row in rows:
        if row.get("occurrence_key") != occurrence_key:
            continue
        if row.get("kind") != kind:
            continue
        payload = row.get("payload") or {}
        ts_raw = payload.get("now_ms")
        if ts_raw is None:
            ts_raw = row.get("created_at") or 0
        ts = int(ts_raw)
        if ts > latest:
            latest = ts
    return latest


def record_event(
    *,
    rule_id: str,
    occurrence_key: str | None,
    kind: str,
    recipient: str,
    payload: dict | None = None,
    now_ms: int | None = None,
) -> dict:
    """Append a one-shot event notification (create/supplement_confirm/
    occurrence_started/result_or_failure).

    Returns the persisted record.  If `now_ms` is provided, it is stored
    in `payload["now_ms"]` so future cadence calls can read it without
    relying on wall-clock `created_at`.
    """
    _validate_kind(kind)
    merged = dict(payload or {})
    if now_ms is not None:
        merged.setdefault("now_ms", int(now_ms))
    return scheduled_tasks.append_notification(
        rule_id,
        recipient,
        kind,
        occurrence_key=occurrence_key,
        payload=merged,
    )


def compute_reminder_actions(*, now_ms: int) -> list[dict]:
    """Compute manager-reminder and user-notification actions to take now.

    For each `awaiting_manager` occurrence, looks up the last
    `manager_reminder` and `user_notification` notification in the
    ledger and decides whether the cadence window has elapsed:

      * manager_reminder   fires if `now_ms - last >= 30 minutes`
                            (or never fired before)
      * user_notification  fires if `now_ms - last >= 2 hours`
                            (or never fired before)

    Each action is BOTH appended to the notification ledger and
    returned in the action list.  Idempotency: re-calling with the same
    `now_ms` does not re-fire because the ledger now contains a fresh
    same-kind same-occurrence record.
    """
    actions: list[dict] = []

    occurrences = scheduled_tasks.list_occurrences(status=AWAITING_STATUS)
    if not occurrences:
        return actions

    # Pre-load ledger once for efficiency.
    all_rows = scheduled_tasks.list_notifications()

    for occ in occurrences:
        occ_key = occ["id"]
        rule_id = occ["rule_id"]
        last_manager = _latest_at(
            all_rows, occurrence_key=occ_key, kind="manager_reminder"
        )
        last_user = _latest_at(
            all_rows, occurrence_key=occ_key, kind="user_notification"
        )

        if last_manager == 0 or (now_ms - last_manager) >= MANAGER_REMINDER_INTERVAL_MS:
            record = scheduled_tasks.append_notification(
                rule_id,
                "manager",
                "manager_reminder",
                occurrence_key=occ_key,
                payload={"now_ms": now_ms},
            )
            actions.append({
                "action": "notify",
                "recipient": "manager",
                "kind": "manager_reminder",
                "rule_id": rule_id,
                "occurrence_key": occ_key,
                "created_at": record["created_at"],
            })

        if last_user == 0 or (now_ms - last_user) >= USER_NOTIFICATION_INTERVAL_MS:
            record = scheduled_tasks.append_notification(
                rule_id,
                "user",
                "user_notification",
                occurrence_key=occ_key,
                payload={"now_ms": now_ms},
            )
            actions.append({
                "action": "notify",
                "recipient": "user",
                "kind": "user_notification",
                "rule_id": rule_id,
                "occurrence_key": occ_key,
                "created_at": record["created_at"],
            })

    return actions


def actions_for_occurrence(actions: list[dict], occurrence_key: str) -> list[dict]:
    """Filter helper for tests and callers: actions targeting one occurrence."""
    return [a for a in actions if a.get("occurrence_key") == occurrence_key]