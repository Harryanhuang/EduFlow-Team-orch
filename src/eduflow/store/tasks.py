"""Local task store — coordination cards across agents.

One JSON file (`$EDUFLOW_STATE_DIR/tasks.json`) with shape:
    {"tasks": [...], "_meta": {"last_id": N}}

Each task:
    {id, title, description, assignee, creator,
     status, created_at, updated_at, completed_at}

Pure file-locked CRUD; lifecycle (assignment, completion, etc.) is whatever
the agents agree on — the store is opinion-free.

Legacy status vocabulary: 待处理 / 进行中 / 已完成 / 已取消

Flow-task vocabulary (schema_version=2):
  status: queued / assigned / in_progress / blocked /
          submitted_for_review / delivered / cancelled
  verdict: pending / approved / rejected / manager_action
"""
from __future__ import annotations

import hashlib
import json
import re
from uuid import uuid4
from pathlib import Path

from eduflow.runtime import paths
from eduflow.store import task_evidence_account
from eduflow.util import atomic_write_text, flock, now_ms, read_json, read_jsonl, write_json


VALID_STATUSES = {"待处理", "进行中", "已完成", "已取消"}

VALID_WORKSPACE_MODES = frozenset({
    "shared", "worktree", "container", "external_artifact",
})
DEFAULT_STATUS = "待处理"
TERMINAL_STATUSES = {"已完成", "已取消"}

FLOW_STAGE_ALIASES = {
    "course": "curriculum",
}
FLOW_STAGES = frozenset({"curriculum", "review", "qbank", "builder", "admissions", "school"})
FLOW_STATUSES = frozenset({
    "queued",
    "assigned",
    "in_progress",
    "blocked",
    "submitted_for_review",
    "delivered",
    "cancelled",
    # `failed` is a worker/reviewer self-reported terminal state. Unlike
    # `cancelled` (manager-only termination) and `delivered` (formal
    # completion with a review verdict), `failed` means "the worker
    # itself hit an unrecoverable error and is asking for help". It
    # always carries a `failure_reason` and always fires the memory
    # event_bridge so the failure becomes a candidate.
    # Allowed transitions OUT of `failed`:
    #   - failed -> cancelled (manager gives up on it)
    #   - failed -> in_progress (manager retries after worker recovery)
    # Allowed transitions INTO `failed`:
    #   - from assigned / in_progress / blocked / submitted_for_review
    #     by the worker or reviewer (any actor responsible for execution)
    "failed",
})
FLOW_TERMINAL_STATUSES = frozenset({"delivered", "cancelled", "failed"})
FLOW_VERDICTS = frozenset({"pending", "approved", "rejected", "manager_action"})
# T-104: statuses eligible for physical archive. Terminal, boss-visible
# "done" states only — `failed` is deliberately excluded (it usually still
# wants manager attention, not silent filing). Covers both flow (delivered/
# cancelled) and legacy (已完成/已取消) task vocabularies.
ARCHIVABLE_STATUSES = frozenset({"delivered", "cancelled", "已完成", "已取消"})
LOOP_STATUSES = frozenset({
    "running",
    "checking",
    "repair_needed",
    "passed",
    "stopped",
    "failed",
})
CHECK_SUMMARY_STATUSES = frozenset({"", "pending", "passed", "failed", "blocked"})
CLOSEOUT_TIER_STATUSES = frozenset({
    "unit_seed_ready",
    "unit_package_ready",
    "subject_sample_ready",
    "qbank_agent_ready",
    "closeout_completed",
})
FLOW_ALLOWED_STAGE_STATUSES = {
    "curriculum": frozenset({"queued", "assigned", "in_progress", "blocked", "submitted_for_review", "delivered", "cancelled", "failed"}),
    "review": frozenset({"queued", "assigned", "in_progress", "blocked", "delivered", "cancelled", "failed"}),
    # QBank stage intentionally omits submitted_for_review — QBank verification is
    # external (scripts/qbank_verify.py), not internally flow-reviewed. The dedup
    # gate uses review_course_pass (a boolean derived from verification output),
    # not a flow reviewer verdict. See dedup_import_gate() and qbank_lifecycle_status().
    "qbank": frozenset({"queued", "assigned", "in_progress", "blocked", "delivered", "cancelled", "failed"}),
    "builder": frozenset({"queued", "assigned", "in_progress", "blocked", "delivered", "cancelled", "failed"}),
    "admissions": frozenset({"queued", "assigned", "in_progress", "blocked", "submitted_for_review", "delivered", "cancelled", "failed"}),
    "school": frozenset({"queued", "assigned", "in_progress", "blocked", "submitted_for_review", "delivered", "cancelled", "failed"}),
}
FLOW_TRANSITIONS = {
    "queued": {
        "assigned": frozenset({"manager"}),
        "cancelled": frozenset({"manager"}),
    },
    "assigned": {
        "in_progress": frozenset({"worker"}),
        "blocked": frozenset({"worker"}),
        "cancelled": frozenset({"manager"}),
        # worker self-reports an unrecoverable error before starting work
        "failed": frozenset({"worker"}),
    },
    "in_progress": {
        "blocked": frozenset({"worker"}),
        "submitted_for_review": frozenset({"worker"}),
        "delivered": frozenset({"worker", "manager"}),
        "cancelled": frozenset({"manager"}),
        # worker self-reports an unrecoverable error mid-execution
        "failed": frozenset({"worker", "reviewer"}),
    },
    "blocked": {
        "assigned": frozenset({"manager"}),
        "in_progress": frozenset({"manager", "worker"}),
        "cancelled": frozenset({"manager"}),
        # the block turned out to be unrecoverable; worker or reviewer
        # escalates to "failed" so the memory system records a witness
        "failed": frozenset({"worker", "reviewer"}),
    },
    "submitted_for_review": {
        "in_progress": frozenset({"reviewer"}),
        "delivered": frozenset({"reviewer"}),
        "blocked": frozenset({"reviewer"}),
        "cancelled": frozenset({"manager"}),
        # reviewer cannot complete the review (e.g. the artifacts are
        # unreadable) and self-reports
        "failed": frozenset({"reviewer"}),
    },
    "delivered": {},
    "cancelled": {},
    "failed": {
        # manager decides what to do with a failed task: cancel it
        # outright, or retry by sending it back to in_progress
        "cancelled": frozenset({"manager"}),
        "in_progress": frozenset({"manager"}),
    },
}
FLOW_REVIEW_OUTCOMES = frozenset({"approve", "reject", "manager_action"})
FLOW_REVIEW_TRANSITIONS = {
    "approve": ("delivered", "approved"),
    "reject": ("in_progress", "rejected"),
    "manager_action": ("blocked", "manager_action"),
}
FLOW_MANAGER_ACTION_TYPES = frozenset({
    "manager_review_needed",
    "clarify_scope",
    "choose_direction",
    "provide_missing_info",
    "reassign_reviewer",
    "decide_user_message",
})
FLOW_REVIEW_REASONS = frozenset({
    "approved_for_delivery",
    "changes_requested",
    "reviewer_requested_manager_action",
    "missing_scope_confirmation",
    "missing_owner_decision",
    "quality_not_met",
    "missing_required_artifact",
})
_MEANINGFUL_EVENT_FIELDS = (
    "owner",
    "reviewer",
    "stage",
    "status",
    "verdict",
    "needs_manager_action",
    "blocking_reason",
    "manager_action_type",
    "review_reason",
    "latest_turn_summary",
    "workflow_id",
    "scope_topic",
    "scope_files",
    "verdict_target",
    "verdict_scope",
    "evidence_packet",
    "evidence_snapshot",
    "latest_authoritative_verdict",
    "required_fix",
    "blocking_files",
    "closeout_status",
    "loop_run_id",
    "loop_status",
    "loop_cycle_count",
    "loop_stop_reason",
    "loop_recommended_action",
    "loop_evidence_ref",
    "loop_updated_by",
    "self_check_status",
    "review_check_status",
    "manager_closeout_status",
    "batch_closed_out_at",
    "manager_closed_out_at",
    "revision_priority",
    "revision_priority_set_at",
)
_FLOW_SEMANTIC_DEFAULTS = {
    "manager_action_type": "",
    "review_reason": "",
    "latest_turn_summary": "",
    "scope_topic": "",
    "scope_files": [],
    "verdict_target": "",
    "verdict_scope": "",
    "evidence_packet": {},
    "evidence_snapshot": {},
    "latest_authoritative_verdict": {},
    "required_fix": [],
    "blocking_files": [],
    "closeout_status": "",
    "loop_run_id": "",
    "loop_status": "",
    "loop_cycle_count": 0,
    "loop_stop_reason": "",
    "loop_recommended_action": "",
    "loop_evidence_ref": "",
    "loop_updated_by": "",
    "self_check_status": "",
    "review_check_status": "",
    "manager_closeout_status": "",
    "tier_status": "",
    "batch_closed_out_at": None,
    "manager_closed_out_at": None,
    "revision_priority": "",
    "revision_priority_set_at": None,
}
_FLOW_REVISION_PRIORITIES = frozenset({"minor", "manager", "user"})
IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID = "igcse-subject-launch"
AP_KNOWLEDGE_BASE_OPTIMIZATION_WORKFLOW_ID = "ap-knowledge-base-optimization"
WORKFLOW_DEFAULT_REVIEWERS = {
    IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID: "review_course",
    AP_KNOWLEDGE_BASE_OPTIMIZATION_WORKFLOW_ID: "review_course",
}
AP_TITLE_MARKERS = (
    "AP ",
    "AP-",
    "AP_Calculus",
    "AP_Computer_Science",
    "AP_Physics",
    "AP_Statistics",
    "AP_Psychology",
    "Advanced Placement",
)
IGCSE_TITLE_MARKERS = (
    "IGCSE",
    "0452",
    "0455",
    "0478",
    "0610",
    "0620",
    "0625",
    "0580",
    "0606",
    "0653",
)
IGCSE_SYLLABUS_CODES = ("0450", "0452", "0455", "0478", "0580", "0606", "0610", "0620", "0625", "0653")
IGCSE_SUBJECT_NAMES = {
    "0450": "Business Studies",
    "0452": "Accounting",
    "0455": "Economics",
    "0478": "Computer Science",
    "0580": "Mathematics",
    "0606": "Additional Mathematics",
    "0610": "Biology",
    "0620": "Chemistry",
    "0625": "Physics",
    "0653": "Combined Science",
}
REVIEW_REQUIRED_STAGES = frozenset({"curriculum", "admissions", "school"})
REVIEW_EVIDENCE_FIELDS = (
    "files_sampled",
    "items_mapping_count",
    "qa_count",
    "item_count",
    "q_ids_checked",
    "sampled_topic_count",
    "missing_topic_count",
    "qbank_readiness",
    "calculation_or_concept_checks",
    "path_naming_result",
    # Package 7 (Revision-First Gate) fields — preserved through
    # `_normalize_evidence_packet` so `validate_evidence_packet` can see
    # them on the saved task record.
    "workflow_id",
    "task_id",
    "batch_range",
    "items_count",
    "qql_count",
    "manifest_evidence",
)
SUBJECT_QA_STANDARD = {
    "qa_min": 300,
    "qa_max": 500,
    "item_min": 300,
    "item_max": 500,
}
QBANK_READINESS_VALUES = frozenset({
    "qbank_ready",
    "qbank_blocked_low_volume",
    "qbank_blocked_missing_mapping",
    "qbank_blocked_missing_question_directions",
    "qbank_review_needed",
})

# ── QBank lifecycle states ─────────────────────────────────────────
# These are derived states, not stored in task.status — QBank tasks use
# the standard flow status vocabulary. These states are computed from
# verification report output and dedup dry-run results.

QBANK_LIFECYCLE_STATES = frozenset({
    "scan",
    "empty",
    "issue_fix",
    "reverify",
    "ready_for_import",
    "needs_review",
    "needs_user_authorization",
})

QBANK_LIFECYCLE_NEXT_ACTIONS = {
    "scan": "initial_scan_complete_review_results",
    "empty": "no_qa_found_check_content",
    "issue_fix": "fix_schema_or_manifest_errors",
    "reverify": "review_course_reverify_subject",
    "ready_for_import": "needs_user_authorization",
    "needs_review": "review_course_review_required",
    "needs_user_authorization": "manager_or_user_authorize_import",
}

QBANK_TERMINAL_LIFECYCLE = frozenset({
    "ready_for_import",
    "needs_user_authorization",
})


def qbank_lifecycle_status(subject_slug: str, verification_summary: dict | None = None) -> dict:
    """Compute QBank lifecycle status for a subject from verification output.

    Returns a compact dict with current state and next action.
    """

    def _safe_int(value, default=0):
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    if verification_summary is None:
        return {
            "subject": subject_slug,
            "lifecycle_state": "scan",
            "next_action": "run_qbank_verify",
            "needs_review": True,
            "needs_user_authorization": False,
            "ready_for_import": False,
            "review_course_pass": False,
        }

    # Normalize status: accept both per-subject "status" and overall "overall_status"
    raw_status = str(verification_summary.get("status") or verification_summary.get("overall_status") or "scan")
    status = raw_status.upper()
    total_questions = int(verification_summary.get("total_questions") or 0)
    errors = _safe_int(verification_summary.get("total_errors") or verification_summary.get("error_count"))
    warnings = _safe_int(verification_summary.get("total_warnings") or verification_summary.get("warning_count"))
    questions = _safe_int(verification_summary.get("total_questions") or total_questions)
    subjects_scanned = _safe_int(verification_summary.get("subjects_scanned"))
    manifest_issues = _safe_int(verification_summary.get("manifest_issues"))

    if questions == 0 and subjects_scanned == 0:
        lifecycle = "scan"
    elif status == "FAIL" or errors > 0:
        lifecycle = "issue_fix"
    elif warnings > 0 or manifest_issues > 0:
        lifecycle = "reverify"
    elif status == "PASS":
        lifecycle = "ready_for_import"
    else:
        lifecycle = "needs_review"

    return {
        "subject": subject_slug,
        "lifecycle_state": lifecycle,
        "next_action": QBANK_LIFECYCLE_NEXT_ACTIONS.get(lifecycle, "review_status"),
        "needs_review": lifecycle in {"scan", "issue_fix", "reverify", "needs_review"},
        "needs_user_authorization": lifecycle == "ready_for_import",
        "ready_for_import": lifecycle == "ready_for_import",
        "review_course_pass": status == "PASS",
        "total_questions": questions,
        "errors": errors,
        "warnings": warnings,
        "manifest_issues": manifest_issues,
    }


# ── Dedup / import gate ────────────────────────────────────────────


def dedup_import_gate(*, review_course_pass: bool = False,
                      user_authorized: bool = False,
                      manager_authorized: bool = False,
                      dry_run: bool = True) -> dict:
    """Check whether dedup/import apply is allowed.

    Apply requires BOTH:
      - review_course PASS
      - user or manager explicit authorization

    Dry-run is always allowed; it does NOT count as authorization.
    """
    blocked = False
    blocking_reasons = []

    if not review_course_pass:
        blocked = True
        blocking_reasons.append("review_course_pass_required")

    if not (user_authorized or manager_authorized):
        blocked = True
        blocking_reasons.append("user_or_manager_authorization_required")

    if dry_run:
        return {
            "apply_allowed": False,
            "blocked": False,
            "mode": "dry_run",
            "review_course_pass": review_course_pass,
            "user_authorized": user_authorized,
            "manager_authorized": manager_authorized,
            "blocking_reasons": [],
            "next_action": "review_dry_run_results_then_authorize",
            "summary": "Dry-run only — no content will be modified. Review results before requesting authorization.",
        }

    if blocked:
        return {
            "apply_allowed": False,
            "blocked": True,
            "mode": "apply_blocked",
            "review_course_pass": review_course_pass,
            "user_authorized": user_authorized,
            "manager_authorized": manager_authorized,
            "blocking_reasons": blocking_reasons,
            "next_action": _dedup_import_next_action(blocking_reasons),
            "summary": _dedup_import_block_summary(blocking_reasons),
        }

    return {
        "apply_allowed": True,
        "blocked": False,
        "mode": "apply",
        "review_course_pass": review_course_pass,
        "user_authorized": user_authorized,
        "manager_authorized": manager_authorized,
        "blocking_reasons": [],
        "next_action": "proceed_with_dedup_import_apply",
        "summary": "All gates passed — dedup/import apply is authorized.",
    }


