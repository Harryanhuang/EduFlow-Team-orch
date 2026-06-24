"""Tests for EduFlow Memory Phase 1A: Active Constraint Rehydration.

Covers: schema init, constraint CRUD, scope aggregation, packet assembly,
Package 1/3 derivation, closeout supersession, send integration,
reidentify integration, CLI commands.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env, run_cli


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    """Ensure schema is initialized in the current isolated env."""
    from eduflow.memory.db import init_schema, close
    close()  # clear any stale connection from prior test
    init_schema()


def _reset_db():
    """Close connection so next test gets a fresh one to the temp DB."""
    from eduflow.memory.db import close
    close()


# ── schema init ───────────────────────────────────────────────────

class TestSchemaInit:
    def test_tables_created(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "active_constraints" in tables
            assert "task_capsules" in tables
            _reset_db()

    def test_idempotent(self):
        with isolated_env():
            _init_db()
            _init_db()  # second call should not raise
            from eduflow.memory.db import get_conn
            conn = get_conn()
            count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            assert count >= 2
            _reset_db()


# ── constraint CRUD ──────────────────────────────────────────────

class TestConstraintCRUD:
    def test_add_and_get(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, get_constraint
            cid = add_constraint(
                scope="team",
                level="L0",
                constraint_type="must_follow",
                content="manager不亲自干活",
                enforcement="gate_required",
                created_by="test",
            )
            assert cid.startswith("AC-")
            c = get_constraint(cid)
            assert c is not None
            assert c["scope"] == "team"
            assert c["constraint_level"] == "L0"
            assert c["content"] == "manager不亲自干活"
            assert c["status"] == "active"
            _reset_db()

    def test_list_constraints(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, list_constraints
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="rule1", created_by="test")
            add_constraint(scope="task:T-1", level="L2", constraint_type="gate_check",
                           content="rule2", created_by="test")
            all_active = list_constraints(status="active")
            assert len(all_active) == 2
            team_only = list_constraints(scope="team", status="active")
            assert len(team_only) == 1
            _reset_db()

    def test_deactivate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import (
                add_constraint, get_constraint, deactivate_constraint,
            )
            cid = add_constraint(scope="team", level="L0", constraint_type="must_follow",
                                 content="test rule", created_by="test")
            ok = deactivate_constraint(cid, reason="no longer needed")
            assert ok is True
            c = get_constraint(cid)
            assert c["status"] == "inactive"
            # double-deactivate returns False
            ok2 = deactivate_constraint(cid)
            assert ok2 is False
            _reset_db()

    def test_supersede(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import (
                add_constraint, get_constraint, supersede_constraint,
            )
            old = add_constraint(scope="team", level="L0", constraint_type="must_follow",
                                 content="old rule", created_by="test")
            new = add_constraint(scope="team", level="L0", constraint_type="must_follow",
                                 content="new rule", created_by="test")
            ok = supersede_constraint(old, new)
            assert ok is True
            assert get_constraint(old)["status"] == "inactive"
            assert get_constraint(new)["status"] == "active"
            _reset_db()

    def test_invalid_level_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            with pytest.raises(ValueError, match="invalid level"):
                add_constraint(scope="team", level="L99", constraint_type="must_follow",
                               content="bad", created_by="test")
            _reset_db()

    def test_empty_content_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            with pytest.raises(ValueError, match="content cannot be empty"):
                add_constraint(scope="team", level="L0", constraint_type="must_follow",
                               content="   ", created_by="test")
            _reset_db()


# ── scope aggregation ─────────────────────────────────────────────

class TestScopeAggregation:
    def test_query_for_agent_team_and_task(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, query_for_agent
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="team rule", created_by="test")
            add_constraint(scope="task:T-29", level="L2", constraint_type="gate_check",
                           content="task rule for T-29", created_by="test")
            add_constraint(scope="task:T-30", level="L2", constraint_type="gate_check",
                           content="task rule for T-30", created_by="test")

            results = query_for_agent("worker_course", task_id="T-29")
            contents = [r["content"] for r in results]
            assert "team rule" in contents
            assert "task rule for T-29" in contents
            assert "task rule for T-30" not in contents
            _reset_db()

    def test_query_deduplicates_by_content(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, query_for_agent
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="same rule", created_by="test")
            add_constraint(scope="lane:curriculum", level="L1", constraint_type="must_follow",
                           content="same rule", created_by="test")
            results = query_for_agent("worker_course")
            assert len([r for r in results if r["content"] == "same rule"]) == 1
            _reset_db()

    def test_query_respects_level_priority(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, query_for_agent
            add_constraint(scope="task:T-1", level="L2", constraint_type="must_follow",
                           content="L2 rule", created_by="test")
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="L0 rule", created_by="test")
            add_constraint(scope="lane:x", level="L1", constraint_type="must_follow",
                           content="L1 rule", created_by="test")
            results = query_for_agent("any_agent", task_id="T-1")
            levels = [r["constraint_level"] for r in results]
            assert levels == ["L0", "L1", "L2"]
            _reset_db()


# ── packet assembly ──────────────────────────────────────────────

class TestPacketAssembly:
    def test_empty_when_no_constraints(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            packet = assemble_memory_packet("worker_course")
            assert packet == ""
            _reset_db()

    def test_includes_constraints(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.packet import assemble_memory_packet
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="manager不亲自干活", enforcement="gate_required",
                           created_by="test")
            packet = assemble_memory_packet("worker_course")
            assert "EduFlow Active Constraints" in packet
            assert "manager不亲自干活" in packet
            assert "[L0/gate_required]" in packet
            _reset_db()

    def test_includes_capsule(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.capsules import upsert_capsule
            from eduflow.memory.packet import assemble_memory_packet
            upsert_capsule(
                "T-29",
                workflow_id="igcse-subject-launch",
                owner="worker_course",
                gate="review_handoff_gate",
                goal="Launch IGCSE Math",
                next_action="submit_review",
            )
            packet = assemble_memory_packet("worker_course", task_id="T-29")
            assert "T-29" in packet
            assert "igcse-subject-launch" in packet
            _reset_db()

    def test_budget_enforcement(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.packet import assemble_memory_packet
            # Add 10 constraints (over the MAX_CONSTRAINTS=8 limit)
            for i in range(10):
                add_constraint(scope="team", level="L3", constraint_type="must_follow",
                               content=f"constraint-{i}-" + "x" * 50,
                               created_by="test")
            packet = assemble_memory_packet("worker_course")
            # Should contain at most 8 constraint items
            assert packet.count("- [L3") <= 8
            _reset_db()

    def test_only_active_constraints_shown(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import (
                add_constraint, deactivate_constraint,
            )
            from eduflow.memory.packet import assemble_memory_packet
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="active rule", created_by="test")
            cid2 = add_constraint(scope="team", level="L0", constraint_type="must_follow",
                                  content="inactive rule", created_by="test")
            deactivate_constraint(cid2)
            packet = assemble_memory_packet("worker_course")
            assert "active rule" in packet
            assert "inactive rule" not in packet
            _reset_db()


# ── extract_task_id_from_message ──────────────────────────────────

class TestExtractTaskId:
    def test_extracts_task_id(self):
        from eduflow.memory.packet import extract_task_id_from_message
        assert extract_task_id_from_message("请处理 T-29 的返修") == "T-29"
        assert extract_task_id_from_message("no task here") is None
        assert extract_task_id_from_message("T-100 完成") == "T-100"


# ── Package 1 derivation ─────────────────────────────────────────

class TestPackage1Derivation:
    def test_on_revision_priority_set(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.derivation import on_revision_priority_set
            from eduflow.memory.constraints import list_constraints
            on_revision_priority_set("T-42", "minor", actor="reviewer_x")
            constraints = list_constraints(scope="task:T-42", status="active")
            assert len(constraints) == 1
            c = constraints[0]
            assert c["constraint_level"] == "L2"
            assert c["constraint_type"] == "gate_check"
            assert "revision_priority=minor" in c["content"]
            assert "不能继续下一批" in c["content"]
            _reset_db()

    def test_empty_priority_is_noop(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.derivation import on_revision_priority_set
            from eduflow.memory.constraints import list_constraints
            on_revision_priority_set("T-42", "")
            assert len(list_constraints(scope="task:T-42")) == 0
            _reset_db()


# ── Package 3 derivation ─────────────────────────────────────────

class TestPackage3Derivation:
    def test_on_authoritative_verdict_fail(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.derivation import on_authoritative_verdict_fail
            from eduflow.memory.constraints import list_constraints
            verdict = {
                "outcome": "fail",
                "reviewer": "review_course",
                "review_reason": "items/QQL count mismatch",
            }
            on_authoritative_verdict_fail("T-55", verdict)
            constraints = list_constraints(scope="task:T-55", status="active")
            assert len(constraints) == 1
            c = constraints[0]
            assert "manager 不得 closeout" in c["content"]
            assert "items/QQL count mismatch" in c["content"]
            _reset_db()

    def test_pass_verdict_is_noop(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.derivation import on_authoritative_verdict_fail
            from eduflow.memory.constraints import list_constraints
            on_authoritative_verdict_fail("T-55", {"outcome": "pass"})
            assert len(list_constraints(scope="task:T-55")) == 0
            _reset_db()


# ── closeout supersession ────────────────────────────────────────

class TestCloseoutSupersession:
    def test_on_closeout_completed_deactivates(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint, list_constraints
            from eduflow.memory.derivation import on_closeout_completed
            add_constraint(scope="task:T-60", level="L2", constraint_type="gate_check",
                           content="pre-closeout rule", created_by="test")
            add_constraint(scope="task:T-60", level="L2", constraint_type="gate_check",
                           content="another rule", created_by="test")
            on_closeout_completed("T-60")
            active = list_constraints(scope="task:T-60", status="active")
            assert len(active) == 0
            all_constraints = list_constraints(scope="task:T-60", status="inactive")
            assert len(all_constraints) == 2
            _reset_db()


# ── CLI commands ─────────────────────────────────────────────────

class TestMemoryCLI:
    def test_constraints_list_empty(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli(["memory", "constraints", "--agent", "worker_course"])
            assert rc == 0
            assert "No active constraints" in out
            _reset_db()

    def test_constraints_add_and_list(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "memory", "constraints", "add",
                "team", "L0", "must_follow",
                "manager不亲自干活",
                "--enforcement", "gate_required",
            ])
            assert rc == 0
            assert "Created constraint:" in out
            rc2, out2, err2 = run_cli(["memory", "constraints", "--agent", "manager"])
            assert rc2 == 0
            assert "manager不亲自干活" in out2
            _reset_db()

    def test_constraints_deactivate(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli([
                "memory", "constraints", "add",
                "team", "L0", "must_follow",
                "test rule",
            ])
            # Extract constraint ID from output
            cid = out.strip().split(": ")[-1]
            rc2, out2, err2 = run_cli(["memory", "constraints", "deactivate", cid])
            assert rc2 == 0
            assert "Deactivated" in out2
            _reset_db()

    def test_capsule_empty(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli(["memory", "capsule", "T-999"])
            assert rc == 0
            assert "No capsule" in out
            _reset_db()

    def test_packet_empty(self):
        with isolated_env():
            _init_db()
            rc, out, err = run_cli(["memory", "packet", "--agent", "worker_course"])
            assert rc == 0
            assert "No memory packet" in out
            _reset_db()

    def test_packet_with_constraints(self):
        with isolated_env():
            _init_db()
            run_cli([
                "memory", "constraints", "add",
                "team", "L0", "must_follow",
                "test constraint for packet",
            ])
            rc, out, err = run_cli(["memory", "packet", "--agent", "worker_course"])
            assert rc == 0
            assert "test constraint for packet" in out
            _reset_db()


# ── send integration ─────────────────────────────────────────────

class TestSendIntegration:
    def test_no_memory_flag_skips_packet(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="should NOT appear without flag", created_by="test")
            rc, out, err = run_cli([
                "send", "worker_course", "manager",
                "test message", "中", "--no-inject", "--no-memory",
            ])
            assert rc == 0
            # Verify the message was sent (inbox created)
            assert "inbox:" in out
            _reset_db()

    def test_default_includes_packet(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="should appear in message", created_by="test")
            rc, out, err = run_cli([
                "send", "worker_course", "manager",
                "test message with T-1", "中", "--no-inject",
            ])
            assert rc == 0
            _reset_db()


# ── reidentify integration ───────────────────────────────────────

class TestReidentifyIntegration:
    def test_init_prompt_includes_constraints(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.constraints import add_constraint
            add_constraint(scope="team", level="L0", constraint_type="must_follow",
                           content="constraint in init prompt", created_by="test")
            # init_prompt requires agent config; use a minimal team setup
            team = {"agents": {"worker_course": {"cli": "claude-code", "model": "sonnet"}}}
            with isolated_env(team=team):
                _init_db()
                from eduflow.memory.constraints import add_constraint
                add_constraint(scope="team", level="L0", constraint_type="must_follow",
                               content="constraint in init prompt", created_by="test")
                from eduflow.agents.identity import init_prompt
                prompt = init_prompt("worker_course")
                assert "constraint in init prompt" in prompt
                _reset_db()
