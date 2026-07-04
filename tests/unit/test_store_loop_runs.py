from helpers import isolated_env
from eduflow.store import loop_runs


def test_create_or_get_active_run_reuses_existing_run():
    with isolated_env():
        first = loop_runs.create_or_get_active(
            task_id="T-1",
            spec="code-repair",
            max_cycles=3,
        )
        second = loop_runs.create_or_get_active(
            task_id="T-1",
            spec="code-repair",
            max_cycles=3,
        )

        assert second["id"] == first["id"]
        assert second["task_id"] == "T-1"
        assert second["status"] == "running"


def test_append_cycle_writes_artifacts():
    with isolated_env():
        run = loop_runs.create_or_get_active(
            task_id="T-1",
            spec="code-repair",
            max_cycles=3,
        )
        updated = loop_runs.append_cycle(
            run["id"],
            checker_output="FAILED test_x.py",
            diff_text="diff --git a/x b/x",
            preflight={"workspace_mode": "shared"},
            failed_commands=["pytest -q"],
            passed_commands=[],
            failure_fingerprint="abc123",
            status="repair_needed",
            stop_reason="",
        )

        assert updated["cycle_count"] == 1
        assert updated["status"] == "repair_needed"
        assert loop_runs.artifact_path(run["id"], "cycle-001-checker.txt").exists()
        assert loop_runs.artifact_path(run["id"], "cycle-001-preflight.json").exists()


def test_terminal_run_is_not_reused():
    with isolated_env():
        run = loop_runs.create_or_get_active(
            task_id="T-1",
            spec="code-repair",
            max_cycles=1,
        )
        loop_runs.update_status(run["id"], status="passed", stop_reason="all_green")

        next_run = loop_runs.create_or_get_active(
            task_id="T-1",
            spec="code-repair",
            max_cycles=1,
        )
        assert next_run["id"] != run["id"]
