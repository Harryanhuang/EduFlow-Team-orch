"""`eduflow task <subcommand>`

  task create <assignee> <title> [--by <agent>] [--desc <text>]
  task flow-create <assignee> <title> --stage S --owner O [--by <agent>] [--desc <text>] [--workflow W]
  task dispatch <assignee> <title> --stage S --owner O [--by manager] [--desc text] [--workflow W]
  task correct <agent> "<correction_content>" [--severity high|medium|critical] [--context "<ctx>"] [--force | --no-sensitive-check]
  task flow-transition <id> --to S --actor A
  task submit-review <id> --actor A
  task assign-reviewer <id> --reviewer R [--by manager]
  task review <id> --actor reviewer (--approve | --reject | --manager-action)
  task review-queue [--stage S] [--reviewer R]
  task workflow-status <id>
  task subject-inventory
  task batch-closeout <id> --actor manager
  task manager-closeout <id> --actor manager
  task manager-overview
  task scan-anomalies
  task auto-ops-context [--send-manager]
  task auto-ops-production [--send-manager]
  task manager-actions
  task manager-action-apply <action_code> --subject-id <id> [--confirm] [--skip-verifier]
  task manager-panel
  task ops-dashboard [--json] [--text] [--deep-manager-actions]
  task evidence-account [--task-id T] [--workflow W] [--json]
  task evidence-explain <task_id> [--json]
  task loop-check <task_id> [--spec code-repair] [--max-cycles N] [--new-run] [--allow-unscoped-workspace] [--background]
  task loop-status <task_id|loop_id>
  task loop-list [--task-id T] [--status S]
  task supervisor-check [--advance] [--send] [--json]
  # downstream helpers (Phase 2/3 skeletons; not Phase 1 core)
  task publish-check <id> --sender A [--to T]
  task publish-scan [--to T] [--include-silent] [--advance]
  task publish-run [--to T] [--send] [--advance]
  task update <id>       [--status S] [--assignee A] [--title T] [--desc D]
  task list              [--status S] [--assignee A]
  task get <id>
  task done <id>          (alias for `update <id> --status 已完成`)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from eduflow.commands import say as say_cmd
from eduflow.commands import send as send_cmd
from eduflow.commands import workflow as workflow_cmd
from eduflow.runtime import (
    config, context_monitor, loop_preflight, loop_runner, loop_specs,
    paths, tmux, tunables,
)
from eduflow.store import (
    employee_read_model, evolution_packet, local_facts,
    loop_runs, operational_readiness, task_event_scanner, task_publish_gate, task_publish_render,
    task_loop_contract, tasks, team_loop_account, tool_risk, subject_verifier,
)
from eduflow.util import (
    error_exit, fmt_time_ms, maybe_print_help, pop_flag, usage_error,
    pop_bool_flag, print_json, now_ms,
)

_AUTO_STAGE_REASSURANCE_REASONS = frozenset({
    "worker_accepted",
    "worker_started",
    "worker_completed_handed_to_manager",
    # worker/reviewer self-reported failure: surfaces immediately so
    # the team sees the failed state in chat (otherwise it would
    # only show up in memory_candidates via the bridge).
    "worker_reported_failure",
})


def _verifier_bypass_allowed() -> bool:
    """Gate for the verifier skip escape hatch.

    Package 2 (Codex Q2): production CLI must never silently bypass the
    artifact verifier. The env var `EDUFLOW_VERIFIER_BYPASS_ALLOWED=1`
    is reserved for test fixtures that exercise closeout behaviour without
    a real content directory. Production runners leave the var unset and
    the skip flag is rejected.
    """
    import os as _os
    return _os.environ.get("EDUFLOW_VERIFIER_BYPASS_ALLOWED", "").strip() == "1"


USAGE = (
    "usage:\n"
    "  eduflow task create <assignee> <title> [--by <agent>] [--desc <text>]\n"
    "  eduflow task flow-create <assignee> <title> --stage S --owner O [--by <agent>] [--desc <text>] [--workflow W]\n"
    "  eduflow task dispatch <assignee> <title> --stage S --owner O [--by manager] [--desc <text>] [--workflow W] [--hermes-can-promote]\n"
    "    [--workspace-mode <shared|worktree|container|external_artifact>] [--workspace-path <path>] [--workspace-branch <branch>] [--workspace-base-commit <sha>]\n"
    "  eduflow task correct <agent> \"<correction_content>\" [--severity high|medium|critical] [--context \"<ctx>\"]\n"
    "  eduflow task flow-transition <id> --to S --actor A\n"
    "  eduflow task submit-review <id> --actor A\n"
    "  eduflow task assign-reviewer <id> --reviewer R [--by manager]\n"
    "  eduflow task review <id> --actor reviewer (--approve | --reject | --manager-action) [--reason R] [--scope-topic S] [--scope-file F] [--verdict-target T] [--required-fix R1] [--blocking-file F1] [--evidence-json JSON]\n"
    "  eduflow task review-queue [--stage S] [--reviewer R]\n"
    "  eduflow task workflow-status <id>\n"
    "  eduflow task subject-inventory\n"
    "  eduflow task batch-closeout <id> --actor manager\n"
    "  eduflow task manager-closeout <id> --actor manager\n"
    "  eduflow task manager-overview\n"
    "  eduflow task scan-anomalies\n"
    "  eduflow task auto-ops-context [--send-manager]\n"
    "  eduflow task auto-ops-production [--send-manager]\n"
    "  eduflow task manager-actions\n"
    "  eduflow task manager-action-apply <action_code> --subject-id <id> [--confirm] [--skip-verifier]\n"
    "  eduflow task manager-panel\n"
    "  eduflow task ops-dashboard [--json] [--text] [--deep-manager-actions]\n"
    "  eduflow task evidence-account [--task-id T] [--workflow W] [--json]\n"
    "  eduflow task evidence-explain <task_id> [--json]\n"
    "  eduflow task loop-check <task_id> [--spec code-repair] [--max-cycles N] [--new-run] [--allow-unscoped-workspace] [--background]\n"
    "  eduflow task loop-status <task_id|loop_id>\n"
    "  eduflow task loop-contract <task_id> [--json]\n"
    "  eduflow task tool-risk --command \"<cmd>\" [--json]\n"
    "  eduflow task evolution-packet <task_id> [--json]\n"
    "  eduflow task readiness-check <task_id> [--json] [--diagnostics]\n"
    "  eduflow task loop-list [--task-id T] [--status S]\n"
    "  eduflow task supervisor-check [--advance] [--send] [--json]\n"
    "  # downstream helpers (Phase 2/3 skeletons; not Phase 1 core)\n"
    "  eduflow task publish-check <id> --sender A [--to T]\n"
    "  eduflow task publish-scan [--to T] [--include-silent] [--advance]\n"
    "  eduflow task publish-run [--to T] [--send] [--advance]\n"
    "  eduflow task update <id>  [--status S] [--assignee A] [--title T] [--desc D]\n"
    "  eduflow task list  [--status S] [--assignee A] [--include-archived]\n"
    "  eduflow task get <id>\n"
    "  eduflow task archive [--older-than 90d] [--dry-run]\n"
    "  eduflow task archive-schedule [--interval daily] [--older-than 90d] [--enable <true|false>]\n"
    "  eduflow task done <id>\n"
    "  eduflow task report-failure <id> --actor <worker|reviewer> [--reason <text>]\n"
    "  eduflow task update-verdict <id> --actor <reviewer|manager> --verdict <approved|rejected|manager_action|pending> [--reason <text>]"
)


def _fmt_task(t: dict) -> list[str]:
    ts = fmt_time_ms(t["created_at"])
    head = f"{t['id']}  [{t['status']}]  {t['title']}"
    body = [f"  assignee: {t.get('assignee') or '-'}"]
    if t.get("stage"):
        body.append(f"  stage: {t['stage']}")
    if t.get("workflow_id"):
        body.append(f"  workflow_id: {t['workflow_id']}")
        gate = tasks.workflow_gate_status(t)
        body.append(f"  workflow_gate: {gate['gate']}")
        body.append(f"  workflow_gate_status: {gate['gate_status']}")
        body.append(f"  workflow_next_action: {gate['next_action']}")
    if t.get("owner"):
        body.append(f"  owner: {t['owner']}")
    if t.get("reviewer"):
        body.append(f"  reviewer: {t['reviewer']}")
    if t.get("verdict"):
        body.append(f"  verdict: {t['verdict']}")
    # M10: workspace policy display.  Show workspace_mode and
    # workspace_branch when set; workspace_path and base_commit are
    # only shown in the JSON output of task get to keep the text
    # format concise.
    if t.get("workspace_mode"):
        body.append(f"  workspace_mode: {t['workspace_mode']}")
    if t.get("workspace_branch"):
        body.append(f"  workspace_branch: {t['workspace_branch']}")
    if t.get("failure_reason"):
        # Show the worker's reported failure reason so reviewers see
        # why this task is in `failed` status.
        body.append(f"  failure_reason: {t['failure_reason']}")
    if t.get("manager_action_type"):
        body.append(f"  manager_action_type: {t['manager_action_type']}")
    if t.get("review_reason"):
        body.append(f"  review_reason: {t['review_reason']}")
    if t.get("loop_run_id"):
        for key in (
            "loop_run_id",
            "loop_status",
            "loop_cycle_count",
            "loop_stop_reason",
            "loop_recommended_action",
            "loop_evidence_ref",
            "loop_updated_by",
            "self_check_status",
            "review_check_status",
            "manager_closeout_status",
        ):
            value = t.get(key)
            if value not in ("", None):
                body.append(f"  {key}: {value}")
    if t.get("latest_turn_summary"):
        body.append(f"  latest_turn_summary: {t['latest_turn_summary']}")
    if t.get("scope_topic"):
        body.append(f"  scope_topic: {t['scope_topic']}")
    if t.get("scope_files"):
        body.append("  scope_files: " + ", ".join(str(item) for item in t["scope_files"]))
    if t.get("verdict_target"):
        body.append(f"  verdict_target: {t['verdict_target']}")
    if t.get("evidence_packet"):
        packet = t["evidence_packet"]
        bits = []
        for key in tasks.REVIEW_EVIDENCE_FIELDS:
            value = packet.get(key)
            if isinstance(value, list):
                shown = ",".join(str(item) for item in value)
            else:
                shown = str(value)
            bits.append(f"{key}={shown}")
        body.append("  evidence_packet: " + " ".join(bits))
    if t.get("schema_version") == 2:
        live_summary = tasks.flow_live_summary(t)
        if live_summary:
            body.append(f"  current_summary: {live_summary}")
        actions = tasks.subject_followup_actions(t)
        if actions:
            body.append("  subject_followups: " + ", ".join(actions))
    if t.get("creator"):
        body.append(f"  by: {t['creator']}")
    if t.get("description"):
        if t.get("schema_version") == 2:
            body.append(f"  initial_brief: {t['description']}")
        else:
            body.append(f"  desc: {t['description']}")
    body.append(f"  created: {ts}")
    return [head] + body


def _cmd_create(rest: list[str]) -> int:
    by = pop_flag(rest, "--by") or ""
    desc = pop_flag(rest, "--desc") or ""
    if len(rest) < 2:
        return usage_error(USAGE)
    assignee = rest[0]
    title = " ".join(rest[1:])
    try:
        tid = tasks.create(assignee, title, description=desc, creator=by)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    print(f"✅ created {tid}: {title} → {assignee}")
    return 0


def _cmd_flow_create(rest: list[str]) -> int:
    by = pop_flag(rest, "--by") or ""
    desc = pop_flag(rest, "--desc") or ""
    stage = pop_flag(rest, "--stage")
    owner = pop_flag(rest, "--owner")
    workflow_id = pop_flag(rest, "--workflow") or ""
    if len(rest) < 2 or not stage or not owner:
        return usage_error(USAGE)
    if workflow_id and not workflow_cmd.is_active_workflow(workflow_id):
        return error_exit(f"❌ unknown workflow: {workflow_id}")
    assignee = rest[0]
    title = " ".join(rest[1:])
    try:
        effective_workflow_id = tasks.normalize_required_workflow_id(
            title=title,
            stage=stage,
            workflow_id=workflow_id,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if effective_workflow_id and not workflow_cmd.is_active_workflow(effective_workflow_id):
        return error_exit(f"❌ unknown workflow: {effective_workflow_id}")
    try:
        tid = tasks.create_flow(
            assignee,
            title,
            stage=stage,
            owner=owner,
            creator=by,
            description=desc,
            workflow_id=effective_workflow_id,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    workflow_text = f" workflow={effective_workflow_id}" if effective_workflow_id else ""
    if effective_workflow_id and effective_workflow_id != workflow_id:
        workflow_text += " auto_mounted=true"
    print(f"✅ created flow task {tid}: {title} → {assignee} [{stage}] owner={owner}{workflow_text}")
    _print_dispatch_packet(assignee, tid)
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_dispatch(rest: list[str]) -> int:
    by = pop_flag(rest, "--by") or "manager"
    desc = pop_flag(rest, "--desc") or ""
    stage = pop_flag(rest, "--stage")
    owner = pop_flag(rest, "--owner")
    workflow_id = pop_flag(rest, "--workflow") or ""
    hermes_can_promote = pop_bool_flag(rest, "--hermes-can-promote")
    # M10: workspace policy flags.  All optional; unpassed flags
    # remain "" so the task store defaults to unset.
    workspace_mode = pop_flag(rest, "--workspace-mode") or ""
    workspace_path = pop_flag(rest, "--workspace-path") or ""
    workspace_branch = pop_flag(rest, "--workspace-branch") or ""
    workspace_base_commit = pop_flag(rest, "--workspace-base-commit") or ""
    if len(rest) < 2 or not stage or not owner:
        return usage_error(USAGE)
    if by != "manager":
        return error_exit("❌ dispatch currently only supports --by manager")
    if workflow_id and not workflow_cmd.is_active_workflow(workflow_id):
        return error_exit(f"❌ unknown workflow: {workflow_id}")
    assignee = rest[0]
    title = " ".join(rest[1:])
    try:
        effective_workflow_id = tasks.normalize_required_workflow_id(
            title=title,
            stage=stage,
            workflow_id=workflow_id,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if effective_workflow_id and not workflow_cmd.is_active_workflow(effective_workflow_id):
        return error_exit(f"❌ unknown workflow: {effective_workflow_id}")
    # If --hermes-can-promote was passed, record the marker in the
    # task description so the Hermes adapter (or any later
    # `memory promote` invocation) can see the manager's
    # authorization. This is purely advisory text — the actual
    # gate is in `candidates.promote_candidate`.
    if hermes_can_promote:
        marker = "\n[hermes-can-promote: true]"
        if marker.strip() not in desc:
            desc = (desc or "") + marker
    try:
        tid = tasks.create_flow(
            assignee,
            title,
            stage=stage,
            owner=owner,
            creator=by,
            description=desc,
            workflow_id=effective_workflow_id,
            workspace_mode=workspace_mode,
            workspace_path=workspace_path,
            workspace_branch=workspace_branch,
            workspace_base_commit=workspace_base_commit,
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
    except ValueError as e:
        return error_exit(f"❌ {e}")
    print(
        f"✅ dispatched {tid}: {title} → {assignee} "
        f"[{stage}] owner={owner} status=assigned"
        f"{(' workflow=' + effective_workflow_id) if effective_workflow_id else ''}"
        f"{' auto_mounted=true' if effective_workflow_id and effective_workflow_id != workflow_id else ''}"
    )
    if hermes_can_promote:
        print("  ↳ hermes_can_promote: manager authorized non-high-impact promotions")
    _print_dispatch_packet(assignee, tid)
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_update(rest: list[str]) -> int:
    status = pop_flag(rest, "--status")
    assignee = pop_flag(rest, "--assignee")
    title = pop_flag(rest, "--title")
    desc = pop_flag(rest, "--desc")
    if len(rest) < 1:
        return usage_error(USAGE)
    tid = rest[0]
    try:
        ok = tasks.update(tid, status=status, assignee=assignee,
                          title=title, description=desc)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    print(f"✅ updated {tid}")
    return 0


def _cmd_flow_transition(rest: list[str]) -> int:
    to_status = pop_flag(rest, "--to")
    actor = pop_flag(rest, "--actor")
    if len(rest) < 1 or not to_status or not actor:
        return usage_error(USAGE)
    tid = rest[0]
    try:
        ok = tasks.transition_flow(tid, to_status=to_status, actor=actor)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    print(f"✅ transitioned {tid} -> {to_status} ({actor})")
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_review(rest: list[str]) -> int:
    actor = pop_flag(rest, "--actor")
    review_reason = pop_flag(rest, "--reason") or ""
    latest_turn_summary = pop_flag(rest, "--summary") or ""
    manager_action_type = pop_flag(rest, "--manager-action-type") or ""
    scope_topic = pop_flag(rest, "--scope-topic") or ""
    verdict_target = pop_flag(rest, "--verdict-target") or ""
    evidence_json = pop_flag(rest, "--evidence-json") or ""
    scope_files = []
    while True:
        value = pop_flag(rest, "--scope-file")
        if value is None:
            break
        scope_files.append(value)
    required_fix = []
    while True:
        value = pop_flag(rest, "--required-fix")
        if value is None:
            break
        required_fix.append(value)
    blocking_files = []
    while True:
        value = pop_flag(rest, "--blocking-file")
        if value is None:
            break
        blocking_files.append(value)
    approve = pop_bool_flag(rest, "--approve")
    reject = pop_bool_flag(rest, "--reject")
    manager_action = pop_bool_flag(rest, "--manager-action")
    flags = [
        ("approve", approve),
        ("reject", reject),
        ("manager_action", manager_action),
    ]
    chosen = [name for name, enabled in flags if enabled]
    if len(rest) < 1 or not actor:
        return usage_error(USAGE)
    if len(chosen) != 1:
        return error_exit("❌ review requires exactly one outcome flag")
    tid = rest[0]
    outcome = chosen[0]
    evidence_packet = {}
    if evidence_json:
        try:
            evidence_packet = json.loads(evidence_json)
        except json.JSONDecodeError as e:
            return error_exit(f"❌ invalid evidence json: {e}")
    try:
        ok = tasks.review_flow(
            tid,
            outcome=outcome,
            actor=actor,
            review_reason=review_reason,
            latest_turn_summary=latest_turn_summary,
            manager_action_type=manager_action_type,
            scope_topic=scope_topic,
            scope_files=scope_files,
            verdict_target=verdict_target,
            evidence_packet=evidence_packet,
            required_fix=required_fix or None,
            blocking_files=blocking_files or None,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    task = tasks.get(tid) or {}
    print(
        f"✅ reviewed {tid} outcome={outcome} "
        f"status={task.get('status', '-')} verdict={task.get('verdict', '-')}"
    )
    if outcome == "reject":
        _bridge_review_reject(task, review_reason)
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_submit_review(rest: list[str]) -> int:
    actor = pop_flag(rest, "--actor")
    if len(rest) < 1 or not actor:
        return usage_error(USAGE)
    tid = rest[0]
    try:
        ok = tasks.submit_for_review(tid, actor=actor)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    task = tasks.get(tid) or {}
    print(
        f"✅ submitted {tid} for review "
        f"status={task.get('status', '-')} verdict={task.get('verdict', '-')}"
    )
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_assign_reviewer(rest: list[str]) -> int:
    reviewer = pop_flag(rest, "--reviewer")
    by = pop_flag(rest, "--by") or "manager"
    if len(rest) < 1 or not reviewer:
        return usage_error(USAGE)
    tid = rest[0]
    try:
        ok = tasks.assign_reviewer(tid, reviewer=reviewer, actor=by)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    print(f"✅ assigned reviewer {reviewer} to {tid}")
    _auto_publish_stage_tick(tid)
    return 0


def _auto_publish_stage_tick(task_id: str) -> None:
    """Best-effort one-task worker/reviewer reassurance after a state change.

    The long-running `task-publish` loop remains the normal batch publisher.
    This tick is a small UX safety net for live supervision: it only sends
    worker reassurance reasons, advances the same explanation/cursor state,
    and never blocks the task command on delivery failure.
    """
    if not bool(tunables.tunable("task.auto_publish_tick", True)):
        return
    if not config.chat_id():
        return
    try:
        rows = task_event_scanner.scan_publish_decisions(
            to_target="user",
            include_silent=True,
            advance=False,
        )
        selected = [
            row for row in rows
            if (
                str(row.get("task_id") or "") == task_id
                and bool(row.get("publish"))
                and str(row.get("reason") or "") in _AUTO_STAGE_REASSURANCE_REASONS
            )
        ]
        if not selected:
            return
        selected.sort(key=lambda row: int(row.get("created_at") or 0))
        for row in selected:
            task = tasks.get(str(row.get("task_id") or "")) or {}
            message = task_publish_render.render_publish_message(task, row)
            if not message:
                continue
            sender = str(task.get("assignee") or row.get("sender") or "manager")
            rc = say_cmd.main([sender, message, "--to", str(row.get("to_target") or "user")])
            if rc != 0:
                print(f"  ⚠️ auto publish tick failed for {task_id}")
                return
        explanation_state = task_event_scanner.read_explanation_state()
        sent = explanation_state.setdefault("sent", {})
        for row in selected:
            sent[f"{row.get('task_id') or ''}::{row.get('reason') or ''}"] = str(row.get("event_id") or "")
        task_event_scanner.write_explanation_state(explanation_state)
        print(f"  📣 auto stage reassurance published for {task_id}")
    except Exception as e:
        print(f"  ⚠️ auto publish tick skipped for {task_id}: {e}")


def _cmd_review_queue(rest: list[str]) -> int:
    stage = pop_flag(rest, "--stage")
    reviewer = pop_flag(rest, "--reviewer")
    if rest:
        return usage_error(USAGE)
    rows = tasks.list_review_queue(stage=stage, reviewer=reviewer)
    if not rows:
        print("📭 no tasks awaiting review")
        return 0
    head = "📥 awaiting review"
    if stage:
        head += f" [{stage}]"
    if reviewer:
        head += f" reviewer={reviewer}"
    print(head)
    for t in rows:
        print(
            f"{t['id']}  [{t.get('stage') or '-'}]  {t['title']}  "
            f"owner={t.get('owner') or '-'} assignee={t.get('assignee') or '-'} "
            f"reviewer={t.get('reviewer') or '-'}"
        )
    return 0


_WORKFLOW_HINTS = {
    "igcse-subject-launch": {
        "gate": "review_handoff_gate",
        "next_check": "workflow closeout igcse-subject-launch",
    },
    "igcse-item-level-prototype": {
        "gate": "file_evidence_gate",
        "next_check": "workflow gates igcse-item-level-prototype",
    },
    "realrun-to-workflow": {
        "gate": "artifact_standard_gate",
        "next_check": "workflow maintainer realrun-to-workflow",
    },
    "ap-knowledge-base-optimization": {
        "gate": "review_handoff_gate",
        "next_check": "task tier-status <id>",
    },
}


def _workflow_hint(row: dict) -> dict:
    workflow_id = str(row.get("workflow_id") or "").strip()
    if not workflow_id:
        return {}
    hint = _WORKFLOW_HINTS.get(workflow_id)
    if hint is None:
        return {
            "gate": "unknown_workflow",
            "next_check": f"workflow validate / workflow list ({workflow_id})",
        }
    return hint


def _cmd_manager_overview(rest: list[str]) -> int:
    if rest:
        return usage_error(USAGE)
    overview = tasks.manager_overview()
    print("📊 manager overview")
    for key in ("in_progress", "awaiting_review", "blocked", "manager_action", "subject_closeout"):
        rows = overview[key]
        print(f"{key}: {len(rows)}")
        for row in rows[:5]:
            print(
                f"  - {row['id']} [{row.get('stage') or '-'}] {row['title']} "
                f"owner={row.get('owner') or '-'} reviewer={row.get('reviewer') or '-'}"
                f"{(' workflow=' + row['workflow_id']) if row.get('workflow_id') else ''}"
            )
            live_summary = tasks.flow_live_summary(row)
            if live_summary:
                print(f"    manager_summary={live_summary}")
            workflow_hint = _workflow_hint(row)
            if workflow_hint:
                print(f"    workflow_gate_hint={workflow_hint['gate']}")
                print(f"    workflow_next_check={workflow_hint['next_check']}")
            if row.get("manager_action_type") or row.get("review_reason"):
                print(
                    "    "
                    f"manager_action_type={row.get('manager_action_type') or '-'} "
                    f"review_reason={row.get('review_reason') or '-'}"
                )
            if row.get("latest_turn_summary"):
                print(f"    latest_turn_summary={row['latest_turn_summary']}")
    return 0


def _cmd_scan_anomalies(rest: list[str]) -> int:
    if rest:
        return usage_error(USAGE)
    rows = task_event_scanner.scan_manager_anomalies()
    if not rows:
        print("📭 no manager-facing task anomalies")
        return 0
    print("🚨 manager-facing task anomalies")
    for row in rows:
        print(
            f"{row['category']}  task={row['task_id']}  "
            f"stage={row.get('stage') or '-'}  status={row.get('status') or '-'}"
        )
        if row.get("surface_state"):
            print(
                f"  surface_state: "
                f"{task_publish_render.describe_surface_state(str(row.get('surface_state') or ''))}"
            )
        print(f"  why: {row['why']}")
        print(f"  evidence: {row['evidence_summary']}")
        if row.get("recommended_action"):
            print(f"  recommended_action: {row['recommended_action']}")
        if row.get("action_packet"):
            _print_action_packet(row["action_packet"], indent="  ")
    return 0


def _auto_ops_context_row(agent: str, session: str, *, session_alive: bool) -> dict:
    row = {
        "agent": agent,
        "level": "unknown",
        "percent": None,
        "marker": "-",
        "recommended_action": "no_action",
        "allow_continue_original_task": True,
    }
    if not session_alive:
        row.update({
            "level": "no_session",
            "marker": f"tmux_session_missing:{session}",
            "recommended_action": "restore_team_runtime",
            "allow_continue_original_task": False,
        })
        return row

    target = tmux.Target(session, agent)
    if not tmux.has_window(target):
        row.update({
            "level": "no_window",
            "marker": "tmux_window_missing",
            "recommended_action": "hire_or_recover_agent",
            "allow_continue_original_task": False,
        })
        return row

    text = tmux.capture_pane(target, lines=80)
    signal = context_monitor.detect_context_usage(text)
    if signal is None:
        row.update({"level": "ok", "marker": "no_context_pressure_signal"})
        return row

    row.update({
        "level": signal.level,
        "percent": signal.percent,
        "marker": signal.marker,
    })
    if signal.exhausted:
        row.update({
            "recommended_action": "run_eduflow_compact_then_restart_or_reidentify_agent",
            "allow_continue_original_task": False,
        })
    elif signal.compact_recommended:
        row.update({
            "recommended_action": "run_eduflow_compact_agent_before_long_work",
            "allow_continue_original_task": False,
        })
    else:
        row.update({
            "recommended_action": "monitor_and_split_next_packet",
            "allow_continue_original_task": True,
        })
    return row


def _auto_ops_context_report(rows: list[dict]) -> str:
    risk_rows = [row for row in rows if row.get("level") not in {"ok"}]
    lines = [
        "auto_ops context snapshot",
        f"agents={len(rows)} risks={len(risk_rows)}",
    ]
    for row in rows:
        percent = row.get("percent")
        pct = "-" if percent is None else f"{percent:g}%"
        lines.append(
            f"- {row['agent']}: level={row['level']} pct={pct} "
            f"marker={row['marker']} "
            f"allow_continue_original_task="
            f"{str(bool(row.get('allow_continue_original_task'))).lower()} "
            f"recommended_action={row['recommended_action']}"
        )
    return "\n".join(lines)


def _cmd_auto_ops_context(rest: list[str]) -> int:
    send_manager = pop_bool_flag(rest, "--send-manager")
    if rest:
        return usage_error("usage: eduflow task auto-ops-context [--send-manager]")

    try:
        agents = sorted(config.agent_names())
    except Exception as e:
        return error_exit(f"❌ failed to load team agents: {e}")
    session = config.session_name()
    session_alive = tmux.has_session(session)
    rows = [
        _auto_ops_context_row(agent, session, session_alive=session_alive)
        for agent in agents
    ]
    report = _auto_ops_context_report(rows)
    print(report)

    if send_manager:
        message = (
            "auto_ops 全员 context 巡检：\n"
            f"{report}\n\n"
            "请 manager 只处理 recommended_action != no_action 的风险项；"
            "90% 以上必须运行 `eduflow compact <agent>` 或飞书 `/compact <agent>`，"
            "禁止只发文字提醒；100%/limit 再考虑 restart/reidentify。"
        )
        rc = send_cmd.main(["manager", "auto_ops", message, "高"])
        if rc == 0:
            print("sent_to_manager=true")
        return rc
    return 0


_PRODUCTION_ACTIVE_STATUSES = frozenset({"进行中", "已接单", "in_progress"})
_PRODUCTION_IDLE_STATUSES = frozenset({"待命", "空闲", "ready", "idle", "已交付"})
_PRODUCTION_STALE_AFTER_MS = 30 * 60 * 1000


def _task_short(value: str, *, limit: int = 90) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text or "-"
    return text[:limit - 1] + "…"


def _overview_work_for_agent(agent: str, overview: dict) -> dict:
    in_progress = [
        row for row in overview.get("in_progress", [])
        if str(row.get("assignee") or "") == agent
    ]
    awaiting_review = [
        row for row in overview.get("awaiting_review", [])
        if str(row.get("reviewer") or "") == agent
    ]
    blocked = [
        row for row in overview.get("blocked", []) + overview.get("manager_action", [])
        if str(row.get("assignee") or row.get("owner") or "") == agent
    ]
    return {
        "in_progress": in_progress,
        "awaiting_review": awaiting_review,
        "blocked": blocked,
    }


def _auto_ops_production_row(agent: str, overview: dict, now: int) -> dict:
    status_row = local_facts.get_status(agent) or {}
    status = str(status_row.get("status") or "")
    task_text = str(status_row.get("task") or "")
    updated_at = int(status_row.get("updated_at") or 0)
    heartbeat_at = int(local_facts.get_heartbeat(agent) or 0)
    last_signal_at = max(updated_at, heartbeat_at)
    age_min = None if last_signal_at <= 0 else max(now - last_signal_at, 0) // 60000
    high_unread = [
        msg for msg in local_facts.list_messages(agent, unread_only=True)
        if local_facts.is_high_priority(str(msg.get("priority") or ""))
    ]
    work = _overview_work_for_agent(agent, overview)
    guard = local_facts.runtime_guard_block_evidence(agent)
    state = "idle"
    next_action = "no_action"
    evidence = "no_active_work"

    if guard is not None:
        state = "blocked"
        next_action = f"recover_runtime:{agent}"
        evidence = "runtime_guard_escalation"
    elif high_unread:
        state = "waiting_manager" if agent == "manager" else "waiting_worker"
        next_action = (
            "manager_read_high_priority_inbox"
            if agent == "manager"
            else f"nudge_or_recover:{agent}"
        )
        evidence = f"high_priority_unread={len(high_unread)}"
    elif work["blocked"]:
        state = "blocked"
        next_action = f"manager_decide_blocked_task:{work['blocked'][0].get('id')}"
        evidence = f"blocked_task={work['blocked'][0].get('id')}"
    elif work["awaiting_review"]:
        state = "waiting_review"
        next_action = f"review_queue:{agent}"
        evidence = f"awaiting_review={work['awaiting_review'][0].get('id')}"
    elif work["in_progress"]:
        state = "active"
        evidence = f"in_progress_task={work['in_progress'][0].get('id')}"
    elif status in _PRODUCTION_ACTIVE_STATUSES:
        state = "active"
        evidence = f"status={status}"
    elif status in _PRODUCTION_IDLE_STATUSES:
        state = "idle"
        evidence = f"status={status}"
    elif not status and last_signal_at <= 0:
        state = "idle"
        evidence = "no_status_or_heartbeat"
    elif status:
        evidence = f"status={status}"

    if (
        state == "active"
        and last_signal_at > 0
        and now - last_signal_at >= _PRODUCTION_STALE_AFTER_MS
    ):
        state = "stale"
        next_action = f"peek_agent_pane:{agent}"
        evidence = f"active_signal_stale_min={age_min}"

    return {
        "agent": agent,
        "state": state,
        "status": status or "-",
        "task": _task_short(task_text),
        "high_unread": len(high_unread),
        "age_min": age_min,
        "evidence": evidence,
        "next_action": next_action,
    }


def _auto_ops_production_manager_next(rows: list[dict]) -> str:
    priority = {
        "waiting_manager": 0,
        "blocked": 1,
        "waiting_worker": 2,
        "waiting_review": 3,
        "stale": 4,
    }
    actionable = [
        row for row in rows
        if row.get("next_action") and row.get("next_action") != "no_action"
    ]
    if not actionable:
        return "no_action"
    actionable.sort(key=lambda row: (priority.get(str(row.get("state") or ""), 99), str(row.get("agent") or "")))
    return str(actionable[0]["next_action"])


def _auto_ops_production_report(rows: list[dict]) -> str:
    counts = {
        "active": 0,
        "blocked": 0,
        "waiting_manager": 0,
        "waiting_review": 0,
        "stale": 0,
    }
    for row in rows:
        if row.get("state") in counts:
            counts[str(row["state"])] += 1
    lines = [
        "auto_ops production snapshot",
        (
            f"active={counts['active']} blocked={counts['blocked']} "
            f"waiting_manager={counts['waiting_manager']} "
            f"waiting_review={counts['waiting_review']} stale={counts['stale']}"
        ),
    ]
    for row in rows:
        age = "-" if row.get("age_min") is None else f"{row['age_min']}m"
        lines.append(
            f"- {row['agent']}: state={row['state']} status={row['status']} "
            f"high_unread={row['high_unread']} age={age} "
            f"evidence={row['evidence']} next={row['next_action']} "
            f"task={row['task']}"
        )
    lines.append(f"manager_next_action={_auto_ops_production_manager_next(rows)}")
    return "\n".join(lines)


def _cmd_auto_ops_production(rest: list[str]) -> int:
    send_manager = pop_bool_flag(rest, "--send-manager")
    if rest:
        return usage_error("usage: eduflow task auto-ops-production [--send-manager]")
    try:
        agents = sorted(config.agent_names())
        overview = tasks.manager_overview()
    except Exception as e:
        return error_exit(f"❌ failed to load team production state: {e}")
    rows = [_auto_ops_production_row(agent, overview, now_ms()) for agent in agents]
    report = _auto_ops_production_report(rows)
    print(report)
    if send_manager:
        message = (
            "auto_ops 全员生产状态巡检：\n"
            f"{report}\n\n"
            "请 manager 优先处理 manager_next_action；若为 no_action，保持现有派发节奏。"
        )
        rc = send_cmd.main(["manager", "auto_ops", message, "高"])
        if rc == 0:
            print("sent_to_manager=true")
        return rc
    return 0


def _task_brief(row: dict) -> str:
    brief = (
        f"{row['id']} [{row.get('stage') or '-'}] {row['title']} "
        f"owner={row.get('owner') or '-'} reviewer={row.get('reviewer') or '-'}"
    )
    if row.get("workflow_id"):
        brief += f" workflow={row['workflow_id']}"
        workflow_hint = _workflow_hint(row)
        if workflow_hint:
            brief += (
                f" workflow_gate_hint={workflow_hint['gate']}"
                f" workflow_next_check={workflow_hint['next_check']}"
            )
    live_summary = tasks.flow_live_summary(row)
    if live_summary:
        brief += f" :: {live_summary}"
    elif row.get("manager_action_type") or row.get("review_reason"):
        if row.get("manager_action_type"):
            brief += f" manager_action_type={row['manager_action_type']}"
        if row.get("review_reason"):
            brief += f" review_reason={row['review_reason']}"
    return brief


def _is_workflow_drive_task(row: dict) -> bool:
    """Tasks that should be surfaced in the manager-panel workflow drive lane.

    Includes all IGCSE/AP subject production tasks (regardless of whether the
    workflow_id is mounted yet) and any task that already carries a workflow_id.
    """
    if not isinstance(row, dict) or not row.get("id"):
        return False
    if row.get("schema_version") != 2:
        return False
    if str(row.get("status") or "") in {"delivered", "cancelled", "failed", "已完成", "已取消"}:
        return False
    if str(row.get("workflow_id") or "").strip():
        return True
    if tasks.is_igcse_course_task(
        title=str(row.get("title") or ""),
        stage=str(row.get("stage") or ""),
    ):
        return True
    if tasks.is_ap_knowledge_task(
        title=str(row.get("title") or ""),
        stage=str(row.get("stage") or ""),
    ):
        return True
    return False


def _collect_workflow_drive_rows() -> list[dict]:
    """Return active tasks that should appear in the workflow drive lane."""
    rows = tasks.list_tasks()
    return [row for row in rows if _is_workflow_drive_task(row)]


def _collect_revision_priority_blockers() -> list[dict]:
    """Return active flow tasks whose revision_priority is still set.

    Package 7 (Revision-First Gate): these tasks take priority over any
    continuation logic. The manager-panel and manager-action surfaces
    must surface them before continue_next_batch / select_next_subject
    recommendations.
    """
    rows = tasks.list_tasks()
    blockers: list[dict] = []
    for row in rows:
        if row.get("schema_version") != 2:
            continue
        if str(row.get("status") or "") in {"delivered", "cancelled", "failed", "已完成", "已取消"}:
            continue
        revision_priority = str(row.get("revision_priority") or "").strip()
        if not revision_priority:
            continue
        gate = tasks.workflow_gate_status(row)
        blockers.append({
            "task_id": str(row.get("id") or ""),
            "title": str(row.get("title") or ""),
            "workflow_id": str(row.get("workflow_id") or "").strip(),
            "revision_priority": revision_priority,
            "scope_topic": str(row.get("scope_topic") or "").strip(),
            "owner": str(row.get("owner") or row.get("assignee") or "").strip(),
            "next_action": str(gate.get("next_action") or ""),
            "recommended_action": "clear_revision_priority_or_stay_in_scope",
        })
    return blockers


def _packet_apply_allowed_for_subject(subject_id: str, packets: list[dict]) -> bool:
    return any(
        str(p.get("subject_id") or "") == subject_id
        and bool(p.get("apply_allowed"))
        for p in packets
    )


def _packet_blocking_reasons_for_subject(subject_id: str, packets: list[dict]) -> list[str]:
    """Surface blocking reasons from the action packet layer.

    This keeps the manager-action / manager-panel views honest about WHY a
    packet is not yet apply_allowed, while staying quiet when the gate is
    green. Each packet reports only its own critical blockers, not the
    downstream follow-ups (qbank readiness is a follow-up, not a blocker
    for manager_formal_closeout).
    """
    reasons: list[str] = []
    for p in packets:
        if str(p.get("subject_id") or "") != subject_id:
            continue
        action_code = str(p.get("action_code") or "")
        gate = p.get("closeout_gate") or {}
        if action_code == "manager_formal_closeout":
            if gate.get("review_approved") is False:
                _append_unique(reasons, "review_not_approved")
            if gate.get("evidence_present") is False:
                _append_unique(reasons, "evidence_missing")
            if gate.get("qa_standard_met") is False:
                _append_unique(reasons, "qa_standard_not_met")
            # qbank_ready is a downstream follow-up, not a blocker for
            # manager_formal_closeout itself.
            continue
        # Generic case: report every gate field that is False.
        for key, label in (
            ("review_approved", "review_not_approved"),
            ("evidence_present", "evidence_missing"),
            ("qa_standard_met", "qa_standard_not_met"),
            ("qbank_ready", "qbank_not_ready"),
        ):
            if gate.get(key) is False:
                _append_unique(reasons, label)
    return reasons


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _workflow_drive_line(row: dict, *, packets: list[dict] | None = None) -> str:
    """Single-line summary of a task's workflow drive state for manager-panel.

    Keeps the field order stable for grep-based operators/tests:
    workflow_id | workflow_gate | workflow_gate_status | next_action |
    apply_allowed | blocking_reasons
    """
    task_id = str(row.get("id") or "")
    title = str(row.get("title") or "-")
    gate = tasks.workflow_gate_status(row)
    workflow_id = str(gate.get("workflow_id") or "").strip()
    if not workflow_id:
        # Subject task but workflow was never mounted: surface it explicitly.
        is_igcse = tasks.is_igcse_course_task(
            title=str(row.get("title") or ""),
            stage=str(row.get("stage") or ""),
        )
        is_ap = tasks.is_ap_knowledge_task(
            title=str(row.get("title") or ""),
            stage=str(row.get("stage") or ""),
        )
        if is_igcse:
            return (
                f"{task_id} [{row.get('stage') or '-'}] {title} "
                f"workflow_missing=true "
                f"workflow_id=- "
                f"workflow_gate=- "
                f"workflow_gate_status=- "
                f"next_action=mount_igcse_subject_launch_workflow "
                f"apply_allowed=false "
                f"blocking_reasons=workflow_not_mounted"
            )
        if is_ap:
            return (
                f"{task_id} [{row.get('stage') or '-'}] {title} "
                f"workflow_missing=true "
                f"workflow_id=- "
                f"workflow_gate=- "
                f"workflow_gate_status=- "
                f"next_action=mount_ap_knowledge_base_optimization_workflow "
                f"apply_allowed=false "
                f"blocking_reasons=workflow_not_mounted"
            )
        return ""
    next_action = str(gate.get("next_action") or "-")
    apply_allowed = _packet_apply_allowed_for_subject(task_id, packets or [])
    reasons = _packet_blocking_reasons_for_subject(task_id, packets or [])
    if not apply_allowed and not reasons:
        # Even when no subject-closeout packet exists, the closeout_status
        # itself encodes gate reasons. Only inject when we actually have data
        # to keep the output minimal.
        pass
    return (
        f"{task_id} [{row.get('stage') or '-'}] {title} "
        f"workflow_id={workflow_id} "
        f"workflow_gate={str(gate.get('gate') or '-')} "
        f"workflow_gate_status={str(gate.get('gate_status') or '-')} "
        f"next_action={next_action} "
        f"apply_allowed={str(apply_allowed).lower()} "
        f"blocking_reasons={','.join(reasons) if reasons else '-'}"
    )


def _subject_inventory_brief(row: dict) -> str:
    return (
        f"{row.get('subject_id') or '-'} :: {row.get('subject_name') or '-'} "
        f"slug={row.get('subject_slug') or '-'} "
        f"code={row.get('subject_code') or '-'} "
        f"qa_count={row.get('qa_count') or 0} "
        f"item_count={row.get('item_count') or 0} "
        f"outline_topic_count={row.get('outline_topic_count') or 0} "
        f"manifest_covered_count={row.get('manifest_covered_count') or 0} "
        f"qa_standard={row.get('qa_standard') or '-'} "
        f"qa_range={row.get('qa_min') or 0}-{row.get('qa_max') or 0} "
        f"qbank_readiness={row.get('qbank_readiness') or '-'} "
        f"recommended_qbank_action={row.get('recommended_qbank_action') or '-'} "
        f"review_status={row.get('review_status') or '-'} "
        f"closeout_status={row.get('closeout_status') or '-'} "
        f"next_candidate_rank={row.get('next_candidate_rank') or 0} "
        f"next_action={row.get('next_action') or row.get('recommended_action') or '-'} "
        f"recommended_action={row.get('recommended_action') or '-'}"
    )


def _cmd_subject_inventory(rest: list[str]) -> int:
    content_dir = pop_flag(rest, "--content-dir") or "content"
    if rest:
        return usage_error(USAGE)
    rows = tasks.subject_inventory_extended()
    print("📚 subject inventory (extended)")
    if not rows:
        print("none")
        return 0
    # Package 6: show verifier compact summary for each subject
    for row in rows:
        print(f"  - {_subject_inventory_brief(row)}")
        slug = row.get("subject_slug", "")
        if slug:
            try:
                vresult = subject_verifier.verify_subject(content_dir, slug)
                compact = subject_verifier.compact_summary(vresult)
                print(f"    verifier: status={compact['status']} "
                      f"topics={compact['topic_count']} "
                      f"questions={compact['total_questions']} "
                      f"qa={compact['qa_count']} qql={compact['qql_count']} items={compact['items_count']} "
                      f"manifest={compact['has_manifest']} "
                      f"legacy={compact['legacy_fragment_present']} "
                      f"orphans={compact['orphan_candidate_count']}")
                if compact["blocking_reasons"]:
                    print(f"    verifier_blocking: {'; '.join(compact['blocking_reasons'])}")
            except Exception as e:
                print(f"    verifier: error ({e})", file=sys.stderr)
    return 0


def _cmd_manager_closeout(rest: list[str]) -> int:
    actor = pop_flag(rest, "--actor")
    content_dir = pop_flag(rest, "--content-dir") or "content"
    skip_verifier = pop_bool_flag(rest, "--skip-verifier")
    if len(rest) != 1 or not actor:
        return usage_error(USAGE)
    # Package 2 (Codex Q2): production CLI must not silently bypass the
    # verifier. `--skip-verifier` is only allowed when the operator has
    # explicitly enabled it via an env var that is meant for test fixtures
    # where no real content directory exists. In production the right
    # action is to dispatch the worker to repair the drift and re-verify.
    if skip_verifier and not _verifier_bypass_allowed():
        return error_exit(
            "❌ --skip-verifier is disabled in production; "
            "set EDUFLOW_VERIFIER_BYPASS_ALLOWED=1 only for test fixtures, "
            "otherwise repair the verifier blockers and re-run"
        )
    tid = rest[0]
    task = tasks.get(tid)
    if task is None:
        return error_exit(f"❌ no such task: {tid}")
    # Package 6: run verifier before allowing closeout (skippable for tests)
    title = str(task.get("title") or "")
    slug = tasks.extract_subject_slug(title)
    vresult = None
    if slug and not skip_verifier:
        vresult = subject_verifier.verify_subject(content_dir, slug)
        compact = subject_verifier.compact_summary(vresult)
        print(f"🔍 subject verifier: {compact['status']} topics={compact['topic_count']} "
              f"questions={compact['total_questions']} legacy={compact['legacy_fragment_present']}")
        if compact["blocking_reasons"]:
            print(f"   blocking_reasons: {'; '.join(compact['blocking_reasons'])}")
    try:
        ok = tasks.manager_closeout_subject(
            tid, actor=actor, verifier_result=vresult, content_dir=content_dir,
            skip_subject_verifier=skip_verifier,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    gate = tasks.subject_closeout_status(tasks.get(tid))
    print(
        f"✅ manager closeout {tid} "
        f"closeout_status={gate.get('closeout_status') or '-'} "
        f"recommended_action={gate.get('recommended_action') or '-'}"
    )
    _bridge_closeout_anomaly(tasks.get(tid) or {})
    return 0


def _cmd_batch_closeout(rest: list[str]) -> int:
    actor = pop_flag(rest, "--actor")
    if len(rest) != 1 or not actor:
        return usage_error(USAGE)
    tid = rest[0]
    try:
        ok = tasks.batch_closeout(tid, actor=actor)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    task = tasks.get(tid) or {}
    gate = tasks.workflow_gate_status(task)
    print(
        f"✅ batch closeout {tid} "
        f"closeout_status={task.get('closeout_status') or '-'} "
        f"workflow_gate={gate.get('gate') or '-'}"
    )
    return 0


def _cmd_workflow_status(rest: list[str]) -> int:
    if len(rest) != 1:
        return usage_error(USAGE)
    tid = rest[0]
    task = tasks.get(tid)
    if task is None:
        return error_exit(f"❌ no such task: {tid}")
    gate = tasks.workflow_gate_status(task)
    print(f"workflow_id={gate.get('workflow_id') or '-'}")
    print(f"gate={gate.get('gate') or '-'}")
    print(f"gate_status={gate.get('gate_status') or '-'}")
    print(f"status={gate.get('status') or '-'}")
    print(f"verdict={gate.get('verdict') or '-'}")
    print(f"reviewer={gate.get('reviewer') or '-'}")
    print(f"default_reviewer={gate.get('default_reviewer') or '-'}")
    print(f"evidence_keys={','.join(gate.get('evidence_keys') or []) or '-'}")
    print(f"closeout_status={gate.get('closeout_status') or '-'}")
    print(f"next_action={gate.get('next_action') or '-'}")
    return 0


def _action_packet_line(packet: dict) -> str:
    return (
        f"action_code={packet.get('action_code') or '-'} "
        f"apply_allowed={str(bool(packet.get('apply_allowed'))).lower()} "
        f"assignee={packet.get('assignee') or '-'} "
        f"task_stage={packet.get('task_stage') or '-'} "
        f"subject_id={packet.get('subject_id') or '-'} "
        f"subject_name={packet.get('subject_name') or '-'}"
    )


def _print_closeout_gate(gate: dict, *, indent: str = "") -> None:
    if not isinstance(gate, dict) or not gate:
        return
    # Accept both prefixed (from subject_closeout_status) and unprefixed
    # (from _closeout_gate_summary) keys so the function is safe for any caller.
    review_approved = bool(gate.get("closeout_gate_review_approved") or gate.get("review_approved"))
    evidence_present = bool(gate.get("closeout_gate_evidence_present") or gate.get("evidence_present"))
    qa_standard_met = bool(gate.get("closeout_gate_qa_standard_met") or gate.get("qa_standard_met"))
    qbank_ready = bool(gate.get("closeout_gate_qbank_ready") or gate.get("qbank_ready"))
    print(
        f"{indent}closeout_gate: "
        f"review_approved={str(review_approved).lower()} "
        f"evidence_present={str(evidence_present).lower()} "
        f"qa_standard_met={str(qa_standard_met).lower()} "
        f"qbank_ready={str(qbank_ready).lower()}"
    )


def _print_action_packet(packet: dict, *, indent: str = "") -> None:
    print(f"{indent}action_packet: {_action_packet_line(packet)}")
    if packet.get("reason"):
        print(f"{indent}  reason={packet['reason']}")
    if packet.get("suggested_brief"):
        print(f"{indent}  suggested_brief={packet['suggested_brief']}")
    _print_closeout_gate(packet.get("closeout_gate") or {}, indent=indent + "  ")
    plan = packet.get("execution_plan") or {}
    if isinstance(plan, dict) and plan:
        _print_execution_plan(plan, indent=indent + "  ")
    status = task_event_scanner.manager_action_apply_status(
        str(packet.get("action_code") or ""),
        str(packet.get("subject_id") or ""),
    )
    if not status:
        status = task_event_scanner.action_packet_preview_status(packet)
    _print_apply_result(status, indent=indent + "  ", label="apply_status")


def _print_execution_plan(plan: dict, *, indent: str = "") -> None:
    print(
        f"{indent}execution_plan: "
        f"plan_type={plan.get('plan_type') or '-'} "
        f"dry_run={str(bool(plan.get('dry_run'))).lower()} "
        f"execution_policy={plan.get('execution_policy') or '-'}"
    )
    preconditions = plan.get("preconditions") or []
    if preconditions:
        print(f"{indent}  preconditions=" + ", ".join(str(item) for item in preconditions))
    if plan.get("proposed_command"):
        print(f"{indent}  proposed_command={plan['proposed_command']}")
    if plan.get("proposed_brief"):
        print(f"{indent}  proposed_brief={plan['proposed_brief']}")


def _print_apply_result(result: dict, *, indent: str = "", label: str = "apply_result") -> None:
    apply_mode = result.get("apply_mode") or "-"
    apply_reason = result.get("apply_reason") or "-"
    apply_state = "confirmed_state" if apply_mode == "confirmed" else "dry_run_preview"
    print(
        f"{indent}{label}: "
        f"applied={str(bool(result.get('applied'))).lower()} "
        f"action_code={result.get('action_code') or '-'} "
        f"subject_id={result.get('subject_id') or '-'} "
        f"apply_mode={apply_mode} "
        f"apply_reason={apply_reason} "
        f"apply_state={apply_state}"
    )
    print(f"{indent}  created_task_id={result.get('created_task_id') or '-'}")
    print(f"{indent}  updated_subject_id={result.get('updated_subject_id') or '-'}")
    print(f"{indent}  existing_task_id={result.get('existing_task_id') or '-'}")
    print(f"{indent}  apply_summary={result.get('apply_summary') or '-'}")


def _print_context_guard_fields(row: dict, *, indent: str = "  ") -> None:
    affected = row.get("affected_agent") or row.get("agent")
    if affected:
        print(f"{indent}affected_agent={affected}")
    if row.get("message_id"):
        print(f"{indent}message_id={row['message_id']}")
    if "allow_continue_original_task" in row:
        print(
            f"{indent}allow_continue_original_task="
            f"{str(bool(row.get('allow_continue_original_task'))).lower()}"
        )
    if "inbox_recovery_needed" in row:
        print(
            f"{indent}inbox_recovery_needed="
            f"{str(bool(row.get('inbox_recovery_needed'))).lower()}"
        )


def _extract_action_packets(rows: list[dict]) -> list[dict]:
    """Deduplicate action packets from anomaly rows."""
    packets: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        packet = row.get("action_packet")
        if not isinstance(packet, dict) or not packet.get("action_code"):
            continue
        key = (
            str(packet.get("action_code") or ""),
            str(packet.get("subject_id") or row.get("task_id") or ""),
            str(packet.get("assignee") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        packets.append(packet)
    return packets


def _manager_action_packets() -> list[dict]:
    """Return deduplicated manager action packets (fail-fast).

    ``manager-panel`` / ``manager-actions`` callers surface scan errors
    directly; the ops dashboard uses ``_safe_aggregate`` instead.
    """
    rows = task_event_scanner.scan_manager_anomalies()
    return _extract_action_packets(rows)


_CONTEXT_GUARD_CATEGORIES = frozenset({
    "worker_context_exhausted",
    "worker_context_compact_recommended",
    "worker_context_usage_warning",
    "worker_high_priority_unacked_while_producing",
    "status_pane_truth_conflict",
    "unsafe_long_context_execution",
})


def _cmd_manager_actions(rest: list[str]) -> int:
    if rest:
        return usage_error(USAGE)
    packets = _manager_action_packets()
    print("🧭 suggested manager actions")
    context_blockers = [
        row for row in task_event_scanner.scan_manager_anomalies()
        if str(row.get("category") or "") in _CONTEXT_GUARD_CATEGORIES
    ]
    if context_blockers:
        print("context_guard_blockers:")
        for row in context_blockers[:8]:
            print(
                f"- blocker={row['category']} "
                f"affected_agent={row.get('affected_agent') or row.get('agent') or '-'} "
                f"recommended_action={row.get('recommended_action') or '-'} "
                f"allow_continue_original_task="
                f"{str(bool(row.get('allow_continue_original_task'))).lower()}"
            )
            if row.get("message_id"):
                print(f"  message_id={row['message_id']}")
            print(f"  latest_evidence={row.get('evidence_summary') or '-'}")
    if not packets:
        if not context_blockers:
            print("none")
        return 0
    # Package 7 (Revision-First Gate): if any active flow task has
    # revision_priority set, suppress action codes that would pivot
    # production away from the open revision. Other action codes
    # (rework, closeout, evidence, qbank) remain visible because they
    # are valid under the revision gate. `dispatch_next_subject_worker_course`
    # and `request_worker_course_expand_qa` are the real production-pivot
    # paths; they must NOT be recommended actions while the gate is active.
    revision_first_active = tasks.has_active_revision_priority("")
    # Package 7 (Revision-First Gate) round 7 fix: use the full
    # REVISION_FIRST_BLOCKED_RECOMMENDATIONS set (includes
    # continue_next_batch / select_next_subject which are
    # recommendations, not apply action_codes, but the recommendation
    # layer must still filter them).
    blocked_codes = task_event_scanner.REVISION_FIRST_BLOCKED_RECOMMENDATIONS
    suppressed_codes = (
        blocked_codes
        if revision_first_active
        else set()
    )
    if suppressed_codes:
        packets = [
            packet for packet in packets
            if str(packet.get("action_code") or "") not in suppressed_codes
        ]
        if not packets:
            print("none (revision_first_gate_holds_continuation)")
            return 0
        print(
            "revision_first_active :: suppressed_codes="
            f"{','.join(sorted(suppressed_codes))} :: "
            "owner_must_clear_revision_priority_or_stay_in_scope"
        )
    for packet in packets:
        print(f"- {_action_packet_line(packet)}")
        # workflow-first summary line — gives manager the next move at a glance.
        subject_id = str(packet.get("subject_id") or "")
        next_action = str(packet.get("action_code") or "-")
        apply_allowed = bool(packet.get("apply_allowed"))
        blocking_reasons = _packet_blocking_reasons_for_subject(
            subject_id, [packet],
        )
        print(
            f"  workflow_next_action={next_action} "
            f"apply_allowed={str(apply_allowed).lower()} "
            f"blocking_reasons={','.join(blocking_reasons) if blocking_reasons else '-'}"
        )
        if packet.get("suggested_brief"):
            print(f"  suggested_brief={packet['suggested_brief']}")
        gate = packet.get("closeout_gate") or {}
        if gate:
            _print_closeout_gate(gate, indent="  ")
        plan = packet.get("execution_plan") or {}
        if isinstance(plan, dict) and plan:
            _print_execution_plan(plan, indent="  ")
        status = task_event_scanner.manager_action_apply_status(
            str(packet.get("action_code") or ""),
            str(packet.get("subject_id") or ""),
        )
        if not status:
            status = task_event_scanner.action_packet_preview_status(packet)
        _print_apply_result(status, indent="  ", label="apply_status")
    return 0


def _cmd_manager_action_apply(rest: list[str]) -> int:
    subject_id = pop_flag(rest, "--subject-id")
    confirm = pop_bool_flag(rest, "--confirm")
    skip_verifier = pop_bool_flag(rest, "--skip-verifier")
    if len(rest) != 1 or not subject_id:
        return usage_error(USAGE)
    # Package 2 (Codex Q2): `manager-action-apply manager_formal_closeout`
    # routes through the same verifier bypass. Gate it identically to
    # `manager-closeout` so a test-only escape hatch cannot be used in prod.
    if skip_verifier and not _verifier_bypass_allowed():
        return error_exit(
            "❌ --skip-verifier is disabled in production; "
            "set EDUFLOW_VERIFIER_BYPASS_ALLOWED=1 only for test fixtures, "
            "otherwise repair the verifier blockers and re-run"
        )
    action_code = rest[0]
    result = task_event_scanner.manager_action_apply(
        action_code,
        subject_id,
        confirm=confirm,
        skip_subject_verifier=skip_verifier,
    )
    _print_apply_result(result)
    plan = result.get("execution_plan") or {}
    if isinstance(plan, dict) and plan:
        _print_execution_plan(plan, indent="  ")
    return 0


def _publishable_rows(limit: int = 5) -> list[dict]:
    rows = task_event_scanner.scan_publish_decisions(
        to_target="user",
        include_silent=False,
        advance=False,
    )
    lane_priority = {
        "manager_result": 0,
        "manager_problem": 1,
        "worker_reassurance": 2,
        "internal_only": 3,
    }
    rows = sorted(
        rows,
        key=lambda row: (
            lane_priority.get(str(row.get("delivery_lane") or ""), 9),
            -int(row.get("created_at") or 0),
        ),
    )
    rendered_rows = []
    seen_task_ids: set[str] = set()
    for row in rows:
        task = tasks.get(row["task_id"]) or {}
        if not row["publish"]:
            continue
        if row["task_id"] in seen_task_ids:
            continue
        seen_task_ids.add(row["task_id"])
        rendered_rows.append({
            "row": row,
            "task": task,
            "stage": task.get("stage") or "",
            "manager_response_type": task_publish_render.compose_manager_response(task, row)["type"],
            "message": task_publish_render.render_publish_message(task, row),
        })
        if len(rendered_rows) >= limit:
            break
    return rendered_rows


def _render_candidate_message(task: dict, decision: dict) -> str:
    message = task_publish_render.render_publish_message(task, decision)
    if not message:
        return ""
    if str(decision.get("manager_response_type") or "") == "internal_only":
        return ""
    return message


def _suppressed_renderable_rows(limit: int = 5) -> list[dict]:
    rows = task_event_scanner.scan_publish_decisions(
        to_target="user",
        include_silent=True,
        advance=False,
    )
    selected = []
    seen_task_ids: set[str] = set()
    for row in rows:
        if row.get("publish"):
            continue
        task = tasks.get(row["task_id"]) or {}
        message = _render_candidate_message(task, row)
        if not message:
            continue
        if row["task_id"] in seen_task_ids:
            continue
        seen_task_ids.add(row["task_id"])
        selected.append({
            "row": row,
            "task": task,
            "message": message,
            "stage": task.get("stage") or "",
            "manager_response_type": task_publish_render.compose_manager_response(task, row)["type"],
        })
        if len(selected) >= limit:
            break
    return selected


def _load_qbank_verification() -> dict | None:
    """Best-effort load of the latest QBank verification JSON summary.

    Tries to run `python3 scripts/qbank_verify.py --content-dir content --json`
    and parse the output. Returns None if the script is unavailable.

    Parses stdout even when the verifier returns non-zero (FAIL) because
    verification failures still produce valid JSON that the manager needs.
    """
    try:
        import subprocess as _sp
        result = _sp.run(
            [sys.executable, "scripts/qbank_verify.py", "--content-dir", "content", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            parsed = json.loads(result.stdout)
            # Tag source for manager-panel consumers
            if result.returncode != 0:
                parsed["verification_command_failed"] = True
            return parsed
        # No stdout at all — genuine infrastructure failure
        if result.returncode != 0:
            return {
                "overall_status": "INFRA_ERROR",
                "error_detail": "qbank_verify script failed with no stdout",
                "returncode": result.returncode,
                "stderr": result.stderr[:500] if result.stderr else "",
            }
    except json.JSONDecodeError:
        return {
            "overall_status": "PARSE_ERROR",
            "error_detail": "qbank_verify stdout was not valid JSON",
        }
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _contract_line(task_id: str) -> str:
    """Return one compact line: ``contract: phase=<...> failed=<n> ...``.

    Read-only. If either read-model raises, the line degrades to a
    one-word warning so the panel must still render.
    """
    try:
        contract = task_loop_contract.build(task_id)
    except Exception as exc:  # pragma: no cover — defensive only
        return f"contract: read-model unavailable ({type(exc).__name__})"
    if contract is None:
        return ""
    phase = str(contract.get("current_phase") or "")
    failed = len(contract.get("failed_checks") or [])
    delivery = "n/a"
    productivity = "n/a"
    source = "n/a"
    try:
        readiness = operational_readiness.build(task_id)
    except Exception as exc:  # pragma: no cover
        return (
            f"contract: phase={phase} failed={failed} "
            f"readiness=read-model unavailable ({type(exc).__name__})"
        )
    if readiness is not None:
        delivery = str(readiness.get("delivery", {}).get("status") or "n/a")
        productivity = str(readiness.get("productivity", {}).get("status") or "n/a")
        source = str(readiness.get("source", {}).get("status") or "n/a")
    return (
        f"contract: phase={phase} failed={failed} "
        f"delivery={delivery} productivity={productivity} source={source}"
    )


def _cmd_manager_panel(rest: list[str]) -> int:
    if rest:
        return usage_error(USAGE)
    overview = tasks.manager_overview()
    anomalies = task_event_scanner.scan_manager_anomalies()
    publishable = _publishable_rows()
    suppressed = _suppressed_renderable_rows()
    manager_packets = _manager_action_packets()

    print("🧭 manager panel")

    print("\n== Workflow Drive ==")
    drive_rows = _collect_workflow_drive_rows()
    if not drive_rows:
        print("none")
    else:
        for row in drive_rows:
            line = _workflow_drive_line(row, packets=manager_packets)
            if line:
                print(line)

    print("\n== Task Buckets ==")
    for key, label in (
        ("in_progress", "in progress"),
        ("awaiting_review", "awaiting review"),
        ("blocked", "blocked"),
        ("manager_action", "needs manager action"),
        ("subject_closeout", "subject closeout pending"),
    ):
        rows = overview[key]
        print(f"{label}: {len(rows)}")
        for row in rows[:5]:
            print(f"  - {_task_brief(row)}")
            # Package 6: append one compact contract line per workflow task.
            # Defensive: read-model errors must not crash the panel.
            contract_line = _contract_line(str(row.get("id") or ""))
            if contract_line:
                print(f"    {contract_line}")
            if row.get("latest_turn_summary"):
                print(f"    latest_turn_summary={row['latest_turn_summary']}")

    print("\n== Subject Closeout ==")
    inventory = tasks.subject_inventory()
    if not inventory:
        print("none")
    else:
        for row in inventory[:8]:
            print(f"- {_subject_inventory_brief(row)}")
            if row.get("closeout_status") not in {"not_subject", "closeout_completed"}:
                print("  legacy_category=subject_closeout_pending")
                print("  recommended_action: close_subject_and_dispatch_followups")
                _print_closeout_gate({
                    "review_approved": row.get("closeout_gate_review_approved"),
                    "evidence_present": row.get("closeout_gate_evidence_present"),
                    "qa_standard_met": row.get("closeout_gate_qa_standard_met"),
                    "qbank_ready": row.get("closeout_gate_qbank_ready"),
                }, indent="  ")
        completed = [
            row for row in inventory
            if row.get("closeout_status") == "closeout_completed"
        ]
        next_candidates = [
            row for row in inventory
            if int(row.get("next_candidate_rank") or 0) == 1
        ]
        if completed and next_candidates:
            next_row = next_candidates[0]
            # Package 7 (Revision-First Gate): do NOT recommend
            # `dispatch_next_subject_worker_course` here. The actual
            # Revision-First Blockers section below carries the
            # authoritative block signal; emitting a rollover line
            # above it would visually contradict the gate.
            if not tasks.has_active_revision_priority(""):
                print("next_subject_rollover_ready")
                print(
                    "recommended_action: dispatch_next_subject_worker_course"
                    f" :: {next_row.get('subject_name') or next_row.get('subject_id') or '-'}"
                )
            else:
                print(
                    "next_subject_rollover_ready_suppressed=revision_first_active "
                    f":: candidate={next_row.get('subject_name') or next_row.get('subject_id') or '-'}"
                )

    print("\n== Revision-First Blockers ==")
    revision_blockers = _collect_revision_priority_blockers()
    if not revision_blockers:
        print("none")
    else:
        for blocker in revision_blockers:
            print(
                f"revision_first :: task_id={blocker['task_id']} "
                f"workflow_id={blocker['workflow_id'] or '-'} "
                f"revision_priority={blocker['revision_priority']} "
                f"scope_topic={blocker['scope_topic'] or '-'} "
                f"owner={blocker['owner'] or '-'} "
                f"next_action={blocker['next_action']} "
                f"recommended_action={blocker['recommended_action']}"
            )
        print(
            "revision_first_priority: blockers_above_continuation :: "
            "next_subject_rollover_and_continue_next_batch_are_suppressed_until_clear"
        )

    print("\n== Evidence Accounts ==")
    account_rows = [
        row for row in tasks.subject_inventory()
        if row.get("evidence_account")
        and row.get("closeout_status") not in {"not_subject", "closeout_completed"}
    ]
    if not account_rows:
        print("none")
    else:
        for row in account_rows[:8]:
            account = row.get("evidence_account") or {}
            print(
                f"evidence_account :: task_id={account.get('task_id') or row.get('subject_id') or '-'} "
                f"workflow_id={account.get('workflow_id') or '-'} "
                f"closeout_ready={str(bool(account.get('closeout_ready'))).lower()} "
                f"items_count={account.get('items_count')} "
                f"qql_count={account.get('qql_count')} "
                f"manifest_rows={account.get('manifest_rows')} "
                f"recommended_action={account.get('recommended_action') or '-'}"
            )
            if account.get("missing_evidence"):
                print("  missing_evidence=" + ",".join(account["missing_evidence"]))
            if account.get("conflicting_evidence"):
                print("  conflicting_evidence=" + ",".join(account["conflicting_evidence"]))

    print("\n== Context Guard Blockers ==")
    context_blockers = [
        row for row in anomalies
        if str(row.get("category") or "") in _CONTEXT_GUARD_CATEGORIES
    ]
    if not context_blockers:
        print("none")
    else:
        for row in context_blockers[:8]:
            print(
                f"blocker={row['category']} "
                f"affected_agent={row.get('affected_agent') or row.get('agent') or '-'} "
                f"recommended_action={row.get('recommended_action') or '-'} "
                f"allow_continue_original_task="
                f"{str(bool(row.get('allow_continue_original_task'))).lower()}"
            )
            if row.get("message_id"):
                print(f"  message_id={row['message_id']}")
            if "inbox_recovery_needed" in row:
                print(
                    "  inbox_recovery_needed="
                    f"{str(bool(row.get('inbox_recovery_needed'))).lower()}"
                )
            print(f"  latest_evidence={row.get('evidence_summary') or '-'}")

    print("\n== Subject Continuation ==")
    next_subject = tasks.select_next_subject()
    if next_subject is None:
        # No candidates: show safe default workflow
        print("no_next_subject_candidate")
        print("default_workflow: refresh_subject_inventory | scan_manifests | await_reviewer")
    else:
        print(
            f"next_subject_recommendation: {next_subject['subject_id']} :: "
            f"{next_subject['subject_name']} "
            f"closeout_status={next_subject['closeout_status']} "
            f"rank={next_subject['next_candidate_rank']} "
            f"reason={next_subject['reason']}"
        )
        print(f"  recommended_action={next_subject['recommended_action']}")
        # Show batch continuation check for current active subject
        active_subjects = [
            row for row in inventory
            if row.get("closeout_status") not in {"closeout_completed", "not_subject"}
        ]
        for subj_row in active_subjects[:2]:
            gate = tasks.next_batch_continuation_gate(subj_row["subject_id"])
            if gate.get("should_continue"):
                print(
                    f"  batch_continuation: subject={gate['subject_id']} "
                    f"should_continue=true reason={gate['reason']} "
                    f"recommended_action={gate['recommended_action']}"
                )
                coverage = gate.get("coverage", {})
                if coverage:
                    print(
                        f"    coverage: qa_count={coverage.get('qa_count', 0)} "
                        f"item_count={coverage.get('item_count', 0)} "
                        f"outline_topic_count={coverage.get('outline_topic_count', 0)} "
                        f"manifest_covered_count={coverage.get('manifest_covered_count', 0)}"
                    )
            else:
                print(
                    f"  batch_continuation: subject={gate['subject_id']} "
                    f"should_continue=false reason={gate['reason']}"
                )
        # Show extended inventory summary line
        extended_inventory = tasks.subject_inventory_extended()
        visible_subjects = [
            r for r in extended_inventory
            if r.get("closeout_status") == "no_closeout_signal"
        ]
        if visible_subjects:
            print(
                f"  visible_without_closeout_signal: "
                f"{len(visible_subjects)} IGCSE subject(s) without completion markers "
                f"— refresh_inventory_and_check_progress"
            )

    print("\n== QBank Lifecycle ==")
    qbank_data = _load_qbank_verification()
    if qbank_data is None:
        print("no verification data — run: python3 scripts/qbank_verify.py --content-dir content --json")
    else:
        qbank_panel = tasks.qbank_manager_panel_summary(qbank_data)
        print(f"overall_status={qbank_panel.get('overall_status') or 'UNKNOWN'}")
        print(f"total_subjects={qbank_panel.get('total_subjects') or 0} "
              f"total_errors={qbank_panel.get('total_errors') or 0} "
              f"total_warnings={qbank_panel.get('total_warnings') or 0}")
        print(f"lifecycle_breakdown={qbank_panel.get('lifecycle_breakdown') or {}}")
        print(f"most_urgent_action={qbank_panel.get('most_urgent_action') or '-'}")
        for subj in qbank_panel.get("subjects") or []:
            lifecycle_state = subj.get("lifecycle_state") or "scan"
            next_action = tasks.QBANK_LIFECYCLE_NEXT_ACTIONS.get(lifecycle_state, "review_status")
            print(
                f"  - {subj.get('subject') or '-'} :: "
                f"lifecycle_state={lifecycle_state} "
                f"questions={subj.get('total_questions') or 0} "
                f"errors={subj.get('error_count') or 0} "
                f"warnings={subj.get('warning_count') or 0} "
                f"next_action={next_action}"
            )
        # Dedup/import gate summary

    # Package 8: visible sources audit — trace every manager-panel claim
    # back to its structured origin.
    print("\n== Visible Sources ==")
    for key, rows_slice in (
        ("in_progress", overview.get("in_progress", [])[:3]),
        ("awaiting_review", overview.get("awaiting_review", [])[:3]),
        ("blocked", overview.get("blocked", [])[:3]),
        ("manager_action", overview.get("manager_action", [])[:3]),
        ("subject_closeout", overview.get("subject_closeout", [])[:3]),
    ):
        for task_row in rows_slice:
            tid = task_row.get("id", "")
            if not tid:
                continue
            sources = task_publish_render.compose_visible_sources(task_row)
            missing = sources.get("sources_missing") or []
            present = sources.get("sources_present") or []
            missing_str = ", ".join(missing) if missing else "none"
            present_str = ", ".join(present) if present else "none"
            print(
                f"  [{key}] {tid}: "
                f"present=[{present_str}] missing=[{missing_str}]"
            )
            for src_key in ("subject_inventory_source", "qbank_report_path",
                            "verifier_report_path"):
                val = sources.get(src_key)
                if val:
                    print(f"    {src_key}: {val}")

    # Dedup/import gate summary — runs once after Visible Sources
    gate = tasks.dedup_import_gate(
        review_course_pass=(qbank_data.get("overall_status") == "PASS" if qbank_data else False),
        user_authorized=False,
        manager_authorized=False,
        dry_run=True,
    )
    print(f"dedup_import_gate_mode={gate['mode']}")
    print(f"dedup_import_apply_allowed={str(gate['apply_allowed']).lower()}")
    if gate.get("blocking_reasons"):
        print(f"dedup_import_blocking_reasons={','.join(gate['blocking_reasons'])}")
    print(f"dedup_import_next_action={gate['next_action']}")

    print("\n== Next Executable Actions ==")
    actionable = [row for row in anomalies if row.get("action_packet")]
    # Package 7 (Revision-First Gate) round 6 fix: use the canonical
    # REVISION_FIRST_BLOCKED_RECOMMENDATIONS set from task_event_scanner
    # so apply / manager-actions / manager-panel cannot drift.
    if tasks.has_active_revision_priority(""):
        actionable = [
            row for row in actionable
            if (row.get("action_packet") or {}).get("action_code")
            not in task_event_scanner.REVISION_FIRST_BLOCKED_RECOMMENDATIONS
        ]
        if not actionable:
            print("none (revision_first_gate_holds_executable_actions)")
        else:
            print("revision_first_active :: suppressed_continuation_actions_in_panel")
    if actionable:
        priority_order = ["safe_task_review_approve", "manager_formal_closeout"]
        def _action_priority(row):
            code = (row.get("action_packet") or {}).get("action_code", "")
            try:
                return priority_order.index(code)
            except ValueError:
                return len(priority_order)
        actionable.sort(key=_action_priority)
        for row in actionable[:10]:
            packet = row["action_packet"]
            print(f"⚡ {packet['action_code']} :: {row['task_id']} :: {row['why']}")
            if packet.get("evidence_summary"):
                print(f"   evidence: {packet['evidence_summary']}")
            if packet.get("suggested_brief"):
                print(f"   suggested: {packet['suggested_brief']}")
            plan = packet.get("execution_plan") or {}
            if isinstance(plan, dict) and plan.get("proposed_command") and plan["proposed_command"] != "no-op":
                print(f"   run: {plan['proposed_command']}")
            if packet.get("apply_allowed"):
                print(f"   ✅ apply: eduflow task manager-action-apply {packet['action_code']} --subject-id {packet.get('subject_id', '')} --confirm")
            else:
                print(f"   ⚠️  dry-run only — manual review required")

    print("\n== Anomalies (non-actionable) ==")
    non_actionable = [row for row in anomalies if not row.get("action_packet")]
    if not non_actionable:
        print("none")
    else:
        for row in non_actionable[:8]:
            print(f"- {row['category']} :: {row['task_id']} :: {row['why']}")
            if row.get("surface_state"):
                print(
                    "  surface_state: "
                    f"{task_publish_render.describe_surface_state(str(row.get('surface_state') or ''))}"
                )
            print(f"  evidence: {row['evidence_summary']}")
            _print_context_guard_fields(row, indent="  ")
            if row.get("recommended_action"):
                print(f"  recommended_action: {row['recommended_action']}")
            if row.get("action_packet"):
                _print_action_packet(row["action_packet"], indent="  ")
            task = tasks.get(row["task_id"]) or {}
            if task.get("latest_turn_summary"):
                print(f"  latest_turn_summary: {task['latest_turn_summary']}")

    print("\n== Suggested Manager Actions ==")
    packets = _manager_action_packets()
    # Package 7 (Revision-First Gate) round 6 fix: use the canonical
    # blocked-actions set from task_event_scanner.
    if tasks.has_active_revision_priority(""):
        packets = [
            packet for packet in packets
            if str(packet.get("action_code") or "") not in task_event_scanner.REVISION_FIRST_BLOCKED_RECOMMENDATIONS
        ]
        if not packets:
            print("none (revision_first_gate_holds_suggested_actions)")
        else:
            print("revision_first_active :: suppressed_continuation_actions_in_panel")
    if not packets:
        print("none")
    else:
        for packet in packets[:8]:
            print(f"- {_action_packet_line(packet)}")
            if packet.get("suggested_brief"):
                print(f"  suggested_brief={packet['suggested_brief']}")
            gate = packet.get("closeout_gate") or {}
            if gate:
                _print_closeout_gate(gate, indent="  ")
            plan = packet.get("execution_plan") or {}
            if isinstance(plan, dict) and plan:
                _print_execution_plan(plan, indent="  ")
            status = task_event_scanner.manager_action_apply_status(
                str(packet.get("action_code") or ""),
                str(packet.get("subject_id") or ""),
            )
            if not status:
                status = task_event_scanner.action_packet_preview_status(packet)
            _print_apply_result(status, indent="  ", label="apply_status")

    print("\n== User-Ready Updates ==")
    if not publishable:
        print("none")
    else:
        aggregate = task_publish_render.compose_publish_aggregate(publishable)
        print(aggregate["headline"])
        if aggregate["results"]:
            print("results:")
            for item in aggregate["results"]:
                row = item["row"]
                print(
                    f"  - {row['task_id']} :: {item.get('manager_response_type') or row['reason']} :: {item['message']}"
                )
        if aggregate["problems"]:
            print("problems:")
            for item in aggregate["problems"]:
                row = item["row"]
                print(
                    f"  - {row['task_id']} :: {item.get('manager_response_type') or row['reason']} :: {item['message']}"
                )
        if aggregate["reassurances"]:
            print("reassurances:")
            for item in aggregate["reassurances"]:
                row = item["row"]
                print(
                    f"  - {row['task_id']} :: {item.get('manager_response_type') or row['reason']} :: {item['message']}"
                )
        if not (aggregate["results"] or aggregate["problems"] or aggregate["reassurances"]):
            print(
                f"fallback :: {aggregate['fallback']}"
            )

    print("\n== Suppressed User-Ready Candidates ==")
    if not suppressed:
        print("none")
    else:
        for item in suppressed:
            row = item["row"]
            print(
                f"- {row['task_id']} :: {item.get('manager_response_type') or row['reason']} "
                f":: publish=false reason={row['reason']} cadence_action={row.get('cadence_action') or '-'}"
            )
            print(f"  candidate_rendered :: {item['message']}")
    return 0


# ── Ops Dashboard (M2) ───────────────────────────────────────────
#
# Lightweight operator snapshot: team status, top actions, review queue,
# manager actions, and degraded-mode aggregation.  Designed to return in
# ~5 seconds and never crash the whole command when one sub-aggregation
# fails.


_OPS_DASHBOARD_SUMMARY_KEYS = (
    "active",
    "stale_display",
    "waiting_inbox",
    "blocked",
    "idle",
    "warm_idle",
    "unknown",
)


def _degraded_note(source: str, exc: Exception) -> dict:
    return {
        "source": source,
        "error_type": type(exc).__name__,
        "message": str(exc),
    }


def _safe_aggregate(label: str, fn, default=None):
    """Call ``fn`` and return (result, degraded_note).

    On exception, returns ``default`` (defaulting to ``[]``) plus a degraded
    note so callers can degrade gracefully without crashing.
    """
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001
        fallback = default if default is not None else []
        return fallback, _degraded_note(label, exc)


def _ops_dashboard_summary(employees: list[dict]) -> dict:
    summary = {key: 0 for key in _OPS_DASHBOARD_SUMMARY_KEYS}
    summary["agents_total"] = len(employees)
    for emp in employees:
        verdict = str(emp.get("display_verdict") or "unknown")
        if verdict in summary:
            summary[verdict] += 1
        else:
            summary["unknown"] += 1
    return summary


def _ops_dashboard_residency(employees: list[dict]) -> dict:
    """Count residency modes and related signals from employee snapshots."""
    counts = {
        "resident": 0,
        "warm": 0,
        "cold": 0,
        "wake_failed": 0,
        "sleep_candidates": 0,
    }
    for emp in employees:
        mode = str(emp.get("residency_mode") or "")
        if mode == "resident":
            counts["resident"] += 1
        elif mode == "warm":
            counts["warm"] += 1
        elif mode == "cold":
            counts["cold"] += 1
        if str(emp.get("wake_status") or "") == "wake_failed":
            counts["wake_failed"] += 1
        if str(emp.get("sleep_decision") or "") == "sleep_ok":
            counts["sleep_candidates"] += 1
    return counts


def _ops_dashboard_top_actions(
    employees: list[dict],
    manager_packets: list[dict],
    review_queue_rows: list[dict],
) -> list[dict]:
    """Generate prioritized operator actions.

    Priority order (lower number = higher priority):
      1. high-priority unread (including warm-agent wake-or-route)
      2. blocked / wake failure
      3. stale_display
      4. manager_action packets + residency policy mismatch
      5. review_queue
      6. warm_idle wake/sleep issues
    """
    actions: list[dict] = []

    for emp in employees:
        agent = str(emp.get("agent") or "")
        verdict = str(emp.get("display_verdict") or "")
        residency_mode = str(emp.get("residency_mode") or "")
        residency_label = str(emp.get("residency_label") or "")
        unread_high = int(emp.get("unread_high_priority_count") or 0)
        wake_status = str(emp.get("wake_status") or "")
        sleep_decision = str(emp.get("sleep_decision") or "")
        blocker = str(emp.get("blocker") or "")

        # 1. High-priority unread (highest)
        if unread_high > 0:
            if residency_mode == "warm" or residency_label == "温备":
                actions.append({
                    "priority": 1,
                    "agent": agent,
                    "reason": f"warm agent has {unread_high} high-priority unread message(s)",
                    "recommended_next_action": (
                        "Wake or route inbox; verify wake path if CLI is sleeping."
                    ),
                })
            else:
                actions.append({
                    "priority": 1,
                    "agent": agent,
                    "reason": f"{unread_high} high-priority unread message(s)",
                    "recommended_next_action": (
                        emp.get("recommended_next_action")
                        or "Consume high-priority inbox."
                    ),
                })
            continue

        # 2. Wake failure / blocked
        if wake_status == "wake_failed":
            actions.append({
                "priority": 2,
                "agent": agent,
                "reason": "wake failure evidence detected",
                "recommended_next_action": (
                    "Repair wake path; check runtime/CLI readiness."
                ),
            })
            continue
        if verdict == "blocked" or blocker:
            actions.append({
                "priority": 2,
                "agent": agent,
                "reason": blocker or "agent is blocked",
                "recommended_next_action": (
                    emp.get("recommended_next_action") or "Resolve block."
                ),
            })
            continue

        # 3. Stale display
        if verdict == "stale_display":
            actions.append({
                "priority": 3,
                "agent": agent,
                "reason": str(emp.get("staleness_reason") or "display stale"),
                "recommended_next_action": (
                    emp.get("recommended_next_action")
                    or "Refresh status/heartbeat/log surface."
                ),
            })
            continue

        # 4. Residency policy mismatch (resident agent should never sleep)
        if residency_mode == "resident" and sleep_decision == "sleep_ok":
            actions.append({
                "priority": 4,
                "agent": agent,
                "reason": "residency policy mismatch: resident agent flagged as sleep candidate",
                "recommended_next_action": (
                    "Review residency policy; resident agents should never sleep."
                ),
            })
            continue

    # 4. Manager action packets
    for packet in manager_packets:
        actions.append({
            "priority": 4,
            "agent": str(packet.get("assignee") or ""),
            "reason": str(packet.get("reason") or "manager action"),
            "recommended_next_action": (
                str(packet.get("suggested_brief") or "")
                or str(packet.get("action_code") or "")
            ),
        })

    # 5. Review queue
    for t in review_queue_rows:
        actions.append({
            "priority": 5,
            "agent": str(t.get("assignee") or t.get("reviewer") or ""),
            "reason": f"task awaiting review: {t.get('title', '')}",
            "recommended_next_action": "Review or assign reviewer.",
        })

    # 6. Warm idle wake/sleep issues
    for emp in employees:
        if str(emp.get("display_verdict") or "") != "warm_idle":
            continue
        agent = str(emp.get("agent") or "")
        sleep_decision = str(emp.get("sleep_decision") or "")
        if sleep_decision == "sleep_ok":
            actions.append({
                "priority": 6,
                "agent": agent,
                "reason": "sleep candidate (warm idle beyond threshold)",
                "recommended_next_action": (
                    "Review sleep candidate; run residency-sleep dry-run if appropriate."
                ),
            })
        else:
            actions.append({
                "priority": 6,
                "agent": agent,
                "reason": "warm idle; no active task or unread",
                "recommended_next_action": (
                    emp.get("recommended_next_action")
                    or "Warm standby; wake on assignment."
                ),
            })

    actions.sort(key=lambda a: a["priority"])
    return actions


def _build_ops_dashboard(*, include_manager_actions: bool = False) -> dict:
    """Aggregate the ops dashboard payload with degraded-mode isolation."""
    degraded: list[dict] = []
    notes: list[str] = []
    generated_at_ms = now_ms()

    employees, note = _safe_aggregate(
        "employee_read_model.build_team_snapshot",
        employee_read_model.build_team_snapshot,
    )
    if note:
        degraded.append(note)

    summary = _ops_dashboard_summary(employees)

    residency, note = _safe_aggregate(
        "residency",
        lambda: _ops_dashboard_residency(employees),
        default={
            "resident": 0,
            "warm": 0,
            "cold": 0,
            "wake_failed": 0,
            "sleep_candidates": 0,
        },
    )
    if note:
        degraded.append(note)

    review_queue_rows, note = _safe_aggregate(
        "tasks.list_review_queue",
        tasks.list_review_queue,
    )
    if note:
        degraded.append(note)

    manager_anomaly_rows = []
    if include_manager_actions:
        manager_anomaly_rows, note = _safe_aggregate(
            "task_event_scanner.scan_manager_anomalies",
            task_event_scanner.scan_manager_anomalies,
        )
        if note:
            degraded.append(note)
    else:
        notes.append(
            "manager_actions skipped for fast dashboard; use --deep-manager-actions"
        )
    manager_packets = _extract_action_packets(manager_anomaly_rows)

    top_actions, note = _safe_aggregate(
        "top_actions",
        lambda: _ops_dashboard_top_actions(employees, manager_packets, review_queue_rows),
        default=[],
    )
    if note:
        degraded.append(note)

    review_queue = [
        {
            "id": t["id"],
            "title": t["title"],
            "stage": t.get("stage", ""),
            "assignee": t.get("assignee", ""),
            "reviewer": t.get("reviewer", ""),
        }
        for t in review_queue_rows
    ]
    manager_actions = [
        {
            "action_code": p.get("action_code", ""),
            "assignee": p.get("assignee", ""),
            "subject_id": p.get("subject_id", ""),
            "subject_name": p.get("subject_name", ""),
            "apply_allowed": bool(p.get("apply_allowed")),
            "suggested_brief": p.get("suggested_brief", ""),
        }
        for p in manager_packets
    ]

    return {
        "generated_at_ms": generated_at_ms,
        "summary": summary,
        "residency": residency,
        "top_actions": top_actions,
        "employees": employees,
        "review_queue": review_queue,
        "manager_actions": manager_actions,
        "degraded": degraded,
        "notes": notes,
    }


def _emit_ops_dashboard_text(dashboard: dict) -> None:
    summary = dashboard["summary"]
    residency = dashboard["residency"]
    print("ops dashboard")
    print(
        f"summary: agents={summary['agents_total']} "
        f"active={summary['active']} "
        f"stale_display={summary['stale_display']} "
        f"waiting_inbox={summary['waiting_inbox']} "
        f"blocked={summary['blocked']} "
        f"warm_idle={summary['warm_idle']} "
        f"idle={summary['idle']} "
        f"unknown={summary['unknown']}"
    )
    print(
        f"residency: resident={residency['resident']} "
        f"warm={residency['warm']} "
        f"cold={residency['cold']} "
        f"wake_failed={residency['wake_failed']} "
        f"sleep_candidates={residency['sleep_candidates']}"
    )

    print("top_actions:")
    if dashboard["top_actions"]:
        for i, action in enumerate(dashboard["top_actions"][:10], 1):
            print(
                f"  {i}. [p{action['priority']}] {action['agent']}: "
                f"{action['reason']} -> {action['recommended_next_action']}"
            )
    else:
        print("  none")

    print("employees:")
    if dashboard["employees"]:
        for emp in dashboard["employees"]:
            task = emp.get("current_task_title") or emp.get("declared_task") or "-"
            print(
                f"  - {emp.get('agent', '')} "
                f"verdict={emp.get('display_verdict', '')} "
                f"residency={emp.get('residency_label', '')} "
                f"task={task} "
                f"next={emp.get('recommended_next_action', '')}"
            )
    else:
        print("  none")

    if dashboard["review_queue"]:
        print("review_queue:")
        for t in dashboard["review_queue"]:
            print(
                f"  - {t['id']} [{t['stage']}] {t['title']} "
                f"assignee={t['assignee']} reviewer={t['reviewer']}"
            )

    if dashboard["manager_actions"]:
        print("manager_actions:")
        for a in dashboard["manager_actions"]:
            print(
                f"  - {a['action_code']} assignee={a['assignee']} "
                f"apply_allowed={str(a['apply_allowed']).lower()} "
                f"subject={a['subject_name'] or a['subject_id']}"
            )

    degraded = dashboard["degraded"]
    print(f"degraded: {len(degraded)}")
    if degraded:
        for d in degraded:
            print(f"  - {d['source']}: {d['error_type']}: {d['message']}")


def _cmd_ops_dashboard(rest: list[str]) -> int:
    as_json = pop_bool_flag(rest, "--json")
    as_text = pop_bool_flag(rest, "--text")
    deep_manager_actions = pop_bool_flag(rest, "--deep-manager-actions")
    if rest:
        return usage_error(USAGE)
    if not as_json and not as_text:
        as_text = True
    dashboard = _build_ops_dashboard(include_manager_actions=deep_manager_actions)
    if as_json:
        print_json(dashboard)
    else:
        _emit_ops_dashboard_text(dashboard)
    return 0


def _cmd_supervisor_check(rest: list[str]) -> int:
    advance = pop_bool_flag(rest, "--advance")
    do_send = pop_bool_flag(rest, "--send")
    as_json = pop_bool_flag(rest, "--json")
    if rest:
        return usage_error(USAGE)
    result = task_event_scanner.evaluate_manager_supervision()
    if advance:
        result = task_event_scanner.advance_manager_supervision(result)
    if do_send:
        body = result.get("user_message") or (
            "Supervisor 巡检完成："
            f" {result.get('health_status') or '-'} / "
            f"{result.get('primary_reason') or '-'}"
        )
        rc = say_cmd.main([
            "manager",
            body,
            "--channel", "supervisor",
            "--to", "user",
        ])
        if rc != 0:
            return error_exit("❌ supervisor-check send failed")
        result = dict(result)
        result["sent_to_supervisor_channel"] = True
    else:
        result = dict(result)
        result["sent_to_supervisor_channel"] = False
    if advance:
        result["advanced_supervisor_state_file"] = str(paths.task_supervisor_state_file())
    if as_json:
        print_json(result)
        return 0

    print("🛡️ supervisor check")
    print(f"health_status={result.get('health_status') or '-'}")
    print(f"primary_reason={result.get('primary_reason') or '-'}")
    print(f"recommended_action={result.get('recommended_action') or '-'}")
    print(f"user_alert_action={result.get('user_alert_action') or '-'}")
    print(f"repair_channel={result.get('repair_channel') or '-'}")
    print(f"heartbeat_interval_ms={result.get('heartbeat_interval_ms') or 0}")
    print(f"consecutive_issue_count={result.get('consecutive_issue_count') or 0}")
    print(f"state_stale={str(bool(result.get('state_stale'))).lower()}")
    print(f"state_age_ms={result.get('state_age_ms') or 0}")

    reasons = result.get("auto_summary_reasons") or []
    print("auto_summary_reasons:")
    for reason in reasons:
        print(f"  - {reason}")

    if result.get("user_message"):
        print(f"user_message :: {result['user_message']}")
    else:
        print("user_message :: silent")

    anomalies = result.get("anomalies") or []
    print("anomalies:")
    if not anomalies:
        print("  - none")
    else:
        for row in anomalies[:8]:
            print(
                f"  - {row['category']} :: {row['task_id']} :: "
                f"{row.get('recommended_action') or '-'} :: {row['why']}"
            )
            # Package 7 (Revision-First Gate): surface the structured
            # scope-mismatch fields so supervisors can read them without
            # the full JSON payload.
            for scope_key in (
                "expected_revision_scope",
                "observed_new_scope",
                "workflow_id",
                "affected_agent",
                "message_id",
                "closeout_ready",
            ):
                value = row.get(scope_key)
                if value not in (None, ""):
                    print(f"    {scope_key}: {value}")
            if row.get("missing_evidence"):
                print("    missing_evidence: " + ",".join(row["missing_evidence"]))
            if row.get("conflicting_evidence"):
                print("    conflicting_evidence: " + ",".join(row["conflicting_evidence"]))
            if "allow_continue_original_task" in row:
                print(
                    "    allow_continue_original_task: "
                    f"{str(bool(row.get('allow_continue_original_task'))).lower()}"
                )
            if "inbox_recovery_needed" in row:
                print(
                    "    inbox_recovery_needed: "
                    f"{str(bool(row.get('inbox_recovery_needed'))).lower()}"
                )
    runtime_guard_agents = result.get("runtime_guard_agents") or {}
    print("runtime_guard:")
    if not runtime_guard_agents:
        print("  - none")
    else:
        for agent, row in sorted(runtime_guard_agents.items()):
            bits = []
            if row.get("last_failure_reason"):
                bits.append(f"failure={row['last_failure_reason']}")
            if row.get("last_switch_outcome"):
                bits.append(f"outcome={row['last_switch_outcome']}")
            if row.get("escalation_reason"):
                bits.append(f"escalation={row['escalation_reason']}")
            if row.get("from_runtime") or row.get("to_runtime"):
                bits.append(f"route={row.get('from_runtime') or '-'}->{row.get('to_runtime') or '-'}")
            if row.get("escalation_needed"):
                bits.append("escalation_needed=true")
            print(f"  - {agent} :: {' '.join(bits) if bits else 'state_present'}")
    supervisor_processes = result.get("supervisor_processes") or []
    print("supervisor_processes:")
    if not supervisor_processes:
        print("  - none")
    else:
        for row in supervisor_processes:
            state = "alive" if row.get("alive") else ("pid_only" if row.get("pid_present") else "missing")
            print(f"  - {row.get('name') or '-'} :: {state}")
    if result.get("sent_to_supervisor_channel"):
        print("✅ supervisor-check sent to supervisor channel")
    if advance:
        print(f"✅ advanced supervisor state: {paths.task_supervisor_state_file()}")
    return 0


def _cmd_evidence_account(rest: list[str]) -> int:
    task_id = pop_flag(rest, "--task-id") or ""
    workflow_id = pop_flag(rest, "--workflow") or ""
    as_json = pop_bool_flag(rest, "--json")
    if rest:
        return usage_error(USAGE)
    rows = []
    for task in tasks.list_tasks():
        if task.get("schema_version") != 2:
            continue
        if task_id and str(task.get("id") or "") != task_id:
            continue
        if workflow_id and str(task.get("workflow_id") or "") != workflow_id:
            continue
        gate = tasks.subject_closeout_status(task)
        account = gate.get("evidence_account")
        if account:
            rows.append(account)
    if as_json:
        print_json({"evidence_accounts": rows})
        return 0
    if not rows:
        print("no evidence accounts")
        return 0
    for account in rows:
        print(
            f"evidence_account :: task_id={account.get('task_id') or '-'} "
            f"workflow_id={account.get('workflow_id') or '-'} "
            f"stage={account.get('stage') or '-'} "
            f"status={account.get('status') or '-'} "
            f"verdict={account.get('verdict') or '-'} "
            f"closeout_ready={str(bool(account.get('closeout_ready'))).lower()} "
            f"recommended_action={account.get('recommended_action') or '-'}"
        )
        print(
            f"  scope={account.get('scope') or '-'} "
            f"items_count={account.get('items_count')} "
            f"qql_count={account.get('qql_count')} "
            f"manifest_rows={account.get('manifest_rows')}"
        )
        print(
            "  latest_authoritative_review_verdict_source="
            f"{account.get('latest_authoritative_review_verdict_source') or '-'}"
        )
        print(
            f"  subject_verifier_status={account.get('subject_verifier_status') or '-'} "
            f"source={account.get('subject_verifier_source') or '-'}"
        )
        if account.get("missing_evidence"):
            print("  missing_evidence=" + ",".join(account["missing_evidence"]))
        if account.get("conflicting_evidence"):
            print("  conflicting_evidence=" + ",".join(account["conflicting_evidence"]))
    return 0


_READY_QBANK_STATES_FOR_VERDICT = frozenset({
    "qbank_ready", "ready_for_import", "needs_user_authorization",
})


def _classify_evidence_verdict(
    *,
    missing: list[str],
    conflicts: list[str],
    subject_verifier_status: str,
    latest_verdict: str,
    qbank_readiness: str,
) -> str:
    """Map the evidence-account raw fields into the 4-bucket verdict.

    Tie-breakers (M6 spec, OPT-2 tightened):
    1. conflicting_evidence non-empty  -> BLOCKED
    2. subject_verifier in {fail, warn} -> BLOCKED
    3. missing_evidence non-empty       -> NEEDS_FIX
    4. latest verdict rejected / manager_action -> BLOCKED
       (rejected = explicit closeout block; manager_action is a
       request-for-decision that has not been answered)
    5. latest verdict empty/pending     -> OBSERVE
    6. latest verdict approved and qbank in ready set (or empty) -> PASS
    7. else                             -> OBSERVE
    """
    if conflicts:
        return "BLOCKED"
    if subject_verifier_status in {"fail", "warn"}:
        return "BLOCKED"
    if missing:
        return "NEEDS_FIX"
    if latest_verdict in {"rejected", "manager_action"}:
        return "BLOCKED"
    if not latest_verdict or latest_verdict == "pending":
        return "OBSERVE"
    if latest_verdict == "approved":
        if not qbank_readiness or qbank_readiness in _READY_QBANK_STATES_FOR_VERDICT:
            return "PASS"
        return "OBSERVE"
    return "OBSERVE"


def _evidence_confidence(
    *,
    missing: list[str],
    latest: dict,
    subject_verifier_status: str,
    subject_verifier_source: str,
    items_count: int | None,
    qql_count: int | None,
    manifest_rows: int | None,
) -> str:
    """Drive confidence from the rubric in the SKILL.md.

    low  - any of {latest_authoritative_review, subject_verifier_status,
            items_count, qql_count, manifest_rows} is missing or
            source_missing.
    medium - latest review verdict is present but subject_verifier_status
            empty (or qbank_readiness empty on a task that has not yet
            reached the qbank stage).
    high  - all required fields present and consistent.
    """
    if (
        not latest
        or not subject_verifier_status
        or subject_verifier_source in {"source_missing", ""}
        or items_count is None
        or qql_count is None
        or manifest_rows is None
    ):
        return "low"
    if missing:
        return "medium"
    return "high"


def _required_next_owner(packet: dict) -> str:
    """Pick the role that owns the next repair step. '-' when ambiguous."""
    action = str(packet.get("safe_next_action") or "")
    if not action:
        return "-"
    if action.startswith("request_worker_course") or action == "complete_closeout_evidence_account":
        return "worker_course"
    if action.startswith("request_review_course") or action == "request_subject_count_evidence":
        return "review_course"
    if action == "request_qbank_readiness_check":
        return "worker_qbank"
    if action in {"manager_formal_closeout", "select_next_subject_from_inventory"}:
        return "manager"
    if action.startswith("resolve_evidence_account_conflict"):
        # Default conflict owner: worker_course (most common cause is QA
        # expansion drift). Reviewer can pick a different owner; the
        # packet only signals the default lane.
        return "worker_course"
    return "-"


def _safe_next_action(
    *,
    missing: list[str],
    conflicts: list[str],
    recommended: str,
    latest_verdict: str,
) -> str:
    """Map the action packet / account into a one-line imperative.

    Falls back to the account's `recommended_action` so the explainer
    stays consistent with the closeout layer. Order matters: an
    explicit reviewer verdict is more actionable than a generic
    "resolve conflict" line, so it wins.
    """
    if latest_verdict in {"rejected", "manager_action"}:
        # Always actionable: get a fresh reviewer verdict. The
        # BLOCKED verdict above already covers the conflict story.
        return "wait_for_review_approval"
    if conflicts:
        return "resolve_evidence_account_conflict"
    if missing:
        # Distinguish worker-side vs reviewer-side fixes by the missing
        # field, without changing the underlying gate.
        if any(m in {"items_count", "qql_count", "manifest_evidence", "manifest_rows"} for m in missing):
            return "request_worker_course_expand_qa_and_evidence_packet"
        if "subject_verifier_status" in missing:
            return "request_review_course_run_subject_verifier"
        return "complete_closeout_evidence_account"
    if recommended:
        return recommended
    return "manager_formal_closeout"


def _do_not_say_to_user_yet(verdict: str, *, qbank_readiness: str,
                            subject_verifier_status: str) -> str:
    """One-line guard that blocks premature user-facing closeout language."""
    if verdict == "BLOCKED":
        if subject_verifier_status in {"fail", "warn"}:
            return (
                "do not yet say '正式 PASS' until subject verifier returns "
                "pass on full subject scope"
            )
        return (
            "do not yet say 'closeout' until conflicting evidence is "
            "resolved and subject verifier status is pass"
        )
    if verdict == "NEEDS_FIX":
        return (
            "do not yet say 'closeout' until missing evidence is filled "
            "and the next review cycle returns approved"
        )
    if verdict == "OBSERVE":
        if not qbank_readiness:
            return (
                "do not yet say 'closeout' until qbank readiness is recorded"
            )
        return (
            "do not yet say 'closeout completed' until latest authoritative "
            "review verdict is approved and qbank is in a ready state"
        )
    # PASS
    return (
        "the gate is green, but the user-facing 'closeout completed' line "
        "must still wait for manager formal closeout"
    )


def build_evidence_verdict_packet(task: dict, account: dict) -> dict:
    """Build the M6 evidence-account verdict packet for one task.

    Reuses `task_evidence_account.build_evidence_account` output and
    the task's `latest_authoritative_verdict`. Never recomputes the
    gate and never auto-promotes package PASS into subject PASS.
    """
    task = task or {}
    account = account or {}
    latest = task.get("latest_authoritative_verdict") or {}
    if not isinstance(latest, dict):
        latest = {}
    missing = list(account.get("missing_evidence") or [])
    conflicts = list(account.get("conflicting_evidence") or [])
    subject_verifier_status = str(account.get("subject_verifier_status") or "")
    subject_verifier_source = str(account.get("subject_verifier_source") or "source_missing")
    qbank_readiness = str(account.get("qbank_readiness") or "")
    items_count = account.get("items_count")
    qql_count = account.get("qql_count")
    manifest_rows = account.get("manifest_rows")
    latest_verdict = str(latest.get("verdict") or "")
    verdict = _classify_evidence_verdict(
        missing=missing,
        conflicts=conflicts,
        subject_verifier_status=subject_verifier_status,
        latest_verdict=latest_verdict,
        qbank_readiness=qbank_readiness,
    )
    confidence = _evidence_confidence(
        missing=missing,
        latest=latest,
        subject_verifier_status=subject_verifier_status,
        subject_verifier_source=subject_verifier_source,
        items_count=items_count,
        qql_count=qql_count,
        manifest_rows=manifest_rows,
    )
    closeout_ready = bool(account.get("closeout_ready"))
    recommended = str(account.get("recommended_action") or "")
    safe_next = _safe_next_action(
        missing=missing,
        conflicts=conflicts,
        recommended=recommended,
        latest_verdict=latest_verdict,
    )
    # manager_action_allowed is True only when both the account gate and
    # the recommended action line up to manager_formal_closeout. We do
    # NOT let an OBSERVE or NEEDS_FIX packet silently grant manager
    # formal closeout.
    manager_action_allowed = bool(
        closeout_ready and recommended == "manager_formal_closeout"
        and verdict == "PASS"
    )
    packet = {
        "task_id": str(account.get("task_id") or task.get("id") or ""),
        "workflow_id": str(account.get("workflow_id") or task.get("workflow_id") or ""),
        "verdict": verdict,
        "confidence": confidence,
        "missing_evidence": missing,
        "conflicting_evidence": conflicts,
        "latest_authoritative_review": {
            "reviewer": str(latest.get("reviewer") or ""),
            "verdict": latest_verdict,
            "scope": str(latest.get("verdict_scope") or ""),
            "at_ms": int(latest.get("at_ms") or 0),
        },
        "subject_verifier_status": subject_verifier_status,
        "subject_verifier_source": subject_verifier_source,
        "qbank_readiness": qbank_readiness,
        "qbank_readiness_source": str(account.get("qbank_readiness_source") or "source_missing"),
        "manager_action_allowed": manager_action_allowed,
        "required_next_owner": "-",
        "safe_next_action": safe_next,
        "do_not_say_to_user_yet": _do_not_say_to_user_yet(
            verdict, qbank_readiness=qbank_readiness,
            subject_verifier_status=subject_verifier_status,
        ),
        "evidence_account_closeout_ready": closeout_ready,
        "evidence_account_recommended_action": recommended,
        "items_count": items_count,
        "qql_count": qql_count,
        "manifest_rows": manifest_rows,
        "supporting_evidence": {},
    }
    if task.get("loop_run_id"):
        packet["supporting_evidence"]["loop"] = {
            "run_id": str(task.get("loop_run_id") or ""),
            "status": str(task.get("loop_status") or ""),
            "cycle_count": int(task.get("loop_cycle_count") or 0),
            "stop_reason": str(task.get("loop_stop_reason") or ""),
            "recommended_action": str(task.get("loop_recommended_action") or ""),
            "evidence_ref": str(task.get("loop_evidence_ref") or ""),
        }
    packet["required_next_owner"] = _required_next_owner(packet)
    return packet


def print_evidence_verdict_packet(packet: dict) -> None:
    """Render the packet as a paste-ready markdown block for manager / reviewer."""
    latest = packet.get("latest_authoritative_review") or {}
    missing = packet.get("missing_evidence") or []
    conflicts = packet.get("conflicting_evidence") or []
    print("## Evidence Account Verdict Packet")
    print(f"- task_id: {packet.get('task_id') or '-'}")
    print(f"- workflow_id: {packet.get('workflow_id') or '-'}")
    print(f"- verdict: {packet.get('verdict') or '-'}")
    print(f"- confidence: {packet.get('confidence') or '-'}")
    print(f"- missing_evidence: [{','.join(missing) if missing else '-'}]")
    print(f"- conflicting_evidence: [{','.join(conflicts) if conflicts else '-'}]")
    print(
        f"- latest_authoritative_review: "
        f"reviewer={latest.get('reviewer') or '-'} "
        f"verdict={latest.get('verdict') or '-'} "
        f"scope={latest.get('scope') or '-'} "
        f"at_ms={int(latest.get('at_ms') or 0)}"
    )
    print(
        f"- subject_verifier_status: {packet.get('subject_verifier_status') or '-'} "
        f"(source={packet.get('subject_verifier_source') or '-'})"
    )
    print(
        f"- qbank_readiness: {packet.get('qbank_readiness') or '-'} "
        f"(source={packet.get('qbank_readiness_source') or '-'})"
    )
    print(f"- manager_action_allowed: {str(bool(packet.get('manager_action_allowed'))).lower()}")
    print(f"- required_next_owner: {packet.get('required_next_owner') or '-'}")
    print(f"- safe_next_action: {packet.get('safe_next_action') or '-'}")
    print(f"- do_not_say_to_user_yet: {packet.get('do_not_say_to_user_yet') or '-'}")


def _cmd_evidence_explain(rest: list[str]) -> int:
    """Render the Evidence Account Verdict Packet for one task.

    M6: read-only explainer for `review_course full verdict`,
    `worker_course selfcheck`, `worker_qbank qbank slice`, and
    `manager closeout-lite`. Reuses the existing
    `task_evidence_account.build_evidence_account` output; never
    recomputes the gate, never sends Feishu, never auto-promotes
    package PASS into subject PASS.
    """
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0].startswith("-"):
        return usage_error(USAGE)
    task_id = rest[0]
    if len(rest) > 1:
        return usage_error(USAGE)
    task = tasks.get(task_id)
    if task is None:
        return error_exit(f"❌ no such task: {task_id}")
    gate = tasks.subject_closeout_status(task)
    account = gate.get("evidence_account") or {}
    packet = build_evidence_verdict_packet(task, account)
    if as_json:
        print_json({"evidence_explain": packet})
        return 0
    print_evidence_verdict_packet(packet)
    return 0


def _cmd_publish_check(rest: list[str]) -> int:
    sender = pop_flag(rest, "--sender")
    to_target = pop_flag(rest, "--to") or "user"
    if len(rest) < 1 or not sender:
        return usage_error(USAGE)
    tid = rest[0]
    task = tasks.get(tid)
    if task is None:
        return error_exit(f"❌ no such task: {tid}")
    events = tasks.list_task_events(task_id=tid, limit=1)
    if not events:
        return error_exit(f"❌ no task events for {tid}")
    decision = task_publish_gate.decide_task_event_publish(
        events[-1],
        sender=sender,
        to_target=to_target,
    )
    rendered = _render_candidate_message(task, decision)
    print(
        f"publish={str(decision['publish']).lower()} "
        f"reason={decision['reason']} "
        f"task_id={decision['task_id']} "
        f"status={decision['status'] or '-'} "
        f"to={decision['to_target']}"
    )
    print(f"audience_policy={decision.get('audience_policy') or '-'}")
    print(f"delivery_lane={decision.get('delivery_lane') or '-'}")
    print(f"cadence_action={decision.get('cadence_action') or '-'}")
    print(f"cadence_reason={decision.get('cadence_reason') or '-'}")
    print(f"manager_response_type={decision.get('manager_response_type') or '-'}")
    print(f"close_loop_state={decision.get('close_loop_state') or '-'}")
    print(f"close_loop_reason={decision.get('close_loop_reason') or '-'}")
    if decision["publish"] and rendered:
        print(f"rendered :: {rendered}")
    return 0


def _cmd_publish_scan(rest: list[str]) -> int:
    to_target = pop_flag(rest, "--to") or "user"
    include_silent = pop_bool_flag(rest, "--include-silent")
    advance = pop_bool_flag(rest, "--advance")
    if rest:
        return usage_error(USAGE)
    rows = task_event_scanner.scan_publish_decisions(
        to_target=to_target,
        include_silent=include_silent,
        advance=advance,
    )
    if not rows:
        print("📭 no matching unpublished task events")
        return 0
    for row in rows:
        task = tasks.get(row["task_id"]) or {}
        print(
            f"{row['event_id']}  publish={str(row['publish']).lower()}  "
            f"task={row['task_id']}  status={row['status'] or '-'}  "
            f"sender={row['sender']}  to={row['to_target']}  reason={row['reason']}"
        )
        print(f"  audience_policy={row.get('audience_policy') or '-'}")
        print(f"  delivery_lane={row.get('delivery_lane') or '-'}")
        print(f"  cadence_action={row.get('cadence_action') or '-'}")
        print(f"  cadence_reason={row.get('cadence_reason') or '-'}")
        print(f"  manager_response_type={row.get('manager_response_type') or '-'}")
        print(f"  close_loop_state={row.get('close_loop_state') or '-'}")
        print(f"  close_loop_reason={row.get('close_loop_reason') or '-'}")
        rendered = _render_candidate_message(task, row)
        if row["publish"] and rendered:
            print(
                "  rendered :: "
                f"{rendered}"
            )
        elif rendered:
            print(
                "  suppressed_rendered :: "
                f"{rendered}"
            )
    if advance:
        print("✅ advanced task publish cursor")
    return 0


def _cmd_publish_run(rest: list[str]) -> int:
    to_target = pop_flag(rest, "--to") or "user"
    do_send = pop_bool_flag(rest, "--send")
    advance = pop_bool_flag(rest, "--advance")
    if rest:
        return usage_error(USAGE)
    if advance and not do_send:
        return error_exit("❌ --advance requires --send")

    rows = task_event_scanner.scan_publish_decisions(
        to_target=to_target,
        include_silent=True,
        advance=False,
    )
    if not rows:
        print("📭 no unpublished task events")
        return 0

    publishable = [row for row in rows if row["publish"]]
    if not publishable:
        print("📭 no publishable task events")
        return 0
    publishable = sorted(
        publishable,
        key=lambda row: int(row.get("created_at") or 0),
        reverse=True,
    )[:3]
    rendered = []
    for row in publishable:
        task = tasks.get(row["task_id"]) or {}
        rendered.append({
            "row": row,
            "task": task,
            "message": task_publish_render.render_publish_message(task, row),
            "stage": task.get("stage") or "",
            "manager_response_type": task_publish_render.compose_manager_response(task, row)["type"],
        })
    aggregate = task_publish_render.compose_publish_aggregate(rendered)
    summary = aggregate["headline"]

    if not do_send:
        print(f"preview summary :: {summary}")
        for label, key in (("result", "results"), ("problem", "problems"), ("reassurance", "reassurances")):
            for item in aggregate[key]:
                row = item["row"]
                print(
                    f"preview {label} sender={row['sender']} to={row['to_target']} "
                    f"task={row['task_id']} reason={row['reason']} :: {item['message']}"
                )
    else:
        # Phase 4 (2026-07-01, P4-B 调后): stamp ONLY handoff-class
        # publish reasons with `touch_handoff`; everything else is
        # left untouched so we don't flood agent_residency.json
        # with every reassurance ping.  `worker_completed_handed_to
        # _manager` and `delivered_to_user` are the two reasons
        # that start the handoff buffer (plan §设计二).
        try:
            from eduflow.store import agent_residency
            _handoff_reasons = {
                "worker_completed_handed_to_manager",
                "delivered_to_user",
            }
            for r in rows:
                if r.get("publish") and r.get("reason") in _handoff_reasons:
                    agent_residency.touch_handoff(str(r.get("to_target") or ""))
        except Exception:
            pass
        summary_sender = rendered[0]["row"]["sender"]
        rc = say_cmd.main([summary_sender, summary, "--to", to_target])
        if rc != 0:
            return error_exit(
                f"❌ publish-run failed for summary "
                f"(sender={summary_sender}, to={to_target})"
            )
        for key in ("results", "problems", "reassurances"):
            for item in aggregate[key]:
                row = item["row"]
                rc = say_cmd.main([row["sender"], item["message"], "--to", row["to_target"]])
                if rc != 0:
                    return error_exit(
                        f"❌ publish-run failed for {row['task_id']} "
                        f"(sender={row['sender']}, to={row['to_target']})"
                    )
    if advance:
        last = rows[-1]
        task_event_scanner.write_cursor(last["event_id"], last["created_at"])
        print(f"✅ advanced task publish cursor: {paths.task_publish_cursor_file()}")
    elif do_send:
        print("✅ publish-run sent without advancing cursor")
    else:
        print("ℹ️ dry-run only; add --send to publish")
    return 0


def _cmd_done(rest: list[str]) -> int:
    if len(rest) < 1:
        return usage_error(USAGE)
    return _cmd_update([rest[0], "--status", "已完成"])


def _cmd_list(rest: list[str]) -> int:
    status = pop_flag(rest, "--status")
    assignee = pop_flag(rest, "--assignee")
    include_archived = pop_bool_flag(rest, "--include-archived")
    rows = tasks.list_tasks(status=status, assignee=assignee,
                            include_archived=include_archived)
    if not rows:
        print("📋 no matching tasks")
        return 0
    print(f"📋 {len(rows)} tasks")
    for t in rows:
        for line in _fmt_task(t):
            print(line)
        print()
    return 0


def _cmd_archive(rest: list[str]) -> int:
    """T-104: physically move terminal tasks older than N days into
    monthly archive slices. Soft-marks them `archived=true` first (B),
    then drops them from tasks.json (A). Dry-run by default for safety.
    """
    older_than = pop_flag(rest, "--older-than") or "90d"
    dry_run = pop_bool_flag(rest, "--dry-run")
    if rest:
        return error_exit(f"❌ unexpected args: {rest}\n"
                          f"usage: eduflow task archive [--older-than 90d] [--dry-run]")
    days = _parse_older_than_days(older_than)
    summary = tasks.archive_tasks(older_than_days=days, dry_run=dry_run)
    summary["older_than"] = older_than
    print_json(summary)
    return 0


def _cmd_archive_schedule(rest: list[str]) -> int:
    """T-104: configure the watchdog's daily archive run.
    Persists into facts/archive-schedule.json (read by watchdog daily tick).
    """
    import time as _t
    from eduflow.runtime import paths
    from eduflow.util import write_json
    interval = pop_flag(rest, "--interval") or "daily"
    older_than = pop_flag(rest, "--older-than") or "90d"
    enable_arg = pop_flag(rest, "--enable")
    enable = (enable_arg or "").lower() not in ("false", "0", "no") if enable_arg else True
    if rest:
        return error_exit(f"❌ unexpected args: {rest}\n"
                          f"usage: eduflow task archive-schedule [--interval daily] "
                          f"[--older-than 90d] [--enable <true|false>]")
    if interval != "daily":
        return error_exit(f"❌ only --interval daily is supported (got {interval!r})")
    days = _parse_older_than_days(older_than)
    schedule = {
        "interval": interval,
        "older_than_days": days,
        "enabled": enable,
        "local_hour": 3,
        "updated_at": _t.time(),
    }
    path = paths.facts_dir() / "archive-schedule.json"
    paths.facts_dir().mkdir(parents=True, exist_ok=True)
    write_json(path, schedule)
    print_json(schedule)
    return 0


def _parse_older_than_days(value: str) -> int:
    """Accept '90d' / '90' / '30d' etc. Reject garbage; return int days."""
    text = str(value or "").strip().lower()
    if not text:
        return 90
    if text.endswith("d"):
        text = text[:-1]
    try:
        n = int(text)
    except ValueError:
        return error_exit(f"❌ invalid --older-than value: {value!r} (want e.g. 90d / 30)")
    if n < 0:
        return error_exit(f"❌ --older-than must be >= 0 (got {n})")
    return n


def _cmd_get(rest: list[str]) -> int:
    if len(rest) < 1:
        return usage_error(USAGE)
    t = tasks.get(rest[0])
    if t is None:
        return error_exit(f"❌ no such task: {rest[0]}")
    for line in _fmt_task(t):
        print(line)
    return 0


def _cmd_loop_check(rest: list[str]) -> int:
    spec_name = pop_flag(rest, "--spec") or "code-repair"
    max_cycles = int(pop_flag(rest, "--max-cycles") or "3")
    new_run = pop_bool_flag(rest, "--new-run")
    allow_unscoped = pop_bool_flag(rest, "--allow-unscoped-workspace")
    background = pop_bool_flag(rest, "--background")
    if len(rest) < 1:
        return usage_error(USAGE)
    tid = rest[0]
    task = tasks.get(tid)
    if task is None:
        return error_exit(f"❌ no such task: {tid}")
    if task.get("schema_version") != 2:
        return error_exit(f"❌ task {tid} is not a flow task")
    try:
        spec = loop_specs.resolve(spec_name)
        run = (
            loop_runs.create_new(task_id=tid, spec=spec["name"], max_cycles=max_cycles)
            if new_run
            else loop_runs.create_or_get_active(
                task_id=tid,
                spec=spec["name"],
                max_cycles=max_cycles,
            )
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")

    if background:
        try:
            tasks.set_loop_evidence(
                tid,
                loop_run_id=run["id"],
                loop_status="running",
                loop_cycle_count=int(run.get("cycle_count") or 0),
                loop_evidence_ref=loop_runs.evidence_ref(run["id"]),
                actor="manager",
            )
            cmd = [
                sys.executable,
                "-m",
                "eduflow.cli",
                "task",
                "loop-check",
                tid,
                "--spec",
                spec["name"],
                "--max-cycles",
                str(max_cycles),
            ]
            if allow_unscoped:
                cmd.append("--allow-unscoped-workspace")
            loop_runs.attach_background_log(run["id"])
            with loop_runs.artifact_path(run["id"], "background.log").open("a", encoding="utf-8") as log_fh:
                log_fh.write(f"$ {' '.join(cmd)}\n")
                log_fh.flush()
                subprocess.Popen(
                    cmd,
                    cwd=str(Path.cwd()),
                    stdout=log_fh,
                    stderr=log_fh,
                )
        except Exception as e:
            return error_exit(f"❌ failed to start background loop-check: {e}")
        print(f"✅ loop-check scheduled {tid} loop_id={run['id']} background=true")
        return 0

    cwd = Path(task.get("workspace_path") or Path.cwd())
    preflight = loop_preflight.check_workspace(
        workspace_mode=str(task.get("workspace_mode") or ""),
        workspace_path=str(task.get("workspace_path") or ""),
        allow_unscoped=allow_unscoped,
        cwd=cwd,
    )
    previous = (run.get("cycles") or [])[-1] if run.get("cycles") else None
    cycle = int(run.get("cycle_count") or 0) + 1
    if not preflight.get("ok"):
        check = {
            "passed": False,
            "checker_unavailable": False,
            "check_mode": "self_check",
            "passed_commands": [],
            "failed_commands": ["workspace preflight"],
            "checker_output": f"workspace preflight blocked: {preflight.get('reason')}",
            "failure_fingerprint": str(preflight.get("reason") or "workspace_policy_blocked"),
        }
        decision = {"status": "failed", "stop_reason": "workspace_policy_blocked"}
    else:
        check = loop_runner.run_checker_cycle(
            commands=spec["commands"],
            cwd=cwd,
            check_mode="self_check",
        )
        decision = loop_runner.decide_stop(
            check,
            previous,
            cycle=cycle,
            max_cycles=max_cycles,
        )

    updated = loop_runs.append_cycle(
        run["id"],
        checker_output=check.get("checker_output", ""),
        diff_text="",
        preflight=preflight,
        failed_commands=check.get("failed_commands") or [],
        passed_commands=check.get("passed_commands") or [],
        failure_fingerprint=check.get("failure_fingerprint", ""),
        status=decision["status"],
        stop_reason=decision.get("stop_reason", ""),
    )
    self_check_status = "passed" if decision["status"] == "passed" else "failed"
    recommended_action = (
        "send_builder_handoff"
        if decision["status"] in {"repair_needed", "stopped", "failed"}
        else ""
    )
    try:
        tasks.set_loop_evidence(
            tid,
            loop_run_id=run["id"],
            loop_status=decision["status"],
            loop_cycle_count=updated["cycle_count"],
            loop_stop_reason=decision.get("stop_reason", ""),
            loop_recommended_action=recommended_action,
            loop_evidence_ref=loop_runs.evidence_ref(run["id"]),
            self_check_status=self_check_status,
            review_check_status="pending",
            manager_closeout_status="blocked",
            actor="manager",
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")

    bg = " background=true" if background else ""
    print(
        f"✅ loop-check {tid} loop_id={run['id']} "
        f"loop_status={decision['status']} cycle_count={updated['cycle_count']}{bg}"
    )
    if recommended_action:
        print(f"recommended_action={recommended_action}")
        print(_builder_handoff_packet(tid, run["id"], check, loop_runs.evidence_ref(run["id"])))
    return 0


def _builder_handoff_packet(task_id: str, loop_id: str, check: dict, evidence_ref: str) -> str:
    failed = ", ".join(check.get("failed_commands") or []) or "-"
    output = str(check.get("checker_output") or "").strip().splitlines()
    summary = "\n".join(output[-8:]) if output else "-"
    return "\n".join([
        "Builder handoff",
        f"task_id: {task_id}",
        f"loop_id: {loop_id}",
        f"failed_commands: {failed}",
        f"failure_summary: {summary}",
        f"evidence_ref: {evidence_ref}",
        "red_lines: Do not weaken tests; do not delete tests; do not skip tests; do not edit unrelated files.",
        f"please re-run: eduflow task loop-check {task_id} --background",
    ])


def _cmd_loop_status(rest: list[str]) -> int:
    if len(rest) < 1:
        return usage_error(USAGE)
    ref = rest[0]
    task = tasks.get(ref)
    run = loop_runs.get(ref) if task is None else None
    if task is None and run is None:
        return error_exit(f"❌ no such task or loop: {ref}")
    if task is not None:
        print("agent_loop:")
        print(f"  loop_run_id: {task.get('loop_run_id') or ''}")
        print(f"  loop_status: {task.get('loop_status') or ''}")
        print(f"  cycle_count: {task.get('loop_cycle_count') or 0}")
        print(f"  evidence_ref: {task.get('loop_evidence_ref') or ''}")
        print(f"  recommended_action: {task.get('loop_recommended_action') or ''}")
        team_loop = team_loop_account.build(ref)
        if team_loop:
            print("team_loop:")
            for key in (
                "workflow_id",
                "phase",
                "cycle_count",
                "current_owner",
                "next_owner",
                "last_gate",
                "loop_health",
                "stuck_reason",
                "recommended_action",
                "self_check_status",
                "review_check_status",
                "manager_closeout_status",
            ):
                print(f"  {key}: {team_loop.get(key) or ''}")
        return 0
    print("agent_loop:")
    print(f"  loop_run_id: {run.get('id')}")
    print(f"  task_id: {run.get('task_id')}")
    print(f"  loop_status: {run.get('status')}")
    print(f"  cycle_count: {run.get('cycle_count')}")
    print(f"  evidence_ref: {run.get('evidence_ref')}")
    return 0


def _cmd_loop_contract(rest: list[str]) -> int:
    """Render the Loop Contract (Package 2 read model) for one task.

    Strictly read-only. Reuses existing task/evidence/loop/delivery state;
    does not write to the task or inbox.
    """
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0].startswith("-"):
        return usage_error(USAGE)
    if len(rest) > 1:
        return usage_error(USAGE)
    task_id = rest[0]
    contract = task_loop_contract.build(task_id)
    if contract is None:
        return error_exit(f"❌ no such task: {task_id}")
    if as_json:
        print_json({"loop_contract": contract})
        return 0
    print("- task_id: " + str(contract.get("task_id") or ""))
    print("- workflow_id: " + str(contract.get("workflow_id") or ""))
    print("- current_phase: " + str(contract.get("current_phase") or ""))
    print("- owner: " + str(contract.get("owner") or ""))
    print("- iteration: " + str(contract.get("iteration") or 0))
    delivery = contract.get("delivery") or {}
    print("- delivery_state: " + str(delivery.get("state") or ""))
    print("- delivery_inbox_local_id: " + str(delivery.get("inbox_local_id") or ""))
    print("- delivery_ack_required: " + str(bool(delivery.get("ack_required"))))
    print("- delivery_ack_state: " + str(delivery.get("ack_state") or ""))
    print("- delivery_ack_deadline: " + str(delivery.get("ack_deadline") or ""))
    failed = contract.get("failed_checks") or []
    print("- failed_checks:")
    if failed:
        for entry in failed:
            print(f"    - {entry}")
    else:
        print("    - (none)")
    allowed = contract.get("allowed_actions") or []
    print("- allowed_actions:")
    if allowed:
        for entry in allowed:
            print(f"    - {entry}")
    else:
        print("    - (none)")
    forbidden = contract.get("forbidden_actions") or []
    if forbidden:
        print("- forbidden_actions:")
        for entry in forbidden:
            print(f"    - {entry}")
    print("- next_required_output: " + str(contract.get("next_required_output") or ""))
    refs = contract.get("evidence_refs") or []
    print("- evidence_refs:")
    if refs:
        for entry in refs:
            print(f"    - {entry}")
    else:
        print("    - (none)")
    return 0


def _cmd_tool_risk(rest: list[str]) -> int:
    """Render the Tool Risk verdict (Package 3 read model) for one command.

    Strictly read-only. Never mutates command behavior. Caller passes a
    command string via `--command "..."`; we classify it and print the
    risk_level / access_mode / reason / advisory flags.
    """
    as_json = pop_bool_flag(rest, "--json")
    command = pop_flag(rest, "--command")
    if not command:
        return usage_error(USAGE)
    verdict = tool_risk.classify(command)
    if as_json:
        print_json({"tool_risk": verdict})
        return 0
    print(f"- risk_level: {verdict['risk_level']}")
    print(f"- access_mode: {verdict['access_mode']}")
    print(f"- reason: {verdict['reason']}")
    print(f"- requires_preflight: {verdict['requires_preflight']}")
    print(f"- requires_human_confirm: {verdict['requires_human_confirm']}")
    return 0


def _cmd_readiness_check(rest: list[str]) -> int:
    """Render the Operational Readiness verdict (Package 5 read model).

    Strictly read-only. NEVER auto-fixes, sends, archives, or touches
    runtime. Returns structured pass / warn / fail across
    delivery / productivity / source.

    Use `--diagnostics` to also print the raw signal values behind the
    verdict (for threshold tuning).
    """
    as_json = pop_bool_flag(rest, "--json")
    diagnostics = pop_bool_flag(rest, "--diagnostics")
    if not rest or rest[0].startswith("-"):
        return usage_error(USAGE)
    if len(rest) > 1:
        return usage_error(USAGE)
    task_id = rest[0]
    verdict = operational_readiness.build(task_id)
    if verdict is None:
        return error_exit(f"❌ no such task: {task_id}")
    signals = operational_readiness.diagnostics(task_id)
    if as_json:
        payload = {"readiness": verdict}
        if diagnostics and signals is not None:
            payload["readiness_diagnostics"] = signals
        print_json(payload)
        return 0
    print(f"- task_id: {verdict['task_id']}")
    for key in ("delivery", "productivity", "source"):
        section = verdict.get(key) or {}
        print(f"- {key}:")
        print(f"    status: {section.get('status', '')}")
        print(f"    reason: {section.get('reason', '')}")
    print(f"- overall: {verdict['overall']}")
    if diagnostics and signals is not None:
        print("- diagnostics:")
        print(f"    thresholds: {signals.get('thresholds')}")
        for key in ("delivery_signals", "productivity_signals", "source_signals"):
            print(f"    {key}: {signals.get(key)}")
    return 0


def _cmd_evolution_packet(rest: list[str]) -> int:
    """Render the Evolution Packet candidate (Package 4 read model).

    Strictly read-only. NEVER writes to memory / flow-memory / skills.
    Returns `{"candidates": []}` when no trigger fires.
    """
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0].startswith("-"):
        return usage_error(USAGE)
    if len(rest) > 1:
        return usage_error(USAGE)
    task_id = rest[0]
    payload = evolution_packet.build(task_id)
    if as_json:
        print_json(payload)
        return 0
    candidates = payload.get("candidates") or []
    print(f"- task_id: {task_id}")
    print(f"- candidate_count: {len(candidates)}")
    for i, c in enumerate(candidates, start=1):
        print(f"- candidate[{i}]:")
        for key in (
            "source_event", "trigger_reason", "scope", "kind",
            "confidence", "recommended_action",
        ):
            print(f"    {key}: {c.get(key) or ''}")
        refs = c.get("evidence_refs") or []
        print(f"    evidence_refs:")
        if refs:
            for r in refs:
                print(f"      - {r}")
        else:
            print("      - (none)")
        content = str(c.get("content") or "")
        print(f"    content: {content[:280]}")
    return 0


def _cmd_loop_list(rest: list[str]) -> int:
    task_id = pop_flag(rest, "--task-id") or ""
    status = pop_flag(rest, "--status") or ""
    if rest:
        return usage_error(USAGE)
    rows = loop_runs.list_runs(task_id=task_id, status=status)
    if not rows:
        print("📋 no matching loop runs")
        return 0
    print(f"📋 {len(rows)} loop runs")
    for row in rows:
        print(
            f"{row.get('id')} task_id={row.get('task_id')} "
            f"status={row.get('status')} cycle_count={row.get('cycle_count')} "
            f"evidence_ref={row.get('evidence_ref')}"
        )
    return 0


# ── Memory Bridge Helpers (Package: Memory + Hermes Manager Loop) ──
#
# These helpers wire task lifecycle events into the memory system.
# Design contract: every helper is fail-open. A memory-system error
# (ImportError, SQLite lock, exception in hook) MUST NEVER block the
# task command. The dispatch / review / closeout / correct paths
# remain the source of truth; memory is a downstream observer.
#
# All candidates generated here are "proposed" — promotion to confirmed
# memory requires an explicit `eduflow memory promote` by the manager.
# The bridge layer never auto-promotes.


def _print_dispatch_packet(assignee: str, task_id: str) -> None:
    """Print a pre-dispatch memory packet for the assignee.

    Fail-open: empty packet → note line; exception → warning.
    Never raises. Never blocks the caller (dispatch/flow_create).
    """
    try:
        from eduflow.memory.packet import assemble_memory_packet
    except Exception as e:
        print(f"⚠ memory packet: packet module unavailable ({e})")
        return
    try:
        packet = assemble_memory_packet(assignee, task_id=task_id)
    except Exception as e:
        print(f"⚠ memory packet failed for {assignee} task={task_id}: {e}")
        return
    if packet:
        print("--- Memory Packet (pre-dispatch) ---")
        print(packet)
        print("--- End Memory Packet ---")
    else:
        print(f"(no memory packet for {assignee} task={task_id})")


def _bridge_review_reject(task: dict, review_reason: str) -> None:
    """If review rejected a task, generate a proposed memory candidate.

    Fail-open. Never raises. Never blocks the caller (review command).
    Returns the candidate_id string for printing, or None.
    """
    try:
        from eduflow.memory.event_bridge import bridge_review_event
    except Exception as e:
        print(f"⚠ memory bridge: event_bridge unavailable ({e})")
        return None
    tid = task.get("id", "")
    if not tid:
        return None
    review_result = {
        "task_id": tid,
        "worker": task.get("assignee") or "",
        "verdict": "REJECTED",
        "reason": review_reason or "",
        "workflow_id": task.get("workflow_id") or "",
    }
    try:
        candidate_id = bridge_review_event(review_result)
    except Exception as e:
        print(f"⚠ memory bridge: review reject bridge failed ({e})")
        return None
    if candidate_id:
        print(f"📝 memory candidate: {candidate_id}")
    return candidate_id


def _resolve_evidence_field(evidence: dict, *candidates: str) -> int:
    """Resolve an evidence_packet field by trying multiple candidate keys.

    Tries each candidate in order, returning the first one that
    resolves to a positive integer. Returns 0 if none match.

    Why multiple candidates: legacy task evidence_packets use
    inconsistent field names depending on the workflow vintage
    (`items_count` vs `item_count`, `qql_count` vs `qa_count`,
    `manifest_rows` vs `manifest_covered_count` vs `items_mapping_count`).
    Falling back across candidates lets the bridge recognize more
    real tasks without changing their on-disk format.

    Skips None / empty string / non-positive values so that "missing
    field" and "field explicitly set to 0" both produce 0.
    """
    for key in candidates:
        val = evidence.get(key)
        if val is None:
            continue
        try:
            n = int(val)
            if n > 0:
                return n
        except (TypeError, ValueError):
            continue
    return 0


def _bridge_closeout_anomaly(task: dict) -> None:
    """After closeout, run consistency check and surface anomaly candidate.

    Fail-open. Never raises. Never blocks the caller (closeout command).

    Recognized evidence_packet field names (tried in order until a
    positive integer is found):

      items_count  ← items_count, item_count, itemcount
      qql_count    ← qql_count, qa_count, qa_count, qa_qql, qql
      manifest_count ← manifest_rows, manifest_covered_count,
                       items_mapping_count, manifest_count, mapping_count

    If all three resolve to 0 (legacy task with empty evidence_packet,
    or counts genuinely zero), the helper logs a no-op rather than
    firing a false-positive anomaly candidate.
    """
    try:
        from eduflow.memory.event_bridge import bridge_closeout_check
    except Exception as e:
        print(f"⚠ memory bridge: event_bridge unavailable ({e})")
        return
    tid = task.get("id", "")
    if not tid:
        return
    evidence = task.get("evidence_packet") or {}
    items_count = _resolve_evidence_field(
        evidence, "items_count", "item_count", "itemcount",
    )
    qql_count = _resolve_evidence_field(
        evidence, "qql_count", "qa_count", "qa_qql", "qql",
    )
    manifest_count = _resolve_evidence_field(
        evidence,
        "manifest_rows", "manifest_covered_count", "items_mapping_count",
        "manifest_count", "mapping_count",
    )
    workflow_id = task.get("workflow_id") or ""

    # No-op if all counts are 0: the evidence_packet is genuinely
    # missing or counts are zero, neither of which should trigger a
    # candidate (we'd be flooding the queue with false positives).
    if items_count == 0 and qql_count == 0 and manifest_count == 0:
        print(f"(closeout: no evidence counts for {tid}; bridge skipped)")
        return

    try:
        result = bridge_closeout_check(
            tid, items_count, qql_count, manifest_count,
            agent="manager", workflow_id=workflow_id,
        )
    except Exception as e:
        print(f"⚠ memory bridge: closeout check failed ({e})")
        return
    if result.get("consistent"):
        print(f"(closeout counts consistent: items={items_count} qql={qql_count} manifest={manifest_count})")
    else:
        cid = result.get("candidate_id")
        if cid:
            print(f"📝 closeout anomaly candidate: {cid} (items={items_count} qql={qql_count} manifest={manifest_count})")
        else:
            print(f"⚠ closeout counts inconsistent (items={items_count} qql={qql_count} manifest={manifest_count}) but no candidate created")
    blocking = result.get("blocking_constraints") or []
    if blocking:
        print(f"   blocking constraints ({len(blocking)}):")
        for b in blocking[:3]:
            bid = b.get("id", "")
            print(f"   - [{bid}] {b.get('content', '')}")


def _cmd_correct(rest: list[str]) -> int:
    """Manager explicit correction → memory candidate.

    Usage:
      eduflow task correct <agent> "<correction_content>" [--severity high|medium|critical] [--context "<ctx>"] [--force | --no-sensitive-check]

    The correction is recorded as a proposed candidate. It never
    auto-promotes to confirmed memory; the manager must review via
    `eduflow memory candidates` / `promote` / `reject`.

    Fail-open: if the memory bridge is unavailable, the command still
    returns 0 with a warning. Corrections are deliberate knowledge
    transfers; we don't want to silently drop them.

    Sensitive-content guardrail (PII / secrets):
      Detects likely API keys, tokens, passwords, emails, and SSN-like
      strings in the content or context. When detected, prints a clear
      warning to stderr but does NOT block the command — managers are
      the ultimate authority on what they paste.

      Flag semantics:
        --force              generic "I know what I'm doing" flag.
                              Used to override ANY future safety
                              check (PII, profanity, length, etc.).
        --no-sensitive-check semantic alias — overrides ONLY the
                              PII scanner. Same effect today as
                              --force, but tracked separately in
                              the bridge context so future
                              additional checks (profanity,
                              length, etc.) can be left enabled
                              while still skipping just the
                              sensitive-content scanner.

      If both are passed, --force wins on the "I meant to override"
      semantic. The bridge context records which flag(s) the caller
      used, so downstream reviewers can audit.
    """
    if len(rest) < 2:
        return usage_error(USAGE)
    agent = rest.pop(0)
    content = rest.pop(0)
    severity = (pop_flag(rest, "--severity") or "medium").lower()
    if severity not in ("low", "medium", "high", "critical"):
        return usage_error(f"❌ invalid --severity: {severity} (use low|medium|high|critical)")
    ctx = pop_flag(rest, "--context") or ""
    # --force is the original generic override: skip ALL safety checks.
    force = pop_bool_flag(rest, "--force")
    # --no-sensitive-check: skip ONLY the PII/sensitive-content
    # scanner. Unlike --force, this does NOT suppress future checks
    # (profanity, length limits, etc.). The distinction matters when
    # the scanner grows additional checks — --no-sensitive-check lets
    # those run while still skipping just the sensitive scan.
    no_sensitive_check = pop_bool_flag(rest, "--no-sensitive-check")
    # Track each flag separately for the audit log / bridge context.
    # If both flags are passed, both are recorded; --force wins
    # semantically (it's the broader override).
    suppress_sensitive = force or no_sensitive_check
    if not agent or not content:
        return usage_error("usage: eduflow task correct <agent> \"<correction_content>\" [--severity ...] [--context ...] [--force | --no-sensitive-check]")

    # ── Pre-checks ──────────────────────────────────────────────
    # --force skips ALL pre-checks (--no-sensitive-check skips only
    # the sensitive-content scanner; future checks still run).
    if not force:
        # Sensitive-content check (warn-only; suppressed by either
        # flag). Fail-open: if the scanner itself raises, log a
        # warning and continue. The bridge to memory is the source
        # of truth; a broken scanner must not block corrections.
        try:
            matches = _scan_sensitive_content(content, ctx)
        except Exception as e:
            print(f"⚠ sensitive-content scanner failed ({e}); proceeding without warning", file=sys.stderr)
            matches = []
        if matches and not suppress_sensitive:
            print(
                "⚠ sensitive-pattern warning: detected in content/context:",
                file=sys.stderr,
            )
            for kind in matches[:5]:
                print(f"   - {kind}", file=sys.stderr)
            print(
                "   This content will be written to memory_candidates DB "
                "and exported to Obsidian. Re-run with --force to skip "
                "all checks, or --no-sensitive-check to skip only this "
                "scanner.",
                file=sys.stderr,
            )

    try:
        from eduflow.memory.event_bridge import bridge_manager_correction
    except Exception as e:
        print(f"⚠ memory bridge: event_bridge unavailable ({e})")
        return 0
    try:
        candidate_id = bridge_manager_correction(
            agent, content, severity=severity, context=ctx,
        )
    except Exception as e:
        print(f"⚠ memory bridge: manager correction bridge failed ({e})")
        return 0
    if candidate_id:
        flags_used = []
        if force:
            flags_used.append("force")
        if no_sensitive_check:
            flags_used.append("no_sensitive_check")
        flag_str = f" flags={','.join(flags_used)}" if flags_used else ""
        print(f"📝 correction candidate: {candidate_id} agent={agent} severity={severity}{flag_str}")
    else:
        print(f"⚠ memory bridge returned no candidate_id (agent={agent})")
    return 0


def _cmd_report_failure(rest: list[str]) -> int:
    """Worker/reviewer self-reports an unrecoverable failure on a task.

    Usage:
      eduflow task report-failure <id> --actor <worker|reviewer> [--reason "<text>"]

    Transitions the task to status=failed. The state machine allows
    worker/reviewer from assigned / in_progress / blocked /
    submitted_for_review; manager is not allowed (manager should use
    `task flow-transition ... --to cancelled` for explicit cancellation).

    Always fires `bridge_task_lifecycle("fail", ...)` so the failure
    becomes a candidate in memory_candidates (idempotent by task_id).

    Fail-open: bridge failures don't block the state transition. The
    reason text is preserved on the task itself so subsequent review
    of the failure has context.
    """
    if len(rest) < 1:
        return usage_error(USAGE)
    actor = pop_flag(rest, "--actor")
    reason = pop_flag(rest, "--reason") or ""
    if not actor:
        return usage_error(
            "usage: eduflow task report-failure <id> --actor <worker|reviewer> [--reason \"<text>\"]"
        )
    tid = rest[0]
    try:
        ok = tasks.report_flow_failure(tid, actor=actor, reason=reason)
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    task = tasks.get(tid) or {}
    print(
        f"✅ reported failure on {tid} actor={actor} "
        f"status={task.get('status', '-')}"
        f"{' reason=' + reason if reason else ''}"
    )
    # Bridge fires inside report_flow_failure; if a candidate was
    # created we can't tell here without re-querying, but the standard
    # transition announcement is enough for the operator.
    _auto_publish_stage_tick(tid)
    return 0


def _cmd_update_verdict(rest: list[str]) -> int:
    """Update a task's verdict after it has been delivered.

    Usage:
      eduflow task update-verdict <id> --actor <reviewer|manager> --verdict <value> [--reason "<text>"]

    Verdict values: approved / rejected / manager_action / pending.

    Use this when a downstream review concludes the task's gate failed
    even though the worker formally "completed". The state machine
    normally resets verdict to "approved" on `to_status="delivered"`,
    so a post-delivery verdict update requires going around the state
    machine. When verdict transitions to "rejected", the memory
    bridge fires a witness candidate (the delivered+rejected path).
    """
    if len(rest) < 1:
        return usage_error(USAGE)
    actor = pop_flag(rest, "--actor")
    verdict = pop_flag(rest, "--verdict")
    reason = pop_flag(rest, "--reason") or ""
    if not actor or not verdict:
        return usage_error(
            "usage: eduflow task update-verdict <id> --actor <reviewer|manager> "
            "--verdict <approved|rejected|manager_action|pending> [--reason \"<text>\"]"
        )
    tid = rest[0]
    try:
        ok = tasks.update_post_delivery_verdict(
            tid, actor=actor, verdict=verdict, reason=reason,
        )
    except ValueError as e:
        return error_exit(f"❌ {e}")
    if not ok:
        return error_exit(f"❌ no such task: {tid}")
    task = tasks.get(tid) or {}
    print(
        f"✅ verdict updated {tid} "
        f"verdict={task.get('verdict', '-')}"
        f"{' reason=' + reason if reason else ''}"
    )
    _auto_publish_stage_tick(tid)
    return 0


# Patterns that should trigger a sensitive-content warning. The check is
# intentionally conservative — false positives are cheaper than a leaked
# secret. The list is plain string substrings; case-insensitive matching
# keeps the implementation stdlib-only.
_SENSITIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    # Generic API key / secret indicators
    ("api_key=", "API key assignment"),
    ("apikey=", "API key assignment"),
    ("api-token", "API token reference"),
    ("bearer ", "Bearer token prefix"),
    ("secret_key", "secret key reference"),
    ("password=", "password assignment"),
    ("passwd=", "password assignment"),
    ("-----BEGIN", "PEM private key block"),
    ("aws_access_key", "AWS access key reference"),
    ("aws_secret", "AWS secret reference"),
    ("private_key", "private key reference"),
    # Token-shaped strings (long hex/base64)
    # We look for explicit prefixes rather than try to detect random tokens,
    # which would have too many false positives.
    ("sk_live_", "Stripe live secret key"),
    ("sk_test_", "Stripe test secret key"),
    ("ghp_", "GitHub personal access token"),
    ("xoxb-", "Slack bot token"),
    ("xoxp-", "Slack user token"),
    # PII patterns (string-substring, conservative)
    ("@gmail.com", "email address (gmail)"),
    ("@yahoo.com", "email address (yahoo)"),
    ("@qq.com", "email address (qq)"),
    ("@163.com", "email address (163)"),
    ("ssn:", "SSN label"),
    ("social security", "SSN label"),
    ("身份证", "Chinese national ID label"),
    ("手机号:", "phone label"),
)


def _scan_sensitive_content(content: str, context: str = "") -> list[str]:
    """Return list of sensitive-pattern labels found in content/context.

    Returns an empty list when nothing detected. Always case-insensitive.
    Stdlib-only; no regex compilation needed.
    """
    haystack = (content or "") + "\n" + (context or "")
    if not haystack:
        return []
    lowered = haystack.lower()
    found: list[str] = []
    seen: set[str] = set()
    for needle, label in _SENSITIVE_PATTERNS:
        # Lower the needle too — patterns are written in mixed case for
        # human readability, but the haystack is already lowered, so
        # raw needles like "-----BEGIN" never match. Lowering here is
        # cheaper than re-lowering the pattern list at module load.
        if needle.lower() in lowered and label not in seen:
            found.append(label)
            seen.add(label)
    return found


SUBCOMMANDS = {
    "create": _cmd_create,
    "flow-create": _cmd_flow_create,
    "dispatch": _cmd_dispatch,
    "correct": _cmd_correct,
    "report-failure": _cmd_report_failure,
    "update-verdict": _cmd_update_verdict,
    "flow-transition": _cmd_flow_transition,
    "submit-review": _cmd_submit_review,
    "assign-reviewer": _cmd_assign_reviewer,
    "review": _cmd_review,
    "review-queue": _cmd_review_queue,
    "workflow-status": _cmd_workflow_status,
    "manager-overview": _cmd_manager_overview,
    "scan-anomalies": _cmd_scan_anomalies,
    "auto-ops-context": _cmd_auto_ops_context,
    "auto-ops-production": _cmd_auto_ops_production,
    "manager-actions": _cmd_manager_actions,
    "manager-action-apply": _cmd_manager_action_apply,
    "manager-panel": _cmd_manager_panel,
    "ops-dashboard": _cmd_ops_dashboard,
    "evidence-account": _cmd_evidence_account,
    "evidence-explain": _cmd_evidence_explain,
    "loop-check": _cmd_loop_check,
    "loop-status": _cmd_loop_status,
    "loop-contract": _cmd_loop_contract,
    "tool-risk": _cmd_tool_risk,
    "evolution-packet": _cmd_evolution_packet,
    "readiness-check": _cmd_readiness_check,
    "loop-list": _cmd_loop_list,
    "subject-inventory": _cmd_subject_inventory,
    "batch-closeout": _cmd_batch_closeout,
    "manager-closeout": _cmd_manager_closeout,
    "supervisor-check": _cmd_supervisor_check,
    "publish-check": _cmd_publish_check,
    "publish-scan": _cmd_publish_scan,
    "publish-run": _cmd_publish_run,
    "update": _cmd_update,
    "done":   _cmd_done,
    "list":   _cmd_list,
    "get":    _cmd_get,
    "archive": _cmd_archive,
    "archive-schedule": _cmd_archive_schedule,
}


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, USAGE):
        return 0
    if not argv:
        # No subcommand: print usage to stdout (it IS the requested output)
        # but return 1 so scripts know the call was incomplete.
        print(USAGE)
        return 1
    sub = argv[0]
    if sub not in SUBCOMMANDS:
        return error_exit(f"unknown task subcommand: {sub}\n{USAGE}")
    return SUBCOMMANDS[sub](list(argv[1:]))
