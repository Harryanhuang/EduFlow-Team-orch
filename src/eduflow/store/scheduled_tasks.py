"""Independent D-ID scheduled task store.

D domain persists separately from the T task store:
  - rules.json       active/paused/cancelled D rules
  - occurrences.json awaiting_manager / running / skipped / done occurrences
  - lanes.json       lane snapshots bound to an occurrence
  - notifications.jsonl  manager/user notification ledger
  - heartbeat.json   last tick / success / lag
  - meta.json        D-ID sequence counter

All mutating operations on rules are CAS/version protected.  Cancel does
not delete records; it marks status and records cancelled_at.
"""
from __future__ import annotations

from eduflow.runtime import paths
from eduflow.util import flock, now_ms, read_json, read_jsonl, write_json


VALID_FREQUENCIES = frozenset({"once", "daily", "weekly"})
VALID_RULE_STATUSES = frozenset({"active", "paused", "cancelled", "attention_required"})
VALID_OCCURRENCE_STATUSES = frozenset({
    "awaiting_manager",
    "confirmed",
    "running",
    "blocked",
    "skipped",
    "done",
    "failed",
})

# Allowed rule status transitions.  Empty set means terminal.
RULE_TRANSITIONS = {
    "active": {"paused", "cancelled", "attention_required"},
    "paused": {"active", "cancelled"},
    "cancelled": set(),
    "attention_required": {"active", "cancelled"},
}


class VersionConflict(Exception):
    """Raised when a CAS write finds a different version than expected."""


class NotFound(Exception):
    """Raised when a requested rule/occurrence/lane does not exist."""


# ── low-level file helpers ───────────────────────────────────────────


def _rules_file():
    return paths.scheduler_rules_file()


def _occurrences_file():
    return paths.scheduler_occurrences_file()


def _lanes_file():
    return paths.scheduler_lanes_file()


def _notifications_file():
    return paths.scheduler_notifications_file()


def _heartbeat_file():
    return paths.scheduler_heartbeat_file()


def _meta_file():
    return paths.scheduler_meta_file()


def _rules_lock():
    return flock(_rules_file().with_suffix(".lock"))


def _occurrences_lock():
    return flock(_occurrences_file().with_suffix(".lock"))


def _lanes_lock():
    return flock(_lanes_file().with_suffix(".lock"))


def _meta_lock():
    return flock(_meta_file().with_suffix(".lock"))


def _load_rules() -> dict:
    return read_json(_rules_file(), {"rules": [], "_meta": {"version_counter": 0}})


def _save_rules(data: dict) -> None:
    write_json(_rules_file(), data)


def _load_occurrences() -> dict:
    return read_json(_occurrences_file(), {"occurrences": [], "_meta": {"version_counter": 0}})


def _save_occurrences(data: dict) -> None:
    write_json(_occurrences_file(), data)


def _load_lanes() -> dict:
    return read_json(_lanes_file(), {"lanes": [], "_meta": {"version_counter": 0}})


def _save_lanes(data: dict) -> None:
    write_json(_lanes_file(), data)


def _load_meta() -> dict:
    return read_json(_meta_file(), {"last_id": 0})


def _save_meta(data: dict) -> None:
    write_json(_meta_file(), data)


# ── D-ID allocation ──────────────────────────────────────────────────


def _next_d_id() -> str:
    with _meta_lock():
        data = _load_meta()
        data["last_id"] = data.get("last_id", 0) + 1
        _save_meta(data)
        return f"D-{data['last_id']}"


# ── rules ────────────────────────────────────────────────────────────


def _validate_frequency(value: str) -> str:
    value = str(value or "").strip()
    if value not in VALID_FREQUENCIES:
        raise ValueError(f"invalid frequency: {value!r} (valid: {sorted(VALID_FREQUENCIES)})")
    return value


def _validate_rule_status(value: str) -> str:
    value = str(value or "").strip()
    if value not in VALID_RULE_STATUSES:
        raise ValueError(f"invalid status: {value!r} (valid: {sorted(VALID_RULE_STATUSES)})")
    return value


def _find_rule(data: dict, rule_id: str) -> dict | None:
    for rule in data.get("rules", []):
        if rule.get("id") == rule_id:
            return rule
    return None


