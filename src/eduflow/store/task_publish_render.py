"""Render boss-facing publish messages from flow-task decisions.

Package 8: adds ``render_visible_truth_snapshot`` (evidence-driven
snapshot with NO hand-written subject lists) and ``compose_visible_sources``
(source audit trail for manager panel).
"""
from __future__ import annotations

from eduflow.util import now_ms


_STAGE_LABELS = {
    "curriculum": "课程研发",
    "review": "审核",
    "qbank": "题库",
    "builder": "系统建设",
    "admissions": "申请服务",
    "school": "学校事务",
}
MANAGER_RESPONSE_TAXONOMY = frozenset({
    "final_result_delivered",
    "manager_problem_scope_pending",
    "manager_problem_material_pending",
    "manager_problem_direction_pending",
    "manager_problem_revision_in_progress",
    "generic_manager_update_fallback",
    "internal_only",
    "worker_reassurance",
})
_MANAGER_RESPONSE_BY_REASON = {
    "delivered_to_user": "final_result_delivered",
    "user_explanation_scope_pending": "manager_problem_scope_pending",
    "user_explanation_material_pending": "manager_problem_material_pending",
    "user_explanation_direction_pending": "manager_problem_direction_pending",
    "user_explanation_revision_in_progress": "manager_problem_revision_in_progress",
}
_MANAGER_RESPONSE_BY_REVIEW_REASON = {
    "approved_for_delivery": "final_result_delivered",
    "missing_scope_confirmation": "manager_problem_scope_pending",
    "missing_required_artifact": "manager_problem_material_pending",
    "missing_owner_decision": "manager_problem_direction_pending",
    "changes_requested": "manager_problem_revision_in_progress",
    "quality_not_met": "manager_problem_revision_in_progress",
}
SURFACE_STATE_LABELS = {
    "accepted_current_subject": "已接到当前学科任务",
    "producing_current_subject": "正在处理当前学科",
    "delivered_to_review": "已交给 review",
    "review_pending_current_subject": "当前学科待 review 接手",
    "reviewing_current_subject": "正在 review 当前学科",
    "minor_fix_requested": "已要求 minor fix",
    "review_passed_waiting_manager_closeout": "review 已通过，待 manager 收口",
    "builder_task_accepted": "builder 已接单",
    "builder_artifact_ready": "builder 产物已回交",
    "qbank_check_accepted": "qbank 校验已接单",
    "qbank_first_verdict_ready": "qbank 首个 verdict 已就绪",
    "stale_status_surface": "状态面滞后",
    "status_truth_lag_detected": "状态真相未同步",
    "unknown_surface_state": "未识别状态面",
}


def stage_label(stage: str) -> str:
    return _STAGE_LABELS.get(stage, stage or "未分类")


def describe_surface_state(state: str) -> str:
    normalized = str(state or "").strip()
    if not normalized:
        return SURFACE_STATE_LABELS["unknown_surface_state"]
    return SURFACE_STATE_LABELS.get(normalized, normalized)


