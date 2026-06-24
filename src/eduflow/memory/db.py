"""SQLite connection management and schema for EduFlow Memory.

Introduces SQLite as a new persistence mechanism alongside the existing
JSON/JSONL stores. Connection is cached per-thread via threading.local().
WAL mode + short transactions + 5s busy timeout for concurrency.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from eduflow.runtime.paths import ensure_state_dir, memory_db_file

_local = threading.local()

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS active_constraints (
    id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    constraint_level TEXT NOT NULL,
    constraint_type TEXT NOT NULL,
    content TEXT NOT NULL,
    source_ref TEXT DEFAULT '',
    evidence_refs TEXT DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    enforcement TEXT NOT NULL DEFAULT 'prompt_only',
    injection_point TEXT DEFAULT 'send,reidentify,compact',
    valid_from TEXT NOT NULL,
    valid_until TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_capsules (
    task_id TEXT PRIMARY KEY,
    workflow_id TEXT DEFAULT '',
    owner TEXT DEFAULT '',
    gate TEXT DEFAULT '',
    goal TEXT DEFAULT '',
    acceptance TEXT DEFAULT '',
    current_status TEXT DEFAULT '',
    decisions TEXT DEFAULT '[]',
    blockers TEXT DEFAULT '[]',
    next_action TEXT DEFAULT '',
    last_evidence_ref TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

-- Phase 1: Memory Core tables
CREATE TABLE IF NOT EXISTS memory_items (
    id              TEXT PRIMARY KEY,   -- MI-{YYYYMMDD}-{seq:03d}
    layer           TEXT NOT NULL,      -- core | task | episode | decision | reflection | archive
    scope           TEXT NOT NULL,      -- team | lane:X | agent:X | workflow:X | task:X | subject:X | project:X
    kind            TEXT NOT NULL,      -- role_rule | workflow_rule | decision | mistake | preference | handoff | domain_fact | runtime_rule | note
    status          TEXT NOT NULL DEFAULT 'candidate',  -- candidate | confirmed | deprecated | rejected
    content         TEXT NOT NULL,
    summary         TEXT DEFAULT '',
    source_ref      TEXT DEFAULT '',
    evidence_refs   TEXT DEFAULT '[]',  -- JSON array of strings
    confidence      REAL DEFAULT 1.0,
    importance      INTEGER DEFAULT 5,  -- 1-10
    valid_from      TEXT NOT NULL,      -- ISO timestamp
    valid_until     TEXT DEFAULT '',    -- empty = no expiry
    created_by      TEXT DEFAULT '',
    created_at      TEXT NOT NULL,      -- ISO timestamp
    updated_at      TEXT NOT NULL,      -- ISO timestamp
    supersedes      TEXT DEFAULT '',    -- ID of memory this completely replaces
    revision_of     TEXT DEFAULT '',    -- ID of memory this minorly updates (old kept for audit)
    metadata_json   TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS memory_scope_aliases (
    alias           TEXT PRIMARY KEY,   -- e.g. "worker_course"
    target_scope    TEXT NOT NULL,      -- e.g. "agent:worker_course"
    kind_filter     TEXT DEFAULT '',    -- optional: only apply for this kind
    active          INTEGER DEFAULT 1,  -- 0 = inactive
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_candidates (
    candidate_id    TEXT PRIMARY KEY,   -- CAND-{YYYYMMDD}-{seq:03d}
    source_type     TEXT NOT NULL,      -- manual | review_reject | closeout_anomaly | manager_correction
    source_ref      TEXT DEFAULT '',
    proposed_layer  TEXT DEFAULT 'episode',
    proposed_scope  TEXT NOT NULL,
    proposed_kind   TEXT NOT NULL,
    content         TEXT NOT NULL,
    reason          TEXT DEFAULT '',
    evidence_refs   TEXT DEFAULT '[]',  -- JSON array
    risk_flags      TEXT DEFAULT '[]',  -- JSON array
    created_at      TEXT NOT NULL,
    review_status   TEXT NOT NULL DEFAULT 'proposed',  -- proposed | promoted | rejected
    reviewed_by     TEXT DEFAULT '',
    reviewed_at     TEXT DEFAULT '',
    expires_at      TEXT NOT NULL       -- default 90 days from creation
);

CREATE INDEX IF NOT EXISTS idx_ac_scope ON active_constraints(scope);
CREATE INDEX IF NOT EXISTS idx_ac_status ON active_constraints(status);
CREATE INDEX IF NOT EXISTS idx_ac_level ON active_constraints(constraint_level);

-- Memory Items indexes
CREATE INDEX IF NOT EXISTS idx_mi_scope ON memory_items(scope);
CREATE INDEX IF NOT EXISTS idx_mi_status ON memory_items(status);
CREATE INDEX IF NOT EXISTS idx_mi_kind ON memory_items(kind);
CREATE INDEX IF NOT EXISTS idx_mi_layer ON memory_items(layer);

-- Memory Scope Aliases indexes
CREATE INDEX IF NOT EXISTS idx_msa_active ON memory_scope_aliases(active);

-- Memory Candidates indexes
CREATE INDEX IF NOT EXISTS idx_mc_status ON memory_candidates(review_status);
CREATE INDEX IF NOT EXISTS idx_mc_scope ON memory_candidates(proposed_scope);
"""


def get_conn() -> sqlite3.Connection:
    """Return a per-thread cached SQLite connection with WAL mode."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn
    db_path = memory_db_file()
    ensure_state_dir()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    _local.conn = conn
    return conn


def init_schema() -> None:
    """Create tables and indexes if they don't exist. Idempotent."""
    conn = get_conn()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()


def close() -> None:
    """Close the current thread's connection (for cleanup / testing)."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
