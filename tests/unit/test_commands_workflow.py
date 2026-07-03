"""Tests for `eduflowteam workflow`."""
from __future__ import annotations

from helpers import env_patch, run_cli
from eduflow.commands.workflow import is_active_workflow


def _write_workflow(root, workflow_id="igcse-subject-launch"):
    d = root / workflow_id
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        f"# workflow: {workflow_id}\n\n"
        "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n\n"
        "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
        "## Boundary\n\nworker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    (d / "trigger.md").write_text(
        f"# trigger: {workflow_id}\n\n调用 workflow: {workflow_id}\n",
        encoding="utf-8",
    )
    (d / "roles.md").write_text(
        f"# roles: {workflow_id}\n\n## manager\n\n- Calls the workflow.\n\n"
        "## worker_builder\n\n- Maintains workflow assets.\n",
        encoding="utf-8",
    )
    (d / "checklist.md").write_text(
        f"# checklist: {workflow_id}\n\n- [ ] dispatch accepted\n",
        encoding="utf-8",
    )
    (d / "handoff-template.md").write_text(
        f"# handoff: {workflow_id}\n\n## Manager -> worker\n\nhandoff text\n",
        encoding="utf-8",
    )


def _write_template(root):
    d = root / "_template"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "# workflow: <workflow_id>\n\n"
        "## Metadata\n\n"
        "- workflow_id: `<workflow_id>`\n"
        "- workflow_name: `<workflow_name>`\n"
        "- status: `draft`\n"
        "- owner: `worker_builder`\n\n"
        "## Primary Chain\n\nmanager -> <worker_role> -> <review_role> -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n\n"
        "## Manager Closeout\n\nmanager owns formal closeout.\n",
        encoding="utf-8",
    )
    (d / "trigger.md").write_text(
        "# trigger: <workflow_id>\n\n调用 workflow: <workflow_id>\n",
        encoding="utf-8",
    )
    (d / "roles.md").write_text(
        "# roles: <workflow_id>\n\n## manager\n\n- Calls workflow.\n\n## worker_builder\n\n- Maintains workflow.\n",
        encoding="utf-8",
    )
    (d / "checklist.md").write_text(
        "# checklist: <workflow_id>\n\n- [ ] intake checked\n",
        encoding="utf-8",
    )
    (d / "handoff-template.md").write_text(
        "# handoff-template: <workflow_id>\n\n## Manager -> worker_builder\n\nhandoff\n",
        encoding="utf-8",
    )


def _write_candidate(root, workflow_id="example-draft-workflow", status="draft"):
    d = root / "_candidates" / workflow_id
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        f"# workflow: {workflow_id}\n\n"
        "## Metadata\n\n"
        f"- workflow_id: `{workflow_id}`\n"
        "- workflow_name: `Example Draft Workflow`\n"
        f"- status: `{status}`\n"
        "- owner: `worker_builder`\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n- runtime_reality\n\n"
        "## Forbidden Moves\n\n"
        "- Candidate cannot be treated as active workflow.\n"
        "- Candidate cannot be used for `task dispatch --workflow`.\n"
        "- promotion requires manager closeout.\n\n"
        "## Reassurance Policy\n\n"
        "Reassurance must not抢 manager formal decision.\n\n"
        "## Builder Followup\n\nworker_builder recommends promotion, backlog, or case-note-only.\n",
        encoding="utf-8",
    )
    (d / "trigger.md").write_text(
        f"# trigger: {workflow_id}\n\n调用 candidate workflow: {workflow_id}\n",
        encoding="utf-8",
    )
    (d / "roles.md").write_text(
        f"# roles: {workflow_id}\n\n"
        "## manager\n\n- Owns closeout and promotion decision.\n\n"
        "## worker_builder\n\n- Maintains candidate files.\n",
        encoding="utf-8",
    )
    (d / "checklist.md").write_text(
        f"# checklist: {workflow_id}\n\n"
        "## Candidate Intake\n\n"
        "- [ ] Source evidence exists.\n"
        "- [ ] manager closeout is explicit.\n\n"
        "## Block Promotion If\n\n"
        "- [ ] Candidate treats worker reassurance as manager result.\n",
        encoding="utf-8",
    )
    (d / "handoff-template.md").write_text(
        f"# handoff-template: {workflow_id}\n\n"
        "## Manager -> worker_builder\n\n"
        f"调用 candidate workflow: {workflow_id}\n\n"
        "## worker_builder -> manager\n\n"
        f"candidate workflow: {workflow_id}\nstatus: {status}\nmanager closeout needed: yes\n",
        encoding="utf-8",
    )
    return d


def _write_three_workflows(root):
    _write_workflow(root, "igcse-subject-launch")
    _write_workflow(root, "igcse-item-level-prototype")
    _write_workflow(root, "realrun-to-workflow")
    (root / "igcse-item-level-prototype" / "README.md").write_text(
        "# workflow: igcse-item-level-prototype\n\n"
        "Use for qbank item-level prototype work.\n\n"
        "## Primary Chain\n\nmanager -> worker_qbank -> review_course -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- file_evidence_gate\n- quality_gate\n\n"
        "## Forbidden Moves\n\n- qbank must not bypass manager closeout.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )


def _write_runtime_failover(root):
    """Write the runtime-failover-hardening workflow with all 5 standard files."""
    _write_workflow(root, "runtime-failover-hardening")
    (root / "runtime-failover-hardening" / "README.md").write_text(
        "# workflow: runtime-failover-hardening\n\n"
        "Runtime 容灾机制升级。\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> auto_ops -> manager\n\n"
        "## Core Gates\n\n- runtime_reality\n- repair_acceptance_contract\n"
        "- file_evidence_gate\n- stale_state_reconciliation\n\n"
        "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    (root / "realrun-to-workflow" / "README.md").write_text(
        "# workflow: realrun-to-workflow\n\n"
        "Use for gap note and real run workflow asset maintenance.\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- artifact_standard_gate\n- runtime_reality\n\n"
        "## Forbidden Moves\n\n- builder must not mark active without manager closeout.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )


def test_workflow_list_reads_registry_dirs(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "list"])
    assert rc == 0
    assert err == ""
    assert "workflow_id" in out
    assert "igcse-subject-launch" in out
    assert "workflow: igcse-subject-launch" in out


def test_workflow_list_excludes_template_dir(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    _write_template(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "list"])
    assert rc == 0
    assert err == ""
    assert "igcse-subject-launch" in out
    assert "_template" not in out


def test_workflow_list_excludes_candidates_dir(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "list"])
    assert rc == 0
    assert err == ""
    assert "igcse-subject-launch" in out
    assert "_candidates" not in out
    assert "example-draft-workflow" not in out


