from helpers import attr_patch, isolated_env, run_cli
from eduflow.commands import task as task_cmd
from eduflow.store import tasks, team_loop_account


def test_agent_loop_evidence_write_smoke():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair runtime",
            stage="builder",
            owner="worker_builder",
            workspace_mode="shared",
        )
        with attr_patch(
            task_cmd.loop_runner,
            run_checker_cycle=lambda **kwargs: {
                "passed": True,
                "checker_unavailable": False,
                "check_mode": "self_check",
                "passed_commands": ["pytest -q"],
                "failed_commands": [],
                "checker_output": "ok",
                "failure_fingerprint": "",
            },
            decide_stop=lambda current, previous, cycle, max_cycles: {
                "status": "passed",
                "stop_reason": "all_green",
            },
        ):
            rc, out, err = run_cli(["task", "loop-check", tid])
        assert rc == 0, err
        assert "loop_status=passed" in out

        row = tasks.get(tid)
        assert row["loop_status"] == "passed"
        assert row["loop_evidence_ref"] == "loop_runs/L-000001/meta.json"
        assert row["status"] == "queued"
        assert row["verdict"] == "pending"
        assert row["closeout_status"] == ""


def test_builder_loop_dispatch_background_then_rerun_smoke():
    with isolated_env():
        rc, out, err = run_cli([
            "task",
            "dispatch",
            "worker_builder",
            "Repair runtime verifier",
            "--stage",
            "builder",
            "--owner",
            "worker_builder",
            "--workspace-mode",
            "shared",
            "--by",
            "manager",
        ])
        assert rc == 0, err
        assert "dispatched T-1" in out
        calls = []

        class FakePopen:
            def __init__(self, args, **kwargs):
                calls.append({"args": args, "kwargs": kwargs})

        with attr_patch(task_cmd.subprocess, Popen=FakePopen):
            rc, out, err = run_cli(["task", "loop-check", "T-1", "--background"])
        assert rc == 0, err
        assert "background=true" in out
        assert calls
        assert tasks.get("T-1")["loop_status"] == "running"

        with attr_patch(
            task_cmd.loop_runner,
            run_checker_cycle=lambda **kwargs: {
                "passed": True,
                "checker_unavailable": False,
                "check_mode": "self_check",
                "passed_commands": ["pytest -q"],
                "failed_commands": [],
                "checker_output": "ok after worker fix",
                "failure_fingerprint": "",
            },
            decide_stop=lambda current, previous, cycle, max_cycles: {
                "status": "passed",
                "stop_reason": "all_green",
            },
        ):
            rc, out, err = run_cli(["task", "loop-check", "T-1"])
        assert rc == 0, err
        row = tasks.get("T-1")
        assert row["loop_status"] == "passed"
        assert row["status"] == "assigned"
        assert row["verdict"] == "pending"
        assert row["closeout_status"] == ""


def test_team_loop_repair_phase_smoke():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="reject", actor="review_course")

        rc, out, err = run_cli(["task", "loop-status", tid])
        assert rc == 0, err
        assert "team_loop:" in out
        assert "phase: team_repair_needed" in out
        assert team_loop_account.build(tid)["cycle_count"] == 1
