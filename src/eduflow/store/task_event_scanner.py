"""Scan append-only flow-task events and derive publish decisions."""
from __future__ import annotations

import re

from eduflow.runtime import context_monitor, paths, watchdog as runtime_watchdog
from eduflow.store import (
    local_facts, task_evidence_account, task_publish_gate,
    task_publish_render, tasks,
)
from eduflow.util import now_ms
from eduflow.util import read_json, read_jsonl, write_json


STALE_TASK_THRESHOLD_MS = 30 * 60 * 1000
MANAGER_ACTION_THRESHOLD_MS = 15 * 60 * 1000
REJECT_RESUBMIT_THRESHOLD = 2
SUPERVISOR_HEARTBEAT_INTERVAL_MS = 10 * 60 * 1000
SUPERVISOR_RECENT_ACTIVITY_MS = 10 * 60 * 1000
SUPERVISOR_STALE_RESULT_MS = 20 * 60 * 1000
SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS = 20 * 60 * 1000
SUPERVISOR_MANAGER_HIGH_PRIORITY_UNREAD_MS = 2 * 60 * 1000
SUPERVISOR_MANAGER_AUTO_REPORT_UNREAD_MS = 2 * 60 * 1000
HIGH_PRIORITY_READ_WITHOUT_ACK_WINDOW_MS = 60 * 60 * 1000
SUPERVISOR_REPEAT_ALERT_THRESHOLD = 2
STATUS_TRUTH_LAG_THRESHOLD_MS = 10 * 60 * 1000
REVIEW_STATUS_TRUTH_LAG_THRESHOLD_MS = 5 * 60 * 1000
PROCESS_VISIBILITY_STALE_THRESHOLD_MS = 10 * 60 * 1000
ACCEPTED_WITHOUT_STARTED_THRESHOLD_MS = 2 * 60 * 1000
SECONDHAND_VISIBILITY_THRESHOLD_MS = 3 * 60 * 1000
SECONDHAND_VISIBILITY_WINDOW_MS = 10 * 60 * 1000
REQUIRED_EVIDENCE_PACKET_FIELDS = (
    "workflow_id",
    "task_id",
    "batch_range",
    "items_count",
    "qql_count",
    "manifest_evidence",
)
WORKER_CONTEXT_GUARD_AGENTS = frozenset({
    "worker_course",
    "review_course",
    "worker_builder",
    "worker_qbank",
})
CONTEXT_EXHAUSTION_MARKERS = (
    "ready_unproven",
    "cli not ready",
)
PRODUCTION_MARKERS = (
    "continuing production",
    "production",
    "generated",
    "generating",
    "继续生产",
    "继续生成",
    "正在生产",
    "正在生成",
    "产出",
    "写入",
    "draft",
)
BLOCKED_STATUS_MARKERS = (
    "blocked",
    "受阻",
    "阻塞",
    "卡住",
    "等待",
)


def validate_evidence_packet(packet: dict) -> list[str]:
    """Return list of required field names that are missing or empty.

    A field is considered present when its value is truthy and not an
    empty string / list / dict. The check is intentionally structural —
    the validator guards the contract for Package 7's evidence-packet
    consumers, not the field semantics.
    """
    if not isinstance(packet, dict):
        return list(REQUIRED_EVIDENCE_PACKET_FIELDS)
    missing: list[str] = []
    for field in REQUIRED_EVIDENCE_PACKET_FIELDS:
        if field not in packet:
            missing.append(field)
            continue
        value = packet[field]
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, (str, list, dict)) and not value:
            missing.append(field)
    return missing


DIRECT_VISIBILITY_AGENTS = frozenset({
    "worker_course",
    "review_course",
    "worker_builder",
    "worker_qbank",
    "auto_ops",
})
CONTINUING_WATCH_MARKERS = (
    "继续盯盘",
    "盯盘待命",
    "持续盯盘",
    "值守",
)
MANAGER_ACTION_APPLY_ALLOWLIST = frozenset({
    "manager_formal_closeout",
    "request_worker_course_expand_qa",
    "request_review_course_file_evidence",
    "request_qbank_readiness_check",
    "dispatch_next_subject_worker_course",
    "safe_task_review_approve",
})
# Package 7 (Revision-First Gate): actions that pivot production away
# from the open revision scope. These are still allowlisted for
# dry-run visibility, but `manager_action_apply()` will refuse to
# actually create / dispatch them when any flow task has
# revision_priority set. Keep the allowlist untouched for non-pivot
# actions (`safe_task_review_approve` is intentionally NOT in this set
# — that one helps clear the revision, not pivot past it).
REVISION_FIRST_BLOCKED_APPLY_ACTIONS = frozenset({
    "dispatch_next_subject_worker_course",
    "request_worker_course_expand_qa",
})
# Package 7 (Revision-First Gate) round 6 fix: a single canonical
# blocked action-code set shared by:
#   * manager_action_apply()   (apply-level enforcement)
#   * manager-actions CLI      (recommendation-level filter)
#   * manager-panel CLI        (display-level filter)
# This prevents the three layers from drifting out of sync.
# `safe_task_review_approve` is intentionally NOT in this set — it
# helps clear the revision, not pivot past it.
# `continue_next_batch` / `select_next_subject` are not action_codes
# in the apply sense but are recommendations emitted by
# `_next_subject_rollover_finding` / `next_batch_continuation_gate`;
# they are filtered separately at the recommendation layer using
# `REVISION_FIRST_BLOCKED_RECOMMENDATIONS`.
REVISION_FIRST_BLOCKED_ACTIONS = frozenset({
    "dispatch_next_subject_worker_course",
    "request_worker_course_expand_qa",
})
REVISION_FIRST_BLOCKED_RECOMMENDATIONS = frozenset({
    "continue_next_batch",
    "select_next_subject",
    "dispatch_next_subject_worker_course",
    "request_worker_course_expand_qa",
})
MANAGER_ACTION_DRY_RUN_ONLY = frozenset({
    "approve_subject_for_qbank_seed",
    "no_next_subject_candidate",
    "send_lightweight_reassurance",
})
_FOLLOWUP_TERMINAL_STATUSES = frozenset({"delivered", "cancelled"})


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _surface_stage_state(task: dict) -> str:
    stage = str(task.get("stage") or "")
    status = str(task.get("status") or "")
    verdict = str(task.get("verdict") or "")
    assignee = str(task.get("assignee") or "")
    review_reason = str(task.get("review_reason") or "")

    if assignee == "worker_course":
        if status in {"queued", "assigned"}:
            return "accepted_current_subject"
        if status == "in_progress":
            return "producing_current_subject"
        if status == "submitted_for_review":
            return "delivered_to_review"
    if assignee == "review_course":
        if status == "assigned":
            return "review_pending_current_subject"
        if status == "in_progress":
            return "reviewing_current_subject"
        if status == "blocked" and verdict == "manager_action":
            return "minor_fix_requested"
        if status == "delivered":
            return "review_passed_waiting_manager_closeout"
    if assignee == "worker_builder":
        if status in {"queued", "assigned", "in_progress"}:
            return "builder_task_accepted"
        if status in {"submitted_for_review", "delivered"}:
            return "builder_artifact_ready"
    if assignee == "worker_qbank":
        if status in {"queued", "assigned", "in_progress"}:
            return "qbank_check_accepted"
        if status == "delivered":
            return "qbank_first_verdict_ready"
    return ""


def _truth_markers(task: dict) -> tuple[str, ...]:
    title = str(task.get("title") or "")
    summary = str(task.get("latest_turn_summary") or "")
    semantic = tasks.flow_semantic_summary(task)
    subject_summary = tasks.subject_closeout_summary(task)
    return tuple(
        marker for marker in (
            _normalize_text(title),
            _normalize_text(summary),
            _normalize_text(semantic),
            _normalize_text(subject_summary),
        )
        if marker
    )


def _status_surface_markers(agent: str) -> tuple[str, int, str]:
    status = local_facts.get_status(agent) or {}
    latest_logs = local_facts.list_logs(agent, limit=3)
    parts = []
    if status:
        parts.append(_normalize_text(status.get("task") or ""))
        parts.append(_normalize_text(status.get("blocker") or ""))
    for row in latest_logs:
        parts.append(_normalize_text(row.get("content") or ""))
    marker_text = " ".join(part for part in parts if part)
    updated_at = int(status.get("updated_at") or 0)
    return marker_text, updated_at, str(status.get("task") or "")


def _agent_has_progress_signal_after_ack(agent: str, message_id: str, ack_at: int) -> bool:
    ref = f"inbox:{message_id}"
    for row in local_facts.list_logs(agent, limit=12):
        created_at = int(row.get("created_at") or 0)
        if created_at < ack_at:
            continue
        kind = str(row.get("type") or "")
        if str(row.get("ref") or "") == ref and kind in {
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "ack",
        }:
            return True
        if kind == "say":
            return True
    return False


def _message_has_local_visibility_ref(agent: str, message_id: str) -> bool:
    ref = f"inbox:{message_id}"
    visible_kinds = {
        "ack",
        "qbank_followup",
        "worker_course_stage_ack",
        "worker_course_started",
        "review_course_stage_ack",
        "review_course_started",
        "worker_builder_stage_ack",
        "worker_builder_started",
        "worker_stage_ack",
        "worker_started",
    }
    for row in local_facts.list_logs(agent, limit=20):
        if str(row.get("ref") or "") != ref:
            continue
        if str(row.get("type") or "") in visible_kinds:
            return True
    return False


def _ack_kind_is_stale_or_superseded(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    return "stale" in lowered or "superseded" in lowered


def _agent_has_direct_visibility_after(agent: str, since: int) -> bool:
    for row in local_facts.list_logs(agent, limit=12):
        created_at = int(row.get("created_at") or 0)
        if created_at < since:
            continue
        kind = str(row.get("type") or "")
        if kind == "say":
            return True
        if kind in {
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
        }:
            return True
    return False


def _visibility_keywords(text: str) -> set[str]:
    lowered = str(text or "").lower()
    keywords: set[str] = set()
    markers = {
        "qbank": (
            "qbank", "题库", "去重", "dedup", "manifest", "验证",
            "renumber", "collision", "canonical", "round2", "true_dup",
            "id_collision", "v3",
        ),
        "review": ("review", "复核", "verdict", "gate"),
        "business": ("business studies", "0450", "t-10"),
        "economics": ("economics", "0455"),
        "physics": ("physics", "0625"),
        "chemistry": ("chemistry", "0620"),
        "accounting": ("accounting", "0452"),
        "biology": ("biology", "0610"),
        "runtime": (
            "router", "watchdog", "hermes", "runtime", "pidlock",
            "respawn", "path", "cli", "qoder", "health", "tmux",
        ),
    }
    for key, tokens in markers.items():
        if any(token in lowered for token in tokens):
            keywords.add(key)
    return keywords


def _visibility_tokens(text: str) -> set[str]:
    value = str(text or "").lower()
    tokens: set[str] = set()
    for pattern in (
        r"\bt-\d+\b",
        r"\bbatch\s*\d+\b",
        r"\b\d{4}\b",
        r"\b\d+\.\d+\b",
    ):
        tokens.update(re.findall(pattern, value))
    return {" ".join(token.split()) for token in tokens if token.strip()}


def _agent_has_related_visibility_after(agent: str, since: int, content: str) -> bool:
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected and not expected_tokens:
        return _agent_has_direct_visibility_after(agent, since)
    if "runtime" in expected:
        required = {"runtime"}
    elif "qbank" in expected:
        required = {"qbank"}
    else:
        required = expected
    visibility_since = max(since - 1000, 0)
    for row in local_facts.list_logs(agent, limit=12):
        created_at = int(row.get("created_at") or 0)
        if created_at < visibility_since:
            continue
        kind = str(row.get("type") or "")
        if kind not in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
            "task",
        }:
            continue
        row_content = str(row.get("content") or "")
        if required & _visibility_keywords(row_content):
            return True
        if expected_tokens and expected_tokens & _visibility_tokens(row_content):
            return True
    return False


def _agent_has_followthrough_visibility_after(agent: str, since: int) -> bool:
    """Return True when the agent visibly acted after reading a message.

    This is weaker than a formal inbox ACK, so callers should keep an
    ack-semantics finding. It only prevents a real later process/completion
    signal from being misreported as "read but not in role".
    """
    visibility_since = max(since - 1000, 0)
    for row in local_facts.list_logs(agent, limit=12):
        created_at = int(row.get("created_at") or 0)
        if created_at < visibility_since:
            continue
        kind = str(row.get("type") or "")
        content = str(row.get("content") or "")
        if kind in {
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
        }:
            return True
        if kind != "say":
            continue
        if any(marker in content for marker in (
            "已接管",
            "开始",
            "正在",
            "处理中",
            "进行中",
            "已修正",
            "检查完成",
            "确认无遗漏",
            "完工",
            "完成",
            "已交付",
            "PASS",
            "pass",
        )):
            return True
    return False


def _message_has_sender_visibility(msg: dict) -> bool:
    if str(msg.get("to") or "") != "manager":
        return False
    sender = str(msg.get("from") or "")
    if sender not in DIRECT_VISIBILITY_AGENTS:
        return False
    content = str(msg.get("content") or "")
    if not content.strip():
        return False
    created_at = int(msg.get("created_at") or 0)
    since = max(created_at - 1000, 0)
    if _agent_has_related_visibility_after(sender, since, content):
        return True
    status = local_facts.get_status(sender) or {}
    if int(status.get("updated_at") or 0) < since:
        return False
    status_text = f"{status.get('task') or ''} {status.get('blocker') or ''}"
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected and not expected_tokens:
        return bool(status_text.strip())
    if expected & _visibility_keywords(status_text):
        return True
    return bool(expected_tokens and expected_tokens & _visibility_tokens(status_text))


def _agent_status_indicates_related_progress(agent: str, content: str) -> tuple[bool, dict]:
    raw_status = local_facts.get_raw_status(agent) or {}
    projected_status = local_facts.get_status(agent) or {}
    status = raw_status or projected_status
    candidates = [row for row in (raw_status, projected_status) if row]
    if not candidates:
        return False, status
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected and not expected_tokens:
        for candidate in candidates:
            if str(candidate.get("status") or "") in {"已接单", "进行中", "已交付", "已完成"}:
                return bool(str(candidate.get("task") or "").strip()), candidate
        return False, status
    if "runtime" in expected:
        required = {"runtime"}
    elif "qbank" in expected:
        required = {"qbank"}
    else:
        required = expected
    for candidate in candidates:
        state = str(candidate.get("status") or "")
        if state not in {"已接单", "进行中", "已交付", "已完成"}:
            continue
        status_text = f"{candidate.get('task') or ''} {candidate.get('blocker') or ''}"
        if required & _visibility_keywords(status_text):
            return True, candidate
        if expected_tokens and expected_tokens & _visibility_tokens(status_text):
            return True, candidate
    return False, status


def _message_superseded_by_projected_status(agent: str, content: str, created_at: int) -> bool:
    """Return True when newer real surface evidence has closed this inbox item.

    We still do not mutate the inbox ACK fields. This only prevents diagnostics
    from keeping an old "started without explicit ACK" warning alive after a
    later visible PASS/closeout or qbank handoff has made the live state clear.
    """
    projected = local_facts.get_status(agent) or {}
    projected_at = int(projected.get("updated_at") or 0)
    if projected_at < max(created_at - 1000, 0):
        return False
    if str(projected.get("status") or "") not in {"空闲", "待命", "已交付", "已完成"}:
        return False
    projected_text = f"{projected.get('task') or ''} {projected.get('blocker') or ''}"
    if any(marker in projected_text for marker in ("closeout", "等待审批", "待审批", "review_course 已 PASS")):
        return True
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected and not expected_tokens:
        return bool(str(projected.get("task") or "").strip())
    if expected & _visibility_keywords(projected_text):
        return True
    return bool(expected_tokens and expected_tokens & _visibility_tokens(projected_text))


def _message_superseded_by_manager_closeout(agent: str, content: str, created_at: int) -> bool:
    if agent != "worker_course":
        return False
    expected_tokens = _visibility_tokens(content)
    expected_keywords = _visibility_keywords(content)
    if not expected_tokens and not expected_keywords:
        return False
    since = max(created_at - 1000, 0)
    for surface_agent in ("manager", "review_course"):
        for row in local_facts.list_logs(surface_agent, limit=30):
            if int(row.get("created_at") or 0) < since:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed"}:
                continue
            row_content = str(row.get("content") or "")
            lowered = row_content.lower()
            terminal = (
                "closeout" in lowered
                or "正式 pass" in lowered
                or "正式 PASS" in row_content
                or "pass" in lowered
                or "闭环" in row_content
                or "可 closeout" in row_content
            )
            if not terminal:
                continue
            if expected_tokens and expected_tokens & _visibility_tokens(row_content):
                return True
            if expected_keywords and expected_keywords & _visibility_keywords(row_content):
                return True
    return False


def _message_has_later_direct_process_visibility(msg: dict) -> bool:
    """Return True when a later same-lane signal proves an unread prompt moved on."""
    agent = str(msg.get("to") or "")
    local_id = str(msg.get("local_id") or "")
    created_at = int(msg.get("created_at") or 0)
    content = str(msg.get("content") or "")
    if not agent or not local_id:
        return False
    return (
        _message_has_local_visibility_ref(agent, local_id)
        or _agent_has_related_visibility_after(agent, created_at, content)
        or _message_superseded_by_manager_closeout(agent, content, created_at)
    )


def _agent_has_specific_inbox_blocker(agent: str) -> bool:
    for msg in reversed(local_facts.list_messages(agent)):
        if not local_facts.is_high_priority(str(msg.get("priority") or "")):
            continue
        ack_state = str(msg.get("ack_state") or "pending")
        if not bool(msg.get("read")):
            return True
        if ack_state not in {"agent_acknowledged", "action_started"}:
            return True
    return False


def _manager_observation_resolved_by_visible_terminal(content: str, agent: str, created_at: int) -> bool:
    tokens = _visibility_tokens(content)
    if not tokens:
        return False
    for surface_agent in (agent, "manager"):
        for row in local_facts.list_logs(surface_agent, limit=30):
            if int(row.get("created_at") or 0) < created_at:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed"}:
                continue
            row_content = str(row.get("content") or "")
            lowered = row_content.lower()
            terminal = (
                "pass" in lowered
                or "verdict" in lowered
                or "closeout" in lowered
                or "已交付" in row_content
                or "复核完成" in row_content
                or "验收通过" in row_content
            )
            if not terminal:
                continue
            if tokens & _visibility_tokens(row_content):
                return True
    return False


def _secondhand_visibility_findings(*, now: int) -> list[dict]:
    rows: list[dict] = []
    tracked_agents = ("worker_course", "review_course", "worker_builder", "worker_qbank")
    manager_markers = (
        "正在工作",
        "正在生产",
        "正在生成",
        "正在复核",
        "正在进行",
        "在跑",
        "运行中",
    )
    for row in local_facts.list_logs("manager", limit=20):
        created_at = int(row.get("created_at") or 0)
        if now - created_at > SECONDHAND_VISIBILITY_WINDOW_MS:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        if not any(marker in content for marker in manager_markers):
            continue
        for agent in tracked_agents:
            if agent not in content:
                continue
            age_ms = max(now - created_at, 0)
            if age_ms < SECONDHAND_VISIBILITY_THRESHOLD_MS:
                continue
            if _agent_has_specific_inbox_blocker(agent):
                continue
            if _agent_has_direct_visibility_after(agent, created_at):
                continue
            if _manager_observation_resolved_by_visible_terminal(content, agent, created_at):
                continue
            rows.append({
                "category": "secondhand_worker_visibility",
                "task_id": f"visibility:{agent}",
                "message_id": str(row.get("local_id") or ""),
                "stage": "visibility",
                "status": "manager_observed_worker_active",
                "severity": "warn",
                "age_ms": age_ms,
                "why": (
                    f"manager 已通报 {agent} 正在工作，但 {agent} 没有自己的 "
                    "started/say 过程信号；老板看到的是二手外显"
                ),
                "evidence_summary": (
                    f"manager_log={row.get('local_id') or '-'} agent={agent} "
                    f"created_at={created_at} content={content[:120]}"
                ),
                "recommended_action": "request_agent_direct_process_signal",
            })
    return rows


def _secondhand_acceptance_conflict_findings(*, now: int) -> list[dict]:
    rows: list[dict] = []
    tracked_agents = ("worker_course", "review_course", "worker_builder", "worker_qbank")
    manager_claim_markers = ("已接单", "已受理", "正在处理", "正在执行", "开始处理")
    for row in local_facts.list_logs("manager", limit=20):
        created_at = int(row.get("created_at") or 0)
        if now - created_at > SECONDHAND_VISIBILITY_WINDOW_MS:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        if not any(marker in content for marker in manager_claim_markers):
            continue
        manager_tokens = _visibility_tokens(content)
        if not manager_tokens:
            continue
        for agent in tracked_agents:
            if agent not in content:
                continue
            agent_claim_text = ""
            for segment in re.split(r"[\n。；;]", content):
                if agent in segment and any(marker in segment for marker in manager_claim_markers):
                    agent_claim_text = segment.strip()
                    break
            if not agent_claim_text:
                continue
            claim_tokens = _visibility_tokens(agent_claim_text)
            for msg in reversed(local_facts.list_messages(agent, unread_only=True)):
                if not local_facts.is_high_priority(str(msg.get("priority") or "")):
                    continue
                msg_content = str(msg.get("content") or "")
                msg_tokens = _visibility_tokens(msg_content)
                matched_tokens = claim_tokens & msg_tokens
                if not matched_tokens:
                    continue
                rows.append({
                    "category": "secondhand_acceptance_conflict",
                    "task_id": str(msg.get("task_id") or msg.get("local_id") or f"visibility:{agent}"),
                    "message_id": str(msg.get("local_id") or ""),
                    "stage": "visibility",
                    "status": "manager_claim_conflicts_with_agent_inbox",
                    "severity": "warn",
                    "age_ms": max(now - created_at, 0),
                    "why": (
                        f"manager 声称 {agent} 已接单/处理中，但 {agent} 自己仍有同范围高优未读；"
                        "不能把二手状态当作 agent 已在岗"
                    ),
                    "evidence_summary": (
                        f"manager_log={row.get('local_id') or '-'} agent={agent} "
                        f"manager_tokens={','.join(sorted(matched_tokens))} "
                        f"inbox_message={msg.get('local_id') or '-'} "
                        f"manager_content={agent_claim_text[:120]} inbox_content={msg_content[:120]}"
                    ),
                    "recommended_action": "request_agent_explicit_ack_or_runtime_blocker",
                })
                break
    return rows


