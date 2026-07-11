"""Read-only Evolution Packet candidate generator for one task.

Package 4 of the 2026-07-06 production-contract pilot. Produces a
candidate packet only when a recognized trigger fires; otherwise returns
`{"candidates": []}`. **Strictly read-only**: never writes to memory,
flow-memory, skills, or runtime state.

Trigger → source_event mapping (governed by
`docs/templates/EVOLUTION_PACKET_TEMPLATE.md`):

- `latest_authoritative_verdict.outcome == "reject"` → `review_rejected`
- `manager_action_type` non-empty → `manager_action`
- `status == "failed"` (after `report_flow_failure`) → `runtime_incident`
- `loop_cycle_count >= 2` → `repair_cycle_ge2`

When multiple triggers fire for the same task, only the highest-priority
event is emitted (`review_rejected` > `manager_action` >
`runtime_incident` > `repair_cycle_ge2`). This keeps one task → at most
one candidate per call, matching the template's red-line.
"""
from __future__ import annotations

from typing import Any

from eduflow.store import loop_runs, tasks


# Priority order from highest to lowest. Used to deduplicate multiple
# triggers on the same task.
_TRIGGER_PRIORITY = (
    "review_rejected",
    "manager_action",
    "runtime_incident",
    "repair_cycle_ge2",
)


def _detect_triggers(task: dict) -> tuple[str | None, str]:
    """Return (highest_priority_trigger, reason_text)."""
    authoritative = task.get("latest_authoritative_verdict") or {}
    if isinstance(authoritative, dict):
        outcome = str(authoritative.get("outcome") or "").strip().lower()
        if outcome == "reject":
            reason = str(authoritative.get("review_reason") or "").strip() or "review_rejected"
            return "review_rejected", f"review rejected: {reason}"

    manager_action_type = str(task.get("manager_action_type") or "").strip()
    if manager_action_type:
        review_reason = str(task.get("review_reason") or "").strip()
        reason = f"manager_action={manager_action_type}"
        if review_reason:
            reason += f" review_reason={review_reason}"
        return "manager_action", reason

    status = str(task.get("status") or "").strip().lower()
    if status == "failed":
        return "runtime_incident", "task self-reported failure"

    try:
        cycle = int(task.get("loop_cycle_count") or 0)
    except (TypeError, ValueError):
        cycle = 0
    if cycle >= 2:
        return "repair_cycle_ge2", f"loop_cycle_count={cycle}"

    return None, ""


def _build_evidence_refs(task_id: str, task: dict, source_event: str) -> list[str]:
    refs: list[str] = [f"task:{task_id}"]
    if source_event in {"review_rejected", "manager_action"}:
        verdict = task.get("latest_authoritative_verdict") or {}
        if isinstance(verdict, dict):
            target = str(verdict.get("verdict_target") or "").strip()
            if target:
                refs.append(f"verdict_target:{target}")
            reviewer = str(verdict.get("reviewer") or "").strip()
            if reviewer:
                refs.append(f"reviewer:{reviewer}")
            at_ms = int(verdict.get("at_ms") or 0)
            if at_ms:
                refs.append(f"review_at_ms:{at_ms}")
    elif source_event == "repair_cycle_ge2":
        loop_ref = str(task.get("loop_evidence_ref") or "").strip()
        if loop_ref:
            refs.append(loop_ref)
    return refs


def _build_evidence_refs(task_id: str, task: dict, source_event: str) -> list[str]:
    refs: list[str] = [f"task:{task_id}"]
    if source_event in {"review_rejected", "manager_action"}:
        verdict = task.get("latest_authoritative_verdict") or {}
        if isinstance(verdict, dict):
            target = str(verdict.get("verdict_target") or "").strip()
            if target:
                refs.append(f"verdict_target:{target}")
            reviewer = str(verdict.get("reviewer") or "").strip()
            if reviewer:
                refs.append(f"reviewer:{reviewer}")
            at_ms = int(verdict.get("at_ms") or 0)
            if at_ms:
                refs.append(f"review_at_ms:{at_ms}")
    elif source_event == "repair_cycle_ge2":
        loop_ref = str(task.get("loop_evidence_ref") or "").strip()
        if loop_ref:
            refs.append(loop_ref)
        loop_id = _loop_id_from_task(task)
        if loop_id:
            refs.append(f"loop:{loop_id}")
    return refs


