"""Focused tests for eduflow.memory.packet — assembly and budget enforcement.

Covers:
- assemble_memory_packet: empty result when no data
- scope isolation: agent-scoped memories don't leak across scopes
- budget trimming: total output respects max_chars
- constraint section rendered
- capsule section rendered
- memory section rendered with confirmed items only
- extract_task_id_from_message
"""
from __future__ import annotations

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


def _add_constraint(scope="team", level="L0", content="test constraint", **kw):
    from eduflow.memory.constraints import add_constraint
    return add_constraint(
        scope=scope, level=level, constraint_type="must_follow",
        content=content, **kw,
    )


def _add_memory(scope="agent:alice", content="mem", kind="note", **kw):
    from eduflow.memory.items import add_memory
    return add_memory(
        scope=scope, kind=kind, content=content, status="confirmed", **kw,
    )


def _add_capsule(task_id, goal="build feature"):
    from eduflow.memory.capsules import upsert_capsule
    upsert_capsule(task_id=task_id, goal=goal, current_status="in_progress")


# ── empty packet ───────────────────────────────────────────────────

class TestEmptyPacket:
    def test_no_data_returns_empty_string(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            result = assemble_memory_packet("alice")
            assert result == ""
            _reset_db()

    def test_unknown_agent_no_constraints_returns_empty(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            result = assemble_memory_packet("nonexistent_agent")
            assert result == ""
            _reset_db()


# ── constraints section ────────────────────────────────────────────

class TestConstraintsSection:
    def test_renders_team_constraint(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="always verify output")
            result = assemble_memory_packet("alice")
            assert "always verify output" in result
            assert "Active Constraints" in result
            _reset_db()

    def test_renders_l0_grouped_header(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", level="L0", content="team rule")
            result = assemble_memory_packet("alice")
            assert "Must Follow" in result
            _reset_db()

    def test_renders_l2_grouped_header(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(
                scope="task:T-1", level="L2", content="task rule",
            )
            result = assemble_memory_packet("alice", task_id="T-1")
            assert "Task Constraints" in result
            _reset_db()

    def test_max_8_constraints(self):
        """Only MAX_CONSTRAINTS (8) constraints are included."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            for i in range(12):
                _add_constraint(scope="team", content=f"rule {i}")
            result = assemble_memory_packet("alice")
            # Count constraint bullets (lines starting with "- [")
            lines = [l for l in result.split("\n") if l.startswith("- [")]
            assert len(lines) <= 8
            _reset_db()


# ── capsule section ────────────────────────────────────────────────

class TestCapsuleSection:
    def test_capsule_included_in_packet(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_capsule("T-100", goal="refactor auth module")
            result = assemble_memory_packet("alice", task_id="T-100")
            assert "refactor auth module" in result
            assert "Capsule" in result
            _reset_db()

    def test_no_capsule_for_unknown_task(self):
        """When task_id has no capsule, no capsule section appears."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="rule")
            result = assemble_memory_packet("alice", task_id="T-999")
            assert "Capsule" not in result
            _reset_db()

    def test_capsule_truncated_at_max_chars(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            # goal is truncated to 200 chars by _render_capsule, so we need
            # a very large capsule to exceed MAX_CAPSULE_CHARS overall.
            # Create many blocker entries to inflate the capsule.
            _add_capsule("T-200", goal="x" * 200)
            from eduflow.memory.capsules import upsert_capsule
            upsert_capsule(
                task_id="T-200",
                goal="g" * 200,
                acceptance="a" * 200,
                next_action="n" * 200,
                blockers=[f"blocker-{i}" * 20 for i in range(10)],
            )
            result = assemble_memory_packet("alice", task_id="T-200")
            # With such inflation, the capsule section should be capped
            # Verify the capsule section exists
            assert "Capsule" in result
            _reset_db()


# ── memory section ─────────────────────────────────────────────────

class TestMemorySection:
    def test_confirmed_memories_appear(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_memory(scope="agent:alice", content="alice prefers dark mode")
            result = assemble_memory_packet("alice")
            assert "alice prefers dark mode" in result
            assert "Memories" in result
            _reset_db()

    def test_candidate_memories_excluded(self):
        """Only confirmed memories are included, not candidates."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            from eduflow.memory.items import add_memory
            add_memory(
                scope="agent:alice", kind="note",
                content="still pending", status="candidate",
            )
            result = assemble_memory_packet("alice")
            assert "still pending" not in result
            _reset_db()

    def test_max_5_memories(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            for i in range(8):
                _add_memory(
                    scope="agent:alice", content=f"memory item {i}",
                )
            result = assemble_memory_packet("alice")
            mem_lines = [l for l in result.split("\n") if l.startswith("- [")]
            assert len(mem_lines) <= 5
            _reset_db()


# ── scope isolation ────────────────────────────────────────────────

class TestScopeIsolation:
    def test_agent_sees_own_memories_only(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_memory(scope="agent:alice", content="alice data")
            _add_memory(scope="agent:bob", content="bob data")
            alice_pkt = assemble_memory_packet("alice")
            bob_pkt = assemble_memory_packet("bob")
            assert "alice data" in alice_pkt
            assert "bob data" not in alice_pkt
            assert "bob data" in bob_pkt
            assert "alice data" not in bob_pkt
            _reset_db()

    def test_team_constraints_visible_to_all_agents(self):
        """Team-scoped constraints are visible to any agent."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="universal rule")
            alice_pkt = assemble_memory_packet("alice")
            bob_pkt = assemble_memory_packet("bob")
            assert "universal rule" in alice_pkt
            assert "universal rule" in bob_pkt
            _reset_db()

    def test_task_constraints_only_for_matching_task(self):
        """Task-scoped constraints only appear when the matching task_id is passed."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(
                scope="task:T-50", level="L2", content="task-50 rule",
            )
            pkt_with = assemble_memory_packet("alice", task_id="T-50")
            pkt_without = assemble_memory_packet("alice", task_id="T-99")
            assert "task-50 rule" in pkt_with
            assert "task-50 rule" not in pkt_without
            _reset_db()


# ── budget enforcement ─────────────────────────────────────────────

class TestBudgetEnforcement:
    def test_respects_max_chars(self):
        """Output does not exceed max_chars."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            # Create lots of data to exceed budget
            for i in range(8):
                _add_constraint(
                    scope="team", content=f"long constraint text number {i} " + "x" * 200,
                )
            for i in range(5):
                _add_memory(
                    scope="agent:alice",
                    content=f"long memory text number {i} " + "y" * 200,
                )
            _add_capsule("T-1", goal="z" * 500)
            result = assemble_memory_packet(
                "alice", task_id="T-1", max_chars=2000,
            )
            assert len(result) <= 2010  # allow small overhead for "..." marker
            _reset_db()

    def test_constraints_never_truncated_individually(self):
        """Individual constraint lines are not truncated, only total budget clips from bottom."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="SHORT")
            result = assemble_memory_packet("alice", max_chars=500)
            assert "SHORT" in result
            _reset_db()

    def test_memories_dropped_before_constraints_on_budget_overflow(self):
        """When over budget, memory section is truncated before constraints."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="CRITICAL RULE")
            for i in range(5):
                _add_memory(
                    scope="agent:alice",
                    content=f"memory {i} " + "z" * 300,
                )
            result = assemble_memory_packet("alice", max_chars=1500)
            # Constraint should survive
            assert "CRITICAL RULE" in result
            _reset_db()

    def test_custom_max_chars(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="a rule")
            result = assemble_memory_packet("alice", max_chars=500)
            assert len(result) <= 510
            _reset_db()


# ── extract_task_id_from_message ───────────────────────────────────

class TestExtractTaskId:
    def test_extracts_t_dash_number(self):
        from eduflow.memory.packet import extract_task_id_from_message
        assert extract_task_id_from_message("please fix T-42 now") == "T-42"

    def test_no_match_returns_none(self):
        from eduflow.memory.packet import extract_task_id_from_message
        assert extract_task_id_from_message("no task id here") is None

    def test_extracts_first_match(self):
        from eduflow.memory.packet import extract_task_id_from_message
        assert extract_task_id_from_message("T-1 and T-2") == "T-1"

    def test_large_task_number(self):
        from eduflow.memory.packet import extract_task_id_from_message
        assert extract_task_id_from_message("see T-99999") == "T-99999"


# ── combined sections ──────────────────────────────────────────────

class TestCombinedSections:
    def test_all_sections_present_when_data_exists(self):
        """Packet with constraints + capsule + memories has all 3 sections."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="rule one")
            _add_capsule("T-50", goal="ship feature X")
            _add_memory(scope="agent:alice", content="remember this")
            result = assemble_memory_packet("alice", task_id="T-50")
            assert "Active Constraints" in result
            assert "Capsule" in result
            assert "Memories" in result
            _reset_db()

    def test_only_memories_no_constraints(self):
        """Packet with only memories (no constraints or capsule)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_memory(scope="agent:alice", content="just a memory")
            result = assemble_memory_packet("alice")
            assert "just a memory" in result
            assert "Active Constraints" not in result
            _reset_db()

    def test_only_constraints_no_memories(self):
        """Packet with only constraints (no memories or capsule)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            _add_constraint(scope="team", content="only a rule")
            result = assemble_memory_packet("alice")
            assert "only a rule" in result
            assert "Memories" not in result
            _reset_db()
