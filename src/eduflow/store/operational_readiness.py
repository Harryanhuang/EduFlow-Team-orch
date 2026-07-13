"""Read-only Operational Readiness check for one task.

Package 5 of the 2026-07-06 production-contract pilot. Combines T-118
runtime lessons into a single readiness verdict across three dimensions:
delivery / productivity / source.

**Strictly read-only.** NEVER auto-fixes, sends messages, archives tasks,
or touches runtime. Returns structured pass / warn / fail verdicts.

Threshold constants are exposed at module top so they can be tuned in
one place without touching call-sites.
"""
from __future__ import annotations

from typing import Any

from eduflow.store import local_facts, tasks


# ── thresholds ────────────────────────────────────────────────────

# Delivery: how long after `created_at` we still treat an ack as "fresh"
# for pass-status. 5 minutes matches the manager cadence.
DELIVERY_FRESH_MS = 5 * 60 * 1000

# Productivity: heartbeat window before we say "stale"
HEARTBEAT_FRESH_MS = 5 * 60 * 1000

# Productivity: log recency for "active progress"
PROGRESS_FRESH_MS = 30 * 60 * 1000

# Delivery failure patterns (the manager-panel / publish-gate taxonomy)
_DELIVERY_FAILURE_STATES = frozenset({
    "blocked",
    "inject_failed",
    "requires_polling",
    "delivery_blocked",
})


# ── delivery ──────────────────────────────────────────────────────


def _classify_delivery(task: dict) -> dict[str, str]:
    """Inspect inbox rows for `task_id` and classify the delivery dimension."""
    handoff: dict | None = None
    for msg in local_facts.list_all_messages():
        if str(msg.get("task_id") or "") != str(task.get("id") or ""):
            continue
        if local_facts.is_reconciliation_managed(msg):
            continue
        # Pick the most recent handoff (by created_at)
        if handoff is None or int(msg.get("created_at") or 0) > int(handoff.get("created_at") or 0):
            handoff = msg
    if handoff is None:
        return {"status": "pass", "reason": "no handoff message required"}
    priority = str(handoff.get("priority") or "")
    ack_state = str(handoff.get("ack_state") or "pending")
    delivery_state = str(handoff.get("delivery_state") or "delivered_to_inbox")
    is_high_priority = priority in {"高", "high", "urgent", "p0", "p1"}
    # Fail: explicit failure state, regardless of priority
    if delivery_state in _DELIVERY_FAILURE_STATES:
        return {
            "status": "fail",
            "reason": f"delivery_state={delivery_state} blocks handoff",
        }
    # High-priority handoff without ack
    if is_high_priority and ack_state == "pending":
        return {
            "status": "warn",
            "reason": "high-priority handoff delivered but ack pending",
        }
    # High-priority handoff with ack
    if is_high_priority and ack_state != "pending":
        return {
            "status": "pass",
            "reason": f"high-priority handoff ack_state={ack_state}",
        }
    # Normal-priority handoff, still pending
    if ack_state == "pending":
        return {
            "status": "warn",
            "reason": "handoff delivered but ack pending",
        }
    return {
        "status": "pass",
        "reason": f"handoff ack_state={ack_state}",
    }


# ── productivity ──────────────────────────────────────────────────


def _classify_productivity(task: dict) -> dict[str, str]:
    """Check assignee heartbeat + recent progress signal."""
    assignee = str(task.get("owner") or task.get("assignee") or "").strip()
    if not assignee:
        return {"status": "warn", "reason": "no assignee / owner to track"}
    heartbeat_ms = local_facts.get_heartbeat(assignee)
    if heartbeat_ms is None or heartbeat_ms <= 0:
        # Without an inbox handoff for this task, missing heartbeat is
        # not a fail signal: the worker may be idle, waiting for dispatch.
        return {"status": "warn", "reason": f"no heartbeat for {assignee}"}
    # Use shared now_ms clock
    from eduflow.util import now_ms
    now = now_ms()
    age_ms = now - heartbeat_ms
    if age_ms > HEARTBEAT_FRESH_MS:
        return {
            "status": "fail",
            "reason": f"heartbeat stale for {assignee} ({age_ms}ms)",
        }
    # Heartbeat fresh — check progress signal
    logs = local_facts.list_logs(assignee, limit=10)
    has_recent_progress = False
    for entry in logs:
        created_at = int(entry.get("created_at") or 0)
        if created_at > 0 and (now - created_at) <= PROGRESS_FRESH_MS:
            has_recent_progress = True
            break
    if has_recent_progress:
        return {
            "status": "pass",
            "reason": f"heartbeat fresh + recent log for {assignee}",
        }
    return {
        "status": "warn",
        "reason": f"heartbeat fresh but no recent log for {assignee}",
    }


# ── source ────────────────────────────────────────────────────────


def _has_evidence(task: dict) -> bool:
    evidence = task.get("evidence_packet") or {}
    if isinstance(evidence, dict):
        # any non-empty key counts
        if any(evidence.values()):
            return True
    verdict = task.get("latest_authoritative_verdict") or {}
    if isinstance(verdict, dict):
        if any(verdict.values()):
            return True
    # scope_files / blocking_files signal "files reviewed"
    scope_files = task.get("scope_files") or []
    if isinstance(scope_files, list) and scope_files:
        return True
    blocking = task.get("blocking_files") or []
    if isinstance(blocking, list) and blocking:
        return True
    return False


