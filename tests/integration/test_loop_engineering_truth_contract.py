from helpers import isolated_env, run_cli
from eduflow.store import tasks


def test_loop_pass_never_auto_delivers_subject_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
        )

        assert tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="passed",
            loop_cycle_count=1,
            loop_stop_reason="all_green",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        row = tasks.get(tid)
        assert row["status"] == "queued"
        assert row["verdict"] == "pending"
        assert row["closeout_status"] == ""


def test_loop_pass_does_not_make_evidence_explain_pass():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="passed",
            loop_cycle_count=1,
            loop_stop_reason="all_green",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        rc, out, err = run_cli(["task", "evidence-explain", tid, "--json"])
        assert rc == 0, err
        assert '"verdict": "PASS"' not in out
        assert '"manager_action_allowed": true' not in out
