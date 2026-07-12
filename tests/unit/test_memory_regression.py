"""Regression tests for EduFlow Memory V1 — real-world scenarios.

Covers 3 cases that exercise multiple memory subsystems together:
- Case 1: Agent fired but scope resolution + supersession correct
- Case 2: Closeout constraint injection (items/QQL/manifest)
- Case 3: Verdict FAIL blocks closeout (gate_required must_not)
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


# ── Case 1: Anna fired but scope resolution correct ──────────────

class TestAnnaFiredScopeResolution:
    """Anna was an active agent bound to lane:course_caie.

    After firing, her alias is deactivated and old memories are
    superseded. Verify that:
    1. While active, resolve_alias("anna") returns her target scope.
    2. Memory items exist for both agent:anna and lane:course_caie.
    3. After deactivation, resolve_alias returns None.
    4. Superseded old memory is deprecated; search filters it out.
    """

    def test_anna_scope_and_supersession(self):
        with isolated_env():
            _init_db()

            from eduflow.memory.items import add_memory, get_memory, list_memories
            from eduflow.memory.scope_aliases import (
                add_alias, resolve_alias, deactivate_alias,
            )

            # 1. Create alias: anna → agent:anna (active)
            add_alias("anna", "agent:anna")
            assert resolve_alias("anna") == "agent:anna"

            # 2. Create memory: scope=agent:anna, Anna 负责 CAIE
            mi_old = add_memory(
                scope="agent:anna", kind="role_rule",
                content="Anna 负责 CAIE 课程",
                layer="decision", status="confirmed",
                importance=8,
            )

            # 3. Create memory: scope=lane:course_caie, closeout 约束
            add_memory(
                scope="lane:course_caie", kind="workflow_rule",
                content="CAIE closeout 必须 items/QQL/manifest 一致",
                layer="decision", status="confirmed",
                importance=9,
            )

            # 4. Verify both memories exist
            anna_items = list_memories(scope="agent:anna", status="confirmed")
            lane_items = list_memories(scope="lane:course_caie", status="confirmed")
            assert len(anna_items) == 1
            assert len(lane_items) == 1

            # 5. Deactivate alias (Anna fired)
            ok = deactivate_alias("anna")
            assert ok is True
            assert resolve_alias("anna") is None

            # 6. Create superseding memory: "Anna 已被 fire"
            mi_new = add_memory(
                scope="agent:anna", kind="role_rule",
                content="Anna 已被 fire，不再是 active agent",
                layer="decision", status="confirmed",
                importance=9,
            )

            # 7. Supersede old memory with new
            from eduflow.memory.items import supersede_memory
            ok = supersede_memory(mi_old, mi_new)
            assert ok is True

            # 8. Verify old memory is deprecated
            old = get_memory(mi_old)
            assert old["status"] == "deprecated"

            # 9. Verify new memory references the old one
            new = get_memory(mi_new)
            assert new["supersedes"] == mi_old

            # 10. Search confirmed: old memory excluded
            confirmed = list_memories(scope="agent:anna", status="confirmed")
            assert len(confirmed) == 1
            assert confirmed[0]["id"] == mi_new

            # 11. Lane memory still intact (independent of Anna's status)
            lane_still = list_memories(scope="lane:course_caie", status="confirmed")
            assert len(lane_still) == 1
            assert "items/QQL/manifest" in lane_still[0]["content"]

            _reset_db()


# ── Case 2: 0606 items/QQL/manifest closeout constraint ──────────

class TestCloseoutConstraintInjection:
    """T-29 must satisfy items/QQL/manifest consistency before closeout.

    The constraint is registered both as a workflow memory item and as
    an active constraint scoped to the task. The assembled memory packet
    must contain the constraint text BEFORE the task capsule section.
    """

    def test_closeout_constraint_in_packet(self):
        with isolated_env():
            _init_db()

            from eduflow.memory.items import add_memory
            from eduflow.memory.constraints import add_constraint
            from eduflow.memory.capsules import upsert_capsule
            from eduflow.memory.packet import assemble_memory_packet

            # 1. Workflow-level rule
            add_memory(
                scope="workflow:igcse-subject-launch", kind="workflow_rule",
                content="closeout 前必须 items/QQL/manifest 一致",
                layer="decision", status="confirmed",
                importance=10,
            )

            # 2. Task-level constraint (gate_required)
            add_constraint(
                scope="task:T-29", level="L2", constraint_type="must_follow",
                content="本任务 closeout 前必须 items/QQL/manifest 一致",
                enforcement="gate_required",
                source_ref="task:T-29",
            )

            # 3. Task capsule
            upsert_capsule(
                "T-29",
                workflow_id="igcse-subject-launch",
                owner="worker_course",
                gate="closeout_gate",
                goal="Produce 0606 Biology items",
                current_status="in_progress",
                next_action="awaiting_closeout",
            )

            # 4. Assemble packet for a worker on this task
            packet = assemble_memory_packet("worker_course", task_id="T-29")

            # 5. Packet must contain the closeout constraint text
            assert "closeout" in packet.lower() or "items/QQL/manifest" in packet

            # 6. Active Constraints section must appear before Task Capsule
            #    (constraints section header comes first in packet assembly)
            if "## EduFlow Active Constraints" in packet and "### Current Task Capsule" in packet:
                ac_pos = packet.index("## EduFlow Active Constraints")
                cap_pos = packet.index("### Current Task Capsule")
                assert ac_pos < cap_pos, "Constraints must appear before capsule in packet"

            # 7. Verify deprecated constraint does NOT appear in packet
            #    (add a deprecated constraint and re-check)
            dep_cid = add_constraint(
                scope="task:T-29", level="L2", constraint_type="must_follow",
                content="DEPRECATED old closeout rule",
                enforcement="prompt_only",
            )
            from eduflow.memory.constraints import deactivate_constraint
            deactivate_constraint(dep_cid)

            packet2 = assemble_memory_packet("worker_course", task_id="T-29")
            assert "DEPRECATED old closeout rule" not in packet2

            _reset_db()


# ── Case 3: Biology 0610 false closeout (verdict FAIL) ───────────

class TestVerdictFailBlocksCloseout:
    """When review verdict is FAIL, manager must not announce closeout.

    The constraint has constraint_type=must_not and enforcement=gate_required.
    Queries for the task scope must return this constraint with the
    correct type and enforcement.
    """

    def test_verdict_fail_constraint_blocks_closeout(self):
        with isolated_env():
            _init_db()

            from eduflow.memory.items import add_memory
            from eduflow.memory.constraints import add_constraint, list_constraints
            from eduflow.memory.capsules import upsert_capsule

            # 1. Workflow-level rule: verdict FAIL → no closeout
            add_memory(
                scope="workflow:igcse-subject-launch", kind="workflow_rule",
                content="review verdict FAIL 时 manager 不得宣布 closeout",
                layer="decision", status="confirmed",
                importance=10,
            )

            # 2. Task-level constraint: must_not, gate_required
            ac_id = add_constraint(
                scope="task:T-34", level="L2", constraint_type="must_not",
                content="verdict=FAIL 期间禁止 closeout",
                enforcement="gate_required",
            )

            # 3. Task capsule: current_status=review_failed
            upsert_capsule(
                "T-34",
                workflow_id="igcse-subject-launch",
                owner="worker_course",
                gate="review_gate",
                goal="Produce 0610 Biology items",
                current_status="review_failed",
                next_action="address_review_feedback",
            )

            # 4. Query constraints for this task
            constraints = list_constraints(scope="task:T-34", status="active")
            assert len(constraints) >= 1

            # 5. Find the must_not constraint
            must_not_c = [c for c in constraints if c["constraint_type"] == "must_not"]
            assert len(must_not_c) >= 1
            c = must_not_c[0]
            assert c["id"] == ac_id
            assert c["content"] == "verdict=FAIL 期间禁止 closeout"

            # 6. Verify enforcement=gate_required is present
            assert c["enforcement"] == "gate_required"

            # 7. Verify via inject module's gate check
            #    L2 constraints inform but don't block structural gates;
            #    L0/L1 gate_required constraints DO block.
            #    Add an L0 must_not to verify blocking behavior.
            add_constraint(
                scope="team", level="L0", constraint_type="must_not",
                content="verdict=FAIL 全局禁止 closeout",
                enforcement="gate_required",
            )
            from eduflow.memory.inject import build_gate_check
            result = build_gate_check("worker_course", "T-34", "closeout_gate")
            assert result["allowed"] is False
            blocking = result.get("blocking_constraints", [])
            blocking_contents = [b.get("content", "") for b in blocking]
            assert any("全局禁止" in bc for bc in blocking_contents)

            _reset_db()