def _dedup_import_next_action(reasons: list[str]) -> str:
    if "review_course_pass_required" in reasons and "user_or_manager_authorization_required" in reasons:
        return "complete_review_course_then_authorize"
    if "review_course_pass_required" in reasons:
        return "complete_review_course_pass"
    if "user_or_manager_authorization_required" in reasons:
        return "request_manager_or_user_authorization"
    return "unknown_blocking_reason"


def _dedup_import_block_summary(reasons: list[str]) -> str:
    parts = []
    if "review_course_pass_required" in reasons:
        parts.append("review_course must PASS before dedup/import")
    if "user_or_manager_authorization_required" in reasons:
        parts.append("explicit user or manager authorization required")
    return "; ".join(parts) if parts else "blocked for unknown reason"


def qbank_manager_panel_summary(verification_summary: dict | None = None,
                                subjects: list[str] | None = None) -> dict:
    """Build a compact QBank section for the manager-panel.

    Summarizes lifecycle states across all subjects and identifies
    the most urgent next action.
    """
    if verification_summary is None:
        return {
            "qbank_active": False,
            "subjects": [],
            "total_subjects": 0,
            "lifecycle_breakdown": {},
            "most_urgent_action": "run_qbank_verify_for_status",
            "summary": "No QBank verification data available.",
        }

    subject_summaries = verification_summary.get("subjects") or []
    lifecycle_breakdown: dict[str, int] = {}
    most_urgent = "no_action"
    urgent_priority = {
        "issue_fix": 0,
        "scan": 1,
        "reverify": 2,
        "needs_review": 3,
        "ready_for_import": 4,
        "needs_user_authorization": 5,
    }

    processed_subjects = []
    for subj in subject_summaries:
        slug = str(subj.get("subject") or "")
        status = str(subj.get("status") or "scan")
        lifecycle_breakdown[status] = lifecycle_breakdown.get(status, 0) + 1
        if status in urgent_priority:
            current_priority = urgent_priority.get(most_urgent, 99)
            if urgent_priority[status] < current_priority:
                most_urgent = status
        processed_subjects.append({
            "subject": slug,
            "name": subj.get("name", slug),
            "lifecycle_state": status,
            "total_questions": int(subj.get("total_questions") or 0),
            "error_count": int(subj.get("error_count") or 0),
            "warning_count": int(subj.get("warning_count") or 0),
        })

    return {
        "qbank_active": len(processed_subjects) > 0,
        "subjects": processed_subjects,
        "total_subjects": len(processed_subjects),
        "lifecycle_breakdown": lifecycle_breakdown,
        "most_urgent_action": QBANK_LIFECYCLE_NEXT_ACTIONS.get(most_urgent, "review_qbank_status"),
        "overall_status": verification_summary.get("overall_status", "UNKNOWN"),
        "total_errors": int(verification_summary.get("total_errors") or 0),
        "total_warnings": int(verification_summary.get("total_warnings") or 0),
        "summary": (
            f"QBank: {len(processed_subjects)} subjects, "
            f"{verification_summary.get('overall_status', 'UNKNOWN')}, "
            f"{lifecycle_breakdown}"
        ),
    }
_DEFAULT_MANAGER_ACTION_TYPE = "manager_review_needed"
_DEFAULT_REVIEW_REASON_BY_OUTCOME = {
    "approve": "approved_for_delivery",
    "reject": "changes_requested",
    "manager_action": "reviewer_requested_manager_action",
}
_MANAGER_ACTION_TYPE_LABELS = {
    "manager_review_needed": "需要经理介入判断",
    "clarify_scope": "确认任务范围",
    "choose_direction": "拍板下一步方向",
    "provide_missing_info": "补充缺失信息",
    "reassign_reviewer": "重新指定审核人",
    "decide_user_message": "决定对 user 的表达",
}
_REVIEW_REASON_LABELS = {
    "approved_for_delivery": "已审核通过，可对外同步",
    "changes_requested": "需要修改后重新提交",
    "reviewer_requested_manager_action": "审核人请求经理介入",
    "missing_scope_confirmation": "范围仍待经理确认",
    "missing_owner_decision": "存在分歧，待经理拍板",
    "quality_not_met": "当前质量未达标",
    "missing_required_artifact": "缺少必要产物或材料",
}
_MANAGER_ACTION_RECOMMENDATIONS = {
    "manager_review_needed": "先查看 reviewer 备注，再决定由谁继续推进。",
    "clarify_scope": "先确认范围边界，再决定是否让 worker 重做或继续。",
    "choose_direction": "尽快拍板下一步方向，避免任务继续空转。",
    "provide_missing_info": "补齐 reviewer 缺的材料或上下文，再回给执行人。",
    "reassign_reviewer": "判断是否需要更换 reviewer 或追加二审。",
    "decide_user_message": "判断现在是否需要对 user 做受控解释。",
}
_REVIEW_REASON_RECOMMENDATIONS = {
    "approved_for_delivery": "可以安排对外同步，确保对 user 的说法与交付一致。",
    "changes_requested": "督促 owner 按修改意见尽快重提。",
    "reviewer_requested_manager_action": "优先由经理接手判断，别让任务挂起。",
    "missing_scope_confirmation": "先确认范围，再决定是否继续执行。",
    "missing_owner_decision": "优先拍板，避免 reviewer 和 worker 来回消耗。",
    "quality_not_met": "明确质量缺口，再要求重做。",
    "missing_required_artifact": "先补齐必要产物或附件，再进入下一轮。",
}
_SUBJECT_COMPLETION_MARKERS = (
    "300 QA",
    "最终批",
    "全部 10 批次",
    "正式完成",
    "全学科",
    "sub-topics 正式完成",
)
_PACKAGE_SCOPE_MARKERS = (
    "batch",
    "小包",
    "topic",
    "topics",
    "unit",
    "prototype",
    "seed",
)
_SUBJECT_FOLLOWUP_ACTIONS = (
    "manager_closeout_pending",
    "builder_retro_pending",
    "qbank_refresh_pending",
    "next_subject_decision_pending",
)
_SUBJECT_FOLLOWUP_LABELS = {
    "manager_closeout_pending": "manager 正式收口",
    "builder_retro_pending": "builder 复盘沉淀",
    "qbank_refresh_pending": "qbank 学科级复核",
    "next_subject_decision_pending": "下一学科决策",
}


def _file() -> Path:
    return paths.state_dir() / "tasks.json"


def _events_file() -> Path:
    return paths.task_events_file()


def _locked():
    return flock(_file().with_suffix(".lock"))


def _load() -> dict:
    data = read_json(_file(), {"tasks": [], "_meta": {"last_id": 0}})
    for task in data.get("tasks", []):
        _ensure_flow_semantic_defaults(task)
    return data


def _save(data: dict) -> None:
    write_json(_file(), data)


def _task_snapshot(task: dict | None) -> dict | None:
    if task is None:
        return None
    return json.loads(json.dumps(task, ensure_ascii=False))


def _task_changes(before: dict | None, after: dict | None) -> dict:
    if before is None or after is None:
        return {}
    keys = sorted(set(before) | set(after))
    changes = {}
    for key in keys:
        if before.get(key) != after.get(key):
            changes[key] = {"before": before.get(key), "after": after.get(key)}
    return changes


def _meaningful_task_changes(before: dict | None, after: dict | None) -> dict:
    if before is None or after is None:
        return {}
    changes = {}
    for key in _MEANINGFUL_EVENT_FIELDS:
        if before.get(key) != after.get(key):
            changes[key] = {"before": before.get(key), "after": after.get(key)}
    return changes


def _append_task_event(*, task_id: str, kind: str, actor: str = "",
                       before: dict | None, after: dict | None) -> dict:
    created_at = now_ms()
    correlation_id = ""
    lane = ""
    event_type = kind
    from_status = ""
    to_status = ""
    from_stage = ""
    to_stage = ""
    from_owner = ""
    to_owner = ""
    from_needs_manager_action = False
    to_needs_manager_action = False
    verdict = ""
    blocking_reason = ""
    meaningful_changes = _meaningful_task_changes(before, after)

    if isinstance(after, dict):
        correlation_id = str(after.get("correlation_id") or "")
        lane = str(after.get("stage") or "")
        to_status = str(after.get("status") or "")
        to_stage = str(after.get("stage") or "")
        to_owner = str(after.get("owner") or "")
        to_needs_manager_action = bool(after.get("needs_manager_action") or False)
        verdict = str(after.get("verdict") or "")
        blocking_reason = str(after.get("blocking_reason") or "")
    if isinstance(before, dict):
        correlation_id = correlation_id or str(before.get("correlation_id") or "")
        lane = lane or str(before.get("stage") or "")
        from_status = str(before.get("status") or "")
        from_stage = str(before.get("stage") or "")
        from_owner = str(before.get("owner") or "")
        from_needs_manager_action = bool(before.get("needs_manager_action") or False)
    if kind == "created":
        event_type = "task_created"
    elif kind == "transition":
        if (
            "reviewer" in meaningful_changes
            and set(meaningful_changes).issubset({"reviewer", "latest_turn_summary"})
        ):
            event_type = "reviewer_assigned"
        elif "status" in meaningful_changes:
            event_type = "status_changed"
        elif "needs_manager_action" in meaningful_changes:
            event_type = "manager_action_changed"
        else:
            event_type = "task_updated"

    row = {
        "event_id": f"te-{created_at}-{uuid4().hex[:8]}",
        "schema_version": 2,
        "task_id": task_id,
        "correlation_id": correlation_id,
        "kind": kind,
        "event_type": event_type,
        "actor": actor,
        "lane": lane,
        "from_status": from_status,
        "to_status": to_status,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "from_owner": from_owner,
        "to_owner": to_owner,
        "from_needs_manager_action": from_needs_manager_action,
        "to_needs_manager_action": to_needs_manager_action,
        "verdict": verdict,
        "blocking_reason": blocking_reason,
        "before": before,
        "after": after,
        "changes": _task_changes(before, after),
        "meaningful_changes": meaningful_changes,
        "created_at": created_at,
    }
    path = _events_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _next_task_id(data: dict) -> str:
    data["_meta"]["last_id"] = data["_meta"].get("last_id", 0) + 1
    return f"T-{data['_meta']['last_id']}"


def canonical_stage(stage: str) -> str:
    normalized = str(stage or "").strip()
    return FLOW_STAGE_ALIASES.get(normalized, normalized)


def _validate_flow_stage_status(stage: str, status: str) -> None:
    stage = canonical_stage(stage)
    if stage not in FLOW_STAGES:
        raise ValueError(f"invalid stage: {stage} (valid: {sorted(FLOW_STAGES)})")
    if status not in FLOW_STATUSES:
        raise ValueError(f"invalid status: {status} (valid: {sorted(FLOW_STATUSES)})")
    allowed = FLOW_ALLOWED_STAGE_STATUSES[stage]
    if status not in allowed:
        raise ValueError(f"invalid status {status!r} for stage {stage!r} (allowed: {sorted(allowed)})")


def _flow_completed_at(status: str) -> int | None:
    return now_ms() if status in FLOW_TERMINAL_STATUSES else None


def _flow_needs_manager_action(status: str, verdict: str) -> bool:
    return status == "blocked" and verdict == "manager_action"


def _ensure_flow_semantic_defaults(task: dict) -> dict:
    if task.get("schema_version") != 2:
        return task
    for key, value in _FLOW_SEMANTIC_DEFAULTS.items():
        task.setdefault(key, json.loads(json.dumps(value, ensure_ascii=False)))
    return task


def _normalize_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _normalize_evidence_packet(value) -> dict:
    if not isinstance(value, dict):
        return {}
    packet: dict = {}
    for field in REVIEW_EVIDENCE_FIELDS:
        if field not in value:
            continue
        raw = value.get(field)
        if field in {"files_sampled", "q_ids_checked", "calculation_or_concept_checks"}:
            packet[field] = _normalize_list(raw)
        elif field in {"items_mapping_count", "qa_count", "item_count", "sampled_topic_count", "missing_topic_count"}:
            try:
                packet[field] = int(raw)
            except (TypeError, ValueError):
                packet[field] = 0
        elif field == "qbank_readiness":
            text = str(raw or "").strip()
            packet[field] = text if text in QBANK_READINESS_VALUES else ""
        else:
            packet[field] = str(raw or "").strip()
    # Package 7 (Revision-First Gate): also persist the new
    # REQUIRED_EVIDENCE_PACKET_FIELDS so `validate_evidence_packet()`
    # can read them off the task row after review_flow runs. Without
    # this, the worker-reported evidence packet would be silently
    # dropped by the legacy REVIEW_EVIDENCE_FIELDS normalizer and
    # closeout would always look incomplete.
    for field in _REQUIRED_EVIDENCE_PACKET_FIELDS:
        if field in value and field not in packet:
            packet[field] = value[field]
    return packet


# Package 7 (Revision-First Gate): mirror the supervisor-side
# REQUIRED_EVIDENCE_PACKET_FIELDS so review_flow can preserve them
# through `_normalize_evidence_packet`. The supervisor-side constant
# is the authoritative one; this is the writer-side alias.
_REQUIRED_EVIDENCE_PACKET_FIELDS = (
    "workflow_id",
    "task_id",
    "batch_range",
    "items_count",
    "qql_count",
    "manifest_evidence",
)


# ── Package 3: Review Verdict Authority ─────────────────────────
# Verdict scope marks which layer a review PASS / FAIL actually covers.
# The closeout gate uses `latest_authoritative_verdict` (the most recent
# review event) rather than the task's static verdict field so that
# older PASSes cannot block a newer FAIL.

VERDICT_SCOPES = frozenset({
    "qql_only",       # review only validated QQL files (qa-question-level)
    "items_only",     # review only validated items layer
    "manifest",       # review only validated the QA manifest
    "qql_items",      # review validated QQL + items but NOT manifest;
                      # recognized scope (avoids empty-string surprise)
                      # but NOT authoritative for subject closeout.
    "package",        # a small batch / package / topic unit
    "full_subject",   # the entire subject (QQL + items + manifest)
})

# A subject closeout can only be satisfied by verdict_scope values that
# cover enough of the subject to call it "the subject has been reviewed".
# `qql_only` / `items_only` / `manifest` / `qql_items` / `package` are
# NOT enough on their own; manager must either re-review the missing
# layer or accept the reduced scope explicitly via an out-of-band manager
# decision (not modeled here — manager-actions / manager-panel must
# not emit a formal closeout action for these scopes).
SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES = frozenset({"full_subject"})

# Mapping from "review outcome" / review_reason → minimal required
# scope to call it authoritative for a subject. This is the gate the
# manager-actions / manager-panel call to decide whether to emit a
# "正式收口" (formal closeout) suggestion.
_OUTCOME_REQUIRED_SCOPE = {
    "approve": "full_subject",
    "reject": "full_subject",  # reject must cover full subject to be authoritative
    "manager_action": "full_subject",
}


def normalize_verdict_scope(value) -> str:
    """Normalize a verdict_scope value to one of VERDICT_SCOPES.

    Returns "" if value is empty / unrecognized. Callers should treat
    empty scope as 'untrusted — do not treat as authoritative'."""
    text = str(value or "").strip()
    if not text:
        return ""
    return text if text in VERDICT_SCOPES else ""


