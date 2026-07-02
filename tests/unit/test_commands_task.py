"""Tests for `eduflow task` subcommand dispatcher."""
from __future__ import annotations

import contextlib
import io
import json

from helpers import attr_patch, env_patch, isolated_env, run_cli, tmux_patch
from eduflow.commands import say as say_cmd
from eduflow.commands import task as task_cmd
from eduflow.runtime import paths
from eduflow.store import local_facts, task_event_scanner, task_publish_gate, tasks


def _healthy_watchdog_rows():
    return [
        {"name": "router", "pid_present": True, "alive": True},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": True, "alive": True},
        {"name": "hermes-supervisor", "pid_present": True, "alive": True},
    ]


@contextlib.contextmanager
def _workflow_env(tmp, workflow_id="igcse-subject-launch"):
    root = tmp / "workflows"
    d = root / workflow_id
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        f"# workflow: {workflow_id}\n\n"
        "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n\n"
        "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    (d / "trigger.md").write_text(
        f"# trigger: {workflow_id}\n\n调用 workflow: {workflow_id}\n",
        encoding="utf-8",
    )
    (d / "roles.md").write_text(
        f"# roles: {workflow_id}\n\n## manager\n\n- Calls the workflow.\n\n## worker_builder\n\n- Maintains assets.\n",
        encoding="utf-8",
    )
    (d / "checklist.md").write_text(
        f"# checklist: {workflow_id}\n\n- [ ] manager closeout checked\n",
        encoding="utf-8",
    )
    (d / "handoff-template.md").write_text(
        f"# handoff: {workflow_id}\n\n## Manager -> worker\n\nhandoff\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        yield root


def _multi_workflow_env(tmp, workflow_ids=("igcse-subject-launch", "ap-knowledge-base-optimization")):
    """Helper that writes multiple workflow dirs under one root and patches env."""
    root = tmp / "workflows_multi"
    root.mkdir(parents=True, exist_ok=True)
    for wid in workflow_ids:
        d = root / wid
        d.mkdir(parents=True, exist_ok=True)
        (d / "README.md").write_text(
            f"# workflow: {wid}\n\n"
            "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
            "## Core Gates\n\n- dispatch_acceptance_gate\n\n"
            "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
            "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
            encoding="utf-8",
        )
        (d / "trigger.md").write_text(
            f"# trigger: {wid}\n\n调用 workflow: {wid}\n",
            encoding="utf-8",
        )
        (d / "roles.md").write_text(
            f"# roles: {wid}\n\n## manager\n\n- Calls the workflow.\n\n## worker_builder\n\n- Maintains assets.\n",
            encoding="utf-8",
        )
        (d / "checklist.md").write_text(
            f"# checklist: {wid}\n\n- [ ] manager closeout checked\n",
            encoding="utf-8",
        )
        (d / "handoff-template.md").write_text(
            f"# handoff: {wid}\n\n## Manager -> worker\n\nhandoff\n",
            encoding="utf-8",
        )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        yield root


# ── create ────────────────────────────────────────────────────────


def test_task_create_minimal():
    with isolated_env():
        rc, out, _ = run_cli(["task", "create", "worker", "do task X"])
        assert rc == 0
        assert "created T-1" in out
        rows = tasks.list_tasks()
        assert rows[0]["title"] == "do task X"
        assert rows[0]["assignee"] == "worker"


def test_task_create_with_by_and_desc():
    with isolated_env():
        run_cli(["task", "create", "worker", "task name",
              "--by", "manager", "--desc", "root cause Y"])
        t = tasks.list_tasks()[0]
        assert t["creator"] == "manager"
        assert t["description"] == "root cause Y"


def test_task_auto_ops_context_scans_all_agents_including_self():
    team = {
        "session": "S",
        "agents": {
            "manager": {"cli": "claude-code"},
            "auto_ops": {"cli": "claude-code"},
            "worker_course": {"cli": "claude-code"},
        },
    }

    def has_window(target):
        return target.window in {"manager", "auto_ops", "worker_course"}

    def capture_pane(target, lines=80):
        return {
            "manager": "bypass permissions on\ncontext: 12% (31k/262k)\n>",
            "auto_ops": "bypass permissions on\ncontext: 84% (220k/262k)\n>",
            "worker_course": "bypass permissions on\ncontext: 93% (244k/262k)\n>",
        }[target.window]

    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), tmux_patch(
        has_session=lambda session: True,
        has_window=has_window,
        capture_pane=capture_pane,
    ):
        rc, out, _ = run_cli(["task", "auto-ops-context"])

    assert rc == 0
    assert "auto_ops context snapshot" in out
    assert "agents=3 risks=2" in out
    assert "- manager: level=ok" in out
    assert "- auto_ops: level=warning pct=84%" in out
    assert "- worker_course: level=compact_recommended pct=93%" in out


def test_task_auto_ops_context_can_send_report_to_manager():
    team = {
        "session": "S",
        "agents": {
            "manager": {"cli": "claude-code"},
            "auto_ops": {"cli": "claude-code"},
        },
    }

    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), tmux_patch(
        has_session=lambda session: True,
        has_window=lambda target: target.window == "auto_ops",
        capture_pane=lambda target, lines=80: "bypass permissions on\ncontext: 91% (238k/262k)\n>",
    ):
        rc, out, _ = run_cli(["task", "auto-ops-context", "--send-manager"])
        messages = local_facts.list_messages("manager")

    assert rc == 0
    assert "sent_to_manager=true" in out
    assert len(messages) == 1
    assert messages[0]["from"] == "auto_ops"
    assert messages[0]["priority"] == "高"
    assert "auto_ops 全员 context 巡检" in messages[0]["content"]
    assert "auto_ops: level=compact_recommended" in messages[0]["content"]
    assert "eduflow compact <agent>" in messages[0]["content"]
    assert "禁止只发文字提醒" in messages[0]["content"]


def test_task_auto_ops_production_reports_team_work_state():
    team = {
        "session": "S",
        "agents": {
            "manager": {"cli": "claude-code"},
            "worker_course": {"cli": "claude-code"},
            "worker_syllabus": {"cli": "claude-code"},
            "review_course": {"cli": "claude-code"},
        },
    }

    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}):
        local_facts.upsert_status("worker_course", "进行中", "T-79 IB Guide 下载中")
        local_facts.upsert_status("review_course", "待命", "ready")
        local_facts.append_message("manager", "user", "请先处理老板消息", priority="高")
        local_facts.append_message("worker_syllabus", "manager", "请接 T-85 syllabus", priority="高")

        rc, out, _ = run_cli(["task", "auto-ops-production"])

    assert rc == 0
    assert "auto_ops production snapshot" in out
    assert "active=1" in out
    assert "waiting_manager=1" in out
    assert "- manager: state=waiting_manager" in out
    assert "- worker_course: state=active" in out
    assert "- worker_syllabus: state=waiting_worker" in out
    assert "manager_next_action=manager_read_high_priority_inbox" in out


def test_task_auto_ops_production_can_send_report_to_manager():
    team = {
        "session": "S",
        "agents": {
            "manager": {"cli": "claude-code"},
            "worker_course": {"cli": "claude-code"},
        },
    }

    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}):
        local_facts.upsert_status("worker_course", "进行中", "T-79 IB Guide 下载中")
        rc, out, _ = run_cli(["task", "auto-ops-production", "--send-manager"])
        messages = local_facts.list_messages("manager")

    assert rc == 0
    assert "sent_to_manager=true" in out
    assert len(messages) == 1
    assert messages[0]["from"] == "auto_ops"
    assert messages[0]["priority"] == "高"
    assert "auto_ops 全员生产状态巡检" in messages[0]["content"]
    assert "auto_ops production snapshot" in messages[0]["content"]
    assert "manager_next_action=no_action" in messages[0]["content"]


def test_task_create_title_with_spaces():
    with isolated_env():
        run_cli(["task", "create", "worker", "fix", "the", "broken", "thing"])
        t = tasks.list_tasks()[0]
        assert t["title"] == "fix the broken thing"


def test_task_create_missing_args_returns_one():
    with isolated_env():
        rc, _, err = run_cli(["task", "create", "worker"])
        assert rc == 1
        assert "usage:" in err


# ── update ────────────────────────────────────────────────────────


def test_task_update_status():
    with isolated_env():
        tasks.create("w", "x")
        rc, out, _ = run_cli(["task", "update", "T-1", "--status", "进行中"])
        assert rc == 0
        assert tasks.get("T-1")["status"] == "进行中"


def test_task_update_invalid_status_returns_one():
    with isolated_env():
        tasks.create("w", "x")
        rc, _, err = run_cli(["task", "update", "T-1", "--status", "bogus"])
        assert rc == 1
        assert "invalid status" in err


def test_task_update_unknown_id_returns_one():
    with isolated_env():
        rc, _, err = run_cli(["task", "update", "T-99", "--status", "已完成"])
        assert rc == 1
        assert "no such task" in err


def test_task_update_can_reassign_and_retitle():
    with isolated_env():
        tasks.create("w1", "old")
        run_cli(["task", "update", "T-1", "--assignee", "w2", "--title", "new"])
        t = tasks.get("T-1")
        assert t["assignee"] == "w2"
        assert t["title"] == "new"


def test_task_update_rejects_flow_task_legacy_mutation_path():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, _, err = run_cli(["task", "update", "T-1", "--title", "retitle me"])
        assert rc == 1
        assert "flow tasks cannot use legacy update" in err


# ── done shortcut ────────────────────────────────────────────────


def test_task_done_marks_completed():
    with isolated_env():
        tasks.create("w", "x")
        rc, out, _ = run_cli(["task", "done", "T-1"])
        assert rc == 0
        t = tasks.get("T-1")
        assert t["status"] == "已完成"
        assert t["completed_at"] is not None


# ── list / get ────────────────────────────────────────────────────


def test_task_list_empty():
    with isolated_env():
        rc, out, _ = run_cli(["task", "list"])
        assert rc == 0
        assert "no matching tasks" in out


def test_task_list_shows_count_and_each_row():
    with isolated_env():
        tasks.create("w", "first task")
        tasks.create("w", "second task")
        rc, out, _ = run_cli(["task", "list"])
        assert rc == 0
        assert "2 tasks" in out
        assert "first task" in out and "second task" in out


def test_task_list_filter_by_status_and_assignee():
    with isolated_env():
        tasks.create("alice", "a-task")
        tasks.create("bob", "b-task")
        tasks.create("alice", "a-done")
        tasks.update("T-3", status="已完成")

        rc, out, _ = run_cli(["task", "list", "--assignee", "alice"])
        assert rc == 0
        assert "a-task" in out and "a-done" in out
        assert "b-task" not in out

        rc, out, _ = run_cli(["task", "list", "--status", "已完成"])
        assert rc == 0
        assert "a-done" in out
        assert "a-task" not in out


def test_task_get_existing_renders_full_card():
    with isolated_env():
        tasks.create("w", "task one", description="d")
        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "T-1" in out and "task one" in out
        assert "desc: d" in out


def test_task_get_unknown_id_returns_one():
    with isolated_env():
        rc, _, err = run_cli(["task", "get", "T-99"])
        assert rc == 1
        assert "no such task" in err


# ── flow-create / flow-transition ───────────────────────────────


def test_task_flow_create_minimal():
    with isolated_env():
        rc, out, _ = run_cli([
            "task", "flow-create",
            "worker_course", "Draft", "Unit", "1",
            "--stage", "curriculum",
            "--owner", "worker_course",
            "--by", "manager",
        ])
        assert rc == 0
        assert "flow task T-1" in out
        t = tasks.get("T-1")
        assert t["schema_version"] == 2
        assert t["stage"] == "curriculum"
        assert t["owner"] == "worker_course"
        assert t["status"] == "queued"


