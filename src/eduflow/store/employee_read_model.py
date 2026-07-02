"""Employee read model — a read-only projection of an agent's surface state.

Aggregates status, heartbeat, logs, inbox, task truth, workflow gate, and
residency into one machine-readable snapshot so dashboards and Feishu cards
can reason about "who is doing what, where they are stuck, and whether the
display is stale" without re-implementing the projection rules in every
consumer.

The module is intentionally read-only: it never writes to
``.eduflow-team-state/`` and never triggers side effects such as sending
Feishu messages or running sleep/wake machinery.
"""
from __future__ import annotations

from eduflow.runtime import config, residency
from eduflow.store import agent_residency, local_facts, tasks
from eduflow.util import now_ms


# Time thresholds (milliseconds).  Kept as module constants so tests and
# downstream consumers can import them directly.
STATUS_STALE_MS = 30 * 60 * 1000
HEARTBEAT_FRESH_MS = 10 * 60 * 1000
LOG_FRESH_MS = 20 * 60 * 1000

# Recent wake-failure evidence window (milliseconds).
_WAKE_FAILURE_WINDOW_MS = 30 * 60 * 1000

_IDLE_STATUSES = {"ready", "idle", "待命", "空闲"}
_IN_PROGRESS_STATUSES = {"进行中", "in_progress"}
_BLOCKED_STATUSES = {"受阻", "blocked"}
_STOPPED_STATUS = "已停止"


def _now_s() -> float:
    """Current epoch time in seconds."""
    return now_ms() / 1000.0


def _residency_policy(agent: str) -> residency.ResidencyPolicy:
    """Return the effective residency policy, degrading to warm defaults."""
    try:
        return config.load_residency_policy(agent)
    except Exception:
        return residency.ResidencyPolicy(
            mode=residency.DEFAULT_MODE,
            idle_timeout_s=residency.DEFAULT_IDLE_TIMEOUT_S,
            handoff_buffer_s=residency.DEFAULT_HANDOFF_BUFFER_S,
            wake_timeout_s=residency.DEFAULT_WAKE_TIMEOUT_S,
            source="default",
        )


def _residency_row(agent: str) -> dict:
    """Return a safe residency row dict (empty if never touched)."""
    try:
        row = agent_residency.get(agent)
    except Exception:
        row = None
    return dict(row) if row else {}


def _sleep_decision(agent: str, policy: residency.ResidencyPolicy,
                    row: dict, *, has_active_task: bool,
                    has_unread_inbox: bool) -> str:
    """Compute the residency sleep decision from collected signals.

    This is a pure read-model classification; it does NOT retire the agent.
    """
    now_s = _now_s()

    last_active_at = row.get("last_active_at")
    last_handoff_at = row.get("last_handoff_at")
    status_updated_at_ms = 0
    status_row = local_facts.get_status(agent)
    if status_row:
        status_updated_at_ms = int(status_row.get("updated_at") or 0)
    log_rows = local_facts.list_logs(agent, limit=1)
    log_at_ms = int(log_rows[-1].get("created_at", 0)) if log_rows else 0
    heartbeat_ms = local_facts.get_heartbeat(agent) or 0

    signal_times_s = []
    if isinstance(last_active_at, (int, float)):
        signal_times_s.append(float(last_active_at))
    if status_updated_at_ms:
        signal_times_s.append(status_updated_at_ms / 1000.0)
    if log_at_ms:
        signal_times_s.append(log_at_ms / 1000.0)
    if heartbeat_ms:
        signal_times_s.append(heartbeat_ms / 1000.0)

    idle_age_s = now_s - max(signal_times_s) if signal_times_s else float("inf")
    since_handoff_s = (
        now_s - float(last_handoff_at)
        if isinstance(last_handoff_at, (int, float))
        else float("inf")
    )

    signals = residency.SleepSignals(
        has_active_task=has_active_task,
        has_unread_inbox=has_unread_inbox,
        in_cooldown=False,
        idle_age_s=idle_age_s,
        since_handoff_s=since_handoff_s,
    )
    return residency.sleep_decision(policy, signals)


def _wake_status(agent: str) -> str:
    """Return ``wake_failed`` if there is recent wake-failure evidence,
    otherwise an empty string.

    Wake failures are recorded by ``commands/wake_alert.py`` as auto_ops
    alert logs containing ``wake 失败: <agent>``.
    """
    now_ms_val = now_ms()
    try:
        logs = local_facts.list_logs("auto_ops", limit=50)
    except Exception:
        return ""
    for row in reversed(logs):
        content = str(row.get("content") or "")
        if f"wake 失败" not in content or f"{agent}" not in content:
            continue
        created_at = int(row.get("created_at") or 0)
        if created_at <= 0:
            continue
        if now_ms_val - created_at <= _WAKE_FAILURE_WINDOW_MS:
            return "wake_failed"
    return ""


def _latest_log(agent: str) -> dict:
    """Return the newest log row for ``agent``, or an empty dict."""
    rows = local_facts.list_logs(agent, limit=1)
    return dict(rows[-1]) if rows else {}


