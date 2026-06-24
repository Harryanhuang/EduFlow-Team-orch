"""Memory Candidates — proposal workflow for new memories.

Candidates are proposed memories that need review before becoming confirmed
memory_items. Supports:
  - add_candidate: create a proposed candidate
  - promote_candidate: convert candidate→confirmed memory_item (with high-impact guard)
  - reject_candidate: mark candidate as rejected

High-impact memory types (workflow_rule, role_rule, runtime_rule, decision,
preference, handoff) require a designated reviewer to promote.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from eduflow.memory.db import get_conn, init_schema
from eduflow.memory import items as _items

_HIGH_IMPACT_KINDS = frozenset({
    "workflow_rule", "role_rule", "runtime_rule",
    "decision", "preference", "handoff",
})
_DESIGNATED_REVIEWERS = frozenset({"manager", "hermes"})
_DEFAULT_EXPIRY_DAYS = 90
_HIGH_IMPACT_EXPIRY_DAYS = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_candidate_id(now: str) -> str:
    date_part = now[:10].replace("-", "")
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) FROM memory_candidates WHERE candidate_id LIKE ?",
        (f"CAND-{date_part}-%",),
    ).fetchone()
    seq = (row[0] or 0) + 1
    return f"CAND-{date_part}-{seq:03d}"


def _default_expires_at(now: str, kind: str = "") -> str:
    dt = datetime.fromisoformat(now)
    days = _HIGH_IMPACT_EXPIRY_DAYS if kind in _HIGH_IMPACT_KINDS else _DEFAULT_EXPIRY_DAYS
    return (dt + timedelta(days=days)).isoformat()


def add_candidate(
    scope: str,
    kind: str,
    content: str,
    *,
    source_type: str = "manual",
    source_ref: str = "",
    layer: str = "episode",
    reason: str = "",
    evidence_refs: list[str] | None = None,
    risk_flags: list[str] | None = None,
    idempotent: bool = True,
) -> str:
    """Add a new memory candidate. Returns candidate_id.

    When ``idempotent`` is True (default) and both ``source_type`` and
    ``source_ref`` are non-empty (and source_type != "manual"), an
    existing ``proposed`` candidate with the same (source_type,
    source_ref) is returned instead of creating a duplicate. Event
    hooks rely on this so the same recurring failure does not flood
    the review queue with redundant entries.
    """
    if not content.strip():
        raise ValueError("content cannot be empty")
    init_schema()
    conn = get_conn()
    # Idempotency: detect duplicate event-driven candidates.
    # Why: hooks may fire repeatedly for the same underlying issue
    # (e.g. a review rejected twice for the same reason). Without
    # dedup the review queue fills with redundant entries that add
    # noise but no new knowledge. We skip this for manual entries
    # (a human deliberately adding the same note twice is rare but
    # legitimate) and when source_ref is empty (no stable key).
    if idempotent and source_type and source_type != "manual" and source_ref:
        existing = conn.execute(
            "SELECT candidate_id FROM memory_candidates "
            "WHERE source_type = ? AND source_ref = ? AND review_status = 'proposed' "
            "LIMIT 1",
            (source_type, source_ref),
        ).fetchone()
        if existing:
            return existing[0]
    now = _now_iso()
    cid = _next_candidate_id(now)
    expires_at = _default_expires_at(now, kind)
    conn.execute(
        """INSERT INTO memory_candidates
           (candidate_id, source_type, source_ref, proposed_layer,
            proposed_scope, proposed_kind, content, reason,
            evidence_refs, risk_flags, created_at, review_status,
            reviewed_by, reviewed_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', '', '', ?)""",
        (
            cid, source_type, source_ref, layer,
            scope, kind, content.strip(), reason,
            json.dumps(evidence_refs or []),
            json.dumps(risk_flags or []),
            now, expires_at,
        ),
    )
    conn.commit()
    return cid


