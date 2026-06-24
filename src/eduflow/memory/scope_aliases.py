"""Memory Scope Aliases — map agent names to target scopes.

Aliases allow agents to have persistent scope bindings that can be
resolved by other modules (e.g. packet.py, search.py) without
hardcoding agent→scope mappings.
"""
from __future__ import annotations

from datetime import datetime, timezone

from eduflow.memory.db import get_conn, init_schema


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_alias(alias: str, target_scope: str, *, kind_filter: str = "") -> None:
    """Add or update a scope alias."""
    if not alias.strip():
        raise ValueError("alias cannot be empty")
    if not target_scope.strip():
        raise ValueError("target_scope cannot be empty")
    init_schema()
    now = _now_iso()
    conn = get_conn()
    conn.execute(
        """INSERT INTO memory_scope_aliases (alias, target_scope, kind_filter, active, created_at)
           VALUES (?, ?, ?, 1, ?)
           ON CONFLICT(alias) DO UPDATE SET target_scope=excluded.target_scope,
           kind_filter=excluded.kind_filter, active=1, created_at=excluded.created_at""",
        (alias.strip(), target_scope.strip(), kind_filter.strip(), now),
    )
    conn.commit()


def get_alias(alias: str) -> dict | None:
    """Fetch a single alias by name."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM memory_scope_aliases WHERE alias = ?", (alias,)
    ).fetchone()
    return dict(row) if row else None


def resolve_alias(alias: str) -> str | None:
    """Returns target_scope if alias is active, else None."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT target_scope, active FROM memory_scope_aliases WHERE alias = ?",
        (alias,),
    ).fetchone()
    if row is None or row["active"] != 1:
        return None
    return row["target_scope"]


def list_aliases(*, active_only: bool = True) -> list[dict]:
    """List all aliases, optionally filtering to active only."""
    init_schema()
    conn = get_conn()
    query = "SELECT * FROM memory_scope_aliases"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY alias"
    rows = conn.execute(query).fetchall()
    return [dict(r) for r in rows]


def deactivate_alias(alias: str) -> bool:
    """Set active=0 for an alias. Returns True if found and changed."""
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT active FROM memory_scope_aliases WHERE alias = ?", (alias,)
    ).fetchone()
    if row is None:
        return False
    if row["active"] == 0:
        return False
    conn.execute(
        "UPDATE memory_scope_aliases SET active = 0 WHERE alias = ?",
        (alias,),
    )
    conn.commit()
    return True