def _unread_high_priority_count(agent: str) -> int:
    """Count unread high-priority inbox items for ``agent``."""
    try:
        messages = local_facts.list_messages(agent, unread_only=True)
    except Exception:
        return 0
    return sum(
        1
        for m in messages
        if local_facts.is_high_priority(str(m.get("priority") or ""))
    )


def _current_task(agent: str) -> dict | None:
    """Pick the most relevant current task assigned to ``agent``.

    Prefers non-terminal tasks and, among those, the most recently updated.
    """
    try:
        rows = tasks.list_tasks(assignee=agent)
    except Exception:
        return None
    if not rows:
        return None

    terminal = {"已完成", "已取消", "delivered", "cancelled", "failed"}
    non_terminal = [t for t in rows if str(t.get("status") or "") not in terminal]
    candidates = non_terminal or rows
    candidates.sort(
        key=lambda t: int(t.get("updated_at") or 0) or int(t.get("created_at") or 0),
        reverse=True,
    )
    return candidates[0]


def _workflow_gate(task: dict | None) -> dict:
    """Return workflow gate info for a task, or empty defaults."""
    if not task:
        return {
            "workflow_id": "",
            "gate": "",
            "gate_status": "",
            "next_action": "",
        }
    gate = tasks.workflow_gate_status(task)
    return {
        "workflow_id": gate.get("workflow_id", ""),
        "gate": gate.get("gate", ""),
        "gate_status": gate.get("gate_status", ""),
        "next_action": gate.get("next_action", ""),
    }


def _residency_info(agent: str, *, has_active_task: bool,
                    has_unread_inbox: bool) -> dict:
    """Collect residency fields for the snapshot."""
    policy = _residency_policy(agent)
    row = _residency_row(agent)
    return {
        "label": residency.display_label(policy.mode),
        "mode": policy.mode,
        "policy_source": policy.source,
        "last_active_at": row.get("last_active_at"),
        "last_handoff_at": row.get("last_handoff_at"),
        "last_sleep_at": row.get("last_sleep_at"),
        "last_wake_at": row.get("last_wake_at"),
        "sleep_decision": _sleep_decision(
            agent, policy, row,
            has_active_task=has_active_task,
            has_unread_inbox=has_unread_inbox,
        ),
        "wake_status": _wake_status(agent),
    }


def classify_display_verdict(snapshot: dict) -> str:
    """Classify an employee snapshot into a top-level display verdict.

    Allowed first-version verdicts:
      active, stale_display, waiting_inbox, blocked, idle, stopped, unknown.
    """
    status = str(snapshot.get("declared_status") or "")
    blocker = str(snapshot.get("blocker") or "")
    task_status = str(snapshot.get("current_task_status") or "")
    unread_high = int(snapshot.get("unread_high_priority_count") or 0)
    heartbeat_age_ms = int(snapshot.get("heartbeat_age_ms") or 0)
    heartbeat_ms = int(snapshot.get("heartbeat_ms") or 0)

    status_age_ms = 0
    status_updated_at_ms = int(snapshot.get("status_updated_at_ms") or 0)
    if status_updated_at_ms:
        status_age_ms = now_ms() - status_updated_at_ms

    log_age_ms = 0
    log_at_ms = int(snapshot.get("latest_log_at_ms") or 0)
    if log_at_ms:
        log_age_ms = now_ms() - log_at_ms

    heartbeat_fresh = heartbeat_ms > 0 and heartbeat_age_ms <= HEARTBEAT_FRESH_MS
    status_fresh = status_updated_at_ms > 0 and status_age_ms <= STATUS_STALE_MS
    log_fresh = log_at_ms > 0 and log_age_ms <= LOG_FRESH_MS

    if status == _STOPPED_STATUS:
        return "stopped"

    if unread_high > 0:
        return "waiting_inbox"

    if blocker or status in _BLOCKED_STATUSES or task_status == "blocked":
        return "blocked"

    if heartbeat_fresh and (not status_fresh or (log_at_ms > 0 and not log_fresh)):
        return "stale_display"

    if heartbeat_fresh and status_fresh and log_fresh:
        if status in _IN_PROGRESS_STATUSES or task_status == "in_progress":
            return "active"

    if status in _IDLE_STATUSES and unread_high == 0:
        return "idle"

    return "unknown"


def _staleness_reason(snapshot: dict) -> str:
    """Human-readable explanation of why a snapshot is considered stale."""
    reasons: list[str] = []
    heartbeat_ms = int(snapshot.get("heartbeat_ms") or 0)
    heartbeat_age_ms = int(snapshot.get("heartbeat_age_ms") or 0)

    if heartbeat_ms == 0:
        reasons.append("no heartbeat")
    elif heartbeat_age_ms > HEARTBEAT_FRESH_MS:
        reasons.append("heartbeat stale")

    status_updated_at_ms = int(snapshot.get("status_updated_at_ms") or 0)
    if status_updated_at_ms:
        if now_ms() - status_updated_at_ms > STATUS_STALE_MS:
            reasons.append("status stale")
    else:
        reasons.append("no status timestamp")

    log_at_ms = int(snapshot.get("latest_log_at_ms") or 0)
    if log_at_ms:
        if now_ms() - log_at_ms > LOG_FRESH_MS:
            reasons.append("log stale")
    else:
        reasons.append("no log")

    return "; ".join(reasons) if reasons else ""


