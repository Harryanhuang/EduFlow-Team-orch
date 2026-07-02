"""Agent→Lane Bindings — durable agent-to-lane assignment with scope inheritance.

Agents inherit memories from all lanes they are bound to.  The
``resolve_scope`` helper expands an agent name into its full scope
list so packet assembly and search automatically pick up lane memories.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from eduflow.memory.db import get_conn, init_schema

_MAX_SCOPES = 20
_log = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def bind_agent(
    agent: str,
    lane_id: str,
    *,
    role: str = "",
    valid_from: str | None = None,
) -> None:
    """Create or re-activate a binding.  If the row already exists and is
    inactive, it is reactivated (active=1).  If already active, role and
    valid_from are updated."""
    if not agent.strip():
        raise ValueError("agent cannot be empty")
    if not lane_id.strip():
        raise ValueError("lane_id cannot be empty")
    init_schema()
    now = _now_iso()
    vf = valid_from or now
    conn = get_conn()
    conn.execute(
        """INSERT INTO agent_lane_bindings
               (agent, lane_id, role, active, valid_from, valid_until, created_at, updated_at)
           VALUES (?, ?, ?, 1, ?, '', ?, ?)
           ON CONFLICT(agent, lane_id) DO UPDATE SET
               role=excluded.role,
               active=1,
               valid_from=excluded.valid_from,
               valid_until='',
               updated_at=excluded.updated_at""",
        (agent.strip(), lane_id.strip(), role.strip(), vf, now, now),
    )
    conn.commit()


def unbind_agent(agent: str, lane_id: str, *, valid_until: str | None = None) -> bool:
    """Deactivate a binding (active=0).  Returns True if found and changed."""
    if not agent.strip() or not lane_id.strip():
        return False
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT active FROM agent_lane_bindings WHERE agent = ? AND lane_id = ?",
        (agent.strip(), lane_id.strip()),
    ).fetchone()
    if row is None:
        return False
    if row["active"] == 0:
        return False
    now = _now_iso()
    until = valid_until or now
    conn.execute(
        "UPDATE agent_lane_bindings SET active = 0, valid_until = ?, updated_at = ? "
        "WHERE agent = ? AND lane_id = ?",
        (until, now, agent.strip(), lane_id.strip()),
    )
    conn.commit()
    return True


def get_agent_lanes(agent: str) -> list[dict]:
    """Return all active lane bindings for *agent*."""
    init_schema()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM agent_lane_bindings WHERE agent = ? AND active = 1 "
        "ORDER BY lane_id",
        (agent.strip(),),
    ).fetchall()
    return [dict(r) for r in rows]


def get_lane_agents(lane_id: str) -> list[dict]:
    """Return all active agents bound to *lane_id*."""
    init_schema()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM agent_lane_bindings WHERE lane_id = ? AND active = 1 "
        "ORDER BY agent",
        (lane_id.strip(),),
    ).fetchall()
    return [dict(r) for r in rows]


def resolve_scope(agent: str) -> list[str]:
    """Expand an agent name into the full scope list for OR-matching.

    Returns ``["agent:<name>", "team", "lane:<lane1>", ...]``.
    "team" is always included so constraints at the team level are
    matched automatically.  If the agent has no active bindings,
    returns ``["agent:<name>", "team"]`` only.

    Result is capped at ``_MAX_SCOPES`` entries.  Falls back to
    ``["agent:<name>", "team"]`` when the bindings table is missing
    (e.g. pre-migration database).
    """
    if not agent:
        return []
    try:
        init_schema()
    except Exception:
        return [f"agent:{agent}", "team"]
    scopes = [f"agent:{agent}", "team"]
    lanes = get_agent_lanes(agent)
    for b in lanes:
        lane_scope = b["lane_id"]  # lane_id is expected to be "lane:xxx"
        if lane_scope not in scopes:
            scopes.append(lane_scope)
    if len(scopes) > _MAX_SCOPES:
        _log.warning("resolve_scope(%s): capped from %d to %d scopes",
                     agent, len(scopes), _MAX_SCOPES)
        scopes = scopes[:_MAX_SCOPES]
    return scopes
