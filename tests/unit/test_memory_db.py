"""Tests for eduflow.memory.db — connection management and schema.

Covers:
- init_schema(): table creation, idempotency
- get_conn(): per-thread caching, WAL mode, row_factory
- close(): connection cleanup
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── init_schema ────────────────────────────────────────────────────

class TestInitSchema:
    def test_creates_all_tables(self):
        """init_schema creates all 5 expected tables."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "ORDER BY name"
            ).fetchall()
            table_names = {r[0] for r in rows}
            expected = {
                "active_constraints",
                "task_capsules",
                "memory_items",
                "memory_scope_aliases",
                "memory_candidates",
            }
            assert expected.issubset(table_names), (
                f"missing tables: {expected - table_names}"
            )
            _reset_db()

    def test_idempotent_double_call(self):
        """Calling init_schema twice does not raise or duplicate tables."""
        with isolated_env():
            from eduflow.memory.db import get_conn
            _init_db()
            count_before = _count_tables(get_conn())
            _init_db()  # second call
            count_after = _count_tables(get_conn())
            assert count_before == count_after
            _reset_db()

    def test_idempotent_triple_call(self):
        """Triple call is still idempotent."""
        with isolated_env():
            from eduflow.memory.db import get_conn
            _init_db()
            _init_db()
            _init_db()
            count = _count_tables(get_conn())
            assert count >= 5
            _reset_db()

    def test_indexes_created(self):
        """init_schema creates the expected indexes."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name LIKE 'idx_%'"
            ).fetchall()
            idx_names = {r[0] for r in rows}
            # Spot-check a few critical indexes
            assert "idx_ac_scope" in idx_names
            assert "idx_mi_scope" in idx_names
            assert "idx_mc_status" in idx_names
            _reset_db()


# ── get_conn ───────────────────────────────────────────────────────

class TestGetConn:
    def test_returns_same_connection_in_same_thread(self):
        """get_conn() caches and returns the same connection object."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn1 = get_conn()
            conn2 = get_conn()
            assert conn1 is conn2
            _reset_db()

    def test_row_factory_is_row(self):
        """Connection returns sqlite3.Row objects."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            assert conn.row_factory is sqlite3.Row
            _reset_db()

    def test_wal_mode_enabled(self):
        """Journal mode is set to WAL."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"
            _reset_db()

    def test_busy_timeout_set(self):
        """Busy timeout is configured to 5 seconds."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            assert timeout == 5000
            _reset_db()

    def test_db_file_created_in_state_dir(self):
        """The SQLite file is created inside EDUFLOW_STATE_DIR."""
        with isolated_env() as tmp:
            _init_db()
            from eduflow.memory.db import memory_db_file
            db_path = memory_db_file()
            assert db_path.exists()
            assert str(db_path).startswith(str(tmp / "state"))
            _reset_db()


# ── close ──────────────────────────────────────────────────────────

class TestClose:
    def test_close_clears_connection_cache(self):
        """After close(), get_conn returns a new connection object."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn, close
            conn1 = get_conn()
            close()
            conn2 = get_conn()
            assert conn1 is not conn2
            _reset_db()

    def test_close_idempotent(self):
        """Calling close() twice does not raise."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import close
            close()
            close()  # should not raise
            _reset_db()

    def test_close_then_schema_still_works(self):
        """After close + re-init, tables are still accessible."""
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn, close, init_schema
            conn = get_conn()
            conn.execute(
                "INSERT INTO memory_items "
                "(id, layer, scope, kind, status, content, valid_from, "
                "created_at, updated_at) "
                "VALUES ('MI-TEST-001', 'core', 'team', 'note', 'confirmed', "
                "'test', '2026-01-01T00:00:00', '2026-01-01T00:00:00', "
                "'2026-01-01T00:00:00')"
            )
            conn.commit()
            close()
            init_schema()
            conn2 = get_conn()
            row = conn2.execute(
                "SELECT id FROM memory_items WHERE id = 'MI-TEST-001'"
            ).fetchone()
            assert row is not None
            _reset_db()


# ── helpers ────────────────────────────────────────────────────────

def _count_tables(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()
    return rows[0]
