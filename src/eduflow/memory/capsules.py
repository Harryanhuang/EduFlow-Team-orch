"""Task Capsules CRUD and refresh from tasks.json.

A Task Capsule is a compact snapshot of a flow task's essential context,
stored in SQLite so it can be injected into Memory Packets after context loss.

P7 also adds decision-grade D scheduler summary helpers.  D scheduler
writes ONLY:
  * rule_summary      — draft / confirmed rule essence
  * workflow_start    — manager dispatched (status -> running)
  * workflow_stop     — done / skipped / cancelled / failed
  * major_failure     — fail_pause_occurrence
  * user_preference   — explicit user preference attached to a rule

Routine tick / reminder / wait events NEVER call this module.  Memory
subsystem failure is caught at the call site — write_d_scheduler_summary
never raises so the scheduler cannot break because of a memory outage.

D summaries live in the ``memory_items`` table with scope
``scheduler:rule:<D-id>`` and ``kind="decision"`` — strictly separate
from the T task_capsules table so T memory behaviour is unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from eduflow.memory.db import get_conn, init_schema


# Decision-grade kinds D scheduler may write.  Anything else is rejected.
D_SCHEDULER_ALLOWED_KINDS = frozenset({
    "rule_summary",
    "workflow_start",
    "workflow_stop",
    "major_failure",
    "user_preference",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_capsule(
    task_id: str,
    *,
    workflow_id: str = "",
    owner: str = "",
    gate: str = "",
    goal: str = "",
    acceptance: str = "",
    current_status: str = "",
    decisions: list[str] | None = None,
    blockers: list[str] | None = None,
    next_action: str = "",
    last_evidence_ref: str = "",
) -> None:
    """Insert or update a task capsule."""
    init_schema()
    now = _now_iso()
    conn = get_conn()
    conn.execute(
        """INSERT INTO task_capsules
           (task_id, workflow_id, owner, gate, goal, acceptance,
            current_status, decisions, blockers, next_action,
            last_evidence_ref, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(task_id) DO UPDATE SET
             workflow_id = excluded.workflow_id,
             owner = excluded.owner,
             gate = excluded.gate,
             goal = excluded.goal,
             acceptance = excluded.acceptance,
             current_status = excluded.current_status,
             decisions = excluded.decisions,
             blockers = excluded.blockers,
             next_action = excluded.next_action,
             last_evidence_ref = excluded.last_evidence_ref,
             updated_at = excluded.updated_at""",
        (
            task_id, workflow_id, owner, gate, goal, acceptance,
            current_status,
            json.dumps(decisions or []),
            json.dumps(blockers or []),
            next_action, last_evidence_ref, now,
        ),
    )
    conn.commit()


def get_capsule(task_id: str) -> dict | None:
    """Fetch a single task capsule by task_id."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM task_capsules WHERE task_id = ?", (task_id,)
    ).fetchone()
    return dict(row) if row else None


def refresh_from_task_store(task_id: str) -> dict | None:
    """Read a task from tasks.json and rebuild its capsule.

    Returns the capsule dict, or None if task not found / not a flow task.
    """
    try:
        from eduflow.store import tasks as _tasks
    except ImportError:
        return None

    # Read task directly via the store's public API
    try:
        task = _tasks.get(task_id)
    except Exception:
        return None
    if task is None:
        return None
    if task.get("schema_version") != 2:
        return None

    # Build capsule fields from task state
    verdict = task.get("verdict") or ""
    closeout = task.get("closeout_status") or ""
    revision = task.get("revision_priority") or ""

    # Determine gate
    gate = ""
    if closeout:
        gate = f"closeout:{closeout}"
    elif verdict == "pending":
        gate = "review_pending"
    elif verdict in ("approved", "rejected"):
        gate = f"verdict:{verdict}"

    # Build blockers from task state
    blockers: list[str] = []
    if revision:
        blockers.append(f"revision_priority={revision}")
    if closeout and closeout not in ("", "closeout_completed"):
        blockers.append(f"closeout_status={closeout}")
    loop_status = str(task.get("loop_status") or "")
    if loop_status and loop_status not in {"passed"}:
        blockers.append(f"loop_status={loop_status}")

    # Determine next action
    status = task.get("status") or ""
    next_action = ""
    if status == "submitted_for_review":
        next_action = "awaiting_review"
    elif status == "in_progress":
        next_action = "continue_work"
    elif status == "delivered":
        next_action = "pending_closeout"
    elif revision:
        next_action = "address_revision"
    if task.get("loop_recommended_action"):
        next_action = str(task.get("loop_recommended_action") or "")

    # Build goal from title + scope
    title = task.get("title") or ""
    scope_topic = task.get("scope_topic") or ""
    goal = title
    if scope_topic:
        goal = f"{title} ({scope_topic})"

    # Build acceptance from required_fix + blocking_files
    required_fix = task.get("required_fix") or []
    acceptance_parts: list[str] = []
    if required_fix:
        acceptance_parts.extend(required_fix)
    acceptance = "; ".join(acceptance_parts)

    # Evidence ref
    evidence = task.get("evidence_packet") or {}
    last_evidence = ""
    if task.get("loop_evidence_ref"):
        last_evidence = str(task.get("loop_evidence_ref") or "")
    elif evidence:
        last_evidence = f"evidence_snapshot:{task.get('evidence_snapshot_hash', '')}"

    upsert_capsule(
        task_id,
        workflow_id=task.get("workflow_id") or "",
        owner=task.get("owner") or task.get("assignee") or "",
        gate=gate,
        goal=goal,
        acceptance=acceptance,
        current_status=status,
        decisions=[],
        blockers=blockers,
        next_action=next_action,
        last_evidence_ref=last_evidence,
    )
    return get_capsule(task_id)


