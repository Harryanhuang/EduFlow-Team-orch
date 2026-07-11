"""Deterministic manager/user/worker operations for D scheduled tasks.

All writes are explicit and role-checked.  Natural language cannot mutate
store directly; callers must invoke these functions or the `task schedule`
CLI.  D lanes never create user-visible T tasks.
"""
from __future__ import annotations

from eduflow.store import scheduled_tasks
from eduflow.util import now_ms


VALID_ROLES = frozenset({"user", "manager", "worker"})


class AuthorizationError(Exception):
    """Raised when an actor/role is not authorized for an operation."""


class _NotFound(scheduled_tasks.NotFound):
    """Re-export store NotFound so callers can catch a single module."""


NotFound = scheduled_tasks.NotFound


def _require_role(actor_role: str, allowed: set[str]) -> None:
    if actor_role not in VALID_ROLES:
        raise AuthorizationError(f"invalid role: {actor_role}")
    if actor_role not in allowed:
        raise AuthorizationError(
            f"role {actor_role} not authorized for this operation "
            f"(allowed: {sorted(allowed)})"
        )


def _is_rule_owner(rule: dict, actor: str) -> bool:
    return rule.get("created_by") == actor


def _require_manager_or_owner(rule: dict, actor: str, actor_role: str) -> None:
    if actor_role == "manager":
        return
    if actor_role == "user" and _is_rule_owner(rule, actor):
        return
    raise AuthorizationError("user can only manage their own rules")


# ── user rule lifecycle ────────────────────────────────────────────────


def create_draft_rule(
    *,
    target: str,
    artifact: str,
    frequency: str,
    timezone: str,
    next_due_utc: str,
    capacity: int = 1,
    workflow_state: dict | None = None,
    created_by: str = "",
) -> str:
    """Persist a new D rule in `draft` status."""
    return scheduled_tasks.create_rule(
        target=target,
        artifact=artifact,
        frequency=frequency,
        timezone=timezone,
        next_due_utc=next_due_utc,
        capacity=capacity,
        workflow_state=workflow_state,
        created_by=created_by,
        status="draft",
    )