def compose_manager_response(task: dict, decision: dict | None = None) -> dict:
    decision = decision or {}
    reason = str(decision.get("reason") or "").strip()
    delivery_lane = str(decision.get("delivery_lane") or "").strip()
    review_reason = str(task.get("review_reason") or "").strip()
    latest_turn_summary = str(task.get("latest_turn_summary") or "").strip()
    stage_cn = stage_label(str(task.get("stage") or ""))
    title = task.get("title") or str(decision.get("task_id") or task.get("id") or "")
    task_id = str(decision.get("task_id") or task.get("id") or "")
    verdict = str(task.get("verdict") or "").strip()

    manager_response_type = str(decision.get("manager_response_type") or "").strip()
    if not manager_response_type:
        manager_response_type = _MANAGER_RESPONSE_BY_REASON.get(reason, "")
    if not manager_response_type:
        manager_response_type = _MANAGER_RESPONSE_BY_REVIEW_REASON.get(review_reason, "")
    if not manager_response_type and delivery_lane == "worker_reassurance":
        manager_response_type = "worker_reassurance"
    if not manager_response_type and reason == "manager_action_internal_only":
        manager_response_type = "generic_manager_update_fallback"
    if not manager_response_type and (task.get("needs_manager_action") or verdict == "manager_action"):
        manager_response_type = "generic_manager_update_fallback"
    if not manager_response_type:
        manager_response_type = "internal_only"

    if manager_response_type == "final_result_delivered":
        message = f"{stage_cn}已完成并交付：{title}（{task_id}）"
    elif manager_response_type == "manager_problem_scope_pending":
        message = f"{stage_cn}正在确认范围后再继续推进：{title}（{task_id}）"
    elif manager_response_type == "manager_problem_material_pending":
        message = f"{stage_cn}正在补齐必要材料后再继续推进：{title}（{task_id}）"
    elif manager_response_type == "manager_problem_direction_pending":
        message = f"{stage_cn}正在等待方向确认后再继续推进：{title}（{task_id}）"
    elif manager_response_type == "manager_problem_revision_in_progress":
        message = f"{stage_cn}正在根据当前问题处理并推进修订：{title}（{task_id}）"
    elif manager_response_type == "generic_manager_update_fallback":
        if latest_turn_summary:
            message = f"{stage_cn}正在处理中：{title}（{task_id}）"
        else:
            message = f"{stage_cn}正在由 manager 跟进处理：{title}（{task_id}）"
    elif manager_response_type == "worker_reassurance":
        message = ""
    else:
        message = ""

    return {
        "type": manager_response_type,
        "message": message,
    }


def render_publish_message(task: dict, decision: dict) -> str:
    title = task.get("title") or decision["task_id"]
    stage = str(task.get("stage") or "")
    stage_cn = stage_label(stage)
    verdict = task.get("verdict") or "-"
    task_id = decision["task_id"]
    reason = str(decision.get("reason") or "")
    delivery_phrase = task_publish_render_phrase(task)
    delivery_lane = str(decision.get("delivery_lane") or "")
    manager_response = compose_manager_response(task, decision)

    if delivery_lane == "worker_reassurance":
        return render_worker_reassurance(task, decision)

    if manager_response["type"] in MANAGER_RESPONSE_TAXONOMY - {"internal_only", "worker_reassurance"}:
        return manager_response["message"]

    if reason and reason != "delivered_to_user":
        return f"内部事件：{title}（{task_id}，status={task.get('status') or '-'}，reason={reason or 'internal_only'}）"

    if stage == "curriculum":
        return f"课程研发{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    if stage == "review":
        return f"审核任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    if stage == "qbank":
        return f"题库任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    if stage == "builder":
        return f"系统建设任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    if stage == "admissions":
        return f"申请服务任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    if stage == "school":
        return f"学校事务任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"
    return f"{stage_cn}任务{delivery_phrase}：{title}（{task_id}，结论={verdict}）"


def task_publish_render_phrase(task: dict) -> str:
    try:
        from eduflow.store import tasks
        return tasks.flow_user_delivery_phrase(task)
    except Exception:
        return "已完成交付"


def render_user_explanation(task: dict, decision: dict) -> str:
    return compose_manager_response(task, decision)["message"]


def render_worker_reassurance(task: dict, decision: dict) -> str:
    title = task.get("title") or decision["task_id"]
    task_id = decision["task_id"]
    reason = str(decision.get("reason") or "")
    stage_cn = stage_label(str(task.get("stage") or ""))

    if reason == "worker_accepted":
        return f"{stage_cn}任务已接单：{title}（{task_id}）"
    if reason == "worker_started":
        return f"{stage_cn}任务已开始处理：{title}（{task_id}）"
    if reason == "worker_waiting_on_manager":
        return f"{stage_cn}任务已提交 manager 处理：{title}（{task_id}）"
    if reason == "worker_completed_handed_to_manager":
        return f"{stage_cn}任务已完成并交给 manager：{title}（{task_id}）"
    return f"{stage_cn}任务处理中：{title}（{task_id}）"


def render_publish_summary(items: list[dict]) -> str:
    items = [item for item in items if (item.get("row") or {}).get("publish")]
    count = len(items)
    if count <= 0:
        return "本轮暂无可对老板播报的交付结果。"
    stages: list[str] = []
    for item in items:
        stage = stage_label(str(item.get("stage") or ""))
        if stage not in stages:
            stages.append(stage)
    stage_part = "、".join(stages[:3])
    if count == 1:
        return f"本轮有 1 项新交付，来自 {stage_part}。"
    return f"本轮有 {count} 项新交付，主要来自 {stage_part}。"


