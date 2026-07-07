"""Read-only Loop Contract render for one task.

Package 2 of the 2026-07-06 production-contract pilot: produce a single
actionable handoff packet from existing task/evidence/loop/delivery state.

**Strictly read-only.** This module never mutates task or inbox state. It
exists so manager-facing surfaces (`task loop-contract`,
`task manager-panel`, future Evolution Packet and Readiness Check) can
share one deterministic contract shape.

All values are derived from existing fields; unknown fields return empty
strings or empty lists (never invented text). The shape is governed by
`docs/templates/LOOP_CONTRACT_TEMPLATE.md`.
"""
from __future__ import annotations

from typing import Any

from eduflow.store import local_facts, tasks


_HIGH_PRIORITIES = frozenset({"高", "high", "urgent", "p0", "p1"})

# Phase derivation: prefer stage when known, else fall back to status.
# Status alone is ambiguous (e.g. `in_progress` covers every stage).
_FALLBACK_PHASE_BY_STATUS = {
    "submitted_for_review": "review_pending",
    "delivered": "delivered",
    "failed": "failed",
    "blocked": "blocked",
    "in_progress": "in_progress",
    "assigned": "assigned",
    "queued": "queued",
    "cancelled": "cancelled",
}


def _normalize_priority(value: str) -> str:
    return str(value or "").strip().lower()


def _is_high_priority(value: str) -> bool:
    return _normalize_priority(value) in _HIGH_PRIORITIES


def _latest_handoff_message(task_id: str) -> dict | None:
    """Return the latest inbox message that handoffs work for this task.

    A "handoff message" is any inbox row carrying `task_id == task_id`
    (regardless of `to`). We pick the most recent such row by created_at.
    """
    candidates: list[dict] = []
    for msg in local_facts.list_all_messages():
        if str(msg.get("task_id") or "") != str(task_id or ""):
            continue
        candidates.append(msg)
    if not candidates:
        return None
    candidates.sort(key=lambda m: int(m.get("created_at") or 0))
    return dict(candidates[-1])


def _derive_current_phase(task: dict) -> str:
    stage = str(task.get("stage") or "").strip()
    status = str(task.get("status") or "").strip()
    if stage and status:
        return f"{stage}_{status}"
    if stage:
        return stage
    return _FALLBACK_PHASE_BY_STATUS.get(status, status)


def _collect_failed_checks(task: dict) -> list[str]:
    out: list[str] = []
    required_fix = task.get("required_fix") or []
    if isinstance(required_fix, list):
        for entry in required_fix:
            text = str(entry or "").strip()
            if text:
                out.append(f"required_fix: {text}")
    elif isinstance(required_fix, str) and required_fix.strip():
        out.append(f"required_fix: {required_fix.strip()}")

    blocking_files = task.get("blocking_files") or []
    if isinstance(blocking_files, list):
        for entry in blocking_files:
            text = str(entry or "").strip()
            if text:
                out.append(f"blocking_files: {text}")
    elif isinstance(blocking_files, str) and blocking_files.strip():
        out.append(f"blocking_files: {blocking_files.strip()}")

    review_reason = str(task.get("review_reason") or "").strip()
    if review_reason:
        out.append(f"review_reason: {review_reason}")

    loop_stop_reason = str(task.get("loop_stop_reason") or "").strip()
    if loop_stop_reason:
        out.append(f"loop_stop_reason: {loop_stop_reason}")

    return out


def _collect_allowed_actions(task: dict) -> list[str]:
    out: list[str] = []
    recommended = str(task.get("loop_recommended_action") or "").strip()
    if recommended:
        out.append(recommended)
    return out


def _collect_evidence_refs(task_id: str, task: dict) -> list[str]:
    out: list[str] = [f"task:{task_id}"]
    loop_ref = str(task.get("loop_evidence_ref") or "").strip()
    if loop_ref:
        out.append(loop_ref)
    return out


def _derive_next_required_output(task: dict) -> str:
    stage = str(task.get("stage") or "").strip()
    status = str(task.get("status") or "").strip()
    verdict = str(task.get("verdict") or "").strip()
    manager_action = str(task.get("manager_action_type") or "").strip()
    loop_status = str(task.get("loop_status") or "").strip()
    if manager_action:
        return f"manager_action: {manager_action}"
    if verdict == "rejected" or status == "blocked":
        return "repair iteration"
    if status == "submitted_for_review":
        return "review verdict"
    if status == "delivered" and verdict == "approved":
        return "manager closeout"
    if loop_status in {"repair_needed", "failed"}:
        return "repair iteration"
    if status == "failed":
        return "runtime incident triage"
    if stage:
        return f"advance {stage} from {status or 'queued'}"
    return ""


def _build_delivery(task_id: str) -> dict[str, Any]:
    handoff = _latest_handoff_message(task_id)
    if handoff is None:
        return {
            "state": "",
            "inbox_local_id": "",
            "ack_required": False,
            "ack_state": "",
            "ack_deadline": "",
        }
    priority = str(handoff.get("priority") or "")
    return {
        "state": str(handoff.get("delivery_state") or ""),
        "inbox_local_id": str(handoff.get("local_id") or ""),
        "ack_required": _is_high_priority(priority),
        "ack_state": str(handoff.get("ack_state") or ""),
        "ack_deadline": "",
    }


def build(task_id: str) -> dict | None:
    """Render the Loop Contract for `task_id`, or `None` if the task is unknown.

    Strictly read-only. Does not mutate task or inbox state.
    """
    if not task_id:
        return None
    task = tasks.get(task_id)
    if task is None:
        return None
    return {
        "task_id": task_id,
        "workflow_id": str(task.get("workflow_id") or ""),
        "current_phase": _derive_current_phase(task),
        "owner": str(task.get("owner") or task.get("assignee") or ""),
        "iteration": int(task.get("loop_cycle_count") or 0),
        "delivery": _build_delivery(task_id),
        "passed_checks": [],
        "failed_checks": _collect_failed_checks(task),
        "allowed_actions": _collect_allowed_actions(task),
        "forbidden_actions": [],
        "next_required_output": _derive_next_required_output(task),
        "evidence_refs": _collect_evidence_refs(task_id, task),
    }