def create_rule(
    *,
    target: str,
    artifact: str,
    frequency: str,
    timezone: str,
    next_due_utc: str,
    capacity: int = 1,
    workflow_state: dict | None = None,
) -> str:
    """Create a new D rule and return its D-<id>."""
    rule_id = _next_d_id()
    created_at = now_ms()
    rule = {
        "id": rule_id,
        "version": 1,
        "target": str(target or "").strip(),
        "artifact": str(artifact or "").strip(),
        "frequency": _validate_frequency(frequency),
        "timezone": str(timezone or "").strip(),
        "next_due_utc": str(next_due_utc or "").strip(),
        "status": "active",
        "capacity": int(capacity or 1),
        "workflow_state": dict(workflow_state) if workflow_state else {},
        "created_at": created_at,
        "updated_at": created_at,
        "cancelled_at": None,
    }
    with _rules_lock():
        data = _load_rules()
        data["rules"].append(rule)
        _save_rules(data)
    return rule_id


def get_rule(rule_id: str) -> dict | None:
    data = _load_rules()
    return _find_rule(data, rule_id)


def list_rules(*, status: str | None = None) -> list[dict]:
    data = _load_rules()
    rules = list(data.get("rules", []))
    if status is not None:
        rules = [r for r in rules if r.get("status") == status]
    return rules


def update_rule(
    rule_id: str,
    changes: dict,
    *,
    expected_version: int,
) -> dict:
    """CAS update of a rule.  `changes` may contain any rule field except
    id/version/created_at/cancelled_at/status (use lifecycle ops for status).
    """
    forbidden = {"id", "version", "created_at", "cancelled_at"}
    if forbidden & set(changes):
        raise ValueError(f"cannot mutate protected fields: {sorted(forbidden & set(changes))}")
    if "status" in changes:
        raise ValueError("use pause_rule/resume_rule/cancel_rule for status changes")

    with _rules_lock():
        data = _load_rules()
        rule = _find_rule(data, rule_id)
        if rule is None:
            raise NotFound(f"rule {rule_id} not found")
        if rule.get("version") != expected_version:
            raise VersionConflict(
                f"rule {rule_id} version {rule.get('version')} != expected {expected_version}"
            )
        for key, value in changes.items():
            if key == "frequency":
                value = _validate_frequency(value)
            elif key == "capacity":
                value = int(value or 1)
            rule[key] = value
        rule["version"] = expected_version + 1
        rule["updated_at"] = now_ms()
        _save_rules(data)
        return dict(rule)


def _transition_rule_status(rule_id: str, expected_version: int, new_status: str) -> dict:
    new_status = _validate_rule_status(new_status)
    with _rules_lock():
        data = _load_rules()
        rule = _find_rule(data, rule_id)
        if rule is None:
            raise NotFound(f"rule {rule_id} not found")
        current = rule.get("status")
        if current != "cancelled" and new_status == current:
            # Idempotent no-op, but still bump version for consistency.
            rule["version"] = expected_version + 1
            rule["updated_at"] = now_ms()
            _save_rules(data)
            return dict(rule)
        if current not in RULE_TRANSITIONS or new_status not in RULE_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"illegal status transition: {current} -> {new_status}"
            )
        if rule.get("version") != expected_version:
            raise VersionConflict(
                f"rule {rule_id} version {rule.get('version')} != expected {expected_version}"
            )
        rule["status"] = new_status
        rule["version"] = expected_version + 1
        rule["updated_at"] = now_ms()
        if new_status == "cancelled":
            rule["cancelled_at"] = now_ms()
        _save_rules(data)
        return dict(rule)


def pause_rule(rule_id: str, *, expected_version: int) -> dict:
    return _transition_rule_status(rule_id, expected_version, "paused")


def resume_rule(rule_id: str, *, expected_version: int) -> dict:
    return _transition_rule_status(rule_id, expected_version, "active")


def cancel_rule(rule_id: str, *, expected_version: int) -> dict:
    return _transition_rule_status(rule_id, expected_version, "cancelled")


# ── occurrences ──────────────────────────────────────────────────────


def _occurrence_key(rule_id: str, scheduled_at_utc: str) -> str:
    return f"{rule_id}:{str(scheduled_at_utc or '').strip()}"


def _find_occurrence(data: dict, key: str) -> dict | None:
    for occ in data.get("occurrences", []):
        if occ.get("id") == key:
            return occ
    return None


def create_occurrence(
    rule_id: str,
    scheduled_at_utc: str,
    *,
    status: str = "awaiting_manager",
    context: dict | None = None,
) -> str:
    """Create or return an existing occurrence keyed by rule_id + scheduled_at_utc."""
    key = _occurrence_key(rule_id, scheduled_at_utc)
    with _occurrences_lock():
        data = _load_occurrences()
        existing = _find_occurrence(data, key)
        if existing is not None:
            return key
        created_at = now_ms()
        occurrence = {
            "id": key,
            "rule_id": rule_id,
            "scheduled_at_utc": str(scheduled_at_utc or "").strip(),
            "status": status if status in VALID_OCCURRENCE_STATUSES else "awaiting_manager",
            "context": dict(context) if context else {},
            "created_at": created_at,
            "updated_at": created_at,
        }
        data["occurrences"].append(occurrence)
        _save_occurrences(data)
        return key


