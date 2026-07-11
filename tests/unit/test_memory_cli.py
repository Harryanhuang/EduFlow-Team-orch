"""Tests for `eduflow memory` CLI subcommands."""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli


def test_memory_doctor_reports_counts_and_placeholders():
    """doctor is read-only and reports row counts + placeholder detection."""
    with isolated_env():
        from eduflow.memory import db
        from eduflow.memory.candidates import add_candidate
        from eduflow.memory.constraints import add_constraint

        db.init_schema()
        # Normal proposed candidate
        add_candidate(
            scope="team", kind="workflow_rule",
            content="Always review large refactors",
            source_type="manual", reason="best practice",
        )
        # Obvious placeholder candidate
        add_candidate(
            scope="team", kind="note",
            content="pin me",
            source_type="manual", reason="test fixture",
        )
        # A confirmed memory item for row-count coverage
        from eduflow.memory.items import add_memory
        add_memory(
            scope="team", kind="workflow_rule",
            content="Use plan mode for architecture changes",
            status="confirmed", importance=8,
        )
        # Active constraint
        add_constraint(
            scope="team", level="L0",
            constraint_type="must_follow",
            content="All public APIs must have tests",
        )

        before_counts = _row_counts(db.get_conn())
        rc, out, err = run_cli(["memory", "doctor"])
        after_counts = _row_counts(db.get_conn())

        assert rc == 0, err
        assert "Memory Doctor (read-only)" in out
        assert "memory_items: 1" in out
        assert "memory_candidates: 2" in out
        assert "active_constraints: 1" in out
        assert "manual: 2" in out
        assert "Obvious placeholder candidates: 1" in out
        assert "Manager governance signal: yes" in out
        assert before_counts == after_counts, "doctor must not mutate rows"


def test_memory_doctor_warns_on_path_mismatch():
    """doctor warns when the EduFlow DB and flow_memory DB disagree."""
    import os
    from helpers import env_patch

    with isolated_env() as tmp:
        from eduflow.memory import db
        from flow_memory.storage import paths as fm_paths, sql as fm_sql

        db.init_schema()
        # Force a path disagreement by pointing FLOW_MEMORY_DB elsewhere.
        other_db = tmp / "other" / "flow_memory.db"
        other_db.parent.mkdir(parents=True, exist_ok=True)
        fm_paths._provider = None
        fm_sql._backend = None
        with env_patch(FLOW_MEMORY_DB=str(other_db)):
            fm_paths._provider = None
            fm_sql._backend = None
            rc, out, err = run_cli(["memory", "doctor"])
            fm_paths._provider = None
            fm_sql._backend = None

        assert rc == 0, err
        assert "CLI/package DB path disagreement" in out


def _row_counts(conn):
    tables = [
        "memory_items", "memory_candidates", "active_constraints",
        "task_capsules", "memory_user_profile",
    ]
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in tables}
