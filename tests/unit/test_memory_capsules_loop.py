import json

from helpers import isolated_env
from eduflow.memory import capsules
from eduflow.store import tasks


def test_refresh_capsule_includes_loop_blocker_and_evidence_ref():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair runtime",
            stage="builder",
            owner="worker_builder",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="repair_needed",
            loop_cycle_count=2,
            loop_recommended_action="send_builder_handoff",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        capsule = capsules.refresh_from_task_store(tid)
        blockers = json.loads(capsule["blockers"])
        assert "loop_status=repair_needed" in blockers
        assert capsule["next_action"] == "send_builder_handoff"
        assert capsule["last_evidence_ref"] == "loop_runs/L-000001/meta.json"