def _facts_process_visibility_stale_findings(*, now: int) -> list[dict]:
    """Flag facts-only active surfaces that have gone quiet.

    Flow-task checks cover normal production tasks. Qbank/runtime repair lines
    can still live mostly in facts/status, so this keeps a stale "进行中" row
    from looking like fresh work without rewriting the status itself.
    """
    rows: list[dict] = []
    active_task_agents = {
        _task_lane_owner(task)
        for task in _active_flow_tasks()
        if str(task.get("status") or "") == "in_progress"
    }
    for agent in DIRECT_VISIBILITY_AGENTS:
        provider_block = local_facts.provider_quota_block_evidence(agent)
        if provider_block is not None:
            status = local_facts.get_status(agent) or {}
            status_at = int(status.get("updated_at") or 0)
            evidence_at = int(provider_block.get("created_at") or status_at)
            rows.append({
                "category": "facts_process_visibility_stale",
                "task_id": f"facts:{agent}",
                "agent": agent,
                "stage": "facts",
                "status": "runtime_blocked_provider_quota",
                "severity": "warn",
                "live_blocker": True,
                "age_ms": max(now - evidence_at, 0),
                "why": (
                    f"{agent} 缺少新的直接过程信号，但 manager 已核实 Qoder "
                    "Credits exhausted/FORBIDDEN；这不是新鲜实做，应按运行时阻断处理"
                ),
                "evidence_summary": (
                    f"agent={agent} status={status.get('status') or '-'} "
                    f"status_updated_at={status_at} "
                    f"manager_log={provider_block.get('local_id') or '-'} "
                    f"manager_content={str(provider_block.get('content') or '')[:180]}"
                ),
                "recommended_action": "restore_provider_quota_or_reassign_runtime",
            })
            continue
        if agent in active_task_agents:
            continue
        status = local_facts.get_status(agent) or {}
        state = str(status.get("status") or "")
        if state not in {"已接单", "进行中"}:
            continue
        task_text = str(status.get("task") or "")
        if agent == "auto_ops" and any(marker in task_text for marker in CONTINUING_WATCH_MARKERS):
            continue
        status_at = int(status.get("updated_at") or 0)
        latest_log_at = 0
        for row in local_facts.list_logs(agent, limit=12):
            if str(row.get("type") or "") not in {
                "say",
                "worker_course_started",
                "review_course_started",
                "worker_builder_started",
                "worker_started",
                "qbank_followup",
                "task_completed",
                "task",
            }:
                continue
            latest_log_at = max(latest_log_at, int(row.get("created_at") or 0))
        last_signal = max(status_at, latest_log_at)
        if not last_signal:
            continue
        age_ms = max(now - last_signal, 0)
        if age_ms < PROCESS_VISIBILITY_STALE_THRESHOLD_MS:
            continue
        rows.append({
            "category": "facts_process_visibility_stale",
            "task_id": f"facts:{agent}",
            "agent": agent,
            "stage": "facts",
            "status": "active_surface_stale",
            "severity": "info",
            "live_blocker": False,
            "age_ms": age_ms,
            "why": (
                f"{agent} facts/status 仍显示{state}，但 {age_ms // 60000}m "
                "内没有新的直接过程信号；应视为外显陈旧，而不是新鲜实做"
            ),
            "evidence_summary": (
                f"agent={agent} status={state} status_updated_at={status_at} "
                f"latest_process_log_at={latest_log_at} "
                f"status_task={task_text[:160]}"
            ),
            "recommended_action": "request_lightweight_process_update",
        })
    return rows


def _facts_accepted_without_started_findings(*, now: int) -> list[dict]:
    rows: list[dict] = []
    for agent in DIRECT_VISIBILITY_AGENTS:
        status = local_facts.get_status(agent) or {}
        if str(status.get("status") or "") != "已接单":
            continue
        status_at = int(status.get("updated_at") or 0)
        age_ms = max(now - status_at, 0)
        if age_ms < ACCEPTED_WITHOUT_STARTED_THRESHOLD_MS:
            continue
        status_task = str(status.get("task") or "")
        scope_tokens = _visibility_tokens(status_task)
        if not scope_tokens:
            continue
        has_followthrough = False
        for row in local_facts.list_logs(agent, limit=12):
            created_at = int(row.get("created_at") or 0)
            if created_at <= status_at:
                continue
            if str(row.get("type") or "") not in {
                "say",
                "worker_course_started",
                "review_course_started",
                "worker_builder_started",
                "worker_started",
                "qbank_followup",
                "task_completed",
                "task",
            }:
                continue
            content = str(row.get("content") or "")
            lowered = content.lower()
            progressed = (
                "开始" in content
                or "正在" in content
                or "完成" in content
                or "交付" in content
                or "pass" in lowered
                or "verdict" in lowered
                or "blocked" in lowered
                or "卡" in content
            )
            if progressed and scope_tokens & _visibility_tokens(content):
                has_followthrough = True
                break
        if has_followthrough:
            continue
        rows.append({
            "category": "accepted_without_started_signal",
            "task_id": f"facts:{agent}",
            "agent": agent,
            "stage": "facts",
            "status": "accepted_waiting_started_signal",
            "severity": "warn",
            "live_blocker": False,
            "age_ms": age_ms,
            "why": (
                f"{agent} 已接单 {age_ms // 60000}m，但还没有同范围 started/process/blocker 信号；"
                "manager 会看到接单，却看不出是否真的开始"
            ),
            "evidence_summary": (
                f"agent={agent} status_updated_at={status_at} "
                f"scope_tokens={','.join(sorted(scope_tokens))} "
                f"status_task={status_task[:180]}"
            ),
            "recommended_action": "request_started_or_blocker_signal",
        })
    return rows


def _recent_agent_evidence(agent: str, *, limit: int = 20) -> list[dict]:
    rows = [
        row for row in local_facts.list_logs(agent, limit=limit)
        if str(row.get("type") or "") in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
            "task",
        }
    ]
    return sorted(rows, key=lambda row: int(row.get("created_at") or 0))


def _text_has_any(text: str, markers: tuple[str, ...]) -> bool:
    value = str(text or "")
    lowered = value.lower()
    return any(marker in lowered or marker in value for marker in markers)


def _is_context_exhaustion_text(text: str) -> bool:
    signal = context_monitor.detect_context_usage(text)
    return bool(signal and signal.exhausted) or _text_has_any(text, CONTEXT_EXHAUSTION_MARKERS)


def _context_usage_signal(text: str) -> context_monitor.ContextUsageSignal | None:
    signal = context_monitor.detect_context_usage(text)
    if signal:
        return signal
    if _text_has_any(text, CONTEXT_EXHAUSTION_MARKERS):
        return context_monitor.ContextUsageSignal(None, "exhausted", "cli_readiness_failure")
    return None


def _is_production_text(text: str) -> bool:
    return _text_has_any(text, PRODUCTION_MARKERS)


def _open_high_priority_unacked_messages(agent: str) -> list[dict]:
    rows = []
    for msg in local_facts.list_messages(agent):
        if not local_facts.is_high_priority(str(msg.get("priority") or "")):
            continue
        ack_state = str(msg.get("ack_state") or "pending")
        if (not bool(msg.get("read"))) or ack_state not in {
            "agent_acknowledged",
            "action_started",
            "completed",
            "reconciled",
        }:
            rows.append(msg)
    return rows


def _worker_context_guard_findings(*, now: int) -> list[dict]:
    rows: list[dict] = []
    for agent in sorted(WORKER_CONTEXT_GUARD_AGENTS):
        status = local_facts.get_status(agent) or {}
        status_at = int(status.get("updated_at") or 0)
        status_text = " ".join(
            str(status.get(key) or "") for key in ("status", "task", "blocker")
        ).strip()
        evidence_rows = _recent_agent_evidence(agent)
        latest_evidence = evidence_rows[-1] if evidence_rows else {}
        latest_content = str(latest_evidence.get("content") or "")
        latest_at = int(latest_evidence.get("created_at") or 0)
        combined = " ".join([status_text, latest_content])

        context_signal = _context_usage_signal(combined)
        if context_signal and context_signal.exhausted:
            marker_source = latest_content if _context_usage_signal(latest_content) else status_text
            rows.append({
                "category": "worker_context_exhausted",
                "task_id": f"runtime:{agent}",
                "agent": agent,
                "affected_agent": agent,
                "stage": "runtime",
                "status": "context_exhausted",
                "severity": "error",
                "live_blocker": True,
                "allow_continue_original_task": False,
                "inbox_recovery_needed": True,
                "age_ms": max(now - max(latest_at, status_at), 0) if max(latest_at, status_at) else 0,
                "why": (
                    f"{agent} surface contains context/CLI readiness failure markers; "
                    "pane ready must not be treated as safe long-context execution"
                ),
                "evidence_summary": (
                    f"affected_agent={agent} latest_log={latest_evidence.get('local_id') or '-'} "
                    f"status={status.get('status') or '-'} "
                    f"status_updated_at={status_at} "
                    f"latest_evidence={marker_source[:180]}"
                ),
                "recommended_action": "restart_worker_runtime",
            })
        elif context_signal and context_signal.compact_recommended:
            marker_source = latest_content if _context_usage_signal(latest_content) else status_text
            rows.append({
                "category": "worker_context_compact_recommended",
                "task_id": f"runtime:{agent}",
                "agent": agent,
                "affected_agent": agent,
                "stage": "runtime",
                "status": "context_near_limit",
                "severity": "warn",
                "live_blocker": False,
                "allow_continue_original_task": False,
                "inbox_recovery_needed": False,
                "age_ms": max(now - max(latest_at, status_at), 0) if max(latest_at, status_at) else 0,
                "why": (
                    f"{agent} context is near the limit; compact and reidentify before "
                    "continuing broad or long-running work"
                ),
                "evidence_summary": (
                    f"affected_agent={agent} {context_signal.marker} "
                    f"latest_log={latest_evidence.get('local_id') or '-'} "
                    f"status={status.get('status') or '-'} "
                    f"status_updated_at={status_at} "
                    f"latest_evidence={marker_source[:180]}"
                ),
                "recommended_action": "run_eduflow_compact_before_long_work",
            })
        elif context_signal and context_signal.warning:
            marker_source = latest_content if _context_usage_signal(latest_content) else status_text
            rows.append({
                "category": "worker_context_usage_warning",
                "task_id": f"runtime:{agent}",
                "agent": agent,
                "affected_agent": agent,
                "stage": "runtime",
                "status": "context_warning",
                "severity": "warn",
                "live_blocker": False,
                "allow_continue_original_task": True,
                "inbox_recovery_needed": False,
                "age_ms": max(now - max(latest_at, status_at), 0) if max(latest_at, status_at) else 0,
                "why": (
                    f"{agent} context usage is high; monitor or split the next work packet "
                    "before it reaches the compact threshold"
                ),
                "evidence_summary": (
                    f"affected_agent={agent} {context_signal.marker} "
                    f"latest_log={latest_evidence.get('local_id') or '-'} "
                    f"status={status.get('status') or '-'} "
                    f"status_updated_at={status_at} "
                    f"latest_evidence={marker_source[:180]}"
                ),
                "recommended_action": "monitor_context_and_split_next_packet",
            })

        open_msgs = _open_high_priority_unacked_messages(agent)
        if open_msgs:
            latest_msg = open_msgs[-1]
            msg_created = int(latest_msg.get("created_at") or 0)
            producing = next(
                (
                    row for row in evidence_rows
                    if int(row.get("created_at") or 0) >= msg_created
                    and _is_production_text(str(row.get("content") or ""))
                ),
                None,
            )
            if producing is not None:
                rows.append({
                    "category": "worker_high_priority_unacked_while_producing",
                    "task_id": str(latest_msg.get("task_id") or latest_msg.get("local_id") or f"runtime:{agent}"),
                    "message_id": str(latest_msg.get("local_id") or ""),
                    "agent": agent,
                    "affected_agent": agent,
                    "stage": "inbox",
                    "status": "unsafe_unacked_execution",
                    "severity": "error",
                    "live_blocker": True,
                    "allow_continue_original_task": False,
                    "inbox_recovery_needed": True,
                    "age_ms": max(now - msg_created, 0),
                    "why": (
                        f"{agent} has high-priority inbox work without ACK/read recovery, "
                        "but later log evidence shows it is still producing"
                    ),
                    "evidence_summary": (
                        f"affected_agent={agent} message_id={latest_msg.get('local_id') or '-'} "
                        f"read={str(bool(latest_msg.get('read'))).lower()} "
                        f"ack_state={latest_msg.get('ack_state') or 'pending'} "
                        f"latest_log={producing.get('local_id') or '-'} "
                        f"latest_evidence={str(producing.get('content') or '')[:180]}"
                    ),
                    "recommended_action": "interrupt_old_context_and_read_inbox",
                })

        if (
            _text_has_any(status_text, BLOCKED_STATUS_MARKERS)
            and latest_at >= status_at
            and _is_production_text(latest_content)
        ):
            rows.append({
                "category": "status_pane_truth_conflict",
                "task_id": f"runtime:{agent}",
                "agent": agent,
                "affected_agent": agent,
                "stage": "facts",
                "status": "status_blocked_but_pane_producing",
                "severity": "warn",
                "live_blocker": True,
                "allow_continue_original_task": False,
                "inbox_recovery_needed": False,
                "age_ms": max(now - latest_at, 0) if latest_at else 0,
                "why": (
                    f"{agent} status surface says blocked, but newer pane/log evidence "
                    "shows production; status and execution surfaces conflict"
                ),
                "evidence_summary": (
                    f"affected_agent={agent} status={status.get('status') or '-'} "
                    f"blocker={status.get('blocker') or '-'} "
                    f"status_updated_at={status_at} latest_log={latest_evidence.get('local_id') or '-'} "
                    f"latest_evidence={latest_content[:180]}"
                ),
                "recommended_action": "reassign_small_batch",
            })

    return rows


def _surface_state_status(task: dict, *, now: int) -> dict | None:
    agent = str(task.get("assignee") or "")
    desired = _surface_stage_state(task)
    if not agent or not desired:
        return None

    marker_text, updated_at, status_task = _status_surface_markers(agent)
    if not updated_at and not marker_text:
        return None
    markers = _truth_markers(task)
    if not markers:
        return None

    truth_present = any(marker in marker_text for marker in markers)
    stage_truth_present = False
    if desired == "delivered_to_review":
        stage_truth_present = any(
            marker in marker_text
            for marker in (
                "waiting review",
                "waiting for review",
                "ready for review",
                "submitted for review",
                "submitted to review",
                "等待 review",
                "等待 review_course",
                "交给 review",
                "交给 review_course",
                "交给 manager",
                "交给manager",
                "完成并交给 manager",
                "完成并交给manager",
                "送 review",
                "送审",
            )
        )
        truth_present = truth_present or stage_truth_present
    task_last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    age_ms = max(now - max(updated_at, task_last), 0)
    threshold = (
        REVIEW_STATUS_TRUTH_LAG_THRESHOLD_MS
        if agent == "review_course"
        else STATUS_TRUTH_LAG_THRESHOLD_MS
    )

    if desired == "delivered_to_review":
        visible_review = _visible_review_pass_for_task(task, after=max(updated_at - 1000, 0))
        if visible_review is not None:
            return {
                "surface_state": desired,
                "surface_truth_synced": True,
                "status_task": status_task,
                "truth_markers": markers,
                "truth_source": "visible_review_pass",
            }

    stale = bool(updated_at) and updated_at < task_last and age_ms >= 0 and not stage_truth_present
    lagged = (not truth_present) and (now - task_last >= threshold)
    if not stale and not lagged:
        return {
            "surface_state": desired,
            "surface_truth_synced": True,
            "status_task": status_task,
            "truth_markers": markers,
        }
    category = "status_truth_lag_detected" if lagged else "stale_status_surface"
    return {
        "surface_state": desired,
        "surface_truth_synced": False,
        "status_task": status_task,
        "truth_markers": markers,
        "category": category,
        "status_updated_at": updated_at,
        "task_last_meaningful_update_at": task_last,
        "age_ms": max(now - task_last, 0),
    }


def _surface_truth_finding(task: dict, *, now: int) -> dict | None:
    if _has_newer_active_task_for_same_lane(task):
        return None
    surface = _surface_state_status(task, now=now)
    if surface is None or surface.get("surface_truth_synced"):
        return None
    desired = str(surface.get("surface_state") or "")
    category = str(surface.get("category") or "status_truth_lag_detected")
    recommended_action = (
        "refresh_review_surface"
        if str(task.get("assignee") or "") == "review_course"
        else "refresh_worker_surface"
    )
    if str(task.get("assignee") or "") == "worker_builder":
        recommended_action = "refresh_builder_surface"
    elif str(task.get("assignee") or "") == "worker_qbank":
        recommended_action = "refresh_qbank_surface"
    return {
        "category": category,
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "age_ms": int(surface.get("age_ms") or 0),
        "surface_state": desired,
        "why": (
            f"{task_publish_render.describe_surface_state(desired)}，"
            f"但 {task.get('assignee') or '-'} 状态面未同步到当前真相"
        ),
        "evidence_summary": (
            f"assignee={task.get('assignee') or '-'} "
            f"status_task={surface.get('status_task') or '-'} "
            f"task_summary={tasks.flow_live_summary(task) or '-'} "
            f"status_updated_at={surface.get('status_updated_at') or 0} "
            f"task_last_meaningful_update_at={surface.get('task_last_meaningful_update_at') or 0}"
        ),
        "recommended_action": recommended_action,
    }


def _runtime_guard_state() -> dict:
    return read_json(paths.runtime_guard_state_file(), {"agents": {}})


def _watchdog_rows() -> list[dict]:
    rows: list[dict] = []
    for spec in runtime_watchdog.all_known_specs():
        pid_present = spec.pid_file.exists()
        alive = runtime_watchdog.is_alive(spec) if pid_present else False
        rows.append({
            "name": spec.name,
            "pid_present": pid_present,
            "alive": alive,
        })
    supervisor_pid = paths.hermes_supervisor_pid_file()
    rows.append({
        "name": "hermes-supervisor",
        "pid_present": supervisor_pid.exists(),
        "alive": runtime_watchdog.is_alive(
            runtime_watchdog.ProcessSpec(
                name="hermes-supervisor",
                pid_file=supervisor_pid,
                expected_cmdline="hermes-supervisor-loop.sh",
                spawn_cmd=[],
                log_file=paths.hermes_supervisor_log_file(),
            )
        ) if supervisor_pid.exists() else False,
    })
    return rows


def _runtime_visibility_findings(*, now: int) -> list[dict]:
    rows = _watchdog_rows()
    unhealthy = [
        row for row in rows
        if row["name"] in {"router", "watchdog", "hermes-supervisor"}
        and (not row["pid_present"] or not row["alive"])
    ]
    if not unhealthy:
        return []
    evidence = " ".join(
        f"{row['name']}:pid={'yes' if row['pid_present'] else 'no'},alive={'yes' if row['alive'] else 'no'}"
        for row in rows
        if row["name"] in {"router", "watchdog", "hermes-supervisor", "task-publish"}
    )
    reason_parts = []
    if any(row["name"] == "router" and row["pid_present"] and not row["alive"] for row in unhealthy):
        reason_parts.append("router_pid_stale")
    if any(row["name"] == "router" and not row["pid_present"] for row in unhealthy):
        reason_parts.append("router_down")
    if any(row["name"] == "watchdog" and (not row["pid_present"] or not row["alive"]) for row in unhealthy):
        reason_parts.append("watchdog_down")
    if any(row["name"] == "hermes-supervisor" and (not row["pid_present"] or not row["alive"]) for row in unhealthy):
        reason_parts.append("hermes_supervisor_down")
    return [{
        "category": "runtime_visibility_unhealthy",
        "task_id": "runtime:watchdog-router",
        "stage": "runtime",
        "status": "runtime_health_degraded",
        "severity": "warn",
        "live_blocker": True,
        "age_ms": 0,
        "why": (
            "router/watchdog runtime health is degraded; live delivery may rely on catchup/respawn "
            "instead of steady event flow"
        ),
        "evidence_summary": f"reasons={','.join(reason_parts) or '-'} {evidence}",
        "recommended_action": "trigger_or_dispatch_runtime_repair",
    }]


def read_cursor() -> dict:
    return read_json(paths.task_publish_cursor_file(), {})


def read_explanation_state() -> dict:
    return read_json(paths.task_publish_explanations_file(), {"sent": {}})


def write_explanation_state(state: dict) -> None:
    write_json(paths.task_publish_explanations_file(), state)


def read_pending_state() -> dict:
    return read_json(paths.task_publish_pending_file(), {"pending": {}})


def write_pending_state(state: dict) -> None:
    write_json(paths.task_publish_pending_file(), state)


def read_close_loop_state() -> dict:
    return read_json(paths.task_publish_close_loop_file(), {"tasks": {}})


def write_close_loop_state(state: dict) -> None:
    write_json(paths.task_publish_close_loop_file(), state)


def read_supervisor_state() -> dict:
    return read_json(
        paths.task_supervisor_state_file(),
        {
            "last_check_at": 0,
            "last_health_status": "",
            "last_primary_reason": "",
            "consecutive_issue_count": 0,
            "last_repair_at": 0,
            "last_alert_at": 0,
        },
    )


def write_supervisor_state(state: dict) -> None:
    write_json(paths.task_supervisor_state_file(), state)


def _manager_action_apply_file():
    return paths.state_dir() / "manager-action-apply.json"


def read_manager_action_apply_state() -> dict:
    return read_json(_manager_action_apply_file(), {"applies": {}})


def write_manager_action_apply_state(state: dict) -> None:
    write_json(_manager_action_apply_file(), state)


def _apply_key(action_code: str, subject_id: str) -> str:
    return f"{subject_id}::{action_code}"


def write_cursor(event_id: str, created_at: int | str) -> None:
    if not event_id:
        return
    write_json(
        paths.task_publish_cursor_file(),
        {
            "event_id": str(event_id),
            "created_at": int(created_at or 0),
        },
    )


def _all_events() -> list[dict]:
    return read_jsonl(paths.task_events_file())


def _unseen_events(rows: list[dict], cursor: dict) -> list[dict]:
    cursor_event_id = str(cursor.get("event_id") or "")
    if not cursor_event_id:
        return rows
    seen_cursor = False
    tail: list[dict] = []
    for row in rows:
        if seen_cursor:
            tail.append(row)
            continue
        if str(row.get("event_id") or "") == cursor_event_id:
            seen_cursor = True
    if seen_cursor:
        return tail
    cursor_created_at = int(cursor.get("created_at") or 0)
    # Recovery path when the exact cursor event vanished from task-events.jsonl:
    # use created_at as a coarse fallback, but do not require a strictly newer
    # millisecond. Some tests and fast local writes can land the next task event
    # in the same ms bucket as the missing cursor event.
    return [
        r for r in rows
        if (
            int(r.get("created_at") or 0) >= cursor_created_at
            and str(r.get("event_id") or "") != cursor_event_id
        )
    ]


def _suggested_sender(event: dict) -> str:
    after = event.get("after") or {}
    status = str(after.get("status") or "")
    owner = str(after.get("owner") or "")
    actor = str(event.get("actor") or "")
    if status == "delivered" and owner:
        return owner
    if actor:
        return actor
    if owner:
        return owner
    return "manager"


def _is_progress_explanation_reason(reason: str) -> bool:
    return reason.startswith("user_explanation_") or reason.startswith("worker_")


def _explanation_state_has_reason(task_id: str, reason: str, state: dict | None = None) -> bool:
    if not task_id or not reason:
        return False
    current = state if state is not None else read_explanation_state()
    sent = current.get("sent", {})
    return f"{task_id}::{reason}" in sent


def _apply_explanation_dedupe(rows: list[dict], *, advance: bool) -> list[dict]:
    state = read_explanation_state()
    sent = state.setdefault("sent", {})
    kept: list[dict] = []
    changed = False

    for row in rows:
        reason = str(row.get("reason") or "")
        if not row.get("publish") or not _is_progress_explanation_reason(reason):
            kept.append(row)
            continue
        key = f"{row.get('task_id') or ''}::{reason}"
        if key in sent:
            row["publish"] = False
            row["cadence_action"] = "suppress_duplicate_update"
            row["cadence_reason"] = "duplicate_reassurance_reason"
            continue
        kept.append(row)
        if advance:
            sent[key] = str(row.get("event_id") or "")
            changed = True

    if advance and changed:
        write_explanation_state(state)
    return kept


def _close_loop_status(task_id: str, state: dict | None = None) -> dict:
    current = state if state is not None else read_close_loop_state()
    return dict((current.get("tasks") or {}).get(task_id) or {})


def _is_close_loop_reopen_event(row: dict) -> bool:
    reason = str(row.get("reason") or "")
    if reason in {"worker_started", "worker_completed_handed_to_manager", "worker_waiting_on_manager"}:
        return True
    return str(row.get("status") or "") in {"in_progress", "submitted_for_review", "blocked"}


