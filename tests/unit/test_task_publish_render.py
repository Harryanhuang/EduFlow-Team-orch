"""Tests for task publish message rendering."""
from __future__ import annotations

from eduflow.store import task_publish_render


def _decision(task_id: str = "T-1") -> dict:
    return {"task_id": task_id}


def test_render_curriculum_message():
    msg = task_publish_render.render_publish_message(
        {
            "title": "完成 Unit 1 大纲",
            "stage": "curriculum",
            "verdict": "approved",
            "review_reason": "approved_for_delivery",
        },
        _decision(),
    )
    assert "课程研发已完成并交付" in msg
    assert "完成 Unit 1 大纲" in msg


def test_compose_manager_response_for_final_result():
    composed = task_publish_render.compose_manager_response(
        {
            "id": "T-1",
            "title": "完成 Unit 1 大纲",
            "stage": "curriculum",
            "verdict": "approved",
            "review_reason": "approved_for_delivery",
        },
        {"task_id": "T-1", "reason": "delivered_to_user", "delivery_lane": "manager_result"},
    )
    assert composed["type"] == "final_result_delivered"
    assert "已完成并交付" in composed["message"]


def test_compose_manager_response_for_scope_pending_problem():
    composed = task_publish_render.compose_manager_response(
        {
            "id": "T-1",
            "title": "Draft Unit 1",
            "stage": "curriculum",
            "review_reason": "missing_scope_confirmation",
            "needs_manager_action": True,
        },
        {"task_id": "T-1", "reason": "user_explanation_scope_pending", "delivery_lane": "manager_problem"},
    )
    assert composed["type"] == "manager_problem_scope_pending"
    assert "正在确认范围后再继续推进" in composed["message"]


def test_compose_manager_response_falls_back_cleanly_for_legacy_problem():
    composed = task_publish_render.compose_manager_response(
        {
            "id": "T-9",
            "title": "Legacy Manager Task",
            "stage": "curriculum",
            "review_reason": "legacy_phrase",
            "needs_manager_action": True,
            "latest_turn_summary": "Internal manager-only trace",
        },
        {"task_id": "T-9", "delivery_lane": "manager_problem"},
    )
    assert composed["type"] == "generic_manager_update_fallback"
    assert "正在处理中" in composed["message"]


def test_render_worker_started_reassurance():
    msg = task_publish_render.render_publish_message(
        {"title": "完成 Unit 1 大纲", "stage": "curriculum"},
        {
            "task_id": "T-1",
            "reason": "worker_started",
            "delivery_lane": "worker_reassurance",
        },
    )
    assert "已开始处理" in msg
    assert "完成 Unit 1 大纲" in msg


def test_render_worker_completed_handoff_reassurance():
    msg = task_publish_render.render_publish_message(
        {"title": "完成 Unit 1 大纲", "stage": "curriculum"},
        {
            "task_id": "T-1",
            "reason": "worker_completed_handed_to_manager",
            "delivery_lane": "worker_reassurance",
        },
    )
    assert "已完成并交给 manager" in msg


def test_render_worker_waiting_on_manager_reassurance():
    msg = task_publish_render.render_publish_message(
        {"title": "完成 Unit 1 大纲", "stage": "curriculum"},
        {
            "task_id": "T-1",
            "reason": "worker_waiting_on_manager",
            "delivery_lane": "worker_reassurance",
        },
    )
    assert "已提交 manager 处理" in msg


def test_render_builder_message():
    msg = task_publish_render.render_publish_message(
        {
            "title": "修复发布链路",
            "stage": "builder",
            "verdict": "approved",
            "review_reason": "approved_for_delivery",
        },
        _decision(),
    )
    assert "系统建设已完成并交付" in msg
    assert "修复发布链路" in msg


def test_render_unknown_stage_falls_back_to_generic():
    msg = task_publish_render.render_publish_message(
        {
            "title": "其他事项",
            "stage": "ops",
            "verdict": "approved",
            "review_reason": "approved_for_delivery",
        },
        _decision("T-9"),
    )
    assert "ops已完成并交付" in msg
    assert "T-9" in msg


def test_render_internal_reason_returns_internal_marker():
    msg = task_publish_render.render_publish_message(
        {"title": "Draft Unit 1", "stage": "curriculum", "status": "blocked"},
        {"task_id": "T-1", "reason": "manager_action_internal_only"},
    )
    assert "正在由 manager 跟进处理" in msg


def test_render_scope_pending_user_explanation():
    msg = task_publish_render.render_publish_message(
        {"title": "Draft Unit 1", "stage": "curriculum"},
        {
            "task_id": "T-1",
            "reason": "user_explanation_scope_pending",
            "delivery_lane": "manager_problem",
        },
    )
    assert "正在确认范围后再继续推进" in msg
    assert "Draft Unit 1" in msg