def _loop_id_from_task(task: dict) -> str:
    """Resolve loop_id from task fields or loop_evidence_ref path."""
    loop_id = str(task.get("loop_run_id") or "").strip()
    if loop_id:
        return loop_id
    ref = str(task.get("loop_evidence_ref") or "").strip()
    if ref.startswith("loop_runs/") and ref.endswith("/meta.json"):
        return ref[len("loop_runs/"):-len("/meta.json")]
    return ""


def _read_loop_meta(task: dict) -> dict[str, Any] | None:
    """Read loop run meta for the task's loop_id, if available."""
    loop_id = _loop_id_from_task(task)
    if not loop_id:
        return None
    try:
        return loop_runs.get(loop_id)
    except Exception:
        return None


def _recent_failed_commands(loop_meta: dict | None, limit: int = 5) -> list[str]:
    """Collect failed commands from the most recent cycle(s)."""
    if not loop_meta:
        return []
    cycles = loop_meta.get("cycles") or []
    if not cycles:
        return []
    # Take the most recent cycle first
    recent = sorted(cycles, key=lambda c: c.get("cycle", 0), reverse=True)
    failed: list[str] = []
    for cycle in recent:
        for cmd in cycle.get("failed_commands") or []:
            failed.append(str(cmd))
            if len(failed) >= limit:
                return failed
    return failed


def _infer_loop_surface(stop_reason: str, failed_commands: list[str]) -> str:
    """Map loop stop reason + failed commands to an update surface."""
    sr = str(stop_reason or "").lower()
    if "workspace_policy_missing" in sr or "preflight" in sr:
        return "handoff"
    if "same_failure_repeated" in sr or "checker_unavailable" in sr:
        return "loop_spec"
    if "regression_detected" in sr:
        return "workflow_rule"
    if any("preflight" in (cmd or "").lower() for cmd in failed_commands):
        return "handoff"
    if any("checker" in (cmd or "").lower() for cmd in failed_commands):
        return "loop_spec"
    return "no_reuse"


def _build_content(task_id: str, task: dict, source_event: str) -> str:
    """Build the candidate `content` string. ≤ 280 chars, evidence-backed."""
    parts: list[str] = []
    verdict = task.get("latest_authoritative_verdict") or {}
    if source_event == "review_rejected":
        reason = str(verdict.get("review_reason") or task.get("review_reason") or "").strip()
        required = verdict.get("required_fix") or task.get("required_fix") or []
        blocking = verdict.get("blocking_files") or task.get("blocking_files") or []
        parts.append(f"Task {task_id} review rejected (reason={reason or 'n/a'}).")
        if required:
            parts.append(f"required_fix: {'; '.join(str(x) for x in required[:3])}.")
        if blocking:
            parts.append(f"blocking_files: {'; '.join(str(x) for x in blocking[:3])}.")
    elif source_event == "manager_action":
        action_type = str(task.get("manager_action_type") or "").strip()
        reason = str(task.get("review_reason") or "").strip()
        parts.append(f"Task {task_id} blocked on manager_action={action_type or 'n/a'}.")
        if reason:
            parts.append(f"review_reason={reason}.")
    elif source_event == "runtime_incident":
        parts.append(f"Task {task_id} self-reported failure.")
    elif source_event == "repair_cycle_ge2":
        cycle = int(task.get("loop_cycle_count") or 0)
        stop = str(task.get("loop_stop_reason") or "").strip()
        recommended = str(task.get("loop_recommended_action") or "").strip()
        parts.append(f"Task {task_id} entered repair cycle #{cycle}.")
        if stop:
            parts.append(f"loop_stop_reason={stop}.")
        loop_meta = _read_loop_meta(task)
        if loop_meta:
            fingerprint = str(loop_meta.get("latest_failure_fingerprint") or "").strip()
            if fingerprint:
                parts.append(f"fingerprint={fingerprint}.")
            failed = _recent_failed_commands(loop_meta, limit=3)
            if failed:
                parts.append(f"failed={','.join(failed)}.")
        if recommended:
            parts.append(f"recommended: {recommended}.")
    return " ".join(parts)[:280]