def _apply_close_loop(rows: list[dict], *, advance: bool) -> list[dict]:
    state = read_close_loop_state()
    tasks_state = state.setdefault("tasks", {})
    changed = False
    output: list[dict] = []

    for row in rows:
        task_id = str(row.get("task_id") or "")
        status = _close_loop_status(task_id, state)
        current_state = str(status.get("state") or "open")
        reason = str(row.get("reason") or "")
        manager_response_type = str(row.get("manager_response_type") or "")
        row["close_loop_state"] = current_state
        row["close_loop_reason"] = str(status.get("reason") or "")

        if current_state in {"manager_result_closed", "manager_problem_closed"}:
            if _is_close_loop_reopen_event(row):
                row["close_loop_state"] = "reopen_after_new_meaningful_change"
                row["close_loop_reason"] = "new_meaningful_change_after_close"
                if advance:
                    tasks_state[task_id] = {
                        "state": "open",
                        "reason": "reopened_after_new_meaningful_change",
                        "event_id": str(row.get("event_id") or ""),
                    }
                    changed = True
            elif str(row.get("delivery_lane") or "") == "worker_reassurance":
                row["publish"] = False
                row["cadence_action"] = "suppress_low_signal_update"
                row["cadence_reason"] = "worker_reassurance_suppressed_after_close"
                row["close_loop_state"] = "worker_reassurance_suppressed_after_close"
                row["close_loop_reason"] = str(status.get("reason") or "manager_already_closed_loop")

        if manager_response_type == "final_result_delivered":
            row["close_loop_state"] = "manager_result_closed"
            row["close_loop_reason"] = "final_result_delivered"
            if advance:
                tasks_state[task_id] = {
                    "state": "manager_result_closed",
                    "reason": "final_result_delivered",
                    "event_id": str(row.get("event_id") or ""),
                }
                changed = True
        elif manager_response_type == "generic_manager_update_fallback" and row.get("publish"):
            row["close_loop_state"] = "manager_problem_closed"
            row["close_loop_reason"] = "generic_manager_update_fallback"
            if advance:
                tasks_state[task_id] = {
                    "state": "manager_problem_closed",
                    "reason": "generic_manager_update_fallback",
                    "event_id": str(row.get("event_id") or ""),
                }
                changed = True
        elif row["close_loop_state"] == "reopen_after_new_meaningful_change":
            pass
        else:
            if not row.get("close_loop_state"):
                row["close_loop_state"] = "open"
                row["close_loop_reason"] = ""

        output.append(row)

    if advance and changed:
        write_close_loop_state(state)
    return output


def _apply_cadence_timing(rows: list[dict], *, advance: bool) -> list[dict]:
    state = read_pending_state()
    pending = state.setdefault("pending", {})
    changed = False
    output: list[dict] = []
    by_task: dict[str, list[dict]] = {}

    for row in rows:
        by_task.setdefault(str(row.get("task_id") or ""), []).append(row)

    for task_id, task_rows in by_task.items():
        has_manager_result = any(
            str(row.get("reason") or "") == "delivered_to_user"
            for row in task_rows
        )
        has_waiting = any(
            str(row.get("reason") or "") == "worker_waiting_on_manager"
            for row in task_rows
        )
        for row in task_rows:
            reason = str(row.get("reason") or "")
            key = f"{task_id}::{reason}"

            if reason == "worker_completed_handed_to_manager" and has_manager_result:
                row["publish"] = False
                row["cadence_action"] = "merge_with_next_update"
                row["cadence_reason"] = "manager_result_ready_in_same_batch"
                if advance:
                    pending.pop(key, None)
                    changed = True
                output.append(row)
                continue

            if reason == "worker_completed_handed_to_manager" and has_waiting:
                row["publish"] = False
                row["cadence_action"] = "merge_with_next_update"
                row["cadence_reason"] = "waiting_on_manager_followed_immediately"
                if advance:
                    pending.pop(key, None)
                    changed = True
                output.append(row)
                continue

            if reason == "worker_waiting_on_manager":
                if row.get("cadence_action") == "delay_and_wait":
                    if advance:
                        pending[key] = {
                            "event_id": str(row.get("event_id") or ""),
                            "created_at": int(row.get("created_at") or 0),
                        }
                        changed = True
                    output.append(row)
                    continue
                if advance:
                    pending.pop(key, None)
                    changed = True

            output.append(row)

    if advance and changed:
        write_pending_state(state)
    return output


def _worker_reassurance_recommended_action(task: dict) -> str:
    task_id = str(task.get("id") or "")
    explanation_state = read_explanation_state()
    close_loop = _close_loop_status(task_id)
    if str(close_loop.get("state") or "") in {"manager_result_closed", "manager_problem_closed"}:
        return "worker_reassurance_suppressed_after_close"
    if task.get("status") == "submitted_for_review":
        return "merge_with_next_update"
    if task.get("needs_manager_action"):
        state = read_pending_state()
        if _explanation_state_has_reason(task_id, "worker_waiting_on_manager", explanation_state):
            return "suppress_duplicate_update"
        if f"{task_id}::worker_waiting_on_manager" in state.get("pending", {}):
            return "delay_and_wait"
        return "send_now"
    for reason in (
        "worker_waiting_on_manager",
        "worker_completed_handed_to_manager",
        "worker_started",
        "worker_accepted",
    ):
        if _explanation_state_has_reason(task_id, reason, explanation_state):
            return "suppress_duplicate_update"
    return "send_worker_reassurance"


def scan_publish_decisions(*, to_target: str = "user",
                           include_silent: bool = False,
                           advance: bool = False) -> list[dict]:
    rows = _unseen_events(_all_events(), read_cursor())
    decisions: list[dict] = []
    for event in rows:
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender=_suggested_sender(event),
            to_target=to_target,
        )
        decision["event_id"] = str(event.get("event_id") or "")
        decision["created_at"] = int(event.get("created_at") or 0)
        decision["sender"] = decision.get("sender") or _suggested_sender(event)
        if include_silent or decision["publish"]:
            decisions.append(decision)
    decisions = _apply_cadence_timing(decisions, advance=advance)
    decisions = _apply_close_loop(decisions, advance=advance)
    decisions = _apply_explanation_dedupe(decisions, advance=advance)
    if advance and rows:
        last = rows[-1]
        write_cursor(str(last.get("event_id") or ""), int(last.get("created_at") or 0))
    return decisions


def _active_flow_tasks() -> list[dict]:
    return [
        row for row in tasks.list_tasks()
        if row.get("schema_version") == 2
        and row.get("status") not in {"delivered", "cancelled", "已完成", "已取消"}
    ]


def _task_events_by_id() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in _all_events():
        tid = str(row.get("task_id") or "")
        if not tid:
            continue
        grouped.setdefault(tid, []).append(row)
    return grouped


def _task_lane_owner(task: dict) -> str:
    return str(task.get("assignee") or task.get("owner") or "")


def _has_newer_active_task_for_same_lane(task: dict) -> bool:
    lane_owner = _task_lane_owner(task)
    if not lane_owner:
        return False
    task_id = str(task.get("id") or "")
    task_last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    for other in tasks.list_tasks():
        if other.get("schema_version") != 2:
            continue
        if str(other.get("id") or "") == task_id:
            continue
        if str(other.get("status") or "") in {"delivered", "cancelled"}:
            continue
        if _task_lane_owner(other) != lane_owner:
            continue
        other_last = int(other.get("last_meaningful_update_at") or other.get("updated_at") or 0)
        if other_last > task_last:
            return True
    return False


def _stale_finding(task: dict, *, now: int) -> dict | None:
    if _has_newer_active_task_for_same_lane(task):
        return None
    last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    age_ms = max(now - last, 0)
    if age_ms < STALE_TASK_THRESHOLD_MS:
        return None
    status = str(task.get("status") or "")
    recommended_action = (
        _worker_reassurance_recommended_action(task)
        if status in {"queued", "assigned", "in_progress"}
        else (
            tasks.recommended_manager_action(task)
            or "先确认当前卡点由 owner、reviewer 还是 manager 处理。"
        )
    )
    finding = {
        "category": "stale_task",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": status,
        "severity": "warn",
        "age_ms": age_ms,
        "why": (
            f"no meaningful progress for {age_ms // 60000}m "
            f"(threshold={STALE_TASK_THRESHOLD_MS // 60000}m)"
        ),
        "evidence_summary": (
            f"last_meaningful_update_at={last} "
            f"status={task.get('status') or '-'} owner={task.get('owner') or '-'} "
            f"semantic={tasks.flow_semantic_summary(task) or '-'}"
        ),
        "recommended_action": recommended_action,
    }
    # Attach a dry-run reassurance packet for IGCSE workflow-drive tasks only,
    # so manager-actions / manager-panel surfaces can offer the lightest move.
    if status in {"queued", "assigned", "in_progress"}:
        packet = _stale_reassurance_packet(task)
        if packet is not None:
            finding["action_packet"] = packet
            finding["recommended_action"] = packet["action_code"]
    return finding


def _process_visibility_stale_finding(task: dict, *, now: int) -> dict | None:
    if _has_newer_active_task_for_same_lane(task):
        return None
    if str(task.get("status") or "") != "in_progress":
        return None
    agent = _task_lane_owner(task)
    if agent not in DIRECT_VISIBILITY_AGENTS:
        return None
    status = local_facts.get_status(agent) or {}
    status_at = int(status.get("updated_at") or 0)
    recent_log_at = 0
    for row in local_facts.list_logs(agent, limit=12):
        if str(row.get("type") or "") not in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
            "task",
        }:
            continue
        recent_log_at = max(recent_log_at, int(row.get("created_at") or 0))
    last_signal = max(
        int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0),
        status_at,
        recent_log_at,
    )
    age_ms = max(now - last_signal, 0)
    if age_ms < PROCESS_VISIBILITY_STALE_THRESHOLD_MS:
        return None
    return {
        "category": "process_visibility_stale",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "info",
        "live_blocker": False,
        "age_ms": age_ms,
        "why": (
            f"{agent} 仍在进行中，但 {age_ms // 60000}m 内没有新的轻量过程信号；"
            "这不是失败，只是 live 在岗感会开始变弱"
        ),
        "evidence_summary": (
            f"assignee={agent} task_last_meaningful_update_at={task.get('last_meaningful_update_at') or task.get('updated_at') or 0} "
            f"status_updated_at={status_at} latest_process_log_at={recent_log_at} "
            f"status_task={str(status.get('task') or '')[:160]}"
        ),
        "recommended_action": "request_lightweight_process_update",
    }


def _manager_action_finding(task: dict, *, now: int) -> dict | None:
    if not task.get("needs_manager_action"):
        return None
    last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    age_ms = max(now - last, 0)
    is_overdue = age_ms >= MANAGER_ACTION_THRESHOLD_MS
    explanation_state = read_explanation_state()
    pending_state = read_pending_state()
    cadence_action = (
        "suppress_duplicate_update"
        if _explanation_state_has_reason(task["id"], "worker_waiting_on_manager", explanation_state)
        else (
            "delay_and_wait"
            if f"{task['id']}::worker_waiting_on_manager" in pending_state.get("pending", {})
            else "request_manager_decision"
        )
    )
    # Always produce a finding for manager_action tasks, but vary category/severity based on age
    if is_overdue:
        category = "manager_action_overdue"
        severity = "warn"
        why = (
            f"{tasks.flow_semantic_summary(task) or 'manager_action unresolved'} "
            f"for {age_ms // 60000}m "
            f"(threshold={MANAGER_ACTION_THRESHOLD_MS // 60000}m)"
        )
    else:
        category = "manager_action_pending"
        severity = "info"
        why = (
            f"{tasks.flow_semantic_summary(task) or 'manager_action pending'} "
            f"awaiting manager decision"
        )
    return {
        "category": category,
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": severity,
        "age_ms": age_ms,
        "why": why,
        "evidence_summary": (
            f"blocking_reason={task.get('blocking_reason') or '-'} "
            f"verdict={task.get('verdict') or '-'} reviewer={task.get('reviewer') or '-'} "
            f"manager_action={tasks.describe_manager_action_type(task.get('manager_action_type') or '') or '-'} "
            f"review_reason={tasks.describe_review_reason(task.get('review_reason') or '') or '-'}"
        ),
        "recommended_action": cadence_action,
    }


def _reject_resubmit_finding(task: dict, events: list[dict]) -> dict | None:
    reject_count = 0
    resubmit_count = 0
    for event in events:
        if str(event.get("event_type") or "") != "status_changed":
            continue
        after = event.get("after") or {}
        verdict = str(after.get("verdict") or event.get("verdict") or "")
        to_status = str(event.get("to_status") or "")
        from_status = str(event.get("from_status") or "")
        if verdict == "rejected" and to_status == "in_progress":
            reject_count += 1
        elif to_status == "submitted_for_review" and from_status == "in_progress":
            resubmit_count += 1
    loops = min(reject_count, resubmit_count)
    if loops < REJECT_RESUBMIT_THRESHOLD:
        return None
    return {
        "category": "reject_resubmit_loop",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "loop_count": loops,
        "why": (
            f"task hit {loops} reject/resubmit loops "
            f"(threshold={REJECT_RESUBMIT_THRESHOLD})"
        ),
        "evidence_summary": (
            f"rejects={reject_count} resubmits={resubmit_count} "
            f"current_verdict={task.get('verdict') or '-'} "
            f"review_reason={tasks.describe_review_reason(task.get('review_reason') or '') or '-'}"
        ),
        "recommended_action": (
            "send_manager_result"
            if str(task.get("verdict") or "") == "rejected"
            else (
                tasks.recommended_manager_action(task)
                or "先确认 reviewer 的主要退回原因，再决定是重做还是缩范围。"
            )
        ),
    }


def _subject_closeout_evidence(gate: dict) -> str:
    return (
        f"subject={gate.get('subject_name') or '-'} "
        f"qa_count={gate.get('qa_count') or 0} "
        f"item_count={gate.get('item_count') or 0} "
        f"qa_standard={gate.get('qa_standard') or '-'} "
        f"qa_range={gate.get('qa_min') or 0}-{gate.get('qa_max') or 0} "
        f"qbank_readiness={gate.get('qbank_readiness') or '-'} "
        f"review_status={gate.get('review_status') or '-'} "
        f"closeout_status={gate.get('closeout_status') or '-'}"
    )


def _apply_allowed(action_code: str) -> bool:
    return action_code in MANAGER_ACTION_APPLY_ALLOWLIST


def _is_workflow_drive_task(task: dict) -> bool:
    """Mirror of the manager-panel workflow-drive filter.

    Keeps the reassurance scope on IGCSE subject production only, so we do
    not spam manager-facing views for unrelated flow tasks.
    """
    if not isinstance(task, dict) or not task.get("id"):
        return False
    if task.get("schema_version") != 2:
        return False
    if str(task.get("status") or "") in {"delivered", "cancelled"}:
        return False
    if str(task.get("workflow_id") or "").strip():
        return True
    return tasks.is_igcse_course_task(
        title=str(task.get("title") or ""),
        stage=str(task.get("stage") or ""),
    )


def _stale_reassurance_packet(task: dict) -> dict | None:
    """Build a dry-run-only reassurance packet for an IGCSE workflow-drive task.

    The packet is never `apply_allowed`; manager must explicitly invoke
    `manager-action-apply send_lightweight_reassurance --confirm` if they want
    to follow through. This keeps the routine reassurance cycle out of the
    auto-apply allowlist.
    """
    if not _is_workflow_drive_task(task):
        return None
    status = str(task.get("status") or "")
    if status not in {"queued", "assigned", "in_progress"}:
        return None
    last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    age_ms = max(now_ms() - last, 0)
    subject_id = str(task.get("id") or "")
    subject_name = str(task.get("title") or "")
    suggested = (
        f"{subject_name} 已 {age_ms // 60000}m 没有新的轻量过程信号；"
        "建议发一次轻量 reassurance 询问 owner 当前进度，避免下次再被 stale_task 命中。"
    )
    packet = {
        "action_code": "send_lightweight_reassurance",
        "apply_allowed": False,
        "assignee": str(task.get("owner") or task.get("assignee") or "manager"),
        "task_stage": str(task.get("stage") or ""),
        "reason": "igcse subject production task is stale; lightweight reassurance needed",
        "subject_id": subject_id,
        "subject_name": subject_name,
        "evidence_summary": (
            f"status={status} last_meaningful_update_at={last} age_ms={age_ms}"
        ),
        "suggested_brief": suggested,
        "closeout_gate": {},
    }
    packet["execution_plan"] = {
        "plan_type": "manager_action_dry_run",
        "dry_run": True,
        "action_code": "send_lightweight_reassurance",
        "assignee": packet["assignee"],
        "task_stage": packet["task_stage"],
        "subject_id": subject_id,
        "subject_name": subject_name,
        "preconditions": ["igcse workflow drive task", "no fresh light signal"],
        "proposed_command": (
            f"eduflow task manager-action-apply send_lightweight_reassurance "
            f"--subject-id {subject_id} --confirm"
        ),
        "proposed_brief": suggested,
        "execution_policy": (
            "dry_run_only/requires_manager_confirmation/no_auto_dispatch/"
            "no_live_wakeup"
        ),
    }
    return packet


def _closeout_gate_summary(gate: dict) -> dict:
    return {
        "review_approved": bool(gate.get("closeout_gate_review_approved")),
        "evidence_present": bool(gate.get("closeout_gate_evidence_present")),
        "qa_standard_met": bool(gate.get("closeout_gate_qa_standard_met")),
        "qbank_ready": bool(gate.get("closeout_gate_qbank_ready")),
    }


def _build_closeout_packet(
    *,
    task: dict,
    gate: dict,
    evidence_summary: str,
    why: str,
    action_code: str,
    apply_allowed: bool,
    suggested_brief_override: str | None = None,
) -> dict:
    """Build the action_packet for `_subject_closeout_finding` with
    Package-3-aware overrides.

    When the latest authoritative verdict blocks closeout we
    substitute a `wait_for_*` action_code, mark apply_allowed=False,
    and overwrite `suggested_brief` with a hard-gate explanation so
    the manager-actions / manager-panel surfaces do NOT print a
    "manager 可以正式收口" line that contradicts the verdict.
    """
    if suggested_brief_override is None:
        packet = _subject_action_packet(
            action_code=action_code,
            gate=gate,
            evidence_summary=evidence_summary,
            reason=why,
        )
        return _packet_with_apply_allowed(packet, apply_allowed=apply_allowed)
    # Build a custom packet with the override brief.
    subject_id = str(gate.get("subject_id") or task.get("id") or "")
    subject_name = str(gate.get("subject_name") or task.get("title") or "")
    packet = {
        "action_code": action_code,
        "apply_allowed": apply_allowed,
        "assignee": "manager",
        "task_stage": "curriculum",
        "reason": why,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "evidence_summary": evidence_summary,
        "suggested_brief": suggested_brief_override,
        "closeout_gate": _closeout_gate_summary(gate),
    }
    packet["execution_plan"] = _execution_plan_for_packet(packet)
    return packet


def _subject_action_packet(
    *,
    action_code: str,
    gate: dict,
    evidence_summary: str,
    reason: str,
) -> dict:
    subject_id = str(gate.get("subject_id") or "")
    subject_name = str(gate.get("subject_name") or "")
    qa_count = int(gate.get("qa_count") or 0)
    item_count = int(gate.get("item_count") or 0)
    qa_min = int(gate.get("qa_min") or 0)
    qa_max = int(gate.get("qa_max") or 0)
    assignee = "manager"
    if action_code == "request_worker_course_expand_qa":
        assignee = "worker_course"
        missing_qa = max(qa_min - qa_count, 0)
        missing_items = max(qa_min - item_count, 0)
        suggested = (
            f"请 worker_course 返修 {subject_name}：当前 qa_count={qa_count}, "
            f"item_count={item_count}，标准范围 {qa_min}-{qa_max}；"
            f"还差 {max(missing_qa, missing_items)} 个可题库化 QA/item 后再提交 review。"
        )
    elif action_code == "block_closeout_until_quality_standard_met":
        assignee = "manager"
        suggested = (
            f"{subject_name} 当前 qa_count={qa_count}, item_count={item_count} "
            f"超出标准范围 {qa_min}-{qa_max}，请 manager 先决定是否拆分或要求重整，再收口。"
        )
    elif action_code in {"request_review_evidence_packet", "request_review_course_file_evidence"}:
        action_code = "request_review_course_file_evidence"
        assignee = "review_course"
        suggested = (
            f"请 review_course 补齐 {subject_name} 的文件级 evidence packet："
            "files_sampled、q_ids_checked、sampled_topic_count、missing_topic_count、"
            "path_naming_result 与 qbank_readiness。"
        )
    elif action_code == "request_subject_count_evidence":
        assignee = "review_course"
        suggested = (
            f"请 review_course 补齐 {subject_name} 的 qa_count / item_count，"
            f"按 {qa_min}-{qa_max} 标准确认是否可收口。"
        )
    elif action_code == "request_qbank_readiness_check":
        assignee = "worker_qbank"
        suggested = (
            f"请 worker_qbank 对 {subject_name} 做最小题库 readiness 验证："
            "mapping 是否完整、question directions 是否足够、QA 是否可直接转成题库素材。"
        )
    elif action_code == "approve_subject_for_qbank_seed":
        assignee = "manager"
        suggested = (
            f"{subject_name} 已达到 qbank_ready，可由 manager 确认可作为题库种子输入。"
        )
    elif action_code == "manager_formal_closeout":
        assignee = "manager"
        suggested = (
            f"{subject_name} review passed，evidence packet 已存在，QA 标准已达标；"
            "manager 可以正式收口。"
        )
    elif action_code == "wait_for_review_approval":
        assignee = "review_course"
        suggested = f"{subject_name} 尚未 review approved，请 review_course 先完成 verdict。"
    else:
        suggested = f"请 manager 查看 {subject_name or subject_id} 的异常并决定下一步。"
    packet = {
        "action_code": action_code,
        "apply_allowed": _apply_allowed(action_code),
        "assignee": assignee,
        "task_stage": "curriculum",
        "reason": reason,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "evidence_summary": evidence_summary,
        "suggested_brief": suggested,
        "closeout_gate": _closeout_gate_summary(gate),
    }
    packet["execution_plan"] = _execution_plan_for_packet(packet)
    return packet


def action_packet_preview_status(packet: dict) -> dict:
    return _base_apply_result({
        "action_code": str(packet.get("action_code") or ""),
        "subject_id": str(packet.get("subject_id") or ""),
        "suggested_brief": str(packet.get("suggested_brief") or ""),
        "execution_plan": packet.get("execution_plan") or _empty_execution_plan(),
    }, confirm=False)