def _classify_source(task: dict) -> dict[str, str]:
    """Source / evidence / manifest health for the task."""
    if _has_evidence(task):
        return {"status": "pass", "reason": "evidence_packet / verdict present"}
    stage = str(task.get("stage") or "").strip().lower()
    # Curriculum and qbank tasks without evidence are warn (pilot scope)
    if stage in {"curriculum", "qbank"}:
        return {
            "status": "warn",
            "reason": f"{stage} task without source / evidence",
        }
    # Other stages: warn unless there's an explicit missing-source marker
    review_reason = str(task.get("review_reason") or "").strip()
    if "missing" in review_reason.lower() and "source" in review_reason.lower():
        return {"status": "fail", "reason": f"review flagged missing source: {review_reason}"}
    return {"status": "warn", "reason": "no source / evidence on task"}


# ── overall ───────────────────────────────────────────────────────


_STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2}


def _overall(*statuses: str) -> str:
    if not statuses:
        return "pass"
    worst = max(statuses, key=lambda s: _STATUS_ORDER.get(s, 0))
    return worst


# ── public API ────────────────────────────────────────────────────


def diagnostics(task_id: str) -> dict[str, Any] | None:
    """Return raw signal values behind the readiness verdict.

    Use this to tune thresholds after collecting real-world samples.
    Strictly read-only.
    """
    if not task_id:
        return None
    task = tasks.get(task_id)
    if task is None:
        return None
    from eduflow.util import now_ms
    now = now_ms()

    # Delivery raw signals
    handoff_count = 0
    latest_handoff: dict | None = None
    for msg in local_facts.list_all_messages():
        if str(msg.get("task_id") or "") != str(task.get("id") or ""):
            continue
        handoff_count += 1
        if latest_handoff is None or int(msg.get("created_at") or 0) > int(latest_handoff.get("created_at") or 0):
            latest_handoff = msg
    delivery_signals = {
        "handoff_count": handoff_count,
        "latest_handoff_priority": str(latest_handoff.get("priority") or "") if latest_handoff else "",
        "latest_handoff_ack_state": str(latest_handoff.get("ack_state") or "") if latest_handoff else "",
        "latest_handoff_delivery_state": str(latest_handoff.get("delivery_state") or "") if latest_handoff else "",
        "latest_handoff_age_ms": (now - int(latest_handoff.get("created_at") or now)) if latest_handoff else None,
    }

    # Productivity raw signals
    assignee = str(task.get("owner") or task.get("assignee") or "").strip()
    heartbeat_ms = local_facts.get_heartbeat(assignee)
    logs = local_facts.list_logs(assignee, limit=10) if assignee else []
    most_recent_log_age_ms = None
    for entry in logs:
        created_at = int(entry.get("created_at") or 0)
        if created_at > 0:
            age = now - created_at
            if most_recent_log_age_ms is None or age < most_recent_log_age_ms:
                most_recent_log_age_ms = age
    productivity_signals = {
        "assignee": assignee,
        "heartbeat_age_ms": (now - heartbeat_ms) if heartbeat_ms else None,
        "heartbeat_present": heartbeat_ms is not None and heartbeat_ms > 0,
        "recent_log_count": len(logs),
        "most_recent_log_age_ms": most_recent_log_age_ms,
    }

    # Source raw signals
    evidence = task.get("evidence_packet") or {}
    verdict = task.get("latest_authoritative_verdict") or {}
    source_signals = {
        "stage": str(task.get("stage") or ""),
        "has_evidence_packet": bool(isinstance(evidence, dict) and any(evidence.values())),
        "has_authoritative_verdict": bool(isinstance(verdict, dict) and any(verdict.values())),
        "scope_files_count": len(task.get("scope_files") or []),
        "blocking_files_count": len(task.get("blocking_files") or []),
        "review_reason": str(task.get("review_reason") or ""),
    }

    return {
        "task_id": task_id,
        "thresholds": {
            "HEARTBEAT_FRESH_MS": HEARTBEAT_FRESH_MS,
            "PROGRESS_FRESH_MS": PROGRESS_FRESH_MS,
            "DELIVERY_FRESH_MS": DELIVERY_FRESH_MS,
        },
        "delivery_signals": delivery_signals,
        "productivity_signals": productivity_signals,
        "source_signals": source_signals,
    }


def build(task_id: str) -> dict[str, Any] | None:
    """Render the Operational Readiness verdict for `task_id`.

    Strictly read-only. Returns `None` for unknown tasks.
    """
    if not task_id:
        return None
    task = tasks.get(task_id)
    if task is None:
        return None
    delivery = _classify_delivery(task)
    productivity = _classify_productivity(task)
    source = _classify_source(task)
    return {
        "task_id": task_id,
        "delivery": delivery,
        "productivity": productivity,
        "source": source,
        "overall": _overall(delivery["status"], productivity["status"], source["status"]),
    }