def test_task_flow_create_records_workflow_id():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "flow-create",
                "worker_course", "Draft", "Unit", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
                "--workflow", "igcse-subject-launch",
            ])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        t = tasks.get("T-1")
        assert t["workflow_id"] == "igcse-subject-launch"
        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "workflow_id: igcse-subject-launch" in out
        assert "workflow_gate: dispatch_acceptance_gate" in out
        assert "workflow_gate_status: waiting_worker_acceptance" in out


def test_task_flow_create_auto_mounts_workflow_for_igcse_course_stage_alias():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, err = run_cli([
                "task", "flow-create",
                "worker_course", "IGCSE", "Chemistry", "0620", "Batch", "1",
                "--stage", "course",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        assert rc == 0, err
        assert "workflow=igcse-subject-launch" in out
        assert "auto_mounted=true" in out
        t = tasks.get("T-1")
        assert t["stage"] == "curriculum"
        assert t["workflow_id"] == "igcse-subject-launch"


def test_task_flow_create_rejects_missing_stage():
    with isolated_env():
        rc, _, err = run_cli([
            "task", "flow-create",
            "worker_course", "Draft", "Unit", "1",
            "--owner", "worker_course",
        ])
        assert rc == 1
        assert "usage:" in err


def test_task_dispatch_creates_and_assigns_flow_task():
    with isolated_env():
        rc, out, _ = run_cli([
            "task", "dispatch",
            "worker_course", "Draft", "Unit", "1",
            "--stage", "curriculum",
            "--owner", "worker_course",
            "--by", "manager",
            "--desc", "Focus on Unit 1 scope",
        ])
        assert rc == 0
        assert "dispatched T-1" in out
        t = tasks.get("T-1")
        assert t["schema_version"] == 2
        assert t["status"] == "assigned"
        assert t["owner"] == "worker_course"
        assert t["creator"] == "manager"
        assert t["description"] == "Focus on Unit 1 scope"
        events = tasks.list_task_events(task_id="T-1")
        assert [e["kind"] for e in events] == ["created", "transition"]
        assert events[-1]["after"]["status"] == "assigned"


def test_task_dispatch_records_workflow_id_and_surfaces_in_panels():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "Draft", "Unit", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
                "--workflow", "igcse-subject-launch",
            ])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        assert tasks.get("T-1")["workflow_id"] == "igcse-subject-launch"

        rc, out, _ = run_cli(["task", "list"])
        assert rc == 0
        assert "workflow_id: igcse-subject-launch" in out

        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        assert "workflow_gate_hint=review_handoff_gate" in out
        assert "workflow_next_check=workflow closeout igcse-subject-launch" in out
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        assert "workflow_gate_hint=review_handoff_gate" in out
        assert "workflow_next_check=workflow closeout igcse-subject-launch" in out


def test_task_flow_create_rejects_unknown_workflow():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, _, err = run_cli([
                "task", "flow-create",
                "worker_course", "Draft", "Unit", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--workflow", "missing-workflow",
            ])
        assert rc == 1
        assert "unknown workflow: missing-workflow" in err


def test_task_dispatch_rejects_unknown_workflow():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, _, err = run_cli([
                "task", "dispatch",
                "worker_course", "Draft", "Unit", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--workflow", "missing-workflow",
            ])
        assert rc == 1
        assert "unknown workflow: missing-workflow" in err


def test_task_legacy_flow_without_workflow_id_still_renders():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "workflow_id:" not in out


def test_task_manager_surfaces_unknown_workflow_hint_safely():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="old-workflow-id",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")

        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        assert "workflow=old-workflow-id" in out
        assert "workflow_gate_hint=unknown_workflow" in out
        assert "workflow_next_check=workflow validate / workflow list (old-workflow-id)" in out

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "workflow=old-workflow-id" in out
        assert "workflow_gate_hint=unknown_workflow" in out


def test_task_dispatch_rejects_non_manager_sender():
    with isolated_env():
        rc, _, err = run_cli([
            "task", "dispatch",
            "worker_course", "Draft", "Unit", "1",
            "--stage", "curriculum",
            "--owner", "worker_course",
            "--by", "worker_cc",
        ])
        assert rc == 1
        assert "only supports --by manager" in err


def test_task_flow_transition_happy_path():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli([
            "task", "flow-transition", "T-1",
            "--to", "assigned",
            "--actor", "manager",
        ])
        assert rc == 0
        assert "transitioned T-1" in out
        assert tasks.get("T-1")["status"] == "assigned"


def test_task_flow_transition_rejects_illegal_transition():
    with isolated_env():
        tasks.create_flow(
            "worker_builder", "Repair router",
            stage="builder", owner="worker_builder", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="blocked", actor="worker")
        rc, _, err = run_cli([
            "task", "flow-transition", "T-1",
            "--to", "delivered",
            "--actor", "manager",
        ])
        assert rc == 1
        assert "illegal status transition" in err


def test_task_review_approve_delivers_flow_task():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        rc, out, _ = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer",
            "--approve",
        ])
        assert rc == 0
        assert "reviewed T-1" in out
        row = tasks.get("T-1")
        assert row["status"] == "delivered"
        assert row["verdict"] == "approved"


def test_task_review_reject_sends_back_to_in_progress():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        rc, out, _ = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer",
            "--reject",
        ])
        assert rc == 0
        assert "outcome=reject" in out
        row = tasks.get("T-1")
        assert row["status"] == "in_progress"
        assert row["verdict"] == "rejected"


def test_task_review_manager_action_blocks_task():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        rc, out, _ = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer",
            "--manager-action",
        ])
        assert rc == 0
        assert "outcome=manager_action" in out
        row = tasks.get("T-1")
        assert row["status"] == "blocked"
        assert row["verdict"] == "manager_action"
        assert row["needs_manager_action"] is True
        assert row["blocking_reason"] == "reviewer_requested_manager_action"
        assert row["manager_action_type"] == "manager_review_needed"
        assert row["review_reason"] == "reviewer_requested_manager_action"


def test_task_review_requires_exactly_one_outcome_flag():
    with isolated_env():
        rc, _, err = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer",
        ])
        assert rc == 1
        assert "exactly one" in err


def test_task_submit_review_moves_task_to_submitted_for_review():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        rc, out, _ = run_cli([
            "task", "submit-review", "T-1",
            "--actor", "worker",
        ])
        assert rc == 0
        assert "submitted T-1 for review" in out
        row = tasks.get("T-1")
        assert row["status"] == "submitted_for_review"
        assert row["verdict"] == "pending"


def test_task_submit_review_auto_assigns_workflow_default_reviewer():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, err = run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Chemistry", "0620", "Batch", "1",
                "--stage", "course",
                "--owner", "worker_course",
                "--by", "manager",
            ])
            assert rc == 0, err
            tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
            rc, out, err = run_cli([
                "task", "submit-review", "T-1",
                "--actor", "worker_course",
            ])
        assert rc == 0, err
        row = tasks.get("T-1")
        assert row["reviewer"] == "review_course"
        assert "submitted T-1 for review" in out


def test_task_workflow_status_prints_gate_details():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Chemistry", "0620", "Batch", "1",
                "--stage", "course",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        rc, out, err = run_cli(["task", "workflow-status", "T-1"])
        assert rc == 0, err
        assert "workflow_id=igcse-subject-launch" in out
        assert "gate=dispatch_acceptance_gate" in out
        assert "gate_status=waiting_worker_acceptance" in out
        assert "default_reviewer=review_course" in out


def test_task_batch_closeout_closes_package_not_subject():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Chemistry", "0620", "Batch", "1",
                "--stage", "course",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="demo pass",
            evidence_packet={"files_sampled": ["Q-1.md"], "path_naming_result": "pass"},
        )
        rc, out, err = run_cli(["task", "batch-closeout", "T-1", "--actor", "manager"])
        assert rc == 0, err
        assert "closeout_status=batch_closeout_completed" in out
        rc, out, err = run_cli(["task", "get", "T-1"])
        assert rc == 0, err
        assert "workflow_gate: batch_closeout_gate" in out


def test_task_review_accepts_semantic_flags():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, out, _ = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer_amy",
            "--manager-action",
            "--manager-action-type", "clarify_scope",
            "--reason", "missing_scope_confirmation",
            "--summary", "Reviewer needs manager to confirm scope before rewrite.",
        ])
        assert rc == 0
        assert "outcome=manager_action" in out
        row = tasks.get("T-1")
        assert row["manager_action_type"] == "clarify_scope"
        assert row["review_reason"] == "missing_scope_confirmation"
        assert row["latest_turn_summary"] == "Reviewer needs manager to confirm scope before rewrite."


def test_task_review_accepts_scope_and_evidence_packet_flags():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Accounting 3.2",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="review_course", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, out, err = run_cli([
            "task", "review", "T-1",
            "--actor", "review_course",
            "--approve",
            "--reason", "approved_for_delivery",
            "--scope-topic", "Accounting 3.2",
            "--scope-file", "Q-3.2-01.md",
            "--scope-file", "Q-3.2-08.md",
            "--verdict-target", "Accounting 3.2 revised QA",
            "--evidence-json", json.dumps({
                "files_sampled": ["Q-3.2-01.md"],
                "items_mapping_count": 9,
                "q_ids_checked": ["Q-3.2-01"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
            }),
        ])
        assert rc == 0, err
        assert "outcome=approve" in out
        row = tasks.get("T-1")
        assert row["scope_topic"] == "Accounting 3.2"
        assert row["scope_files"] == ["Q-3.2-01.md", "Q-3.2-08.md"]
        assert row["verdict_target"] == "Accounting 3.2 revised QA"
        assert row["evidence_packet"]["items_mapping_count"] == 9

        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "scope_topic: Accounting 3.2" in out
        assert "scope_files: Q-3.2-01.md, Q-3.2-08.md" in out
        assert "verdict_target: Accounting 3.2 revised QA" in out
        assert "items_mapping_count=9" in out


def test_task_subject_inventory_and_manager_panel_show_closeout_gate():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
            scope_topic="IGCSE Business Studies 0450",
            verdict_target="IGCSE Business Studies 0450",
        )

        rc, out, err = run_cli(["task", "subject-inventory"])
        assert rc == 0, err
        assert "subject inventory" in out
        assert "IGCSE Business Studies 0450" in out
        assert "qa_count=300" in out
        assert "item_count=300" in out
        assert "closeout_status=closeout_ready" in out

        rc, panel_out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "== Subject Closeout ==" in panel_out
        assert "IGCSE Business Studies 0450" in panel_out
        assert "closeout_status=closeout_ready" in panel_out
        assert "recommended_action=manager_formal_closeout" in panel_out
        assert "closeout_gate: review_approved=true evidence_present=true qa_standard_met=true qbank_ready=false" in panel_out


def test_task_subject_inventory_and_manager_panel_show_qa_standard_and_qbank_readiness():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
                "sampled_topic_count": 10,
                "missing_topic_count": 0,
                "qbank_readiness": "qbank_ready",
            },
            scope_topic="IGCSE Business Studies 0450",
            verdict_target="IGCSE Business Studies 0450",
        )

        rc, out, err = run_cli(["task", "subject-inventory"])
        assert rc == 0, err
        assert "qa_standard=qa_standard_met" in out
        assert "qa_range=300-500" in out
        assert "qbank_readiness=qbank_ready" in out
        assert "recommended_qbank_action=approve_subject_for_qbank_seed" in out

        rc, panel_out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "qa_standard=qa_standard_met" in panel_out
        assert "qbank_readiness=qbank_ready" in panel_out


