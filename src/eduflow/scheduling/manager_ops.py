"""Deterministic manager/user/worker operations for D scheduled tasks.

All writes are explicit and role-checked.  Natural language cannot mutate
store directly; callers must invoke these functions or the `task schedule`
CLI.  D lanes never create user-visible T tasks.

P7 also routes decision-grade summaries through ``memory_bridge`` at
exactly four moments:
  * confirm_draft_rule       -> rule_summary
  * re_dispatch (success)    -> workflow_start
  * skip_occurrence          -> workflow_stop
  * fail_pause_occurrence    -> major_failure + workflow_stop
Routine events (tick / reminder / wait) NEVER write to memory.
Memory subsystem failure is fully absorbed by memory_bridge — the
return-value contract is "always succeed or return None", so the
scheduler keeps running.
"""
from __future__ import annotations

from eduflow.scheduling import memory_bridge
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
    updated = scheduled_tasks._transition_rule_status(
        rule_id, version, "active", extra_context=extra
    )
    # P7: decision-grade rule summary.  Memory outage is absorbed by
    # memory_bridge and must not affect the return value.
    summary_parts = [
        f"D rule {rule_id} confirmed: target={updated.get('target','')!r}",
        f"frequency={updated.get('frequency','')}",
        f"timezone={updated.get('timezone','')}",
        f"artifact={updated.get('artifact','')!r}",
        f"capacity={updated.get('capacity',1)}",
    ]
    memory_bridge.record_rule_summary(
        rule_id,
        content="; ".join(summary_parts),
        metadata={
            "confirmed_by": actor,
            "status": "active",
            "version": updated.get("version", 1),
        },
    )
    return updated


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
    lane = scheduled_tasks.get_lane(lane_id)
    if lane is None:
        raise NotFound(f"lane {lane_id} not found after creation")
    return lane


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
        lane = scheduled_tasks.get_lane(lane_id)
        if lane is None:
            raise NotFound(f"lane {lane_id} not found after creation")
        created.append(lane)
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
    updated = scheduled_tasks.update_occurrence(occurrence_key, changes, expected_version=version)
    # P7: skip is a soft workflow stop — not a major failure.
    memory_bridge.record_workflow_stop(
        occ["rule_id"],
        occurrence_key,
        content=(
            f"D occurrence {occurrence_key} skipped by {actor}: {reason}"
        ),
        metadata={"reason": reason, "actor": actor, "kind": "skip"},
    )
    return updated


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
        # P7: cancel-before-dispatch is also a workflow stop.
        memory_bridge.record_workflow_stop(
            rule["id"],
            occurrence_key,
            content=(
                f"D occurrence {occurrence_key} cancelled before dispatch: "
                f"rule_status={rule.get('status')}"
            ),
            metadata={"reason": "rule_cancelled_or_paused", "actor": actor},
        )
        return {
            "dispatched": False,
            "reason": "rule_cancelled_or_paused",
            "occurrence": updated,
        }

    if rule.get("status") != "active":
        # P7: non-active rule still ends the workflow attempt.
        memory_bridge.record_workflow_stop(
            rule["id"],
            occurrence_key,
            content=(
                f"D occurrence {occurrence_key} not dispatched: "
                f"rule_status={rule.get('status')}"
            ),
            metadata={"reason": f"rule_status_{rule.get('status')}"},
        )
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
    # P7: decision-grade workflow start summary.
    memory_bridge.record_workflow_start(
        rule["id"],
        occurrence_key,
        content=(
            f"D occurrence {occurrence_key} dispatched by {actor} "
            f"(rule {rule['id']} v{rule['version']})"
        ),
        metadata={"dispatched_by": actor},
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
    # P7: major_failure + workflow_stop summaries.
    failure_content = (
        f"D occurrence {occurrence_key} marked failed by {actor}: {reason}"
    )
    memory_bridge.record_major_failure(
        rule["id"],
        occurrence_key,
        content=failure_content,
        metadata={"reason": reason, "failed_by": actor},
    )
    memory_bridge.record_workflow_stop(
        rule["id"],
        occurrence_key,
        content=failure_content,
        metadata={"reason": reason, "actor": actor, "kind": "failure"},
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