def test_render_revision_in_progress_user_explanation():
    msg = task_publish_render.render_publish_message(
        {"title": "Draft Unit 1", "stage": "curriculum"},
        {
            "task_id": "T-1",
            "reason": "user_explanation_revision_in_progress",
            "delivery_lane": "manager_problem",
        },
    )
    assert "正在根据当前问题处理并推进修订" in msg


def test_render_direction_pending_user_explanation():
    msg = task_publish_render.render_publish_message(
        {"title": "School Contact", "stage": "school"},
        {
            "task_id": "T-3",
            "reason": "user_explanation_direction_pending",
            "delivery_lane": "manager_problem",
        },
    )
    assert "正在等待方向确认后再继续推进" in msg


def test_render_message_falls_back_cleanly_for_legacy_reason():
    msg = task_publish_render.render_publish_message(
        {"title": "Legacy Task", "stage": "curriculum", "verdict": "approved", "review_reason": "legacy_phrase"},
        _decision(),
    )
    assert "课程研发已审核通过并交付" in msg


def test_render_publish_summary_for_multiple_items():
    msg = task_publish_render.render_publish_summary([
        {"stage": "curriculum", "row": {"publish": True}},
        {"stage": "builder", "row": {"publish": True}},
        {"stage": "qbank", "row": {"publish": True}},
    ])
    assert "本轮有 3 项新交付" in msg
    assert "课程研发" in msg
    assert "系统建设" in msg


def test_render_publish_summary_ignores_internal_rows():
    msg = task_publish_render.render_publish_summary([
        {"stage": "curriculum", "row": {"publish": False}},
        {"stage": "builder", "row": {"publish": True}},
    ])
    assert "本轮有 1 项新交付" in msg
    assert "系统建设" in msg
    assert "课程研发" not in msg


def test_render_publish_summary_for_empty_items():
    msg = task_publish_render.render_publish_summary([])
    assert "暂无可对老板播报" in msg


def test_compose_publish_aggregate_prioritizes_results_in_headline():
    aggregate = task_publish_render.compose_publish_aggregate([
        {
            "stage": "curriculum",
            "manager_response_type": "final_result_delivered",
            "message": "课程研发已完成并交付：A（T-1）",
            "row": {"publish": True},
        },
        {
            "stage": "school",
            "manager_response_type": "manager_problem_direction_pending",
            "message": "学校事务正在等待方向确认后再继续推进：B（T-2）",
            "row": {"publish": True},
        },
        {
            "stage": "builder",
            "manager_response_type": "worker_reassurance",
            "message": "系统建设任务已开始处理：C（T-3）",
            "row": {"publish": True},
        },
    ])
    assert "已完成 1 项正式交付" in aggregate["headline"]
    assert len(aggregate["results"]) == 1
    assert len(aggregate["problems"]) == 1
    assert len(aggregate["reassurances"]) == 1


def test_compose_publish_aggregate_uses_problem_headline_when_no_results():
    aggregate = task_publish_render.compose_publish_aggregate([
        {
            "stage": "curriculum",
            "manager_response_type": "manager_problem_scope_pending",
            "message": "课程研发正在确认范围后再继续推进：A（T-1）",
            "row": {"publish": True},
        },
        {
            "stage": "school",
            "manager_response_type": "worker_reassurance",
            "message": "学校事务任务已开始处理：B（T-2）",
            "row": {"publish": True},
        },
    ])
    assert "待 manager 继续处理" in aggregate["headline"]
    assert len(aggregate["results"]) == 0
    assert len(aggregate["problems"]) == 1
    assert len(aggregate["reassurances"]) == 1


def test_describe_surface_state_returns_stable_label():
    assert task_publish_render.describe_surface_state("accepted_current_subject") == "已接到当前学科任务"
    assert task_publish_render.describe_surface_state("legacy_phrase") == "legacy_phrase"
    assert task_publish_render.describe_surface_state("") == "未识别状态面"


# ── Package 8: visible truth snapshot & source audit ─────────────────