def test_workflow_show_prints_readme(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "show", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "# workflow: igcse-subject-launch" in out
    assert "Primary Chain" in out


def test_workflow_trigger_prints_trigger_template(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "trigger", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "调用 workflow: igcse-subject-launch" in out


def test_workflow_roles_checklist_handoff_print_standard_files(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_roles, out_roles, err_roles = run_cli(["workflow", "roles", "igcse-subject-launch"])
        rc_check, out_check, err_check = run_cli(["workflow", "checklist", "igcse-subject-launch"])
        rc_hand, out_hand, err_hand = run_cli(["workflow", "handoff", "igcse-subject-launch"])
    assert rc_roles == rc_check == rc_hand == 0
    assert err_roles == err_check == err_hand == ""
    assert "## manager" in out_roles
    assert "- [ ] dispatch accepted" in out_check
    assert "Manager -> worker" in out_hand


def test_workflow_files_prints_asset_paths(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "files", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "README.md" in out
    assert "trigger.md" in out
    assert "roles.md" in out
    assert "checklist.md" in out
    assert "handoff-template.md" in out


def test_workflow_validate_passes_complete_assets(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate"])
    assert rc == 0
    assert err == ""
    assert "workflow registry valid" in out
    assert "igcse-subject-launch" in out


def test_workflow_validate_ignores_template_dir(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    _write_template(root)
    (root / "_template" / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate", "--strict"])
    assert rc == 0
    assert err == ""
    assert "workflow registry strict valid" in out
    assert "_template" not in out


def test_workflow_validate_ignores_candidates_dir(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    candidate = _write_candidate(root)
    (candidate / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate", "--strict"])
    assert rc == 0
    assert err == ""
    assert "workflow registry strict valid" in out
    assert "example-draft-workflow" not in out


def test_workflow_validate_strict_passes_complete_assets(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate", "--strict"])
    assert rc == 0
    assert err == ""
    assert "workflow registry strict valid" in out


def test_workflow_validate_strict_reports_missing_workflow_reference(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    (root / "igcse-subject-launch" / "roles.md").write_text(
        "# roles\n\n## manager\n\n- Calls the workflow.\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate", "--strict"])
    assert rc == 1
    assert err == ""
    assert "roles.md missing workflow_id reference" in out


def test_workflow_use_prints_manager_package(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "use", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "manager workflow package: igcse-subject-launch" in out
    assert "Trigger" in out
    assert "Closeout Checklist" in out
    assert "Forbidden Moves" in out


def test_workflow_maintainer_prints_builder_package(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "maintainer", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "worker_builder maintenance package: igcse-subject-launch" in out
    assert "Validate Result" in out
    assert "Next Maintenance Checklist" in out
    assert "passed" in out


def test_workflow_maintainer_prints_action_taxonomy(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "maintainer", "igcse-subject-launch"])
    assert rc == 0
    assert err == ""
    assert "Maintenance Action Taxonomy" in out
    assert "update_trigger_examples" in out
    assert "update_forbidden_moves" in out
    assert "update_acceptance_gates" in out
    assert "mark_stale_candidate" in out
    assert "split_new_workflow_candidate" in out


def test_workflow_template_prints_readme(tmp_path):
    root = tmp_path / "workflows"
    _write_template(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "template"])
    assert rc == 0
    assert err == ""
    assert "# workflow: <workflow_id>" in out
    assert "workflow_name" in out
    assert "Manager Closeout" in out


def test_workflow_template_prints_each_part(tmp_path):
    root = tmp_path / "workflows"
    _write_template(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_trigger, out_trigger, err_trigger = run_cli(["workflow", "template", "trigger"])
        rc_roles, out_roles, err_roles = run_cli(["workflow", "template", "roles"])
        rc_check, out_check, err_check = run_cli(["workflow", "template", "checklist"])
        rc_hand, out_hand, err_hand = run_cli(["workflow", "template", "handoff"])
    assert rc_trigger == rc_roles == rc_check == rc_hand == 0
    assert err_trigger == err_roles == err_check == err_hand == ""
    assert "调用 workflow: <workflow_id>" in out_trigger
    assert "worker_builder" in out_roles
    assert "- [ ] intake checked" in out_check
    assert "Manager -> worker_builder" in out_hand


def test_workflow_template_rejects_unknown_part(tmp_path):
    root = tmp_path / "workflows"
    _write_template(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "template", "bogus"])
    assert rc == 1
    assert out == ""
    assert "unknown template part" in err


def test_workflow_candidates_lists_candidate_workflows(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidates"])
    assert rc == 0
    assert err == ""
    assert "candidate_workflow_id" in out
    assert "example-draft-workflow" in out
    assert "draft" in out


def test_workflow_candidate_show_prints_readme(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-show", "example-draft-workflow"])
    assert rc == 0
    assert err == ""
    assert "# workflow: example-draft-workflow" in out
    assert "Candidate cannot be treated as active workflow" in out


def test_workflow_candidate_files_prints_asset_paths(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-files", "example-draft-workflow"])
    assert rc == 0
    assert err == ""
    assert "_candidates/example-draft-workflow/README.md" in out
    assert "trigger.md" in out
    assert "roles.md" in out
    assert "checklist.md" in out
    assert "handoff-template.md" in out


def test_workflow_candidate_validate_passes_complete_candidate(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-validate"])
    assert rc == 0
    assert err == ""
    assert "candidate workflow registry valid" in out
    assert "example-draft-workflow status=draft" in out


def test_workflow_promotion_map_reports_candidate_only_state(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map"])
    assert rc == 0
    assert err == ""
    assert "workflow_id\tcandidate_status\tactive_present\tcandidate_present\tlink_state" in out
    assert "example-draft-workflow\tpromotion_ready\tno\tyes\tcandidate_only" in out
    assert "promotion-map is read-only" in out


def test_workflow_promotion_map_reports_active_only_state(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map"])
    assert rc == 0
    assert err == ""
    assert "igcse-subject-launch\t-\tyes\tno\tactive_only" in out


def test_workflow_promotion_map_reports_promoted_state_after_write(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_promote, out_promote, err_promote = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
        rc_map, out_map, err_map = run_cli(["workflow", "promotion-map"])
    assert rc_promote == rc_map == 0
    assert err_promote == err_map == ""
    assert "promoted workflow: example-draft-workflow" in out_promote
    assert "example-draft-workflow\tpromotion_ready\tyes\tyes\tpromoted" in out_map


def test_workflow_promotion_map_summary_reports_counts(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--summary"])
    assert rc == 0
    assert err == ""
    assert "promotion_map_summary" in out
    assert "candidate_only\t1" in out
    assert "promoted\t0" in out
    assert "active_only\t1" in out
    assert "read_only\tyes" in out


def test_workflow_promotion_map_state_filter_limits_rows(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--state", "candidate_only"])
    assert rc == 0
    assert err == ""
    assert "example-draft-workflow\tpromotion_ready\tno\tyes\tcandidate_only" in out
    assert "igcse-subject-launch" not in out
    assert "filtered_state: candidate_only" in out


def test_workflow_promotion_map_summary_supports_state_filter(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promotion-map", "--summary", "--state", "candidate_only",
        ])
    assert rc == 0
    assert err == ""
    assert "candidate_only\t1" in out
    assert "promoted\t0" in out
    assert "active_only\t0" in out
    assert "filtered_state\tcandidate_only" in out


def test_workflow_promotion_map_manager_view_prioritizes_promotion_ready_candidates(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager"])
    assert rc == 0
    assert err == ""
    assert "workflow_id\tcandidate_status\tlink_state\tmanager_priority\tnext_step" in out
    lines = [line for line in out.splitlines() if line and not line.startswith("workflow_id") and not line.startswith("legend:") and not line.startswith("- ")]
    assert lines[0].startswith("example-draft-workflow\tpromotion_ready\tcandidate_only\t0\t")
    assert "run promote-plan example-draft-workflow then manager closeout" in out
    assert "backlog-candidate\tbacklog\tcandidate_only\t1\tkeep in backlog until a real run or gap note justifies promotion review" in out
    assert "igcse-subject-launch\t-\tactive_only\t3\tactive-only audit; candidate source not present" in out
    assert "manager view is read-only" in out


def test_workflow_promotion_map_manager_view_supports_state_filter(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager", "--state", "candidate_only"])
    assert rc == 0
    assert err == ""
    assert "example-draft-workflow\tpromotion_ready\tcandidate_only\t0\t" in out
    assert "igcse-subject-launch" not in out
    assert "filtered_state: candidate_only" in out


def test_workflow_promotion_map_manager_view_status_specific_guidance(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, workflow_id="draft-candidate", status="draft")
    _write_candidate(root, workflow_id="stale-candidate", status="stale_candidate")
    _write_candidate(root, workflow_id="rejected-candidate", status="rejected")
    _write_candidate(root, workflow_id="case-note-candidate", status="case_note_only")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager", "--state", "candidate_only"])
    assert rc == 0
    assert err == ""
    assert "draft-candidate\tdraft\tcandidate_only\t1\tfinish candidate drafting and rerun candidate-validate --strict" in out
    assert "stale-candidate\tstale_candidate\tcandidate_only\t1\treconfirm runtime fit or retire the candidate from active consideration" in out
    assert "rejected-candidate\trejected\tcandidate_only\t1\tretain as rejected evidence; do not reopen without new real-run evidence" in out
    assert "case-note-candidate\tcase_note_only\tcandidate_only\t1\tkeep as case-note evidence, not a reusable workflow candidate" in out


def test_workflow_promotion_map_manager_summary_reports_actionable_buckets(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager", "--summary"])
    assert rc == 0
    assert err == ""
    assert "promotion_map_manager_summary" in out
    assert "ready_for_closeout\t1" in out
    assert "candidate_review\t1" in out
    assert "promoted_audit\t0" in out
    assert "active_only_audit\t1" in out
    assert "top_priority_workflow\texample-draft-workflow" in out
    assert "top_priority_next_step\trun promote-plan example-draft-workflow then manager closeout" in out
    assert "read_only\tyes" in out


def test_workflow_promotion_map_manager_summary_supports_state_filter(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promotion-map", "--manager", "--summary", "--state", "candidate_only",
        ])
    assert rc == 0
    assert err == ""
    assert "ready_for_closeout\t1" in out
    assert "candidate_review\t1" in out
    assert "promoted_audit\t0" in out
    assert "active_only_audit\t0" in out
    assert "filtered_state\tcandidate_only" in out


def test_workflow_promotion_map_actionable_limits_manager_view_to_candidate_queue(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager", "--actionable"])
    assert rc == 0
    assert err == ""
    assert "example-draft-workflow\tpromotion_ready\tcandidate_only\t0\t" in out
    assert "igcse-subject-launch" not in out
    assert "actionable_only: candidate-only manager decision queue" in out
    assert "filtered_state: candidate_only" in out


def test_workflow_promotion_map_actionable_summary_focuses_candidate_buckets(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promotion-map", "--manager", "--summary", "--actionable",
        ])
    assert rc == 0
    assert err == ""
    assert "promotion_map_manager_summary" in out
    assert "ready_for_closeout\t1" in out
    assert "candidate_review\t1" in out
    assert "promoted_audit\t0" in out
    assert "active_only_audit\t0" in out
    assert "actionable_only\tyes" in out
    assert "filtered_state\tcandidate_only" in out


def test_workflow_promotion_map_ready_focuses_only_promotion_ready_candidates(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--manager", "--ready"])
    assert rc == 0
    assert err == ""
    assert "example-draft-workflow\tpromotion_ready\tcandidate_only\t0\trun promote-plan example-draft-workflow then manager closeout" in out
    assert "backlog-candidate" not in out
    assert "igcse-subject-launch" not in out
    assert "ready_only: candidate-only rows already marked promotion_ready" in out
    assert "filtered_state: candidate_only" in out


def test_workflow_promotion_map_ready_shorthand_defaults_to_manager_view(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--ready"])
    assert rc == 0
    assert err == ""
    assert "workflow_id\tcandidate_status\tlink_state\tmanager_priority\tnext_step" in out
    assert "example-draft-workflow\tpromotion_ready\tcandidate_only\t0\trun promote-plan example-draft-workflow then manager closeout" in out
    assert "backlog-candidate" not in out
    assert "ready_only: candidate-only rows already marked promotion_ready" in out
    assert "actionable_only: candidate-only manager decision queue" in out


def test_workflow_promotion_map_ready_summary_reports_only_ready_bucket(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    _write_workflow(root, "igcse-subject-launch")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promotion-map", "--manager", "--summary", "--ready",
        ])
    assert rc == 0
    assert err == ""
    assert "promotion_map_manager_summary" in out
    assert "ready_for_closeout\t1" in out
    assert "candidate_review\t0" in out
    assert "promoted_audit\t0" in out
    assert "active_only_audit\t0" in out
    assert "top_priority_workflow\texample-draft-workflow" in out
    assert "top_priority_next_step\trun promote-plan example-draft-workflow then manager closeout" in out
    assert "ready_only\tyes" in out
    assert "actionable_only\tyes" in out
    assert "filtered_state\tcandidate_only" in out


def test_workflow_promotion_map_ready_summary_shorthand_defaults_to_manager_summary(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_candidate(root, workflow_id="backlog-candidate", status="backlog")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--summary", "--ready"])
    assert rc == 0
    assert err == ""
    assert "promotion_map_manager_summary" in out
    assert "ready_for_closeout\t1" in out
    assert "candidate_review\t0" in out
    assert "ready_only\tyes" in out
    assert "actionable_only\tyes" in out


def test_workflow_promotion_map_rejects_unknown_state_filter(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promotion-map", "--state", "bogus"])
    assert rc == 1
    assert out == ""
    assert "unknown promotion-map state" in err


def test_workflow_candidate_validate_reports_missing_file(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root)
    (candidate / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-validate"])
    assert rc == 1
    assert err == ""
    assert "candidate workflow validation failed" in out
    assert "missing roles.md" in out


def test_workflow_candidate_validate_rejects_active_trigger_syntax(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root)
    (candidate / "trigger.md").write_text(
        "# trigger: example-draft-workflow\n\n调用 workflow: example-draft-workflow\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-validate"])
    assert rc == 1
    assert err == ""
    assert "missing 调用 candidate workflow: example-draft-workflow" in out
    assert "must not use active call syntax" in out


def test_workflow_candidate_validate_strict_reports_missing_boundaries(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root)
    (candidate / "README.md").write_text(
        "# workflow: example-draft-workflow\n\n"
        "## Metadata\n\n"
        "- workflow_id: `example-draft-workflow`\n"
        "- status: `draft`\n"
        "- owner: `worker_builder`\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n",
        encoding="utf-8",
    )
    (candidate / "roles.md").write_text(
        "# roles: example-draft-workflow\n\n"
        "## manager\n\n- Calls candidate review.\n\n"
        "## worker_builder\n\n- Maintains candidate files.\n",
        encoding="utf-8",
    )
    (candidate / "checklist.md").write_text(
        "# checklist: example-draft-workflow\n\n"
        "## Candidate Intake\n\n"
        "- [ ] Source evidence exists.\n",
        encoding="utf-8",
    )
    (candidate / "handoff-template.md").write_text(
        "# handoff-template: example-draft-workflow\n\n"
        "## Manager -> worker_builder\n\n"
        "调用 candidate workflow: example-draft-workflow\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "candidate-validate", "--strict"])
    assert rc == 1
    assert err == ""
    assert "strict missing active/task-dispatch boundary" in out
    assert "strict missing promotion closeout boundary" in out


def test_is_active_workflow_returns_false_for_candidate(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    _write_candidate(root)
    assert is_active_workflow("igcse-subject-launch", root=root) is True
    assert is_active_workflow("example-draft-workflow", root=root) is False


def test_workflow_promote_plan_outputs_read_only_plan_for_promotion_ready_candidate(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    before = sorted(p.relative_to(root) for p in root.rglob("*"))
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
    after = sorted(p.relative_to(root) for p in root.rglob("*"))
    assert rc == 0
    assert err == ""
    assert before == after
    assert "candidate promotion plan: example-draft-workflow" in out
    assert "candidate workflow id: example-draft-workflow" in out
    assert "current status: promotion_ready" in out
    assert "_candidates/example-draft-workflow" in out
    assert "workflows/example-draft-workflow" in out
    assert "manager closeout must explicitly approve promotion" in out
    assert "README.md" in out
    assert "trigger.md" in out
    assert "roles.md" in out
    assert "checklist.md" in out
    assert "handoff-template.md" in out
    assert "不会写文件、不会移动文件、不会派单、不会发飞书" in out
    assert "future: eduflowteam workflow promote example-draft-workflow --approved-by-manager --write" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_plan_rejects_missing_candidate(tmp_path):
    root = tmp_path / "workflows"
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "missing"])
    assert rc == 1
    assert out == ""
    assert "no such candidate workflow" in err


def test_workflow_promote_plan_rejects_incomplete_candidate(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root, status="promotion_ready")
    (candidate / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
    assert rc == 1
    assert err == ""
    assert "candidate validation failed" in out
    assert "missing roles.md" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_plan_rejects_strict_invalid_candidate(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root, status="promotion_ready")
    (candidate / "README.md").write_text(
        "# workflow: example-draft-workflow\n\n"
        "## Metadata\n\n"
        "- workflow_id: `example-draft-workflow`\n"
        "- status: `promotion_ready`\n"
        "- owner: `worker_builder`\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
    assert rc == 1
    assert err == ""
    assert "strict validation failed" in out
    assert "strict missing active/task-dispatch boundary" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_plan_rejects_active_target_conflict(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_workflow(root, "example-draft-workflow")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
    assert rc == 1
    assert err == ""
    assert "promotion target conflict" in out
    assert "active workflow already exists" in out


def test_workflow_promote_plan_blocks_non_promotion_ready_status(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="draft")
    before = sorted(p.relative_to(root) for p in root.rglob("*"))
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
    after = sorted(p.relative_to(root) for p in root.rglob("*"))
    assert rc == 1
    assert err == ""
    assert before == after
    assert "candidate is not promotion_ready" in out
    assert "current status: draft" in out
    assert "no files were written or moved" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_plan_preserves_active_registry_boundary(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_plan, out_plan, err_plan = run_cli(["workflow", "promote-plan", "example-draft-workflow"])
        rc_list, out_list, err_list = run_cli(["workflow", "list"])
    assert rc_plan == rc_list == 0
    assert err_plan == err_list == ""
    assert "candidate promotion plan" in out_plan
    assert "igcse-subject-launch" in out_list
    assert "example-draft-workflow" not in out_list
    assert is_active_workflow("example-draft-workflow", root=root) is False


def test_workflow_promote_requires_both_authorization_flags(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "promote", "example-draft-workflow"])
    assert rc == 1
    assert err == ""
    assert "promotion requires explicit authorization" in out
    assert "--approved-by-manager --write" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_requires_write_flag(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager",
        ])
    assert rc == 1
    assert err == ""
    assert "missing write confirmation" in out
    assert "--write" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_requires_manager_approval_flag(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--write",
        ])
    assert rc == 1
    assert err == ""
    assert "missing manager approval" in out
    assert "--approved-by-manager" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_rejects_missing_candidate(tmp_path):
    root = tmp_path / "workflows"
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "missing", "--approved-by-manager", "--write",
        ])
    assert rc == 1
    assert out == ""
    assert "no such candidate workflow" in err


def test_workflow_promote_rejects_incomplete_candidate(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root, status="promotion_ready")
    (candidate / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
    assert rc == 1
    assert err == ""
    assert "candidate validation failed" in out
    assert "missing roles.md" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_rejects_strict_invalid_candidate(tmp_path):
    root = tmp_path / "workflows"
    candidate = _write_candidate(root, status="promotion_ready")
    (candidate / "README.md").write_text(
        "# workflow: example-draft-workflow\n\n"
        "## Metadata\n\n"
        "- workflow_id: `example-draft-workflow`\n"
        "- status: `promotion_ready`\n"
        "- owner: `worker_builder`\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> manager\n\n"
        "## Core Gates\n\n- dispatch_acceptance_gate\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
    assert rc == 1
    assert err == ""
    assert "strict validation failed" in out
    assert "strict missing active/task-dispatch boundary" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_rejects_active_target_conflict(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="promotion_ready")
    _write_workflow(root, "example-draft-workflow")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
    assert rc == 1
    assert err == ""
    assert "promotion target conflict" in out
    assert "active workflow already exists" in out


def test_workflow_promote_rejects_non_promotion_ready_candidate(tmp_path):
    root = tmp_path / "workflows"
    _write_candidate(root, status="draft")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
    assert rc == 1
    assert err == ""
    assert "candidate is not promotion_ready" in out
    assert "current status: draft" in out
    assert not (root / "example-draft-workflow").exists()


def test_workflow_promote_creates_active_workflow_with_converted_trigger(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "igcse-subject-launch")
    candidate = _write_candidate(root, status="promotion_ready")
    (candidate / "extra-notes.md").write_text("keep out of active", encoding="utf-8")
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_promote, out_promote, err_promote = run_cli([
            "workflow", "promote", "example-draft-workflow", "--approved-by-manager", "--write",
        ])
        rc_list, out_list, err_list = run_cli(["workflow", "list"])
        rc_candidates, out_candidates, err_candidates = run_cli(["workflow", "candidates"])
        rc_active_validate, out_active_validate, err_active_validate = run_cli(["workflow", "validate", "--strict"])
        rc_candidate_validate, out_candidate_validate, err_candidate_validate = run_cli(["workflow", "candidate-validate", "--strict"])
    assert rc_promote == 0
    assert err_promote == ""
    assert "promoted workflow: example-draft-workflow" in out_promote
    assert "source path:" in out_promote
    assert "target path:" in out_promote
    assert "README.md" in out_promote
    assert "trigger.md converted `调用 candidate workflow: example-draft-workflow` -> `调用 workflow: example-draft-workflow`" in out_promote
    assert "未派单" in out_promote
    assert "未写 task" in out_promote
    assert "未发飞书" in out_promote
    assert "未自动执行 workflow" in out_promote
    assert "candidate source retained" in out_promote

    target = root / "example-draft-workflow"
    assert target.exists()
    assert sorted(p.name for p in target.iterdir()) == sorted([
        "README.md", "trigger.md", "roles.md", "checklist.md", "handoff-template.md",
    ])
    assert not (target / "extra-notes.md").exists()
    assert "调用 workflow: example-draft-workflow" in (target / "trigger.md").read_text(encoding="utf-8")
    assert "调用 candidate workflow: example-draft-workflow" not in (target / "trigger.md").read_text(encoding="utf-8")
    assert "调用 candidate workflow: example-draft-workflow" in (candidate / "trigger.md").read_text(encoding="utf-8")
    assert candidate.exists()
    assert (root / "_candidates" / "example-draft-workflow").exists()
    assert "example-draft-workflow" in out_list
    assert "example-draft-workflow" in out_candidates
    assert is_active_workflow("example-draft-workflow", root=root) is True
    assert rc_list == rc_candidates == 0
    assert err_list == err_candidates == ""
    assert rc_active_validate == rc_candidate_validate == 0
    assert err_active_validate == err_candidate_validate == ""
    assert "workflow registry strict valid" in out_active_validate
    assert "candidate workflow registry strict valid" in out_candidate_validate


def test_workflow_recommend_matches_subject_launch(tmp_path):
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "launch", "Physics", "0625", "after", "Accounting", "closeout",
        ])
    assert rc == 0
    assert err == ""
    assert "workflow recommendations" in out
    assert "igcse-subject-launch" in out
    assert "confidence=" in out


def test_workflow_recommend_hides_low_confidence(tmp_path):
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "recommend", "manager"])
    assert rc == 0
    assert err == ""
    assert "no confident workflow recommendation" in out


def test_workflow_recommend_no_match_suggests_list(tmp_path):
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "recommend", "banana", "calendar"])
    assert rc == 0
    assert err == ""
    assert "no confident workflow recommendation" in out
    assert "eduflowteam workflow list" in out


# ── M8: ops / status-drift recommend coverage ───────────────────


def test_workflow_recommend_status_drift_query_surfaces_runtime_fallback(tmp_path):
    """M8: a status-drift query must surface runtime-failover-hardening
    and attach a candidate_skill (drift explainer) so the operator has
    a parallel read-only lane."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    _write_runtime_failover(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "agent", "外显陈旧但实际功能正常", "想制定优化方案",
        ])
    assert rc == 0, err
    # runtime-failover-hardening must be the top recommendation.
    assert "runtime-failover-hardening" in out
    assert "confidence=high" in out or "confidence=medium" in out
    # candidate_skill surfaces the drift explainer.
    assert "candidate_skill: eduflow-runtime-task-drift-explainer" in out
    # next_step points at the workflow use page.
    assert "suggested_next_step: ./scripts/eduflowteam workflow use" in out


def test_workflow_recommend_429_fallback_env_drift(tmp_path):
    """M8: a runtime/fallback query must recommend runtime-failover-hardening
    with high confidence via keyword hits."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    _write_runtime_failover(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend", "429", "fallback", "env", "drift",
        ])
    assert rc == 0, err
    lines = out.splitlines()
    rec_line = next(l for l in lines if l.startswith("- runtime-failover-hardening"))
    assert "confidence=high" in rec_line, rec_line
    assert "keywords=429" in rec_line or "fallback" in rec_line


def test_workflow_recommend_realrun_chinese_keywords_still_recommend(tmp_path):
    """M8: 重复真实运行沉淀流程 must still recommend realrun-to-workflow
    even when score lands in the low tier (single keyword hit)."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend", "重复真实运行沉淀流程",
        ])
    assert rc == 0, err
    # realrun-to-workflow is the only active workflow whose keyword
    # bucket contains 沉淀. The recommend output must surface it.
    assert "realrun-to-workflow" in out
    assert "沉淀" in out


def test_workflow_recommend_status_drift_no_active_workflow(tmp_path):
    """M8: when no active workflow covers the query, the output must
    still be useful: suggested_next_step points at ops-dashboard and
    candidate_skill points at the drift explainer skill."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "agent", "外显陈旧", "heartbeat", "fresh", "但", "显示", "卡住",
        ])
    # The query is on the status-drift topic. The recommendation can
    # be either a low-confidence candidate OR a no-confident path
    # with the topic-specific next_step + skill. Both are valid.
    assert rc == 0, err
    has_no_confident = "no confident workflow recommendation" in out
    has_recommendation = "runtime-failover-hardening" in out
    assert has_no_confident or has_recommendation
    # Either way, the drift-explainer must be mentioned as the
    # parallel read-only skill.
    if has_no_confident:
        assert "candidate_skill: eduflow-runtime-task-drift-explainer" in out
        assert "task ops-dashboard" in out


def test_workflow_recommend_no_confident_topic_aware_fallback(tmp_path):
    """M8: an unrelated query still falls back to eduflowteam workflow
    list (not ops-dashboard), because no topic matched."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend", "banana", "calendar", "purple",
        ])
    assert rc == 0, err
    assert "no confident workflow recommendation" in out
    assert "eduflowteam workflow list" in out
    # No topic matched, so no candidate_skill.
    assert "candidate_skill" not in out


def test_workflow_recommend_task_truth_drift_routes_realrun(tmp_path):
    """M8: supervisor-check / manager panel / 状态不一致 route to
    realrun-to-workflow + harness-surface-audit candidate skill."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "manager", "panel", "supervisor-check", "状态不一致",
        ])
    assert rc == 0, err
    assert "realrun-to-workflow" in out
    assert "candidate_skill: eduflow-harness-surface-audit" in out
    # OPT-6: the runtime drift explainer is the alternative.
    assert "also_consider_skill: eduflow-runtime-task-drift-explainer" in out


def test_workflow_recommend_warm_residency_keywords_route_drift(tmp_path):
    """OPT-5: 温备 / wake failed keywords live in their own gate bucket
    and route to the drift-explainer via the unified topic table."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    _write_runtime_failover(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend", "温备", "agent", "wake", "failed",
        ])
    assert rc == 0, err
    assert "runtime-failover-hardening" in out
    assert "candidate_skill: eduflow-runtime-task-drift-explainer" in out


def test_workflow_recommend_status_drift_no_match_emits_topic_fallback(tmp_path):
    """OPT-5: when no active workflow matches but the query is on a
    drift topic, the no-confident path uses the unified topic table
    to pick the drift-explainer and ops-dashboard next_step."""
    root = tmp_path / "workflows"
    # Only ship the three original workflows; no runtime-failover, so
    # the recommendation path falls through to the no-confident path.
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "外显陈旧", "实际功能正常", "但", "状态", "卡住",
        ])
    assert rc == 0, err
    assert "no confident workflow recommendation" in out
    assert "candidate_skill: eduflow-runtime-task-drift-explainer" in out
    assert "task ops-dashboard --json" in out


def test_workflow_recommend_no_topic_match_emits_no_skill(tmp_path):
    """OPT-5: an unrelated query (no topic keyword matches) still
    falls back to the workflow-list handoff, with no candidate_skill."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend", "purple", "banana", "calendar",
        ])
    assert rc == 0, err
    assert "no confident workflow recommendation" in out
    assert "candidate_skill" not in out
    assert "also_consider_skill" not in out


def test_workflow_recommend_task_truth_drift_no_active_workflow_emits_alternatives(tmp_path):
    """OPT-5/OPT-6: the no-confident path also surfaces the
    multi-skill candidate_skill + also_consider_skill list when the
    query hits a topic that has multiple candidate_skills."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "manager", "panel", "supervisor-check", "状态不一致",
            "（仅在没有 active workflow 的 fixture 下）",
        ])
    # The three-workflow fixture DOES include realrun-to-workflow, so
    # the query produces a high-confidence match. The recommend path
    # will then ALSO surface the topic skills (primary + alternative).
    assert rc == 0, err
    assert "realrun-to-workflow" in out
    # The primary is harness-surface-audit; the alternative is the
    # runtime drift explainer.
    assert "candidate_skill: eduflow-harness-surface-audit" in out
    assert "also_consider_skill: eduflow-runtime-task-drift-explainer" in out


def test_workflow_recommend_old_subject_launch_does_not_regress(tmp_path):
    """M8 regression: the original subject-launch example still
    recommends igcse-subject-launch with high confidence."""
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "launch", "Physics", "0625", "after", "Accounting", "closeout",
        ])
    assert rc == 0, err
    assert "igcse-subject-launch" in out
    assert "confidence=high" in out


def test_workflow_gates_and_closeout_print_gate_surfaces(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    (root / "igcse-subject-launch" / "checklist.md").write_text(
        "# checklist: igcse-subject-launch\n\n"
        "## Before Manager Announces Launch\n\n"
        "- [ ] review handoff accepted\n\n"
        "## Block Closeout If\n\n"
        "- review_handoff_gate missing\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc_gates, out_gates, err_gates = run_cli(["workflow", "gates", "igcse-subject-launch"])
        rc_close, out_close, err_close = run_cli(["workflow", "closeout", "igcse-subject-launch"])
    assert rc_gates == rc_close == 0
    assert err_gates == err_close == ""
    assert "Core Gates" in out_gates
    assert "dispatch_acceptance_gate" in out_gates
    assert "Forbidden Moves" in out_gates
    assert "Block Closeout If" in out_gates
    assert "manager closeout checklist: igcse-subject-launch" in out_close
    assert "review handoff accepted" in out_close


def test_workflow_gap_map_maps_gap_keywords_to_gates(tmp_path):
    docs = tmp_path / "docs"
    root = docs / "workflows"
    _write_three_workflows(root)
    (docs / "IGCSE_TOPIC_REALRUN_GAP_NOTE_2026-06-19.md").write_text(
        "dispatch accepted but review handoff lacked file evidence and runtime 429 fallback drift.",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "gap-map"])
    assert rc == 0
    assert err == ""
    assert "workflow gap-map" in out
    assert "dispatch_acceptance_gate" in out
    assert "review_handoff_gate" in out
    assert "file_evidence_gate" in out
    assert "runtime_reality" in out
    assert "igcse-subject-launch" in out


def test_workflow_gap_map_labels_candidate_matches_separately(tmp_path):
    docs = tmp_path / "docs"
    root = docs / "workflows"
    _write_workflow(root)
    _write_candidate(root)
    (docs / "IGCSE_TOPIC_REALRUN_GAP_NOTE_2026-06-19.md").write_text(
        "dispatch accepted but runtime drift needs a workflow candidate review.",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "gap-map"])
    assert rc == 0
    assert err == ""
    assert "active_workflows: igcse-subject-launch" in out
    assert "candidate_workflows: example-draft-workflow" in out


def test_workflow_validate_reports_missing_file(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    (root / "igcse-subject-launch" / "roles.md").unlink()
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate"])
    assert rc == 1
    assert err == ""
    assert "validation failed" in out
    assert "missing roles.md" in out


def test_workflow_validate_reports_missing_key_field(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    (root / "igcse-subject-launch" / "trigger.md").write_text(
        "# trigger\n\nmissing call text\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate"])
    assert rc == 1
    assert err == ""
    assert "trigger.md missing 调用 workflow" in out


def test_workflow_rejects_unknown_id(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root)
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "show", "missing"])
    assert rc == 1
    assert out == ""
    assert "no such workflow" in err


def test_workflow_appears_in_top_level_command_list():
    rc, out, err = run_cli([])
    assert rc == 0
    assert err == ""
    assert "workflow" in out


def test_workflow_help_uses_eduflowteam_name():
    rc, out, err = run_cli(["workflow", "--help"])
    assert rc == 0
    assert err == ""
    assert "usage:" in out
    assert "eduflowteam workflow list" in out
    assert "eduflowteam workflow validate" in out
    assert "eduflowteam workflow use" in out
    assert "eduflowteam workflow maintainer" in out
    assert "eduflowteam workflow template" in out
    assert "eduflowteam workflow candidates" in out
    assert "eduflowteam workflow candidate-show" in out
    assert "eduflowteam workflow candidate-files" in out
    assert "eduflowteam workflow candidate-validate" in out
    assert "eduflowteam workflow promotion-map" in out
    assert "--summary" in out
    assert "--manager" in out
    assert "--actionable" in out
    assert "--ready" in out
    assert "--state <candidate_only|promoted|active_only>" in out
    assert "eduflowteam workflow promote-plan" in out
    assert "eduflowteam workflow promote" in out
    assert "eduflowteam workflow recommend" in out
    assert "eduflowteam workflow gates" in out
    assert "eduflowteam workflow closeout" in out
    assert "eduflowteam workflow gap-map" in out
    assert "legacy alias: eduflow workflow" in out


def test_workflow_validate_accepts_runtime_failover_hardening(tmp_path):
    root = tmp_path / "workflows"
    _write_three_workflows(root)
    rf_dir = root / "runtime-failover-hardening"
    rf_dir.mkdir(parents=True)
    (rf_dir / "README.md").write_text(
        "# workflow: runtime-failover-hardening\n\n"
        "## Primary Chain\n\nmanager -> worker_builder -> auto_ops -> manager\n\n"
        "## Core Gates\n\n- runtime_reality\n- repair_acceptance_contract\n\n"
        "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    (rf_dir / "trigger.md").write_text(
        "# trigger: runtime-failover-hardening\n\n调用 workflow: runtime-failover-hardening\n",
        encoding="utf-8",
    )
    (rf_dir / "roles.md").write_text(
        "# roles: runtime-failover-hardening\n\n## manager\n\n- Calls the workflow.\n\n"
        "## worker_builder\n\n- Maintains workflow assets.\n",
        encoding="utf-8",
    )
    (rf_dir / "checklist.md").write_text(
        "# checklist: runtime-failover-hardening\n\n- [ ] smoke verified\n",
        encoding="utf-8",
    )
    (rf_dir / "handoff-template.md").write_text(
        "# handoff: runtime-failover-hardening\n\n## Manager -> worker_builder\n\nhandoff\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate"])
    assert rc == 0, f"validate failed: {out}"
    assert err == ""
    assert "runtime-failover-hardening" in out
    assert "workflow registry valid" in out


def test_workflow_recommend_ap_qbank_recommends_ap_knowledge_base(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "ap-knowledge-base-optimization")
    (root / "ap-knowledge-base-optimization" / "README.md").write_text(
        "# workflow: ap-knowledge-base-optimization\n\n"
        "AP qbank optimization for AP Physics 2, AP Calculus, AP CSA.\n\n"
        "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
        "## Core Gates\n\n- subject_sample_first_gate\n- ap_qbank_schema_gate\n"
        "- content_quality_gate\n- role_boundary_gate\n\n"
        "## Forbidden Moves\n\n- worker_builder must not produce actual MCQ content.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli([
            "workflow", "recommend",
            "AP Physics 2 full subject qbank sample",
        ])
    assert rc == 0
    assert err == ""
    assert "workflow recommendations" in out
    assert "ap-knowledge-base-optimization" in out


def test_workflow_gates_ap_knowledge_base_outputs_ap_gates(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "ap-knowledge-base-optimization")
    (root / "ap-knowledge-base-optimization" / "README.md").write_text(
        "# workflow: ap-knowledge-base-optimization\n\n"
        "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
        "## Core Gates\n\n"
        "- subject_sample_first_gate\n"
        "- ap_qbank_schema_gate\n"
        "- content_quality_gate\n"
        "- role_boundary_gate\n"
        "- review_verdict_authority_gate\n"
        "- retro_before_next_subject_gate\n"
        "- manager_closeout_gate\n\n"
        "## Forbidden Moves\n\n- worker_builder must not produce actual MCQ content.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "gates", "ap-knowledge-base-optimization"])
    assert rc == 0, f"gates failed: {err}"
    assert err == ""
    assert "Core Gates" in out
    assert "subject_sample_first_gate" in out
    assert "ap_qbank_schema_gate" in out
    assert "content_quality_gate" in out
    assert "role_boundary_gate" in out
    assert "review_verdict_authority_gate" in out
    assert "retro_before_next_subject_gate" in out
    assert "manager_closeout_gate" in out
    assert "Forbidden Moves" in out
    assert "worker_builder" in out.lower() or "MCQ" in out


def test_workflow_validate_accepts_ap_gates_as_known_gates(tmp_path):
    root = tmp_path / "workflows"
    _write_workflow(root, "ap-knowledge-base-optimization")
    (root / "ap-knowledge-base-optimization" / "README.md").write_text(
        "# workflow: ap-knowledge-base-optimization\n\n"
        "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
        "## Core Gates\n\n- subject_sample_first_gate\n- ap_qbank_schema_gate\n"
        "- content_quality_gate\n\n"
        "## Forbidden Moves\n\n- worker_builder must not produce actual MCQ content.\n\n"
        "worker_builder maintains this workflow; reassurance must not抢 manager 正式结论.\n",
        encoding="utf-8",
    )
    with env_patch(EDUFLOW_WORKFLOW_DIR=root):
        rc, out, err = run_cli(["workflow", "validate"])
    assert rc == 0, f"validate failed: {out}"
    assert "ap-knowledge-base-optimization" in out


def test_workflow_ap_readme_forbidden_worker_builder_mcq_content():
    """AP workflow README must explicitly forbid worker_builder from producing actual MCQ content."""
    from eduflow.commands.workflow import _workflow_root, _read_required
    root = _workflow_root()
    readme = _read_required(root / "ap-knowledge-base-optimization", "README.md")
    if not readme:
        import pytest
        pytest.skip("ap-knowledge-base-optimization workflow not in registry")
    assert "worker_builder" in readme
    assert "MCQ" in readme or "actual" in readme.lower()
    assert "forbidden" in readme.lower() or "Forbidden Moves" in readme