def compose_publish_aggregate(items: list[dict]) -> dict:
    publishable = [item for item in items if (item.get("row") or {}).get("publish")]
    if not publishable:
        return {
            "headline": "当前暂无新的正式汇报。",
            "results": [],
            "problems": [],
            "reassurances": [],
            "fallback": "none",
        }

    results = [
        item for item in publishable
        if str(item.get("manager_response_type") or "") == "final_result_delivered"
    ]
    problems = [
        item for item in publishable
        if str(item.get("manager_response_type") or "").startswith("manager_problem_")
        or str(item.get("manager_response_type") or "") == "generic_manager_update_fallback"
    ]
    reassurances = [
        item for item in publishable
        if str(item.get("manager_response_type") or "") == "worker_reassurance"
    ]

    result_stages: list[str] = []
    for item in results:
        stage = stage_label(str(item.get("stage") or ""))
        if stage not in result_stages:
            result_stages.append(stage)

    problem_types: list[str] = []
    for item in problems:
        manager_response_type = str(item.get("manager_response_type") or "")
        if manager_response_type == "manager_problem_scope_pending":
            label = "范围确认"
        elif manager_response_type == "manager_problem_material_pending":
            label = "材料补齐"
        elif manager_response_type == "manager_problem_direction_pending":
            label = "方向确认"
        elif manager_response_type == "manager_problem_revision_in_progress":
            label = "修订处理中"
        else:
            label = "问题处理中"
        if label not in problem_types:
            problem_types.append(label)

    reassurance_stages: list[str] = []
    for item in reassurances:
        stage = stage_label(str(item.get("stage") or ""))
        if stage not in reassurance_stages:
            reassurance_stages.append(stage)

    if results:
        headline = (
            f"本轮已完成 {len(results)} 项正式交付"
            f"{'，涉及 ' + '、'.join(result_stages[:3]) if result_stages else ''}。"
        )
        if problems:
            headline += (
                f" 另有 {len(problems)} 项待处理问题，主要集中在"
                f"{'、'.join(problem_types[:3])}。"
            )
    elif problems:
        headline = (
            f"当前有 {len(problems)} 项事项待 manager 继续处理，"
            f"主要集中在{'、'.join(problem_types[:3])}。"
        )
    elif reassurances:
        headline = (
            f"当前主要是执行中更新，已有 {len(reassurances)} 项在推进"
            f"{'，来自 ' + '、'.join(reassurance_stages[:3]) if reassurance_stages else ''}。"
        )
    else:
        headline = "当前暂无新的正式汇报。"

    return {
        "headline": headline,
        "results": results,
        "problems": problems,
        "reassurances": reassurances,
        "fallback": "none" if (results or problems or reassurances) else "empty_publishable",
    }


# ── Package 8: visible truth snapshot & source audit ─────────────


