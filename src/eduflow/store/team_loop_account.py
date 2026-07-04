"""Read model for workflow-backed team loop state."""
from __future__ import annotations

from eduflow.store import tasks


def _reject_cycle_count(events: list[dict]) -> int:
    count = 0
    for event in events:
        after = event.get("after") or {}
        before = event.get("before") or {}
        if after.get("verdict") == "rejected" and before.get("verdict") != "rejected":
            count += 1
    return count


def build(task_id: str) -> dict:
    task = tasks.get(task_id) or {}
    if not task or task.get("schema_version") != 2:
        return {}
    events = tasks.list_task_events(task_id=task_id, limit=1000)
    workflow_id = str(task.get("workflow_id") or "")
    status = str(task.get("status") or "")
    verdict = str(task.get("verdict") or "")
    owner = str(task.get("owner") or task.get("assignee") or "")
    reviewer = str(task.get("reviewer") or "")
    loop_status = str(task.get("loop_status") or "")
    closeout = str(task.get("closeout_status") or "")

    phase = "protocol_missing"
    current_owner = owner
    next_owner = owner
    last_gate = ""
    loop_health = "unknown"
    stuck_reason = ""
    recommended_action = ""

    if workflow_id:
        if closeout == "closeout_completed":
            phase = "closed"
            current_owner = "manager"
            next_owner = ""
            last_gate = "manager_closeout"
            loop_health = "closed"
            recommended_action = "no_action"
        elif status == "delivered" and verdict == "approved":
            phase = "manager_closeout_ready"
            current_owner = "manager"
            next_owner = "manager"
            last_gate = "review_verdict_authority_gate"
            loop_health = "ready"
            recommended_action = "manager_formal_closeout"
        elif verdict == "rejected":
            phase = "team_repair_needed"
            current_owner = owner
            next_owner = owner
            last_gate = "review_verdict_authority_gate"
            loop_health = "repairing"
            recommended_action = "send_repair_handoff"
        elif loop_status in {"repair_needed", "stopped", "failed"}:
            phase = "member_loop_repair"
            current_owner = owner
            next_owner = owner
            last_gate = "agent_loop"
            loop_health = "repairing"
            recommended_action = str(task.get("loop_recommended_action") or "send_repair_handoff")
        elif status == "submitted_for_review":
            phase = "reviewing"
            current_owner = reviewer or "reviewer"
            next_owner = reviewer or "reviewer"
            last_gate = "review_verdict_authority_gate"
            loop_health = "reviewing"
            recommended_action = "await_review_verdict"
        elif status in {"assigned", "in_progress"}:
            phase = "member_execution"
            current_owner = owner
            next_owner = owner
            loop_health = "running"
            recommended_action = "await_member_update"
        elif status == "queued":
            phase = "dispatching"
            current_owner = "manager"
            next_owner = owner
            loop_health = "starting"
            recommended_action = "send_task_handoff"
        else:
            phase = "stale_or_stuck"
            stuck_reason = f"unhandled_status:{status}"
            loop_health = "stuck"
            recommended_action = "inspect_task_events"

    return {
        "task_id": task_id,
        "workflow_id": workflow_id,
        "phase": phase,
        "cycle_count": _reject_cycle_count(events),
        "current_owner": current_owner,
        "next_owner": next_owner,
        "last_gate": last_gate,
        "last_review_reason": str(task.get("review_reason") or ""),
        "loop_health": loop_health,
        "stuck_reason": stuck_reason,
        "recommended_action": recommended_action,
        "self_check_status": str(task.get("self_check_status") or ""),
        "review_check_status": str(task.get("review_check_status") or ""),
        "manager_closeout_status": str(task.get("manager_closeout_status") or ""),
        "agent_loop": {
            "run_id": str(task.get("loop_run_id") or ""),
            "status": loop_status,
        },
    }