def test_task_scan_anomalies_and_panel_show_manager_action_packets():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 299,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 299,
                "item_count": 299,
            },
            scope_topic="IGCSE Business Studies 0450",
            verdict_target="IGCSE Business Studies 0450",
        )

        rc, out, err = run_cli(["task", "scan-anomalies"])
        assert rc == 0, err
        assert "action_packet:" in out
        assert "action_code=request_worker_course_expand_qa apply_allowed=true" in out
        assert "assignee=worker_course" in out
        assert "suggested_brief=" in out
        assert "closeout_gate: review_approved=true evidence_present=true qa_standard_met=false qbank_ready=false" in out
        assert "execution_plan:" in out
        assert "dry_run=true" in out
        assert "execution_policy=dry_run_only/requires_manager_confirmation/no_auto_dispatch" in out
        assert "proposed_command=eduflow task dispatch worker_course" in out

        rc, panel_out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "== Suggested Manager Actions ==" in panel_out
        assert "request_worker_course_expand_qa" in panel_out
        assert "worker_course" in panel_out
        assert "apply_allowed=true" in panel_out
        assert "apply_state=dry_run_preview" in panel_out
        assert "execution_plan:" in panel_out
        assert "proposed_brief=" in panel_out

        rc, actions_out, err = run_cli(["task", "manager-actions"])
        assert rc == 0, err
        assert "suggested manager actions" in actions_out
        assert "action_code=request_worker_course_expand_qa apply_allowed=true" in actions_out
        assert "apply_state=dry_run_preview" in actions_out
        assert "execution_plan:" in actions_out
        assert "no_auto_dispatch" in actions_out


def test_task_manager_actions_surfaces_manager_boundary_owner_and_next_action():
    with isolated_env():
        local_facts.append_log(
            "manager",
            "say",
            "已派 worker_course 启动 IGCSE Chemistry 0620 下一学科生产。",
        )

        rc, out, err = run_cli(["task", "manager-actions"])

        assert rc == 0, err
        assert "action_code=create_task_backed_dispatch_to_worker_course" in out
        assert "apply_allowed=false" in out
        assert "assignee=worker_course" in out
        assert "workflow_next_action=create_task_backed_dispatch_to_worker_course" in out
        assert "manager 口头声称已派 worker_course" in out


def test_task_manager_panel_shows_boundary_findings_as_actionable_blockers():
    with isolated_env():
        local_facts.append_log(
            "manager",
            "say",
            "我直接修复 Physics 0625 content 文件，并跑了 Python 验证确认 PASS。",
        )

        rc, out, err = run_cli(["task", "manager-panel"])

        assert rc == 0, err
        next_actions = out.split("== Next Executable Actions ==")[1]
        assert "dispatch_worker_course_for_content_repair" in next_actions
        assert "dispatch_review_course_for_verdict_or_worker_builder_for_tool_verification" in next_actions
        assert "请派 worker_course" in next_actions
        assert "派 review_course" in next_actions
        assert "dry-run only" in next_actions


def test_task_manager_closeout_marks_completed_and_panel_recommends_rollover():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
            scope_topic="IGCSE Business Studies 0450",
            verdict_target="IGCSE Business Studies 0450",
        )
        tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )

        rc, out, err = run_cli(["task", "manager-closeout", tid, "--actor", "manager", "--skip-verifier"])
        assert rc == 0, err
        assert "closeout_status=closeout_completed" in out

        rc, panel_out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "next_subject_rollover_ready" in panel_out
        assert "recommended_action: dispatch_next_subject_worker_course" in panel_out


def test_task_review_rejects_invalid_manager_action_type_flag():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, _, err = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer_amy",
            "--manager-action",
            "--manager-action-type", "invented_taxonomy",
        ])
        assert rc == 1
        assert "invalid manager_action_type" in err


def test_task_review_rejects_invalid_review_reason_flag():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, _, err = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer_amy",
            "--reject",
            "--reason", "rewrite_more",
        ])
        assert rc == 1
        assert "invalid review_reason" in err


def test_task_review_reject_disallows_manager_action_type_flag():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, _, err = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer_amy",
            "--reject",
            "--manager-action-type", "clarify_scope",
        ])
        assert rc == 1
        assert "manager_action_type is only allowed" in err


def test_task_submit_review_requires_actor():
    with isolated_env():
        rc, _, err = run_cli([
            "task", "submit-review", "T-1",
        ])
        assert rc == 1
        assert "usage:" in err


def test_task_review_queue_lists_submitted_tasks():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_admissions", "Visa Checklist",
            stage="admissions", owner="worker_admissions", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.submit_for_review("T-1", actor="worker")
        tasks.transition_flow("T-2", to_status="assigned", actor="manager")
        rc, out, _ = run_cli(["task", "review-queue"])
        assert rc == 0
        assert "awaiting review" in out
        assert "Draft Unit 1" in out
        assert "Visa Checklist" not in out


def test_task_review_queue_can_filter_by_stage():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_admissions", "Visa Checklist",
            stage="admissions", owner="worker_admissions", creator="manager",
        )
        for tid in ("T-1", "T-2"):
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.submit_for_review(tid, actor="worker")
        rc, out, _ = run_cli(["task", "review-queue", "--stage", "admissions"])
        assert rc == 0
        assert "Visa Checklist" in out
        assert "Draft Unit 1" not in out


def test_task_assign_reviewer_sets_reviewer_field():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli([
            "task", "assign-reviewer", "T-1",
            "--reviewer", "reviewer_amy",
            "--by", "manager",
        ])
        assert rc == 0
        assert "assigned reviewer reviewer_amy" in out
        assert tasks.get("T-1")["reviewer"] == "reviewer_amy"


def test_task_review_rejects_unassigned_reviewer_actor():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, _, err = run_cli([
            "task", "review", "T-1",
            "--actor", "reviewer_bob",
            "--approve",
        ])
        assert rc == 1
        assert "assigned reviewer" in err


def test_task_review_queue_can_filter_by_reviewer():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_admissions", "Visa Checklist",
            stage="admissions", owner="worker_admissions", creator="manager",
        )
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.assign_reviewer("T-2", reviewer="reviewer_bob", actor="manager")
        for tid, owner in (("T-1", "worker_course"), ("T-2", "worker_admissions")):
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor=owner)
            tasks.submit_for_review(tid, actor=owner)
        rc, out, _ = run_cli(["task", "review-queue", "--reviewer", "reviewer_bob"])
        assert rc == 0
        assert "Visa Checklist" in out
        assert "Draft Unit 1" not in out


def test_task_manager_overview_groups_key_work_buckets():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_admissions", "Visa Checklist",
            stage="admissions", owner="worker_admissions", creator="manager",
        )
        tasks.create_flow(
            "worker_builder", "Fix Router",
            stage="builder", owner="worker_builder", creator="manager",
        )
        tasks.create_flow(
            "worker_school", "School Contact",
            stage="school", owner="worker_school", creator="manager",
        )

        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")

        tasks.assign_reviewer("T-2", reviewer="reviewer_amy", actor="manager")
        tasks.transition_flow("T-2", to_status="assigned", actor="manager")
        tasks.transition_flow("T-2", to_status="in_progress", actor="worker_admissions")
        tasks.submit_for_review("T-2", actor="worker_admissions")

        tasks.transition_flow("T-3", to_status="assigned", actor="manager")
        tasks.transition_flow("T-3", to_status="in_progress", actor="worker_builder")
        tasks.transition_flow("T-3", to_status="blocked", actor="worker_builder")

        tasks.assign_reviewer("T-4", reviewer="reviewer_bob", actor="manager")
        tasks.transition_flow("T-4", to_status="assigned", actor="manager")
        tasks.transition_flow("T-4", to_status="in_progress", actor="worker_school")
        tasks.submit_for_review("T-4", actor="worker_school")
        tasks.review_flow("T-4", outcome="manager_action", actor="reviewer_bob")

        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        assert "manager overview" in out
        assert "in_progress: 1" in out
        assert "awaiting_review: 1" in out
        assert "blocked: 1" in out
        assert "manager_action: 1" in out
        assert "subject_closeout: 0" in out
        assert "Draft Unit 1" in out
        assert "Visa Checklist" in out
        assert "Fix Router" in out
        assert "School Contact" in out


def test_task_publish_check_reports_delivered_as_publishable():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "worker_course",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=true" in out
        assert "reason=delivered_to_user" in out
        assert "manager_response_type=final_result_delivered" in out
        assert "close_loop_state=open" in out


def test_task_publish_check_reports_created_as_internal():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "manager",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=true" in out
        assert "reason=worker_accepted" in out
        assert "audience_policy=worker_reassurance" in out
        assert "delivery_lane=worker_reassurance" in out
        assert "cadence_action=send_now" in out
        assert "已接单" in out


def test_task_publish_check_renders_delivered_message():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "worker_course",
            "--to", "user",
        ])
        assert rc == 0
        assert "rendered ::" in out
        assert "课程研发已完成并交付" in out
        assert "delivery_lane=manager_result" in out
        assert "manager_response_type=final_result_delivered" in out


def test_task_publish_check_keeps_manager_action_internal():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow("T-1", outcome="manager_action", actor="reviewer_amy")
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "reviewer_amy",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=false" in out
        assert "reason=worker_waiting_on_manager" in out
        assert "audience_policy=worker_reassurance" in out
        assert "delivery_lane=worker_reassurance" in out
        assert "cadence_action=delay_and_wait" in out
        assert "manager_response_type=worker_reassurance" in out
        assert "rendered ::" not in out


def test_task_publish_check_can_render_scope_pending_user_explanation():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "reviewer_amy",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=false" in out
        assert "reason=worker_waiting_on_manager" in out
        assert "audience_policy=worker_reassurance" in out
        assert "cadence_action=delay_and_wait" in out
        assert "manager_response_type=worker_reassurance" in out
        assert "已提交 manager 处理" not in out


def test_task_publish_check_can_render_direction_pending_user_explanation():
    with isolated_env():
        tasks.create_flow(
            "worker_school", "School Contact",
            stage="school", owner="worker_school", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_school")
        tasks.assign_reviewer("T-1", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_school")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_cindy",
            review_reason="missing_owner_decision",
            manager_action_type="choose_direction",
        )
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "reviewer_cindy",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=false" in out
        assert "reason=worker_waiting_on_manager" in out
        assert "audience_policy=worker_reassurance" in out
        assert "cadence_action=delay_and_wait" in out
        assert "manager_response_type=worker_reassurance" in out
        assert "已提交 manager 处理" not in out


def test_task_publish_check_renders_worker_completed_handoff_reassurance():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "worker_course",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=true" in out
        assert "reason=worker_completed_handed_to_manager" in out
        assert "audience_policy=worker_reassurance" in out
        assert "delivery_lane=worker_reassurance" in out
        assert "cadence_action=send_now" in out
        assert "已完成并交给 manager" in out


def test_task_publish_check_renders_worker_started_reassurance():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        rc, out, _ = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "worker_course",
            "--to", "user",
        ])
        assert rc == 0
        assert "publish=true" in out
        assert "reason=worker_started" in out
        assert "audience_policy=worker_reassurance" in out
        assert "delivery_lane=worker_reassurance" in out
        assert "cadence_action=send_now" in out
        assert "已开始处理" in out