def _determine_confidence(source_event: str, task: dict) -> str:
    if source_event == "review_rejected":
        verdict = task.get("latest_authoritative_verdict") or {}
        has_fix = bool(verdict.get("required_fix") or task.get("required_fix"))
        has_blocking = bool(verdict.get("blocking_files") or task.get("blocking_files"))
        if has_fix and has_blocking:
            return "high"
        if has_fix or has_blocking:
            return "medium"
        return "low"
    if source_event in {"manager_action", "runtime_incident"}:
        return "medium"
    if source_event == "repair_cycle_ge2":
        loop_meta = _read_loop_meta(task)
        if loop_meta and loop_meta.get("cycles"):
            return "medium"
        return "low"
    return "low"


def _determine_recommended_action(source_event: str, confidence: str) -> str:
    if confidence == "high":
        return "remember"
    if source_event == "review_rejected":
        return "remember" if confidence in {"high", "medium"} else "review_only"
    return "review_only"


def _determine_kind(source_event: str) -> str:
    if source_event == "manager_action":
        return "agent_skill"
    return "workflow_rule"


def _build_reuse_reason(source_event: str, task: dict, surface: str = "") -> str:
    if source_event == "review_rejected":
        return (
            "When a future review rejects a task in this workflow with "
            "non-empty required_fix + blocking_files, reuse this contract."
        )
    if source_event == "manager_action":
        return (
            "When a future review requests manager_action with this "
            "manager_action_type, surface the same blocking pattern."
        )
    if source_event == "runtime_incident":
        return (
            "When a future task self-reports failure in this workflow, "
            "reuse the same triage contract."
        )
    if source_event == "repair_cycle_ge2":
        surface_txt = surface or "repair"
        return (
            "When a future task in this workflow exceeds loop_cycle_count >= 2, "
            f"reuse the same {surface_txt} pattern."
        )
    return ""


def _build_candidate(
    task_id: str, task: dict, source_event: str, trigger_reason: str
) -> dict[str, Any] | None:
    evidence_refs = _build_evidence_refs(task_id, task, source_event)
    content = _build_content(task_id, task, source_event)
    if not content:
        return None
    workflow_id = str(task.get("workflow_id") or "").strip()
    owner = str(task.get("owner") or task.get("assignee") or "").strip()
    scope = f"workflow:{workflow_id}" if workflow_id else f"agent:{owner}" if owner else ""
    confidence = _determine_confidence(source_event, task)
    candidate: dict[str, Any] = {
        "source_task_id": task_id,
        "source_event": source_event,
        "trigger_reason": trigger_reason,
        "content": content,
        "scope": scope,
        "kind": _determine_kind(source_event),
        "evidence_refs": evidence_refs,
        "reuse_reason": _build_reuse_reason(source_event, task),
        "confidence": confidence,
        "recommended_action": _determine_recommended_action(source_event, confidence),
    }
    if source_event == "repair_cycle_ge2":
        loop_meta = _read_loop_meta(task)
        stop_reason = str(task.get("loop_stop_reason") or "").strip()
        failed_commands = _recent_failed_commands(loop_meta)
        surface = _infer_loop_surface(stop_reason, failed_commands)
        candidate["loop_id"] = _loop_id_from_task(task)
        candidate["cycle_count"] = int(task.get("loop_cycle_count") or 0)
        candidate["loop_status"] = str(task.get("loop_status") or "").strip()
        candidate["stop_reason"] = stop_reason
        candidate["latest_failure_fingerprint"] = (
            str(loop_meta.get("latest_failure_fingerprint") or "").strip()
            if loop_meta else ""
        )
        candidate["recent_failed_commands"] = failed_commands
        candidate["suggested_update_surface"] = surface
        candidate["reuse_reason"] = _build_reuse_reason(
            source_event, task, surface=surface
        )
    return candidate


def build(task_id: str) -> dict[str, list[dict[str, Any]]]:
    """Return Evolution Packet candidates for `task_id`.

    Strictly read-only. Returns `{"candidates": []}` when no trigger fires
    or the task is unknown.
    """
    if not task_id:
        return {"candidates": []}
    task = tasks.get(task_id)
    if task is None:
        return {"candidates": []}
    trigger, reason = _detect_triggers(task)
    if trigger is None:
        return {"candidates": []}
    candidate = _build_candidate(task_id, task, trigger, reason)
    if candidate is None:
        return {"candidates": []}
    return {"candidates": [candidate]}