def _execution_plan_for_packet(packet: dict) -> dict:
    action_code = str(packet.get("action_code") or "")
    assignee = str(packet.get("assignee") or "")
    stage = str(packet.get("task_stage") or "")
    subject_id = str(packet.get("subject_id") or "")
    subject_name = str(packet.get("subject_name") or "")
    suggested = str(packet.get("suggested_brief") or "")
    base = {
        "plan_type": "manager_action_dry_run",
        "dry_run": True,
        "action_code": action_code,
        "assignee": assignee,
        "task_stage": stage,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "preconditions": [],
        "proposed_command": "no-op",
        "proposed_brief": suggested,
        "execution_policy": "dry_run_only/requires_manager_confirmation/no_auto_dispatch",
    }
    if action_code == "manager_formal_closeout":
        base["preconditions"] = ["review approved", "evidence packet present", "QA standard met"]
        base["proposed_command"] = f"eduflow task manager-closeout {subject_id} --actor manager"
    elif action_code == "request_worker_course_expand_qa":
        base["preconditions"] = ["subject exists", "QA standard not met", "manager confirms rework"]
        base["proposed_command"] = (
            f"eduflow task dispatch worker_course \"{subject_name} QA volume repair\" "
            "--stage curriculum --owner worker_course"
        )
        base["proposed_brief"] = f"{suggested} 返修后必须回 review_course。"
    elif action_code in {"request_review_course_file_evidence", "request_subject_count_evidence"}:
        base["preconditions"] = ["review evidence incomplete", "manager confirms evidence recheck"]
        base["proposed_command"] = (
            f"eduflow task dispatch review_course \"{subject_name} evidence recheck\" "
            "--stage curriculum --owner review_course"
        )
        base["proposed_brief"] = (
            f"{suggested} 必须补 files_sampled、q_ids_checked、sampled_topic_count、"
            "missing_topic_count、path_naming_result、qbank_readiness。"
        )
    elif action_code == "request_qbank_readiness_check":
        base["preconditions"] = ["QA evidence present", "manager confirms qbank check"]
        base["proposed_command"] = (
            f"eduflow task dispatch worker_qbank \"{subject_name} qbank readiness check\" "
            "--stage qbank --owner worker_qbank"
        )
        base["proposed_brief"] = (
            f"{suggested} 输出 qbank_readiness verdict，并说明 mapping 完整性、"
            "question directions、QA 是否可转题库。"
        )
    elif action_code == "dispatch_next_subject_worker_course":
        base["preconditions"] = ["current subject closeout_completed", "next subject candidate exists"]
        base["proposed_command"] = (
            f"eduflow task dispatch worker_course \"{subject_name}\" "
            "--stage curriculum --owner worker_course"
        )
        base["proposed_brief"] = (
            f"{suggested} 先做计划、对齐 topic，目标 300-500 QA/item，完成后交 review_course。"
        )
    elif action_code == "no_next_subject_candidate":
        base["preconditions"] = ["current subject closeout_completed", "no next subject candidate"]
        base["proposed_command"] = "no-op"
    elif action_code == "approve_subject_for_qbank_seed":
        base["preconditions"] = ["qbank_ready", "manager confirms seed approval"]
        base["proposed_command"] = "no-op"
    elif action_code == "safe_task_review_approve":
        base["preconditions"] = ["visible PASS/verdict signal in review_course log", "task verdict still pending"]
        base["proposed_command"] = f"eduflow task review {subject_id} --actor review_course --approve"
        base["proposed_brief"] = f"{suggested} 基于 review_course 可见的 PASS 信号执行结构化审批。"
    return base


def _packet_with_apply_allowed(packet: dict, *, apply_allowed: bool) -> dict:
    updated = dict(packet)
    updated["apply_allowed"] = apply_allowed
    return updated


def _manager_boundary_packet(
    *,
    action_code: str,
    assignee: str,
    task_stage: str,
    subject_id: str,
    subject_name: str,
    evidence_summary: str,
    suggested_brief: str,
    reason: str,
) -> dict:
    packet = {
        "action_code": action_code,
        "apply_allowed": False,
        "assignee": assignee,
        "task_stage": task_stage,
        "reason": reason,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "evidence_summary": evidence_summary,
        "suggested_brief": suggested_brief,
        "closeout_gate": {},
    }
    packet["execution_plan"] = _execution_plan_for_packet(packet)
    return packet


def _manager_action_packet(action_code: str, subject_id: str) -> dict | None:
    for row in scan_manager_anomalies():
        packet = row.get("action_packet")
        if not isinstance(packet, dict):
            continue
        if (
            str(packet.get("action_code") or "") == action_code
            and str(packet.get("subject_id") or "") == subject_id
        ):
            return packet
    return None


def _description_marker(action_code: str, subject_id: str) -> str:
    return (
        f"manager_apply_action_code={action_code}\n"
        f"manager_apply_subject_id={subject_id}"
    )


def _existing_followup_task(action_code: str, subject_id: str) -> dict | None:
    marker = _description_marker(action_code, subject_id)
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        if str(task.get("status") or "") in _FOLLOWUP_TERMINAL_STATUSES:
            continue
        description = str(task.get("description") or "")
        if marker in description:
            return task
    return None


def _empty_execution_plan() -> dict:
    return {
        "plan_type": "manager_action_dry_run",
        "dry_run": True,
        "execution_policy": "dry_run_only/requires_manager_confirmation/no_auto_dispatch",
        "proposed_command": "no-op",
        "proposed_brief": "",
        "preconditions": [],
    }


def _normalize_apply_result(result: dict) -> dict:
    normalized = {
        "applied": False,
        "action_code": "",
        "subject_id": "",
        "apply_mode": "",
        "apply_reason": "",
        "created_task_id": "",
        "updated_subject_id": "",
        "existing_task_id": "",
        "apply_summary": "",
        "execution_plan": {},
    }
    normalized.update(result or {})
    normalized["applied"] = bool(normalized.get("applied"))
    for key in (
        "action_code",
        "subject_id",
        "apply_mode",
        "apply_reason",
        "created_task_id",
        "updated_subject_id",
        "existing_task_id",
        "apply_summary",
    ):
        normalized[key] = str(normalized.get(key) or "")
    if not isinstance(normalized.get("execution_plan"), dict):
        normalized["execution_plan"] = {}
    return normalized


def _already_exists_apply_result(action_code: str, subject_id: str, existing: dict) -> dict:
    existing_id = str(existing.get("id") or "")
    return _normalize_apply_result({
        "applied": False,
        "action_code": action_code,
        "subject_id": subject_id,
        "apply_mode": "confirmed",
        "apply_reason": "already_exists",
        "existing_task_id": existing_id,
        "apply_summary": f"未重复创建，已有未完成 follow-up task {existing_id}",
    })


def _apply_state_for(action_code: str, subject_id: str) -> dict:
    state = read_manager_action_apply_state()
    result = dict((state.get("applies") or {}).get(_apply_key(action_code, subject_id)) or {})
    existing = _existing_followup_task(action_code, subject_id)
    if existing is not None:
        result.update(_already_exists_apply_result(action_code, subject_id, existing))
    if result:
        return _normalize_apply_result(result)
    return {}


def manager_action_apply_status(action_code: str, subject_id: str) -> dict:
    return _apply_state_for(str(action_code or ""), str(subject_id or ""))


def _record_apply_result(result: dict) -> dict:
    result = _normalize_apply_result(result)
    state = read_manager_action_apply_state()
    applies = state.setdefault("applies", {})
    applies[_apply_key(str(result.get("action_code") or ""), str(result.get("subject_id") or ""))] = result
    write_manager_action_apply_state(state)
    return result


def _base_apply_result(packet: dict, *, confirm: bool) -> dict:
    return _normalize_apply_result({
        "applied": False,
        "action_code": str(packet.get("action_code") or ""),
        "subject_id": str(packet.get("subject_id") or ""),
        "apply_mode": "confirmed" if confirm else "dry_run",
        "created_task_id": "",
        "updated_subject_id": "",
        "existing_task_id": "",
        "apply_reason": "dry_run_preview",
        "apply_summary": str(packet.get("suggested_brief") or ""),
        "execution_plan": packet.get("execution_plan") or {},
    })


def _qa_delta_text(gate: dict) -> str:
    qa_count = int(gate.get("qa_count") or 0)
    item_count = int(gate.get("item_count") or 0)
    qa_min = int(gate.get("qa_min") or 0)
    qa_max = int(gate.get("qa_max") or 0)
    missing = max(qa_min - qa_count, qa_min - item_count, 0)
    excess = max(qa_count - qa_max, item_count - qa_max, 0)
    if missing:
        return f"缺 {missing} 个"
    if excess:
        return f"超 {excess} 个"
    return "数量在标准范围内"


def _apply_description(action_code: str, subject: dict, packet: dict) -> str:
    subject_id = str(packet.get("subject_id") or "")
    subject_name = str(packet.get("subject_name") or "")
    gate = tasks.subject_closeout_status(subject)
    evidence = subject.get("evidence_packet") or {}
    marker = _description_marker(action_code, subject_id)
    if action_code == "request_worker_course_expand_qa":
        return (
            f"{marker}\n"
            "manager_apply_source=confirmed\n\n"
            f"Subject: {subject_name}\n"
            f"Current qa_count={gate.get('qa_count') or 0}, item_count={gate.get('item_count') or 0}.\n"
            f"Standard range: {gate.get('qa_min') or 0}-{gate.get('qa_max') or 0} QA/item.\n"
            f"Gap: {_qa_delta_text(gate)}.\n"
            "After repair, submit back to review_course before any manager closeout."
        )
    if action_code == "request_review_course_file_evidence":
        return (
            f"{marker}\n"
            "manager_apply_source=confirmed\n\n"
            f"Subject: {subject_name}\n"
            f"files_sampled={evidence.get('files_sampled') or []}\n"
            f"q_ids_checked={evidence.get('q_ids_checked') or []}\n"
            f"sampled_topic_count={evidence.get('sampled_topic_count') or 0}\n"
            f"missing_topic_count={evidence.get('missing_topic_count') or 0}\n"
            f"path_naming_result={evidence.get('path_naming_result') or '-'}\n"
            f"qbank_readiness={evidence.get('qbank_readiness') or '-'}\n"
            "补 evidence packet，不直接改 verdict。"
        )
    if action_code == "request_qbank_readiness_check":
        return (
            f"{marker}\n"
            "manager_apply_source=confirmed\n\n"
            f"Subject: {subject_name}\n"
            "Check mapping completeness.\n"
            "Check question directions.\n"
            "Check whether QA can be converted into qbank material.\n"
            "Return a final qbank_readiness verdict."
        )
    if action_code == "dispatch_next_subject_worker_course":
        return (
            f"{marker}\n"
            "manager_apply_source=confirmed\n\n"
            f"Subject: {subject_name}\n"
            "先做计划。\n"
            "对齐 topic。\n"
            "目标 300-500 QA/item。\n"
            "完成后交 review_course。"
        )
    return f"{marker}\nmanager_apply_source=confirmed\n\n{packet.get('suggested_brief') or ''}"


def _create_internal_followup(action_code: str, packet: dict) -> str:
    subject_id = str(packet.get("subject_id") or "")
    subject = tasks.get(subject_id) or {}
    if not subject:
        raise ValueError(f"no such subject: {subject_id}")
    assignee_by_action = {
        "request_worker_course_expand_qa": ("worker_course", "curriculum", "worker_course", "QA volume repair"),
        "request_review_course_file_evidence": ("review_course", "curriculum", "review_course", "evidence recheck"),
        "request_qbank_readiness_check": ("worker_qbank", "qbank", "worker_qbank", "qbank readiness check"),
        "dispatch_next_subject_worker_course": ("worker_course", "curriculum", "worker_course", "curriculum production"),
    }
    assignee, stage, owner, suffix = assignee_by_action[action_code]
    title = f"{packet.get('subject_name') or subject.get('title') or subject_id} {suffix}"
    return tasks.create_flow(
        assignee,
        title,
        stage=stage,
        owner=owner,
        creator="manager",
        description=_apply_description(action_code, subject, packet),
        status="assigned",
        emit_event=False,
    )


def _rollover_preconditions_met(subject_id: str) -> bool:
    inventory = tasks.subject_inventory()
    has_closed_source = any(row.get("closeout_status") == "closeout_completed" for row in inventory)
    has_candidate = any(
        str(row.get("subject_id") or "") == subject_id
        and int(row.get("next_candidate_rank") or 0) == 1
        for row in inventory
    )
    return has_closed_source and has_candidate


def manager_action_apply(action_code: str, subject_id: str, *,
                         confirm: bool = False,
                         skip_subject_verifier: bool = False) -> dict:
    action_code = str(action_code or "").strip()
    subject_id = str(subject_id or "").strip()
    packet = _manager_action_packet(action_code, subject_id)
    if packet is None:
        packet = {
            "action_code": action_code,
            "subject_id": subject_id,
            "suggested_brief": "",
            "execution_plan": _empty_execution_plan(),
        }
    result = _base_apply_result(packet, confirm=confirm)
    if action_code not in MANAGER_ACTION_APPLY_ALLOWLIST:
        result["apply_reason"] = "not_allowed_dry_run_only"
        result["apply_summary"] = (
            f"{action_code or '-'} 本轮只保留为 dry-run 建议，不执行 apply。"
        )
        return _record_apply_result(result) if confirm else result
    # Package 7 (Revision-First Gate): block any apply that would
    # pivot production away from the open revision. This catches the
    # `dispatch_next_subject_worker_course` rollover path which is in
    # the apply-allowlist but must be held while a revision is open.
    if action_code in REVISION_FIRST_BLOCKED_APPLY_ACTIONS and tasks.has_active_revision_priority():
        result["apply_reason"] = "precondition_failed_revision_first"
        result["apply_summary"] = (
            f"{action_code} blocked: revision-first gate is active. "
            "Clear revision_priority on the active task before applying this action."
        )
        return _record_apply_result(result)
    if not confirm:
        return result

    if action_code != "manager_formal_closeout":
        existing = _existing_followup_task(action_code, subject_id)
        if existing is not None:
            existing_result = _already_exists_apply_result(action_code, subject_id, existing)
            existing_result["execution_plan"] = result.get("execution_plan") or {}
            return _record_apply_result(existing_result)

    try:
        if action_code == "safe_task_review_approve":
            task = tasks.get(subject_id)
            if task is None:
                result["apply_reason"] = "subject_not_found"
                result["apply_summary"] = f"no such task: {subject_id}"
                return _record_apply_result(result)
            if str(task.get("status") or "") != "submitted_for_review" or str(task.get("verdict") or "") != "pending":
                result["apply_reason"] = "precondition_failed"
                result["apply_summary"] = (
                    "safe review approve requires submitted_for_review with verdict=pending."
                )
                return _record_apply_result(result)
            reviewer = str(task.get("reviewer") or "review_course")
            ok = tasks.review_flow(
                subject_id,
                outcome="approve",
                actor=reviewer,
                review_reason="approved_for_delivery",
                latest_turn_summary="Structured review truth reconciled from visible PASS signal.",
            )
            if not ok:
                result["apply_reason"] = "subject_not_found"
                result["apply_summary"] = f"no such task: {subject_id}"
                return _record_apply_result(result)
            result.update({
                "applied": True,
                "apply_reason": "review_approved",
                "updated_subject_id": subject_id,
                "apply_summary": "manager confirmed apply: task review approved from visible PASS signal.",
            })
            return _record_apply_result(result)

        if action_code == "manager_formal_closeout":
            subject = tasks.get(subject_id)
            gate = tasks.subject_closeout_status(subject)
            if gate.get("closeout_status") == "closeout_completed":
                result.update({
                    "applied": False,
                    "apply_reason": "already_applied",
                    "updated_subject_id": subject_id,
                    "apply_summary": "subject 已经 closeout_completed，未重复收口。",
                })
                return _record_apply_result(result)
            # Package 7 (Revision-First Gate): the closeout path here
            # is for the legacy closeout contract that accepts the
            # REVIEW_EVIDENCE_FIELDS packet (10 fields). The new
            # REQUIRED_EVIDENCE_PACKET_FIELDS packet (6 fields) is
            # machine-checkable via `validate_evidence_packet()` and
            # surfaces as `evidence_packet_incomplete` findings from
            # the supervisor — those findings are escalated to
            # severity=error for closeout candidates. The supervisor
            # is the single source of truth, so we re-scan here and
            # block the apply if a `severity=error` finding exists
            # for this subject_id. The pre-existing
            # `test_task_manager_action_apply_confirm_closeout_without_publish_event`
            # test continues to pass because it builds a fully
            # populated packet (qa_count/item_count/etc.) that the
            # supervisor does not flag.
            from eduflow.store.task_event_scanner import (  # local import to avoid cycle
                _evidence_packet_incomplete_finding,
            )
            incomplete = [
                f for f in _evidence_packet_incomplete_finding()
                if f.get("task_id") == subject_id
                and f.get("severity") == "error"
            ]
            if incomplete:
                missing = incomplete[0].get("missing_fields") or []
                result.update({
                    "applied": False,
                    "apply_reason": "precondition_failed_evidence_packet_incomplete",
                    "updated_subject_id": subject_id,
                    "apply_summary": (
                        f"closeout blocked: evidence_packet is missing "
                        f"{','.join(missing)}. Ask the worker to submit a complete "
                        "packet (workflow_id, task_id, batch_range, items_count, "
                        "qql_count, manifest_evidence) before applying."
                    ),
                })
                return _record_apply_result(result)
            ok = tasks.manager_closeout_subject(
                subject_id, actor="manager", emit_event=False,
                skip_subject_verifier=skip_subject_verifier,
            )
            if not ok:
                result["apply_reason"] = "subject_not_found"
                result["apply_summary"] = f"no such subject: {subject_id}"
                return _record_apply_result(result)
            result.update({
                "applied": True,
                "apply_reason": "closeout_completed",
                "updated_subject_id": subject_id,
                "apply_summary": "manager confirmed apply: subject closeout_completed.",
            })
            return _record_apply_result(result)

        if action_code == "dispatch_next_subject_worker_course" and not _rollover_preconditions_met(subject_id):
            result["apply_reason"] = "precondition_failed"
            result["apply_summary"] = "rollover preconditions failed: need current closeout_completed and rank-1 next subject candidate."
            return _record_apply_result(result)

        created_id = _create_internal_followup(action_code, packet)
        result.update({
            "applied": True,
            "apply_reason": "created_internal_followup_task",
            "created_task_id": created_id,
            "apply_summary": f"created internal follow-up task {created_id}; no send/publish/agent wakeup.",
        })
        return _record_apply_result(result)
    except ValueError as exc:
        result["apply_reason"] = "precondition_failed"
        result["apply_summary"] = str(exc)
        return _record_apply_result(result)


def _subject_closeout_finding(task: dict) -> dict | None:
    closeout_signal_text = " ".join(
        str(task.get(key) or "")
        for key in ("title", "description", "latest_turn_summary")
    ).lower()
    if (
        not tasks.is_subject_completion_candidate(task)
        and str(task.get("closeout_status") or "") != "closeout_completed"
        and not any(
            marker in closeout_signal_text
            for marker in ("正式完成", "正式收口", "closeout")
        )
    ):
        return None
    gate = tasks.subject_closeout_status(task)
    status = str(gate.get("closeout_status") or "")
    if status in {"not_subject", "closeout_completed"}:
        return None
    # Package 3: if the latest authoritative verdict blocks closeout,
    # we MUST NOT emit a `manager_formal_closeout` action — even when
    # the static verdict field says approved — because QQL-only /
    # items-only / rejected / manager_action verdicts cannot satisfy
    # the subject closeout gate.
    latest_blocks, latest_block_reasons = tasks.latest_verdict_blocks_closeout(task)
    latest = task.get("latest_authoritative_verdict") or {}
    latest_scope = str(latest.get("verdict_scope") or "")
    review_authority_ok = bool(gate.get("closeout_gate_review_approved"))
    visible_verdict = _visible_review_pass_for_task(task)
    if status == "closeout_blocked_review_not_approved" and visible_verdict:
        evidence_summary = (
            f"{_subject_closeout_evidence(gate)} "
            f"visible_review_pass_log={visible_verdict.get('local_id') or '-'} "
            f"visible_review_pass_at={visible_verdict.get('created_at') or 0}"
        )
        finding = {
            "category": "subject_truth_sync_lag_detected",
            "task_id": task["id"],
            "stage": str(task.get("stage") or ""),
            "status": str(task.get("status") or ""),
            "severity": "info",
            "live_blocker": False,
            "structured_truth_lag": True,
            "truth_source": "visible_review_pass",
            "why": (
                "review_course has a visible PASS/verdict signal, but the structured task "
                "truth still does not carry verdict=approved; this is a structured truth lag, "
                "not a live availability blocker"
            ),
            "evidence_summary": evidence_summary,
            "recommended_action": "reconcile_task_truth_from_visible_verdict",
            "action_packet": _subject_action_packet(
                action_code="safe_task_review_approve",
                gate={
                    "subject_id": task["id"],
                    "subject_name": str(task.get("title") or gate.get("subject_name") or ""),
                    **gate,
                },
                evidence_summary=(
                    f"log_id={visible_verdict.get('local_id') or '-'} "
                    f"task_id={task['id']} "
                    f"reviewer={task.get('reviewer') or '-'} "
                    f"reason=visible_review_pass"
                ),
                reason="visible PASS/verdict signal detected but task verdict still pending",
            ),
        }
        return finding
    if status == "closeout_ready":
        category = "subject_closeout_ready"
        severity = "info"
        why = "subject review passed with evidence and valid QA/item count; manager formal closeout is ready"
    elif status in {
        "closeout_blocked_review_not_approved",
        "closeout_blocked_missing_evidence",
        "review_passed_waiting_closeout",
        "closeout_blocked_count_out_of_range",
    }:
        category = "subject_closeout_blocked"
        severity = "warn"
        why = f"subject cannot close out yet: {status}"
    else:
        category = "subject_closeout_blocked"
        severity = "warn"
        why = f"subject closeout status is not recognized: {status or '-'}"
    evidence_summary = _subject_closeout_evidence(gate)
    action_code = str(gate.get("recommended_action") or "no_action")
    if str(gate.get("qbank_readiness") or "") == "qbank_ready" and status == "closeout_ready":
        # Keep closeout as the primary finding; qbank seed approval remains visible in the packet layer.
        action_code = "manager_formal_closeout"
    # Package 3: do NOT emit a `manager_formal_closeout` packet when
    # the latest authoritative verdict blocks closeout. Switch the
    # recommended_action to the appropriate repair / re-review path
    # so manager-actions / manager-panel print the blocker instead of
    # a contradictory closeout suggestion.
    packet_apply_allowed = True
    packet_action_code = action_code
    packet_suggested_brief = None
    if latest_blocks or (
        action_code == "manager_formal_closeout"
        and (latest_scope and latest_scope not in tasks.SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES)
    ):
        verdict_value = str(latest.get("verdict") or "")
        if verdict_value == "rejected":
            packet_action_code = "wait_for_worker_repair_and_re_review"
            packet_suggested_brief = (
                f"review_course 已 verdict=rejected（"
                f"scope={latest_scope or '-'}"
                f"{',' + ','.join(latest.get('required_fix') or []) if latest.get('required_fix') else ''}"
                f"），manager 不得仅凭 worker 自报修复而正式收口。"
                "先督促 worker 按 required_fix 返修并重新提交 review_course。"
            )
        elif verdict_value == "manager_action":
            packet_action_code = "resolve_manager_action_then_re_review"
            packet_suggested_brief = (
                f"review_course 已发出 manager_action，"
                f"manager 需先决定方向或范围，等 review_course 重新给出 verdict 后再推进。"
            )
        elif latest_scope and latest_scope != "full_subject":
            packet_action_code = "request_full_subject_review_recheck"
            if latest_scope == "qql_items":
                missing_layer_msg = "manifest"
            elif latest_scope.endswith("_only"):
                missing_layer_msg = latest_scope.replace(
                    "_only", ""
                ).upper() + " + 缺失层"
            else:
                missing_layer_msg = "缺失层（manifest）"
            packet_suggested_brief = (
                f"review_course 当前 verdict_scope={latest_scope} 不满足 full_subject 收口条件；"
                f"manager 不得仅凭 {latest_scope} PASS 升级为正式收口。"
                f"先让 review_course 对 {missing_layer_msg} 一起复核。"
            )
        else:
            packet_action_code = "reconcile_review_truth_with_latest_verdict"
            packet_suggested_brief = (
                "review verdict 与 closeout 路径存在矛盾，请先核对 latest_authoritative_verdict。"
            )
        packet_apply_allowed = False
    return {
        "category": category,
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": severity,
        "why": why,
        "evidence_summary": evidence_summary,
        "recommended_action": packet_action_code,
        "action_packet": _build_closeout_packet(
            task=task,
            gate=gate,
            evidence_summary=evidence_summary,
            why=why,
            action_code=packet_action_code,
            apply_allowed=packet_apply_allowed,
            suggested_brief_override=packet_suggested_brief,
        ),
    }