def confirm_draft_rule(
    rule_id: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    """Confirm a draft rule and bind the actor + version."""
    _require_role(actor_role, {"user", "manager"})
    rule = scheduled_tasks.get_rule(rule_id)
    if rule is None:
        raise NotFound(f"rule {rule_id} not found")
    _require_manager_or_owner(rule, actor, actor_role)
    if rule.get("status") != "draft":
        raise ValueError(f"rule {rule_id} is not draft (status={rule.get('status')})")
    version = expected_version if expected_version is not None else rule["version"]
    extra = {
        "confirmed_by": actor,
        "confirmed_at": now_ms(),
    }
    return scheduled_tasks._transition_rule_status(
        rule_id, version, "active", extra_context=extra
    )


def pause_rule(
    rule_id: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    _require_role(actor_role, {"user", "manager"})
    rule = scheduled_tasks.get_rule(rule_id)
    if rule is None:
        raise NotFound(f"rule {rule_id} not found")
    _require_manager_or_owner(rule, actor, actor_role)
    version = expected_version if expected_version is not None else rule["version"]
    return scheduled_tasks.pause_rule(rule_id, expected_version=version)


def resume_rule(
    rule_id: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    _require_role(actor_role, {"user", "manager"})
    rule = scheduled_tasks.get_rule(rule_id)
    if rule is None:
        raise NotFound(f"rule {rule_id} not found")
    _require_manager_or_owner(rule, actor, actor_role)
    version = expected_version if expected_version is not None else rule["version"]
    return scheduled_tasks.resume_rule(rule_id, expected_version=version)


def cancel_rule(
    rule_id: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    _require_role(actor_role, {"user", "manager"})
    rule = scheduled_tasks.get_rule(rule_id)
    if rule is None:
        raise NotFound(f"rule {rule_id} not found")
    _require_manager_or_owner(rule, actor, actor_role)
    version = expected_version if expected_version is not None else rule["version"]
    return scheduled_tasks.cancel_rule(rule_id, expected_version=version)


# ── manager occurrence operations ──────────────────────────────────────


def confirm_occurrence(
    occurrence_key: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    """Manager confirms an awaiting occurrence; binds rule version + key."""
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    if occ.get("status") != "awaiting_manager":
        raise ValueError(
            f"occurrence {occurrence_key} cannot be confirmed (status={occ.get('status')})"
        )
    rule = scheduled_tasks.get_rule(occ["rule_id"])
    if rule is None:
        raise NotFound(f"rule {occ['rule_id']} not found")
    version = expected_version if expected_version is not None else occ.get("version", 1)
    changes = {
        "status": "confirmed",
        "confirmed_by": actor,
        "confirmed_at": now_ms(),
        "confirmed_rule_version": rule["version"],
    }
    return scheduled_tasks.update_occurrence(occurrence_key, changes, expected_version=version)


def choose_lane(
    occurrence_key: str,
    *,
    agent: str,
    dependencies: list[str] | None = None,
    inputs: dict | None = None,
    artifacts: list[str] | None = None,
    evidence: dict | None = None,
    actor: str,
    actor_role: str,
) -> dict:
    """Manager records a single lane snapshot for an occurrence."""
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    lane_id = scheduled_tasks.create_lane(
        occurrence_key=occurrence_key,
        agent=agent,
        dependencies=dependencies,
        inputs=inputs,
        artifacts=artifacts,
        evidence=evidence,
    )
    return scheduled_tasks.get_lane(lane_id)


def choose_lanes(
    occurrence_key: str,
    *,
    lanes: list[dict],
    mode: str = "parallel",
    actor: str,
    actor_role: str,
) -> list[dict]:
    """Manager records multiple lanes; serial mode chains dependencies.

    `lanes` is a list of dicts with keys: agent, dependencies, inputs,
    artifacts, evidence.
    """
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    if mode not in {"serial", "parallel"}:
        raise ValueError(f"invalid lane mode: {mode!r} (use serial|parallel)")
    created: list[dict] = []
    previous_lane_id: str | None = None
    for spec in lanes:
        deps = list(spec.get("dependencies") or [])
        if mode == "serial" and previous_lane_id is not None:
            deps.append(previous_lane_id)
        lane_id = scheduled_tasks.create_lane(
            occurrence_key=occurrence_key,
            agent=spec["agent"],
            dependencies=deps,
            inputs=spec.get("inputs"),
            artifacts=spec.get("artifacts"),
            evidence=spec.get("evidence"),
        )
        created.append(scheduled_tasks.get_lane(lane_id))
        previous_lane_id = lane_id
    return created


def skip_occurrence(
    occurrence_key: str,
    *,
    actor: str,
    actor_role: str,
    reason: str = "",
    expected_version: int | None = None,
) -> dict:
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    version = expected_version if expected_version is not None else occ.get("version", 1)
    changes = {
        "status": "skipped",
        "skipped_by": actor,
        "skipped_reason": reason,
        "skipped_at": now_ms(),
    }
    return scheduled_tasks.update_occurrence(occurrence_key, changes, expected_version=version)


def re_dispatch(
    occurrence_key: str,
    *,
    actor: str,
    actor_role: str,
    expected_version: int | None = None,
) -> dict:
    """Manager dispatches a confirmed occurrence.

    Before dispatch the active rule state is re-read.  If the rule is
    cancelled or paused, cancel wins and the occurrence is marked cancelled
    without creating any user-visible T task.
    """
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    rule = scheduled_tasks.get_rule(occ["rule_id"])
    if rule is None:
        raise NotFound(f"rule {occ['rule_id']} not found")
    version = expected_version if expected_version is not None else occ.get("version", 1)

    if rule.get("status") in ("cancelled", "paused"):
        changes = {
            "status": "cancelled",
            "cancelled_by": actor,
            "cancelled_reason": "rule_cancelled_or_paused",
            "cancelled_at": now_ms(),
        }
        updated = scheduled_tasks.update_occurrence(
            occurrence_key, changes, expected_version=version
        )
        return {
            "dispatched": False,
            "reason": "rule_cancelled_or_paused",
            "occurrence": updated,
        }

    if rule.get("status") != "active":
        return {
            "dispatched": False,
            "reason": f"rule_status_{rule.get('status')}",
            "occurrence": occ,
        }

    changes = {
        "status": "running",
        "dispatched_by": actor,
        "dispatched_at": now_ms(),
        "dispatched_rule_version": rule["version"],
    }
    updated = scheduled_tasks.update_occurrence(
        occurrence_key, changes, expected_version=version
    )
    return {
        "dispatched": True,
        "occurrence": updated,
        "lanes": scheduled_tasks.list_lanes(occurrence_key=occurrence_key),
    }


def fail_pause_occurrence(
    occurrence_key: str,
    *,
    actor: str,
    actor_role: str,
    reason: str = "",
    expected_version: int | None = None,
) -> dict:
    _require_role(actor_role, {"manager"})
    occ = scheduled_tasks.get_occurrence(occurrence_key)
    if occ is None:
        raise NotFound(f"occurrence {occurrence_key} not found")
    rule = scheduled_tasks.get_rule(occ["rule_id"])
    if rule is None:
        raise NotFound(f"rule {occ['rule_id']} not found")
    version = expected_version if expected_version is not None else occ.get("version", 1)
    changes = {
        "status": "failed",
        "failure_reason": reason,
        "failed_by": actor,
        "failed_at": now_ms(),
    }
    updated = scheduled_tasks.update_occurrence(
        occurrence_key, changes, expected_version=version
    )
    if rule.get("status") != "cancelled":
        scheduled_tasks._transition_rule_status(
            rule["id"], rule["version"], "attention_required"
        )
    return updated


# ── worker report-back ─────────────────────────────────────────────────


def report_back(
    occurrence_key: str,
    lane_id: str,
    *,
    status: str,
    evidence: dict,
    actor: str,
    actor_role: str,
) -> dict:
    """Worker updates lane status and evidence only."""
    _require_role(actor_role, {"worker"})
    lane = scheduled_tasks.get_lane(lane_id)
    if lane is None:
        raise NotFound(f"lane {lane_id} not found")
    if lane.get("occurrence_key") != occurrence_key:
        raise ValueError(
            f"lane {lane_id} does not belong to occurrence {occurrence_key}"
        )
    changes = {
        "status": status,
        "evidence": dict(evidence),
        "reported_by": actor,
        "reported_at": now_ms(),
    }
    return scheduled_tasks.update_lane(
        lane_id, changes, expected_version=lane.get("version")
    )