def summarize_next_action(snapshot: dict) -> str:
    """Return a concise recommended next action for an employee snapshot."""
    verdict = str(snapshot.get("display_verdict") or "")
    blocker = str(snapshot.get("blocker") or "")
    unread_high = int(snapshot.get("unread_high_priority_count") or 0)
    workflow_next = str(snapshot.get("workflow_next_action") or "")
    task_title = str(snapshot.get("current_task_title") or "")

    if verdict == "stopped":
        return "Agent stopped; restart or re-hire."
    if verdict == "waiting_inbox":
        return f"Consume {unread_high} high-priority unread message(s)."
    if verdict == "blocked":
        if blocker:
            return f"Resolve blocker: {blocker}"
        return "Resolve task block."
    if verdict == "stale_display":
        return "Refresh status/heartbeat/log surface."
    if verdict == "active":
        if workflow_next:
            return workflow_next
        if task_title:
            return f"Continue: {task_title}"
        return "Continue current task."
    if verdict == "idle":
        return "Awaiting next assignment."
    return "Investigate missing or stale signals."


def build_employee_snapshot(agent: str) -> dict:
    """Build a read-only snapshot for ``agent``.

    The snapshot folds together status projection, heartbeat, latest log,
    inbox, current task/workflow gate, and residency state.
    """
    status_row = local_facts.get_status(agent) or {}
    raw_status = local_facts.get_raw_status(agent) or {}

    heartbeat_ms = local_facts.get_heartbeat(agent) or 0
    current_now = now_ms()
    heartbeat_age_ms = current_now - heartbeat_ms if heartbeat_ms else current_now

    latest_log = _latest_log(agent)
    unread_high = _unread_high_priority_count(agent)
    current_task = _current_task(agent)
    gate = _workflow_gate(current_task)

    has_active_task = str((current_task or {}).get("status") or "") == "in_progress"
    residency_info = _residency_info(
        agent,
        has_active_task=has_active_task,
        has_unread_inbox=unread_high > 0,
    )

    snapshot = {
        "agent": agent,
        "declared_status": str(status_row.get("status") or ""),
        "declared_task": str(status_row.get("task") or ""),
        "blocker": str(status_row.get("blocker") or ""),
        "status_updated_at_ms": int(status_row.get("updated_at") or 0),
        "heartbeat_ms": heartbeat_ms,
        "heartbeat_age_ms": heartbeat_age_ms,
        "latest_log_type": str(latest_log.get("type") or ""),
        "latest_log_content": str(latest_log.get("content") or ""),
        "latest_log_at_ms": int(latest_log.get("created_at") or 0),
        "unread_high_priority_count": unread_high,
        "current_task_id": str((current_task or {}).get("id") or ""),
        "current_task_title": str((current_task or {}).get("title") or ""),
        "current_task_status": str((current_task or {}).get("status") or ""),
        "workflow_id": gate["workflow_id"],
        "workflow_gate": gate["gate"],
        "workflow_gate_status": gate["gate_status"],
        "workflow_next_action": gate["next_action"],
        "residency_label": residency_info["label"],
        "policy_mode": residency_info["mode"],
        "residency_policy_source": residency_info["policy_source"],
        "last_active_at": residency_info["last_active_at"],
        "last_handoff_at": residency_info["last_handoff_at"],
        "last_sleep_at": residency_info["last_sleep_at"],
        "last_wake_at": residency_info["last_wake_at"],
        "sleep_decision": residency_info["sleep_decision"],
        "wake_status": residency_info["wake_status"],
        # Placeholders filled below.
        "display_verdict": "",
        "staleness_reason": "",
        "recommended_next_action": "",
    }

    snapshot["display_verdict"] = classify_display_verdict(snapshot)
    snapshot["staleness_reason"] = _staleness_reason(snapshot)
    snapshot["recommended_next_action"] = summarize_next_action(snapshot)

    # Surface the raw declared status too, so consumers can tell whether
    # the status was projected from inbox/logs vs. explicitly set.
    snapshot["raw_status"] = str(raw_status.get("status") or "")
    snapshot["raw_task"] = str(raw_status.get("task") or "")

    return snapshot


def build_team_snapshot() -> list[dict]:
    """Build snapshots for every agent that has a status row or heartbeat."""
    agents: set[str] = set()
    try:
        for row in local_facts.list_all_statuses():
            agents.add(str(row.get("agent") or ""))
    except Exception:
        pass
    try:
        for agent in local_facts.all_heartbeats():
            agents.add(str(agent))
    except Exception:
        pass
    agents.discard("")
    return [build_employee_snapshot(a) for a in sorted(agents)]