def _review_truth_lag_finding(task: dict) -> dict | None:
    if task.get("schema_version") != 2:
        return None
    if str(task.get("status") or "") != "submitted_for_review":
        return None
    if str(task.get("verdict") or "") != "pending":
        return None
    task_last = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    visible_verdict = _visible_review_pass_for_task(task, after=max(task_last - 1000, 0))
    if visible_verdict is None:
        return None
    tokens = _subject_match_tokens(task)
    manager_closeout = _manager_closeout_signal_for_subject(tokens, after=int(visible_verdict.get("created_at") or task_last))
    evidence_summary = (
        f"task_status={task.get('status') or '-'} verdict={task.get('verdict') or '-'} "
        f"visible_review_pass_log={visible_verdict.get('local_id') or '-'} "
        f"visible_review_pass_at={visible_verdict.get('created_at') or 0} "
        f"manager_closeout_log={manager_closeout.get('local_id') if manager_closeout else '-'} "
        f"manager_closeout_at={manager_closeout.get('created_at') if manager_closeout else 0}"
    )
    return {
        "category": "review_pass_log_but_task_pending",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "info",
        "live_blocker": False,
        "structured_truth_lag": True,
        "truth_source": "visible_review_pass",
        "why": (
            "review_course/manager surface shows a PASS/closeout for this review handoff, "
            "but the structured task still says submitted_for_review with verdict=pending"
        ),
        "evidence_summary": evidence_summary,
        "recommended_action": "reconcile_task_review_truth_from_visible_verdict",
        "action_packet": _subject_action_packet(
            action_code="safe_task_review_approve",
            gate={
                "subject_id": task["id"],
                "subject_name": str(task.get("title") or ""),
                "review_status": str(task.get("status") or ""),
                "closeout_status": str(task.get("closeout_status") or ""),
            },
            evidence_summary=(
                f"local_id={visible_verdict.get('local_id') or '-'} "
                f"task_id={task['id']} "
                f"reviewer={task.get('reviewer') or '-'} "
                f"reason=review_pass_log_truth_lag"
            ),
            reason="review PASS visible in logs but task truth not yet reconciled",
        ),
    }


def _worker_transition_suggestion_finding(task: dict) -> dict | None:
    """Detect worker log signals that don't match structured task state."""
    if task.get("schema_version") != 2:
        return None
    status = str(task.get("status") or "")
    assignee = str(task.get("assignee") or "")
    if assignee not in ("worker_course", "worker_builder", "worker_qbank"):
        return None

    title = str(task.get("title") or "")
    task_id = task["id"]
    tokens = _subject_match_tokens(task)

    # Check worker logs for completion signals when task is still in_progress
    if status == "in_progress":
        for row in local_facts.list_logs(assignee, limit=30):
            if str(row.get("type") or "") != "say":
                continue
            content = str(row.get("content") or "")
            lowered = content.lower()
            has_completion_signal = (
                "task_completed" in lowered
                or "已完成并交付" in content
                or "完成并交付" in content
                or "完工交付" in content
                or "完工报告" in content
                or "已交付" in content
            )
            if has_completion_signal:
                if _text_matches_task_scope(content, tokens) or title.lower() in lowered:
                    return {
                        "category": "worker_completed_missing_review_transition",
                        "task_id": task_id,
                        "stage": str(task.get("stage") or ""),
                        "status": status,
                        "severity": "info",
                        "live_blocker": False,
                        "why": (
                            f"{assignee} log shows task_completed/完工 but task is still in_progress; "
                            f"suggest submit-review + assign-reviewer transition"
                        ),
                        "evidence_summary": (
                            f"log_id={row.get('local_id') or '-'} "
                            f"task_id={task_id} "
                            f"assignee={assignee} "
                            f"signal=task_completed"
                        ),
                        "recommended_action": "submit-review + assign-reviewer transition",
                        "action_packet": {
                            "action_code": "suggest_submit_review",
                            "apply_allowed": False,
                            "assignee": assignee,
                            "task_stage": str(task.get("stage") or ""),
                            "reason": "worker completion signal detected without structured submit",
                            "subject_id": task_id,
                            "subject_name": title,
                            "evidence_summary": f"log_id={row.get('local_id') or '-'} task_id={task_id}",
                            "suggested_brief": f"请 {assignee} 执行 submit-review 将 {title} 提交给 review_course。",
                            "execution_plan": {
                                "plan_type": "manager_action_dry_run",
                                "dry_run": True,
                                "action_code": "suggest_submit_review",
                                "assignee": assignee,
                                "task_stage": str(task.get("stage") or ""),
                                "subject_id": task_id,
                                "subject_name": title,
                                "preconditions": ["worker confirms completion", "reviewer assigned"],
                                "proposed_command": f"eduflow task submit-review {task_id} --actor {assignee}",
                                "proposed_brief": f"请 {assignee} 提交 {title} 给 review_course 复核。",
                                "execution_policy": "dry_run_only/requires_manager_confirmation/no_auto_dispatch",
                            },
                        },
                    }

    # Check worker logs for started/accepted signals when task is still assigned
    if status == "assigned":
        for row in local_facts.list_logs(assignee, limit=30):
            if str(row.get("type") or "") != "say":
                continue
            content = str(row.get("content") or "")
            lowered = content.lower()
            has_acceptance_signal = (
                "已接单" in content
                or "已接管" in content
                or "开始处理" in content
                or "已开始处理" in content
                or "started" in lowered
                or "accepted" in lowered
            )
            negative_start_signal = any(marker in content for marker in ("准备开始", "待开始", "无法开始", "不能开始"))
            if has_acceptance_signal and not negative_start_signal:
                if _text_matches_task_scope(content, tokens) or title.lower() in lowered:
                    return {
                        "category": "worker_accepted_missing_transition",
                        "task_id": task_id,
                        "stage": str(task.get("stage") or ""),
                        "status": status,
                        "severity": "info",
                        "live_blocker": False,
                        "why": (
                            f"{assignee} log shows started/accepted signal but task is still assigned; "
                            f"suggest transition to in_progress"
                        ),
                        "evidence_summary": (
                            f"log_id={row.get('local_id') or '-'} "
                            f"task_id={task_id} "
                            f"assignee={assignee} "
                            f"signal=accepted"
                        ),
                        "recommended_action": "transition to in_progress",
                        "action_packet": {
                            "action_code": "suggest_in_progress_transition",
                            "apply_allowed": False,
                            "assignee": assignee,
                            "task_stage": str(task.get("stage") or ""),
                            "reason": "worker acceptance signal detected without structured transition",
                            "subject_id": task_id,
                            "subject_name": title,
                            "evidence_summary": f"log_id={row.get('local_id') or '-'} task_id={task_id}",
                            "suggested_brief": f"请 {assignee} 将 {title} 状态推进到 in_progress。",
                            "execution_plan": {
                                "plan_type": "manager_action_dry_run",
                                "dry_run": True,
                                "action_code": "suggest_in_progress_transition",
                                "assignee": assignee,
                                "task_stage": str(task.get("stage") or ""),
                                "subject_id": task_id,
                                "subject_name": title,
                                "preconditions": ["worker confirms acceptance"],
                                "proposed_command": f"eduflow task flow-transition {task_id} --to in_progress --actor worker",
                                "proposed_brief": f"请 {assignee} 推进 {title} 到 in_progress。",
                                "execution_policy": "dry_run_only/requires_manager_confirmation/no_auto_dispatch",
                            },
                        },
                    }
    return None


def _workflow_mount_finding(task: dict) -> dict | None:
    if task.get("schema_version") != 2:
        return None
    if str(task.get("workflow_id") or "").strip():
        return None
    text = f"{task.get('title') or ''} {task.get('description') or ''}"
    if (
        tasks.IGCSE_SUBJECT_LAUNCH_WORKFLOW_ID not in text
        and not tasks.is_igcse_course_task(
            title=str(task.get("title") or ""),
            stage=str(task.get("stage") or ""),
        )
    ):
        return None
    return {
        "category": "workflow_mentioned_but_not_mounted",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": "task text or IGCSE course scope indicates igcse-subject-launch, but workflow_id is empty",
        "evidence_summary": (
            f"title={str(task.get('title') or '')[:120]} "
            f"description={str(task.get('description') or '')[:160]} "
            f"workflow_id={task.get('workflow_id') or '-'}"
        ),
        "recommended_action": "mount_igcse_subject_launch_workflow",
    }


def _submitted_without_reviewer_finding(task: dict) -> dict | None:
    if task.get("schema_version") != 2:
        return None
    if str(task.get("status") or "") != "submitted_for_review":
        return None
    if str(task.get("reviewer") or "").strip():
        return None
    return {
        "category": "submitted_for_review_without_reviewer",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": "task is awaiting review but reviewer is empty, so review-queue filtering cannot route it",
        "evidence_summary": (
            f"workflow_id={task.get('workflow_id') or '-'} "
            f"default_reviewer={tasks.default_reviewer_for_workflow(str(task.get('workflow_id') or '')) or '-'} "
            f"reviewer={task.get('reviewer') or '-'}"
        ),
        "recommended_action": "assign_default_reviewer_before_review",
    }


# ── Package 3: review truth conflict detection ─────────────────────
# Surface situations where group / oral / older PASS / worker self-repair
# claims conflict with the latest structured review verdict. These
# findings feed the manager-actions / manager-panel closeout gate so
# that "正式收口" / "PASS closeout" / "items_layer OK" lines are NOT
# emitted when the latest authoritative verdict disagrees.
#
# === Package 3 finding family: complementary, not redundant ===
#
# On a "manager 口头 closeout + latest verdict FAIL" scenario, two
# findings may fire on the SAME task_id with distinct roles:
#
#   _visible_closeout_contradicts_latest_verdict_finding
#       category: review_truth_conflict
#       subtype:  visible_closeout_contradicts_latest_fail
#       role:     ALERT — "chat contradicts structured truth"
#       severity: error, live_blocker=True
#       carries:  NO action_packet
#       appears:  manager-panel "Anomalies (non-actionable)" section,
#                 supervisor alerts
#
#   _manager_closeout_action_finding
#       category: manager_closeout_but_task_pending
#       subtype:  blocked_by_latest_verdict
#       role:     ACTION — "what to do next"
#       carries:  action_packet with wait_for_* / re-review action_code,
#                 apply_allowed=False
#       appears:  manager-actions output list, manager-panel
#                 "Next Executable Actions" section
#
# The alert explains WHY the gate blocks; the action explains WHAT
# the manager should do. Both are needed: dropping either leaves
# the operator with a contradiction (chat says PASS, panel says
# nothing) or with a missing path forward (alert without an action).
#
# Verifies this in test_store_tasks_authority:
#   test_visible_closeout_conflict_and_manager_closeout_action_are_complementary


def _latest_verdict_finding(task: dict) -> dict | None:
    """Surface a finding whenever the latest authoritative verdict on a
    flow task blocks subject closeout. This is the hard gate that the
    manager panel / manager-actions surface must read.
    """
    if task.get("schema_version") != 2:
        return None
    if tasks.canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return None
    latest = task.get("latest_authoritative_verdict") or {}
    if not latest:
        # No authoritative verdict yet — only block when task has
        # reached delivered status without ever being reviewed (legacy).
        if (
            str(task.get("status") or "") == "delivered"
            and str(task.get("verdict") or "") == "approved"
        ):
            # No latest record but static verdict = approved → warn so
            # operator can backfill a verdict_target if missing.
            target = str(task.get("verdict_target") or "").strip()
            if not target:
                return {
                    "category": "review_truth_conflict",
                    "subtype": "missing_verdict_target_on_approved_task",
                    "task_id": task["id"],
                    "stage": str(task.get("stage") or ""),
                    "status": str(task.get("status") or ""),
                    "severity": "warn",
                    "live_blocker": True,
                    "why": (
                        "task is delivered with verdict=approved but has no "
                        "verdict_target / latest_authoritative_verdict; closeout "
                        "must not advance until reviewer re-declares scope."
                    ),
                    "evidence_summary": (
                        f"verdict=approved status=delivered "
                        f"verdict_target=- "
                        f"verdict_scope=-"
                    ),
                    "recommended_action": "request_verdict_target_for_existing_pass",
                }
        return None
    blocks, reasons = tasks.latest_verdict_blocks_closeout(task)
    if not blocks:
        return None
    verdict_value = str(latest.get("verdict") or "")
    scope = str(latest.get("verdict_scope") or "")
    reviewer = str(latest.get("reviewer") or "-")
    at_ms = int(latest.get("at_ms") or 0)
    target = str(latest.get("verdict_target") or "-")
    # Distinguish between "latest verdict is bad" vs "latest verdict is
    # too narrow for closeout target" — different operator language.
    if verdict_value == "rejected":
        subtype = "latest_verdict_rejected_blocks_closeout"
        severity = "error"
    elif verdict_value == "manager_action":
        subtype = "latest_verdict_manager_action_blocks_closeout"
        severity = "error"
    elif scope and scope not in tasks.SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES:
        subtype = f"verdict_scope_{scope}_insufficient_for_subject_closeout"
        severity = "warn"
    else:
        subtype = "latest_verdict_blocks_closeout"
        severity = "warn"
    return {
        "category": "review_truth_conflict",
        "subtype": subtype,
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": severity,
        "live_blocker": True,
        "why": (
            f"latest authoritative review verdict (reviewer={reviewer}, "
            f"at_ms={at_ms}) verdict={verdict_value or '-'} scope={scope or '-'} "
            f"target={target} blocks subject closeout: {'; '.join(reasons)}"
        ),
        "evidence_summary": (
            f"latest_verdict={verdict_value or '-'} "
            f"latest_scope={scope or '-'} "
            f"latest_target={target} "
            f"blocking_reasons={','.join(reasons)}"
        ),
        "recommended_action": (
            "wait_for_worker_repair_and_re_review"
            if verdict_value == "rejected"
            else "request_full_subject_review_recheck"
            if scope and scope not in tasks.SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES
            else "resolve_manager_action_then_re_review"
            if verdict_value == "manager_action"
            else "reconcile_review_truth_with_latest_verdict"
        ),
    }


def _evidence_account_finding(task: dict) -> dict | None:
    if task.get("schema_version") != 2:
        return None
    if tasks.canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return None
    if _has_newer_active_task_for_same_lane(task):
        return None
    if not task_evidence_account.requires_strict_account(task):
        return None
    gate = tasks.subject_closeout_status(task)
    account = gate.get("evidence_account") or task_evidence_account.build_evidence_account(
        task,
        closeout_status=gate,
    )
    status = str(gate.get("closeout_status") or "")
    missing = list(account.get("missing_evidence") or [])
    conflicts = list(account.get("conflicting_evidence") or [])
    if status in {"not_subject", "closeout_completed"}:
        return None
    if not missing and not conflicts:
        return None
    if conflicts:
        category = "evidence_account_conflict"
        severity = "error"
        recommended = "resolve_evidence_account_conflict"
        why = (
            "closeout evidence account has conflicting machine-traceable facts; "
            "manager/auto_ops must not mark the task closeout-ready."
        )
    else:
        category = "evidence_account_incomplete"
        severity = "error"
        recommended = "block_closeout_until_evidence_packet_complete"
        why = (
            "closeout evidence account is missing required machine-traceable facts; "
            "worker self-report or chat PASS is not enough for closeout-ready."
        )
    return {
        "category": category,
        "task_id": str(task.get("id") or ""),
        "workflow_id": account.get("workflow_id") or "",
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": severity,
        "live_blocker": True,
        "missing_evidence": missing,
        "conflicting_evidence": conflicts,
        "closeout_ready": False,
        "why": why,
        "evidence_summary": (
            f"workflow_id={account.get('workflow_id') or '-'} "
            f"task_id={account.get('task_id') or '-'} "
            f"scope={account.get('scope') or '-'} "
            f"items_count={account.get('items_count')} "
            f"qql_count={account.get('qql_count')} "
            f"manifest_rows={account.get('manifest_rows')} "
            f"latest_verdict_source={account.get('latest_authoritative_review_verdict_source') or '-'} "
            f"subject_verifier_status={account.get('subject_verifier_status') or '-'} "
            f"missing={','.join(missing) or '-'} "
            f"conflicts={','.join(conflicts) or '-'}"
        ),
        "recommended_action": recommended,
        "evidence_account": account,
    }


def _visible_closeout_contradicts_latest_verdict_finding(
    task: dict, *, now: int
) -> dict | None:
    """Detect a visible PASS / closeout signal in chat / logs that
    contradicts the latest authoritative review verdict.

    Example: manager says "T-26 正式闭环" while review_course inbox /
    task state says items-layer FAIL.
    """
    if task.get("schema_version") != 2:
        return None
    if tasks.canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return None
    latest = task.get("latest_authoritative_verdict") or {}
    if not latest:
        return None
    verdict_value = str(latest.get("verdict") or "")
    if verdict_value not in {"rejected", "manager_action"}:
        return None
    tokens = _subject_match_tokens(task)
    if not tokens:
        return None
    # Look for PASS / closeout claims AFTER the latest authoritative verdict.
    after = int(latest.get("at_ms") or 0)
    visible_closeout = _manager_closeout_signal_for_subject(tokens, after=after)
    visible_pass = _visible_review_pass_for_task(task, after=after)
    visible_items_pass = False
    for row in local_facts.list_logs("review_course", limit=50):
        created_at = int(row.get("created_at") or 0)
        if created_at < after:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        if not _text_mentions_any_subject_token(content, tokens):
            continue
        lowered = content.lower()
        if (
            "items" in lowered
            and ("pass" in lowered or "可发布" in content or "verdict" in lowered)
        ):
            visible_items_pass = True
            break
    if not (visible_closeout or visible_pass):
        return None
    # Conflict — surface as a hard warn.
    parts: list[str] = []
    if visible_closeout:
        parts.append(
            f"manager_closeout_signal_visible log_id="
            f"{visible_closeout.get('local_id') or '-'}"
        )
    if visible_pass:
        parts.append(
            f"review_pass_visible log_id="
            f"{visible_pass.get('local_id') or '-'}"
        )
    if visible_items_pass:
        parts.append("items_pass_signal_visible")
    return {
        "category": "review_truth_conflict",
        "subtype": "visible_closeout_contradicts_latest_fail",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "error",
        "live_blocker": True,
        "why": (
            f"latest authoritative verdict={verdict_value} "
            f"(scope={latest.get('verdict_scope') or '-'}, "
            f"reviewer={latest.get('reviewer') or '-'}, "
            f"at_ms={latest.get('at_ms') or 0}), but later manager / "
            f"review_course / chat signals claim PASS / closeout: "
            f"{'; '.join(parts)}"
        ),
        "evidence_summary": " | ".join(parts) or "no_evidence",
        "recommended_action": (
            "acknowledge_latest_fail_and_block_closeout_until_re_review"
        ),
    }


def _worker_self_repair_supersedes_latest_verdict_finding(
    task: dict, *, now: int
) -> dict | None:
    """Detect worker self-repair signals that claim '已修好' / 'fixed' /
    '已修复' AFTER the latest authoritative review verdict was a FAIL.

    The repair claim cannot supersede the verdict — the next reviewer
    pass is the only thing that can clear the FAIL. Until then,
    closeout must remain blocked.
    """
    if task.get("schema_version") != 2:
        return None
    if tasks.canonical_stage(str(task.get("stage") or "")) != "curriculum":
        return None
    latest = task.get("latest_authoritative_verdict") or {}
    if not latest:
        return None
    verdict_value = str(latest.get("verdict") or "")
    if verdict_value != "rejected":
        return None
    after = int(latest.get("at_ms") or 0)
    tokens = _subject_match_tokens(task)
    if not tokens:
        return None
    for row in local_facts.list_logs(str(task.get("owner") or "worker_course"), limit=20):
        created_at = int(row.get("created_at") or 0)
        if created_at < after:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        if not _text_mentions_any_subject_token(content, tokens):
            continue
        lowered = content.lower()
        # Look for self-repair / "已修好" markers, NOT a fresh verdict.
        has_repair_claim = (
            "已修好" in content
            or "已修复" in content
            or "修复完成" in content
            or "重新提交" in content
            or "fixed" in lowered
            or "repaired" in lowered
            or "已按要求" in content
        )
        if not has_repair_claim:
            continue
        # Make sure it isn't itself a review verdict line.
        if "verdict" in lowered or "verdict:" in lowered or "复检" in content:
            continue
        return {
            "category": "review_truth_conflict",
            "subtype": "worker_self_repair_supersedes_latest_fail",
            "task_id": task["id"],
            "stage": str(task.get("stage") or ""),
            "status": str(task.get("status") or ""),
            "severity": "warn",
            "live_blocker": True,
            "why": (
                f"latest authoritative verdict=rejected (reviewer="
                f"{latest.get('reviewer') or '-'}, at_ms="
                f"{latest.get('at_ms') or 0}); worker self-repair signal "
                f"cannot supersede the verdict — closeout stays blocked "
                f"until review_course re-reviews"
            ),
            "evidence_summary": (
                f"latest_verdict=rejected "
                f"worker_repair_log={row.get('local_id') or '-'} "
                f"worker_repair_at={created_at}"
            ),
            "recommended_action": (
                "require_review_course_re_review_before_closeout"
            ),
        }
    return None


def _package_promoted_to_subject_closeout_finding(task: dict) -> dict | None:
    if task.get("schema_version") != 2:
        return None
    if not tasks.is_package_scope(task):
        return None
    tokens = _subject_match_tokens(task)
    manager_closeout = _manager_closeout_signal_for_subject(tokens, after=0)
    if manager_closeout is None:
        return None
    content = str(manager_closeout.get("content") or "")
    lowered = content.lower()
    if "batch closeout" in lowered or "package closeout" in lowered or "小包 closeout" in lowered:
        return None
    if not (
        "subject closeout" in lowered
        or "整科" in content
        or "全学科" in content
        or "正式完成" in content
        or "正式闭环" in content
    ):
        return None
    return {
        "category": "package_pass_promoted_to_subject_closeout",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": "manager closeout language appears to promote a package/batch PASS into subject closeout",
        "evidence_summary": (
            f"closeout_status={task.get('closeout_status') or '-'} "
            f"manager_log={manager_closeout.get('local_id') or '-'} "
            f"manager_content={content[:180]}"
        ),
        "recommended_action": "use_batch_closeout_not_subject_closeout",
    }


def _subject_qbank_readiness_finding(task: dict) -> dict | None:
    gate = tasks.subject_closeout_status(task)
    status = str(gate.get("closeout_status") or "")
    qbank_readiness = str(gate.get("qbank_readiness") or "")
    if status in {"not_subject", "closeout_completed"}:
        return None
    if qbank_readiness in {"", "qbank_ready"}:
        return None
    if qbank_readiness == "qbank_blocked_low_volume":
        return None
    evidence_summary = _subject_closeout_evidence(gate)
    action_code = str(
        gate.get("recommended_qbank_action")
        or "request_qbank_readiness_check"
    )
    return {
        "category": "subject_qbank_readiness_blocked",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": f"subject qbank readiness is not ready: {qbank_readiness}",
        "evidence_summary": evidence_summary,
        "recommended_action": action_code,
        "action_packet": _subject_action_packet(
            action_code=action_code,
            gate=gate,
            evidence_summary=evidence_summary,
            reason=f"subject qbank readiness is not ready: {qbank_readiness}",
        ),
    }