# ── D scheduler decision-grade summaries (P7) ────────────────────────
#
# D scheduler writes ONLY decision-grade summaries to memory.  Routine
# tick / reminder / wait events MUST NOT call into here.
#
# These records live in memory_items with scope "scheduler:rule:<D-id>"
# and kind="decision".  A "summary_kind" discriminator inside
# metadata_json separates them from regular T decision records.  This
# keeps the T task_capsules table and T memory packet assembly
# untouched.
#
# write_d_scheduler_summary is intentionally try/except-safe: if the
# memory subsystem raises, it returns "" instead of propagating, so the
# scheduler cannot break because of a memory outage.


def _d_scheduler_scope(rule_id: str) -> str:
    return f"scheduler:rule:{rule_id}"


def _d_scheduler_next_id() -> str:
    """Allocate a stable ID for a D scheduler summary record.

    Uses the memory_items id format so D summaries and regular memory
    items share a single namespace but are distinguishable by scope
    and metadata.summary_kind.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    date_part = now[:10].replace("-", "")
    prefix = f"MI-{date_part}-"
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(id, ?) AS INTEGER)) FROM memory_items WHERE id LIKE ?",
        (len(prefix) + 1, f"{prefix}%"),
    ).fetchone()
    seq = (row[0] or 0) + 1
    return f"{prefix}{seq:03d}"


def validate_d_scheduler_kind(kind: str) -> str:
    """Raise ValueError unless `kind` is one of the five decision-grade kinds."""
    if kind not in D_SCHEDULER_ALLOWED_KINDS:
        raise ValueError(
            f"D scheduler summary_kind {kind!r} not in decision-grade set "
            f"(allowed: {sorted(D_SCHEDULER_ALLOWED_KINDS)})"
        )
    return kind


def write_d_scheduler_summary(
    rule_id: str,
    summary_kind: str,
    content: str,
    *,
    occurrence_key: str = "",
    evidence_refs: list[str] | None = None,
    importance: int = 6,
    metadata: dict | None = None,
) -> str:
    """Persist a decision-grade D scheduler summary.

    Returns the memory_id on success, or "" on any failure.  This
    function is try/except-safe by contract — callers (engine /
    manager_ops) MUST NOT need to wrap it in another try/except.
    """
    try:
        validate_d_scheduler_kind(summary_kind)
    except ValueError:
        # Re-raise validation errors: those are programming bugs, not
        # memory outages, and the scheduler should still see them.
        raise

    if not str(rule_id or "").strip():
        raise ValueError("rule_id is required for D scheduler summary")
    if not str(content or "").strip():
        raise ValueError("content is required for D scheduler summary")

    try:
        init_schema()
        now = _now_iso()
        mid = _d_scheduler_next_id()
        conn = get_conn()
        meta = dict(metadata or {})
        meta.setdefault("summary_kind", summary_kind)
        meta.setdefault("scheduler", "d")
        if occurrence_key:
            meta.setdefault("occurrence_key", occurrence_key)
        if evidence_refs:
            meta.setdefault("evidence_refs", list(evidence_refs))
        meta.setdefault("rule_id", rule_id)
        conn.execute(
            """INSERT INTO memory_items
               (id, layer, scope, kind, status, content, summary, source_ref,
                evidence_refs, confidence, importance, valid_from, valid_until,
                created_by, created_at, updated_at, supersedes, revision_of,
                metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mid,
                "task",  # distinct from T which is also 'task' but in different table
                _d_scheduler_scope(rule_id),
                "decision",
                "confirmed",
                str(content).strip(),
                "",  # summary: empty, content is already compact
                f"scheduler:rule:{rule_id}",
                json.dumps(list(evidence_refs or []) + (
                    [occurrence_key] if occurrence_key else []
                )),
                1.0,
                max(1, min(10, int(importance))),
                now,  # valid_from
                "",   # valid_until
                "scheduler",
                now,  # created_at
                now,  # updated_at
                "",   # supersedes
                "",   # revision_of
                json.dumps(meta, ensure_ascii=False),
            ),
        )
        conn.commit()
        return mid
    except Exception:
        # Memory subsystem failure — never propagate; scheduler must keep going.
        return ""


def get_d_scheduler_summaries(
    rule_id: str | None = None,
    *,
    summary_kind: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch decision-grade D scheduler summary records.

    Filters by rule_id and/or summary_kind when provided.  Only records
    whose metadata_json carries a "summary_kind" discriminator are
    returned — even if a non-decision-grade memory somehow ended up
    under the scheduler scope.
    """
    try:
        init_schema()
        conn = get_conn()
        params: list = []
        clauses = ["scope LIKE ?"]
        params.append("scheduler:rule:%")
        if rule_id is not None:
            clauses = ["scope = ?"]
            params = [_d_scheduler_scope(rule_id)]
        where = " AND ".join(clauses)
        query = (
            f"SELECT * FROM memory_items WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ?"
        )
        params.append(int(limit))
        rows = conn.execute(query, params).fetchall()
        out: list[dict] = []
        for row in rows:
            d = dict(row)
            meta_raw = d.get("metadata_json") or "{}"
            try:
                meta = json.loads(meta_raw) if isinstance(meta_raw, str) else dict(meta_raw or {})
            except Exception:
                meta = {}
            sk = meta.get("summary_kind") if isinstance(meta, dict) else None
            if not sk:
                continue  # not a D summary, skip
            if summary_kind is not None and sk != summary_kind:
                continue
            d["metadata_json"] = json.dumps(meta, ensure_ascii=False)
            out.append(d)
        return out
    except Exception:
        return []


def list_d_scheduler_kinds() -> frozenset:
    """Expose the allowed D scheduler summary kinds."""
    return D_SCHEDULER_ALLOWED_KINDS
