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

import time

from eduflow.runtime import paths
from eduflow.util import flock, now_ms, read_json, read_jsonl, write_json


VALID_FREQUENCIES = frozenset({"once", "daily", "weekly"})
VALID_RULE_STATUSES = frozenset({"draft", "active", "paused", "cancelled", "attention_required"})
VALID_OCCURRENCE_STATUSES = frozenset({
    "awaiting_manager",
    "confirmed",
    "running",
    "blocked",
    "skipped",
    "done",
    "failed",
    "cancelled",
})

# Allowed rule status transitions.  Empty set means terminal.
RULE_TRANSITIONS = {
    "draft": {"active", "cancelled"},
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
    created_by: str = "",
    status: str = "active",
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
        "status": _validate_rule_status(status),
        "capacity": int(capacity or 1),
        "workflow_state": dict(workflow_state) if workflow_state else {},
        "created_by": str(created_by or "").strip(),
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


def _transition_rule_status(rule_id: str, expected_version: int, new_status: str, *, extra_context: dict | None = None) -> dict:
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
            if extra_context:
                rule.update(extra_context)
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
        if extra_context:
            rule.update(extra_context)
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
            "version": 1,
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
    lane_id = f"{occurrence_key}:lane:{now_ms()}:{time.time_ns()}"
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


def update_lane(
    lane_id: str,
    changes: dict,
    *,
    expected_version: int | None = None,
) -> dict:
    """CAS update of a lane.  `changes` may not touch id/occurrence_key/created_at."""
    forbidden = {"id", "occurrence_key", "created_at"}
    if forbidden & set(changes):
        raise ValueError(f"cannot mutate protected fields: {sorted(forbidden & set(changes))}")
    with _lanes_lock():
        data = _load_lanes()
        lane = _find_lane(data, lane_id)
        if lane is None:
            raise NotFound(f"lane {lane_id} not found")
        if expected_version is not None and lane.get("version") != expected_version:
            raise VersionConflict(
                f"lane {lane_id} version {lane.get('version')} != expected {expected_version}"
            )
        for key_name, value in changes.items():
            lane[key_name] = value
        lane["version"] = (expected_version or lane.get("version", 0)) + 1
        lane["updated_at"] = now_ms()
        _save_lanes(data)
        return dict(lane)


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


# ── retention / archival (P7) ────────────────────────────────────────
#
# The scheduler store is the single source of truth.  After a configured
# retention window (default 90 days), full per-occurrence / lane /
# notification audit is summarised and the raw rows are deleted.  Active
# or unfinished references (awaiting_manager / running / confirmed /
# blocked) MUST stay in the active store regardless of age.
#
# Retention is configurable and supports a dry-run mode that returns the
# list of candidates without mutating state.


# Default retention window in days.  Configurable per call.
DEFAULT_RETENTION_DAYS = 90

# Occurrence statuses that count as "active / unfinished" — these
# rows MUST NEVER be archived regardless of age.
ACTIVE_STATUSES = frozenset({
    "awaiting_manager",
    "running",
    "confirmed",
    "blocked",
})


def _retention_window_ms(retention_days: int | None) -> int:
    days = retention_days if retention_days is not None else DEFAULT_RETENTION_DAYS
    if days < 0:
        raise ValueError(f"retention_days must be >= 0, got {days}")
    return int(days) * 24 * 60 * 60 * 1000


def retention_cutoff_ms(now_ms: int, retention_days: int | None = None) -> int:
    """Compute the cutoff timestamp (epoch ms) for retention.

    `retention_days=None` uses the 90-day default.  Rows with
    created_at < cutoff are eligible for archival (subject to the
    active-status guard).
    """
    return now_ms - _retention_window_ms(retention_days)


def find_archival_candidates(*, cutoff_ms: int) -> dict:
    """Return lists of occurrence / lane / notification rows older than
    `cutoff_ms` that are eligible for archival.

    Active / unfinished occurrences (awaiting_manager / running /
    confirmed / blocked) are NEVER eligible — they stay in the active
    store so the scheduler can keep tracking them.

    Lanes are eligible only when their bound occurrence is also
    eligible (so active lanes tied to an active occurrence remain
    intact).  Notifications follow the same rule: a notification row
    whose occurrence_key points at an active occurrence is kept.

    Returns a dict with three keys: ``occurrences``, ``lanes``,
    ``notifications`` — each a list of the underlying row dicts.
    """
    data = _load_occurrences()
    all_occ = list(data.get("occurrences", []))
    eligible_occ = []
    active_keys: set[str] = set()
    for occ in all_occ:
        if occ.get("status") in ACTIVE_STATUSES:
            active_keys.add(occ.get("id", ""))
            continue
        created_at = int(occ.get("created_at") or 0)
        if created_at and created_at < cutoff_ms:
            eligible_occ.append(dict(occ))

    # Lanes: only those whose occurrence is eligible (not active).
    lane_data = _load_lanes()
    all_lanes = list(lane_data.get("lanes", []))
    eligible_lane_occurrence_keys = {o["id"] for o in eligible_occ}
    eligible_lanes = [
        dict(l) for l in all_lanes
        if l.get("occurrence_key") in eligible_lane_occurrence_keys
    ]

    # Notifications: eligible when older than cutoff AND bound occurrence
    # is not active (i.e. it's in the eligible list).
    all_notifications = read_jsonl(_notifications_file())
    eligible_notifications = []
    for row in all_notifications:
        occ_key = row.get("occurrence_key") or ""
        if occ_key in active_keys:
            continue  # active occurrence — keep notification
        ts = int(row.get("created_at") or 0)
        if ts and ts < cutoff_ms:
            eligible_notifications.append(dict(row))

    return {
        "occurrences": eligible_occ,
        "lanes": eligible_lanes,
        "notifications": eligible_notifications,
    }


def _summarise_occurrence(occ: dict) -> tuple[str, list[str]]:
    """Build a compact summary string + evidence refs for an archived
    occurrence.  Strips noisy detail (context, lane agent lists) while
    keeping enough to reconstruct what happened.
    """
    rule_id = str(occ.get("rule_id") or "")
    occ_key = str(occ.get("id") or "")
    status = str(occ.get("status") or "")
    scheduled_at = str(occ.get("scheduled_at_utc") or "")
    version = occ.get("version", 1)
    parts = [
        f"D occurrence {occ_key}",
        f"rule={rule_id}",
        f"status={status}",
        f"scheduled_at_utc={scheduled_at}",
        f"version={version}",
    ]
    summary = "; ".join(parts)
    evidence = [
        f"scheduler:rule:{rule_id}",
        f"occurrence:{occ_key}",
        f"scheduled_at_utc:{scheduled_at}",
        f"status:{status}",
    ]
    return summary, evidence


def archive_old_records(
    *,
    cutoff_ms: int,
    dry_run: bool = False,
) -> dict:
    """Archive old occurrence / lane / notification rows.

    Behaviour:
      * Eligible rows are listed by ``find_archival_candidates``.
      * In ``dry_run=True`` mode, the store is NOT mutated; only the
        candidate list is returned.
      * In ``dry_run=False`` mode, eligible occurrence rows are
        rewritten in place — the noisy ``context`` field is replaced
        by a compact ``summary`` string, ``archived=True`` /
        ``archived_at`` markers are added, and ``evidence_refs``
        stores the keys needed to reconstruct from the active store.
      * Eligible lane rows are removed (their summary lives inside the
        archived occurrence row).
      * Eligible notification rows are removed from the JSONL ledger.

    Active / unfinished occurrences are NEVER touched.
    """
    candidates = find_archival_candidates(cutoff_ms=cutoff_ms)
    result = {
        "dry_run": bool(dry_run),
        "cutoff_ms": int(cutoff_ms),
        "candidates": candidates,
        "archived_occurrences": [],
        "removed_lanes": [],
        "removed_notifications": 0,
    }
    if dry_run:
        return result

    archived_at = now_ms()
    eligible_occ_ids = {o["id"] for o in candidates["occurrences"]}

    # ── occurrence rows: rewrite in place, preserving id and
    # ── rule_id so the active store can still reference them.
    if eligible_occ_ids:
        with _occurrences_lock():
            data = _load_occurrences()
            touched: list[dict] = []
            for occ in data.get("occurrences", []):
                if occ.get("id") not in eligible_occ_ids:
                    continue
                summary_text, evidence_refs = _summarise_occurrence(occ)
                occ["summary"] = summary_text
                occ["evidence_refs"] = evidence_refs
                occ["archived"] = True
                occ["archived_at"] = archived_at
                # Strip noisy context but keep rule_id / id / status.
                occ.pop("context", None)
                occ.pop("confirmations", None)
                occ.pop("dispatched_by", None)
                occ.pop("skipped_by", None)
                occ.pop("skipped_reason", None)
                occ.pop("skipped_at", None)
                occ.pop("cancelled_by", None)
                occ.pop("cancelled_reason", None)
                occ.pop("cancelled_at", None)
                occ.pop("confirmed_by", None)
                occ.pop("confirmed_at", None)
                occ.pop("confirmed_rule_version", None)
                occ.pop("dispatched_at", None)
                occ.pop("dispatched_rule_version", None)
                occ.pop("failed_by", None)
                occ.pop("failed_at", None)
                occ.pop("failure_reason", None)
                touched.append(dict(occ))
            if touched:
                _save_occurrences(data)
                result["archived_occurrences"] = touched

    # ── lane rows: remove (info summarised inside archived occurrence).
    if candidates["lanes"]:
        eligible_lane_ids = {l["id"] for l in candidates["lanes"]}
        with _lanes_lock():
            data = _load_lanes()
            before = len(data.get("lanes", []))
            data["lanes"] = [
                l for l in data.get("lanes", [])
                if l.get("id") not in eligible_lane_ids
            ]
            after = len(data["lanes"])
            if before != after:
                _save_lanes(data)
                result["removed_lanes"] = [
                    l for l in candidates["lanes"] if l.get("id") in eligible_lane_ids
                ]

    # ── notification rows: rewrite the JSONL excluding eligible rows.
    eligible_notif_keys = {
        (
            str(n.get("rule_id") or ""),
            str(n.get("recipient") or ""),
            str(n.get("kind") or ""),
            str(n.get("created_at") or ""),
        )
        for n in candidates["notifications"]
    }
    if candidates["notifications"]:
        path = _notifications_file()
        if path.exists():
            import json as _json
            kept_lines: list[str] = []
            removed = 0
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = _json.loads(line)
                except Exception:
                    kept_lines.append(line)
                    continue
                key = (
                    str(obj.get("rule_id") or ""),
                    str(obj.get("recipient") or ""),
                    str(obj.get("kind") or ""),
                    str(obj.get("created_at") or ""),
                )
                if key in eligible_notif_keys:
                    removed += 1
                    continue
                kept_lines.append(line)
            if removed:
                path.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")
                result["removed_notifications"] = removed

    return result