def _manager_closeout_action_finding(task: dict) -> dict | None:
    """Detect manager closeout signals for tasks that are still pending.

    This bypasses subject_closeout_status which returns 'not_subject'
    for tasks without verdict=approved.  We still generate a
    manager_formal_closeout action so the manager can reconcile.

    Package 3 (Codex review HIGH #1): when the latest authoritative
    verdict blocks closeout (rejected / manager_action / scope
    insufficient), we must NOT advertise a `manager_formal_closeout`
    packet — the manager-actions / manager-panel must not show
    contradictory closeout UI.  We downgrade the recommended_action
    and suggested_brief to a `wait_for_*` / re-review path so the
    operator sees the same blocker the structured task state carries.
    """
    if task.get("schema_version") != 2:
        return None
    status = str(task.get("status") or "")
    verdict = str(task.get("verdict") or "")
    # Only relevant for tasks that haven't been formally closed yet
    if verdict == "approved" or status == "delivered" or status == "cancelled":
        return None
    tokens = _subject_match_tokens(task)
    if not tokens:
        return None
    closeout_signal = _manager_closeout_signal_for_subject(tokens)
    if closeout_signal is None:
        return None
    # Package 3: suppress manager_formal_closeout when the latest
    # authoritative verdict blocks closeout. This is the same gate
    # `_subject_closeout_finding` uses, applied here so the
    # chat-signal-driven branch does not emit a contradictory
    # closeout action when the structured task truth says block.
    latest_blocks, latest_block_reasons = tasks.latest_verdict_blocks_closeout(task)
    latest = task.get("latest_authoritative_verdict") or {}
    latest_scope = str(latest.get("verdict_scope") or "")
    latest_verdict = str(latest.get("verdict") or "")
    if latest_blocks or (
        latest_scope
        and latest_scope not in tasks.SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES
    ):
        # Pick a coherent action_code / brief for the blocker.
        if latest_verdict == "rejected":
            action_code = "wait_for_worker_repair_and_re_review"
            suggested = (
                f"review_course 已 verdict=rejected（"
                f"scope={latest_scope or '-'}"
                f"{',' + ','.join(latest.get('required_fix') or []) if latest.get('required_fix') else ''}"
                f"），manager 不得仅凭口头 closeout 信号而正式收口。"
                "先督促 worker 按 required_fix 返修并重新提交 review_course。"
            )
        elif latest_verdict == "manager_action":
            action_code = "resolve_manager_action_then_re_review"
            suggested = (
                f"review_course 已发出 manager_action，"
                f"manager 需先决定方向或范围，等 review_course 重新给出 verdict 后再推进。"
            )
        elif latest_scope and latest_scope != "full_subject":
            action_code = "request_full_subject_review_recheck"
            if latest_scope == "qql_items":
                missing_layer_msg = "manifest"
            elif latest_scope.endswith("_only"):
                missing_layer_msg = latest_scope.replace(
                    "_only", ""
                ).upper() + " + 缺失层"
            else:
                missing_layer_msg = "缺失层（manifest）"
            suggested = (
                f"review_course 当前 verdict_scope={latest_scope} 不满足 full_subject 收口条件；"
                f"manager 不得仅凭口头 closeout 信号升级为正式收口。"
                f"先让 review_course 对 {missing_layer_msg} 一起复核。"
            )
        else:
            action_code = "reconcile_review_truth_with_latest_verdict"
            suggested = (
                "review verdict 与口头 closeout 信号矛盾，请先核对 latest_authoritative_verdict。"
            )
        return {
            "category": "manager_closeout_but_task_pending",
            "subtype": "blocked_by_latest_verdict",
            "task_id": task["id"],
            "stage": str(task.get("stage") or ""),
            "status": status,
            "severity": "warn",
            "live_blocker": True,
            "why": (
                f"manager signaled closeout (正式闭环) but latest_authoritative_verdict "
                f"blocks closeout (verdict={latest_verdict or '-'}, "
                f"scope={latest_scope or '-'}): {'; '.join(latest_block_reasons) or 'no_blocker'}"
            ),
            "evidence_summary": (
                f"manager_closeout_log={closeout_signal.get('local_id') or '-'} "
                f"manager_closeout_at={closeout_signal.get('created_at') or 0} "
                f"task_status={status} "
                f"latest_verdict={latest_verdict or '-'} "
                f"latest_scope={latest_scope or '-'}"
            ),
            "recommended_action": action_code,
            "action_packet": {
                "action_code": action_code,
                "apply_allowed": False,
                "assignee": "manager",
                "task_stage": "curriculum",
                "reason": "manager closeout signal found but latest verdict blocks; reconcile truth first",
                "subject_id": str(task.get("id") or ""),
                "subject_name": str(task.get("title") or ""),
                "evidence_summary": (
                    f"manager_closeout_log={closeout_signal.get('local_id') or '-'} "
                    f"latest_verdict={latest_verdict or '-'} "
                    f"latest_scope={latest_scope or '-'}"
                ),
                "suggested_brief": suggested,
                "closeout_gate": {
                    "review_approved": False,
                    "evidence_present": bool(task.get("evidence_packet")),
                    "qa_standard_met": False,
                    "qbank_ready": False,
                },
                "execution_plan": {
                    "plan_type": "manager_action_dry_run",
                    "dry_run": True,
                    "action_code": action_code,
                    "assignee": "manager",
                    "task_stage": "curriculum",
                    "subject_id": str(task.get("id") or ""),
                    "subject_name": str(task.get("title") or ""),
                    "preconditions": ["reconcile_latest_verdict_truth"],
                    "proposed_command": "no-op",
                    "proposed_brief": suggested,
                    "execution_policy": "dry_run_only/requires_manager_confirmation/no_auto_dispatch",
                },
            },
        }
    packet = _subject_action_packet(
        action_code="manager_formal_closeout",
        gate=_closeout_gate_for_task(task),
        evidence_summary=(
            f"log_id={closeout_signal.get('local_id') or '-'} "
            f"task_id={task['id']} "
            f"manager_closeout_signal=正式闭环 "
            f"task_status={status}"
        ),
        reason="manager closeout signal found but structured task not yet closed; reconcile now",
    )
    packet = _packet_with_apply_allowed(packet, apply_allowed=False)
    return {
        "category": "manager_closeout_but_task_pending",
        "task_id": task["id"],
        "stage": str(task.get("stage") or ""),
        "status": status,
        "severity": "info",
        "live_blocker": False,
        "why": (
            f"manager signaled closeout (正式闭环) but task status={status} "
            f"verdict={verdict}; generate manager_formal_closeout action to reconcile"
        ),
        "evidence_summary": (
            f"manager_closeout_log={closeout_signal.get('local_id') or '-'} "
            f"manager_closeout_at={closeout_signal.get('created_at') or 0} "
            f"task_status={status} verdict={verdict}"
        ),
        "recommended_action": "manager_formal_closeout",
        "action_packet": packet,
    }


def _closeout_gate_for_task(task: dict) -> dict:
    """Minimal closeout gate summary for a task that hasn't gone through formal review yet."""
    evidence = task.get("evidence_packet") or {}
    return {
        "subject_id": str(task.get("id") or ""),
        "subject_name": str(task.get("title") or ""),
        "qa_count": int(evidence.get("qa_count") or 0),
        "item_count": int(evidence.get("item_count") or 0),
        "qa_min": 0,
        "qa_max": 0,
        "qbank_readiness": "qbank_review_needed",
        "review_status": str(task.get("verdict") or "pending"),
        "closeout_status": str(task.get("closeout_status") or ""),
        "recommended_action": "manager_formal_closeout",
    }


_MANAGER_DIRECT_CONTENT_MARKERS = (
    "我直接修",
    "我已修复",
    "我修复了",
    "我直接改",
    "我已改",
    "直接修复",
    "直接修改",
)
_MANAGER_DIRECT_VERIFICATION_MARKERS = (
    "我跑了 python",
    "我跑 python",
    "跑了 python 验证",
    "跑 python 验证",
    "我直接验证",
    "我已验证",
    "我执行了验证",
)
_MANAGER_DISPATCH_CLAIM_MARKERS = (
    "已派",
    "已派工",
    "已经派",
    "已分派",
    "dispatch",
)
_MANAGER_NEXT_SUBJECT_MARKERS = (
    "启动下一学科",
    "下一学科",
    "next subject",
)
_PRODUCTION_ROLES = ("worker_course", "worker_builder", "review_course", "worker_qbank")


def _recent_manager_action_logs(*, now: int) -> list[dict]:
    rows: list[dict] = []
    for row in local_facts.list_logs("manager", limit=50):
        if str(row.get("type") or "") not in {"say", "task", "task_completed"}:
            continue
        created_at = int(row.get("created_at") or 0)
        if now - created_at > 60 * 60 * 1000:
            continue
        content = str(row.get("content") or "")
        if content.strip():
            rows.append(row)
    return rows


def _manager_log_subject_name(content: str) -> str:
    match = re.search(r"(?:IGCSE\s+)?[A-Za-z][A-Za-z ]+\s+\d{4}", str(content or ""))
    return match.group(0).strip() if match else ""


def _manager_claimed_role(content: str) -> str:
    text = str(content or "")
    lowered = text.lower()
    for role in _PRODUCTION_ROLES:
        if role in text:
            return role
    if "qbank" in lowered or "题库" in text:
        return "worker_qbank"
    if "review" in lowered or "verdict" in lowered or "复核" in text:
        return "review_course"
    if any(marker in lowered for marker in ("path", "runtime", "tool", "python", "script")) or any(
        marker in text for marker in ("路径", "工具", "执行")
    ):
        return "worker_builder"
    return "worker_course"


def _text_has_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = str(text or "").lower()
    return any(marker.lower() in lowered for marker in markers)


def _has_task_truth_for_manager_claim(role: str, content: str, created_at: int) -> bool:
    subject = _manager_log_subject_name(content)
    subject_tokens = _subject_match_tokens(subject or content)
    since = max(created_at - 1000, 0)
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        if str(task.get("assignee") or "") != role and str(task.get("owner") or "") != role:
            continue
        if int(task.get("created_at") or 0) < since and int(task.get("updated_at") or 0) < since:
            continue
        task_text = " ".join(
            str(task.get(key) or "")
            for key in ("id", "title", "description", "latest_turn_summary")
        )
        if subject_tokens and _text_mentions_any_subject_token(task_text, subject_tokens):
            return True
        if subject and subject.lower() in task_text.lower():
            return True
    for msg in local_facts.list_messages(role):
        if int(msg.get("created_at") or 0) < since:
            continue
        msg_content = str(msg.get("content") or "")
        if subject_tokens and _text_mentions_any_subject_token(msg_content, subject_tokens):
            return True
        if subject and subject.lower() in msg_content.lower():
            return True
    return False


def _active_subject_gate_blockers() -> list[dict]:
    blockers: list[dict] = []
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        if tasks.canonical_stage(str(task.get("stage") or "")) != "curriculum":
            continue
        if not tasks.is_igcse_course_task(
            title=str(task.get("title") or ""),
            stage=str(task.get("stage") or ""),
        ):
            continue
        status = str(task.get("status") or "")
        if status == "cancelled":
            continue
        gate = tasks.subject_closeout_status(task)
        if str(gate.get("closeout_status") or "") == "closeout_completed":
            continue
        blockers.append({
            "task": task,
            "gate": gate,
            "subject_code": tasks.extract_subject_code(str(task.get("title") or "")),
        })
    return blockers


def _manager_boundary_findings(*, now: int) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    active_blockers = _active_subject_gate_blockers()
    for row in _recent_manager_action_logs(now=now):
        content = str(row.get("content") or "")
        lowered = content.lower()
        log_id = str(row.get("local_id") or "")
        subject_name = _manager_log_subject_name(content) or "manager boundary event"
        subject_code = tasks.extract_subject_code(subject_name)
        created_at = int(row.get("created_at") or 0)
        evidence = (
            f"manager_log={log_id or '-'} manager_log_at={created_at} "
            f"content={content[:180]}"
        )

        if _text_has_any(content, _MANAGER_DIRECT_CONTENT_MARKERS) and any(
            marker in lowered or marker in content
            for marker in ("content", "文件", "课程", "qa", "item", "qql", "topic")
        ):
            key = ("manager_direct_content_execution", log_id)
            if key not in seen:
                seen.add(key)
                action_code = "dispatch_worker_course_for_content_repair"
                suggested = (
                    f"manager 不能直接修内容。请派 worker_course 接手 {subject_name} 内容返修，"
                    "返修后必须提交 review_course verdict。"
                )
                findings.append({
                    "category": "manager_direct_content_execution",
                    "task_id": f"manager-boundary:{log_id or 'content'}",
                    "stage": "manager_boundary",
                    "status": "manager_direct_execution_claim",
                    "severity": "error",
                    "live_blocker": True,
                    "why": "manager 明确声称自己直接修内容/课程文件；内容生产和返修必须归 worker_course。",
                    "evidence_summary": evidence,
                    "recommended_action": action_code,
                    "owner": "worker_course",
                    "next_action": action_code,
                    "action_packet": _manager_boundary_packet(
                        action_code=action_code,
                        assignee="worker_course",
                        task_stage="curriculum",
                        subject_id=f"manager-boundary:{log_id or 'content'}",
                        subject_name=subject_name,
                        evidence_summary=evidence,
                        suggested_brief=suggested,
                        reason="manager direct content execution claim",
                    ),
                })

        if _text_has_any(content, _MANAGER_DIRECT_VERIFICATION_MARKERS):
            key = ("manager_direct_verification_execution", log_id)
            if key not in seen:
                seen.add(key)
                action_code = "dispatch_review_course_for_verdict_or_worker_builder_for_tool_verification"
                suggested = (
                    f"manager 不能把自己跑验证当 verdict。若是内容 verdict，派 review_course；"
                    f"若是路径/工具执行验证，派 worker_builder。范围：{subject_name}。"
                )
                findings.append({
                    "category": "manager_direct_verification_execution",
                    "task_id": f"manager-boundary:{log_id or 'verification'}",
                    "stage": "manager_boundary",
                    "status": "manager_direct_verification_claim",
                    "severity": "error",
                    "live_blocker": True,
                    "why": "manager 明确声称自己执行 Python/验证；verdict 归 review_course，工具/路径验证归 worker_builder。",
                    "evidence_summary": evidence,
                    "recommended_action": action_code,
                    "owner": "review_course|worker_builder",
                    "next_action": action_code,
                    "action_packet": _manager_boundary_packet(
                        action_code=action_code,
                        assignee="review_course",
                        task_stage="review",
                        subject_id=f"manager-boundary:{log_id or 'verification'}",
                        subject_name=subject_name,
                        evidence_summary=evidence,
                        suggested_brief=suggested,
                        reason="manager direct verification execution claim",
                    ),
                })

        if _text_has_any(content, _MANAGER_DISPATCH_CLAIM_MARKERS):
            role = _manager_claimed_role(content)
            if not _has_task_truth_for_manager_claim(role, content, created_at):
                key = ("manager_claim_without_task_truth", log_id)
                if key not in seen:
                    seen.add(key)
                    action_code = f"create_task_backed_dispatch_to_{role}"
                    suggested = (
                        f"manager 口头声称已派 {role}，但 task/inbox 没有同范围证据。"
                        "先补 task-backed dispatch，再让 worker ACK。"
                    )
                    findings.append({
                        "category": "manager_claim_without_task_truth",
                        "task_id": f"manager-boundary:{log_id or 'truth'}",
                        "stage": "manager_boundary",
                        "status": "dispatch_claim_without_task_or_inbox",
                        "severity": "error",
                        "live_blocker": True,
                        "why": "manager 群消息声称已派工，但 task/inbox/workflow 没有真实落地证据。",
                        "evidence_summary": (
                            f"{evidence} claimed_role={role} task_truth=false inbox_truth=false"
                        ),
                        "recommended_action": action_code,
                        "owner": role,
                        "next_action": action_code,
                        "action_packet": _manager_boundary_packet(
                            action_code=action_code,
                            assignee=role,
                            task_stage="curriculum" if role == "worker_course" else "builder",
                            subject_id=f"manager-boundary:{log_id or 'truth'}",
                            subject_name=subject_name,
                            evidence_summary=evidence,
                            suggested_brief=suggested,
                            reason="manager dispatch claim lacks task/inbox truth",
                        ),
                    })

        if _text_has_any(content, _MANAGER_NEXT_SUBJECT_MARKERS) and active_blockers:
            for blocker in active_blockers:
                task = blocker["task"]
                current_code = str(blocker.get("subject_code") or "")
                if subject_code and current_code and subject_code == current_code:
                    continue
                key = ("premature_next_subject", log_id)
                if key in seen:
                    break
                seen.add(key)
                gate = blocker["gate"]
                action_code = "finish_current_subject_closeout_gate_first"
                suggested = (
                    f"先处理当前学科 {task.get('title') or task.get('id')} 的 closeout gate："
                    f"{gate.get('closeout_status') or '-'} / {gate.get('recommended_action') or '-'}。"
                    "通过前不得启动下一学科 production/review/closeout。"
                )
                findings.append({
                    "category": "premature_next_subject",
                    "task_id": str(task.get("id") or f"manager-boundary:{log_id or 'next'}"),
                    "stage": "manager_boundary",
                    "status": "next_subject_claim_before_current_closeout",
                    "severity": "error",
                    "live_blocker": True,
                    "why": "当前学科 closeout gate 未满足，manager 已启动/声称启动下一学科。",
                    "evidence_summary": (
                        f"current_subject_id={task.get('id') or '-'} "
                        f"current_closeout_status={gate.get('closeout_status') or '-'} "
                        f"current_recommended_action={gate.get('recommended_action') or '-'} "
                        f"claimed_next_subject={subject_name or '-'} {evidence}"
                    ),
                    "recommended_action": action_code,
                    "owner": "manager",
                    "next_action": action_code,
                    "action_packet": _manager_boundary_packet(
                        action_code=action_code,
                        assignee="manager",
                        task_stage="curriculum",
                        subject_id=str(task.get("id") or f"manager-boundary:{log_id or 'next'}"),
                        subject_name=str(task.get("title") or subject_name),
                        evidence_summary=evidence,
                        suggested_brief=suggested,
                        reason="next subject claim before current subject closeout gate",
                    ),
                })
                break
    return findings


def _next_subject_rollover_finding() -> dict | None:
    inventory = tasks.subject_inventory()
    completed = [row for row in inventory if row.get("closeout_status") == "closeout_completed"]
    if not completed:
        return None
    completed.sort(key=lambda row: int(row.get("closeout_completed_at") or 0), reverse=True)
    source = completed[0]
    candidates = [
        row for row in inventory
        if int(row.get("next_candidate_rank") or 0) == 1
    ]
    if candidates:
        candidate = candidates[0]
        recommended_action = "dispatch_next_subject_worker_course"
        evidence = (
            f"completed_subject={source.get('subject_name') or '-'} "
            f"next_subject={candidate.get('subject_name') or '-'} "
            f"next_subject_id={candidate.get('subject_id') or '-'} "
            f"next_candidate_rank={candidate.get('next_candidate_rank') or 0}"
        )
        why = "manager closeout completed; next subject candidate is ready for worker_course dispatch"
        packet = {
            "action_code": recommended_action,
            "apply_allowed": _apply_allowed(recommended_action),
            "assignee": "worker_course",
            "task_stage": "curriculum",
            "reason": why,
            "subject_id": str(candidate.get("subject_id") or ""),
            "subject_name": str(candidate.get("subject_name") or ""),
            "evidence_summary": evidence,
            "suggested_brief": (
                f"请 worker_course 启动下一学科 {candidate.get('subject_name') or '-'}："
                "先做学科计划、topic 对齐和 300-500 QA 产出路径，再提交 review_course。"
            ),
            "closeout_gate": {},
        }
        packet["execution_plan"] = _execution_plan_for_packet(packet)
    else:
        recommended_action = "no_next_subject_candidate"
        evidence = (
            f"completed_subject={source.get('subject_name') or '-'} "
            "next_subject=- next_subject_id=- next_candidate_rank=0"
        )
        why = "manager closeout completed but no next subject candidate is available"
        packet = {
            "action_code": recommended_action,
            "apply_allowed": _apply_allowed(recommended_action),
            "assignee": "manager",
            "task_stage": "curriculum",
            "reason": why,
            "subject_id": str(source.get("subject_id") or ""),
            "subject_name": str(source.get("subject_name") or ""),
            "evidence_summary": evidence,
            "suggested_brief": "当前没有下一学科候选，请 manager 先补 subject inventory 或明确下一学科。",
            "closeout_gate": {},
        }
        packet["execution_plan"] = _execution_plan_for_packet(packet)
    return {
        "category": "next_subject_rollover_ready",
        "task_id": str(source.get("subject_id") or "subject_inventory"),
        "stage": "curriculum",
        "status": "closeout_completed",
        "severity": "info",
        "why": why,
        "evidence_summary": evidence,
        "recommended_action": recommended_action,
        "action_packet": packet,
    }


def scan_manager_anomalies(*, now: int | None = None) -> list[dict]:
    current_now = int(now if now is not None else now_ms())
    events_by_id = _task_events_by_id()
    findings: list[dict] = []
    findings.extend(_runtime_visibility_findings(now=current_now))
    findings.extend(_high_priority_inbox_blocking_findings(now=current_now))
    findings.extend(_conflicting_task_brief_findings(now=current_now))
    findings.extend(_secondhand_visibility_findings(now=current_now))
    findings.extend(_secondhand_acceptance_conflict_findings(now=current_now))
    findings.extend(_facts_process_visibility_stale_findings(now=current_now))
    findings.extend(_facts_accepted_without_started_findings(now=current_now))
    findings.extend(_worker_context_guard_findings(now=current_now))
    findings.extend(_stale_execution_context_finding())
    findings.extend(_evidence_packet_incomplete_finding())
    findings.extend(_manager_boundary_findings(now=current_now))
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2 or task.get("status") == "cancelled":
            continue
        workflow_mount = _workflow_mount_finding(task)
        if workflow_mount is not None:
            findings.append(workflow_mount)
        missing_reviewer = _submitted_without_reviewer_finding(task)
        if missing_reviewer is not None:
            findings.append(missing_reviewer)
        surface_truth = _surface_truth_finding(task, now=current_now)
        if surface_truth is not None:
            findings.append(surface_truth)
        scope_mismatch = _review_scope_mismatch_finding(task)
        if scope_mismatch is not None:
            findings.append(scope_mismatch)
    for task in _active_flow_tasks():
        events = events_by_id.get(task["id"], [])
        stale = _stale_finding(task, now=current_now)
        if stale is not None:
            findings.append(stale)
        process_visibility = _process_visibility_stale_finding(task, now=current_now)
        if process_visibility is not None:
            findings.append(process_visibility)
        manager_action = _manager_action_finding(task, now=current_now)
        if manager_action is not None:
            findings.append(manager_action)
        revision_ack = _revision_ack_missing_finding(task)
        if revision_ack is not None:
            findings.append(revision_ack)
        loop = _reject_resubmit_finding(task, events)
        if loop is not None:
            findings.append(loop)
        # NEW: worker transition suggestions
        worker_transition = _worker_transition_suggestion_finding(task)
        if worker_transition is not None:
            findings.append(worker_transition)
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        account_finding = _evidence_account_finding(task)
        if account_finding is not None:
            findings.append(account_finding)
        review_truth_lag = _review_truth_lag_finding(task)
        if review_truth_lag is not None:
            findings.append(review_truth_lag)
        subject_closeout = _subject_closeout_finding(task)
        if (
            subject_closeout is not None
            and not (
                review_truth_lag is not None
                and (review_truth_lag.get("action_packet") or {}).get("action_code") == "safe_task_review_approve"
                and (subject_closeout.get("action_packet") or {}).get("action_code") == "safe_task_review_approve"
            )
        ):
            findings.append(subject_closeout)
        package_promoted = _package_promoted_to_subject_closeout_finding(task)
        if package_promoted is not None:
            findings.append(package_promoted)
        qbank_readiness = _subject_qbank_readiness_finding(task)
        if qbank_readiness is not None:
            findings.append(qbank_readiness)
        manager_closeout_action = _manager_closeout_action_finding(task)
        if manager_closeout_action is not None:
            findings.append(manager_closeout_action)
        # Package 3: surface the latest authoritative verdict's block
        # status so manager-actions / manager-panel can suppress the
        # "正式收口" line. This finding is hard (live_blocker=True) when
        # the latest verdict is rejected / manager_action / scope too
        # narrow for subject closeout.
        latest_verdict_block = _latest_verdict_finding(task)
        if latest_verdict_block is not None:
            findings.append(latest_verdict_block)
        # Package 3: detect a visible chat / log PASS / closeout that
        # contradicts the latest authoritative FAIL. This is the
        # "Biology 0606 false closeout" anomaly.
        visible_contradict = _visible_closeout_contradicts_latest_verdict_finding(
            task, now=current_now
        )
        if visible_contradict is not None:
            findings.append(visible_contradict)
        # Package 3: worker self-repair cannot clear a reviewer FAIL.
        # Surface the contradiction so the manager does not believe
        # "worker 已修好 → can closeout".
        self_repair = _worker_self_repair_supersedes_latest_verdict_finding(
            task, now=current_now
        )
        if self_repair is not None:
            findings.append(self_repair)
    rollover = _next_subject_rollover_finding()
    if rollover is not None:
        findings.append(rollover)
    findings.sort(key=lambda row: (row["task_id"], row["category"]))
    return findings


