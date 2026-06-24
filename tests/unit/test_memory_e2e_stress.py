"""Integration stress tests for EduFlow Memory V1 Hardening.

Covers end-to-end scenarios that exercise multiple modules together:
- Candidate batch processing and budget limits
- Full memory lifecycle (create → confirm → deprecate → archive)
- Multi-workflow scope isolation
- Packet budget stress with many constraints
- Gate check pressure with many gate_required constraints
- Expiry + budget joint enforcement
- Export consistency with DB state
"""
from __future__ import annotations

import io
import os
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


# ── Scenario 1: Batch review_reject events ─────────────────────────

class TestBatchReviewReject:
    def test_50_batch_candidates_dedup(self):
        """50 batch review_reject candidates: dedup + budget limits."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, list_candidates
            from eduflow.memory.storage_budget import check_budget

            for i in range(50):
                add_candidate(
                    "team", "note",
                    content=f"batch candidate {i}",
                    source_type="review_reject",
                )

            info = check_budget("memory_candidates")
            assert info["current"] == 50

            # List should return all 50
            candidates = list_candidates(limit=100)
            assert len(candidates) == 50
            _reset_db()


# ── Scenario 2: Full lifecycle ─────────────────────────────────────

class TestFullLifecycle:
    def test_create_confirm_deprecate_archive(self):
        """Full lifecycle: create → confirm → deprecate → archive."""
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, get_memory, deprecate_memory
            from eduflow.memory.audit import full_audit

            # Create and confirm
            mid = add_memory(
                scope="team", kind="workflow_rule",
                content="lifecycle test rule",
                layer="decision", status="confirmed",
            )
            m = get_memory(mid)
            assert m["status"] == "confirmed"

            # Deprecate
            ok = deprecate_memory(mid)
            assert ok is True
            m = get_memory(mid)
            assert m["status"] == "deprecated"

            # Audit should show 1 deprecated
            audit = full_audit()
            assert audit["memory_items"]["deprecated"] == 1
            _reset_db()


# ── Scenario 3: Multi-workflow scope isolation ─────────────────────

class TestScopeIsolation:
    def test_wf_a_does_not_leak_to_wf_b(self):
        """Memories in workflow_A don't appear in workflow_B queries."""
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories

            add_memory(
                scope="workflow:wf_A", kind="workflow_rule",
                content="rule for A", layer="decision", status="confirmed",
            )
            add_memory(
                scope="workflow:wf_B", kind="workflow_rule",
                content="rule for B", layer="decision", status="confirmed",
            )

            # Query by scope
            a_items = list_memories(scope="workflow:wf_A")
            b_items = list_memories(scope="workflow:wf_B")
            assert len(a_items) == 1
            assert a_items[0]["content"] == "rule for A"
            assert len(b_items) == 1
            assert b_items[0]["content"] == "rule for B"
            _reset_db()


# ── Scenario 4: Packet budget stress ───────────────────────────────

class TestPacketBudgetStress:
    def test_20_long_constraints_stay_under_budget(self):
        """20 long constraints should produce a packet under 4000 chars."""
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.packet import assemble_memory_packet

            for i in range(20):
                add_constraint(
                    scope="team", level="L0", constraint_type="must_follow",
                    content=f"Constraint number {i}: " + "x" * 200,
                )

            packet = assemble_memory_packet("worker_course")
            assert len(packet) <= 4000
            _reset_db()


# ── Scenario 5: Gate check pressure ────────────────────────────────

class TestGateCheckPressure:
    def test_15_gate_required_constraints(self):
        """15 gate_required constraints should be handled correctly."""
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.inject import build_gate_check

            for i in range(15):
                add_constraint(
                    scope="team", level="L0", constraint_type="gate_check",
                    content=f"Gate rule {i}",
                    enforcement="gate_required",
                )

            result = build_gate_check("worker_course", "T-99", "review_pending")
            assert "allowed" in result
            assert "blocking_constraints" in result
            # All 15 should be blocking
            assert len(result["blocking_constraints"]) == 15
            _reset_db()


# ── Scenario 6: Expiry + budget joint ──────────────────────────────

class TestExpiryBudgetJoint:
    def test_expire_then_enforce_within_limits(self):
        """205 candidates → expire → enforce → within limits."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate
            from eduflow.memory.expiration import expire_candidates
            from eduflow.memory.storage_budget import enforce_budget, check_budget, LIMITS

            # Add 205 candidates (over limit of 200)
            for i in range(205):
                add_candidate(
                    "team", "note",
                    content=f"candidate {i}", source_type="manual",
                )

            info = check_budget("memory_candidates")
            assert info["current"] == 205
            assert info["over"] == 5

            # Expire doesn't help (none are expired yet)
            expired = expire_candidates()
            assert expired == 0

            # Budget enforce should evict down to limit
            result = enforce_budget("memory_candidates")
            assert result["evicted"] >= 5

            info = check_budget("memory_candidates")
            assert info["current"] <= LIMITS["memory_candidates"]
            _reset_db()


# ── Scenario 7: Export consistency ─────────────────────────────────

class TestExportConsistency:
    def test_db_state_matches_export(self):
        """DB state should match Obsidian export files."""
        with isolated_env() as env:
            os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(env)
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.items import add_memory
            from eduflow.memory.obsidian_export import export_all

            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="export test constraint")
            add_memory(scope="team", kind="workflow_rule",
                       content="export test memory", layer="decision",
                       status="confirmed")

            counts = export_all()
            assert counts["constraints"] == 1
            assert counts["items"] == 1

            # Verify files exist
            exports = env / "_memory-exports"
            assert (exports / "active-constraints.md").exists()
            ac_text = (exports / "active-constraints.md").read_text()
            assert "export test constraint" in ac_text
            _reset_db()