def test_visible_truth_snapshot_includes_task_id_and_sources():
    """render_visible_truth_snapshot returns a dict with task_id and
    evidence-derived fields — no hand-written subject lists."""
    snapshot = task_publish_render.render_visible_truth_snapshot({
        "id": "T-SNAP-1",
        "subject_id": "igcse-physics-0625",
        "subject_name": "IGCSE Physics 0625",
        "closeout_status": "closeout_completed",
        "qbank_report_path": "content/igcse-physics-0625/qbank/report.json",
        "qbank_status": "verified",
        "verdict": "approved",
        "verdict_target": "Unit 1 Outline",
    })
    assert snapshot["task_id"] == "T-SNAP-1"
    assert snapshot["subject_inventory_summary"] != "source_missing"
    assert "igcse-physics-0625" in snapshot["subject_inventory_summary"]
    assert snapshot["qbank_report_path"] == "content/igcse-physics-0625/qbank/report.json"
    assert snapshot["qbank_status"] == "verified"
    assert snapshot["verifier_summary"] is not None
    assert "approved" in (snapshot["verifier_summary"] or "")
    assert isinstance(snapshot["generated_at_ms"], int)
    assert snapshot["generated_at_ms"] > 0


def test_visible_truth_snapshot_no_handwritten_lists():
    """The snapshot must NOT contain hardcoded four-subject lists or
    stale status strings. Every field comes from task evidence."""
    snapshot = task_publish_render.render_visible_truth_snapshot({
        "id": "T-SNAP-2",
        # Minimal task — no subject_id, no qbank, no verifier
    })
    # Must not contain any hand-written subject names
    body = str(snapshot)
    for hardcoded in ("IGCSE", "Physics", "0625", "四个学科"):
        assert hardcoded not in body, \
            f"Snapshot must not contain hand-written '{hardcoded}'"

    # Missing sources are explicitly marked, not invented
    assert snapshot["subject_inventory_summary"] == "source_missing"
    assert snapshot["qbank_report_path"] is None or snapshot["qbank_report_path"] == "source_missing"
    assert snapshot["verifier_summary"] is None


def test_visible_truth_snapshot_generated_at_is_monotonic():
    """The generated_at_ms timestamp should be set at call time."""
    import time
    before = int(time.time() * 1000)
    snapshot = task_publish_render.render_visible_truth_snapshot({
        "id": "T-SNAP-3",
        "subject_id": "igcse-math-0580",
        "subject_name": "IGCSE Mathematics 0580",
    })
    after = int(time.time() * 1000)
    assert before <= snapshot["generated_at_ms"] <= after


def test_visible_sources_includes_all_available_sources():
    """compose_visible_sources returns a dict listing present and missing
    sources for a task with all evidence available."""
    sources = task_publish_render.compose_visible_sources({
        "id": "T-SRC-1",
        "subject_id": "igcse-bio-0610",
        "qbank_report_path": "content/igcse-bio-0610/reports/qbank.json",
        "verifier_result": {"report_path": "content/igcse-bio-0610/reports/verifier.json"},
        "verdict": "approved",
    })
    assert sources["task_id"] == "T-SRC-1"
    assert "subject_inventory" in sources["sources_present"]
    assert "qbank_report" in sources["sources_present"]
    assert "verifier" in sources["sources_present"]
    assert "subject_inventory(igcse-bio-0610)" in sources["subject_inventory_source"]
    assert "content/igcse-bio-0610/reports/qbank.json" == sources["qbank_report_path"]
    assert sources["verifier_report_path"] is not None


def test_visible_sources_shows_warning_for_missing_source():
    """When evidence is absent, compose_visible_sources marks it as
    missing rather than pretending the source exists."""
    sources = task_publish_render.compose_visible_sources({
        "id": "T-SRC-2",
        # No subject_id, no qbank, no verifier — bare task
    })
    assert sources["task_id"] == "T-SRC-2"
    assert sources["subject_inventory_source"] == "source_missing"
    assert sources["qbank_report_path"] is None
    assert sources["verifier_report_path"] is None
    assert "subject_inventory" in sources["sources_missing"]
    assert "qbank_report" in sources["sources_missing"]
    assert "verifier" in sources["sources_missing"]
    assert "task_id" in sources["sources_present"]


def test_visible_truth_snapshot_includes_loop_summary_when_present():
    snapshot = task_publish_render.render_visible_truth_snapshot({
        "id": "T-SNAP-LOOP",
        "loop_run_id": "L-000001",
        "loop_status": "repair_needed",
        "loop_cycle_count": 2,
        "loop_evidence_ref": "loop_runs/L-000001/meta.json",
    })
    assert snapshot["loop_summary"]["run_id"] == "L-000001"
    assert snapshot["loop_summary"]["status"] == "repair_needed"
    assert snapshot["loop_summary"]["cycle_count"] == 2


def test_visible_sources_marks_loop_evidence_present():
    sources = task_publish_render.compose_visible_sources({
        "id": "T-SRC-LOOP",
        "loop_evidence_ref": "loop_runs/L-000001/meta.json",
    })
    assert "loop_evidence" in sources["sources_present"]
    assert sources["loop_evidence_ref"] == "loop_runs/L-000001/meta.json"