def get_occurrence(key: str) -> dict | None:
    data = _load_occurrences()
    return _find_occurrence(data, key)


def list_occurrences(*, rule_id: str | None = None, status: str | None = None) -> list[dict]:
    data = _load_occurrences()
    occurrences = list(data.get("occurrences", []))
    if rule_id is not None:
        occurrences = [o for o in occurrences if o.get("rule_id") == rule_id]
    if status is not None:
        occurrences = [o for o in occurrences if o.get("status") == status]
    return occurrences


def update_occurrence(
    key: str,
    changes: dict,
    *,
    expected_version: int | None = None,
) -> dict:
    """CAS update of an occurrence.  `changes` may not touch id/rule_id/created_at."""
    forbidden = {"id", "rule_id", "created_at"}
    if forbidden & set(changes):
        raise ValueError(f"cannot mutate protected fields: {sorted(forbidden & set(changes))}")
    with _occurrences_lock():
        data = _load_occurrences()
        occ = _find_occurrence(data, key)
        if occ is None:
            raise NotFound(f"occurrence {key} not found")
        if expected_version is not None and occ.get("version") != expected_version:
            raise VersionConflict(
                f"occurrence {key} version {occ.get('version')} != expected {expected_version}"
            )
        for key_name, value in changes.items():
            occ[key_name] = value
        occ["version"] = (expected_version or occ.get("version", 0)) + 1
        occ["updated_at"] = now_ms()
        _save_occurrences(data)
        return dict(occ)


# ── lanes ────────────────────────────────────────────────────────────


def _find_lane(data: dict, lane_id: str) -> dict | None:
    for lane in data.get("lanes", []):
        if lane.get("id") == lane_id:
            return lane
    return None


def create_lane(
    *,
    occurrence_key: str,
    agent: str,
    dependencies: list[str] | None = None,
    inputs: dict | None = None,
    artifacts: list[str] | None = None,
    evidence: dict | None = None,
) -> str:
    """Persist a lane snapshot bound to an occurrence."""
    lane_id = f"{occurrence_key}:lane:{now_ms()}"
    created_at = now_ms()
    lane = {
        "id": lane_id,
        "occurrence_key": occurrence_key,
        "agent": str(agent or "").strip(),
        "dependencies": list(dependencies or []),
        "inputs": dict(inputs) if inputs else {},
        "artifacts": list(artifacts or []),
        "evidence": dict(evidence) if evidence else {},
        "status": "pending",
        "created_at": created_at,
        "updated_at": created_at,
    }
    with _lanes_lock():
        data = _load_lanes()
        data["lanes"].append(lane)
        _save_lanes(data)
    return lane_id


def get_lane(lane_id: str) -> dict | None:
    data = _load_lanes()
    return _find_lane(data, lane_id)


def list_lanes(*, occurrence_key: str | None = None) -> list[dict]:
    data = _load_lanes()
    lanes = list(data.get("lanes", []))
    if occurrence_key is not None:
        lanes = [l for l in lanes if l.get("occurrence_key") == occurrence_key]
    return lanes


# ── notification ledger ──────────────────────────────────────────────


def append_notification(
    rule_id: str,
    recipient: str,
    kind: str,
    *,
    occurrence_key: str | None = None,
    payload: dict | None = None,
) -> dict:
    """Append an immutable notification record to the ledger."""
    from pathlib import Path
    path = _notifications_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "rule_id": rule_id,
        "recipient": recipient,
        "kind": kind,
        "occurrence_key": occurrence_key,
        "payload": dict(payload) if payload else {},
        "created_at": now_ms(),
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(__import__("json").dumps(record, ensure_ascii=False) + "\n")
    return record


def list_notifications(*, rule_id: str | None = None, kind: str | None = None) -> list[dict]:
    rows = read_jsonl(_notifications_file())
    if rule_id is not None:
        rows = [r for r in rows if r.get("rule_id") == rule_id]
    if kind is not None:
        rows = [r for r in rows if r.get("kind") == kind]
    return rows


# ── heartbeat ────────────────────────────────────────────────────────


def touch_heartbeat(*, lag_ms: int = 0, error: str = "") -> dict:
    """Record the latest scheduler tick / health beat."""
    record = {
        "last_tick_at": now_ms(),
        "lag_ms": int(lag_ms or 0),
        "error": str(error or "").strip(),
    }
    write_json(_heartbeat_file(), record)
    return record


def get_heartbeat() -> dict:
    return read_json(_heartbeat_file(), {"last_tick_at": 0, "lag_ms": 0, "error": ""})