def get_candidate(candidate_id: str) -> dict | None:
    """Fetch a single candidate by ID."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM memory_candidates WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    return dict(row) if row else None


def list_candidates(
    *,
    scope: str | None = None,
    status: str = "proposed",
    source_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List candidates with optional filters. Default status='proposed'."""
    init_schema()
    conn = get_conn()
    query = "SELECT * FROM memory_candidates WHERE 1=1"
    params: list = []
    if status:
        query += " AND review_status = ?"
        params.append(status)
    if scope:
        query += " AND proposed_scope = ?"
        params.append(scope)
    if source_type:
        query += " AND source_type = ?"
        params.append(source_type)
    # Filter out expired candidates
    now = _now_iso()
    query += " AND expires_at > ?"
    params.append(now)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def promote_candidate(candidate_id: str, *, reviewer: str = "") -> str:
    """Promote a candidate to a confirmed memory_item.

    Returns the new memory_item ID.
    Raises ValueError if high-impact kind without authorized reviewer.
    Raises ValueError if candidate not found or not in 'proposed' status.
    """
    init_schema()
    cand = get_candidate(candidate_id)
    if cand is None:
        raise ValueError(f"candidate not found: {candidate_id}")
    if cand["review_status"] != "proposed":
        raise ValueError(f"candidate {candidate_id} is not in 'proposed' status (current: {cand['review_status']})")
    # High-impact guard
    if cand["proposed_kind"] in _HIGH_IMPACT_KINDS:
        if not reviewer or reviewer not in _DESIGNATED_REVIEWERS:
            raise ValueError(
                f"high-impact kind '{cand['proposed_kind']}' requires designated reviewer "
                f"({', '.join(sorted(_DESIGNATED_REVIEWERS))}), got '{reviewer}'"
            )
    now = _now_iso()
    conn = get_conn()
    # Create the memory item as confirmed
    evidence = json.loads(cand["evidence_refs"]) if cand["evidence_refs"] else []
    mid = _items.add_memory(
        scope=cand["proposed_scope"],
        kind=cand["proposed_kind"],
        content=cand["content"],
        layer=cand["proposed_layer"],
        summary="",
        source_ref=cand["source_ref"],
        evidence_refs=evidence,
        confidence=1.0,
        importance=5,
        created_by=reviewer,
        status="confirmed",
    )
    # Update candidate status
    conn.execute(
        "UPDATE memory_candidates SET review_status = 'promoted', reviewed_by = ?, reviewed_at = ? WHERE candidate_id = ?",
        (reviewer, now, candidate_id),
    )
    conn.commit()

    # Sync vector index explicitly (add_memory also does it; this is defensive)
    try:
        from eduflow.memory.vector_store import index_memory
        created = _items.get_memory(mid)
        if created:
            index_memory(
                mid,
                created.get("content", ""),
                {
                    "scope": created.get("scope", ""),
                    "kind": created.get("kind", ""),
                    "layer": created.get("layer", ""),
                    "importance": created.get("importance", 5),
                    "status": created.get("status", "confirmed"),
                    "updated_at": created.get("updated_at", ""),
                },
            )
    except Exception:
        pass

    return mid


def reject_candidate(candidate_id: str, *, reviewer: str = "", reason: str = "") -> bool:
    """Set review_status='rejected'. Returns True if found and changed."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT review_status FROM memory_candidates WHERE candidate_id = ?",
        (candidate_id,),
    ).fetchone()
    if row is None:
        return False
    if row["review_status"] != "proposed":
        return False
    now = _now_iso()
    conn.execute(
        "UPDATE memory_candidates SET review_status = 'rejected', reviewed_by = ?, reviewed_at = ? WHERE candidate_id = ?",
        (reviewer, now, candidate_id),
    )
    conn.commit()
    return True


def expire_stale_candidates() -> int:
    """Mark expired candidates (expires_at in the past) as rejected.

    Returns the count of candidates transitioned. Only ``proposed``
    candidates past their ``expires_at`` are affected; already-reviewed
    entries are left alone so audit history is preserved.

    Why reject rather than DELETE: the row still carries useful signal
    (what was proposed, why it expired) and we may want to inspect it
    later. A rejected status with an empty reviewed_by is the convention
    for "system-expired".
    """
    init_schema()
    conn = get_conn()
    now = _now_iso()
    try:
        cursor = conn.execute(
            "UPDATE memory_candidates "
            "SET review_status = 'rejected', reviewed_by = 'system', reviewed_at = ? "
            "WHERE review_status = 'proposed' AND expires_at <= ?",
            (now, now),
        )
        conn.commit()
        return cursor.rowcount
    except Exception:
        # Best-effort cleanup: never crash the caller for housekeeping.
        return 0