def test_task_scan_anomalies_prints_surface_state_for_truth_lag():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Mathematics 0580",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        local_facts.upsert_status("worker_course", "进行中", "Chemistry 0620 首批 300 items 已完工")
        row = tasks.get(tid)
        assert row is not None
        with attr_patch(task_event_scanner, now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "status_truth_lag_detected" in out
        assert "surface_state: 正在处理当前学科" in out


def test_task_manager_panel_prints_surface_state_for_truth_lag():
    with isolated_env():
        tid = tasks.create_flow(
            "review_course", "IGCSE Mathematics 0580 review",
            stage="review", owner="worker_course", creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        local_facts.upsert_status("review_course", "进行中", "正在审 Physics 0625 旧批次")
        row = tasks.get(tid)
        assert row is not None
        with attr_patch(task_event_scanner, now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.REVIEW_STATUS_TRUTH_LAG_THRESHOLD_MS + 1):
            rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "status_truth_lag_detected" in out
        assert "surface_state: 当前学科待 review 接手" in out


def test_task_publish_check_reports_no_task_events_for_legacy_task():
    with isolated_env():
        tasks.create("worker", "legacy task")
        rc, _, err = run_cli([
            "task", "publish-check", "T-1",
            "--sender", "manager",
            "--to", "user",
        ])
        assert rc == 1
        assert "no task events" in err


def test_task_publish_scan_shows_only_publishable_by_default():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-scan"])
        assert rc == 0
        assert "publish=true" in out
        assert "reason=delivered_to_user" in out
        assert "reason=worker_accepted" in out
        assert "reason=worker_started" in out
        assert "manager_response_type=final_result_delivered" in out
        assert "close_loop_state=open" in out
        assert "rendered ::" in out
        assert "internal_assignment" not in out


def test_task_publish_scan_does_not_repeat_worker_started_on_reviewer_assignment():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="review_course", actor="manager")
        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent"])
        assert rc == 0
        assert out.count("reason=worker_started") == 1
        assert "cadence_reason=reviewer_assignment_during_progress" in out


def test_task_publish_run_send_allows_worker_acceptance_and_start_reassurance():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(say_cmd, main=fake_say):
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        rc, out, _ = run_cli(["task", "publish-run", "--send"])
        assert rc == 0
        assert any("已接单" in call[1] for call in calls)
        assert any("已开始处理" in call[1] for call in calls)
        assert "sent without advancing cursor" in out


def test_task_dispatch_auto_publishes_worker_acceptance_tick():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(runtime_config={"chat_id": "oc_demo"}), attr_patch(say_cmd, main=fake_say):
        rc, out, _ = run_cli([
            "task", "dispatch",
            "worker_course", "IGCSE Mathematics 0580",
            "--stage", "curriculum",
            "--owner", "worker_course",
        ])
        assert rc == 0
        assert "auto stage reassurance published" in out
        assert len(calls) == 1
        assert calls[0][0] == "worker_course"
        assert "已接单" in calls[0][1]


def test_task_flow_transition_auto_publishes_worker_start_without_repeating_acceptance():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(runtime_config={"chat_id": "oc_demo"}), attr_patch(say_cmd, main=fake_say):
        run_cli([
            "task", "dispatch",
            "worker_course", "IGCSE Mathematics 0580",
            "--stage", "curriculum",
            "--owner", "worker_course",
        ])
        rc, out, _ = run_cli([
            "task", "flow-transition", "T-1",
            "--to", "in_progress",
            "--actor", "worker_course",
        ])
        assert rc == 0
        assert "auto stage reassurance published" in out
        assert len(calls) == 2
        assert "已接单" in calls[0][1]
        assert "已开始处理" in calls[1][1]


def test_task_submit_review_auto_publishes_worker_handoff_tick():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(runtime_config={"chat_id": "oc_demo"}), attr_patch(say_cmd, main=fake_say):
        run_cli([
            "task", "dispatch",
            "worker_course", "IGCSE Mathematics 0580",
            "--stage", "curriculum",
            "--owner", "worker_course",
        ])
        run_cli([
            "task", "flow-transition", "T-1",
            "--to", "in_progress",
            "--actor", "worker_course",
        ])
        rc, out, _ = run_cli([
            "task", "submit-review", "T-1",
            "--actor", "worker_course",
        ])
        assert rc == 0
        assert "auto stage reassurance published" in out
        assert len(calls) == 3
        assert "已完成并交给 manager" in calls[2][1]


def test_task_auto_publish_tick_does_not_advance_publish_cursor():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(runtime_config={"chat_id": "oc_demo"}), attr_patch(say_cmd, main=fake_say):
        run_cli([
            "task", "dispatch",
            "worker_course", "IGCSE Mathematics 0580",
            "--stage", "curriculum",
            "--owner", "worker_course",
        ])
        assert not paths.task_publish_cursor_file().exists()
        explanation_state = task_event_scanner.read_explanation_state()
        assert "T-1::worker_accepted" in explanation_state.get("sent", {})
        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent"])
        assert rc == 0
        assert "reason=internal_assignment" in out


def test_task_publish_scan_persists_close_loop_after_advance():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent", "--advance"])
        assert rc == 0
        assert "reason=delivered_to_user" in out
        assert "close_loop_state=manager_result_closed" in out
        assert "close_loop_reason=final_result_delivered" in out


def test_task_publish_scan_can_include_silent_and_advance():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        rc, out, _ = run_cli([
            "task", "publish-scan", "--include-silent", "--advance",
        ])
        assert rc == 0
        assert "worker_accepted" in out
        assert "internal_assignment" in out
        assert "advanced task publish cursor" in out

        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent"])
        assert rc == 0
        assert "no matching unpublished task events" in out


def test_task_publish_scan_shows_delay_cadence_for_fresh_waiting_on_manager():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent"])
        assert rc == 0
        assert "reason=worker_waiting_on_manager" in out
        assert "cadence_action=delay_and_wait" in out


def test_task_publish_scan_merges_completed_handoff_when_result_ready():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-scan", "--include-silent"])
        assert rc == 0
        assert "reason=worker_completed_handed_to_manager" in out
        assert "cadence_action=merge_with_next_update" in out
        assert "reason=delivered_to_user" in out


def test_task_publish_run_dry_run_previews_without_advancing():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-run"])
        assert rc == 0
        assert "preview summary ::" in out
        assert "preview result " in out
        assert "reason=delivered_to_user" in out
        assert "课程研发已完成并交付" in out
        assert "dry-run only" in out

        rc, out, _ = run_cli(["task", "publish-run"])
        assert rc == 0
        assert "no publishable task events" in out


def test_task_publish_run_send_and_advance_calls_say_once():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(say_cmd, main=fake_say):
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-run", "--send", "--advance"])
        assert rc == 0
        assert len(calls) == 4
        assert "本轮已完成 1 项正式交付" in calls[0][1]
        assert any("已开始处理" in call[1] for call in calls[1:])
        assert any("已接单" in call[1] for call in calls[1:])
        assert any("已完成并交付" in call[1] for call in calls[1:])
        assert "advanced task publish cursor" in out

        rc, out, _ = run_cli(["task", "publish-run"])
        assert rc == 0
        assert "no unpublished task events" in out


def test_task_publish_run_limits_to_latest_three_publishable_items():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(say_cmd, main=fake_say):
        for i in range(4):
            tid = tasks.create_flow(
                "worker_course",
                f"Draft Unit {i + 1}",
                stage="curriculum",
                owner="worker_course",
                creator="manager",
            )
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker")
            tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
            tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        rc, out, _ = run_cli(["task", "publish-run", "--send"])
        assert rc == 0
        assert "sent without advancing cursor" in out
    assert len(calls) == 4
    body_messages = [c[1] for c in calls[1:]]
    assert any("Draft Unit 4" in msg for msg in body_messages)
    assert all("Draft Unit 1" not in msg for msg in body_messages)


def test_task_publish_run_rejects_advance_without_send():
    with isolated_env():
        rc, _, err = run_cli(["task", "publish-run", "--advance"])
        assert rc == 1
        assert "--advance requires --send" in err


def test_task_scan_anomalies_reports_empty_when_clean():
    with isolated_env():
        rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "no manager-facing task anomalies" in out or "runtime_visibility_unhealthy" in out


def test_task_scan_anomalies_reports_flagged_rows():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        row = tasks.get("T-1")
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "manager-facing task anomalies" in out
        assert "stale_task" in out
        assert "why:" in out
        assert "evidence:" in out
        assert "recommended_action:" in out


def test_task_scan_anomalies_can_surface_suppress_duplicate_update():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        task_event_scanner.scan_publish_decisions(advance=True)
        row = tasks.get("T-1")
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "recommended_action: suppress_duplicate_update" in out


def test_task_scan_anomalies_can_surface_delay_and_wait_for_fresh_waiting():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        row = tasks.get("T-1")
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_publish_gate.WORKER_WAITING_DELAY_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "recommended_action: request_manager_decision" in out


def test_task_manager_panel_reports_empty_sections():
    with isolated_env():
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "manager panel" in out
        assert "== Task Buckets ==" in out
        assert "in progress: 0" in out
        assert "awaiting review: 0" in out
        assert "blocked: 0" in out
        assert "needs manager action: 0" in out
        assert "== Anomalies (non-actionable) ==" in out
        assert "none" in out
        assert "== User-Ready Updates ==" in out


def test_task_supervisor_check_reports_healthy_silent_state():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        from eduflow.store import local_facts

        local_facts.touch_heartbeat("manager")
        rc, out, _ = run_cli(["task", "supervisor-check"])
        assert rc == 0
        assert "supervisor check" in out
        assert "health_status=healthy_silent" in out
        assert "recommended_action=no_action" in out
        assert "user_message :: silent" in out
        assert "state_stale=false" in out
        assert "state_age_ms=0" in out


def test_task_supervisor_check_surfaces_worker_context_guard():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.append_message(
            "worker_course",
            "manager",
            "P0: pause expansion and read inbox before producing more Physics 0625.",
            priority="高",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "100% context used; continuing production Physics 0625 Batch 8 topic 8.3",
        )
        local_facts.touch_heartbeat("manager")

        rc, out, _ = run_cli(["task", "supervisor-check"])

        assert rc == 0
        assert "worker_context_exhausted" in out
        assert "worker_high_priority_unacked_while_producing" in out
        assert "worker_context_risk" in out
        assert "restart_worker_runtime" in out
        assert "interrupt_old_context_and_read_inbox" in out


def test_task_manager_panel_prints_context_guard_recovery_fields():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "P0: pause expansion and read inbox before producing more Physics 0625.",
            priority="高",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "context window exceeds limit; continuing production Physics 0625 Batch 8 topic 8.4",
        )

        rc, out, _ = run_cli(["task", "manager-panel"])

        assert rc == 0
        assert "worker_context_exhausted" in out
        assert "worker_high_priority_unacked_while_producing" in out
        assert "affected_agent=worker_course" in out
        assert f"message_id={msg_id}" in out
        assert "allow_continue_original_task=false" in out
        assert "recommended_action: restart_worker_runtime" in out
        assert "recommended_action: interrupt_old_context_and_read_inbox" in out


def test_task_supervisor_check_surfaces_stale_state_file_without_overwriting():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        task_event_scanner.write_supervisor_state({
            "last_check_at": 100,
            "last_health_status": "escalated_failure",
            "last_primary_reason": "runtime_unhealthy",
            "consecutive_issue_count": 4,
            "last_repair_at": 100,
            "last_alert_at": 100,
        })
        current_now = 10_000
        with attr_patch(task_event_scanner, now_ms=lambda: current_now), attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.touch_heartbeat("manager")
            rc, out, _ = run_cli(["task", "supervisor-check"])
        assert rc == 0
        assert "health_status=healthy_silent" in out
        assert "primary_reason=manager_recently_active" in out
        assert "state_stale=true" in out
        assert "state_age_ms=9900" in out


def test_task_supervisor_check_can_advance_state_for_runtime_issue():
    with isolated_env():
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: task_event_scanner.SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "supervisor-check", "--advance"])
        assert rc == 0
        assert "health_status=repair_needed" in out
        assert "primary_reason=runtime_unhealthy" in out
        assert "recommended_action=trigger_supervisor_repair" in out
        assert "user_alert_action=alert_user_repair_started" in out
        assert "repair_channel=hermes_supervision_group" in out
        assert "advanced supervisor state" in out


def test_task_supervisor_check_flags_stale_manager_high_priority_unread():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        local_facts.append_message(
            "manager",
            "auto_ops",
            "Accounting 3.4 已完整产出，请派 review_course 复核",
            priority="高",
        )
        created = local_facts.list_messages("manager", unread_only=True)[0]["created_at"]
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: created + task_event_scanner.SUPERVISOR_MANAGER_HIGH_PRIORITY_UNREAD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "supervisor-check"])
    assert rc == 0
    assert "health_status=repair_needed" in out
    assert "primary_reason=manager_high_priority_unread" in out
    assert "recommended_action=trigger_manager_recheck" in out
    assert "user_alert_action=alert_user_repair_started" in out
    assert "manager_high_priority_unread" in out


