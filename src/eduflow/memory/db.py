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

-- Agent-lane bindings
CREATE TABLE IF NOT EXISTS agent_lane_bindings (
    agent TEXT NOT NULL,
    lane_id TEXT NOT NULL,
    role TEXT DEFAULT '',
    active INTEGER DEFAULT 1,
    valid_from TEXT NOT NULL,
    valid_until TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (agent, lane_id)
);
CREATE INDEX IF NOT EXISTS idx_alb_agent ON agent_lane_bindings(agent);
CREATE INDEX IF NOT EXISTS idx_alb_lane ON agent_lane_bindings(lane_id);
CREATE INDEX IF NOT EXISTS idx_alb_active ON agent_lane_bindings(active);

-- Memory relationship graph
CREATE TABLE IF NOT EXISTS memory_links (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_ml_from ON memory_links(from_id);
CREATE INDEX IF NOT EXISTS idx_ml_to ON memory_links(to_id);
CREATE INDEX IF NOT EXISTS idx_ml_relation ON memory_links(relation);

-- V3 P0-2: pinned column added via migrate_pinned_column() below.
-- (ALTER TABLE in CREATE block causes duplicate column errors, so the
-- migration is run separately after CREATE statements.)

-- User profile / cross-agent habit storage
CREATE TABLE IF NOT EXISTS memory_user_profile (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    value_type      TEXT DEFAULT 'text',  -- text | json | list
    confidence      REAL DEFAULT 1.0,
    evidence_refs   TEXT DEFAULT '[]',    -- JSON array of strings
    updated_at      TEXT NOT NULL         -- ISO timestamp
);
CREATE INDEX IF NOT EXISTS idx_mup_updated ON memory_user_profile(updated_at);

-- Sensitive data configuration (password hash, salt, security questions)
CREATE TABLE IF NOT EXISTS sensitive_config (
    id              TEXT PRIMARY KEY DEFAULT 'singleton',
    password_hash   TEXT NOT NULL,      -- PBKDF2 hash of password
    salt            TEXT NOT NULL,      -- base64-encoded salt for PBKDF2
    questions_json  TEXT NOT NULL,      -- encrypted JSON of security Q&A
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- Daily summary / short-term memory (V3 P1-5)
CREATE TABLE IF NOT EXISTS memory_daily_summary (
    date            TEXT NOT NULL,           -- YYYY-MM-DD
    agent           TEXT NOT NULL,           -- which agent wrote this
    summary         TEXT NOT NULL,           -- what happened today
    key_decisions   TEXT DEFAULT '[]',      -- JSON array
    open_questions  TEXT DEFAULT '[]',      -- JSON array
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (date, agent)
);
CREATE INDEX IF NOT EXISTS idx_mds_agent ON memory_daily_summary(agent);
CREATE INDEX IF NOT EXISTS idx_mds_created ON memory_daily_summary(created_at);

-- Sensitive memory items (encrypted content)
CREATE TABLE IF NOT EXISTS sensitive_memory_items (
    id              TEXT PRIMARY KEY,   -- SM-{YYYYMMDD}-{seq:03d}
    scope           TEXT NOT NULL,
    kind            TEXT NOT NULL,
    encrypted_data  BLOB NOT NULL,      -- AES-256-GCM encrypted JSON
    nonce           BLOB NOT NULL,      -- 12-byte nonce
    tag             BLOB NOT NULL,      -- 16-byte GCM auth tag
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_smi_scope ON sensitive_memory_items(scope);
CREATE INDEX IF NOT EXISTS idx_smi_status ON sensitive_memory_items(status);
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
    migrate_pinned_column()


def migrate_pinned_column() -> None:
    """V3 P0-2: add `pinned` column to memory_items if missing.

    Idempotent: catches "duplicate column" errors silently.
    """
    conn = get_conn()
    try:
        conn.execute("ALTER TABLE memory_items ADD COLUMN pinned INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass  # column already exists


def close() -> None:
    """Close the current thread's connection (for cleanup / testing)."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
