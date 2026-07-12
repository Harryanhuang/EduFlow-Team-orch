"""D scheduler <-> memory bridge.

Wraps every memory write call in try/except so a memory subsystem
outage NEVER breaks the scheduler.  Callers (engine / manager_ops)
invoke the typed record_* helpers; this module catches exceptions and
returns False so the scheduler keeps moving.

Decision-grade kinds exposed:
  * record_rule_summary     — when a rule is created / confirmed
  * record_workflow_start   — when manager dispatches (status -> running)
  * record_workflow_stop    — when an occurrence ends (done/skipped/cancelled)
  * record_major_failure    — when fail_pause_occurrence fires
  * record_user_preference  — explicit user preference for a rule

Routine tick / reminder / wait events MUST NOT call into here.
"""
from __future__ import annotations

from typing import Any


def _resolve_writer():
    """Re-resolve the underlying D scheduler summary writer.

    The writer function is looked up at call time so tests can
    monkeypatch ``eduflow.memory.capsules.write_d_scheduler_summary``
    and observe the failure path through this bridge.
    """
    from eduflow.memory.capsules import write_d_scheduler_summary
    return write_d_scheduler_summary


def _safe_write(
    *,
    rule_id: str,
    summary_kind: str,
    content: str,
    occurrence_key: str = "",
    evidence_refs: list[str] | None = None,
    importance: int = 6,
    metadata: dict | None = None,
) -> bool:
    """Invoke the D scheduler summary writer with full exception guard.

    Returns True on success, False on any failure (including validation
    errors at runtime — though those should be programming bugs).
    """
    if not rule_id:
        return False
    if not content:
        return False
    writer = _resolve_writer()
    try:
        mid = writer(
            rule_id=rule_id,
            summary_kind=summary_kind,
            content=content,
            occurrence_key=occurrence_key,
            evidence_refs=evidence_refs,
            importance=importance,
            metadata=metadata,
        )
        return bool(mid)
    except Exception:
        return False


def record_rule_summary(
    rule_id: str,
    content: str,
    *,
    importance: int = 6,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist a rule summary (created / confirmed / paused / resumed / cancelled)."""
    return _safe_write(
        rule_id=rule_id,
        summary_kind="rule_summary",
        content=content,
        importance=importance,
        metadata=metadata,
    )


def record_workflow_start(
    rule_id: str,
    occurrence_key: str,
    content: str,
    *,
    importance: int = 7,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist a workflow-start summary when manager dispatches."""
    return _safe_write(
        rule_id=rule_id,
        summary_kind="workflow_start",
        content=content,
        occurrence_key=occurrence_key,
        importance=importance,
        metadata=metadata,
    )


def record_workflow_stop(
    rule_id: str,
    occurrence_key: str,
    content: str,
    *,
    importance: int = 6,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist a workflow-stop summary (done / skipped / cancelled)."""
    return _safe_write(
        rule_id=rule_id,
        summary_kind="workflow_stop",
        content=content,
        occurrence_key=occurrence_key,
        importance=importance,
        metadata=metadata,
    )


def record_major_failure(
    rule_id: str,
    occurrence_key: str,
    content: str,
    *,
    importance: int = 8,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist a major-failure summary when fail_pause_occurrence fires."""
    return _safe_write(
        rule_id=rule_id,
        summary_kind="major_failure",
        content=content,
        occurrence_key=occurrence_key,
        importance=importance,
        metadata=metadata,
    )


def record_user_preference(
    rule_id: str,
    content: str,
    *,
    importance: int = 7,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Persist an explicit user preference attached to a rule."""
    return _safe_write(
        rule_id=rule_id,
        summary_kind="user_preference",
        content=content,
        importance=importance,
        metadata=metadata,
    )