def test_task_supervisor_check_flags_stale_auto_report_to_manager():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        local_facts.append_message(
            "manager",
            "auto_ops",
            "manager_unconsumed: Accounting 3.4 review 已派但未看到 verdict，请 manager recheck",
            priority="中",
        )
        created = local_facts.list_messages("manager", unread_only=True)[0]["created_at"]
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: created + task_event_scanner.SUPERVISOR_MANAGER_AUTO_REPORT_UNREAD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "supervisor-check"])
    assert rc == 0
    assert "health_status=repair_needed" in out
    assert "primary_reason=manager_unconsumed_auto_report" in out
    assert "recommended_action=trigger_manager_recheck" in out


def test_task_supervisor_check_keeps_supervision_group_boundary_visible():
    with isolated_env():
        rc, out, _ = run_cli(["task", "supervisor-check"])
        assert rc == 0
        assert "repair_channel=hermes_supervision_group" in out


def test_task_supervisor_check_can_send_to_supervisor_channel():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(say_cmd, main=fake_say):
        rc, out, _ = run_cli(["task", "supervisor-check", "--send"])
    assert rc == 0
    assert "sent to supervisor channel" in out
    assert len(calls) == 1
    assert "--channel" in calls[0]
    assert "supervisor" in calls[0]


def test_task_supervisor_check_json_emits_structured_payload():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        rc, out, _ = run_cli(["task", "supervisor-check", "--json"])
    assert rc == 0
    data = json.loads(out)
    assert data["health_status"] == "healthy_silent"
    assert data["repair_channel"] == "hermes_supervision_group"
    assert data["sent_to_supervisor_channel"] is False
    assert isinstance(data["auto_summary_reasons"], list)


def test_task_supervisor_check_surfaces_runtime_guard_and_process_state():
    with isolated_env():
        local_facts.touch_heartbeat("manager")
        paths.runtime_guard_state_file().parent.mkdir(parents=True, exist_ok=True)
        paths.runtime_guard_state_file().write_text(json.dumps({
            "agents": {
                "worker_course": {
                    "escalation_needed": True,
                    "last_failure_reason": "rate_limit",
                    "last_switch_outcome": "fallback_exhausted",
                    "escalation_reason": "fallback_chain_exhausted",
                    "from_runtime": "primary",
                    "to_runtime": "backup",
                }
            }
        }), encoding="utf-8")
        rc, out, _ = run_cli(["task", "supervisor-check"])
        assert rc == 0
        assert "runtime_guard:" in out
        assert "worker_course :: failure=rate_limit" in out
        assert "outcome=fallback_exhausted" in out
        assert "escalation=fallback_chain_exhausted" in out
        assert "supervisor_processes:" in out


def test_task_supervisor_check_send_json_marks_supervisor_delivery():
    calls = []

    def fake_say(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(say_cmd, main=fake_say):
        rc, out, _ = run_cli(["task", "supervisor-check", "--send", "--json"])
    assert rc == 0
    data = json.loads(out)
    assert data["sent_to_supervisor_channel"] is True
    assert len(calls) == 1


def test_task_manager_panel_combines_overview_anomalies_and_publishable():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_admissions", "Visa Checklist",
            stage="admissions", owner="worker_admissions", creator="manager",
        )
        tasks.create_flow(
            "worker_school", "School Contact",
            stage="school", owner="worker_school", creator="manager",
        )

        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer_amy")

        tasks.transition_flow("T-2", to_status="assigned", actor="manager")
        tasks.transition_flow("T-2", to_status="in_progress", actor="worker_admissions")
        tasks.assign_reviewer("T-2", reviewer="reviewer_bob", actor="manager")
        for _ in range(2):
            tasks.submit_for_review("T-2", actor="worker_admissions")
            tasks.review_flow("T-2", outcome="reject", actor="reviewer_bob")

        tasks.transition_flow("T-3", to_status="assigned", actor="manager")
        tasks.transition_flow("T-3", to_status="in_progress", actor="worker_school")
        tasks.assign_reviewer("T-3", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-3", actor="worker_school")
        tasks.review_flow(
            "T-3",
            outcome="manager_action",
            actor="reviewer_cindy",
            review_reason="missing_owner_decision",
            latest_turn_summary="Reviewer needs manager to choose between two school-contact options.",
            manager_action_type="choose_direction",
        )

        row = tasks.get("T-3")
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.MANAGER_ACTION_THRESHOLD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "manager panel" in out
        assert "needs manager action: 1" in out
        assert "Draft Unit 1" in out
        assert "School Contact" in out
        assert "reject_resubmit_loop" in out
        assert "manager_action_overdue" in out
        assert "待经理处理：拍板下一步方向；原因：存在分歧，待经理拍板" in out
        assert "recommended_action: request_manager_decision" in out
        assert "latest_turn_summary=Reviewer needs manager to choose between two school-contact options." in out
        assert "本轮已完成" in out
        assert "results:" in out
        assert "reassurances:" in out
        assert "final_result_delivered" in out
        assert "课程研发已完成并交付" in out


def test_task_manager_overview_and_panel_surface_subject_closeout_pending():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "IGCSE Accounting 0452",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Batch 1 已通过；剩余 Batch 2-10 待推进",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="approve",
            actor="reviewer_cindy",
            latest_turn_summary="Batch 10 最终批已审核通过，全部 10 批次、35 sub-topics 正式完成。",
            verdict_target="IGCSE Accounting 0452",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        assert "subject_closeout: 1" in out
        assert "学科已完成，待manager 正式收口 / builder 复盘沉淀 / qbank 学科级复核 / 下一学科决策" in out

        rc, panel_out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "subject closeout pending: 1" in panel_out
        assert "subject_closeout_pending" in panel_out
        assert "recommended_action: close_subject_and_dispatch_followups" in panel_out


def test_task_manager_panel_aggregate_headline_prioritizes_results_over_reassurance():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.create_flow(
            "worker_builder", "Fix Router",
            stage="builder", owner="worker_builder", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.transition_flow("T-1", to_status="submitted_for_review", actor="worker_course")
        tasks.transition_flow("T-1", to_status="delivered", actor="reviewer")
        tasks.transition_flow("T-2", to_status="assigned", actor="manager")
        tasks.transition_flow("T-2", to_status="in_progress", actor="worker_builder")
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "已完成 1 项正式交付" in out
        assert "results:" in out
        assert "reassurances:" in out


def test_task_manager_overview_prints_manager_summary_from_taxonomy():
    with isolated_env():
        tasks.create_flow(
            "worker_school", "School Contact",
            stage="school", owner="worker_school", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_school")
        tasks.assign_reviewer("T-1", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_school")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_cindy",
            review_reason="missing_owner_decision",
            manager_action_type="choose_direction",
        )
        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        assert "manager_summary=待经理处理：拍板下一步方向；原因：存在分歧，待经理拍板" in out


def test_task_manager_overview_sorts_by_latest_meaningful_update():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Older Task",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.create_flow(
            "worker_course", "Newer Task",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow("T-2", to_status="assigned", actor="manager")
        tasks.transition_flow("T-2", to_status="in_progress", actor="worker_course")
        rc, out, _ = run_cli(["task", "manager-overview"])
        assert rc == 0
        older_idx = out.find("Older Task")
        newer_idx = out.find("Newer Task")
        assert newer_idx != -1 and older_idx != -1
        assert newer_idx < older_idx


def test_task_scan_anomalies_uses_taxonomy_driven_explanations():
    with isolated_env():
        tasks.create_flow(
            "worker_school", "School Contact",
            stage="school", owner="worker_school", creator="manager",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_school")
        tasks.assign_reviewer("T-1", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_school")
        tasks.review_flow(
            "T-1",
            outcome="manager_action",
            actor="reviewer_cindy",
            review_reason="missing_owner_decision",
            manager_action_type="choose_direction",
        )
        row = tasks.get("T-1")
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.MANAGER_ACTION_THRESHOLD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "待经理处理：拍板下一步方向；原因：存在分歧，待经理拍板" in out
        assert "review_reason=存在分歧，待经理拍板" in out
        assert "recommended_action: request_manager_decision" in out


def test_task_get_flow_task_renders_stage_owner_and_verdict():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "stage: curriculum" in out
        assert "owner: worker_course" in out
        assert "verdict: pending" in out
        assert "latest_turn_summary: Task created and queued." in out
        assert "current_summary: Task created and queued." in out


def test_task_list_flow_task_renders_stage_and_verdict():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "Draft Unit 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, _ = run_cli(["task", "list"])
        assert rc == 0
        assert "stage: curriculum" in out
        assert "verdict: pending" in out
        assert "current_summary: Task created and queued." in out


def test_task_get_flow_task_labels_stale_dispatch_text_as_initial_brief():
    with isolated_env():
        tasks.create_flow(
            "worker_course", "IGCSE Accounting 0452",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Batch 1 已通过；剩余 Batch 2-10 待推进",
        )
        tasks.transition_flow("T-1", to_status="assigned", actor="manager")
        tasks.transition_flow("T-1", to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer("T-1", reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review("T-1", actor="worker_course")
        tasks.review_flow(
            "T-1",
            outcome="approve",
            actor="reviewer_cindy",
            latest_turn_summary="Batch 10 最终批已审核通过，可由 manager 收口。",
        )
        rc, out, _ = run_cli(["task", "get", "T-1"])
        assert rc == 0
        assert "initial_brief: Batch 1 已通过；剩余 Batch 2-10 待推进" in out
        assert "current_summary: 学科已完成，待manager 正式收口 / builder 复盘沉淀 / qbank 学科级复核 / 下一学科决策；已审核通过，可对外同步；Batch 10 最终批已审核通过，可由 manager 收口。" in out
        assert "subject_followups: manager_closeout_pending, builder_retro_pending, qbank_refresh_pending, next_subject_decision_pending" in out


def _approved_subject_for_apply(title="IGCSE Business Studies 0450", evidence=None):
    tid = tasks.create_flow(
        "worker_course",
        title,
        stage="curriculum",
        owner="worker_course",
        creator="manager",
        description="Subject final batch 正式完成",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    # Package 7 (Revision-First Gate): provide the required evidence
    # packet fields by default. Callers can still override specific
    # fields (e.g. pass evidence={} to test the closeout-block path).
    # When evidence is explicitly an empty dict, use an empty packet
    # to simulate the "no evidence provided" scenario.
    if evidence is not None and evidence == {}:
        packet = {}
    else:
        packet = {
            "workflow_id": "igcse-subject-launch",
            "task_id": tid,
            "batch_range": "1-3",
            "items_count": 300,
            "qql_count": 300,
            "qa_count": 300,
            "item_count": 300,
            "manifest_evidence": "manifest_covered",
        }
        if evidence:
            packet.update(evidence)
    tasks.review_flow(
        tid,
        outcome="approve",
        actor="review_course",
        review_reason="approved_for_delivery",
        latest_turn_summary="全部 10 批次正式完成，review approved.",
        evidence_packet=packet,
        scope_topic=title,
        verdict_target=title,
    )
    return tid


def test_task_manager_action_apply_defaults_to_dry_run_preview():
    with isolated_env():
        tid = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 299,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 299,
        })
        before = len(tasks.list_tasks())
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "request_worker_course_expand_qa",
            "--subject-id", tid,
        ])
        assert rc == 0, err
        assert "apply_result: applied=false" in out
        assert "apply_mode=dry_run" in out
        assert "apply_reason=dry_run_preview" in out
        assert "created_task_id=-" in out
        assert "updated_subject_id=-" in out
        assert "existing_task_id=-" in out
        assert "apply_summary=" in out
        assert "execution_plan:" in out
        assert len(tasks.list_tasks()) == before


def test_task_manager_action_apply_confirm_creates_internal_worker_course_followup_idempotently():
    with isolated_env():
        tid = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 299,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 299,
        })
        auto_ticks = []
        say_calls = []

        def fake_tick(task_id):
            auto_ticks.append(task_id)

        def fake_say(argv):
            say_calls.append(argv)
            return 0

        event_count = len(tasks.list_task_events(limit=100))
        with (
            attr_patch(task_cmd, _auto_publish_stage_tick=fake_tick),
            attr_patch(say_cmd, main=fake_say),
        ):
            rc, out, err = run_cli([
                "task", "manager-action-apply",
                "request_worker_course_expand_qa",
                "--subject-id", tid,
                "--confirm",
            ])
        assert rc == 0, err
        assert "applied=true" in out
        assert "apply_mode=confirmed" in out
        assert "created_task_id=T-2" in out
        assert "updated_subject_id=-" in out
        assert "existing_task_id=-" in out
        followup = tasks.get("T-2")
        assert followup["assignee"] == "worker_course"
        assert followup["status"] == "assigned"
        assert "Current qa_count=299, item_count=299" in followup["description"]
        assert "Standard range: 300-500 QA/item" in followup["description"]
        assert "Gap: 缺 1 个" in followup["description"]
        assert "After repair, submit back to review_course" in followup["description"]
        assert len(tasks.list_task_events(limit=100)) == event_count
        assert auto_ticks == []
        assert say_calls == []

        rc, again, err = run_cli([
            "task", "manager-action-apply",
            "request_worker_course_expand_qa",
            "--subject-id", tid,
            "--confirm",
        ])
        assert rc == 0, err
        assert "applied=false" in again
        assert "apply_reason=already_exists" in again
        assert "existing_task_id=T-2" in again
        assert len(tasks.list_tasks()) == 2

        rc, actions, err = run_cli(["task", "manager-actions"])
        assert rc == 0, err
        assert "apply_status:" in actions
        assert "apply_state=confirmed_state" in actions
        assert "already_exists" in actions


def test_task_manager_action_apply_recreates_followup_after_existing_terminal():
    with isolated_env():
        tid = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 299,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 299,
        })
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "request_worker_course_expand_qa",
            "--subject-id", tid,
            "--confirm",
        ])
        assert rc == 0, err
        assert "created_task_id=T-2" in out
        tasks.transition_flow("T-2", to_status="in_progress", actor="worker_course")
        tasks.transition_flow("T-2", to_status="submitted_for_review", actor="worker_course")
        tasks.transition_flow("T-2", to_status="delivered", actor="reviewer")

        rc, again, err = run_cli([
            "task", "manager-action-apply",
            "request_worker_course_expand_qa",
            "--subject-id", tid,
            "--confirm",
        ])
        assert rc == 0, err
        assert "applied=true" in again
        assert "created_task_id=T-3" in again
        assert "existing_task_id=-" in again
        assert tasks.get("T-3")["status"] == "assigned"