def derive_verdict_scope_from_target(verdict_target: str) -> str:
    """Best-effort auto-derivation of verdict_scope from verdict_target text.

    The reviewer normally supplies verdict_target = "QQL + items layer"
    or "items only" or a specific topic. We map common phrasings onto
    the canonical scope values; if we can't classify the target, we
    return "" (caller must treat verdict as untrusted for closeout).

    Package 3 invariant: an empty verdict_target is NEVER treated as
    full_subject. The reviewer must explicitly declare the scope.
    """
    text = str(verdict_target or "").strip()
    if not text:
        return ""
    lowered = text.lower()

    # Explicit markers first — these win.
    if "full_subject" in lowered or "全学科" in text or "full subject" in lowered:
        return "full_subject"
    # Package 3: "QQL + items" combined review covers two of three
    # layers; it is recognized as the explicit `qql_items` scope
    # (not authoritative for subject closeout) so the reviewer sees
    # a meaningful verdict_scope rather than an empty string. The
    # closeout gate still blocks because qql_items is not in
    # SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES, but manager-actions /
    # manager-panel now report "QQL+items reviewed, manifest layer
    # still pending" instead of "verdict scope undeclared".
    if "qql+items" in lowered or (
        "qql" in lowered and "items" in lowered
    ):
        return "qql_items"
    # Layer-specific markers.
    if "items only" in lowered or "仅 items" in text or "items层" in text or "items_layer" in lowered:
        return "items_only"
    if "qql only" in lowered or "qql层" in text or "qa-question-level" in lowered or "qql_layer" in lowered:
        return "qql_only"
    if "manifest" in lowered and "qql" not in lowered and "items" not in lowered:
        return "manifest"
    # Package / batch markers.
    if any(marker in text or marker in lowered for marker in _PACKAGE_SCOPE_MARKERS):
        return "package"

    # IGCSE title-like targets (e.g. "IGCSE Business Studies 0450",
    # "Biology 0610", "Physics 0625") map to full_subject.
    if re.search(r"\bIGCSE\b", text, re.IGNORECASE):
        return "full_subject"
    if any(code in text for code in IGCSE_SYLLABUS_CODES):
        return "full_subject"
    # Subject names are all multi-word or proper-case.
    for name in IGCSE_SUBJECT_NAMES.values():
        if name and name in text:
            return "full_subject"

    return ""


def evidence_snapshot_hash(evidence_packet: dict) -> str:
    """Return a stable short hash of the evidence packet's structural
    contents (file list + qa / item counts). Used to detect evidence
    drift between the time a verdict was issued and the closeout
    attempt — if the file system has changed since the verdict, the
    verdict is no longer authoritative.

    Returns "" if the packet is empty / unhashable."""
    if not isinstance(evidence_packet, dict) or not evidence_packet:
        return ""
    bits: list[str] = []
    for key in sorted(REVIEW_EVIDENCE_FIELDS):
        value = evidence_packet.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            bits.append(f"{key}={','.join(str(item) for item in value)}")
        else:
            bits.append(f"{key}={value}")
    if not bits:
        return ""
    joined = "|".join(bits)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def build_authoritative_verdict(
    *,
    outcome: str,
    verdict: str,
    reviewer: str,
    review_reason: str = "",
    verdict_target: str = "",
    evidence_packet: dict | None = None,
    scope_topic: str = "",
    scope_files=None,
    required_fix=None,
    blocking_files=None,
    at_ms: int = 0,
) -> dict:
    """Build a structured `latest_authoritative_verdict` record.

    This is the canonical review truth that downstream surfaces
    (manager-actions / manager-panel / closeout gate) must read. The
    record carries:
      - outcome / verdict / review_reason  (mirrors the old fields)
      - reviewer / at_ms  (provenance)
      - verdict_target / verdict_scope  (declared scope)
      - evidence_packet / evidence_snapshot_hash  (drift detection)
      - required_fix / blocking_files  (reviewer's contract for the
        next worker round; survives even when verdict=rejected)
    """
    target = str(verdict_target or "").strip()
    scope = derive_verdict_scope_from_target(target)
    evidence = _normalize_evidence_packet(evidence_packet)
    return {
        "outcome": str(outcome or "").strip(),
        "verdict": str(verdict or "").strip(),
        "reviewer": str(reviewer or "").strip(),
        "review_reason": str(review_reason or "").strip(),
        "verdict_target": target,
        "verdict_scope": scope,
        "evidence_packet": evidence,
        "evidence_snapshot_hash": evidence_snapshot_hash(evidence),
        "scope_topic": str(scope_topic or "").strip(),
        "scope_files": _normalize_list(scope_files),
        "required_fix": _normalize_list(required_fix),
        "blocking_files": _normalize_list(blocking_files),
        "at_ms": int(at_ms or 0),
        "is_authoritative": bool(scope and scope in VERDICT_SCOPES),
    }


def is_verdict_authoritative_for_closeout(
    task: dict,
    *,
    closeout_target: str = "full_subject",
) -> bool:
    """True iff the latest authoritative verdict on this task satisfies
    the closeout target.

    Package 3 contract:
      - latest_authoritative_verdict MUST be present and authoritative
      - its verdict_scope MUST cover the closeout target
      - 'approve' on a qql_only / items_only / manifest / package scope
        is NEVER authoritative for a full_subject closeout
      - a 'reject' or 'manager_action' verdict is NEVER authoritative
        for closeout regardless of scope
      - if the task has no `latest_authoritative_verdict`, fall back
        to the static `verdict` field but ONLY when scope was
        declared via verdict_target
    """
    target = str(closeout_target or "full_subject").strip() or "full_subject"
    if target not in SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES:
        # Unknown target — conservative: refuse.
        return False
    task = task or {}
    latest = task.get("latest_authoritative_verdict") or {}
    if latest:
        verdict_value = str(latest.get("verdict") or "").strip()
        if verdict_value != "approved":
            return False
        latest_scope = str(latest.get("verdict_scope") or "").strip()
        # Subject closeout needs the verdict_scope to cover full_subject.
        if latest_scope == "full_subject":
            return True
        # items_only + qql_only could combine to full_subject only when
        # both have been reviewed authoritatively. We do not model that
        # combination here — manager must require an explicit full_subject
        # verdict (or two distinct authoritative partial scopes and an
        # explicit out-of-band manager decision; not implemented).
        return False
    # Fallback: no latest_authoritative_verdict yet (legacy tasks).
    # Only trust the static verdict field if verdict_target was set
    # and derives to full_subject. Empty verdict_target = untrusted.
    if str(task.get("verdict") or "").strip() != "approved":
        return False
    target_text = str(task.get("verdict_target") or "").strip()
    if not target_text:
        return False
    scope = derive_verdict_scope_from_target(target_text)
    return scope == "full_subject"


def latest_verdict_blocks_closeout(task: dict) -> tuple[bool, list[str]]:
    """Return (blocks, reasons) describing whether the task's latest
    review verdict should block subject closeout.

    Used by manager-actions / manager-panel / closeout-gate to suppress
    "正式收口" suggestions when the latest verdict is FAIL or its
    scope is insufficient.

    Package 3 (Codex review): a `pending` verdict (no review yet) is
    NOT a hard block — manager can still emit a dry-run
    `manager_formal_closeout` so the operator can reconcile; the
    closeout gate itself refuses to advance without an authoritative
    verdict. Only `rejected` / `manager_action` / scope-insufficient /
    missing-scope-authoritative reasons are hard blocks.
    """
    task = task or {}
    reasons: list[str] = []
    latest = task.get("latest_authoritative_verdict") or {}
    verdict_value = str(latest.get("verdict") or task.get("verdict") or "").strip()
    if verdict_value == "rejected":
        reasons.append("latest_verdict_rejected")
    elif verdict_value == "manager_action":
        reasons.append("latest_verdict_manager_action")
    # NOTE: "pending" is intentionally NOT added to reasons — see docstring.
    if latest and not latest.get("is_authoritative"):
        reasons.append("latest_verdict_scope_untrusted")
    if latest:
        scope = str(latest.get("verdict_scope") or "").strip()
        if scope and scope not in SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES:
            reasons.append(
                f"verdict_scope_insufficient:{scope or 'unknown'}"
            )
        elif not scope:
            # Package 3: the verdict_target is parseable (so the task
            # has a verdict_scope) but the value didn't match any
            # known scope marker and didn't trip the IGCSE heuristics
            # either. This typically means the reviewer wrote
            # something ambiguous — e.g. "subject review 5" with no
            # explicit scope. The closeout gate must block because
            # we cannot prove the verdict covers the full_subject.
            reasons.append("verdict_scope_undeclared")
    # Package 3 (Codex review MEDIUM #3): legacy approved tasks
    # without an explicit verdict_target / latest_authoritative_verdict
    # MUST be flagged. The reviewer must re-declare the scope before
    # the closeout gate clears them; without this, the manager can
    # claim "verdict=approved" without any review truth.
    if not latest and str(task.get("verdict") or "") == "approved":
        if not str(task.get("verdict_target") or "").strip():
            reasons.append("missing_verdict_target_on_approved_task")
    return bool(reasons), reasons


def _default_turn_summary(*, status: str, actor: str, outcome: str = "") -> str:
    if outcome == "approve":
        return "Reviewer approved the latest turn for delivery."
    if outcome == "reject":
        return "Reviewer requested revisions and returned the task to in_progress."
    if outcome == "manager_action":
        return "Reviewer requested manager action before the task can continue."
    if status == "queued":
        return "Task created and queued."
    if status == "assigned":
        return "Manager assigned the task to the owner."
    if status == "in_progress":
        return "Work started or resumed on the latest turn."
    if status == "submitted_for_review":
        return "Worker submitted the latest turn for review."
    if status == "delivered":
        return "Task delivered."
    if status == "blocked":
        effective_actor = actor or "worker"
        if effective_actor == "manager":
            return "Manager blocked the task pending a decision."
        if effective_actor == "reviewer":
            return "Reviewer blocked the task pending follow-up."
        return "Worker blocked the task pending follow-up."
    if status == "cancelled":
        return "Task cancelled."
    return ""


def _normalize_flow_taxonomy_value(
    value: str,
    *,
    field_name: str,
    allowed_values: frozenset[str],
    allow_blank: bool = True,
) -> str:
    normalized = value.strip()
    if not normalized:
        if allow_blank:
            return ""
        raise ValueError(
            f"{field_name} cannot be empty "
            f"(valid: {sorted(allowed_values)})"
        )
    if normalized not in allowed_values:
        raise ValueError(
            f"invalid {field_name}: {normalized} "
            f"(valid: {sorted(allowed_values)})"
        )
    return normalized


def _normalize_manager_action_type(value: str, *, allow_blank: bool = True) -> str:
    return _normalize_flow_taxonomy_value(
        value,
        field_name="manager_action_type",
        allowed_values=FLOW_MANAGER_ACTION_TYPES,
        allow_blank=allow_blank,
    )


def _normalize_review_reason(value: str, *, allow_blank: bool = True) -> str:
    return _normalize_flow_taxonomy_value(
        value,
        field_name="review_reason",
        allowed_values=FLOW_REVIEW_REASONS,
        allow_blank=allow_blank,
    )


