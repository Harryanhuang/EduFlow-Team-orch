"""Tests for the Package 6 manager-panel minimal surface contract line.

The manager-panel renderer must append one compact line per workflow
task with the Loop Contract / Readiness summary, and must DEGRADE to a
warning when the read-models raise — it must NEVER crash panel render.
"""
from __future__ import annotations


from helpers import attr_patch, isolated_env, run_cli
from eduflow.store import (
    local_facts, operational_readiness, task_loop_contract, tasks,
)


def _make_review_queue_task(*, with_handoff: bool = True, with_heartbeat: bool = True):
    """Create a task that lands in the `awaiting_review` bucket."""
    tid = tasks.create_flow(
        "worker_course",
        "IGCSE Accounting 0452 panel-line",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.submit_for_review(tid, actor="worker_course")
    if with_handoff:
        local_facts.append_message(
            to="worker_course",
            frm="manager",
            content="please repair q1",
            priority="高",
            task_id=tid,
        )
    if with_heartbeat:
        local_facts.touch_heartbeat("worker_course")
    return tid


def test_manager_panel_appends_contract_line_per_workflow_task():
    with isolated_env():
        _make_review_queue_task()
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "contract:" in out, out
        # Compact line must include the three readiness dimensions
        for needle in ("delivery=", "productivity=", "source="):
            assert needle in out, f"missing contract field: {needle}"


def test_manager_panel_contract_line_includes_failed_check_count():
    with isolated_env():
        tid = _make_review_queue_task()
        # Reject the submission so failed_checks is non-empty; the
        # review-flow transition pushes status back to in_progress.
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="quality_not_met",
            required_fix=["fix q1"],
            blocking_files=["items/q1.md"],
        )
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "failed=" in out
        # At least one contract line should report a non-zero failed count
        contract_lines = [line for line in out.splitlines() if line.strip().startswith("contract:")]
        assert contract_lines, out
        assert any(
            "failed=" in cl and "failed=0" not in cl for cl in contract_lines
        ), contract_lines


def test_manager_panel_degrades_when_loop_contract_read_model_raises():
    """If task_loop_contract.build raises, panel must still render with a warning."""
    with isolated_env():
        _make_review_queue_task()

        def boom(_task_id):
            raise RuntimeError("simulated read-model outage")

        with attr_patch(task_loop_contract, build=boom):
            rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0, "panel must not crash"
        assert "manager panel" in out
        assert "contract: read-model unavailable" in out


def test_manager_panel_degrades_when_operational_readiness_raises():
    """If operational_readiness.build raises, panel must still render with a warning."""
    with isolated_env():
        _make_review_queue_task()

        def boom(_task_id):
            raise RuntimeError("simulated readiness outage")

        with attr_patch(operational_readiness, build=boom):
            rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0, "panel must not crash"
        assert "manager panel" in out
        # The contract line must include the warning token
        contract_lines = [line for line in out.splitlines() if line.strip().startswith("contract:")]
        assert contract_lines, out
        assert any("read-model unavailable" in cl for cl in contract_lines), contract_lines


def test_manager_panel_compact_line_shape():
    """The compact line follows the format from the plan:
    contract: phase=<phase> failed=<n> delivery=<s> productivity=<s> source=<s>
    """
    with isolated_env():
        _make_review_queue_task()
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        contract_lines = [line.strip() for line in out.splitlines() if line.strip().startswith("contract:")]
        assert contract_lines, out
        line = contract_lines[0]
        # Loose structural assertions — we only check that each field appears
        # in the line, not the exact value.
        for needle in ("phase=", "failed=", "delivery=", "productivity=", "source="):
            assert needle in line, f"missing field on contract line: {needle}: {line!r}"