def test_task_manager_action_apply_confirm_closeout_without_publish_event():
    with isolated_env():
        tid = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 300,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 300,
            "item_count": 300,
            # Package 7 (Revision-First Gate): the new closeout gate
            # requires the worker evidence packet to also carry the
            # six REQUIRED_EVIDENCE_PACKET_FIELDS. These pre-existing
            # closeout-flow tests are about idempotency and event
            # count, NOT about evidence gap behavior, so we provide
            # a complete packet here.
            "workflow_id": "igcse-subject-launch",
            "task_id": "T-1",
            "batch_range": "1-3",
            "items_count": 300,
            "qql_count": 300,
            "manifest_evidence": "manifest_covered",
        })
        event_count = len(tasks.list_task_events(limit=100))
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "manager_formal_closeout",
            "--subject-id", tid,
            "--confirm",
            "--skip-verifier",
        ])
        assert rc == 0, err
        assert "applied=true" in out
        assert "apply_reason=closeout_completed" in out
        assert "updated_subject_id=T-1" in out
        assert tasks.subject_closeout_status(tasks.get(tid))["closeout_status"] == "closeout_completed"
        assert len(tasks.list_task_events(limit=100)) == event_count


def test_task_manager_action_apply_closeout_preconditions_and_idempotency():
    with isolated_env():
        blocked = _approved_subject_for_apply(evidence={})
        event_count = len(tasks.list_task_events(limit=100))
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "manager_formal_closeout",
            "--subject-id", blocked,
            "--confirm",
            "--skip-verifier",
        ])
        assert rc == 0, err
        assert "applied=false" in out
        assert "apply_reason=precondition_failed" in out
        assert "subject closeout not ready" in out
        assert tasks.subject_closeout_status(tasks.get(blocked))["closeout_status"] != "closeout_completed"
        assert len(tasks.list_task_events(limit=100)) == event_count

        ready = _approved_subject_for_apply(
            title="IGCSE Chemistry 0620",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
                # Package 7 (Revision-First Gate): see note in
                # test_task_manager_action_apply_confirm_closeout_without_publish_event.
                "workflow_id": "igcse-subject-launch",
                "task_id": "T-2",
                "batch_range": "1-3",
                "items_count": 300,
                "qql_count": 300,
                "manifest_evidence": "manifest_covered",
            },
        )
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "manager_formal_closeout",
            "--subject-id", ready,
            "--confirm",
            "--skip-verifier",
        ])
        assert rc == 0, err
        assert "applied=true" in out
        closed_event_count = len(tasks.list_task_events(limit=100))
        closed_at = tasks.get(ready)["manager_closed_out_at"]
        rc, again, err = run_cli([
            "task", "manager-action-apply",
            "manager_formal_closeout",
            "--subject-id", ready,
            "--confirm",
            "--skip-verifier",
        ])
        assert rc == 0, err
        assert "applied=false" in again
        assert "apply_reason=already_applied" in again
        assert tasks.get(ready)["manager_closed_out_at"] == closed_at
        assert len(tasks.list_task_events(limit=100)) == closed_event_count


def test_task_manager_action_apply_confirm_review_and_qbank_followups():
    with isolated_env():
        missing = _approved_subject_for_apply(evidence={})
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "request_review_course_file_evidence",
            "--subject-id", missing,
            "--confirm",
        ])
        assert rc == 0, err
        assert "created_task_id=T-2" in out
        review_task = tasks.get("T-2")
        assert review_task["assignee"] == "review_course"
        assert "files_sampled=" in review_task["description"]
        assert "q_ids_checked=" in review_task["description"]
        assert "sampled_topic_count=" in review_task["description"]
        assert "missing_topic_count=" in review_task["description"]
        assert "path_naming_result=" in review_task["description"]
        assert "qbank_readiness=" in review_task["description"]
        assert "不直接改 verdict" in review_task["description"]

        qbank = _approved_subject_for_apply(
            title="IGCSE Chemistry 0620",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
                "sampled_topic_count": 8,
                "missing_topic_count": 0,
                "qbank_readiness": "qbank_blocked_missing_question_directions",
            },
        )
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "request_qbank_readiness_check",
            "--subject-id", qbank,
            "--confirm",
        ])
        assert rc == 0, err
        assert "created_task_id=T-4" in out
        qbank_task = tasks.get("T-4")
        assert qbank_task["assignee"] == "worker_qbank"
        assert qbank_task["stage"] == "qbank"
        assert "Check mapping completeness." in qbank_task["description"]
        assert "Check question directions." in qbank_task["description"]
        assert "Return a final qbank_readiness verdict." in qbank_task["description"]


def test_task_manager_action_apply_confirm_rollover_creates_next_curriculum_task():
    with isolated_env():
        done = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 300,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 300,
            "item_count": 300,
        })
        tasks.manager_closeout_subject(done, actor="manager", skip_subject_verifier=True)
        next_tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "dispatch_next_subject_worker_course",
            "--subject-id", next_tid,
            "--confirm",
        ])
        assert rc == 0, err
        assert "created_task_id=T-3" in out
        rollover = tasks.get("T-3")
        assert rollover["assignee"] == "worker_course"
        assert rollover["stage"] == "curriculum"
        assert "先做计划" in rollover["description"]
        assert "对齐 topic" in rollover["description"]
        assert "目标 300-500 QA/item" in rollover["description"]
        assert "完成后交 review_course" in rollover["description"]


def test_task_manager_action_apply_dry_run_only_actions_do_not_create_tasks():
    with isolated_env():
        tid = _approved_subject_for_apply(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 300,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 300,
            "item_count": 300,
            "sampled_topic_count": 10,
            "missing_topic_count": 0,
            "qbank_readiness": "qbank_ready",
        })
        before = len(tasks.list_tasks())
        rc, out, err = run_cli([
            "task", "manager-action-apply",
            "approve_subject_for_qbank_seed",
            "--subject-id", tid,
            "--confirm",
        ])
        assert rc == 0, err
        assert "applied=false" in out
        assert "apply_reason=not_allowed_dry_run_only" in out
        assert "apply_state=confirmed_state" in out
        assert "created_task_id=-" in out
        assert "updated_subject_id=-" in out
        assert "existing_task_id=-" in out
        assert len(tasks.list_tasks()) == before

        status = task_event_scanner.manager_action_apply_status(
            "approve_subject_for_qbank_seed",
            tid,
        )
        assert status["applied"] is False
        assert status["apply_mode"] == "confirmed"
        assert status["apply_reason"] == "not_allowed_dry_run_only"


def test_task_manager_actions_show_dry_run_only_and_closeout_blocked_gate_state():
    with isolated_env():
        blocked = _approved_subject_for_apply(evidence={})
        run_cli([
            "task", "manager-action-apply",
            "approve_subject_for_qbank_seed",
            "--subject-id", blocked,
            "--confirm",
        ])

        rc, actions_out, err = run_cli(["task", "manager-actions"])
        assert rc == 0, err
        assert "action_code=request_review_course_file_evidence apply_allowed=true" in actions_out
        assert "closeout_gate: review_approved=true evidence_present=false qa_standard_met=false qbank_ready=false" in actions_out

        status = task_event_scanner.manager_action_apply_status(
            "approve_subject_for_qbank_seed",
            blocked,
        )
        assert status["apply_reason"] == "not_allowed_dry_run_only"
        assert status["apply_mode"] == "confirmed"


# ── dispatcher ───────────────────────────────────────────────────


def test_task_no_args_prints_usage():
    rc, out, _ = run_cli(["task"])
    # treated as "show usage"; behaviour-wise rc==1 since no subcmd
    assert "usage:" in out
    assert rc == 1


def test_task_unknown_subcommand_returns_one():
    rc, _, err = run_cli(["task", "invent"])
    assert rc == 1
    assert "unknown task subcommand" in err


# ── package 5: subject inventory extension ────────────────────────


def test_task_subject_inventory_shows_outline_and_manifest_counts():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            evidence_packet={
                "sampled_topic_count": 8,
                "items_mapping_count": 150,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
            },
        )
        rc, out, err = run_cli(["task", "subject-inventory"])
        assert rc == 0, err
        assert "outline_topic_count=8" in out
        assert "manifest_covered_count=150" in out


def test_task_subject_inventory_shows_next_action():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 50,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 50,
                "item_count": 50,
            },
        )
        tasks.batch_closeout(tid, actor="manager")
        rc, out, err = run_cli(["task", "subject-inventory"])
        assert rc == 0, err
        assert "next_action=" in out


# ── package 5: manager-panel safe default workflow ─────────────────


def test_task_manager_panel_shows_safe_default_workflow_when_no_p0_blocking():
    """When there are subjects but no P0 anomalies, panel should show
    safe read-only/default workflow actions instead of idle."""
    with isolated_env():
        # Create a subject that has been batch-closed but not subject-closeout
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 50,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 50,
                "item_count": 50,
            },
        )
        tasks.batch_closeout(tid, actor="manager")
        rc, out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "== Subject Continuation ==" in out or "== Subject Closeout ==" in out
        # Should not be idle — should show next action recommendation
        assert "idle" not in out.lower() or "default_workflow" in out


