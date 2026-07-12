"""Tests for EduFlow Memory V1 Hardening modules.

Covers:
- storage_budget: check_budget, enforce_budget, budget_report
- expiration: expire_constraints, expire_memories, expire_candidates, run_all_expirations
- audit: full_audit, scope_coverage_report, retention_report
- CLI: _cmd_budget, _cmd_expire, _cmd_audit, _cmd_promote --yes, _cmd_reject --yes
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── storage_budget ─────────────────────────────────────────────────

class TestStorageBudget:
    def test_check_budget_empty_table(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.storage_budget import check_budget
            info = check_budget("active_constraints")
            assert info["table"] == "active_constraints"
            assert info["current"] == 0
            assert info["limit"] == 50
            assert info["over"] == 0
            assert info["headroom"] == 50
            _reset_db()

    def test_check_budget_with_data(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.storage_budget import check_budget
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="test constraint 1")
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="test constraint 2")
            info = check_budget("active_constraints")
            assert info["current"] == 2
            assert info["headroom"] == 48
            _reset_db()

    def test_check_budget_unknown_table_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.storage_budget import check_budget
            with pytest.raises(ValueError, match="unknown table"):
                check_budget("nonexistent_table")
            _reset_db()

    def test_enforce_budget_under_limit_no_eviction(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.storage_budget import enforce_budget
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="one constraint")
            result = enforce_budget("active_constraints")
            assert result["evicted"] == 0
            assert result["remaining"] == 1
            assert result["strategy"] == "none_under_budget"
            _reset_db()

    def test_enforce_budget_evicts_when_over(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.memory.storage_budget import enforce_budget, LIMITS

            # Temporarily lower limit for testing
            old_limit = LIMITS["memory_candidates"]
            LIMITS["memory_candidates"] = 3

            try:
                for i in range(5):
                    add_candidate(
                        "team", "note",
                        content=f"candidate {i}", source_type="manual",
                    )
                result = enforce_budget("memory_candidates")
                assert result["evicted"] >= 1
                assert result["remaining"] <= 3
            finally:
                LIMITS["memory_candidates"] = old_limit
            _reset_db()

    def test_enforce_budget_keeps_min_keep(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.memory.storage_budget import enforce_budget, LIMITS, _MIN_KEEP

            old_limit = LIMITS["memory_candidates"]
            LIMITS["memory_candidates"] = 1
            try:
                for i in range(3):
                    add_candidate(
                        "team", "note",
                        content=f"candidate {i}", source_type="manual",
                    )
                result = enforce_budget("memory_candidates")
                assert result["remaining"] >= _MIN_KEEP
            finally:
                LIMITS["memory_candidates"] = old_limit
            _reset_db()

    def test_budget_report_includes_db_size(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.storage_budget import budget_report
            report = budget_report()
            assert "tables" in report
            assert "db_size_bytes" in report
            assert report["db_size_bytes"] >= 0
            assert "active_constraints" in report["tables"]
            assert "memory_items" in report["tables"]
            assert "memory_candidates" in report["tables"]
            _reset_db()


# ── expiration ──────────────────────────────────────────────────────

class TestExpiration:
    def test_expire_constraints_transitions_active_to_inactive(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.expiration import expire_constraints

            # Add constraint that expired yesterday
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            cid = add_constraint(
                scope="team", level="L0", constraint_type="must_follow",
                content="expired constraint", valid_until=yesterday,
            )
            count = expire_constraints()
            assert count == 1

            # Verify it's now inactive
            from eduflow.memory.constraints import get_constraint
            c = get_constraint(cid)
            assert c["status"] == "inactive"
            _reset_db()

    def test_expire_constraints_skips_future(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.expiration import expire_constraints

            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            add_constraint(
                scope="team", level="L0", constraint_type="must_follow",
                content="future constraint", valid_until=tomorrow,
            )
            count = expire_constraints()
            assert count == 0
            _reset_db()

    def test_expire_constraints_skips_empty_valid_until(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.expiration import expire_constraints

            add_constraint(
                scope="team", level="L0", constraint_type="must_follow",
                content="no expiry set",
            )
            count = expire_constraints()
            assert count == 0
            _reset_db()

    def test_expire_memories_transitions_confirmed_to_deprecated(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.expiration import expire_memories

            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            mid = add_memory(
                scope="team", kind="workflow_rule",
                content="expired memory", layer="decision",
                status="confirmed", valid_until=yesterday,
            )
            count = expire_memories()
            assert count == 1

            from eduflow.memory.items import get_memory
            m = get_memory(mid)
            assert m["status"] == "deprecated"
            _reset_db()

    def test_expire_candidates_delegates(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.expiration import expire_candidates
            # On empty DB, should return 0 without crashing
            count = expire_candidates()
            assert count == 0
            _reset_db()

    def test_run_all_expirations_returns_summary(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.expiration import run_all_expirations
            result = run_all_expirations()
            assert "constraints_expired" in result
            assert "memories_expired" in result
            assert "candidates_expired" in result
            assert "total" in result
            assert result["total"] == result["constraints_expired"] + result["memories_expired"] + result["candidates_expired"]
            _reset_db()


# ── audit ───────────────────────────────────────────────────────────

class TestAudit:
    def test_full_audit_structure(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.audit import full_audit
            audit = full_audit()
            assert "active_constraints" in audit
            assert "memory_items" in audit
            assert "memory_candidates" in audit
            assert "task_capsules" in audit
            assert "memory_scope_aliases" in audit
            _reset_db()

    def test_full_audit_counts(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.items import add_memory
            from eduflow.memory.audit import full_audit

            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="c1")
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="c2")
            add_memory(scope="team", kind="workflow_rule", content="m1",
                       layer="decision", status="confirmed")

            audit = full_audit()
            assert audit["active_constraints"]["active"] == 2
            assert audit["memory_items"]["confirmed"] == 1
            _reset_db()

    def test_scope_coverage_report_empty(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.audit import scope_coverage_report
            report = scope_coverage_report()
            assert report == []
            _reset_db()

    def test_scope_coverage_report_groups(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.audit import scope_coverage_report

            add_memory(scope="team", kind="workflow_rule", content="r1",
                       layer="decision", status="confirmed")
            add_memory(scope="team", kind="mistake", content="r2",
                       layer="decision", status="confirmed")
            add_memory(scope="lane:caie", kind="handoff", content="r3",
                       layer="decision", status="confirmed")

            report = scope_coverage_report()
            assert len(report) == 2
            team_report = next(r for r in report if r["scope"] == "team")
            assert team_report["total"] == 2
            assert team_report["kinds"]["workflow_rule"] == 1
            assert team_report["kinds"]["mistake"] == 1
            _reset_db()

    def test_retention_report_structure(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.audit import retention_report
            report = retention_report(days=30)
            assert report["period_days"] == 30
            assert "items" in report
            assert "candidates" in report
            assert "constraints" in report
            assert "window_start" in report
            _reset_db()


# ── CLI commands ────────────────────────────────────────────────────

class TestCLICommands:
    def test_cmd_budget_full(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_budget
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_budget([])
            assert rc == 0
            output = buf.getvalue()
            assert "active_constraints" in output
            assert "db_size_bytes" in output or "bytes" in output
            _reset_db()

    def test_cmd_budget_check(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_budget
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_budget(["check", "active_constraints"])
            assert rc == 0
            output = buf.getvalue()
            assert "active_constraints" in output
            assert "0/50" in output
            _reset_db()

    def test_cmd_budget_enforce_under(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_budget
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_budget(["enforce", "active_constraints"])
            assert rc == 0
            output = buf.getvalue()
            assert "Evicted: 0" in output
            _reset_db()

    def test_cmd_expire(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_expire
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_expire([])
            assert rc == 0
            output = buf.getvalue()
            assert "Expired:" in output
            assert "total=0" in output
            _reset_db()

    def test_cmd_audit_full(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_audit
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_audit([])
            assert rc == 0
            output = buf.getvalue()
            assert "active_constraints:" in output
            _reset_db()

    def test_cmd_audit_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_audit
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_audit(["scope"])
            assert rc == 0
            output = buf.getvalue()
            assert "No confirmed memories" in output
            _reset_db()

    def test_cmd_audit_retention(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_audit
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_audit(["retention", "--days", "30"])
            assert rc == 0
            output = buf.getvalue()
            assert "Retention report" in output
            _reset_db()

    def test_cmd_cleanup(self):
        with isolated_env():
            _init_db()
            from eduflow.commands.memory_cli import _cmd_cleanup
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_cleanup([])
            assert rc == 0
            output = buf.getvalue()
            assert "Cleanup complete" in output
            _reset_db()

    def test_cmd_promote_yes_flag(self):
        """_cmd_promote with --yes should skip confirmation prompt."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.commands.memory_cli import _cmd_promote

            cid = add_candidate(
                "team", "note",
                content="test promote", source_type="manual",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_promote([cid, "--yes"])
            assert rc == 0
            output = buf.getvalue()
            assert "Promoted candidate" in output
            _reset_db()

    def test_cmd_reject_yes_flag(self):
        """_cmd_reject with --yes should skip confirmation prompt."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.commands.memory_cli import _cmd_reject

            cid = add_candidate(
                "team", "note",
                content="test reject", source_type="manual",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = _cmd_reject([cid, "--yes", "--reason", "not needed"])
            assert rc == 0
            output = buf.getvalue()
            assert "Rejected candidate" in output
            _reset_db()

    def test_cmd_promote_preview_shown(self):
        """_cmd_promote should show preview before confirmation."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.commands.memory_cli import _cmd_promote

            cid = add_candidate(
                "team", "note",
                content="preview content here", source_type="manual",
            )
            buf = io.StringIO()
            # Use --yes to avoid blocking on input()
            with redirect_stdout(buf):
                _cmd_promote([cid, "--yes"])
            output = buf.getvalue()
            assert "scope=team" in output
            assert "kind=note" in output
            assert "preview content here" in output
            _reset_db()