def describe_manager_action_type(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    return _MANAGER_ACTION_TYPE_LABELS.get(
        normalized,
        f"未归类经理动作：{normalized}",
    )


def describe_review_reason(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    return _REVIEW_REASON_LABELS.get(
        normalized,
        f"未归类审核原因：{normalized}",
    )


def flow_semantic_summary(task: dict) -> str:
    verdict = str(task.get("verdict") or "").strip()
    review_reason = str(task.get("review_reason") or "").strip()
    manager_action_type = str(task.get("manager_action_type") or "").strip()
    needs_manager_action = bool(task.get("needs_manager_action") or False)

    action_text = describe_manager_action_type(manager_action_type)
    reason_text = describe_review_reason(review_reason)

    if needs_manager_action or verdict == "manager_action":
        if action_text and reason_text:
            return f"待经理处理：{action_text}；原因：{reason_text}"
        if action_text:
            return f"待经理处理：{action_text}"
        if reason_text:
            return f"待经理处理：{reason_text}"
        return "待经理处理：审核人请求经理介入"

    if verdict == "rejected":
        if reason_text:
            return f"审核退回：{reason_text}"
        return "审核退回：需要修改后重新提交"

    if verdict == "approved" or review_reason == "approved_for_delivery":
        return "已审核通过，可对外同步"

    if reason_text:
        return reason_text
    return ""


def flow_live_summary(task: dict) -> str:
    """Return the most useful current-state summary for operator surfaces."""
    subject_summary = subject_closeout_summary(task)
    semantic = flow_semantic_summary(task)
    latest_turn_summary = str(task.get("latest_turn_summary") or "").strip()
    if subject_summary and semantic and latest_turn_summary:
        return f"{subject_summary}；{semantic}；{latest_turn_summary}"
    if subject_summary and latest_turn_summary:
        return f"{subject_summary}；{latest_turn_summary}"
    if subject_summary and semantic:
        return f"{subject_summary}；{semantic}"
    if subject_summary:
        return subject_summary
    if semantic and latest_turn_summary:
        return f"{semantic}；{latest_turn_summary}"
    if semantic:
        return semantic
    return latest_turn_summary


def flow_user_delivery_phrase(task: dict) -> str:
    verdict = str(task.get("verdict") or "").strip()
    review_reason = str(task.get("review_reason") or "").strip()
    if verdict == "approved" or review_reason == "approved_for_delivery":
        return "已审核通过并交付"
    return "已完成交付"


def recommended_manager_action(task: dict) -> str:
    if subject_followup_actions(task):
        return "先正式收口该学科，再决定 builder 复盘、qbank 复核与下一学科。"
    manager_action_type = str(task.get("manager_action_type") or "").strip()
    review_reason = str(task.get("review_reason") or "").strip()
    needs_manager_action = bool(task.get("needs_manager_action") or False)
    verdict = str(task.get("verdict") or "").strip()

    if manager_action_type:
        return _MANAGER_ACTION_RECOMMENDATIONS.get(
            manager_action_type,
            f"检查未归类经理动作：{manager_action_type}",
        )
    if review_reason:
        return _REVIEW_REASON_RECOMMENDATIONS.get(
            review_reason,
            f"检查未归类审核原因：{review_reason}",
        )
    if needs_manager_action or verdict == "manager_action":
        return "优先查看 reviewer 说明，并决定下一位责任人。"
    if verdict == "rejected":
        return "联系 owner 修改后重新提交。"
    return ""


def _contains_subject_completion_marker(text: str) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return any(
        marker in normalized or marker.lower() in lowered
        for marker in _SUBJECT_COMPLETION_MARKERS
    )


def is_igcse_course_task(*, title: str, stage: str) -> bool:
    if canonical_stage(stage) != "curriculum":
        return False
    normalized = str(title or "")
    lowered = normalized.lower()
    return any(marker in normalized or marker.lower() in lowered for marker in IGCSE_TITLE_MARKERS)


def is_ap_knowledge_task(*, title: str, stage: str) -> bool:
    if canonical_stage(stage) != "curriculum":
        return False
    normalized = str(title or "")
    lowered = normalized.lower()
    return any(marker.lower().strip() in lowered for marker in AP_TITLE_MARKERS)


def extract_subject_code(title: str) -> str:
    """Extract the 4-digit IGCSE syllabus code from a task title.

    Returns empty string if no known code is found.
    """
    normalized = str(title or "")
    for code in sorted(IGCSE_SYLLABUS_CODES, key=len, reverse=True):
        if code in normalized:
            return code
    # Fallback: scan for any 4-digit number
    import re
    m = re.search(r"\b(\d{4})\b", normalized)
    if m:
        return m.group(1)
    return ""


def extract_subject_slug(title: str) -> str:
    """Extract a stable subject slug from a task title.

    Format: igcse-{subject_name_lower}-{code}
    Example: igcse-physics-0625

    Strips batch/package/unit markers so all tasks for the same subject
    share the same slug regardless of batch number.
    """
    import re as _re

    code = extract_subject_code(title)
    if not code:
        return ""
    subject = IGCSE_SUBJECT_NAMES.get(code, "")
    if not subject:
        # Try to extract subject name from title
        normalized = str(title or "")
        m = _re.search(r"IGCSE\s+(\w+)", normalized, _re.IGNORECASE)
        if m:
            subject = m.group(1)
        else:
            subject = code
    # Strip batch/package/unit suffixes
    slug = f"igcse-{subject.lower().replace(' ', '-')}-{code}"
    # Remove batch references from the slug
    slug = _re.sub(r"-batch-\d+", "", slug)
    slug = _re.sub(r"-batch\d+", "", slug)
    return slug


def extract_subject_label(title: str) -> str:
    """Return human-readable subject label: 'Physics (0625)'."""
    code = extract_subject_code(title)
    if not code:
        return str(title or "")
    subject = IGCSE_SUBJECT_NAMES.get(code, "")
    if subject:
        return f"{subject} ({code})"
    return f"IGCSE {code}"


def required_workflow_id_for_task(*, title: str, stage: str) -> str:
    if is_igcse_course_task(title=title, stage=stage):
        return IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID
    if is_ap_knowledge_task(title=title, stage=stage):
        return AP_KNOWLEDGE_BASE_OPTIMIZATION_WORKFLOW_ID
    return ""


def default_reviewer_for_workflow(workflow_id: str) -> str:
    return WORKFLOW_DEFAULT_REVIEWERS.get(str(workflow_id or "").strip(), "")


def normalize_required_workflow_id(*, title: str, stage: str, workflow_id: str = "") -> str:
    required = required_workflow_id_for_task(title=title, stage=stage)
    normalized = str(workflow_id or "").strip()
    if required:
        if normalized and normalized != required:
            raise ValueError(f"task title requires workflow_id={required}")
        return required
    return normalized


def is_package_scope(task: dict) -> bool:
    text = " ".join(
        str(task.get(key) or "")
        for key in ("title", "scope_topic", "verdict_target")
    )
    lowered = text.lower()
    return any(marker in text or marker in lowered for marker in _PACKAGE_SCOPE_MARKERS)


def is_subject_completion_candidate(task: dict) -> bool:
    if canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return False
    verdict = str(task.get("verdict") or "").strip()
    status = str(task.get("status") or "").strip()
    if verdict != "approved" and status != "delivered":
        return False
    return (
        _contains_subject_completion_marker(str(task.get("latest_turn_summary") or ""))
        or _contains_subject_completion_marker(str(task.get("description") or ""))
    )


def _has_subject_closeout_signal(task: dict) -> bool:
    if canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return False
    return (
        _contains_subject_completion_marker(str(task.get("title") or ""))
        or _contains_subject_completion_marker(str(task.get("description") or ""))
        or _contains_subject_completion_marker(str(task.get("latest_turn_summary") or ""))
        or is_subject_completion_candidate(task)
    )


def subject_followup_actions(task: dict) -> tuple[str, ...]:
    if not is_subject_completion_candidate(task):
        return ()
    return _SUBJECT_FOLLOWUP_ACTIONS


def subject_closeout_summary(task: dict) -> str:
    actions = subject_followup_actions(task)
    if not actions:
        return ""
    labels = [_SUBJECT_FOLLOWUP_LABELS[action] for action in actions]
    return f"学科已完成，待{' / '.join(labels)}"


def workflow_gate_status(task: dict | None) -> dict:
    task = task or {}
    workflow_id = str(task.get("workflow_id") or "").strip()
    status = str(task.get("status") or "").strip()
    verdict = str(task.get("verdict") or "").strip()
    reviewer = str(task.get("reviewer") or "").strip()
    evidence = task.get("evidence_packet") or {}
    closeout_status = str(task.get("closeout_status") or "").strip()
    revision_priority = str(task.get("revision_priority") or "").strip()
    default_reviewer = default_reviewer_for_workflow(workflow_id)

    gate = "no_workflow"
    gate_status = "not_mounted"
    next_action = "mount_workflow"
    evidence_keys = sorted(key for key, value in evidence.items() if value)

    if revision_priority:
        gate = "revision_first"
        gate_status = f"revision_priority_active_{revision_priority}"
        if revision_priority == "minor":
            next_action = "worker_repair_revision_scope_before_any_other_action"
        elif revision_priority == "manager":
            next_action = "manager_decide_scope_or_direction_before_any_other_action"
        elif revision_priority == "user":
            next_action = "wait_for_user_message_or_ack_revision_scope"
        else:
            next_action = "reconcile_revision_priority_before_any_other_action"
    elif workflow_id == IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID:
        if status in {"queued", "assigned"}:
            gate = "dispatch_acceptance_gate"
            gate_status = "waiting_worker_acceptance"
            next_action = "worker_start_or_ack"
        elif status == "in_progress":
            gate = "review_handoff_gate"
            gate_status = "waiting_review_handoff"
            next_action = "submit_review"
        elif status == "submitted_for_review":
            gate = "quality_gate"
            gate_status = "awaiting_review_verdict" if reviewer else "missing_reviewer"
            next_action = "review_course_review" if reviewer else "assign_review_course"
        elif status == "blocked" and verdict == "manager_action":
            gate = "repair_acceptance_contract"
            gate_status = "manager_action_required"
            next_action = "manager_decide_repair_or_scope"
        elif status == "in_progress" and verdict == "rejected":
            gate = "repair_acceptance_contract"
            gate_status = "repair_required"
            next_action = "worker_repair_and_resubmit"
        elif status == "delivered" and closeout_status in {"batch_closeout_completed", "closeout_completed"}:
            gate = "batch_closeout_gate"
            gate_status = "passed"
            next_action = "no_subject_closeout"
        elif status == "delivered" and verdict == "approved":
            gate = "file_evidence_gate" if evidence_keys else "quality_gate"
            gate_status = "review_passed"
            next_action = "batch_closeout_or_subject_closeout"
        else:
            gate = "stale_state_reconciliation"
            gate_status = status or "unknown"
            next_action = "reconcile_task_state"

    return {
        "workflow_id": workflow_id,
        "gate": gate,
        "gate_status": gate_status,
        "status": status,
        "verdict": verdict,
        "reviewer": reviewer,
        "default_reviewer": default_reviewer,
        "evidence_keys": evidence_keys,
        "closeout_status": closeout_status,
        "revision_priority": revision_priority,
        "next_action": next_action,
    }


def _evidence_has_required_packet(evidence: dict) -> bool:
    if not isinstance(evidence, dict) or not evidence:
        return False
    return any(bool(evidence.get(key)) for key in REVIEW_EVIDENCE_FIELDS)


def _subject_counts(task: dict) -> tuple[int, int]:
    evidence = task.get("evidence_packet") or {}
    qa_count = int(evidence.get("qa_count") or evidence.get("items_mapping_count") or 0)
    item_count = int(evidence.get("item_count") or evidence.get("items_mapping_count") or 0)
    return qa_count, item_count


def _qa_standard_status(qa_count: int, item_count: int) -> str:
    if qa_count <= 0 or item_count <= 0:
        return "qa_standard_missing_counts"
    if qa_count < SUBJECT_QA_STANDARD["qa_min"] or item_count < SUBJECT_QA_STANDARD["item_min"]:
        return "qa_standard_low_volume"
    if qa_count > SUBJECT_QA_STANDARD["qa_max"] or item_count > SUBJECT_QA_STANDARD["item_max"]:
        return "qa_standard_high_volume"
    return "qa_standard_met"


def _qbank_readiness_status(evidence: dict, qa_standard: str) -> str:
    if qa_standard in {"qa_standard_low_volume", "qa_standard_high_volume", "qa_standard_missing_counts"}:
        return "qbank_blocked_low_volume"
    explicit = str(evidence.get("qbank_readiness") or "").strip()
    if explicit in QBANK_READINESS_VALUES:
        return explicit
    if int(evidence.get("missing_topic_count") or 0) > 0 or not _normalize_list(evidence.get("q_ids_checked")):
        return "qbank_blocked_missing_mapping"
    if not _normalize_list(evidence.get("calculation_or_concept_checks")):
        return "qbank_blocked_missing_question_directions"
    return "qbank_review_needed"


def _qbank_recommended_action(qbank_readiness: str) -> str:
    if qbank_readiness == "qbank_ready":
        return "approve_subject_for_qbank_seed"
    if qbank_readiness == "qbank_blocked_low_volume":
        return "request_worker_course_expand_qa"
    if qbank_readiness == "qbank_blocked_missing_mapping":
        return "request_review_course_file_evidence"
    if qbank_readiness in {"qbank_blocked_missing_question_directions", "qbank_review_needed"}:
        return "request_qbank_readiness_check"
    return "request_qbank_readiness_check"


def _outline_topic_count(task: dict) -> int:
    """Count of outline topics from evidence_packet.sampled_topic_count."""
    evidence = task.get("evidence_packet") or {}
    return int(evidence.get("sampled_topic_count") or 0)


def _manifest_covered_count(task: dict) -> int:
    """Count of manifest-covered items from evidence_packet.items_mapping_count."""
    evidence = task.get("evidence_packet") or {}
    return int(evidence.get("items_mapping_count") or 0)


def subject_closeout_status(task: dict | None) -> dict:
    """Derived subject-level closeout gate for manager-facing surfaces.

    Package 3: `closeout_gate_review_approved` is now driven by
    `is_verdict_authoritative_for_closeout()` rather than the static
    `task.verdict` field. This means a QQL-only PASS or items-only PASS
    cannot satisfy the gate, and a stale approve verdict that was
    followed by a later reject (now stored in `latest_authoritative_verdict`)
    is correctly recognized as a block.
    """
    task = task or {}
    strict_account = (
        task_evidence_account.requires_strict_account(task)
        and str(task.get("status") or "") == "delivered"
        and str(task.get("verdict") or "") == "approved"
    )
    if (
        task.get("schema_version") != 2
        or canonical_stage(str(task.get("stage") or "")) != "curriculum"
        or (
            str(task.get("closeout_status") or "") != "closeout_completed"
            and not _has_subject_closeout_signal(task)
            and not strict_account
        )
    ):
        return {
            "subject_id": str(task.get("id") or ""),
            "subject_name": str(task.get("title") or ""),
            "qa_count": 0,
            "item_count": 0,
            "outline_topic_count": 0,
            "manifest_covered_count": 0,
            "review_status": "not_subject",
            "qa_min": SUBJECT_QA_STANDARD["qa_min"],
            "qa_max": SUBJECT_QA_STANDARD["qa_max"],
            "item_min": SUBJECT_QA_STANDARD["item_min"],
            "item_max": SUBJECT_QA_STANDARD["item_max"],
            "qa_standard": "not_subject",
            "qbank_readiness": "qbank_review_needed",
            "recommended_qbank_action": "request_qbank_readiness_check",
            "closeout_status": "not_subject",
            "recommended_action": "no_action",
            "next_action": "no_action",
            "closeout_gate_review_approved": False,
            "closeout_gate_evidence_present": False,
            "closeout_gate_qa_standard_met": False,
            "closeout_gate_qbank_ready": False,
            "verdict_scope": "",
            "verdict_authority_reasons": ["not_subject"],
            "evidence_account": task_evidence_account.build_evidence_account(task),
        }
    qa_count, item_count = _subject_counts(task)
    evidence = task.get("evidence_packet") or {}
    qa_standard = _qa_standard_status(qa_count, item_count)
    qbank_readiness = _qbank_readiness_status(evidence, qa_standard)
    recommended_qbank_action = _qbank_recommended_action(qbank_readiness)
    verdict = str(task.get("verdict") or "")
    persisted = str(task.get("closeout_status") or "")
    # Package 3: read the structured verdict authority instead of the
    # static verdict field. The latest_authoritative_verdict carries
    # the reviewer's actual scope, so a QQL-only PASS no longer
    # accidentally clears the subject closeout gate.
    review_authority_ok = is_verdict_authoritative_for_closeout(task)
    latest = task.get("latest_authoritative_verdict") or {}
    verdict_scope = str(latest.get("verdict_scope") or task.get("verdict_scope") or "")
    blocks, block_reasons = latest_verdict_blocks_closeout(task)
    # Package 3 (Codex review MEDIUM #3): do NOT promote legacy
    # approved tasks without `verdict_target` to `full_subject`. The
    # reviewer MUST explicitly declare the scope; the closeout gate
    # must surface a `missing_verdict_target_on_approved_task` reason
    # so manager-actions / manager-panel explain why the verdict
    # isn't authoritative, instead of silently claiming full_subject
    # coverage.
    if persisted == "closeout_completed":
        closeout_status = "closeout_completed"
        recommended_action = "select_next_subject_from_inventory"
    elif blocks:
        closeout_status = "closeout_blocked_review_not_approved"
        # Pick the most specific recommendation.
        if any("verdict_scope_insufficient" in r for r in block_reasons):
            recommended_action = "request_full_subject_review_recheck"
        elif "latest_verdict_rejected" in block_reasons:
            recommended_action = "wait_for_worker_repair_and_re_review"
        elif "latest_verdict_manager_action" in block_reasons:
            recommended_action = "resolve_manager_action_then_re_review"
        else:
            recommended_action = "wait_for_review_approval"
    elif not review_authority_ok:
        closeout_status = "closeout_blocked_review_not_approved"
        if verdict == "approved" and not verdict_scope:
            # Stale approved verdict with no scope declared.
            recommended_action = "request_verdict_target_for_existing_pass"
        else:
            recommended_action = "wait_for_review_approval"
    elif not _evidence_has_required_packet(task.get("evidence_packet") or {}):
        closeout_status = "closeout_blocked_missing_evidence"
        recommended_action = "request_review_evidence_packet"
    elif qa_standard == "qa_standard_missing_counts":
        closeout_status = (
            "evidence_account_incomplete"
            if strict_account
            else "review_passed_waiting_closeout"
        )
        recommended_action = "request_subject_count_evidence"
    elif qa_standard != "qa_standard_met":
        closeout_status = "closeout_blocked_count_out_of_range"
        recommended_action = (
            "request_worker_course_expand_qa"
            if qa_standard == "qa_standard_low_volume"
            else "block_closeout_until_quality_standard_met"
        )
    else:
        closeout_status = "closeout_ready"
        recommended_action = "manager_formal_closeout"
    outline_topics = _outline_topic_count(task)
    manifest_covered = _manifest_covered_count(task)
    preliminary = {
        "closeout_status": closeout_status,
        "recommended_action": recommended_action,
    }
    account = task_evidence_account.build_evidence_account(
        task,
        closeout_status=preliminary,
    )
    if (
        closeout_status == "closeout_ready"
        and strict_account
        and not account["closeout_ready"]
    ):
        if account["conflicting_evidence"]:
            closeout_status = "evidence_account_conflict"
            recommended_action = "resolve_evidence_account_conflict"
        else:
            closeout_status = "evidence_account_incomplete"
            recommended_action = "complete_closeout_evidence_account"
        account = dict(account)
        account["closeout_status"] = closeout_status
        account["recommended_action"] = recommended_action
        account["closeout_ready"] = False
    next_action = _derive_next_action(
        closeout_status=closeout_status,
        recommended_action=recommended_action,
        qa_count=qa_count,
        item_count=item_count,
        outline_topics=outline_topics,
        manifest_covered=manifest_covered,
    )
    tier_status = _derive_tier_status(
        task=task,
        closeout_status=closeout_status,
        qa_standard=qa_standard,
        qbank_readiness=qbank_readiness,
        review_authority_ok=review_authority_ok,
        verdict_scope=verdict_scope,
    )
    return {
        "subject_id": str(task.get("id") or ""),
        "subject_name": str(task.get("title") or ""),
        "qa_count": qa_count,
        "item_count": item_count,
        "outline_topic_count": outline_topics,
        "manifest_covered_count": manifest_covered,
        "qa_min": SUBJECT_QA_STANDARD["qa_min"],
        "qa_max": SUBJECT_QA_STANDARD["qa_max"],
        "item_min": SUBJECT_QA_STANDARD["item_min"],
        "item_max": SUBJECT_QA_STANDARD["item_max"],
        "qa_standard": qa_standard,
        "qbank_readiness": qbank_readiness,
        "recommended_qbank_action": recommended_qbank_action,
        "review_status": "approved" if verdict == "approved" else "not_approved",
        "closeout_status": closeout_status,
        "tier_status": tier_status,
        "closeout_completed_at": int(task.get("manager_closed_out_at") or 0),
        "next_candidate_rank": 0,
        "recommended_action": recommended_action,
        "next_action": next_action,
        "closeout_gate_review_approved": review_authority_ok,
        "closeout_gate_evidence_present": _evidence_has_required_packet(evidence),
        "closeout_gate_qa_standard_met": qa_standard == "qa_standard_met",
        "closeout_gate_qbank_ready": qbank_readiness == "qbank_ready",
        "verdict_scope": verdict_scope,
        "verdict_authority_reasons": block_reasons,
        "latest_authoritative_verdict": latest,
        "evidence_account": account,
        "missing_evidence": account.get("missing_evidence", []),
        "conflicting_evidence": account.get("conflicting_evidence", []),
        "closeout_ready": bool(account.get("closeout_ready")),
    }


def _derive_tier_status(task: dict,
                        closeout_status: str,
                        qa_standard: str,
                        qbank_readiness: str,
                        review_authority_ok: bool,
                        verdict_scope: str) -> str:
    """Map current evidence to one of the four closeout tiers.

    The tiers form a progression:
        unit_seed_ready < unit_package_ready < subject_sample_ready
        < qbank_agent_ready < closeout_completed
    """
    if closeout_status == "closeout_completed":
        return "closeout_completed"

    verdict = str(task.get("verdict") or "")
    package_scope = is_package_scope(task)
    approved = verdict == "approved" and review_authority_ok

    if approved:
        if qbank_readiness == "qbank_ready" and verdict_scope == "full_subject":
            return "qbank_agent_ready"
        if verdict_scope == "full_subject":
            return "subject_sample_ready"
        if package_scope or verdict_scope in {"unit", "package"}:
            return "unit_package_ready"

    # Not yet approved or counts insufficient for full subject.
    if qa_standard == "qa_standard_met":
        return "unit_package_ready"
    return "unit_seed_ready"


def subject_inventory() -> list[dict]:
    """Compatibility inventory API used by pre-package-6 callers.

    Keep this as the stable public entry point while package-6 callers can
    explicitly ask for the extended inventory. Both return the same row shape
    so tier/evidence-account fields do not drift between manager surfaces.
    """
    return subject_inventory_extended()


def subject_inventory_extended() -> list[dict]:
    """Return subject inventory that includes IGCSE course tasks even
    without completion markers, for use by manager continuation logic."""
    rows = [
        task for task in _load().get("tasks", [])
        if task.get("schema_version") == 2 and canonical_stage(str(task.get("stage") or "")) == "curriculum"
    ]
    rows.sort(key=lambda t: int(t["id"].split("-")[1]) if "-" in t["id"] else 0)
    inventory = []
    for task in rows:
        row = _subject_inventory_row(task)
        inventory.append(row)
    rank = 1
    for row in inventory:
        if row["closeout_status"] == "closeout_completed":
            continue
        row["next_candidate_rank"] = rank
        rank += 1
    return inventory


def _subject_inventory_row(task: dict) -> dict:
    """Build a subject inventory row, always including outline/manifest counts.

    For IGCSE-titled tasks that would return 'not_subject' from the standard
    closeout gate, we still report basic progress info with 'no_closeout_signal'
    status so the manager can see all subjects in the pipeline.
    """
    title = str(task.get("title") or "")
    stage = str(task.get("stage") or "")

    # Use standard closeout gate first
    gate = subject_closeout_status(task)

    # If it returned not_subject but is an IGCSE task, provide extended info
    if gate.get("closeout_status") == "not_subject" and is_igcse_course_task(title=title, stage=stage):
        evidence = task.get("evidence_packet") or {}
        qa_count, item_count = _subject_counts(task)
        outline_topics = _outline_topic_count(task)
        manifest_covered = _manifest_covered_count(task)
        status = str(task.get("status") or "")
        verdict = str(task.get("verdict") or "")
        closeout = str(task.get("closeout_status") or "")

        # Determine next_action based on task state
        if closeout:
            next_action = _derive_next_action(
                closeout_status=closeout,
                recommended_action="no_action",
                qa_count=qa_count,
                item_count=item_count,
                outline_topics=outline_topics,
                manifest_covered=manifest_covered,
            )
        elif status in {"submitted_for_review", "in_progress", "assigned", "queued"}:
            next_action = "continue_current_subject_work"
        elif status == "delivered" and verdict == "approved" and qa_count < SUBJECT_QA_STANDARD["qa_min"]:
            next_action = "continue_next_batch"
        elif status == "delivered" and verdict == "approved":
            next_action = "request_evidence_for_closeout"
        else:
            next_action = "monitor_subject_progress"

        return {
            "subject_id": str(task.get("id") or ""),
            "subject_name": title,
            "subject_slug": extract_subject_slug(title),
            "subject_code": extract_subject_code(title),
            "subject_label": extract_subject_label(title),
            "qa_count": qa_count,
            "item_count": item_count,
            "outline_topic_count": outline_topics,
            "manifest_covered_count": manifest_covered,
            "qa_min": SUBJECT_QA_STANDARD["qa_min"],
            "qa_max": SUBJECT_QA_STANDARD["qa_max"],
            "item_min": SUBJECT_QA_STANDARD["item_min"],
            "item_max": SUBJECT_QA_STANDARD["item_max"],
            "qa_standard": _qa_standard_status(qa_count, item_count),
            "qbank_readiness": "",
            "recommended_qbank_action": "qbank_review_needed",
            "review_status": "pending" if verdict != "approved" else "approved",
            "closeout_status": closeout if closeout else "no_closeout_signal",
            "closeout_completed_at": int(task.get("manager_closed_out_at") or 0),
            "next_candidate_rank": 0,
            "recommended_action": "monitor_subject_progress",
            "next_action": next_action,
            "closeout_gate_review_approved": verdict == "approved",
            "closeout_gate_evidence_present": _evidence_has_required_packet(evidence),
            "closeout_gate_qa_standard_met": False,
            "closeout_gate_qbank_ready": False,
        }

    return gate


def _derive_next_action(
    *,
    closeout_status: str,
    recommended_action: str,
    qa_count: int,
    item_count: int,
    outline_topics: int,
    manifest_covered: int,
) -> str:
    """Derive a concise next_action label for manager-facing surfaces."""
    if closeout_status == "closeout_completed":
        return "select_next_subject"
    if closeout_status == "closeout_ready":
        return "manager_formal_closeout"
    if closeout_status in {
        "closeout_blocked_review_not_approved",
        "closeout_blocked_missing_evidence",
        "closeout_blocked_count_out_of_range",
        "evidence_account_incomplete",
        "evidence_account_conflict",
    }:
        return recommended_action
    if closeout_status == "review_passed_waiting_closeout":
        return "request_subject_count_evidence"
    if closeout_status in {"evidence_account_incomplete", "evidence_account_conflict"}:
        return recommended_action
    # Default for non-subject or unknown state
    return "no_action"


def next_batch_continuation_gate(task_id: str) -> dict:
    """Check whether a subject should continue with the next batch.

    Returns a recommendation dict with:
      - should_continue: bool
      - reason: explanation string
      - subject_id: the subject task id
      - recommended_action: what the manager should do next
      - coverage: current progress info
      - evidence_path: audit trail
      - p0_blocking: true if manager has unread high-priority inbox items
    """
    task = get(task_id)
    if task is None:
        return {
            "should_continue": False,
            "reason": "task_not_found",
            "subject_id": task_id,
            "recommended_action": "no_action",
            "coverage": {},
            "evidence_path": [],
            "p0_blocking": False,
        }
    if task.get("schema_version") != 2:
        return {
            "should_continue": False,
            "reason": "not_flow_task",
            "subject_id": task_id,
            "recommended_action": "no_action",
            "coverage": {},
            "evidence_path": [],
            "p0_blocking": False,
        }
    # Package 7 (Revision-First Gate): if any active flow task in this
    # workflow still has revision_priority set, hold the continuation
    # recommendation until the revision is explicitly cleared.
    workflow_id = str(task.get("workflow_id") or "").strip()
    if workflow_id and has_active_revision_priority(workflow_id):
        return {
            "should_continue": False,
            "reason": "revision_priority_active_hold_continuation",
            "subject_id": task_id,
            "recommended_action": "clear_revision_priority_before_continue_next_batch",
            "coverage": {},
            "evidence_path": ["revision_priority_active=true"],
            "p0_blocking": False,
        }
    if canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return {
            "should_continue": False,
            "reason": "not_subject",
            "subject_id": task_id,
            "recommended_action": "no_action",
            "coverage": {},
            "evidence_path": [],
            "p0_blocking": False,
        }

    # Check P0 manager inbox blocking before making continuation recommendation
    p0_blocking = _has_p0_manager_inbox_blocking()

    gate = subject_closeout_status(task)
    closeout_status = gate["closeout_status"]
    qa_count = gate["qa_count"]
    item_count = gate["item_count"]
    outline_topics = gate.get("outline_topic_count", 0)
    manifest_covered = gate.get("manifest_covered_count", 0)

    if closeout_status == "closeout_completed":
        return {
            "should_continue": False,
            "reason": "subject_closeout_completed",
            "subject_id": task_id,
            "recommended_action": "select_next_subject",
            "coverage": {
                "qa_count": qa_count,
                "item_count": item_count,
                "outline_topic_count": outline_topics,
                "manifest_covered_count": manifest_covered,
                "subject_slug": extract_subject_slug(str(task.get("title") or "")),
                "subject_code": extract_subject_code(str(task.get("title") or "")),
            },
            "evidence_path": [f"closeout_status={closeout_status}"],
            "p0_blocking": p0_blocking,
        }

    status = str(task.get("status") or "")
    verdict = str(task.get("verdict") or "")

    if p0_blocking:
        return {
            "should_continue": False,
            "reason": "p0_inbox_blocking_hold_continuation",
            "subject_id": task_id,
            "recommended_action": "consume_high_priority_inbox_first",
            "coverage": {
                "qa_count": qa_count,
                "item_count": item_count,
                "outline_topic_count": outline_topics,
                "manifest_covered_count": manifest_covered,
                "subject_slug": extract_subject_slug(str(task.get("title") or "")),
                "subject_code": extract_subject_code(str(task.get("title") or "")),
            },
            "evidence_path": [
                f"status={status}",
                f"verdict={verdict}",
                f"closeout_status={closeout_status}",
                "p0_inbox_blocking=true",
            ],
            "p0_blocking": True,
        }

    # If the batch was delivered but subject not yet closeout_completed,
    # recommend continuing next batch
    if status == "delivered" and verdict == "approved":
        if gate.get("closeout_status") in {
            "closeout_ready",
            "review_passed_waiting_closeout",
        }:
            # Subject might be complete — let manager decide
            return {
                "should_continue": False,
                "reason": "subject_may_be_complete_review_closeout",
                "subject_id": task_id,
                "recommended_action": gate["recommended_action"],
                "coverage": {
                    "qa_count": qa_count,
                    "item_count": item_count,
                    "outline_topic_count": outline_topics,
                    "manifest_covered_count": manifest_covered,
                    "subject_slug": extract_subject_slug(str(task.get("title") or "")),
                    "subject_code": extract_subject_code(str(task.get("title") or "")),
                },
                "evidence_path": [
                    f"status={status}",
                    f"verdict={verdict}",
                    f"closeout_status={closeout_status}",
                ],
                "p0_blocking": p0_blocking,
            }
        # Subject is incomplete (counts below threshold, or batch-level closeout)
        return {
            "should_continue": True,
            "reason": "latest_batch_delivered_subject_incomplete",
            "subject_id": task_id,
            "recommended_action": "continue_next_batch",
            "coverage": {
                "qa_count": qa_count,
                "item_count": item_count,
                "outline_topic_count": outline_topics,
                "manifest_covered_count": manifest_covered,
                "qa_standard": gate.get("qa_standard", ""),
                "subject_slug": extract_subject_slug(str(task.get("title") or "")),
                "subject_code": extract_subject_code(str(task.get("title") or "")),
            },
            "evidence_path": [
                f"status={status}",
                f"verdict={verdict}",
                f"closeout_status={closeout_status}",
                f"qa_count={qa_count}",
                f"item_count={item_count}",
            ],
            "p0_blocking": p0_blocking,
        }

    return {
        "should_continue": False,
        "reason": "subject_not_ready_for_continuation",
        "subject_id": task_id,
        "recommended_action": "wait_for_current_batch_progress",
        "coverage": {
            "qa_count": qa_count,
            "item_count": item_count,
            "outline_topic_count": outline_topics,
            "manifest_covered_count": manifest_covered,
            "subject_slug": extract_subject_slug(str(task.get("title") or "")),
            "subject_code": extract_subject_code(str(task.get("title") or "")),
        },
        "evidence_path": [
            f"status={status}",
            f"verdict={verdict}",
            f"closeout_status={closeout_status}",
        ],
        "p0_blocking": p0_blocking,
    }


def _has_p0_manager_inbox_blocking() -> bool:
    """Check whether manager has unread high-priority inbox items.

    If true, continuation recommendations should be held until inbox is consumed.
    Uses lazy import to avoid circular dependency at module load time.
    """
    try:
        from eduflow.store.local_facts import list_messages, is_high_priority
        messages = list_messages("manager", unread_only=True)
        return any(
            is_high_priority(str(m.get("priority") or ""))
            for m in messages
        )
    except Exception:
        return False


def select_next_subject(*, exclude_recent_count: int = 1) -> dict | None:
    """Select the next subject candidate from the extended inventory.

    Uses subject_inventory_extended() to include IGCSE tasks without closeout
    signals, so the manager always has visibility into pipeline candidates.
    """
    inventory = subject_inventory_extended()
    if not inventory:
        return None

    # Filter out completed subjects
    candidates = [
        row for row in inventory
        if row["closeout_status"] != "closeout_completed"
    ]
    if not candidates:
        return None

    # Package 7 (Revision-First Gate): if any active flow task in the
    # IGCSE subject-launch workflow still has revision_priority set,
    # do not recommend rolling to the next subject — the worker has
    # unfinished revision work to acknowledge first.
    if has_active_revision_priority(IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID):
        return None

    # Identify recently active subjects (most recently updated, in_progress)
    all_tasks = _load().get("tasks", [])
    recent_subject_slugs = _recently_active_subject_ids(
        all_tasks, limit=exclude_recent_count,
    )

    # Separate into two tiers: with assets vs empty
    with_assets = []
    empty = []
    for row in candidates:
        has_evidence = (
            row.get("qa_count", 0) > 0
            or row.get("item_count", 0) > 0
            or row.get("manifest_covered_count", 0) > 0
        )
        if has_evidence:
            with_assets.append(row)
        else:
            empty.append(row)

    # Prefer with_assets tier, deprioritize recently active (by slug, not task ID)
    def _sort_key(row):
        slug = row.get("subject_slug", "")
        is_recent = slug in recent_subject_slugs
        rank = row.get("next_candidate_rank", 999)
        return (is_recent, rank)

    with_assets.sort(key=_sort_key)
    empty.sort(key=_sort_key)

    # Pick from with_assets first, then empty
    ordered = with_assets + empty
    selected = ordered[0] if ordered else None
    if selected is None:
        return None

    # Build audit trail
    skipped = []
    with_assets_ids = {r["subject_id"] for r in with_assets}
    for row in inventory:
        if row.get("subject_id") == selected["subject_id"]:
            continue
        slug = row.get("subject_slug", "")
        reason_parts = []
        if row["closeout_status"] == "closeout_completed":
            reason_parts.append("closeout_completed")
        else:
            if slug and slug in recent_subject_slugs:
                reason_parts.append("same_subject_recently_active")
            if row["subject_id"] not in with_assets_ids:
                reason_parts.append("no_assets_empty_subject")
            if not reason_parts:
                reason_parts.append("lower_priority_same_tier")
        skipped.append({
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "subject_slug": slug,
            "subject_code": row.get("subject_code", ""),
            "closeout_status": row.get("closeout_status", ""),
            "reason": " + ".join(reason_parts) if reason_parts else "unknown",
            "has_assets": row["subject_id"] in with_assets_ids,
        })

    return {
        "subject_id": selected["subject_id"],
        "subject_name": selected["subject_name"],
        "closeout_status": selected["closeout_status"],
        "next_candidate_rank": selected["next_candidate_rank"],
        "qa_count": selected["qa_count"],
        "item_count": selected["item_count"],
        "outline_topic_count": selected.get("outline_topic_count", 0),
        "manifest_covered_count": selected.get("manifest_covered_count", 0),
        "reason": _selection_reason(selected, with_assets, recent_subject_slugs),
        "selected": {
            "subject_id": selected["subject_id"],
            "subject_name": selected["subject_name"],
            "subject_slug": selected.get("subject_slug", ""),
            "subject_code": selected.get("subject_code", ""),
            "subject_label": selected.get("subject_label", ""),
            "has_assets": selected["subject_id"] in {r["subject_id"] for r in with_assets},
        },
        "skipped": skipped,
        "recommended_action": "dispatch_next_subject_worker_course",
    }


def _recently_active_subject_ids(all_tasks: list[dict], *, limit: int = 1) -> set[str]:
    """Return subject SLUGS that are currently in_progress (actively being worked on).

    Uses extract_subject_slug() to normalize across batches of the same subject.
    "IGCSE Physics 0625 Batch 3" and "IGCSE Physics 0625 Batch 1" share the
    same slug (igcse-physics-0625), so Physics won't be selected as next
    subject while Physics is already being worked on.
    """
    curriculum_tasks = [
        t for t in all_tasks
        if t.get("schema_version") == 2
        and canonical_stage(str(t.get("stage") or "")) == "curriculum"
        and str(t.get("status") or "") == "in_progress"
    ]
    # Deduplicate by subject_slug first, keep most recent per slug
    slug_map: dict[str, dict] = {}
    for t in curriculum_tasks:
        slug = extract_subject_slug(str(t.get("title") or ""))
        if not slug:
            continue
        existing = slug_map.get(slug)
        if existing is None:
            slug_map[slug] = t
        else:
            existing_at = int(existing.get("last_meaningful_update_at") or existing.get("updated_at") or 0)
            current_at = int(t.get("last_meaningful_update_at") or t.get("updated_at") or 0)
            if current_at > existing_at:
                slug_map[slug] = t

    # Sort deduplicated tasks by most recent activity
    deduped = list(slug_map.values())
    deduped.sort(
        key=lambda t: (
            -int(t.get("last_meaningful_update_at") or t.get("updated_at") or 0),
            -int(t["id"].split("-")[1]) if "-" in t.get("id", "") else 0,
        ),
    )
    recent = set()
    for t in deduped[:limit]:
        slug = extract_subject_slug(str(t.get("title") or ""))
        if slug:
            recent.add(slug)
    return recent


def _selection_reason(selected: dict, with_assets: list[dict], recent_slugs: set[str]) -> str:
    """Generate a human-readable selection reason explaining tier and recency."""
    slug = selected.get("subject_slug", "")
    has_assets = selected["subject_id"] in {r["subject_id"] for r in with_assets}
    is_recent = slug in recent_slugs
    if has_assets and not is_recent:
        return "has_assets_not_recently_active"
    if has_assets and is_recent:
        return "has_assets_but_recently_active_fallback"
    if not has_assets and not is_recent:
        return "no_assets_first_available_candidate"
    if not has_assets and is_recent:
        return "no_assets_recently_active_last_resort"
    return "fallback_only_candidate"


# ── revision_priority (Package 7: Revision-First Gate) ─────────────


def set_revision_priority(task_id: str, value: str, *, reason: str = "",
                          actor: str = "") -> bool:
    """Set revision_priority on a flow task.

    The field is sticky: it is cleared only by an explicit call to
    clear_revision_priority(). status changes do not auto-clear it.
    Allowed values: "minor", "manager", "user", or "" (clear).
    Returns True if the task was updated, False if not found.
    """
    normalized = str(value or "").strip()
    if normalized and normalized not in _FLOW_REVISION_PRIORITIES:
        raise ValueError(
            f"invalid revision_priority: {normalized} "
            f"(valid: {sorted(_FLOW_REVISION_PRIORITIES)})"
        )
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        task["revision_priority"] = normalized
        if normalized:
            task["revision_priority_set_at"] = now_ms()
        else:
            task["revision_priority_set_at"] = None
        task["updated_at"] = now_ms()
        task["last_meaningful_update_at"] = task["updated_at"]
        if reason:
            task["latest_turn_summary"] = str(reason).strip()[:240]
        if normalized:
            try:
                from eduflow.memory.derivation import on_revision_priority_set
                on_revision_priority_set(task_id, normalized, reason=reason, actor=actor)
            except Exception:
                pass
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor or "manager",
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
        return True


def clear_revision_priority(task_id: str, *, actor: str = "") -> bool:
    """Explicitly clear revision_priority on a flow task.

    This is the only path that clears the field. Status changes do not
    auto-clear revision_priority — the owner/manager must acknowledge
    the revision before the task returns to normal flow.
    Returns True if the task was updated, False if not found.
    """
    return set_revision_priority(task_id, "", actor=actor)


def has_active_revision_priority(workflow_id: str = "") -> bool:
    """Return True when any active flow task in this workflow still has
    revision_priority set (i.e. the revision has not been acknowledged).

    Pass empty `workflow_id` to query across all active flow tasks.
    """
    target_wf = str(workflow_id or "").strip()
    for task in _load().get("tasks", []):
        if task.get("schema_version") != 2:
            continue
        if str(task.get("status") or "") in FLOW_TERMINAL_STATUSES:
            continue
        if target_wf:
            if str(task.get("workflow_id") or "").strip() != target_wf:
                continue
        if str(task.get("revision_priority") or "").strip():
            return True
    return False


def _find_task(data: dict, task_id: str) -> dict | None:
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def _effective_flow_actor(task: dict, actor: str) -> str:
    if actor in {"manager", "worker", "reviewer"}:
        return actor
    if actor and actor == task.get("owner"):
        return "worker"
    reviewer = str(task.get("reviewer") or "").strip()
    if actor and reviewer and actor == reviewer:
        return "reviewer"
    return actor


def _apply_flow_transition(task: dict, *, to_status: str, actor: str) -> None:
    _ensure_flow_semantic_defaults(task)
    stage = canonical_stage(task.get("stage", ""))
    current = task.get("status", "")
    _validate_flow_stage_status(stage, to_status)
    allowed = FLOW_TRANSITIONS.get(current, {})
    if to_status not in allowed:
        raise ValueError(f"illegal status transition: {current} -> {to_status}")
    allowed_actors = allowed[to_status]
    effective_actor = _effective_flow_actor(task, actor)
    if (
        to_status == "delivered"
        and canonical_stage(str(task.get("stage") or "")) in REVIEW_REQUIRED_STAGES
        and effective_actor != "reviewer"
    ):
        raise ValueError(
            f"actor {actor!r} cannot bypass review verdict before manager closeout "
            f"for stage {task.get('stage')}"
        )
    if effective_actor not in allowed_actors:
        raise ValueError(
            f"actor {actor!r} cannot transition {current} -> {to_status} "
            f"(allowed: {sorted(allowed_actors)})"
        )
    task["status"] = to_status
    if to_status == "submitted_for_review":
        task["verdict"] = "pending"
        task["blocking_reason"] = ""
        task["manager_action_type"] = ""
        task["review_reason"] = ""
    elif to_status == "delivered":
        task["verdict"] = "approved"
        task["blocking_reason"] = ""
        task["manager_action_type"] = ""
        task["review_reason"] = "approved_for_delivery"
    elif to_status == "blocked":
        if not str(task.get("blocking_reason") or "").strip():
            effective_actor = _effective_flow_actor(task, actor)
            if effective_actor == "reviewer":
                task["blocking_reason"] = "review_blocked"
            elif effective_actor == "manager":
                task["blocking_reason"] = "manager_blocked"
            else:
                task["blocking_reason"] = "worker_blocked"
    elif to_status != "blocked":
        task["blocking_reason"] = ""
        task["manager_action_type"] = ""
    # Retry from `failed` → `in_progress` (manager retry): clear
    # failure_reason so subsequent reviewers don't conflate the
    # stale failure with the new attempt. Also append a marker to
    # the default turn summary explaining that this is a retry.
    # Set this BEFORE the default-summary line below so the retry
    # marker survives the assignment.
    if current == "failed" and to_status == "in_progress":
        old_failure_reason = str(task.get("failure_reason") or "").strip()
        task["failure_reason"] = ""
        # Stash a retry note in a temporary field; the default
        # summary line below will read it and append.
        if old_failure_reason:
            task["_retry_failure_note"] = (
                f"Manager retried from failed state. Previous "
                f"failure_reason: {old_failure_reason[:100]}"
            )
        else:
            task["_retry_failure_note"] = "Manager retried from failed state."
    task["needs_manager_action"] = _flow_needs_manager_action(
        to_status,
        str(task.get("verdict") or ""),
    )
    task["completed_at"] = _flow_completed_at(to_status)
    base_summary = _default_turn_summary(status=to_status, actor=actor)
    retry_note = task.pop("_retry_failure_note", None)
    if retry_note:
        task["latest_turn_summary"] = f"{base_summary} [{retry_note}]"
    else:
        task["latest_turn_summary"] = base_summary
    task["updated_at"] = now_ms()
    task["last_meaningful_update_at"] = task["updated_at"]


def _apply_flow_review(task: dict, *, task_id: str = "",
                       outcome: str, actor: str,
                       review_reason: str = "",
                       latest_turn_summary: str = "",
                       manager_action_type: str = "",
                       scope_topic: str = "",
                       scope_files=None,
                       verdict_target: str = "",
                       evidence_packet=None,
                       required_fix=None,
                       blocking_files=None) -> None:
    _ensure_flow_semantic_defaults(task)
    if outcome not in FLOW_REVIEW_OUTCOMES:
        raise ValueError(
            f"invalid review outcome: {outcome} "
            f"(valid: {sorted(FLOW_REVIEW_OUTCOMES)})"
        )
    if task.get("status") != "submitted_for_review":
        raise ValueError(
            f"review requires submitted_for_review status "
            f"(got: {task.get('status')})"
        )
    assigned_reviewer = str(task.get("reviewer") or "").strip()
    if assigned_reviewer and actor != assigned_reviewer:
        raise ValueError(
            f"actor {actor!r} is not the assigned reviewer "
            f"(assigned reviewer: {assigned_reviewer!r})"
        )
    normalized_manager_action_type = _normalize_manager_action_type(manager_action_type)
    normalized_review_reason = _normalize_review_reason(review_reason)
    if outcome != "manager_action" and normalized_manager_action_type:
        raise ValueError(
            "manager_action_type is only allowed for manager_action outcome"
        )
    to_status, verdict = FLOW_REVIEW_TRANSITIONS[outcome]
    _apply_flow_transition(task, to_status=to_status, actor=actor)
    task["verdict"] = verdict
    task["needs_manager_action"] = _flow_needs_manager_action(to_status, verdict)
    task["manager_action_type"] = ""
    if outcome == "manager_action":
        task["blocking_reason"] = "reviewer_requested_manager_action"
        task["manager_action_type"] = (
            normalized_manager_action_type or _DEFAULT_MANAGER_ACTION_TYPE
        )
        task["review_reason"] = (
            normalized_review_reason or _DEFAULT_REVIEW_REASON_BY_OUTCOME[outcome]
        )
    else:
        task["blocking_reason"] = ""
        task["review_reason"] = normalized_review_reason or _DEFAULT_REVIEW_REASON_BY_OUTCOME[outcome]
    task["latest_turn_summary"] = (
        latest_turn_summary.strip()
        or _default_turn_summary(status=to_status, actor=actor, outcome=outcome)
    )
    if outcome == "reject":
        task["revision_priority"] = "minor"
        task["revision_priority_set_at"] = now_ms()
    elif outcome == "manager_action":
        task["revision_priority"] = "manager"
        task["revision_priority_set_at"] = now_ms()
    if task_id and task.get("revision_priority"):
        try:
            from eduflow.memory.derivation import on_revision_priority_set
            on_revision_priority_set(task_id, task["revision_priority"], actor=actor)
        except Exception:
            pass
    task["scope_topic"] = str(scope_topic or task.get("scope_topic") or "").strip()
    task["scope_files"] = _normalize_list(scope_files if scope_files is not None else task.get("scope_files"))
    target_text = str(verdict_target or task.get("verdict_target") or "").strip()
    task["verdict_target"] = target_text
    task["verdict_scope"] = derive_verdict_scope_from_target(target_text)
    evidence = _normalize_evidence_packet(
        evidence_packet if evidence_packet is not None else task.get("evidence_packet")
    )
    task["evidence_packet"] = evidence
    # Package 3: also persist a snapshot of the file-level evidence so
    # later closeout attempts can detect drift (worker may have changed
    # files after the verdict was issued).
    snapshot = {
        key: evidence.get(key)
        for key in ("files_sampled", "q_ids_checked", "qa_count", "item_count")
        if evidence.get(key)
    }
    task["evidence_snapshot"] = snapshot
    task["evidence_snapshot_hash"] = evidence_snapshot_hash(evidence)
    # Package 3: persist the reviewer's required_fix / blocking_files.
    # These survive even on reject / manager_action so the worker has
    # an explicit contract for the next round.
    task["required_fix"] = _normalize_list(
        required_fix if required_fix is not None else task.get("required_fix")
    )
    task["blocking_files"] = _normalize_list(
        blocking_files if blocking_files is not None else task.get("blocking_files")
    )
    # Package 3: capture the latest authoritative verdict so the
    # closeout gate can read it instead of trusting the static verdict
    # field. This is the core "review truth becomes hard gate" change:
    # downstream surfaces MUST read latest_authoritative_verdict.
    authoritative = build_authoritative_verdict(
        outcome=outcome,
        verdict=verdict,
        reviewer=actor,
        review_reason=task["review_reason"],
        verdict_target=target_text,
        evidence_packet=evidence,
        scope_topic=task["scope_topic"],
        scope_files=task["scope_files"],
        required_fix=task["required_fix"],
        blocking_files=task["blocking_files"],
        at_ms=now_ms(),
    )
    task["latest_authoritative_verdict"] = authoritative
    if task_id and authoritative.get("outcome") == "fail":
        try:
            from eduflow.memory.derivation import on_authoritative_verdict_fail
            on_authoritative_verdict_fail(task_id, authoritative)
        except Exception:
            pass
    task["completed_at"] = _flow_completed_at(to_status)
    task["updated_at"] = now_ms()
    task["last_meaningful_update_at"] = task["updated_at"]


# ── public API ────────────────────────────────────────────────────


def create(assignee: str, title: str, *,
           description: str = "", creator: str = "") -> str:
    """Create a new task; return its task_id (T-<n>)."""
    if not title.strip():
        raise ValueError("title cannot be empty")
    with _locked():
        data = _load()
        tid = _next_task_id(data)
        now = now_ms()
        data.setdefault("tasks", []).append({
            "id": tid,
            "title": title.strip(),
            "description": description,
            "assignee": assignee,
            "creator": creator,
            "status": DEFAULT_STATUS,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        })
        _save(data)
        return tid


def create_flow(assignee: str, title: str, *, stage: str, owner: str,
                creator: str = "", description: str = "",
                status: str = "queued", verdict: str = "pending",
                workflow_id: str = "", emit_event: bool = True,
                workspace_mode: str = "",
                workspace_path: str = "",
                workspace_branch: str = "",
                workspace_base_commit: str = "") -> str:
    """Create a schema_version=2 flow task with state-machine fields."""
    if not title.strip():
        raise ValueError("title cannot be empty")
    stage = canonical_stage(stage)
    _validate_flow_stage_status(stage, status)
    if verdict not in FLOW_VERDICTS:
        raise ValueError(f"invalid verdict: {verdict} (valid: {sorted(FLOW_VERDICTS)})")
    workflow_id = normalize_required_workflow_id(
        title=title,
        stage=stage,
        workflow_id=workflow_id,
    )
    # M10: workspace policy metadata.  Defaults to "" (unset) so every
    # existing task is still valid.  When the caller passes an explicit
    # mode, validate it; an unknown mode is a ValueError.
    if workspace_mode and workspace_mode not in VALID_WORKSPACE_MODES:
        raise ValueError(
            f"invalid workspace_mode: {workspace_mode!r} "
            f"(valid: {sorted(VALID_WORKSPACE_MODES)})"
        )
    with _locked():
        data = _load()
        tid = _next_task_id(data)
        now = now_ms()
        row = {
            "id": tid,
            "schema_version": 2,
            "correlation_id": f"tc-{uuid4().hex}",
            "title": title.strip(),
            "description": description,
            "assignee": assignee,
            "creator": creator,
            "owner": owner,
            "reviewer": "",
            "stage": stage,
            "status": status,
            "verdict": verdict,
            "workflow_id": workflow_id,
            "needs_manager_action": _flow_needs_manager_action(status, verdict),
            "blocking_reason": "",
            "manager_action_type": "",
            "review_reason": "",
            "latest_turn_summary": _default_turn_summary(status=status, actor=creator),
            "scope_topic": "",
            "scope_files": [],
            "verdict_target": "",
            "verdict_scope": "",
            "evidence_packet": {},
            "evidence_snapshot": {},
            "evidence_snapshot_hash": "",
            "latest_authoritative_verdict": {},
            "required_fix": [],
            "blocking_files": [],
            "closeout_status": "",
            "loop_run_id": "",
            "loop_status": "",
            "loop_cycle_count": 0,
            "loop_stop_reason": "",
            "loop_recommended_action": "",
            "loop_evidence_ref": "",
            "loop_updated_by": "",
            "self_check_status": "",
            "review_check_status": "",
            "manager_closeout_status": "",
            "batch_closed_out_at": None,
            "manager_closed_out_at": None,
            "revision_priority": "",
            # M10: workspace policy fields.  All default to "" (unset)
            # so every existing task remains valid without migration.
            "workspace_mode": workspace_mode,
            "workspace_path": workspace_path,
            "workspace_branch": workspace_branch,
            "workspace_base_commit": workspace_base_commit,
            "workspace_evidence_ref": "",
            "created_at": now,
            "updated_at": now,
            "last_meaningful_update_at": now,
            "completed_at": _flow_completed_at(status),
        }
        data.setdefault("tasks", []).append(row)
        if emit_event:
            _append_task_event(
                task_id=tid,
                kind="created",
                actor=creator,
                before=None,
                after=_task_snapshot(row),
            )
        _save(data)
        return tid


def update(task_id: str, *, status: str | None = None,
           assignee: str | None = None, title: str | None = None,
           description: str | None = None) -> bool:
    """Apply non-None fields. Returns False if task_id not found."""
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status} (valid: {sorted(VALID_STATUSES)})")
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") == 2:
            raise ValueError(
                "flow tasks cannot use legacy update; use dispatch / "
                "flow-transition / submit-review / assign-reviewer / review"
            )
        if status is not None:
            task["status"] = status
            if status in TERMINAL_STATUSES:
                task["completed_at"] = now_ms()
            else:
                task["completed_at"] = None
        if assignee is not None:
            task["assignee"] = assignee
        if title is not None:
            task["title"] = title.strip()
        if description is not None:
            task["description"] = description
        task["updated_at"] = now_ms()
        _save(data)
        return True
    return False


def set_loop_evidence(
    task_id: str,
    *,
    loop_run_id: str,
    loop_status: str,
    loop_cycle_count: int = 0,
    loop_stop_reason: str = "",
    loop_recommended_action: str = "",
    loop_evidence_ref: str = "",
    self_check_status: str = "",
    review_check_status: str = "",
    manager_closeout_status: str = "",
    actor: str = "",
    emit_event: bool = True,
) -> bool:
    """Attach compact loop evidence to a flow task without changing delivery truth."""
    if loop_status not in LOOP_STATUSES:
        raise ValueError(f"invalid loop_status: {loop_status} (valid: {sorted(LOOP_STATUSES)})")
    checks = {
        "self_check_status": self_check_status,
        "review_check_status": review_check_status,
        "manager_closeout_status": manager_closeout_status,
    }
    for key, value in checks.items():
        if value not in CHECK_SUMMARY_STATUSES:
            raise ValueError(
                f"invalid {key}: {value} (valid: {sorted(CHECK_SUMMARY_STATUSES)})"
            )
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        task.update({
            "loop_run_id": str(loop_run_id or ""),
            "loop_status": loop_status,
            "loop_cycle_count": max(0, int(loop_cycle_count or 0)),
            "loop_stop_reason": str(loop_stop_reason or ""),
            "loop_recommended_action": str(loop_recommended_action or ""),
            "loop_evidence_ref": str(loop_evidence_ref or ""),
            "loop_updated_by": str(actor or ""),
            "self_check_status": str(self_check_status or ""),
            "review_check_status": str(review_check_status or ""),
            "manager_closeout_status": str(manager_closeout_status or ""),
            "updated_at": now_ms(),
            "last_meaningful_update_at": now_ms(),
        })
        if emit_event:
            _append_task_event(
                task_id=task_id,
                kind="transition",
                actor=actor,
                before=before,
                after=_task_snapshot(task),
            )
        _save(data)
        return True


def transition_flow(task_id: str, *, to_status: str, actor: str) -> bool:
    """Apply a validated state-machine transition for schema_version=2 tasks."""
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        _apply_flow_transition(task, to_status=to_status, actor=actor)
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
    # Memory bridge: surface a witness candidate for transitions that
    # indicate a real failure rather than transient progress.
    #
    # Triggered on:
    #   - cancelled       — explicit cancellation by manager
    #   - blocked         — worker/reviewer stuck; recurring blocked state
    #                       is a workflow-level concern
    #   - delivered with verdict=rejected — review concluded the task
    #                       failed its gate, even though the worker
    #                       formally "completed"
    #
    # Not triggered on:
    #   - assigned / in_progress / submitted_for_review / delivered+approved
    #     — normal progress, no failure signal
    #
    # Fail-open: bridge failures never break the state transition.
    if _is_failure_transition(task, to_status=to_status):
        _try_bridge_task_failure(task_id, actor=actor, to_status=to_status)
    return True


def _is_failure_transition(task: dict, *, to_status: str) -> bool:
    """Decide whether a state transition signals a real failure.

    Returns True for transitions we want to surface as memory witnesses:
      - cancelled       (any actor — explicit termination)
      - blocked         (worker or reviewer stuck — recurring signal)
      - delivered       only when verdict=rejected (gate failed)
      - failed          (worker/reviewer self-reported unrecoverable error)

    Returns False for normal progress transitions.
    """
    if to_status == "cancelled":
        return True
    if to_status == "blocked":
        return True
    if to_status == "failed":
        return True
    if to_status == "delivered":
        # delivered+rejected is rare but possible: a review concludes
        # the gate failed even though the worker formally "completed"
        # (e.g. package-level verdict rejection without a rework round).
        return str(task.get("verdict") or "").strip() == "rejected"
    return False


def _try_bridge_task_failure(task_id: str, *, actor: str, to_status: str) -> None:
    """Best-effort call to bridge_task_lifecycle for a failure-shaped transition.

    Fail-open wrapper. Swallows all exceptions. The function does not
    decide whether the cancellation/blocking is a "real" failure — it
    simply records a witness candidate (idempotent by task_id). The
    pattern detector in event_bridge decides whether ≥2 failures
    warrant a workflow-level pattern candidate.

    to_status is one of "cancelled" / "blocked" / "delivered+rejected"
    and is used to compose the failure_reason text shown to reviewers.
    """
    try:
        from eduflow.memory.event_bridge import bridge_task_lifecycle
    except Exception:
        return
    try:
        data = _load()
        task = _find_task(data, task_id) or {}
    except Exception:
        return
    workflow_id = str(task.get("workflow_id") or "")
    if not workflow_id:
        return
    verdict = str(task.get("verdict") or "").strip()
    if to_status == "delivered" and verdict == "rejected":
        reason_text = f"delivered with verdict=rejected (actor={actor})"
    elif to_status == "failed":
        # Prefer the explicit failure_reason the worker/reviewer
        # supplied via task report-failure; fall back to generic.
        reported = str(task.get("failure_reason") or "").strip()
        if reported:
            reason_text = f"failed (actor={actor}): {reported}"
        else:
            reason_text = f"failed (actor={actor})"
    else:
        reason_text = f"{to_status} by {actor}"
    try:
        bridge_task_lifecycle(
            task_id, "fail",
            context={
                "workflow_id": workflow_id,
                "failure_reason": reason_text,
            },
        )
    except Exception:
        pass


def report_flow_failure(task_id: str, *, actor: str, reason: str = "") -> bool:
    """Worker/reviewer self-reports an unrecoverable failure.

    Transitions the task to the `failed` status (idempotent for
    already-failed tasks: returns True without re-firing the bridge).
    Persists the supplied `reason` on the task so the memory witness
    candidate carries it forward to reviewers.

    Allowed actors per state machine:
      - from `assigned`: worker only
      - from `in_progress` / `blocked` / `submitted_for_review`:
        worker OR reviewer (depending on state — see FLOW_TRANSITIONS)

    Always triggers `bridge_task_lifecycle("fail", ...)`, which in
    turn fires the witness + pattern candidate pipeline.

    Returns True on success, False if the task doesn't exist.
    Raises ValueError on illegal transition (e.g. from `delivered`).
    """
    # Adapter-level helper: worker/reviewer code paths can call this
    # directly via tasks.report_flow_failure() instead of shelling
    # out to the CLI. The CLI command _cmd_report_failure in
    # commands/task.py wraps this function.
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        # Idempotent: if already failed, just update the reason (if
        # the caller supplied one) and re-fire the bridge so the new
        # reason makes it into the candidate's content.
        before = _task_snapshot(task)
        if task.get("status") == "failed":
            if reason:
                task["failure_reason"] = reason
                task["latest_turn_summary"] = (
                    f"Worker/reviewer re-reported failure: {reason}"
                )
                task["updated_at"] = now_ms()
            _append_task_event(
                task_id=task_id,
                kind="transition",
                actor=actor,
                before=before,
                after=_task_snapshot(task),
            )
            _save(data)
            if reason:
                _try_bridge_task_failure(task_id, actor=actor, to_status="failed")
            return True
        # Persist reason BEFORE the transition so the bridge helper
        # sees it on the task snapshot.
        if reason:
            task["failure_reason"] = reason
        _apply_flow_transition(task, to_status="failed", actor=actor)
        if reason:
            task["failure_reason"] = reason
            task["latest_turn_summary"] = (
                f"Worker/reviewer self-reported failure: {reason}"
            )
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
    # Memory bridge: failed is always a failure transition.
    _try_bridge_task_failure(task_id, actor=actor, to_status="failed")
    return True


def submit_for_review(task_id: str, *, actor: str) -> bool:
    """Move a flow task into submitted_for_review via the normal worker path."""
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        _apply_flow_transition(task, to_status="submitted_for_review", actor=actor)
        if not str(task.get("reviewer") or "").strip():
            default_reviewer = default_reviewer_for_workflow(str(task.get("workflow_id") or ""))
            if default_reviewer:
                task["reviewer"] = default_reviewer
                task["latest_turn_summary"] = (
                    f"Worker submitted the latest turn for review; "
                    f"default reviewer {default_reviewer} assigned by workflow."
                )
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
        return True


def assign_reviewer(task_id: str, *, reviewer: str, actor: str) -> bool:
    """Assign or update the reviewer for a flow task."""
    if actor != "manager":
        raise ValueError("only manager can assign reviewer")
    if not reviewer.strip():
        raise ValueError("reviewer cannot be empty")
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        task["reviewer"] = reviewer.strip()
        task["latest_turn_summary"] = f"Manager assigned reviewer {reviewer.strip()}."
        task["updated_at"] = now_ms()
        task["last_meaningful_update_at"] = task["updated_at"]
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
        return True


def review_flow(task_id: str, *, outcome: str, actor: str,
                review_reason: str = "",
                latest_turn_summary: str = "",
                manager_action_type: str = "",
                scope_topic: str = "",
                scope_files=None,
                verdict_target: str = "",
                evidence_packet=None,
                required_fix=None,
                blocking_files=None) -> bool:
    """Apply a reviewer outcome to a submitted flow task.

    Package 3: `required_fix` and `blocking_files` are persisted on the
    task so the next worker round has an explicit contract for what
    must change. The `verdict_target` is used to derive verdict_scope
    and to gate subject closeout.
    """
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        before = _task_snapshot(task)
        _apply_flow_review(
            task,
            task_id=task_id,
            outcome=outcome,
            actor=actor,
            review_reason=review_reason,
            latest_turn_summary=latest_turn_summary,
            manager_action_type=manager_action_type,
            scope_topic=scope_topic,
            scope_files=scope_files,
            verdict_target=verdict_target,
            evidence_packet=evidence_packet,
            required_fix=required_fix,
            blocking_files=blocking_files,
        )
        _append_task_event(
            task_id=task_id,
            kind="transition",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
        return True


def manager_closeout_subject(task_id: str, *, actor: str,
                             emit_event: bool = True,
                             verifier_result: dict | None = None,
                             content_dir: str = "",
                             skip_subject_verifier: bool = False) -> bool:
    """Mark a reviewed subject as formally closed by manager.

    Package 6: verifier gate — closeout is blocked if the artifact
    verifier does not pass. Pass verifier_result to enable the check.

    skip_subject_verifier is a TEST-ONLY escape hatch; production code
    must never set it to True — it bypasses the artifact verifier gate
    entirely and should only be used when no real content directory exists
    (e.g. in unit-test fixtures that exercise closeout behaviour, not the
    verifier itself).
    """
    if actor != "manager":
        raise ValueError("only manager can close out a subject")
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        if is_package_scope(task):
            raise ValueError(
                "manager-closeout is only for subject closeout; "
                "use batch-closeout for batch/package tasks"
            )
        before = _task_snapshot(task)
        if skip_subject_verifier and verifier_result is None:
            evidence = task.get("evidence_packet") or {}
            verifier_result = {
                "scope": "subject",
                "status": "pass",
                "items_count": int(evidence.get("items_count") or evidence.get("item_count") or 0),
                "qql_count": int(evidence.get("qql_count") or evidence.get("qa_count") or 0),
                "manifest_rows": int(
                    evidence.get("manifest_rows")
                    or evidence.get("manifest_covered_count")
                    or evidence.get("items_mapping_count")
                    or evidence.get("items_count")
                    or evidence.get("item_count")
                    or 0
                ),
                "consistency": {"drifts": [], "drift_count": 0},
                "blocking_reasons": [],
            }
        if not skip_subject_verifier and verifier_result is None:
            from eduflow.store.subject_verifier import verify_subject
            slug = extract_subject_slug(str(task.get("title") or ""))
            verifier_result = verify_subject(content_dir or "content", slug) if slug else None
        task_for_gate = task
        if verifier_result is not None:
            task_for_gate = dict(task)
            task_for_gate["verifier_result"] = verifier_result
        gate = subject_closeout_status(task_for_gate)
        if gate["closeout_status"] != "closeout_ready":
            blockers = []
            blockers.extend(str(item) for item in gate.get("missing_evidence") or [])
            blockers.extend(str(item) for item in gate.get("conflicting_evidence") or [])
            if verifier_result:
                blockers.extend(str(item) for item in verifier_result.get("blocking_reasons") or [])
                if verifier_result.get("scope") and verifier_result.get("scope") != "subject":
                    blockers.append(f"subject_verifier_scope_is_{verifier_result.get('scope')}")
            detail = f" blockers={';'.join(dict.fromkeys(blockers))}" if blockers else ""
            raise ValueError(
                f"subject closeout not ready: {gate['closeout_status']}{detail}"
            )

        # Package 7 (Revision-First Gate): the worker evidence_packet
        # must contain all REQUIRED_EVIDENCE_PACKET_FIELDS before the
        # subject can be formally closed out. Empty packets are allowed
        # to fall through for legacy flows/tests that have not yet
        # adopted the new packet shape; non-empty packets with missing
        # required fields block closeout.
        # When skip_subject_verifier is True (test-only escape hatch),
        # also skip the evidence-packet shape check so unit tests can
        # exercise closeout transitions without constructing a full
        # production evidence packet.
        if not skip_subject_verifier:
            packet = task.get("evidence_packet") or {}
            if isinstance(packet, dict) and packet:
                from eduflow.store.task_event_scanner import validate_evidence_packet
                missing = validate_evidence_packet(packet)
                if missing:
                    raise ValueError(
                        f"evidence_packet incomplete: missing {','.join(missing)}. "
                        "Provide workflow_id, task_id, batch_range, items_count, "
                        "qql_count, manifest_evidence before closeout."
                    )

        # ── Package 6: artifact verifier gate ─────────────────────
        # Run verifier if not provided (auto-verify for curriculum tasks).
        # The verifier is mandatory for subject closeout; it cannot be
        # bypassed by passing None.
        if not skip_subject_verifier:
            from eduflow.store.subject_verifier import subject_closeout_gate
            vgate = subject_closeout_gate(
                task=task,
                verifier_result=(verifier_result or {"scope": "subject", "status": "fail",
                                                      "blocking_reasons": ["no_verifier_result"]}),
                content_dir=content_dir,
            )
            if not vgate["closeout_allowed"]:
                reasons = "; ".join(vgate["blocking_reasons"])
                raise ValueError(
                    f"subject verifier blocks closeout: {reasons}"
                )

        task["closeout_status"] = "closeout_completed"
        task["tier_status"] = "closeout_completed"
        task["manager_closed_out_at"] = now_ms()
        task["latest_turn_summary"] = "Manager formally closed out the subject."
        task["updated_at"] = task["manager_closed_out_at"]
        task["last_meaningful_update_at"] = task["updated_at"]
        try:
            from eduflow.memory.derivation import on_closeout_completed
            on_closeout_completed(task_id)
        except Exception:
            pass
        if emit_event:
            _append_task_event(
                task_id=task_id,
                kind="transition",
                actor=actor,
                before=before,
                after=_task_snapshot(task),
            )
        _save(data)
        return True


def update_post_delivery_verdict(
    task_id: str,
    *,
    actor: str,
    verdict: str,
    reason: str = "",
) -> bool:
    """Update a task's verdict AFTER the task has been delivered.

    Why this exists: the state machine currently resets verdict to
    "approved" on `to_status="delivered"`. If a downstream review
    (e.g. closeout gate, a second-pass review) later concludes the
    task's gate actually failed, the operator needs a way to flip
    verdict to "rejected" without going through a full state-machine
    transition cycle. This function writes the verdict directly,
    bypassing the state-machine verdict reset.

    Constraints:
      - Task must already be in `status="delivered"`.
      - Actor must be the assigned reviewer (or "reviewer" if none
        assigned) or the manager.
      - Verdict must be one of FLOW_VERDICTS.

    Side effects:
      - Sets `task["verdict"]` to the new value.
      - Updates `latest_turn_summary` so the next human viewer sees
        why the verdict changed.
      - When verdict transitions to "rejected", fires the
        `_try_bridge_task_failure` helper so a memory candidate
        is created (the "delivered+rejected" witness path).
      - When verdict changes at all, invalidates any previously
        computed closeout state (closeout_status, tier_status,
        manager_closed_out_at, latest_authoritative_verdict) so
        downstream closeout gate re-evaluates from scratch.
      - Appends a `verdict_update` event to the task event log.

    Returns True on success, False if the task doesn't exist.
    Raises ValueError on constraint violations (wrong status, wrong
    actor, invalid verdict value).
    """
    if verdict not in FLOW_VERDICTS:
        raise ValueError(
            f"invalid verdict: {verdict!r} (valid: {sorted(FLOW_VERDICTS)})"
        )
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        current_status = str(task.get("status") or "")
        if current_status != "delivered":
            raise ValueError(
                f"update_post_delivery_verdict requires status=delivered "
                f"(got: {current_status!r})"
            )
        # Actor check: only the assigned reviewer (or 'reviewer'
        # generically) or the manager can update a verdict post-delivery.
        actor_norm = str(actor or "").strip()
        if actor_norm not in ("manager", "reviewer"):
            raise ValueError(
                f"actor {actor_norm!r} cannot update verdict; "
                "allowed: manager, reviewer"
            )
        assigned_reviewer = str(task.get("reviewer") or "").strip()
        if actor_norm == "reviewer" and assigned_reviewer and actor != assigned_reviewer:
            raise ValueError(
                f"actor {actor!r} is not the assigned reviewer "
                f"(assigned reviewer: {assigned_reviewer!r})"
            )
        before = _task_snapshot(task)
        old_verdict = str(task.get("verdict") or "").strip()
        task["verdict"] = verdict
        # Compose a turn summary that explains the verdict change.
        if reason:
            task["latest_turn_summary"] = (
                f"Post-delivery verdict update: {old_verdict} → {verdict}. "
                f"Reason: {reason}"
            )
        else:
            task["latest_turn_summary"] = (
                f"Post-delivery verdict update: {old_verdict} → {verdict}"
            )
        # Invalidate any closeout state computed under the old verdict.
        # The closeout gate derives its closeout_status / tier_status
        # from the static verdict field; if we just flipped the
        # verdict, the previous computation is stale. Forcing the
        # gate to re-evaluate from scratch prevents stale
        # "closeout_completed" status from outliving the verdict
        # change.
        #
        # This applies on ANY actual verdict change (not only
        # rejected→) so that e.g. approved → manager_action also
        # invalidates. If the verdict is unchanged (no-op update),
        # the closeout state stays valid and we don't churn it.
        if old_verdict != verdict:
            invalidated_closeout_fields = []
            for field in ("closeout_status", "tier_status", "manager_closed_out_at"):
                if task.get(field) not in (None, "", 0):
                    task[field] = "" if field != "manager_closed_out_at" else None
                    invalidated_closeout_fields.append(field)
            # The latest_authoritative_verdict snapshot also becomes
            # stale — clear it so the closeout gate reconstructs it from
            # the (now-updated) latest events.
            if task.get("latest_authoritative_verdict"):
                task["latest_authoritative_verdict"] = {}
                invalidated_closeout_fields.append("latest_authoritative_verdict")
            if invalidated_closeout_fields:
                # Append to the turn summary so reviewers see why closeout
                # gate will re-evaluate.
                task["latest_turn_summary"] += (
                    f" [closeout gate invalidated: "
                    f"{','.join(invalidated_closeout_fields)}]"
                )
        task["updated_at"] = now_ms()
        task["last_meaningful_update_at"] = task["updated_at"]
        _append_task_event(
            task_id=task_id,
            kind="verdict_update",
            actor=actor,
            before=before,
            after=_task_snapshot(task),
        )
        _save(data)
    # Bridge: if we just flipped verdict to "rejected" on a delivered
    # task, fire the witness candidate. This is the rare
    # "delivered+rejected" path that the state machine can't
    # produce on its own.
    if verdict == "rejected" and old_verdict != "rejected":
        _try_bridge_task_failure(task_id, actor=actor, to_status="delivered")
    return True


def batch_closeout(task_id: str, *, actor: str, emit_event: bool = True) -> bool:
    """Mark a reviewed package/batch as closed without triggering subject rollover."""
    if actor != "manager":
        raise ValueError("only manager can close out a batch/package")
    with _locked():
        data = _load()
        task = _find_task(data, task_id)
        if task is None:
            return False
        if task.get("schema_version") != 2:
            raise ValueError(f"task {task_id} is not a flow task")
        if not is_package_scope(task):
            raise ValueError(
                "batch-closeout is only for batch/package tasks; "
                "use manager-closeout for subject closeout"
            )
        if str(task.get("status") or "") != "delivered" or str(task.get("verdict") or "") != "approved":
            raise ValueError(
                "batch closeout requires delivered status with verdict=approved"
            )
        before = _task_snapshot(task)
        task["closeout_status"] = "batch_closeout_completed"
        task["batch_closed_out_at"] = now_ms()
        task["latest_turn_summary"] = "Manager formally closed out the batch/package."
        task["updated_at"] = task["batch_closed_out_at"]
        task["last_meaningful_update_at"] = task["updated_at"]
        if emit_event:
            _append_task_event(
                task_id=task_id,
                kind="transition",
                actor=actor,
                before=before,
                after=_task_snapshot(task),
            )
        _save(data)
        return True


def list_task_events(*, task_id: str | None = None, limit: int = 50) -> list[dict]:
    rows = read_jsonl(_events_file())
    if task_id is not None:
        rows = [r for r in rows if r.get("task_id") == task_id]
    return rows[-limit:]


def get(task_id: str) -> dict | None:
    for task in _load().get("tasks", []):
        if task["id"] == task_id:
            return task
    return None


def list_tasks(*, status: str | None = None,
               assignee: str | None = None,
               include_archived: bool = False) -> list[dict]:
    """Return tasks filtered by status / assignee, sorted by id.

    T-104: archived tasks are hidden by default. Soft-marked
    (`archived=true`) tasks still resident in tasks.json are filtered out
    unless `include_archived=True`; physically-moved tasks are no longer in
    tasks.json at all. `include_archived` is keyword-only with a default, so
    existing call sites are unaffected — only the default result set shrinks.
    """
    rows = list(_load().get("tasks", []))
    if not include_archived:
        rows = [t for t in rows if not is_archived(t)]
    if status is not None:
        rows = [t for t in rows if t.get("status") == status]
    if assignee is not None:
        rows = [t for t in rows if t.get("assignee") == assignee]
    rows.sort(key=lambda t: int(t["id"].split("-")[1]) if "-" in t["id"] else 0)
    return rows


def list_review_queue(*, stage: str | None = None,
                      reviewer: str | None = None) -> list[dict]:
    """Return flow-tasks currently awaiting review."""
    rows = [
        t for t in _load().get("tasks", [])
        if t.get("schema_version") == 2
        and t.get("status") == "submitted_for_review"
        and t.get("verdict") == "pending"
    ]
    if stage is not None:
        rows = [t for t in rows if t.get("stage") == stage]
    if reviewer is not None:
        rows = [t for t in rows if t.get("reviewer") == reviewer]
    rows.sort(key=lambda t: int(t["id"].split("-")[1]) if "-" in t["id"] else 0)
    return rows


def manager_overview() -> dict:
    """Return manager-facing grouped work buckets for active flow tasks."""
    rows = [t for t in _load().get("tasks", []) if t.get("schema_version") == 2]

    def _bucket(status: str | None = None, *, verdict: str | None = None) -> list[dict]:
        items = rows
        if status is not None:
            items = [t for t in items if t.get("status") == status]
        if verdict is not None:
            items = [t for t in items if t.get("verdict") == verdict]
        items.sort(
            key=lambda t: (
                -int(t.get("last_meaningful_update_at") or t.get("updated_at") or 0),
                -(int(t["id"].split("-")[1]) if "-" in t["id"] else 0),
            ),
        )
        return items

    blocked = [
        t for t in _bucket("blocked")
        if not t.get("needs_manager_action")
    ]
    return {
        "in_progress": _bucket("in_progress"),
        "awaiting_review": _bucket("submitted_for_review"),
        "blocked": blocked,
        "manager_action": [
            t for t in _bucket("blocked")
            if t.get("needs_manager_action")
        ],
        "subject_closeout": [
            t for t in rows
            if subject_closeout_status(t)["closeout_status"] in {
                "review_passed_waiting_closeout",
                "closeout_blocked_missing_evidence",
                "closeout_blocked_count_out_of_range",
                "evidence_account_incomplete",
                "evidence_account_conflict",
                "closeout_ready",
            }
        ],
    }


def has_hermes_can_promote_marker(task_id: str) -> bool:
    """Check if a task's description contains the hermes_can_promote marker.

    This is a convenience helper for Hermes adapter code to determine
    whether the manager authorized Hermes to promote non-high-impact
    candidates for this task.

    The marker format is: [hermes-can-promote: true]

    Returns True if the marker is present in the task description,
    False otherwise.
    """
    task = get(task_id)
    if task is None:
        return False
    desc = str(task.get("description") or "")
    return "[hermes-can-promote: true]" in desc


# ── T-104: task archival (A physical move + B soft mark) ──────────────
# Combo design: `archived=true` is the soft marker (B); `archive_tasks()`
# physically moves matured terminal tasks out of tasks.json into monthly
# JSONL slices under archive/ (A). Keeping the boss's live query set small
#压 token; the archive/ slices stay readable for explicit look-back.

def is_archived(task: dict) -> bool:
    """Soft-mark reader. Missing field on legacy tasks → false (b-compat)."""
    return bool(task.get("archived", False))


def _archive_dir() -> Path:
    return paths.state_dir() / "archive"


def _archive_slice_file(month: str) -> Path:
    return _archive_dir() / f"tasks-{month}.jsonl"


def _archive_reference_ts(task: dict) -> int:
    """The timestamp used to decide a task's age + archive month slice.

    Prefer the moment it reached a terminal state; fall back through the
    other stamps so legacy rows without `completed_at` still resolve.
    """
    for key in ("completed_at", "last_meaningful_update_at",
                "updated_at", "created_at"):
        val = task.get(key)
        if val:
            try:
                return int(val)
            except (TypeError, ValueError):
                continue
    return 0


def _archive_month(ts_ms: int) -> str:
    if ts_ms <= 0:
        return "unknown"
    from datetime import datetime
    return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m")


def archive_candidates(older_than_days: int = 90, *,
                       now: int | None = None) -> list[dict]:
    """Non-mutating: which resident tasks would archive_tasks() move now."""
    now_ts = int(now if now is not None else now_ms())
    cutoff = now_ts - int(older_than_days) * 86_400_000
    out = []
    for task in _load().get("tasks", []):
        if is_archived(task):
            continue
        if str(task.get("status") or "") not in ARCHIVABLE_STATUSES:
            continue
        ref = _archive_reference_ts(task)
        if ref and ref <= cutoff:
            out.append(task)
    return out


def archive_tasks(older_than_days: int = 90, *,
                  dry_run: bool = False, now: int | None = None) -> dict:
    """Physically move terminal tasks older than N days out of tasks.json
    into monthly archive slices (`archive/tasks-YYYY-MM.jsonl`).

    Each moved record is soft-marked `archived=true` + `archived_at` as it
    is written to its slice (B), then dropped from tasks.json (A). A missing
    `archived` field reads as false, so the pass is idempotent and
    backward-compatible. `dry_run=True` computes the plan without writing.
    Returns a summary dict (safe to log / print / json).
    """
    with _locked():
        data = _load()
        now_ts = int(now if now is not None else now_ms())
        cutoff = now_ts - int(older_than_days) * 86_400_000
        move: list[dict] = []
        keep: list[dict] = []
        for task in data.get("tasks", []):
            ref = _archive_reference_ts(task)
            if (not is_archived(task)
                    and str(task.get("status") or "") in ARCHIVABLE_STATUSES
                    and ref and ref <= cutoff):
                move.append(task)
            else:
                keep.append(task)

        by_month: dict[str, int] = {}
        for task in move:
            month = _archive_month(_archive_reference_ts(task))
            by_month[month] = by_month.get(month, 0) + 1

        summary = {
            "dry_run": dry_run,
            "older_than_days": int(older_than_days),
            "cutoff_ms": cutoff,
            "archived_count": len(move),
            "by_month": by_month,
            "task_ids": [t["id"] for t in move],
            "files": sorted(str(_archive_slice_file(m)) for m in by_month),
        }
        if dry_run or not move:
            return summary

        grouped: dict[str, list[dict]] = {}
        for task in move:
            month = _archive_month(_archive_reference_ts(task))
            rec = dict(task)
            rec["archived"] = True
            rec["archived_at"] = now_ts
            grouped.setdefault(month, []).append(rec)

        _archive_dir().mkdir(parents=True, exist_ok=True)
        for month, recs in grouped.items():
            path = _archive_slice_file(month)
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            lines = "\n".join(json.dumps(r, ensure_ascii=False) for r in recs)
            atomic_write_text(path, existing + lines + "\n")

        data["tasks"] = keep
        _save(data)
        return summary