def test_task_manager_panel_shows_subject_continuation_recommendation():
    """After batch closeout with subject incomplete, panel shows continuation rec."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 50,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 50,
                "item_count": 50,
            },
        )
        tasks.batch_closeout(tid, actor="manager")
        # Add another subject as candidate
        tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        # Should show next subject recommendation or continuation recommendation
        assert "next_subject" in out or "continuation" in out or "batch_continuation" in out


def test_task_manager_panel_does_not_recommend_completed_subjects():
    """Panel should never recommend a closeout_completed subject as next."""
    with isolated_env():
        done_tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 正式完成",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject 300 QA 正式完成",
        )
        tasks.assign_reviewer(done_tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(done_tid, to_status="assigned", actor="manager")
        tasks.transition_flow(done_tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(done_tid, actor="worker_course")
        tasks.review_flow(
            done_tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次 正式完成",
            verdict_target="IGCSE Physics 0625",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        # skip_subject_verifier=True: this test is about manager-panel
        # recommendation logic for already-closed-out subjects, not about
        # the artifact verifier. Package 2 makes the verifier stricter
        # (items vs QQL drift fails closeout), so we opt out for this
        # panel-only test. Real content drift in Physics 0625 is real
        # and will continue to block production closeouts as intended.
        tasks.manager_closeout_subject(done_tid, actor="manager",
                                       skip_subject_verifier=True)

        next_tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620",
            stage="curriculum", owner="worker_course", creator="manager",
        )

        rc, out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        # Physics should NOT be recommended as next subject
        lines = out.split("\n")
        for line in lines:
            # Only check lines from the Subject Continuation section
            if "next_subject_recommendation:" in line:
                assert "Chemistry" in line or "0620" in line or next_tid in line
                assert "Physics" not in line or "0625" not in line


def test_task_manager_panel_shows_default_workflow_actions_when_no_anomalies():
    """When no P0 blocking, show safe read-only default workflow actions."""
    with isolated_env():
        # Just create a fresh subject in progress — no anomalies
        tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        rc, out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "== Subject Continuation ==" in out or "== Default Workflow ==" in out or "== Subject Closeout ==" in out


def test_task_evidence_account_cli_json_surfaces_incomplete_account():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 worker says done",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
            status="delivered",
            verdict="approved",
        )

        rc, out, err = run_cli(["task", "evidence-account", "--task-id", tid, "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        account = payload["evidence_accounts"][0]
        assert account["task_id"] == tid
        assert account["closeout_ready"] is False
        assert account["recommended_action"] == "complete_closeout_evidence_account"
        assert "items_count" in account["missing_evidence"]


def test_manager_panel_shows_evidence_account_conflict_not_closeout_ready():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Additional Mathematics 0606 正式完成",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final closeout 正式完成",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            verdict_target="IGCSE Additional Mathematics 0606",
            evidence_packet={
                "workflow_id": "igcse-subject-launch",
                "task_id": tid,
                "batch_range": "full_subject",
                "items_count": 378,
                "qql_count": 324,
                "manifest_evidence": {"rows": 324},
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 324,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 324,
                "item_count": 378,
            },
        )
        data = tasks._load()
        for row in data.get("tasks", []):
            if row.get("id") == tid:
                row["verifier_result"] = {
                    "scope": "subject",
                    "status": "pass",
                    "items_count": 378,
                    "qql_count": 324,
                    "manifest_rows": 324,
                    "blocking_reasons": [],
                    "consistency": {"drifts": [], "drift_count": 0},
                }
        tasks._save(data)

        rc, out, err = run_cli(["task", "manager-panel"])
        assert rc == 0, err
        assert "== Evidence Accounts ==" in out
        assert "evidence_account :: task_id=" in out
        assert "closeout_ready=false" in out
        assert "items_qql_count_drift:items=378:qql=324" in out
        assert "recommended_action=manager_formal_closeout" not in out


# ── V1 workflow-first panel ──────────────────────────────────────


def test_task_dispatch_auto_mounts_igcse_workflow_for_curriculum_owner():
    """Default dispatch path must auto-mount igcse-subject-launch.

    Without --workflow, dispatching an IGCSE course subject to worker_course
    must still produce workflow_id=igcse-subject-launch. This is the entry
    point for the workflow-first main rail.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Accounting", "0452", "Batch", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        assert "auto_mounted=true" in out
        t = tasks.get("T-1")
        assert t["workflow_id"] == "igcse-subject-launch"


def test_task_dispatch_explicit_workflow_overrides_auto_mount():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Chemistry", "0620", "Batch", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
                "--workflow", "igcse-subject-launch",
            ])
        assert rc == 0
        assert "workflow=igcse-subject-launch" in out
        assert "auto_mounted=true" not in out


def test_task_dispatch_does_not_mount_workflow_for_non_subject_curriculum():
    """Non-IGCSE curriculum tasks must NOT be auto-mounted.

    This guards the workflow-first main rail from over-applying to every
    curriculum task — only IGCSE subject production gets the default mount.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "Draft", "Unit", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        assert rc == 0
        assert "auto_mounted=true" not in out
        assert tasks.get("T-1")["workflow_id"] == ""


def test_task_dispatch_does_not_mount_workflow_for_non_curriculum_stage():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_builder", "Repair", "router",
                "--stage", "builder",
                "--owner", "worker_builder",
                "--by", "manager",
            ])
        assert rc == 0
        assert "auto_mounted=true" not in out
        assert tasks.get("T-1")["workflow_id"] == ""


def test_task_manager_panel_surfaces_workflow_drive_section():
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            rc, out, _ = run_cli([
                "task", "dispatch",
                "worker_course", "IGCSE", "Physics", "0625", "Batch", "1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
            ])
        assert rc == 0
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "== Workflow Drive ==" in out
        # workflow_id, gate, gate_status, next_action, apply_allowed, blocking_reasons
        # all surface for the IGCSE subject task that was auto-mounted.
        assert "workflow_id=igcse-subject-launch" in out
        assert "workflow_gate=dispatch_acceptance_gate" in out
        assert "workflow_gate_status=waiting_worker_acceptance" in out
        assert "next_action=worker_start_or_ack" in out
        assert "apply_allowed=false" in out
        assert "blocking_reasons=-" in out


def test_task_manager_panel_flags_workflow_missing_for_igcse_task_without_workflow():
    """IGCSE subject production task that never had workflow_id mounted.

    The V1 contract: such tasks must surface workflow_missing=true so the
    manager immediately knows they are off the automated main rail.
    """
    with isolated_env():
        # create_flow auto-mounts, so we strip workflow_id after creation
        # to simulate a legacy / partially migrated subject.
        tasks.create_flow(
            "worker_course", "IGCSE Economics 0455 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        # Read back the file, clear workflow_id, save again.
        from eduflow.store import tasks as tasks_mod
        from eduflow.runtime import paths
        from eduflow.util import read_json, write_json
        data = read_json(paths.state_dir() / "tasks.json", {"tasks": [], "_meta": {"last_id": 0}})
        for t in data.get("tasks", []):
            t["workflow_id"] = ""
        write_json(paths.state_dir() / "tasks.json", data)
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "== Workflow Drive ==" in out
        assert "workflow_missing=true" in out
        assert "next_action=mount_igcse_subject_launch_workflow" in out
        assert "blocking_reasons=workflow_not_mounted" in out


def test_task_manager_panel_workflow_drive_skips_terminal_tasks():
    """Delivered/cancelled tasks must NOT pollute the workflow drive lane."""
    with isolated_env() as tmp:
        with _workflow_env(tmp):
            tid = tasks.create_flow(
                "worker_course", "IGCSE Accounting 0452 Done",
                stage="curriculum", owner="worker_course", creator="manager",
                workflow_id="igcse-subject-launch",
            )
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
            tasks.submit_for_review(tid, actor="worker_course")
            tasks.review_flow(
                tid,
                outcome="approve",
                actor="review_course",
                review_reason="approved_for_delivery",
                latest_turn_summary="done",
                evidence_packet={"files_sampled": ["Q-1"], "path_naming_result": "pass"},
            )
            # status is now "delivered" + verdict=approved → terminal-ish
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        drive_section = out.split("== Workflow Drive ==")[1].split("== Task Buckets ==")[0]
        # The delivered task should NOT show in the drive lane.
        assert f"{tid} [" not in drive_section


def test_task_manager_actions_surfaces_workflow_next_action_line():
    """Manager actions must lead with workflow_next_action / apply_allowed /
    blocking_reasons so the manager can scan the queue at a glance."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Business Studies 0450",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
            scope_topic="IGCSE Business Studies 0450",
            verdict_target="IGCSE Business Studies 0450",
        )
        rc, out, _ = run_cli(["task", "manager-actions"])
        assert rc == 0
        assert "workflow_next_action=manager_formal_closeout" in out
        assert "apply_allowed=true" in out
        # The closeout gate is fully green, so no blocking reasons.
        assert "blocking_reasons=-" in out


def test_task_manager_actions_blocking_reasons_for_qa_shortfall():
    """When the closeout gate has open blockers, they must surface in
    manager-actions next-action line."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Biology 0610",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject final batch 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 299,  # below QA standard
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 299,
                "item_count": 299,
            },
            scope_topic="IGCSE Biology 0610",
            verdict_target="IGCSE Biology 0610",
        )
        rc, out, _ = run_cli(["task", "manager-actions"])
        assert rc == 0
        assert "workflow_next_action=request_worker_course_expand_qa" in out
        assert "blocking_reasons=qa_standard_not_met" in out


# ── V1 stale reassurance packet ───────────────────────────────────


def test_task_scan_anomalies_attaches_lightweight_reassurance_packet_for_stale_igcse():
    """A stale IGCSE workflow-drive task must carry a dry-run reassurance
    packet so the manager sees a one-tap ping action."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        row = tasks.get(tid)
        assert row is not None
        with attr_patch(
            task_event_scanner,
            now_ms=lambda: row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1,
        ):
            rc, out, _ = run_cli(["task", "scan-anomalies"])
        assert rc == 0
        assert "stale_task" in out
        assert "send_lightweight_reassurance" in out
        assert "apply_allowed=false" in out
        # Packet must explicitly say dry-run only — never auto-apply.
        assert "dry_run_only/requires_manager_confirmation/no_auto_dispatch" in out


def test_task_stale_reassurance_apply_is_dry_run_only_by_default():
    """Even with --confirm, the apply path stays dry-run because the
    action code is not in the auto-apply allowlist.
    """
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        rc, out, _ = run_cli([
            "task", "manager-action-apply",
            "send_lightweight_reassurance",
            "--subject-id", tid,
            "--confirm",
        ])
        assert rc == 0
        # Even with --confirm, the action code is not in the auto-apply
        # allowlist so it cannot perform a real send. The apply_reason
        # is the contract: "not_allowed_dry_run_only".
        assert "apply_reason=not_allowed_dry_run_only" in out
        assert "applied=false" in out
        assert "本轮只保留为 dry-run 建议，不执行 apply" in out


# ── package 7 (Revision-First Gate): manager-panel blocker-first ──