def _contains_9_item_standard(text: str) -> bool:
    normalized = str(text or "").lower()
    return any(marker in normalized for marker in ("9-item", "9 items", "9 qa", "9-item standard"))


def _contains_12_item_standard(text: str) -> bool:
    normalized = str(text or "").lower()
    return any(marker in normalized for marker in ("12-item", "12 items", "12 qa", "12-item standard"))


def _subject_match_tokens(task_or_text: dict | str) -> tuple[str, ...]:
    if isinstance(task_or_text, dict):
        parts = [
            str(task_or_text.get("id") or ""),
            str(task_or_text.get("title") or ""),
            str(task_or_text.get("description") or ""),
            str(task_or_text.get("scope_topic") or ""),
            str(task_or_text.get("verdict_target") or ""),
        ]
        text = " ".join(part for part in parts if part)
    else:
        text = str(task_or_text or "")
    tokens = []
    tid_match = re.search(r"\bT-\d+\b", text)
    if tid_match:
        tokens.append(tid_match.group(0))
    batch_match = re.search(r"\bBatch\s*\d+\b", text, re.IGNORECASE)
    if batch_match:
        tokens.append(" ".join(batch_match.group(0).split()))
    subject_match = re.search(r"(?:IGCSE\s+)?[A-Za-z][A-Za-z ]+\s+\d{4}", text)
    if subject_match:
        tokens.append(subject_match.group(0).strip())
        tokens.append(subject_match.group(0).replace("IGCSE ", "").strip())
    # Keep stable order while dropping blanks/duplicates.
    seen: set[str] = set()
    out: list[str] = []
    for token in tokens:
        normalized = " ".join(token.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return tuple(out)


def _text_mentions_any_subject_token(text: str, tokens: tuple[str, ...]) -> bool:
    if not tokens:
        return False
    normalized = str(text or "")
    lowered = normalized.lower()
    return any(token in normalized or token.lower() in lowered for token in tokens)


def _text_matches_task_scope(text: str, tokens: tuple[str, ...]) -> bool:
    if not tokens:
        return False
    normalized = str(text or "")
    lowered = normalized.lower()
    has_task_id = any(
        (token in normalized or token.lower() in lowered)
        for token in tokens
        if token.lower().startswith("t-")
    )
    has_batch = any(
        (token in normalized or token.lower() in lowered)
        for token in tokens
        if token.lower().startswith("batch")
    )
    if has_task_id or has_batch:
        if has_task_id and has_batch:
            return True
        subject_tokens = [
            token for token in tokens
            if not token.lower().startswith(("t-", "batch"))
        ]
        return any(token in normalized or token.lower() in lowered for token in subject_tokens)
    strong = [
        token for token in tokens
        if token.lower().startswith("t-") or token.lower().startswith("batch")
    ]
    if strong:
        return any(token in normalized or token.lower() in lowered for token in strong)
    return _text_mentions_any_subject_token(text, tokens)


def _text_has_strong_task_scope(text: str, tokens: tuple[str, ...]) -> bool:
    normalized = str(text or "")
    lowered = normalized.lower()
    has_task_id = any(
        (token in normalized or token.lower() in lowered)
        for token in tokens
        if token.lower().startswith("t-")
    )
    has_batch = any(
        (token in normalized or token.lower() in lowered)
        for token in tokens
        if token.lower().startswith("batch")
    )
    return has_task_id and has_batch


def _visible_review_pass_for_task(task: dict, *, after: int = 0) -> dict | None:
    tokens = _subject_match_tokens(task)
    if not tokens:
        return None
    for row in local_facts.list_logs("review_course", limit=50):
        created_at = int(row.get("created_at") or 0)
        if created_at < after:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        lowered = content.lower()
        if not _text_matches_task_scope(content, tokens):
            continue
        # Check for PASS signals or task_completed markers
        has_pass = "pass" in lowered or "verdict" in lowered or "可发布" in content or "复检结果" in content
        has_completion = "task_completed" in lowered or "完工" in content or "交付" in content or "复核完成" in content
        if not (has_pass or has_completion):
            continue
        if (
            _text_has_strong_task_scope(content, tokens)
            or "verdict" in lowered
            or "可发布" in content
            or "复检结果" in content
            or "task_completed" in lowered
            or "完工" in content
        ):
            return row
    return None


def _manager_closeout_signal_for_subject(tokens: tuple[str, ...], *, after: int = 0) -> dict | None:
    if not tokens:
        return None
    for row in local_facts.list_logs("manager", limit=50):
        created_at = int(row.get("created_at") or 0)
        if created_at < after:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        if not _text_mentions_any_subject_token(content, tokens):
            continue
        lowered = content.lower()
        if (
            ("等 verdict" in lowered or "等待 verdict" in lowered or "待 verdict" in lowered)
            and "正在复检" in content
        ):
            continue
        if (
            "正式闭环" in content
            or "已闭环" in content
            or "closeout" in lowered
            or "正式 pass" in lowered
            or "正式 PASS" in content
        ):
            return row
    return None


def _conflicting_task_brief_findings(*, now: int) -> list[dict]:
    recent_ms = 30 * 60 * 1000
    rows = [
        msg for msg in local_facts.list_all_messages()
        if local_facts.is_high_priority(str(msg.get("priority") or ""))
        and now - int(msg.get("created_at") or 0) <= recent_ms
    ]
    subject_rows = [
        msg for msg in rows
        if "Business Studies 0450" in str(msg.get("content") or "")
        or "T-10" in str(msg.get("content") or "")
    ]
    nine = [msg for msg in subject_rows if _contains_9_item_standard(str(msg.get("content") or ""))]
    twelve = [msg for msg in subject_rows if _contains_12_item_standard(str(msg.get("content") or ""))]
    if not nine or not twelve:
        return []
    latest_conflict_at = max(int(msg.get("created_at") or 0) for msg in nine + twelve)
    tokens = _subject_match_tokens("T-10 Business Studies 0450")
    resolved_by_review = _visible_review_pass_for_task(
        {"id": "T-10", "title": "Business Studies 0450"},
        after=latest_conflict_at,
    )
    resolved_by_manager = _manager_closeout_signal_for_subject(tokens, after=latest_conflict_at)
    if resolved_by_review or resolved_by_manager:
        return []
    ids = [str(msg.get("local_id") or "") for msg in nine[:3] + twelve[:3]]
    return [{
        "category": "conflicting_task_brief_detected",
        "task_id": "brief:T-10",
        "stage": "inbox",
        "status": "conflicting_brief",
        "severity": "warn",
        "age_ms": max(now - max(int(msg.get("created_at") or 0) for msg in nine + twelve), 0),
        "why": "T-10 recent briefs conflict: both 9-item and 12-item standards are present",
        "evidence_summary": (
            f"nine_item_messages={','.join(str(msg.get('local_id') or '') for msg in nine[:3])} "
            f"twelve_item_messages={','.join(str(msg.get('local_id') or '') for msg in twelve[:3])}"
        ),
        "recommended_action": "clarify_current_task_standard",
        "message_id": ",".join(item for item in ids if item),
    }]


def _high_priority_inbox_blocking_findings(*, now: int) -> list[dict]:
    rows: list[dict] = []
    for msg in local_facts.list_all_messages():
        if not local_facts.is_high_priority(str(msg.get("priority") or "")):
            continue
        ack_state = str(msg.get("ack_state") or "pending")
        is_unread = not bool(msg.get("read"))
        if not is_unread and ack_state in {
            "agent_acknowledged",
            "action_started",
            "completed",
            "reconciled",
        }:
            ack_at = int(msg.get("ack_at") or 0)
            agent = str(msg.get("to") or "")
            local_id = str(msg.get("local_id") or "")
            if _ack_kind_is_stale_or_superseded(str(msg.get("ack_kind") or "")):
                continue
            if (
                ack_state == "agent_acknowledged"
                and ack_at > 0
                and agent in {"worker_course", "review_course", "worker_builder", "worker_qbank"}
                and not _agent_has_progress_signal_after_ack(agent, local_id, ack_at)
                and max(now - ack_at, 0) >= 2 * 60 * 1000
            ):
                rows.append({
                    "category": "ack_without_followthrough_signal",
                    "task_id": str(msg.get("task_id") or local_id or "inbox"),
                    "message_id": local_id,
                    "stage": "inbox",
                    "status": "awaiting_start_signal",
                    "severity": "warn",
                    "age_ms": max(now - ack_at, 0),
                    "why": f"{agent} 已接单，但还没有 started/say/过程信号，manager 仍会觉得像没在岗",
                    "evidence_summary": (
                        f"message_id={local_id} to={agent or '-'} "
                        f"ack_state={ack_state} ack_kind={msg.get('ack_kind') or '-'} "
                        f"ack_at={ack_at} content={str(msg.get('content') or '')[:120]}"
                    ),
                    "recommended_action": "request_process_visibility_signal",
                })
            continue
        agent = str(msg.get("to") or "")
        local_id = str(msg.get("local_id") or "")
        task_id = str(msg.get("task_id") or "")
        created_at = int(msg.get("created_at") or 0)
        delivery_state = str(msg.get("delivery_state") or "delivered_to_inbox")
        runtime_guard_block = local_facts.runtime_guard_block_evidence(agent)
        if is_unread and _runtime_repair_message_resolved_by_watchdog_recovery(msg):
            continue
        if _verdict_exists_for_review_handoff_message(msg):
            if task_id:
                task = tasks.get(task_id) or {}
                rows.append({
                    "category": "stale_review_handoff_reconciled",
                    "task_id": task_id or local_id or "inbox",
                    "message_id": local_id,
                    "stage": str(task.get("stage") or "inbox"),
                    "status": str(task.get("status") or "reconciled"),
                    "severity": "info",
                    "age_ms": max(now - int(msg.get("created_at") or 0), 0),
                    "why": "review_course 已给出 verdict，旧 review handoff 不再作为未消费阻塞",
                    "evidence_summary": (
                        f"message_id={local_id} task_id={task_id or '-'} "
                        f"verdict={task.get('verdict') or '-'} "
                        f"review_reason={task.get('review_reason') or '-'}"
                    ),
                    "recommended_action": "suppress_stale_review_handoff",
                })
            continue
        delegated_answer = _delegated_unread_answered_by_manager(msg, now=now)
        if delegated_answer is not None:
            rows.append(delegated_answer)
            continue
        if is_unread and _message_has_later_direct_process_visibility(msg):
            rows.append({
                "category": "high_priority_inbox_unread_desynced",
                "task_id": str(msg.get("task_id") or local_id or "inbox"),
                "message_id": local_id,
                "agent": agent,
                "stage": "inbox",
                "status": "read_state_desync",
                "severity": "info",
                "age_ms": max(now - created_at, 0),
                "why": f"{agent} 的高优消息仍是 unread，但后续日志/状态已经证明它被执行过了",
                "evidence_summary": (
                    f"message_id={local_id} delivery_state={delivery_state} "
                    f"to={agent or '-'} from={msg.get('from') or '-'} "
                    f"content={str(msg.get('content') or '')[:120]}"
                ),
                "recommended_action": "reconcile_inbox_state",
            })
            continue
        if not is_unread and (
            _runtime_repair_message_resolved_by_watchdog_recovery(msg)
            or _builder_runtime_course_message_resolved_by_later_closeout(msg)
            or
            _message_has_sender_visibility(msg)
            or _message_has_local_visibility_ref(agent, local_id)
            or _agent_has_related_visibility_after(agent, created_at, str(msg.get("content") or ""))
            or _message_superseded_by_projected_status(agent, str(msg.get("content") or ""), created_at)
            or _message_superseded_by_manager_closeout(agent, str(msg.get("content") or ""), created_at)
        ):
            continue
        age_ms = max(now - created_at, 0)
        status_row_for_evidence: dict = {}
        if is_unread:
            if runtime_guard_block is not None:
                category = "high_priority_inbox_runtime_guard_blocked"
                action = "repair_or_rehire_agent_runtime"
                why = (
                    f"{agent} 有未读高优消息，但 runtime guard 已升级；"
                    "应先修复运行时/rehire，而不是只催 consume inbox"
                )
            elif delivery_state == "requires_polling":
                category = "high_priority_inbox_requires_polling"
                action = "poll_or_consume_high_priority_inbox"
                why = (
                    f"{agent} 的高优消息通过 --no-inject 静默投递，当前需要靠 inbox 轮询消费；"
                    "这应单独观察，不和 live 注入失败混为一谈"
                )
            else:
                category = "high_priority_inbox_unread_blocking"
                action = "consume_high_priority_inbox"
                why = f"{agent} 有未读高优消息，普通 rollover 不应覆盖它"
        else:
            if age_ms > HIGH_PRIORITY_READ_WITHOUT_ACK_WINDOW_MS:
                continue
            status_matches, status_row = _agent_status_indicates_related_progress(
                agent,
                str(msg.get("content") or ""),
            )
            if not status_matches:
                status_matches = _agent_has_followthrough_visibility_after(agent, created_at)
            status_row_for_evidence = status_row
            if status_matches:
                category = "high_priority_inbox_started_without_explicit_ack"
                action = "record_or_request_explicit_ack"
                status_label = "ack_semantics_gap"
                severity = "info"
                why = (
                    f"{agent} 已有相关状态/过程信号，但 inbox 仍缺 explicit ACK；"
                    "应补齐 ACK 语义，不应误判为未在岗"
                )
            else:
                category = "high_priority_inbox_read_without_ack"
                action = "request_explicit_agent_ack"
                status_label = "blocking"
                severity = "warn"
                why = f"{agent} 已读高优消息但没有 accepted/start/revision ACK"
        rows.append({
            "category": category,
            "task_id": str(msg.get("task_id") or local_id or "inbox"),
            "message_id": local_id,
            "agent": agent,
            "stage": "inbox",
            "status": status_label if not is_unread else "blocking",
            "severity": severity if not is_unread else "warn",
            "age_ms": age_ms,
            "why": why,
            "evidence_summary": (
                f"message_id={local_id} to={agent or '-'} from={msg.get('from') or '-'} "
                f"read={bool(msg.get('read'))} ack_state={ack_state} "
                f"ack_kind={msg.get('ack_kind') or '-'} "
                f"delivery_state={delivery_state} "
                f"runtime_guard={runtime_guard_block.get('last_failure_reason') if runtime_guard_block else '-'} "
                f"runtime_guard_outcome={runtime_guard_block.get('last_switch_outcome') if runtime_guard_block else '-'} "
                f"status={status_row_for_evidence.get('status') or '-'} "
                f"status_task={str(status_row_for_evidence.get('task') or '')[:120]} "
                f"content={str(msg.get('content') or '')[:120]}"
            ),
            "recommended_action": action,
        })
    return _collapse_redundant_unread_blockers(rows)


def _runtime_repair_message_resolved_by_watchdog_recovery(msg: dict) -> bool:
    content = str(msg.get("content") or "")
    lowered = content.lower()
    if not any(marker in lowered for marker in ("watchdog", "router")):
        return False
    if not any(marker in content for marker in ("修复", "恢复", "排查", "重启", "兜底保障", "未启动", "缺失", "no pid file")):
        return False
    rows = _watchdog_rows()
    by_name = {str(row.get("name") or ""): row for row in rows}
    for name in ("router", "watchdog"):
        row = by_name.get(name) or {}
        if not row.get("pid_present") or not row.get("alive"):
            return _runtime_repair_message_resolved_by_later_closeout(msg)
    return True


def _runtime_repair_message_resolved_by_later_closeout(msg: dict) -> bool:
    created_at = int(msg.get("created_at") or 0)
    for agent in ("auto_ops", "manager", "worker_builder"):
        for row in local_facts.list_logs(agent, limit=50):
            if int(row.get("created_at") or 0) < created_at:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed", "task"}:
                continue
            content = str(row.get("content") or "")
            lowered = content.lower()
            if (
                ("watchdog 已恢复" in content or "watchdog 修复闭环" in content)
                and ("health 全绿" in content or "alive" in lowered or "pid" in lowered)
            ):
                return True
    return False


def _builder_runtime_course_message_resolved_by_later_closeout(msg: dict) -> bool:
    if str(msg.get("to") or "") != "worker_builder":
        return False
    content = str(msg.get("content") or "")
    lowered = content.lower()
    if not any(marker in lowered for marker in ("worker_course", "qoder", "runtime", "stale")):
        return False
    if not any(marker in content for marker in ("纠偏", "排查", "阻断", "验证", "修复", "respawn")):
        return False
    created_at = int(msg.get("created_at") or 0)
    for agent in ("manager", "worker_course", "review_course"):
        for row in local_facts.list_logs(agent, limit=50):
            if int(row.get("created_at") or 0) < created_at:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed"}:
                continue
            row_content = str(row.get("content") or "")
            row_lowered = row_content.lower()
            if (
                "closeout" in row_lowered
                or "pass" in row_lowered
                or "已交付" in row_content
                or "已完成并交给 manager" in row_content
            ):
                return True
    return False


def _delegated_unread_answered_by_manager(msg: dict, *, now: int) -> dict | None:
    if bool(msg.get("read")):
        return None
    agent = str(msg.get("to") or "")
    if agent not in DIRECT_VISIBILITY_AGENTS:
        return None
    content = str(msg.get("content") or "")
    expected_keywords = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected_keywords and not expected_tokens:
        return None
    created_at = int(msg.get("created_at") or 0)
    local_id = str(msg.get("local_id") or "")
    for row in local_facts.list_logs("manager", limit=30):
        row_created = int(row.get("created_at") or 0)
        if row_created < created_at:
            continue
        if str(row.get("type") or "") != "say":
            continue
        row_content = str(row.get("content") or "")
        row_keywords = _visibility_keywords(row_content)
        row_tokens = _visibility_tokens(row_content)
        if not (expected_keywords & row_keywords or expected_tokens & row_tokens):
            continue
        if not any(marker in row_content for marker in ("已核实", "结论", "无法执行", "可行性", "恢复", "切换")):
            continue
        return {
            "category": "delegated_task_answered_by_manager_but_worker_unread",
            "task_id": str(msg.get("task_id") or local_id or "inbox"),
            "message_id": local_id,
            "agent": agent,
            "stage": "inbox",
            "status": "manager_secondhand_answer_worker_unread",
            "severity": "info",
            "live_blocker": False,
            "age_ms": max(now - created_at, 0),
            "why": (
                f"manager 已对派给 {agent} 的问题给出二手结论，但 {agent} 自己仍未读；"
                "这不是 agent 在岗，只说明派单已被 manager 代办/需清理或改派"
            ),
            "evidence_summary": (
                f"message_id={local_id} manager_log={row.get('local_id') or '-'} "
                f"agent={agent} inbox_content={content[:140]} manager_content={row_content[:180]}"
            ),
            "recommended_action": "clear_or_reassign_stale_delegation",
        }
    return None


def _collapse_redundant_unread_blockers(rows: list[dict]) -> list[dict]:
    """Keep diagnostics focused on the current unread blocker per agent.

    The inbox remains untouched. This only prevents one stale high-priority
    backlog from appearing as several separate manager-facing blockers when
    the latest unread message already represents the current work.
    """
    latest_unread_by_agent: dict[str, dict] = {}
    for row in rows:
        if row.get("category") != "high_priority_inbox_unread_blocking":
            continue
        agent = str(row.get("agent") or "")
        if not agent:
            continue
        current = latest_unread_by_agent.get(agent)
        if current is None or int(row.get("age_ms") or 0) <= int(current.get("age_ms") or 0):
            latest_unread_by_agent[agent] = row
    output: list[dict] = []
    for row in rows:
        if row.get("category") != "high_priority_inbox_unread_blocking":
            output.append(row)
            continue
        agent = str(row.get("agent") or "")
        if latest_unread_by_agent.get(agent) is row:
            output.append(row)
    return output


def _verdict_exists_for_review_handoff_message(msg: dict) -> bool:
    if str(msg.get("to") or "") != "review_course":
        return False
    task_id = str(msg.get("task_id") or "")
    created_at = int(msg.get("created_at") or 0)
    if not task_id:
        content = str(msg.get("content") or "")
        tokens = _visibility_tokens(content)
        if not tokens:
            return False
        for agent in ("review_course", "manager"):
            for row in local_facts.list_logs(agent, limit=30):
                if int(row.get("created_at") or 0) < created_at:
                    continue
                if str(row.get("type") or "") not in {"say", "task_completed"}:
                    continue
                row_content = str(row.get("content") or "")
                lowered = row_content.lower()
                terminal = (
                    "pass" in lowered
                    or "verdict" in lowered
                    or "closeout" in lowered
                    or "复核完成" in row_content
                    or "复检 pass" in lowered
                )
                if terminal and tokens & _visibility_tokens(row_content):
                    return True
        return False
    task = tasks.get(task_id) or {}
    if task.get("schema_version") != 2:
        return False
    verdict = str(task.get("verdict") or "")
    status = str(task.get("status") or "")
    verdict_at = int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
    return verdict in {"approved", "rejected", "manager_action"} and status != "submitted_for_review" and verdict_at >= created_at


def _revision_ack_missing_finding(task: dict) -> dict | None:
    if str(task.get("verdict") or "") != "rejected":
        return None
    task_id = str(task.get("id") or "")
    owner = str(task.get("owner") or task.get("assignee") or "")
    related = [
        msg for msg in local_facts.list_all_messages()
        if str(msg.get("task_id") or "") == task_id and str(msg.get("to") or "") == owner
    ]
    accepted = any(str(msg.get("ack_kind") or "") == "accepted_revision" for msg in related)
    if accepted:
        return None
    latest = related[-1] if related else {}
    return {
        "category": "revision_ack_missing",
        "task_id": task_id,
        "message_id": str(latest.get("local_id") or ""),
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": "review_course 已退回修改，但 worker_course 尚未显式 accepted_revision",
        "evidence_summary": (
            f"verdict={task.get('verdict') or '-'} "
            f"review_reason={task.get('review_reason') or '-'} "
            f"scope_topic={task.get('scope_topic') or '-'} "
            f"owner={owner or '-'} expected_ack=accepted_revision "
            f"latest_message={latest.get('local_id') or '-'} "
            f"latest_ack={latest.get('ack_kind') or '-'}"
        ),
        "recommended_action": "request_worker_revision_ack",
    }


def _stale_execution_context_finding() -> list[dict]:
    """Surface tasks whose revision_priority is still set while the worker's
    own local-facts surface shows execution outside the revision scope.

    Package 7 (Revision-First Gate): the field is sticky on the structured
    task, so a worker that ignores the unacknowledged revision and
    pivots to a new topic (e.g. "8.x", "0653", "next subject") is
    operating on stale context. The supervisor emits a finding with
    the required contract fields so the manager can intervene.

    Observed-scope sources include:
      * local_facts.get_status(agent).task
      * local_facts.get_status(agent).blocker
      * the agent's recent local_facts logs (limit 8, not just 3) so a
        worker that already started writing the new subject shows up
        here even if the status row is still stale.

    Scope-violation detection is structural, not just keyword:
      * explicit pivot markers (8.x, 0653, next subject, 下一学科, ...)
      * hyphenated subject IDs outside the expected scope, e.g.
        `igcse-physics-0625-batch-8`, `igcse-biology-0610-topic-3`
      * `batch-N` / `topic-N` references where N is non-zero and the
        expected scope does not include the same batch/topic
    """
    rows: list[dict] = []
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        if str(task.get("status") or "") in {"delivered", "cancelled"}:
            continue
        revision_priority = str(task.get("revision_priority") or "").strip()
        if not revision_priority:
            continue
        owner = str(task.get("owner") or task.get("assignee") or "")
        if not owner:
            continue
        status_row = local_facts.get_status(owner) or {}
        # Package 7 (Revision-First Gate): only consider local_facts
        # signals that occurred AFTER revision_priority was set. Old
        # out-of-scope logs from before the revision instruction must
        # not produce a false positive once the worker has returned to
        # the correct revision scope.
        revision_set_at = int(task.get("revision_priority_set_at") or 0)
        log_text_parts: list[str] = []
        for log_row in local_facts.list_logs(owner, limit=20):
            if revision_set_at:
                log_ts = int(log_row.get("created_at") or 0)
                if log_ts < revision_set_at:
                    continue
            log_text_parts.append(str(log_row.get("content") or ""))
        log_text = " ".join(part for part in log_text_parts if part)
        status_text = " ".join(
            str(status_row.get(key) or "")
            for key in ("task", "blocker")
        ).strip()
        observed_scope = " ".join(
            part for part in (status_text, log_text) if part
        ).strip()
        if not observed_scope:
            continue
        expected_scope = str(task.get("scope_topic") or task.get("title") or "").strip()
        scope_files = task.get("scope_files") or []
        if scope_files:
            expected_scope = f"{expected_scope} {' '.join(str(f) for f in scope_files)}".strip()
        if not expected_scope:
            expected_scope = str(task.get("id") or "")
        # Hard-coded scope-violation markers: topic-style references
        # (8.x), syllabus codes outside scope (0653), or explicit
        # "next subject" pivots all count as out-of-scope REGARDLESS
        # of whether the same subject token appears in the observed
        # text. A worker that is currently working on Physics 0625 but
        # is told to "fix batch-7 first" and instead jumps to "topic
        # 8.x" is still pivoting, even though the subject token is
        # the same. Order matters: check pivot markers FIRST.
        #
        # SCOPE-AWARE: if the marker ALSO appears in `expected_scope`
        # (e.g. expected_scope="igcse-biology-0610 topic 8 batch-7"
        # and observed says "topic 8" while working on biology 0610),
        # the worker is staying on the expected scope, not pivoting.
        # Only markers that are NOT in `expected_scope` count as a
        # pivot. This is the false-positive guard requested in
        # Codex round 4.
        #
        # Normalize hyphens/dots/commas to spaces so "topic-8" /
        # "topic 8" and "8.x" / "8" match across forms. Note that
        # the dot normalization is what makes the "8.x" marker
        # collapse to "8 x", so we additionally check the bare
        # "8 " / " 8" token via word boundary in the normalized text.
        lowered_observed = observed_scope.lower().replace("-", " ").replace(".", " ").replace(",", " ")
        lowered_expected = expected_scope.lower().replace("-", " ").replace(".", " ").replace(",", " ")
        # For the special "8.x" / "topic 8" markers, presence in
        # expected is decided by whether the digit "8" appears in
        # the expected scope as a topic/batch number (i.e. surrounded
        # by topic/batch/unit/space), so that "igcse-physics-0625
        # topic-8 batch-7" still matches and prevents the false
        # positive.
        has_topic_8_in_expected = bool(
            re.search(r"\b(topic|batch|unit|chapter)\s*8\b", lowered_expected)
        )

        def _marker_pivot(marker: str) -> bool:
            """Return True iff `marker` appears in observed_scope
            (raw or normalized) but does NOT appear in expected_scope
            (raw or normalized) AND the marker is not implicit in
            the expected scope via the topic-N guard above."""
            in_obs = marker in observed_scope or marker in lowered_observed
            in_exp = marker in expected_scope or marker in lowered_expected
            if marker in {"8.x", "topic 8"}:
                # If expected has topic-8 / batch-8 (or normalized
                # `topic 8`), the worker is allowed to mention 8 / 8.x.
                if has_topic_8_in_expected:
                    return False
            return in_obs and not in_exp

        pivot_marker_violation = any(
            _marker_pivot(marker) for marker in (
                "8.x", "topic 8", "0653", "next subject",
                "下一学科", "下一批", "转入", "切换到",
            )
        )
        structural_violation = _structural_pivot_detected(expected_scope, observed_scope)
        scope_violation = pivot_marker_violation or structural_violation
        if not scope_violation:
            in_scope = _text_mentions_any_subject_token(
                observed_scope, _subject_match_tokens(expected_scope),
            )
            if in_scope:
                continue
            # Neither in-scope nor a pivot — no finding.
            continue
        # Skip the broad same-subject escape: even if observed text
        # mentions the same subject, a pivot marker or structural
        # batch/topic mismatch is enough.
        rows.append({
            "category": "stale_execution_context",
            "task_id": str(task.get("id") or ""),
            "workflow_id": str(task.get("workflow_id") or "").strip(),
            "stage": str(task.get("stage") or ""),
            "status": str(task.get("status") or ""),
            "severity": "warn",
            "expected_revision_scope": expected_scope,
            "observed_new_scope": observed_scope[:240],
            "why": (
                f"{owner} local_facts shows work on new scope while "
                f"task {task.get('id') or '-'} still has "
                f"revision_priority={revision_priority}; expected to stay on "
                f"the revision scope {expected_scope!r} until clear_revision_priority"
            ),
            "evidence_summary": (
                f"owner={owner} status_task={str(status_row.get('task') or '')[:160]} "
                f"status_blocker={str(status_row.get('blocker') or '')[:120]} "
                f"revision_priority={revision_priority} "
                f"scope_topic={expected_scope}"
            ),
            "recommended_action": "stop_pivot_to_revision_scope_or_clear_revision_priority",
        })
    return rows


# Pattern: hyphenated IDs that look like subject / batch / topic
# references the worker might put into a status row when it pivots.
# Package 7 (Revision-First Gate) round 7 fix: accept multi-token
# subject slugs like `igcse-combined-science-0653-batch-8` so they
# are structurally detected, not just single-token slugs.
_IGCSE_HYPHEN_ID = re.compile(
    r"\bigcse-(?:[a-z]+-)*[a-z]+-\d{4}(?:-batch-\d+|-topic-\d+)?\b",
    re.IGNORECASE,
)
_BATCH_TOPIC_REF = re.compile(r"\b(?:batch|topic|unit)-(\d+)\b", re.IGNORECASE)


def _structural_pivot_detected(expected_scope: str, observed_scope: str) -> bool:
    """Return True if `observed_scope` references an IGCSE subject,
    batch, or topic that is not part of `expected_scope`.

    False positive guards:
      * tokens that appear in BOTH scopes are skipped (in-scope work)
      * `batch-0` / `topic-0` is treated as "no batch / topic" and skipped
    """
    if not expected_scope or not observed_scope:
        return False
    expected_norm = expected_scope.lower()
    observed_norm = observed_scope.lower()
    # Look at every hyphenated IGCSE subject ID in observed text.
    for match in _IGCSE_HYPHEN_ID.findall(observed_norm):
        if match in expected_norm:
            continue
        return True
    # Look at batch-N / topic-N references in observed text.
    for n_str in _BATCH_TOPIC_REF.findall(observed_norm):
        try:
            n = int(n_str)
        except ValueError:
            continue
        if n == 0:
            continue
        # If observed mentions batch-N or topic-N and expected does NOT
        # mention the same number, treat as pivot.
        expected_has_same = (
            f"batch-{n}" in expected_norm or f"topic-{n}" in expected_norm
        )
        if not expected_has_same:
            return True
    return False


def _evidence_packet_incomplete_finding() -> list[dict]:
    """Package 7 (Revision-First Gate): flag any flow task whose
    evidence_packet is incomplete (missing one or more required fields).

    Required fields are defined in REQUIRED_EVIDENCE_PACKET_FIELDS and
    validated by `validate_evidence_packet()`. The finding is consumed
    by `scan_manager_anomalies` and surfaces in supervisor-check output
    and manager-panel; closeout paths that try to advance on an
    incomplete packet must be blocked separately by the closeout gate.

    Coverage:
      * non-terminal active tasks (in_progress / submitted_for_review /
        blocked / assigned) — these may still submit a complete packet.
      * delivered + approved closeout candidates — the closeout gate
        MUST block advance on these, but the supervisor must still
        surface the gap so the manager can request the missing fields
        BEFORE applying manager_formal_closeout.
      * `cancelled` tasks are skipped (terminal and not a closeout
        candidate).
    """
    findings: list[dict] = []
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        status = str(task.get("status") or "")
        verdict = str(task.get("verdict") or "")
        # Skip pure-cancelled tasks; everything else is in scope.
        if status == "cancelled":
            continue
        # Delivered-only or active-only. Delivered+approved is the
        # closeout-candidate window and is the most important one to
        # flag because a missing-fields block here stops the closeout
        # advance at the gate.
        is_active = status not in tasks.FLOW_TERMINAL_STATUSES
        is_closeout_candidate = (
            status == "delivered" and verdict == "approved"
        )
        if not (is_active or is_closeout_candidate):
            continue
        packet = task.get("evidence_packet") or {}
        if not isinstance(packet, dict) or not packet:
            continue
        missing = validate_evidence_packet(packet)
        if not missing:
            continue
        # The `severity` is escalated to `error` for closeout
        # candidates so the manager-panel and manager-actions cannot
        # ignore the gap and accidentally try to close out without
        # the required worker evidence.
        severity = "error" if is_closeout_candidate else "warn"
        findings.append({
            "category": "evidence_packet_incomplete",
            "task_id": str(task.get("id") or ""),
            "workflow_id": str(task.get("workflow_id") or ""),
            "stage": str(task.get("stage") or ""),
            "status": status,
            "verdict": verdict,
            "is_closeout_candidate": is_closeout_candidate,
            "severity": severity,
            "missing_fields": missing,
            "why": (
                f"evidence_packet for task {task.get('id') or '-'} is "
                f"missing required fields: {','.join(missing)}. "
                + (
                    "Closeout candidate (delivered+approved) — block manager_formal_closeout until complete."
                    if is_closeout_candidate
                    else "Active task — request the missing fields from the worker before advance."
                )
            ),
            "evidence_summary": (
                f"present_fields={','.join(sorted(packet.keys())) or 'none'} "
                f"missing_fields={','.join(missing)}"
            ),
            "recommended_action": "block_closeout_until_evidence_packet_complete",
        })
    return findings


def _review_scope_mismatch_finding(task: dict) -> dict | None:
    if str(task.get("verdict") or "") not in {"approved", "rejected", "manager_action"}:
        return None
    scope_text = _normalize_text(
        " ".join([
            str(task.get("scope_topic") or ""),
            str(task.get("verdict_target") or ""),
            " ".join(str(item) for item in task.get("scope_files") or []),
        ])
    )
    if not scope_text:
        return None
    expected = _normalize_text(
        " ".join([
            str(task.get("title") or ""),
            str(task.get("description") or ""),
            str(task.get("latest_turn_summary") or ""),
        ])
    )
    if not expected:
        return None
    scope_tokens = {token for token in scope_text.split() if any(ch.isdigit() for ch in token) or len(token) >= 5}
    if not scope_tokens:
        return None
    if any(token in expected for token in scope_tokens):
        return None
    return {
        "category": "review_scope_mismatch",
        "task_id": str(task.get("id") or ""),
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "severity": "warn",
        "why": "review verdict 的 scope 与任务标题/brief 不一致，可能越界吸收了其他 topic",
        "evidence_summary": (
            f"title={task.get('title') or '-'} "
            f"scope_topic={task.get('scope_topic') or '-'} "
            f"verdict_target={task.get('verdict_target') or '-'} "
            f"scope_files={','.join(str(item) for item in task.get('scope_files') or []) or '-'}"
        ),
        "recommended_action": "request_narrow_review_recheck",
    }


def _task_ids_with_category(findings: list[dict], category: str) -> list[str]:
    ids: list[str] = []
    for row in findings:
        if str(row.get("category") or "") != category:
            continue
        task_id = str(row.get("task_id") or "")
        if task_id and task_id not in ids:
            ids.append(task_id)
    return ids


def _recent_publishable_results(*, now: int) -> list[dict]:
    rows = scan_publish_decisions(to_target="user", include_silent=True, advance=False)
    recent: list[dict] = []
    for row in rows:
        if str(row.get("reason") or "") != "delivered_to_user":
            continue
        created_at = int(row.get("created_at") or 0)
        if now - created_at > SUPERVISOR_STALE_RESULT_MS:
            continue
        recent.append(row)
    return recent


def _manager_runtime_reason(*, now: int) -> str:
    guard_agents = _runtime_guard_state().get("agents", {})
    if any(bool(row.get("escalation_needed", False)) for row in guard_agents.values()):
        return "runtime_unhealthy"
    watchdog_rows = _watchdog_rows()
    if any(
        row["name"] in {"router", "watchdog", "hermes-supervisor"}
        and (not row["pid_present"] or not row["alive"])
        for row in watchdog_rows
    ):
        return "runtime_unhealthy"
    heartbeat = local_facts.get_heartbeat("manager")
    if heartbeat is None:
        return "runtime_unhealthy"
    if now - int(heartbeat) > SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS:
        return "runtime_unhealthy"
    return "manager_recently_active"


def _manager_high_priority_unread_reason(*, now: int) -> str:
    for row in local_facts.list_messages("manager", unread_only=True):
        if not local_facts.is_high_priority(str(row.get("priority") or "")):
            continue
        age_ms = now - int(row.get("created_at") or 0)
        if age_ms >= SUPERVISOR_MANAGER_HIGH_PRIORITY_UNREAD_MS:
            return "manager_high_priority_unread"
    return ""


def _manager_unconsumed_auto_report_reason(*, now: int) -> str:
    markers = (
        "manager_unconsumed",
        "未处理",
        "未消费",
        "卡住",
        "异常",
        "anomaly",
        "review",
        "复核",
        "verdict",
        "manager_action",
        "runtime",
        "failover",
        "fallback",
    )
    for row in local_facts.list_messages("manager", unread_only=True):
        if str(row.get("from") or "") != "auto_ops":
            continue
        if str(row.get("priority") or "") not in {"中", "高"}:
            continue
        age_ms = now - int(row.get("created_at") or 0)
        if age_ms < SUPERVISOR_MANAGER_AUTO_REPORT_UNREAD_MS:
            continue
        content = str(row.get("content") or "")
        lowered = content.lower()
        if any(marker in content or marker in lowered for marker in markers):
            return "manager_unconsumed_auto_report"
    return ""


def _auto_summary_reasons(*, now: int, anomalies: list[dict]) -> list[str]:
    reasons: list[str] = []

    runtime_reason = _manager_runtime_reason(now=now)
    if runtime_reason == "runtime_unhealthy":
        reasons.append(runtime_reason)
        guard_agents = _runtime_guard_state().get("agents", {})
        if any(bool(row.get("escalation_needed", False)) for row in guard_agents.values()):
            reasons.append("agent_failover_escalation")
        watchdog_rows = _watchdog_rows()
        if any(row["name"] == "router" and row["pid_present"] and not row["alive"] for row in watchdog_rows):
            reasons.append("router_down")
        if any(row["name"] == "watchdog" and (not row["pid_present"] or not row["alive"]) for row in watchdog_rows):
            reasons.append("watchdog_down")
        if any(row["name"] == "hermes-supervisor" and (not row["pid_present"] or not row["alive"]) for row in watchdog_rows):
            reasons.append("hermes_supervisor_down")

    unread_reason = _manager_high_priority_unread_reason(now=now)
    if unread_reason:
        reasons.append(unread_reason)

    auto_report_reason = _manager_unconsumed_auto_report_reason(now=now)
    if auto_report_reason:
        reasons.append(auto_report_reason)

    stale_ids = _task_ids_with_category(anomalies, "stale_task")
    if stale_ids:
        reasons.append("stale_task_backlog")

    process_visibility_ids = _task_ids_with_category(anomalies, "process_visibility_stale")
    if process_visibility_ids:
        reasons.append("process_visibility_stale")

    status_lag_ids = _task_ids_with_category(anomalies, "status_truth_lag_detected")
    if status_lag_ids:
        reasons.append("status_surface_truth_lag")

    context_risk_categories = {
        "worker_context_exhausted",
        "worker_context_compact_recommended",
        "worker_high_priority_unacked_while_producing",
        "status_pane_truth_conflict",
        "unsafe_long_context_execution",
    }
    if any(str(row.get("category") or "") in context_risk_categories for row in anomalies):
        reasons.append("worker_context_risk")

    manager_action_ids = _task_ids_with_category(anomalies, "manager_action_overdue")
    if manager_action_ids:
        reasons.append("manager_action_backlog")

    reject_loop_ids = _task_ids_with_category(anomalies, "reject_resubmit_loop")
    if reject_loop_ids:
        reasons.append("repeated_review_loop")

    active_rows = _active_flow_tasks()
    if any(
        now - int(task.get("last_meaningful_update_at") or task.get("updated_at") or 0)
        <= SUPERVISOR_RECENT_ACTIVITY_MS
        for task in active_rows
    ):
        reasons.append("manager_recently_active")
    elif active_rows:
        reasons.append("manager_idle_too_long")

    if _recent_publishable_results(now=now):
        reasons.append("result_waiting_unclosed")

    if not reasons:
        reasons.append("manager_recently_active")

    return reasons


def _supervisor_message_for_action(action: str, reasons: list[str]) -> str:
    reason_text = "、".join(reasons) if reasons else "未归类原因"
    if action == "alert_user_supervision_issue":
        return f"Hermes 监控发现运行监督异常，已进入监督处理：{reason_text}。"
    if action == "alert_user_repair_started":
        return f"Hermes 已启动运行态修复流程：{reason_text}。"
    if action == "alert_user_repair_result":
        return f"Hermes 已完成本轮运行态修复检查：{reason_text}。"
    return ""


def evaluate_manager_supervision(*, now: int | None = None) -> dict:
    current_now = int(now if now is not None else now_ms())
    anomalies = scan_manager_anomalies(now=current_now)
    reasons = _auto_summary_reasons(now=current_now, anomalies=anomalies)
    state = read_supervisor_state()

    severe_reasons = {
        "runtime_unhealthy",
        "manager_action_backlog",
        "repeated_review_loop",
        "manager_high_priority_unread",
        "manager_unconsumed_auto_report",
        "status_surface_truth_lag",
        "worker_context_risk",
    }
    soft_reasons = {
        "stale_task_backlog",
        "manager_idle_too_long",
        "process_visibility_stale",
        "result_waiting_unclosed",
    }

    primary_reason = next(
        (reason for reason in reasons if reason in severe_reasons),
        next((reason for reason in reasons if reason in soft_reasons), reasons[0] if reasons else ""),
    )

    has_severe = any(reason in severe_reasons for reason in reasons)
    has_soft = any(reason in soft_reasons for reason in reasons)

    previous_reason = str(state.get("last_primary_reason") or "")
    previous_issue_count = int(state.get("consecutive_issue_count") or 0)
    if primary_reason and primary_reason != "manager_recently_active":
        consecutive_issue_count = previous_issue_count + 1 if previous_reason == primary_reason else 1
    else:
        consecutive_issue_count = 0

    if has_severe:
        health_status = "repair_needed"
    elif has_soft:
        health_status = "soft_warning_observe"
    else:
        health_status = "healthy_silent"

    if health_status == "repair_needed" and consecutive_issue_count >= SUPERVISOR_REPEAT_ALERT_THRESHOLD:
        health_status = "escalated_failure"

    if health_status == "healthy_silent":
        recommended_action = "no_action"
        user_alert_action = "no_alert"
    elif health_status == "soft_warning_observe":
        recommended_action = "continue_observing"
        user_alert_action = "no_alert"
    elif health_status == "repair_needed":
        if "worker_context_risk" in reasons:
            recommended_action = "interrupt_old_context_and_read_inbox"
        elif "runtime_unhealthy" in reasons:
            recommended_action = "trigger_supervisor_repair"
        else:
            recommended_action = "trigger_manager_recheck"
        user_alert_action = "alert_user_repair_started"
    else:
        recommended_action = "trigger_supervisor_repair"
        user_alert_action = "alert_user_supervision_issue"

    repair_channel = "hermes_supervision_group"
    if user_alert_action == "no_alert":
        user_message = ""
    else:
        user_message = _supervisor_message_for_action(user_alert_action, reasons)

    state_last_check = int(state.get("last_check_at") or 0)
    state_stale = bool(
        state_last_check
        and (
            str(state.get("last_health_status") or "") != health_status
            or str(state.get("last_primary_reason") or "") != (primary_reason or "manager_recently_active")
        )
    )

    return {
        "heartbeat_interval_ms": SUPERVISOR_HEARTBEAT_INTERVAL_MS,
        "checked_at": current_now,
        "health_status": health_status,
        "primary_reason": primary_reason or "manager_recently_active",
        "auto_summary_reasons": reasons,
        "recommended_action": recommended_action,
        "user_alert_action": user_alert_action,
        "user_message": user_message,
        "repair_channel": repair_channel,
        "consecutive_issue_count": consecutive_issue_count,
        "anomalies": anomalies,
        "runtime_guard_agents": _runtime_guard_state().get("agents", {}),
        "supervisor_processes": _watchdog_rows(),
        "state_before": state,
        "state_stale": state_stale,
        "state_age_ms": max(current_now - state_last_check, 0) if state_last_check else 0,
    }


def advance_manager_supervision(result: dict) -> dict:
    state = read_supervisor_state()
    action = str(result.get("recommended_action") or "")
    alert_action = str(result.get("user_alert_action") or "")
    checked_at = int(result.get("checked_at") or 0)
    updated = {
        "last_check_at": checked_at,
        "last_health_status": str(result.get("health_status") or ""),
        "last_primary_reason": str(result.get("primary_reason") or ""),
        "consecutive_issue_count": int(result.get("consecutive_issue_count") or 0),
        "last_repair_at": int(state.get("last_repair_at") or 0),
        "last_alert_at": int(state.get("last_alert_at") or 0),
    }
    if action in {"trigger_manager_recheck", "trigger_manager_wake", "trigger_supervisor_repair"}:
        updated["last_repair_at"] = checked_at
    if alert_action != "no_alert":
        updated["last_alert_at"] = checked_at
    write_supervisor_state(updated)
    result = dict(result)
    result["state_after"] = updated
    return result