def render_visible_truth_snapshot(task: dict) -> dict:
    """Build an evidence-driven snapshot of a task's visible state.

    **Never** contains hand-written four-subject lists or hardcoded
    status strings. Every field is derived from structured task data.

    Returns a dict with:
    - ``task_id``
    - ``subject_inventory_summary`` — from task evidence, not hand-written
    - ``qbank_report_path`` — from evidence or ``"source_missing"``
    - ``qbank_status`` — from evidence
    - ``verifier_summary`` — from task verifier fields if available
    - ``health_runtime_status`` — if relevant
    - ``generated_at_ms`` — epoch-ms timestamp
    """
    task_id = str(task.get("id") or task.get("task_id") or "")

    # Subject inventory — derived from task evidence, NOT hand-written
    subject_id = str(task.get("subject_id") or task.get("subject_slug") or "")
    subject_name = str(task.get("subject_name") or "")
    inventory_bits = []
    if subject_id:
        inventory_bits.append(f"subject_id={subject_id}")
    if subject_name:
        inventory_bits.append(f"subject_name={subject_name}")
    closeout_status = str(task.get("closeout_status") or "")
    if closeout_status:
        inventory_bits.append(f"closeout={closeout_status}")
    subject_inventory_summary = "; ".join(inventory_bits) if inventory_bits else "source_missing"

    # QBank evidence
    qbank = task.get("qbank") or {}
    qbank_report_path = str(qbank.get("report_path") or task.get("qbank_report_path") or "")
    qbank_status = str(qbank.get("status") or task.get("qbank_status") or "")
    if not qbank_report_path and not qbank_status:
        qbank_report_path = "source_missing"
        qbank_status = "unknown"

    # Verifier evidence — from task's verifier fields
    verifier = task.get("verifier") or {}
    verifier_summary: str | None = str(verifier.get("summary") or "")
    if not verifier_summary:
        verdict_target = str(task.get("verdict_target") or "")
        verdict = str(task.get("verdict") or "")
        if verdict_target or verdict:
            verifier_summary = f"verdict={verdict} target={verdict_target}"
    if not verifier_summary:
        verifier_summary = None  # explicitly absent, not hand-written

    loop_summary = None
    if task.get("loop_run_id"):
        loop_summary = {
            "run_id": str(task.get("loop_run_id") or ""),
            "status": str(task.get("loop_status") or ""),
            "cycle_count": int(task.get("loop_cycle_count") or 0),
            "evidence_ref": str(task.get("loop_evidence_ref") or ""),
        }

    # Health / runtime status — only include if relevant
    runtime_status = str(task.get("runtime_status") or task.get("health_status") or "")
    health_runtime_status = runtime_status if runtime_status else None

    return {
        "task_id": task_id,
        "subject_inventory_summary": subject_inventory_summary,
        "qbank_report_path": qbank_report_path if qbank_report_path else None,
        "qbank_status": qbank_status,
        "verifier_summary": verifier_summary,
        "loop_summary": loop_summary,
        "health_runtime_status": health_runtime_status,
        "generated_at_ms": now_ms(),
    }


def compose_visible_sources(task: dict) -> dict:
    """Return an audit-trail map showing where each piece of evidence
    comes from — or ``"source_missing"`` when evidence is absent.

    Designed for the manager panel so the operator can trace every
    claim back to its origin.
    """
    task_id = str(task.get("id") or task.get("task_id") or "")

    # Subject inventory source
    subject_id = str(task.get("subject_id") or task.get("subject_slug") or "")
    subject_inventory_source = (
        f"subject_inventory({subject_id})" if subject_id
        else "source_missing"
    )

    # QBank report path
    qbank = task.get("qbank") or {}
    qbank_report_path: str | None = str(
        qbank.get("report_path") or task.get("qbank_report_path") or ""
    )
    if not qbank_report_path:
        qbank_report_path = None

    # Verifier report path
    verifier = task.get("verifier") or {}
    verifier_report_path: str | None = str(
        verifier.get("report_path") or task.get("verifier_report_path") or ""
    )
    if not verifier_report_path:
        # Fallback: check if verifier result was embedded
        verifier_result = task.get("verifier_result")
        if isinstance(verifier_result, dict) and verifier_result.get("report_path"):
            verifier_report_path = str(verifier_result["report_path"])
    if not verifier_report_path:
        verifier_report_path = None

    loop_evidence_ref = str(task.get("loop_evidence_ref") or "")

    # Assemble presence / absence lists
    sources_present: list[str] = ["task_id"]
    sources_missing: list[str] = []

    if subject_id:
        sources_present.append("subject_inventory")
    else:
        sources_missing.append("subject_inventory")

    if qbank_report_path:
        sources_present.append("qbank_report")
    else:
        sources_missing.append("qbank_report")

    verifier_present = bool(
        verifier_report_path
        or (isinstance(task.get("verifier_result"), dict) and task["verifier_result"])
        or str(task.get("verdict") or "")
    )
    if verifier_present:
        sources_present.append("verifier")
    else:
        sources_missing.append("verifier")

    if loop_evidence_ref:
        sources_present.append("loop_evidence")

    return {
        "task_id": task_id,
        "subject_inventory_source": subject_inventory_source,
        "qbank_report_path": qbank_report_path,
        "verifier_report_path": verifier_report_path,
        "loop_evidence_ref": loop_evidence_ref,
        "sources_present": sources_present,
        "sources_missing": sources_missing,
    }