def test_manager_panel_lists_revision_first_blocker_above_continuation():
    """Set revision_priority on a task, call manager-panel, assert the
    revision-first blocker text appears before any 'continue next batch' /
    'select next subject' text in the output."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            scope_topic="IGCSE Physics 0625 Batch 1",
        )
        # Confirm revision_priority is set
        row = tasks.get(tid)
        assert row.get("revision_priority") == "minor"

        # Also create a second subject so continuation has something to point at
        tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )

        rc, out, _ = run_cli(["task", "manager-panel"])

    assert rc == 0
    # The revision-first blocker text must appear
    assert "revision_first" in out or "revision-first" in out
    # And it must appear before any continuation text
    revision_idx = out.find("revision_first")
    if revision_idx == -1:
        revision_idx = out.find("revision-first")
    continuation_idx = out.find("continue_next_batch")
    select_idx = out.find("select_next_subject")
    # At least one continuation phrase exists
    continuation_phrases_exist = continuation_idx != -1 or select_idx != -1
    if continuation_phrases_exist:
        # Find the earliest continuation index
        indices = [i for i in (continuation_idx, select_idx) if i != -1]
        if indices:
            earliest_continuation = min(indices)
            assert revision_idx != -1
            assert revision_idx < earliest_continuation


def test_manager_actions_does_not_recommend_continue_next_batch_when_revision_first_active():
    """Set revision_priority, call manager-actions, assert no action_code
    recommends continue_next_batch or select_next_subject for the affected
    task."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            scope_topic="IGCSE Physics 0625 Batch 1",
        )
        row = tasks.get(tid)
        assert row.get("revision_priority") == "minor"

        # Package 7 (Revision-First Gate) round 7 fix: force a real
        # `next_subject_rollover_ready` finding so the manager-actions
        # output actually contains a blocked action_code. The test
        # would silently pass if the recommendation layer never emitted
        # any pivot action in the first place.
        from eduflow.store import tasks as _tasks_mod
        ready_tid = _tasks_mod.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 300 QA 正式完成",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final batch 正式完成",
        )
        _tasks_mod.assign_reviewer(ready_tid, reviewer="review_course", actor="manager")
        _tasks_mod.transition_flow(ready_tid, to_status="assigned", actor="manager")
        _tasks_mod.transition_flow(ready_tid, to_status="in_progress", actor="worker_course")
        _tasks_mod.submit_for_review(ready_tid, actor="worker_course")
        _tasks_mod.review_flow(
            ready_tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="全部 10 批次正式完成，review approved.",
            evidence_packet={
                "workflow_id": "igcse-subject-launch",
                "task_id": ready_tid,
                "batch_range": "1-3",
                "items_count": 300,
                "qql_count": 300,
                "manifest_evidence": "manifest_covered",
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
            scope_topic="IGCSE Chemistry 0620",
            verdict_target="IGCSE Chemistry 0620",
        )
        _tasks_mod.manager_closeout_subject(
            ready_tid, actor="manager", skip_subject_verifier=True,
        )

        # Confirm the rollover finding is present in the anomaly scan
        # before asserting that manager-actions filters it out.
        from eduflow.store import task_event_scanner
        anomalies = task_event_scanner.scan_manager_anomalies()
        rollover = [
            a for a in anomalies
            if a.get("category") == "next_subject_rollover_ready"
        ]
        assert rollover, (
            "test setup failed: no next_subject_rollover_ready finding "
            "to exercise the revision-first filter"
        )

        rc, out, _ = run_cli(["task", "manager-actions"])

    assert rc == 0
    # No action_code should recommend continue_next_batch or select_next_subject
    # for the task that has revision_priority set.
    # Parse action_code lines from output
    action_codes = []
    for line in out.splitlines():
        if "action_code=" in line:
            # Extract value between action_code= and next space
            start = line.index("action_code=") + len("action_code=")
            end = line.find(" ", start)
            if end == -1:
                end = len(line)
            action_codes.append(line[start:end].strip())

    # Package 7 (Revision-First Gate) round 6 fix: assert ALL pivot
    # action_codes are absent, not just `continue_next_batch`. The
    # blocked set is REVISION_FIRST_BLOCKED_RECOMMENDATIONS — see
    # task_event_scanner.py for the canonical list.
    for blocked in (
        "continue_next_batch",
        "select_next_subject",
        "dispatch_next_subject_worker_course",
        "request_worker_course_expand_qa",
    ):
        assert blocked not in action_codes, (
            f"action_code={blocked} leaked through manager-actions under "
            f"active revision-first; output was:\n{out}"
        )


# ── Package 2: Codex Q2 regression — `--skip-verifier` must be gated ──


def test_task_manager_closeout_rejects_skip_verifier_without_env():
    """Production CLI must reject `--skip-verifier` unless the test-only
    env var EDUFLOW_VERIFIER_BYPASS_ALLOWED is explicitly set.
    """
    with isolated_env() as tmp:
        with env_patch(EDUFLOW_VERIFIER_BYPASS_ALLOWED=None):
            tid = tasks.create_flow(
                "worker_course",
                "IGCSE Business Studies 0450 300 QA 正式完成",
                stage="curriculum",
                owner="worker_course",
                creator="manager",
                workflow_id="igcse-subject-launch",
            )
            tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
            tasks.submit_for_review(tid, actor="worker_course")
            tasks.review_flow(
                tid,
                outcome="approve",
                actor="review_course",
                evidence_packet={
                    "workflow_id": "igcse-subject-launch",
                    "task_id": tid,
                    "batch_range": "1-10",
                    "items_count": 300,
                    "qql_count": 300,
                    "qa_count": 300,
                    "item_count": 300,
                    "manifest_evidence": ["qa-manifest.csv"],
                    "files_sampled": ["Q-1.md"],
                    "q_ids_checked": ["Q-1"],
                    "calculation_or_concept_checks": ["checked"],
                },
                verdict_target="full_subject",
            )
            rc, out, err = run_cli(
                ["task", "manager-closeout", tid, "--actor", "manager", "--skip-verifier"]
            )
            assert rc != 0, ("expected non-zero exit for --skip-verifier without env", out, err)
            combined = out + err
            assert "--skip-verifier is disabled in production" in combined


def test_task_manager_closeout_allows_skip_verifier_with_env():
    """When EDUFLOW_VERIFIER_BYPASS_ALLOWED=1 is set, the CLI accepts
    `--skip-verifier` so tests/fixtures can exercise closeout logic.
    """
    with isolated_env() as tmp:
        with env_patch(EDUFLOW_VERIFIER_BYPASS_ALLOWED="1"):
            tid = tasks.create_flow(
                "worker_course",
                "IGCSE Business Studies 0450 300 QA 正式完成",
                stage="curriculum",
                owner="worker_course",
                creator="manager",
                workflow_id="igcse-subject-launch",
            )
            tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
            tasks.submit_for_review(tid, actor="worker_course")
            tasks.review_flow(
                tid,
                outcome="approve",
                actor="review_course",
                evidence_packet={
                    "workflow_id": "igcse-subject-launch",
                    "task_id": tid,
                    "batch_range": "1-10",
                    "items_count": 300,
                    "qql_count": 300,
                    "qa_count": 300,
                    "item_count": 300,
                    "manifest_evidence": ["qa-manifest.csv"],
                    "files_sampled": ["Q-1.md"],
                    "q_ids_checked": ["Q-1"],
                    "calculation_or_concept_checks": ["checked"],
                },
                verdict_target="full_subject",
            )
            rc, out, err = run_cli(
                ["task", "manager-closeout", tid, "--actor", "manager", "--skip-verifier"]
            )
            assert rc == 0, ("expected success with env + --skip-verifier", out, err)
            task = tasks.get(tid)
            assert task["closeout_status"] == "closeout_completed"


def test_task_manager_action_apply_rejects_skip_verifier_without_env():
    """`manager-action-apply --skip-verifier` must also be gated by the
    same env var. Without it the production CLI returns non-zero.
    """
    with isolated_env() as tmp:
        with env_patch(EDUFLOW_VERIFIER_BYPASS_ALLOWED=None):
            tid = tasks.create_flow(
                "worker_course",
                "IGCSE Business Studies 0450 300 QA 正式完成",
                stage="curriculum",
                owner="worker_course",
                creator="manager",
                workflow_id="igcse-subject-launch",
            )
            tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
            tasks.transition_flow(tid, to_status="assigned", actor="manager")
            tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
            tasks.submit_for_review(tid, actor="worker_course")
            tasks.review_flow(
                tid,
                outcome="approve",
                actor="review_course",
                evidence_packet={
                    "workflow_id": "igcse-subject-launch",
                    "task_id": tid,
                    "batch_range": "1-10",
                    "items_count": 300,
                    "qql_count": 300,
                    "qa_count": 300,
                    "item_count": 300,
                    "manifest_evidence": ["qa-manifest.csv"],
                },
                verdict_target="full_subject",
            )
            rc, out, err = run_cli([
                "task", "manager-action-apply",
                "manager_formal_closeout",
                "--subject-id", tid,
                "--confirm",
                "--skip-verifier",
            ])
            assert rc != 0, ("expected rejection without env", out, err)
            combined = out + err
            assert "--skip-verifier is disabled in production" in combined


# ── AP workflow mount rules ──────────────────────────────────────


def test_task_dispatch_ap_title_auto_mounts_ap_workflow_not_igcse():
    """An AP-titled curriculum task must auto-mount to
    ap-knowledge-base-optimization, not fall back to igcse-subject-launch.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp, "igcse-subject-launch"):
            with _workflow_env(tmp, "ap-knowledge-base-optimization"):
                rc, out, err = run_cli([
                    "task", "dispatch",
                    "worker_course", "AP Physics 2 full subject qbank sample",
                    "--stage", "curriculum",
                    "--owner", "worker_course",
                    "--by", "manager",
                ])
        assert rc == 0, err
        assert "workflow=ap-knowledge-base-optimization" in out
        assert "igcse-subject-launch" not in out
        t = tasks.get("T-1")
        assert t["workflow_id"] == "ap-knowledge-base-optimization"


def test_task_flow_create_ap_title_mounts_ap_workflow():
    """task flow-create with an AP title must mount ap-knowledge-base-optimization."""
    with isolated_env() as tmp:
        with _workflow_env(tmp, "ap-knowledge-base-optimization"):
            rc, out, err = run_cli([
                "task", "flow-create",
                "worker_course", "AP Computer Science A Unit 1",
                "--stage", "curriculum",
                "--owner", "worker_course",
                "--by", "manager",
                "--workflow", "ap-knowledge-base-optimization",
            ])
        assert rc == 0, err
        assert "workflow=ap-knowledge-base-optimization" in out
        t = tasks.get("T-1")
        assert t["workflow_id"] == "ap-knowledge-base-optimization"


def test_task_dispatch_rejects_igcse_workflow_for_ap_title():
    """AP tasks cannot be mounted with igcse-subject-launch — they require
    ap-knowledge-base-optimization. The CLI must surface this as an error
    rather than silently accepting the wrong workflow.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp, "igcse-subject-launch"):
            with _workflow_env(tmp, "ap-knowledge-base-optimization"):
                rc, _, err = run_cli([
                    "task", "dispatch",
                    "worker_course", "AP Calculus AB qbank items",
                    "--stage", "curriculum",
                    "--owner", "worker_course",
                    "--by", "manager",
                    "--workflow", "igcse-subject-launch",
                ])
    assert rc == 1
    assert "ap-knowledge-base-optimization" in err


def test_task_dispatch_rejects_unknown_workflow():
    """An unknown workflow id must produce a clear error, not silently
    fall back to igcse-subject-launch or ap-knowledge-base-optimization.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp, "igcse-subject-launch"):
            with _workflow_env(tmp, "ap-knowledge-base-optimization"):
                rc, _, err = run_cli([
                    "task", "dispatch",
                    "worker_course", "AP Calculus AB qbank items",
                    "--stage", "curriculum",
                    "--owner", "worker_course",
                    "--by", "manager",
                    "--workflow", "fake-ap-workflow",
                ])
    assert rc == 1
    assert "fake-ap-workflow" in err
    assert "unknown workflow" in err.lower()


def test_task_dispatch_ap_title_without_workflow_flag_auto_routes():
    """Dispatching an AP task without --workflow flag must auto-route to
    ap-knowledge-base-optimization based on the title alone.
    """
    with isolated_env() as tmp:
        with _workflow_env(tmp, "igcse-subject-launch"):
            with _workflow_env(tmp, "ap-knowledge-base-optimization"):
                rc, out, err = run_cli([
                    "task", "dispatch",
                    "worker_course", "AP Statistics qbank",
                    "--stage", "curriculum",
                    "--owner", "worker_course",
                    "--by", "manager",
                ])
        assert rc == 0, err
        assert "workflow=ap-knowledge-base-optimization" in out
        assert "auto_mounted=true" in out
        t = tasks.get("T-1")
        assert t["workflow_id"] == "ap-knowledge-base-optimization"
