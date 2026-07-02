"""Tests for task event scanner cursoring and decision derivation."""
from __future__ import annotations

import json

from helpers import attr_patch, isolated_env
from eduflow.runtime import paths
from eduflow.store import local_facts, task_event_scanner, task_publish_gate, tasks


def _healthy_watchdog_rows():
    return [
        {"name": "router", "pid_present": True, "alive": True},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": True, "alive": True},
        {"name": "hermes-supervisor", "pid_present": True, "alive": True},
    ]


def test_scan_returns_only_publishable_events_by_default():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        rows = task_event_scanner.scan_publish_decisions()
        reasons = [row["reason"] for row in rows]
        assert "worker_accepted" in reasons
        assert "worker_started" in reasons
        assert "delivered_to_user" in reasons


def test_scan_manager_anomalies_flags_high_priority_unread_and_read_without_ack():
    with isolated_env():
        unread = local_facts.append_message(
            "manager", "auto_ops", "Physics 0625 needs formal decision", priority="高"
        )
        read_no_ack = local_facts.append_message(
            "worker_course", "review_course", "minor revision for Accounting 7.5", priority="高"
        )
        assert local_facts.mark_read(read_no_ack) is True

        findings = task_event_scanner.scan_manager_anomalies()
        by_message = {row.get("message_id"): row for row in findings}
        assert by_message[unread]["category"] == "high_priority_inbox_unread_blocking"
        assert by_message[unread]["recommended_action"] == "consume_high_priority_inbox"
        assert by_message[read_no_ack]["category"] == "high_priority_inbox_read_without_ack"
        assert by_message[read_no_ack]["recommended_action"] == "request_explicit_agent_ack"

        assert local_facts.record_message_ack(read_no_ack, "accepted_revision", topic="Accounting 7.5")
        findings = task_event_scanner.scan_manager_anomalies()
        ids = {row.get("message_id") for row in findings}
        assert read_no_ack not in ids
        assert unread in ids


def test_scan_manager_anomalies_flags_context_exhausted_worker():
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "IGCSE Physics 0625 Batch 8 production")
        local_facts.append_log(
            "worker_course",
            "say",
            "context window exceeds limit while generating IGCSE Physics 0625 Batch 8 topic 8.2",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row.get("category") == "worker_context_exhausted"
            and row.get("agent") == "worker_course"
        ]

        assert len(flagged) == 1
        assert flagged[0]["live_blocker"] is True
        assert flagged[0]["allow_continue_original_task"] is False
        assert flagged[0]["recommended_action"] == "restart_worker_runtime"
        assert "context window exceeds limit" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_warns_before_context_exhaustion():
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "IGCSE Physics 0625 Batch 8 production")
        local_facts.append_log(
            "worker_course",
            "say",
            "continuing production; context: 86.5% (227k/262k)",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "review standby; context: 91% (238k/262k)",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        by_category = {row.get("category"): row for row in findings}

        usage_warning = by_category["worker_context_usage_warning"]
        assert usage_warning["agent"] == "worker_course"
        assert usage_warning["allow_continue_original_task"] is True
        assert usage_warning["recommended_action"] == "monitor_context_and_split_next_packet"
        assert "context_usage=86.5%" in usage_warning["evidence_summary"]

        compact = by_category["worker_context_compact_recommended"]
        assert compact["agent"] == "review_course"
        assert compact["allow_continue_original_task"] is False
        assert compact["recommended_action"] == "run_eduflow_compact_before_long_work"
        assert "context_usage=91%" in compact["evidence_summary"]


def test_scan_manager_anomalies_flags_high_priority_unacked_worker_producing():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "P0: pause expansion and read inbox before producing more Physics 0625.",
            priority="高",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "continuing production: Physics 0625 Batch 8 topic 8.3 generated",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row.get("category") == "worker_high_priority_unacked_while_producing"
        ]

        assert len(flagged) == 1
        assert flagged[0]["message_id"] == msg_id
        assert flagged[0]["agent"] == "worker_course"
        assert flagged[0]["allow_continue_original_task"] is False
        assert flagged[0]["recommended_action"] == "interrupt_old_context_and_read_inbox"


def test_scan_manager_anomalies_flags_status_pane_truth_conflict():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "受阻",
            "Physics 0625 Batch 8 blocked",
            blocker="waiting manager repair instruction",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "继续生产 Physics 0625 Batch 8 topic 8.4 QA items",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row.get("category") == "status_pane_truth_conflict"
            and row.get("agent") == "worker_course"
        ]

        assert len(flagged) == 1
        assert flagged[0]["recommended_action"] == "reassign_small_batch"
        assert flagged[0]["allow_continue_original_task"] is False
        assert "status=受阻" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_marks_no_inject_high_priority_as_requires_polling():
    with isolated_env():
        msg_id = local_facts.append_message(
            "manager",
            "codex",
            "测试高优消息",
            priority="高",
            delivery_state="requires_polling",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row.get("message_id") == msg_id]
        assert len(flagged) == 1
        assert flagged[0]["category"] == "high_priority_inbox_requires_polling"
        assert flagged[0]["recommended_action"] == "poll_or_consume_high_priority_inbox"


def test_scan_manager_anomalies_downgrades_unread_with_later_visibility_to_read_state_desync():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "[T-14 / igcse-subject-launch] 请立即执行 IGCSE Physics 0625 Batch 5。",
            priority="high",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发任务已开始处理：IGCSE Physics 0625 Batch 5 topic-outline + QA seed（T-14）",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row.get("message_id") == msg_id]
        assert len(flagged) == 1
        assert flagged[0]["category"] == "high_priority_inbox_unread_desynced"
        assert flagged[0]["status"] == "read_state_desync"
        assert flagged[0]["recommended_action"] == "reconcile_inbox_state"


def test_scan_manager_anomalies_suppresses_read_without_ack_after_stage_ack_log():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "紧急修 worker_course runtime blocker",
            priority="高",
        )
        assert local_facts.mark_read(msg_id) is True
        local_facts.record_worker_stage_ack(
            "worker_builder",
            msg_id,
            "紧急修 worker_course runtime blocker",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            item for item in findings
            if item.get("message_id") == msg_id
            and item["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_suppresses_old_read_without_ack_backlog():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "Old high-priority task that was read long ago",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        row = local_facts.get_message(msg_id)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=int(row["created_at"]) + task_event_scanner.HIGH_PRIORITY_READ_WITHOUT_ACK_WINDOW_MS + 1
        )
        assert not [
            item for item in findings
            if item.get("message_id") == msg_id
            and item["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_treats_english_high_as_high_priority():
    with isolated_env():
        unread = local_facts.append_message(
            "worker_qbank",
            "codex",
            "please acknowledge qbank readiness work",
            priority="high",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        by_message = {row.get("message_id"): row for row in findings}
        assert by_message[unread]["category"] == "high_priority_inbox_unread_blocking"
        assert by_message[unread]["recommended_action"] == "consume_high_priority_inbox"


def test_scan_manager_anomalies_reports_unread_as_runtime_guard_blocked():
    with isolated_env():
        msg_id = local_facts.append_message(
            "anna",
            "manager",
            "请做 QBank 导入就绪检查，只读输出 readiness 报告。",
            priority="高",
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json

        paths.runtime_guard_state_file().parent.mkdir(parents=True, exist_ok=True)
        write_json(paths.runtime_guard_state_file(), {
            "agents": {
                "anna": {
                    "last_failure_reason": "provider_unavailable",
                    "last_switch_outcome": "switch_failed",
                    "needs_manager_action": True,
                    "escalation_needed": True,
                    "escalation_reason": "fallback_restart_failed",
                }
            }
        })

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row.get("message_id") == msg_id]

        assert len(flagged) == 1
        assert flagged[0]["category"] == "high_priority_inbox_runtime_guard_blocked"
        assert flagged[0]["severity"] == "warn"
        assert flagged[0]["recommended_action"] == "repair_or_rehire_agent_runtime"
        assert "provider_unavailable" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_collapses_redundant_unread_blockers_per_agent():
    with isolated_env():
        old = local_facts.append_message(
            "worker_builder",
            "manager",
            "修复 runtime blocker 第一版指令",
            priority="高",
        )
        new = local_facts.append_message(
            "worker_builder",
            "manager",
            "修复 runtime blocker 最新指令",
            priority="高",
        )
        read_no_ack = local_facts.append_message(
            "worker_builder",
            "manager",
            "已读但尚未 ACK 的独立修复任务",
            priority="高",
        )
        assert local_facts.mark_read(read_no_ack)

        findings = task_event_scanner.scan_manager_anomalies()
        by_message = {row.get("message_id"): row for row in findings}
        assert old not in by_message
        assert by_message[new]["category"] == "high_priority_inbox_unread_blocking"
        assert by_message[read_no_ack]["category"] == "high_priority_inbox_read_without_ack"


def test_scan_manager_anomalies_surfaces_runtime_visibility_unhealthy():
    rows = [
        {"name": "router", "pid_present": True, "alive": False},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": False, "alive": False},
        {"name": "hermes-supervisor", "pid_present": False, "alive": False},
    ]
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=lambda: rows):
        findings = task_event_scanner.scan_manager_anomalies()

    flagged = [
        item for item in findings
        if item["category"] == "runtime_visibility_unhealthy"
    ]
    assert len(flagged) == 1
    assert flagged[0]["severity"] == "warn"
    assert flagged[0]["live_blocker"] is True
    assert flagged[0]["recommended_action"] == "trigger_or_dispatch_runtime_repair"
    assert "router_pid_stale" in flagged[0]["evidence_summary"]
    assert "watchdog_down" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_does_not_surface_runtime_visibility_when_healthy():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        findings = task_event_scanner.scan_manager_anomalies()

    assert not [
        item for item in findings
        if item["category"] == "runtime_visibility_unhealthy"
    ]


def test_scan_manager_anomalies_suppresses_watchdog_repair_unread_after_recovery():
    rows = [
        {"name": "router", "pid_present": True, "alive": True},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": True, "alive": True},
        {"name": "hermes-supervisor", "pid_present": True, "alive": False},
    ]
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=lambda: rows):
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "watchdog 持续缺失，请排查并恢复 watchdog/router 兜底保障。",
            priority="高",
        )

        findings = task_event_scanner.scan_manager_anomalies()

    assert not [
        item for item in findings
        if item.get("message_id") == msg_id
        and item["category"] == "high_priority_inbox_unread_blocking"
    ]
    assert [
        item for item in findings
        if item["category"] == "runtime_visibility_unhealthy"
        and "hermes_supervisor_down" in item["evidence_summary"]
    ]


def test_scan_manager_anomalies_suppresses_watchdog_repair_read_without_ack_after_recovery():
    rows = [
        {"name": "router", "pid_present": True, "alive": True},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": True, "alive": True},
        {"name": "hermes-supervisor", "pid_present": True, "alive": True},
    ]
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=lambda: rows):
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "watchdog 未启动(no pid file)，请排查并恢复 router/watchdog 兜底保障。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)

        findings = task_event_scanner.scan_manager_anomalies()

    assert not [
        item for item in findings
        if item.get("message_id") == msg_id
        and item["category"] == "high_priority_inbox_read_without_ack"
    ]


def test_scan_manager_anomalies_suppresses_watchdog_repair_read_after_later_closeout_even_if_router_flaps():
    rows = [
        {"name": "router", "pid_present": True, "alive": False},
        {"name": "task-publish", "pid_present": True, "alive": True},
        {"name": "watchdog", "pid_present": True, "alive": True},
        {"name": "hermes-supervisor", "pid_present": True, "alive": True},
    ]
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=lambda: rows):
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "watchdog 持续缺失，请排查并恢复 router/watchdog 兜底保障。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "auto_ops",
            "task_completed",
            "watchdog 修复闭环: 核实 watchdog 已恢复(PID 16501) → health 全绿 → 完工报告",
        )

        findings = task_event_scanner.scan_manager_anomalies()

    assert not [
        item for item in findings
        if item.get("message_id") == msg_id
        and item["category"] == "high_priority_inbox_read_without_ack"
    ]


def test_scan_manager_anomalies_suppresses_old_builder_runtime_course_read_after_closeout():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "codex 监控纠偏：确认 stale T-13 消息已阻断，并验证 worker_course pane 实际可用。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "manager",
            "say",
            "✅ T-18 Physics 0625 FINAL closeout，worker_course 已恢复并完成后续批次。",
        )

        findings = task_event_scanner.scan_manager_anomalies()

    assert not [
        item for item in findings
        if item.get("message_id") == msg_id
        and item["category"] == "high_priority_inbox_read_without_ack"
    ]


def test_scan_manager_anomalies_marks_unread_delegation_answered_by_manager_as_secondhand():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "老板问能否切换到备用模型绕过 Qoder API FORBIDDEN。请调查 worker_builder/worker_course/worker_qbank。",
            priority="高",
        )
        local_facts.append_log(
            "manager",
            "say",
            "已核实全部 Qoder worker：worker_builder / worker_course / worker_qbank 都是 provider-level Credits exhausted，CLI 侧无法切换模型。",
        )

        findings = task_event_scanner.scan_manager_anomalies()

    flagged = [
        item for item in findings
        if item.get("message_id") == msg_id
    ]
    assert len(flagged) == 1
    assert flagged[0]["category"] == "delegated_task_answered_by_manager_but_worker_unread"
    assert flagged[0]["severity"] == "info"
    assert flagged[0]["live_blocker"] is False
    assert flagged[0]["recommended_action"] == "clear_or_reassign_stale_delegation"


def test_scan_manager_anomalies_reports_provider_quota_even_when_course_task_active():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(task_event_scanner, now_ms=lambda: current_now):
            task_id = tasks.create_flow(
                title="IGCSE Physics Motion and Forces micro-outline",
                assignee="worker_course",
                stage="curriculum",
                owner="manager",
                status="in_progress",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 60_000):
            local_facts.upsert_status(
                "worker_course",
                "已交付",
                "课程研发已完成并交付：IGCSE Physics 0625 Batch 9 final topic-outline + QA seed（T-18）",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 2 * 60_000):
            local_facts.append_log(
                "manager",
                "say",
                "已核实全部 3 个 Qoder worker (worker_builder / worker_course / worker_qbank) "
                "都是 provider-level Credits exhausted / FORBIDDEN code=112，无法执行任何操作。",
            )

        findings = task_event_scanner.scan_manager_anomalies()

        flagged = [
            item for item in findings
        if item.get("task_id") == "facts:worker_course"
        and item.get("category") == "facts_process_visibility_stale"
    ]
    assert task_id
    assert len(flagged) == 1
    assert flagged[0]["status"] == "runtime_blocked_provider_quota"
    assert flagged[0]["live_blocker"] is True
    assert flagged[0]["recommended_action"] == "restore_provider_quota_or_reassign_runtime"


def test_scan_manager_anomalies_flags_manager_direct_content_and_verification_execution():
    with isolated_env():
        tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 subject closeout package",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            status="in_progress",
        )
        local_facts.append_log(
            "manager",
            "say",
            "我直接修复 Physics 0625 content 文件，并跑了 Python 验证确认 PASS。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        by_category = {row["category"]: row for row in findings}

        assert by_category["manager_direct_content_execution"]["live_blocker"] is True
        assert by_category["manager_direct_content_execution"]["recommended_action"] == (
            "dispatch_worker_course_for_content_repair"
        )
        assert by_category["manager_direct_content_execution"]["action_packet"]["assignee"] == "worker_course"
        assert by_category["manager_direct_verification_execution"]["live_blocker"] is True
        assert by_category["manager_direct_verification_execution"]["recommended_action"] == (
            "dispatch_review_course_for_verdict_or_worker_builder_for_tool_verification"
        )


def test_scan_manager_anomalies_flags_manager_claim_without_task_or_inbox_truth():
    with isolated_env():
        local_facts.append_log(
            "manager",
            "say",
            "已派 worker_course 启动 IGCSE Chemistry 0620 下一学科生产。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row["category"] == "manager_claim_without_task_truth"
        ]

        assert len(flagged) == 1
        assert flagged[0]["live_blocker"] is True
        assert flagged[0]["recommended_action"] == "create_task_backed_dispatch_to_worker_course"
        assert flagged[0]["action_packet"]["assignee"] == "worker_course"
        assert flagged[0]["action_packet"]["apply_allowed"] is False


def test_scan_manager_anomalies_flags_premature_next_subject_when_current_gate_open():
    with isolated_env():
        tasks.create_flow(
            "worker_course",
            "IGCSE Biology 0610 subject closeout package",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            status="in_progress",
        )
        local_facts.append_log(
            "manager",
            "say",
            "启动下一学科 IGCSE Chemistry 0620，已派 worker_course 进入生产。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row["category"] == "premature_next_subject"
        ]

        assert len(flagged) == 1
        assert flagged[0]["live_blocker"] is True
        assert flagged[0]["recommended_action"] == "finish_current_subject_closeout_gate_first"
        assert flagged[0]["action_packet"]["assignee"] == "manager"
        assert "current_subject_id=T-1" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_suppresses_non_production_role_runtime_drift():
    with isolated_env():
        local_facts.upsert_status(
            "Anna",
            "进行中",
            "Anna 正在处理旧模板状态，但不是 worker_course/review_course/worker_builder/worker_qbank。",
        )
        local_facts.upsert_status(
            "Luke",
            "已接单",
            "Luke 旧任务状态残留。",
        )

        findings = task_event_scanner.scan_manager_anomalies()

        assert not [
            row for row in findings
            if row.get("category") == "facts_process_visibility_stale"
            and row.get("agent") in {"Anna", "Luke"}
        ]
        assert not [
            row for row in findings
            if row.get("category") == "inactive_role_runtime_drift"
        ]


def test_manager_boundary_finding_does_not_flag_normal_review_closeout_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 final subject closeout",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            status="submitted_for_review",
        )
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="reviewer",
            review_reason="approved_for_delivery",
            latest_turn_summary="full subject closeout ready",
        )

        findings = task_event_scanner.scan_manager_anomalies()

        assert not [
            row for row in findings
            if row["category"].startswith("manager_direct_")
            or row["category"] in {"manager_claim_without_task_truth", "premature_next_subject"}
        ]


def test_scan_manager_anomalies_suppresses_unread_after_later_related_worker_signal():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "[T-14 / igcse-subject-launch] 请立即执行 IGCSE Physics 0625 Batch 5。",
            priority="high",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发任务已开始处理：IGCSE Physics 0625 Batch 5 topic-outline + QA seed（T-14）",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发任务已完成并交给 manager：IGCSE Physics 0625 Batch 5 topic-outline + QA seed（T-14）",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_unread_blocking"
        ]


def test_scan_manager_anomalies_flags_conflicting_item_standard_briefs():
    with isolated_env():
        local_facts.append_message(
            "worker_course",
            "manager",
            "T-10 Business Studies 0450：请改为 9-item standard，对齐 Economics。",
            priority="高",
        )
        local_facts.append_message(
            "worker_course",
            "codex",
            "T-10 Business Studies 0450：不要改 9-item，当前标准是 12-item standard。",
            priority="high",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["category"] == "conflicting_task_brief_detected"]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == "brief:T-10"
        assert flagged[0]["recommended_action"] == "clarify_current_task_standard"
        assert "nine_item_messages" in flagged[0]["evidence_summary"]
        assert "twelve_item_messages" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_suppresses_conflicting_brief_after_later_pass():
    with isolated_env():
        local_facts.append_message(
            "worker_course",
            "manager",
            "T-10 Business Studies 0450：请改为 9-item standard，对齐 Economics。",
            priority="高",
        )
        local_facts.append_message(
            "review_course",
            "codex",
            "T-10 当前真相：Business Studies 0450 保持 12-item standard，F:3|S:5|C:4。",
            priority="high",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-10 Business Studies 0450 复检结果：Verdict: PASS — 可发布。25 topics × 12 QA = 300。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["category"] == "conflicting_task_brief_detected"]
        assert flagged == []


def test_scan_manager_anomalies_suppresses_read_without_ack_after_direct_visibility():
    with isolated_env():
        msg_id = local_facts.append_message(
            "review_course",
            "manager",
            "请复核 Business Studies 0450 T-10",
            priority="高",
        )
        assert local_facts.mark_read(msg_id) is True
        local_facts.append_log(
            "review_course",
            "say",
            "Business Studies 0450 复核结果：MINOR 修改，难度分布需统一。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]
        assert flagged == []


def test_scan_manager_anomalies_suppresses_qbank_v3_read_without_ack_after_related_visibility():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_qbank",
            "manager",
            "QBank 去重 v3 方案已通过 MINOR 复核。请修正 12 个 keep/renumber 方向反转问题。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "worker_qbank",
            "say",
            "v3.1 方向修正完成: canonical items keep, round2 renumber, JSON 全部 id_collision 已校准。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_suppresses_manager_read_worker_visible_report():
    with isolated_env():
        msg_id = local_facts.append_message(
            "manager",
            "worker_qbank",
            "v3.1方向修正完工. 12个A4/A5条目方向已反转, JSON全部33个id_collision校准.",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "worker_qbank",
            "say",
            "v3.1 方向修正完成: 12 个 A4/A5 条目已修正，JSON 全部 id_collision 已校准。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_treats_manager_status_as_progress_for_worker_report():
    with isolated_env():
        msg_id = local_facts.append_message(
            "manager",
            "worker_builder",
            "排查完成，已提交修复。router PID 文件 gap 已定位，等待验收。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.upsert_status(
            "manager",
            "进行中",
            "等待 worker_builder router 修复验收",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        read_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]
        started_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_started_without_explicit_ack"
        ]
        assert read_without_ack == []
        assert len(started_without_ack) == 1
        assert started_without_ack[0]["agent"] == "manager"
        assert started_without_ack[0]["severity"] == "info"
        assert started_without_ack[0]["status"] == "ack_semantics_gap"


def test_scan_manager_anomalies_suppresses_manager_read_when_sender_status_proves_report():
    with isolated_env():
        msg_id = local_facts.append_message(
            "manager",
            "worker_builder",
            "router PID 文件 gap 修复完成，等待 manager review。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.upsert_status(
            "worker_builder",
            "空闲",
            "router PID 文件 gap 修复已提交 (cb71224) — 待 manager review",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_started_without_explicit_ack"
        ]


def test_scan_manager_anomalies_distinguishes_started_status_from_missing_ack():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "正式恢复课程主线 T-7 Accounting 0452。请从 backlog 继续生产 Batch 3。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "T-7 Accounting 0452 Batch 3 生产",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        read_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]
        started_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_started_without_explicit_ack"
        ]
        assert read_without_ack == []
        assert len(started_without_ack) == 1
        assert started_without_ack[0]["recommended_action"] == "record_or_request_explicit_ack"
        assert started_without_ack[0]["agent"] == "worker_course"
        assert started_without_ack[0]["severity"] == "info"
        assert started_without_ack[0]["status"] == "ack_semantics_gap"


def test_scan_manager_anomalies_treats_later_agent_completion_as_ack_semantics_gap():
    with isolated_env():
        msg_id = local_facts.append_message(
            "auto_ops",
            "manager",
            "纠正任务：runtime/fallback 异常下修正状态板、完成 QBank readiness 检查、确认 review_course ACK。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "auto_ops",
            "say",
            "纠正任务完工：状态板已修正，QBank readiness 检查完成，review_course ACK 确认无遗漏。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        read_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]
        started_without_ack = [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_started_without_explicit_ack"
        ]

        assert read_without_ack == []
        assert len(started_without_ack) == 1
        assert started_without_ack[0]["agent"] == "auto_ops"
        assert started_without_ack[0]["severity"] == "info"
        assert started_without_ack[0]["status"] == "ack_semantics_gap"


def test_scan_manager_anomalies_suppresses_old_started_without_ack_after_closeout_projection():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "T-7 Batch 3 二次复核 FAIL，需要你修复 QA+items 全面同步 F:3|S:3|C:3。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "T-7 Batch 3 二次返修: QA+items 全面同步 F:3|S:3|C:3",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-7 Accounting 0452 Batch 3 三次复检结果：Verdict: PASS — 可发布。",
        )
        local_facts.append_log(
            "manager",
            "say",
            "T-7 Accounting 0452 Batch 3 三次复检正式 PASS closeout。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_started_without_explicit_ack"
        ]


def test_scan_manager_anomalies_suppresses_course_read_unacked_after_later_review_pass():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "T-8 Physics 0625 Batch 1 需修复 qa-manifest.csv 与实际同步。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "review_course",
            "say",
            "T-8 Physics 0625 Batch 1 manifest 修复确认：PASS。可 closeout。",
        )
        local_facts.append_log(
            "manager",
            "say",
            "T-8 Physics 0625 Batch 1 正式闭环 — review_course 复检 PASS。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_suppresses_builder_runtime_message_after_related_completion():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "watchdog 需重启，且 worker_builder/worker_course/worker_qbank CLI 未就绪。请修复 PATH 配置。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "worker_builder",
            "say",
            "排查完成：watchdog PID 正常运行；PATH 问题已修复；worker respawn 方案已写入 worker-respawn-plan.md。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_suppresses_builder_runtime_message_after_task_log_completion():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_builder",
            "manager",
            "请准备 worker respawn 方案，待 worker_course 当前批次完工后执行。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log(
            "worker_builder",
            "task",
            "respawn 方案已写入 worker-respawn-plan.md，待 manager 下令执行。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row.get("message_id") == msg_id
            and row["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_requires_worker_revision_ack_after_review_reject():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
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
            latest_turn_summary="Minor revision required for Q-3.2-08.",
            scope_topic="Accounting 3.2",
        )
        msg_id = local_facts.append_message(
            "worker_course",
            "review_course",
            "Please revise Accounting 3.2 Q-3.2-08",
            priority="高",
            task_id=tid,
        )
        local_facts.mark_read(msg_id)

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["category"] == "revision_ack_missing"]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == tid
        assert flagged[0]["recommended_action"] == "request_worker_revision_ack"
        assert "accepted_revision" in flagged[0]["evidence_summary"]

        local_facts.record_message_ack(msg_id, "accepted_revision", topic="Accounting 3.2")
        findings = task_event_scanner.scan_manager_anomalies()
        assert not [row for row in findings if row["category"] == "revision_ack_missing"]


def test_scan_manager_anomalies_flags_ack_without_followthrough_signal():
    with isolated_env():
        msg_id = local_facts.append_message(
            "review_course",
            "manager",
            "请 review Physics 0625 Batch 1 revised submission",
            priority="高",
        )
        assert local_facts.mark_read(msg_id) is True
        assert local_facts.record_message_ack(
            msg_id,
            "accepted_task",
            topic="Physics 0625 Batch 1",
        ) is True

        row = local_facts.get_message(msg_id)
        assert row is not None
        ack_at = int(row["ack_at"])
        findings = task_event_scanner.scan_manager_anomalies(now=ack_at + 2 * 60 * 1000 + 1)
        flagged = [item for item in findings if item["category"] == "ack_without_followthrough_signal"]
        assert len(flagged) == 1
        assert flagged[0]["message_id"] == msg_id
        assert flagged[0]["recommended_action"] == "request_process_visibility_signal"

        local_facts.append_log("review_course", "say", "收到 revised submission，开始复核关键修复项")
        findings = task_event_scanner.scan_manager_anomalies(now=ack_at + 2 * 60 * 1000 + 2)
        assert not [item for item in findings if item["category"] == "ack_without_followthrough_signal"]


def test_scan_manager_anomalies_suppresses_stale_superseded_ack_followthrough():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "T-13 Batch 4 续做，但后续已被 T-14 取代",
            priority="高",
        )
        assert local_facts.mark_read(msg_id) is True
        assert local_facts.record_message_ack(
            msg_id,
            "stale_superseded_by_T14",
            topic="T-13 Batch 4",
        ) is True

        row = local_facts.get_message(msg_id)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=int(row["ack_at"]) + 2 * 60 * 1000 + 1
        )
        assert not [
            item for item in findings
            if item.get("message_id") == msg_id
            and item["category"] == "ack_without_followthrough_signal"
        ]


def test_scan_manager_anomalies_flags_secondhand_worker_visibility():
    with isolated_env():
        manager_log = local_facts.append_log(
            "manager",
            "say",
            "worker_course 正在工作中：已运行 33 分钟，正在生产 Physics 0625 Batch 2+ QA 文件。",
        )
        row = local_facts.list_logs("manager")[-1]
        created_at = int(row["created_at"])

        findings = task_event_scanner.scan_manager_anomalies(
            now=created_at + task_event_scanner.SECONDHAND_VISIBILITY_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["category"] == "secondhand_worker_visibility"]
        assert len(flagged) == 1
        assert flagged[0]["message_id"] == manager_log
        assert flagged[0]["task_id"] == "visibility:worker_course"
        assert flagged[0]["recommended_action"] == "request_agent_direct_process_signal"

        local_facts.append_log("worker_course", "say", "开始生产 Physics 0625 Batch 2+，当前在生成 wave/optics 系列 QA。")
        findings = task_event_scanner.scan_manager_anomalies(
            now=created_at + task_event_scanner.SECONDHAND_VISIBILITY_THRESHOLD_MS + 2
        )
        assert not [item for item in findings if item["category"] == "secondhand_worker_visibility"]


def test_scan_manager_anomalies_suppresses_secondhand_visibility_when_specific_inbox_blocker_exists():
    with isolated_env():
        local_facts.append_message(
            "worker_builder",
            "manager",
            "watchdog 持续缺失，请排查并重启 watchdog。",
            priority="高",
        )
        manager_log = local_facts.append_log(
            "manager",
            "say",
            "已派 worker_builder 紧急排查修复 watchdog。",
        )
        row = local_facts.list_logs("manager")[-1]
        findings = task_event_scanner.scan_manager_anomalies(
            now=int(row["created_at"]) + task_event_scanner.SECONDHAND_VISIBILITY_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["category"] == "secondhand_worker_visibility"
            and item.get("message_id") == manager_log
        ]
        assert [
            item for item in findings
            if item["category"] == "high_priority_inbox_unread_blocking"
            and item.get("agent") == "worker_builder"
        ]


def test_scan_manager_anomalies_suppresses_secondhand_visibility_after_visible_terminal_signal():
    with isolated_env():
        manager_log = local_facts.append_log(
            "manager",
            "say",
            "T-15 Physics Batch 6 已完成生产，review_course 正在复核中。",
        )
        row = local_facts.list_logs("manager")[-1]
        created_at = int(row["created_at"])
        local_facts.append_log(
            "review_course",
            "say",
            "T-15 Physics 0625 Batch 6 复核完成 — VERDICT: PASS。",
        )

        findings = task_event_scanner.scan_manager_anomalies(
            now=created_at + task_event_scanner.SECONDHAND_VISIBILITY_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["category"] == "secondhand_worker_visibility"
            and item.get("message_id") == manager_log
        ]


def test_scan_manager_anomalies_flags_manager_acceptance_claim_conflicting_with_unread_agent_inbox():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_course",
            "manager",
            "[T-15 / igcse-subject-launch] 请执行 IGCSE Physics 0625 Batch 6。",
            priority="high",
        )
        manager_log = local_facts.append_log(
            "manager",
            "say",
            "worker_course：T-15 Physics 0625 Batch 6 已接单，但 Qoder FORBIDDEN 暂无法执行。",
        )
        row = local_facts.list_logs("manager")[-1]
        created_at = int(row["created_at"])

        findings = task_event_scanner.scan_manager_anomalies(now=created_at + 1)
        flagged = [
            item for item in findings
            if item["category"] == "secondhand_acceptance_conflict"
            and item.get("message_id") == msg_id
        ]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == msg_id
        assert flagged[0]["severity"] == "warn"
        assert flagged[0]["recommended_action"] == "request_agent_explicit_ack_or_runtime_blocker"
        assert manager_log in flagged[0]["evidence_summary"]

        assert local_facts.mark_read(msg_id)
        assert local_facts.record_message_ack(msg_id, "failed_due_to_runtime", reason="Qoder FORBIDDEN")
        findings = task_event_scanner.scan_manager_anomalies(now=created_at + 2)
        assert not [
            item for item in findings
            if item["category"] == "secondhand_acceptance_conflict"
            and item.get("message_id") == msg_id
        ]


def test_scan_manager_anomalies_does_not_cross_match_multiline_manager_status_packet():
    with isolated_env():
        msg_id = local_facts.append_message(
            "review_course",
            "manager",
            "[T-15 / Physics 0625 Batch 6] 请做文件级复核。",
            priority="high",
        )
        local_facts.append_log(
            "manager",
            "say",
            "当前可生产的员工：\n- review_course：待命，可执行复核任务\n\n"
            "被 Qoder API FORBIDDEN 卡住的员工：\n"
            "- worker_course：T-15 Physics 0625 Batch 6 已接单，无法执行",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            item for item in findings
            if item["category"] == "secondhand_acceptance_conflict"
            and item.get("message_id") == msg_id
        ]


def test_scan_manager_anomalies_suppresses_stale_review_handoff_after_verdict():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        msg_id = local_facts.append_message(
            "review_course",
            "worker_course",
            "Review handoff for Accounting 3.2",
            priority="高",
            task_id=tid,
        )
        tasks.review_flow(
            tid,
            outcome="approve",
            actor="review_course",
            review_reason="approved_for_delivery",
            latest_turn_summary="Review verdict exists for Accounting 3.2.",
            scope_topic="Accounting 3.2",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        row = [item for item in findings if item.get("message_id") == msg_id]
        assert len(row) == 1
        assert row[0]["category"] == "stale_review_handoff_reconciled"
        assert row[0]["recommended_action"] == "suppress_stale_review_handoff"


def test_scan_manager_anomalies_suppresses_review_handoff_without_task_id_after_visible_pass():
    with isolated_env():
        msg_id = local_facts.append_message(
            "review_course",
            "manager",
            "T-16 Physics 0625 Batch 7 复检：worker_course 报告已完成 topic-outline + QA seed。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        msg = local_facts.get_message(msg_id)
        assert msg is not None
        with attr_patch(local_facts, now_ms=lambda: int(msg["created_at"]) + 1000):
            local_facts.append_log(
                "review_course",
                "say",
                "T-16 Physics 0625 Batch 7 复核完成 — VERDICT: PASS。",
            )

        findings = task_event_scanner.scan_manager_anomalies()
        rows = [item for item in findings if item.get("message_id") == msg_id]
        assert rows == []
        assert not [
            item for item in findings
            if item.get("message_id") == msg_id
            and item["category"] == "high_priority_inbox_read_without_ack"
        ]


def test_scan_manager_anomalies_flags_review_scope_mismatch():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
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
            scope_topic="Physics 0625",
            verdict_target="Physics 0625",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["category"] == "review_scope_mismatch"]
        assert len(flagged) == 1
        assert flagged[0]["recommended_action"] == "request_narrow_review_recheck"
        assert "Physics 0625" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_surfaces_subject_closeout_blocked_and_ready():
    with isolated_env():
        blocked = _approved_subject_task(evidence={})
        ready = _approved_subject_task(
            title="IGCSE Business Studies 0450",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        findings = task_event_scanner.scan_manager_anomalies()
        by_task = {(row["task_id"], row["category"]): row for row in findings}
        assert by_task[(blocked, "subject_closeout_blocked")]["recommended_action"] == "request_review_evidence_packet"
        assert "closeout_blocked_missing_evidence" in by_task[(blocked, "subject_closeout_blocked")]["evidence_summary"]
        blocked_packet = by_task[(blocked, "subject_closeout_blocked")]["action_packet"]
        assert blocked_packet["apply_allowed"] is True
        assert blocked_packet["closeout_gate"]["review_approved"] is True
        assert blocked_packet["closeout_gate"]["evidence_present"] is False
        assert blocked_packet["closeout_gate"]["qa_standard_met"] is False
        assert blocked_packet["closeout_gate"]["qbank_ready"] is False
        assert by_task[(ready, "subject_closeout_ready")]["recommended_action"] == "manager_formal_closeout"
        packet = by_task[(ready, "subject_closeout_ready")]["action_packet"]
        assert packet["action_code"] == "manager_formal_closeout"
        assert packet["apply_allowed"] is True
        assert packet["assignee"] == "manager"
        assert packet["task_stage"] == "curriculum"
        assert packet["closeout_gate"] == {
            "review_approved": True,
            "evidence_present": True,
            "qa_standard_met": True,
            "qbank_ready": False,
        }
        assert "正式收口" in packet["suggested_brief"]
        plan = packet["execution_plan"]
        assert plan["dry_run"] is True
        assert plan["execution_policy"] == "dry_run_only/requires_manager_confirmation/no_auto_dispatch"
        assert plan["proposed_command"] == f"eduflow task manager-closeout {ready} --actor manager"
        assert "review approved" in plan["preconditions"]


def test_scan_manager_anomalies_surfaces_qa_standard_and_qbank_readiness_gaps():
    with isolated_env():
        low_volume = _approved_subject_task(evidence={
            "files_sampled": ["Q-1.md"],
            "items_mapping_count": 299,
            "q_ids_checked": ["Q-1"],
            "calculation_or_concept_checks": ["checked"],
            "path_naming_result": "pass",
            "qa_count": 299,
            "item_count": 299,
            "sampled_topic_count": 6,
            "missing_topic_count": 0,
            "qbank_readiness": "qbank_ready",
        })
        missing_directions = _approved_subject_task(
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

        findings = task_event_scanner.scan_manager_anomalies()
        by_task = {(row["task_id"], row["category"]): row for row in findings}
        low = by_task[(low_volume, "subject_closeout_blocked")]
        assert low["recommended_action"] == "request_worker_course_expand_qa"
        assert "qa_standard=qa_standard_low_volume" in low["evidence_summary"]
        assert "qbank_readiness=qbank_blocked_low_volume" in low["evidence_summary"]
        assert low["action_packet"]["assignee"] == "worker_course"
        assert low["action_packet"]["action_code"] == "request_worker_course_expand_qa"
        assert low["action_packet"]["apply_allowed"] is True
        assert "还差 1" in low["action_packet"]["suggested_brief"]
        low_plan = low["action_packet"]["execution_plan"]
        assert low_plan["dry_run"] is True
        assert "eduflow task dispatch worker_course" in low_plan["proposed_command"]
        assert "返修后必须回 review_course" in low_plan["proposed_brief"]

        directions = by_task[(missing_directions, "subject_qbank_readiness_blocked")]
        assert directions["recommended_action"] == "request_qbank_readiness_check"
        assert "qbank_blocked_missing_question_directions" in directions["evidence_summary"]
        assert directions["action_packet"]["assignee"] == "worker_qbank"
        assert directions["action_packet"]["action_code"] == "request_qbank_readiness_check"
        assert directions["action_packet"]["apply_allowed"] is True
        assert "题库" in directions["action_packet"]["suggested_brief"]
        qbank_plan = directions["action_packet"]["execution_plan"]
        assert "eduflow task dispatch worker_qbank" in qbank_plan["proposed_command"]
        assert "qbank_readiness verdict" in qbank_plan["proposed_brief"]


def test_scan_manager_anomalies_action_packet_routes_missing_evidence_to_review_course():
    with isolated_env():
        blocked = _approved_subject_task(evidence={})
        findings = task_event_scanner.scan_manager_anomalies()
        by_task = {(row["task_id"], row["category"]): row for row in findings}
        packet = by_task[(blocked, "subject_closeout_blocked")]["action_packet"]
        assert packet["action_code"] == "request_review_course_file_evidence"
        assert packet["assignee"] == "review_course"
        assert "files_sampled" in packet["suggested_brief"]
        plan = packet["execution_plan"]
        assert "eduflow task dispatch review_course" in plan["proposed_command"]
        assert "q_ids_checked" in plan["proposed_brief"]


def test_scan_manager_anomalies_reports_truth_sync_lag_when_visible_pass_exists():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450 ready-for-qbank 补齐与复核闭环",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Business Studies 0450 正式完成，等待 review_course 文件级复核。",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        task = tasks.get(tid)
        task["status"] = "已完成"
        task["completed_at"] = task["updated_at"]
        task["verdict"] = "pending"
        from eduflow.util import write_json

        write_json(paths.state_file("tasks.json"), {"tasks": [task]})
        local_facts.append_log(
            "review_course",
            "say",
            "T-10 Business Studies 0450 复检结果：Verdict: PASS — 可发布。25 topics × 12 QA = 300。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["category"] == "subject_truth_sync_lag_detected"]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == tid
        assert flagged[0]["severity"] == "info"
        assert flagged[0]["live_blocker"] is False
        assert flagged[0]["structured_truth_lag"] is True
        assert flagged[0]["truth_source"] == "visible_review_pass"
        assert flagged[0]["recommended_action"] == "reconcile_task_truth_from_visible_verdict"
        assert "visible_review_pass_log=" in flagged[0]["evidence_summary"]
        assert not [row for row in findings if row["category"] == "subject_closeout_blocked"]


def test_visible_review_pass_requires_batch_or_task_scope_when_available():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4 topic-outline + QA seed",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.append_log(
            "review_course",
            "say",
            "Physics 0625 Batch 1 复检结果：PASS — 可发布。",
        )

        task = tasks.get(tid)
        assert task is not None
        assert task_event_scanner._visible_review_pass_for_task(task) is None


def test_scan_manager_anomalies_reports_review_truth_sync_lag_for_visible_batch_pass():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4 topic-outline + QA seed",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        task = tasks.get(tid)
        assert task is not None
        local_facts.append_log(
            "review_course",
            "say",
            "T-99 Physics 0625 Batch 4 复检结果：Verdict: PASS — 可发布。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row["task_id"] == tid and row["category"] == "review_pass_log_but_task_pending"
        ]
        assert len(flagged) == 1
        assert flagged[0]["severity"] == "info"
        assert flagged[0]["live_blocker"] is False
        assert flagged[0]["recommended_action"] == "reconcile_task_review_truth_from_visible_verdict"


def test_scan_manager_anomalies_does_not_treat_legacy_completed_status_as_active_stale():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450 ready-for-qbank 补齐与复核闭环",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Business Studies 0450 正式完成，等待 review_course 文件级复核。",
        )
        task = tasks.get(tid)
        task["status"] = "已完成"
        task["completed_at"] = task["updated_at"]
        from eduflow.util import write_json

        write_json(paths.state_file("tasks.json"), {"tasks": [task]})

        findings = task_event_scanner.scan_manager_anomalies(
            now=task["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        assert not [
            row for row in findings
            if row["task_id"] == tid and row["category"] == "stale_task"
        ]


def test_scan_manager_anomalies_recommends_rollover_after_closeout_completed():
    with isolated_env():
        done = _approved_subject_task(
            title="IGCSE Business Studies 0450",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        tasks.manager_closeout_subject(done, actor="manager", skip_subject_verifier=True)
        tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        rollover = [row for row in findings if row["category"] == "next_subject_rollover_ready"]
        assert len(rollover) == 1
        assert rollover[0]["recommended_action"] == "dispatch_next_subject_worker_course"
        assert "IGCSE Accounting 0452" in rollover[0]["evidence_summary"]
        packet = rollover[0]["action_packet"]
        assert packet["action_code"] == "dispatch_next_subject_worker_course"
        assert packet["apply_allowed"] is True
        assert packet["assignee"] == "worker_course"
        assert "IGCSE Accounting 0452" in packet["suggested_brief"]
        plan = packet["execution_plan"]
        assert plan["dry_run"] is True
        assert "eduflow task dispatch worker_course" in plan["proposed_command"]
        assert "current subject closeout_completed" in plan["preconditions"]


def test_scan_manager_anomalies_reports_no_next_subject_candidate():
    with isolated_env():
        done = _approved_subject_task(
            title="IGCSE Business Studies 0450",
            evidence={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 300,
                "item_count": 300,
            },
        )
        tasks.manager_closeout_subject(done, actor="manager", skip_subject_verifier=True)
        findings = task_event_scanner.scan_manager_anomalies()
        rollover = [row for row in findings if row["category"] == "next_subject_rollover_ready"]
        assert len(rollover) == 1
        assert rollover[0]["recommended_action"] == "no_next_subject_candidate"
        assert rollover[0]["action_packet"]["assignee"] == "manager"
        assert rollover[0]["action_packet"]["apply_allowed"] is False
        assert rollover[0]["action_packet"]["execution_plan"]["proposed_command"] == "no-op"


def _approved_subject_task(title="IGCSE Accounting 0452", evidence=None):
    tid = tasks.create_flow(
        "worker_course",
        title,
        stage="curriculum",
        owner="worker_course",
        creator="manager",
        description="Subject final closeout 正式完成",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    if evidence is None:
        # Default: provide a complete evidence packet so the subject can
        # be closed out (Package 7 — Revision-First Gate).
        packet = {
            "workflow_id": "igcse-subject-launch",
            "task_id": tid,
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
        }
    else:
        # Caller explicitly passed evidence (may be {} to test
        # missing-evidence paths). Respect it verbatim.
        packet = dict(evidence)
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


def test_scan_include_silent_returns_internal_events_too():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        rows = task_event_scanner.scan_publish_decisions(include_silent=True)
        assert [row["reason"] for row in rows] == [
            "worker_accepted",
            "internal_assignment",
        ]


def test_scan_advance_writes_cursor_and_skips_old_events_next_time():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        first = task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)
        assert len(first) == 2
        assert paths.task_publish_cursor_file().exists()
        second = task_event_scanner.scan_publish_decisions(include_silent=True)
        assert second == []


def test_scan_dedupes_worker_reassurance_after_advance():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        first = task_event_scanner.scan_publish_decisions(advance=True)
        reasons = [row["reason"] for row in first]
        assert "worker_accepted" in reasons
        assert "worker_started" in reasons
        second = task_event_scanner.scan_publish_decisions()
        assert second == []


def test_scan_returns_worker_completed_handoff_and_waiting_on_manager_reasons():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        rows = task_event_scanner.scan_publish_decisions()
        reasons = [row["reason"] for row in rows]
        assert "worker_completed_handed_to_manager" in reasons
        assert "worker_waiting_on_manager" not in reasons


def test_scan_delays_fresh_waiting_on_manager_until_later():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        first = task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)
        waiting = [row for row in first if row["reason"] == "worker_waiting_on_manager"]
        assert len(waiting) == 1
        assert waiting[0]["publish"] is False
        assert waiting[0]["cadence_action"] == "delay_and_wait"

        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_publish_gate.WORKER_WAITING_DELAY_MS + 1
        )
        manager_action = [item for item in findings if item["category"] == "manager_action_overdue"]
        assert len(manager_action) == 1
        assert manager_action[0]["recommended_action"] == "delay_and_wait"


def test_scan_merges_completed_handoff_when_manager_result_arrives_in_same_batch():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        rows = task_event_scanner.scan_publish_decisions(include_silent=True)
        handoff = [row for row in rows if row["reason"] == "worker_completed_handed_to_manager"]
        delivered = [row for row in rows if row["reason"] == "delivered_to_user"]
        assert len(handoff) == 1
        assert handoff[0]["publish"] is False
        assert handoff[0]["cadence_action"] == "merge_with_next_update"
        assert len(delivered) == 1


def test_scan_close_loop_closes_on_final_result_after_advance():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        first = task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)
        delivered = [row for row in first if row["reason"] == "delivered_to_user"]
        assert len(delivered) == 1
        assert delivered[0]["close_loop_state"] == "manager_result_closed"
        assert delivered[0]["close_loop_reason"] == "final_result_delivered"


def test_scan_suppresses_worker_reassurance_after_close_loop():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft IGCSE Physics 0625 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        # Package 3: drive through review_flow() so verdict_target /
        # latest_authoritative_verdict are recorded. The direct
        # transition to delivered used here previously left the task
        # with verdict=approved but no scope declaration, which now
        # legitimately triggers a review_truth_conflict finding.
        # Include all REQUIRED_EVIDENCE_PACKET_FIELDS so Package 7's
        # evidence_packet_incomplete_finding does not also surface
        # here (the test is about close-loop suppression, not about
        # missing packet fields).
        tasks.review_flow(
            tid, outcome="approve", actor="review_course",
            review_reason="approved_for_delivery",
            verdict_target="Draft IGCSE Physics 0625 outline",
            evidence_packet={
                "workflow_id": "igcse-subject-launch",
                "task_id": tid,
                "batch_range": "1",
                "items_count": 9,
                "qql_count": 9,
                "manifest_evidence": "manifest.csv",
                "files_sampled": ["Q-1.md"],
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
            },
        )
        task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)

        tid2 = tasks.create_flow(
            "worker_course",
            "Draft IGCSE Physics 0625 outline 2",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid2, to_status="assigned", actor="manager")
        tasks.transition_flow(tid2, to_status="in_progress", actor="worker_course")
        rows = task_event_scanner.scan_publish_decisions(include_silent=True)
        # control: another task still works
        assert any(row["task_id"] == tid2 for row in rows)

        stale = task_event_scanner.scan_manager_anomalies(
            now=(tasks.get(tid) or {})["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        assert all(item["task_id"] != tid for item in stale)


def test_scan_reopens_after_new_meaningful_change():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)

        # Simulate a new turn by creating a fresh task event shape on same task via live transition path.
        with tasks._locked():
            data = tasks._load()
            row = next(task for task in data["tasks"] if task["id"] == tid)
            row["status"] = "in_progress"
            row["completed_at"] = None
            row["updated_at"] += 1
            row["last_meaningful_update_at"] = row["updated_at"]
            tasks._save(data)
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker_course")
        rows = task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)
        reopened = [row for row in rows if row["task_id"] == tid and row["close_loop_state"] == "reopen_after_new_meaningful_change"]
        assert len(reopened) == 1
        assert reopened[0]["reason"] == "dedup_suppressed"


def test_scan_keeps_manager_summary_only_reason_visible_in_silent_scan():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        first = task_event_scanner.scan_publish_decisions(include_silent=True, advance=True)
        matching = [row for row in first if row["reason"] == "worker_waiting_on_manager"]
        assert len(matching) == 1
        assert matching[0]["publish"] is False
        assert matching[0]["audience_policy"] == "worker_reassurance"
        assert matching[0]["cadence_action"] == "delay_and_wait"
        second = task_event_scanner.scan_publish_decisions(include_silent=True)
        assert second == []


def test_scan_recovers_by_created_at_when_cursor_event_missing():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        events = tasks.list_task_events(task_id=tid)
        first = events[0]
        task_event_scanner.write_cursor(first["event_id"], first["created_at"])
        paths.state_dir().joinpath("task-events.jsonl").write_text("", encoding="utf-8")
        tid2 = tasks.create_flow(
            "worker_course",
            "Draft Unit 2 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid2, to_status="assigned", actor="manager")
        rows = task_event_scanner.scan_publish_decisions(include_silent=True)
        assert len(rows) >= 1
        assert all(row["task_id"] == tid2 for row in rows)


def test_scan_manager_anomalies_flags_stale_task():
    with isolated_env(), attr_patch(task_event_scanner, now_ms=lambda: 2_000_000):
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        stale = [item for item in findings if item["category"] == "stale_task"]
        assert len(stale) == 1
        assert stale[0]["task_id"] == tid
        assert stale[0]["recommended_action"] == "send_worker_reassurance"


def test_scan_manager_anomalies_surfaces_suppress_duplicate_update_for_repeated_reassurance():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        task_event_scanner.scan_publish_decisions(advance=True)
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        stale = [item for item in findings if item["category"] == "stale_task"]
        assert len(stale) == 1
        assert stale[0]["recommended_action"] == "suppress_duplicate_update"


def test_scan_manager_anomalies_flags_reject_resubmit_loop():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        for _ in range(2):
            tasks.submit_for_review(tid, actor="worker_course")
            tasks.review_flow(tid, outcome="reject", actor="reviewer_amy")
        findings = task_event_scanner.scan_manager_anomalies()
        loops = [item for item in findings if item["category"] == "reject_resubmit_loop"]
        assert len(loops) == 1
        assert loops[0]["task_id"] == tid
        assert loops[0]["loop_count"] == 2
        assert "需要修改后重新提交" in loops[0]["evidence_summary"]
        assert loops[0]["recommended_action"] == "send_manager_result"


def test_scan_manager_anomalies_flags_overdue_manager_action():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="manager_action", actor="reviewer_amy")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.MANAGER_ACTION_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["category"] == "manager_action_overdue"]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == tid
        assert "待经理处理" in flagged[0]["why"]
        assert "需要经理介入判断" in flagged[0]["evidence_summary"]
        assert "审核人请求经理介入" in flagged[0]["evidence_summary"]
        assert flagged[0]["recommended_action"] == "request_manager_decision"


def test_scan_manager_anomalies_handles_legacy_semantic_values_safely():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        with tasks._locked():
            data = tasks._load()
            row = next(task for task in data["tasks"] if task["id"] == tid)
            row["review_reason"] = "legacy_phrase"
            tasks._save(data)
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        stale = [item for item in findings if item["category"] == "stale_task"]
        assert len(stale) == 1
        assert "未归类审核原因：legacy_phrase" in stale[0]["evidence_summary"]
        assert stale[0]["recommended_action"] == "send_worker_reassurance"


def test_scan_manager_anomalies_detects_worker_course_status_truth_lag():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Mathematics 0580",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        local_facts.upsert_status("worker_course", "进行中", "Chemistry 0620 首批 300 items 已完工")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["category"] == "status_truth_lag_detected"]
        assert len(flagged) == 1
        assert flagged[0]["task_id"] == tid
        assert flagged[0]["surface_state"] == "producing_current_subject"
        assert flagged[0]["recommended_action"] == "refresh_worker_surface"
        assert "Chemistry 0620" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_detects_review_course_status_truth_lag():
    with isolated_env():
        tid = tasks.create_flow(
            "review_course",
            "IGCSE Mathematics 0580 review",
            stage="review",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        local_facts.upsert_status("review_course", "进行中", "正在审 Physics 0625 旧批次")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.REVIEW_STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["category"] == "status_truth_lag_detected"]
        assert len(flagged) == 1
        assert flagged[0]["surface_state"] == "review_pending_current_subject"
        assert flagged[0]["recommended_action"] == "refresh_review_surface"


def test_scan_manager_anomalies_detects_builder_surface_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Summarize course skill",
            stage="builder",
            owner="worker_builder",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_builder")
        local_facts.upsert_status("worker_builder", "进行中", "Still on old artifact")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["task_id"] == tid and item["category"] == "status_truth_lag_detected"]
        assert len(flagged) == 1
        assert flagged[0]["surface_state"] == "builder_task_accepted"
        assert flagged[0]["recommended_action"] == "refresh_builder_surface"


def test_scan_manager_anomalies_detects_qbank_surface_state():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_qbank",
            "Mathematics 0580 qbank check",
            stage="qbank",
            owner="worker_qbank",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_qbank")
        tasks.transition_flow(tid, to_status="delivered", actor="worker_qbank")
        local_facts.upsert_status("worker_qbank", "进行中", "ETA 30m")
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        )
        flagged = [item for item in findings if item["task_id"] == tid and item["category"] == "status_truth_lag_detected"]
        assert len(flagged) == 1
        assert flagged[0]["surface_state"] == "qbank_first_verdict_ready"
        assert flagged[0]["recommended_action"] == "refresh_qbank_surface"


def test_scan_manager_anomalies_marks_stale_status_surface_when_truth_present_but_snapshot_old():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Mathematics 0580",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        local_facts.upsert_status("worker_course", "进行中", "IGCSE Mathematics 0580")
        row = tasks.get(tid)
        assert row is not None
        with tasks._locked():
            data = tasks._load()
            task = next(item for item in data["tasks"] if item["id"] == tid)
            task["updated_at"] += task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 5
            task["last_meaningful_update_at"] = task["updated_at"]
            tasks._save(data)
        updated = tasks.get(tid)
        assert updated is not None
        findings = task_event_scanner.scan_manager_anomalies(now=updated["last_meaningful_update_at"] + 1)
        flagged = [item for item in findings if item["task_id"] == tid and item["category"] == "stale_status_surface"]
        assert len(flagged) == 1
        assert flagged[0]["surface_state"] == "producing_current_subject"


def test_scan_manager_anomalies_flags_stale_process_visibility_for_active_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        local_facts.upsert_status("worker_course", "进行中", "T-13 Physics Batch 4 开始处理")
        row = tasks.get(tid)
        assert row is not None
        status = local_facts.get_status("worker_course")
        assert status is not None
        current_now = max(
            row["last_meaningful_update_at"],
            status["updated_at"],
        ) + task_event_scanner.PROCESS_VISIBILITY_STALE_THRESHOLD_MS + 1

        findings = task_event_scanner.scan_manager_anomalies(now=current_now)
        flagged = [item for item in findings if item["task_id"] == tid and item["category"] == "process_visibility_stale"]
        assert len(flagged) == 1
        assert flagged[0]["severity"] == "info"
        assert flagged[0]["live_blocker"] is False
        assert flagged[0]["recommended_action"] == "request_lightweight_process_update"

        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.append_log("worker_course", "say", "T-13 Physics Batch 4 仍在推进，当前核查 heat transfer QA。")
        findings = task_event_scanner.scan_manager_anomalies(now=current_now + 1)
        assert not [
            item for item in findings
            if item["task_id"] == tid and item["category"] == "process_visibility_stale"
        ]


def test_scan_manager_anomalies_flags_facts_only_qbank_process_visibility_stale():
    with isolated_env():
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "QBank manifest 盘点：Physics 0625 manifest 不完整，继续分析。",
        )
        status = local_facts.get_status("worker_qbank")
        assert status is not None

        findings = task_event_scanner.scan_manager_anomalies(
            now=status["updated_at"] + task_event_scanner.PROCESS_VISIBILITY_STALE_THRESHOLD_MS + 1
        )
        flagged = [
            item for item in findings
            if item["task_id"] == "facts:worker_qbank"
            and item["category"] == "facts_process_visibility_stale"
        ]
        assert len(flagged) == 1
        assert flagged[0]["severity"] == "info"
        assert flagged[0]["live_blocker"] is False
        assert flagged[0]["recommended_action"] == "request_lightweight_process_update"


def test_scan_manager_anomalies_reports_qbank_stale_as_provider_quota_blocked_when_proven():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_qbank",
                "进行中",
                "QBank manifest 盘点：Physics 0625 manifest 不完整，继续分析。",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 5 * 60 * 1000):
            local_facts.append_log(
                "manager",
                "say",
                "已核实全部 Qoder worker：worker_builder / worker_course / worker_qbank "
                "都是 provider-level Credits exhausted / FORBIDDEN code=112，无法执行任何操作。",
            )

        findings = task_event_scanner.scan_manager_anomalies(
            now=current_now + task_event_scanner.PROCESS_VISIBILITY_STALE_THRESHOLD_MS + 1
        )
        flagged = [
            item for item in findings
            if item["task_id"] == "facts:worker_qbank"
            and item["category"] == "facts_process_visibility_stale"
        ]

        assert len(flagged) == 1
        assert flagged[0]["severity"] == "warn"
        assert flagged[0]["live_blocker"] is True
        assert flagged[0]["status"] == "runtime_blocked_provider_quota"
        assert flagged[0]["recommended_action"] == "restore_provider_quota_or_reassign_runtime"


def test_scan_manager_anomalies_does_not_mark_auto_ops_continuing_watch_as_stale():
    with isolated_env():
        local_facts.upsert_status(
            "auto_ops",
            "进行中",
            "Hermes 告警已接管，auto_ops 继续盯盘。",
        )
        status = local_facts.get_status("auto_ops")
        assert status is not None

        findings = task_event_scanner.scan_manager_anomalies(
            now=status["updated_at"] + task_event_scanner.PROCESS_VISIBILITY_STALE_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == "facts:auto_ops"
            and item["category"] == "facts_process_visibility_stale"
        ]


def test_scan_manager_anomalies_flags_facts_accepted_without_started_signal():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_course",
                "已接单",
                "课程研发任务已接单：IGCSE Physics 0625 Batch 7 topic-outline + QA seed（T-16）",
            )

        findings = task_event_scanner.scan_manager_anomalies(
            now=current_now + task_event_scanner.ACCEPTED_WITHOUT_STARTED_THRESHOLD_MS + 1
        )
        flagged = [
            item for item in findings
            if item["category"] == "accepted_without_started_signal"
            and item.get("agent") == "worker_course"
        ]
        assert len(flagged) == 1
        assert flagged[0]["severity"] == "warn"
        assert flagged[0]["live_blocker"] is False
        assert flagged[0]["recommended_action"] == "request_started_or_blocker_signal"


def test_scan_manager_anomalies_suppresses_facts_accepted_after_started_signal():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_course",
                "已接单",
                "课程研发任务已接单：IGCSE Physics 0625 Batch 7 topic-outline + QA seed（T-16）",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 30_000):
            local_facts.append_log(
                "worker_course",
                "say",
                "课程研发任务已开始处理：IGCSE Physics 0625 Batch 7 topic-outline + QA seed（T-16）",
            )

        findings = task_event_scanner.scan_manager_anomalies(
            now=current_now + task_event_scanner.ACCEPTED_WITHOUT_STARTED_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["category"] == "accepted_without_started_signal"
            and item.get("agent") == "worker_course"
        ]


def test_scan_manager_anomalies_treats_waiting_review_status_as_delivered_to_review():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "Business Studies 0450 完工，等待 review_course 审核",
        )
        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == tid
            and item["category"] == "stale_status_surface"
        ]


def test_scan_manager_anomalies_treats_submitted_for_review_status_as_stage_synced():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "T-12 Physics 0625 Batch 3",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.upsert_status(
            "worker_course",
            "已交付",
            "T-12 Physics 0625 Batch 3 submitted for review. 5 topics x 9 items each.",
        )
        with tasks._locked():
            data = tasks._load()
            task = next(item for item in data["tasks"] if item["id"] == tid)
            task["updated_at"] += 1000
            task["last_meaningful_update_at"] = task["updated_at"]
            tasks._save(data)

        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == tid
            and item["category"] == "stale_status_surface"
        ]


def test_scan_manager_anomalies_treats_completed_to_manager_as_review_delivery_sync():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "T-15 Physics 0625 Batch 6",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.upsert_status(
            "worker_course",
            "已交付",
            "课程研发任务已完成并交给 manager：IGCSE Physics 0625 Batch 6 topic-outline + QA seed（T-15）",
        )
        with tasks._locked():
            data = tasks._load()
            task = next(item for item in data["tasks"] if item["id"] == tid)
            task["updated_at"] += 1000
            task["last_meaningful_update_at"] = task["updated_at"]
            tasks._save(data)

        row = tasks.get(tid)
        assert row is not None
        findings = task_event_scanner.scan_manager_anomalies(
            now=row["last_meaningful_update_at"] + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == tid
            and item["category"] == "stale_status_surface"
        ]


def test_scan_manager_anomalies_treats_visible_review_pass_as_delivery_sync():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4 topic-outline + QA seed",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.upsert_status(
            "worker_course",
            "已交付",
            "课程研发任务已完成并交给 manager：IGCSE Physics 0625 Batch 4 topic-outline + QA seed（T-13）",
        )
        task = tasks.get(tid)
        assert task is not None
        with attr_patch(local_facts, now_ms=lambda: task["last_meaningful_update_at"] + 2000):
            local_facts.append_log(
                "review_course",
                "say",
                "T-13 Physics 0625 Batch 4 复核结果：Verdict: PASS — 可 closeout。",
            )

        findings = task_event_scanner.scan_manager_anomalies(
            now=task["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == tid
            and item["category"] == "stale_status_surface"
        ]


def test_scan_manager_anomalies_does_not_treat_progress_waiting_verdict_as_closeout():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4 topic-outline + QA seed",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        task = tasks.get(tid)
        assert task is not None
        local_facts.append_log(
            "review_course",
            "say",
            "T-13 Physics 0625 Batch 4 复核结果：Verdict: PASS — 可 closeout。",
        )
        local_facts.append_log(
            "manager",
            "say",
            "T-13 Physics 0625 Batch 4 进展：worker_course 已完工交付，review_course 正在复检中，等 verdict 后 closeout。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [
            row for row in findings
            if row["task_id"] == tid and row["category"] == "review_pass_log_but_task_pending"
        ]
        assert len(flagged) == 1
        assert "manager_closeout_log=-" in flagged[0]["evidence_summary"]


def test_scan_manager_anomalies_flags_workflow_mentioned_but_not_mounted():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="调用 workflow: igcse-subject-launch",
        )
        data = tasks._load()
        row = next(item for item in data["tasks"] if item["id"] == tid)
        row["workflow_id"] = ""
        tasks._save(data)
        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid and row["category"] == "workflow_mentioned_but_not_mounted"]
        assert len(flagged) == 1


def test_scan_manager_anomalies_flags_submitted_without_reviewer():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        data = tasks._load()
        row = next(item for item in data["tasks"] if item["id"] == tid)
        row["reviewer"] = ""
        tasks._save(data)
        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid and row["category"] == "submitted_for_review_without_reviewer"]
        assert len(flagged) == 1


def test_scan_manager_anomalies_flags_package_pass_promoted_to_subject_closeout():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
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
            review_reason="approved_for_delivery",
            latest_turn_summary="Batch pass.",
            evidence_packet={"files_sampled": ["Q-1.md"], "path_naming_result": "pass"},
        )
        local_facts.append_log(
            "manager",
            "say",
            "T-1 IGCSE Chemistry 0620 Batch 1 已正式闭环，整科完成。",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid and row["category"] == "package_pass_promoted_to_subject_closeout"]
        assert len(flagged) == 1


def test_scan_manager_anomalies_suppresses_old_lane_task_when_newer_active_task_exists():
    with isolated_env():
        old = tasks.create_flow(
            "worker_course",
            "Old validation task",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(old, to_status="assigned", actor="manager")
        tasks.transition_flow(old, to_status="in_progress", actor="worker_course")
        old_row = tasks.get(old)
        assert old_row is not None

        new = tasks.create_flow(
            "worker_course",
            "Current Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(new, to_status="assigned", actor="manager")
        tasks.transition_flow(new, to_status="in_progress", actor="worker_course")
        local_facts.upsert_status("worker_course", "进行中", "Current Business Studies 0450")

        findings = task_event_scanner.scan_manager_anomalies(
            now=old_row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        )
        assert not [
            item for item in findings
            if item["task_id"] == old
            and item["category"] in {"stale_task", "status_truth_lag_detected"}
        ]


def test_evaluate_manager_supervision_is_healthy_and_silent_when_recently_active():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        result = task_event_scanner.evaluate_manager_supervision()
        assert result["health_status"] == "healthy_silent"
        assert result["recommended_action"] == "no_action"
        assert result["user_alert_action"] == "no_alert"
        assert result["user_message"] == ""
        assert "manager_recently_active" in result["auto_summary_reasons"]
        assert result["state_stale"] is False


def test_evaluate_manager_supervision_escalates_runtime_unhealthy():
    with isolated_env():
        result = task_event_scanner.evaluate_manager_supervision(
            now=task_event_scanner.SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS + 1
        )
        assert result["health_status"] == "repair_needed"
        assert result["primary_reason"] == "runtime_unhealthy"
        assert result["recommended_action"] == "trigger_supervisor_repair"
        assert result["user_alert_action"] == "alert_user_repair_started"
        assert "runtime_unhealthy" in result["auto_summary_reasons"]


def test_evaluate_manager_supervision_marks_stale_persisted_state():
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
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.touch_heartbeat("manager")
        result = task_event_scanner.evaluate_manager_supervision(now=current_now)
        assert result["health_status"] == "healthy_silent"
        assert result["primary_reason"] == "manager_recently_active"
        assert result["state_stale"] is True
        assert result["state_age_ms"] == 9900


def test_evaluate_manager_supervision_reads_runtime_guard_escalation():
    with isolated_env():
        paths.runtime_guard_state_file().parent.mkdir(parents=True, exist_ok=True)
        paths.runtime_guard_state_file().write_text(json.dumps({
            "agents": {
                "worker_course": {
                    "escalation_needed": True,
                    "escalation_reason": "fallback_chain_exhausted",
                    "last_switch_outcome": "fallback_exhausted",
                }
            }
        }), encoding="utf-8")
        local_facts.touch_heartbeat("manager")
        result = task_event_scanner.evaluate_manager_supervision()
        assert result["health_status"] == "repair_needed"
        assert result["primary_reason"] == "runtime_unhealthy"
        assert "agent_failover_escalation" in result["auto_summary_reasons"]
        assert result["runtime_guard_agents"]["worker_course"]["escalation_needed"] is True


def test_evaluate_manager_supervision_prioritizes_missing_supervisor_runtime_over_unread():
    with isolated_env():
        current_now = task_event_scanner.SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS + 1
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.touch_heartbeat("manager")
            local_facts.append_message(
                "manager",
                "codex",
                "监控纠偏：请处理 worker_course runtime blocker",
                priority="高",
            )

        result = task_event_scanner.evaluate_manager_supervision(now=current_now + 3 * 60 * 1000)
        assert result["health_status"] == "repair_needed"
        assert result["primary_reason"] == "runtime_unhealthy"
        assert result["recommended_action"] == "trigger_supervisor_repair"
        assert "runtime_unhealthy" in result["auto_summary_reasons"]
        assert "watchdog_down" in result["auto_summary_reasons"]
        assert "hermes_supervisor_down" in result["auto_summary_reasons"]
        assert "manager_high_priority_unread" in result["auto_summary_reasons"]


def test_evaluate_manager_supervision_treats_status_lag_as_recheck_needed():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        row = tasks.get(tid)
        assert row is not None
        current_now = row["last_meaningful_update_at"] + task_event_scanner.STATUS_TRUTH_LAG_THRESHOLD_MS + 1
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.touch_heartbeat("manager")
            local_facts.upsert_status("worker_course", "进行中", "initializing")
        result = task_event_scanner.evaluate_manager_supervision(now=current_now)
        assert result["health_status"] == "repair_needed"
        assert result["primary_reason"] == "status_surface_truth_lag"
        assert result["recommended_action"] == "trigger_manager_recheck"
        assert "status_surface_truth_lag" in result["auto_summary_reasons"]


def test_evaluate_manager_supervision_treats_process_visibility_stale_as_soft_warning():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        row = tasks.get(tid)
        assert row is not None
        current_now = row["last_meaningful_update_at"] + task_event_scanner.PROCESS_VISIBILITY_STALE_THRESHOLD_MS + 1
        with attr_patch(local_facts, now_ms=lambda: row["last_meaningful_update_at"]):
            local_facts.upsert_status("worker_course", "进行中", "IGCSE Physics 0625 Batch 4 开始处理")
        with attr_patch(task_event_scanner, _manager_runtime_reason=lambda now: ""):
            result = task_event_scanner.evaluate_manager_supervision(now=current_now)
        assert result["health_status"] == "soft_warning_observe"
        assert result["recommended_action"] == "continue_observing"
        assert "process_visibility_stale" in result["auto_summary_reasons"]


def test_evaluate_manager_supervision_soft_warning_does_not_alert_user():
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        row = tasks.get(tid)
        assert row is not None
        current_now = row["last_meaningful_update_at"] + task_event_scanner.STALE_TASK_THRESHOLD_MS + 1
        with attr_patch(task_event_scanner, now_ms=lambda: current_now), attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.touch_heartbeat("manager")
        result = task_event_scanner.evaluate_manager_supervision(
            now=current_now
        )
        assert result["health_status"] == "soft_warning_observe"
        assert result["recommended_action"] == "continue_observing"
        assert result["user_alert_action"] == "no_alert"
        assert "stale_task_backlog" in result["auto_summary_reasons"]


def test_advance_manager_supervision_tracks_repeated_issue_until_escalated_failure():
    with isolated_env():
        first = task_event_scanner.advance_manager_supervision(
            task_event_scanner.evaluate_manager_supervision(
                now=task_event_scanner.SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS + 1
            )
        )
        assert first["state_after"]["consecutive_issue_count"] == 1

        second = task_event_scanner.evaluate_manager_supervision(
            now=task_event_scanner.SUPERVISOR_MANAGER_HEARTBEAT_GRACE_MS + 2
        )
        assert second["health_status"] == "escalated_failure"
        assert second["user_alert_action"] == "alert_user_supervision_issue"


def test_safe_task_review_approve_action_packet_for_verdict_pass():
    """Test that VERDICT: PASS log generates safe_task_review_approve action packet."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Task verdict is still "pending" (no structured review_flow called)
        task = tasks.get(tid)
        assert task is not None
        assert task["verdict"] == "pending"

        # Inject log with VERDICT: PASS signal
        local_facts.append_log(
            "review_course",
            "say",
            f"{tid} IGCSE Business Studies 0450 VERDICT: PASS — 复核完成",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        # Should generate safe_task_review_approve action packet
        approve_findings = [
            row for row in flagged
            if row.get("action_packet", {}).get("action_code") == "safe_task_review_approve"
        ]
        assert len(approve_findings) == 1

        packet = approve_findings[0]["action_packet"]
        assert packet["apply_allowed"] is True
        assert packet["assignee"] in ("review_course", "manager")
        assert "log_id" in str(packet.get("evidence_summary", "")) or "local_id" in str(packet.get("evidence_summary", ""))
        assert str(tid) in str(packet.get("evidence_summary", ""))

        # Check execution_plan has proposed_command
        plan = packet.get("execution_plan", {})
        assert "proposed_command" in plan
        assert "task review" in plan["proposed_command"] and "--approve" in plan["proposed_command"]

        result = task_event_scanner.manager_action_apply(
            "safe_task_review_approve",
            tid,
            confirm=True,
        )
        assert result["applied"] is True
        assert result["apply_reason"] == "review_approved"
        reviewed = tasks.get(tid)
        assert reviewed is not None
        assert reviewed["status"] == "delivered"
        assert reviewed["verdict"] == "approved"


def test_safe_task_review_approve_for_task_completed_signal():
    """Test that task_completed log generates safe_task_review_approve action packet."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Inject log with task_completed signal instead of VERDICT: PASS
        local_facts.append_log(
            "review_course",
            "say",
            "Physics 0625 Batch 1 task_completed — 复核通过，可以发布",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        # Should generate safe_task_review_approve action packet
        approve_findings = [
            row for row in flagged
            if row.get("action_packet", {}).get("action_code") == "safe_task_review_approve"
        ]
        assert len(approve_findings) >= 1

        packet = approve_findings[0]["action_packet"]
        assert packet["apply_allowed"] is True


def test_safe_task_review_approve_for_fuhe_wancheng_verdict_pass():
    """Test that '复核完成 — VERDICT: PASS' generates safe_task_review_approve action packet."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 2",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Inject log with Chinese marker
        local_facts.append_log(
            "review_course",
            "say",
            "T-10 Chemistry 0620 Batch 2 复核完成 — VERDICT: PASS",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        # Should generate safe_task_review_approve action packet
        approve_findings = [
            row for row in flagged
            if row.get("action_packet", {}).get("action_code") == "safe_task_review_approve"
        ]
        assert len(approve_findings) >= 1


def test_worker_completed_suggests_submit_review_when_no_review_inbox():
    """Test that worker completion without submit_for_review suggests transition."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 Batch 3",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")

        # Worker says task_completed but no submit_for_review done
        local_facts.append_log(
            "worker_course",
            "say",
            "Accounting 0452 Batch 3 task_completed — 完工交付",
        )

        # Task status is still "in_progress" (no submit-review done)
        task = tasks.get(tid)
        assert task is not None
        assert task["status"] == "in_progress"

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        suggestion_findings = [
            row for row in flagged
            if row.get("category") == "worker_completed_missing_review_transition"
        ]
        assert len(suggestion_findings) == 1
        assert suggestion_findings[0]["action_packet"]["action_code"] == "suggest_submit_review"


def test_worker_accepted_suggests_in_progress_transition():
    """Test that worker acceptance without in_progress suggests transition."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Economics 0455 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        # Not transitioned to in_progress yet

        # Worker log shows started/accepted signal
        local_facts.append_log(
            "worker_course",
            "say",
            "Economics 0455 Batch 1 已接单，开始处理",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        transition_findings = [
            row for row in flagged
            if row.get("category") == "worker_accepted_missing_transition"
        ]
        assert len(transition_findings) == 1
        assert transition_findings[0]["action_packet"]["action_code"] == "suggest_in_progress_transition"


def test_worker_transition_suggestion_ignores_future_or_preparatory_logs():
    with isolated_env():
        assigned = tasks.create_flow(
            "worker_course",
            "IGCSE Economics 0455 Batch 2",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(assigned, to_status="assigned", actor="manager")
        local_facts.append_log(
            "worker_course",
            "say",
            "Economics 0455 Batch 2 已接单，准备开始，但还在等 manager 明确 scope。",
        )

        in_progress = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 4",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(in_progress, to_status="assigned", actor="manager")
        tasks.transition_flow(in_progress, to_status="in_progress", actor="worker_course")
        local_facts.append_log(
            "worker_course",
            "say",
            "Physics 0625 Batch 4 待当前素材完工后交付，不是本轮完成信号。",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        assert not [
            row for row in findings
            if row["task_id"] == assigned
            and row.get("category") == "worker_accepted_missing_transition"
        ]
        assert not [
            row for row in findings
            if row["task_id"] == in_progress
            and row.get("category") == "worker_completed_missing_review_transition"
        ]


def test_manager_action_status_not_reported_as_waiting_review():
    """Test that manager_action tasks don't appear as waiting_review."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Mathematics 0580 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Set needs_manager_action=True, verdict="manager_action"
        with tasks._locked():
            data = tasks._load()
            task = next(item for item in data["tasks"] if item["id"] == tid)
            task["needs_manager_action"] = True
            task["verdict"] = "manager_action"
            tasks._save(data)

        findings = task_event_scanner.scan_manager_anomalies()

        # Assert NO finding with category "waiting_review" for this task
        waiting_review = [
            row for row in findings
            if row["task_id"] == tid and "waiting_review" in str(row.get("category", ""))
        ]
        assert len(waiting_review) == 0

        # Assert the manager_action_finding is present instead
        manager_action = [
            row for row in findings
            if row["task_id"] == tid and "manager_action" in str(row.get("category", ""))
        ]
        assert len(manager_action) >= 1


def test_manager_closeout_signal_with_pending_task_generates_action():
    """Test that manager closeout signal generates manager_formal_closeout action."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Biology 0610 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Manager says "正式闭环"
        local_facts.append_log(
            "manager",
            "say",
            f"{tid} IGCSE Biology 0610 Batch 1 正式闭环",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        # Should generate manager_formal_closeout action packet
        closeout_findings = [
            row for row in flagged
            if row.get("action_packet", {}).get("action_code") == "manager_formal_closeout"
        ]
        assert len(closeout_findings) >= 1

        assert len(closeout_findings) == 1
        packet = closeout_findings[0]["action_packet"]
        assert packet["apply_allowed"] is False
        assert packet["assignee"] == "manager"


def test_safe_task_review_approve_includes_evidence_fields():
    """Test that safe_task_review_approve includes specific evidence fields."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 9",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Inject log with VERDICT: PASS signal
        local_facts.append_log(
            "review_course",
            "say",
            "Physics 0625 Batch 9 VERDICT: PASS — 复核完成，可发布",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid]

        approve_findings = [
            row for row in flagged
            if row.get("action_packet", {}).get("action_code") == "safe_task_review_approve"
        ]
        assert len(approve_findings) >= 1

        packet = approve_findings[0]["action_packet"]

        # Assert specific evidence fields
        evidence_summary = str(packet.get("evidence_summary", ""))
        assert "log_id" in evidence_summary or "local_id" in evidence_summary
        assert str(tid) in evidence_summary

        # Assert execution_plan has required sections
        plan = packet.get("execution_plan", {})
        assert "preconditions" in plan
        assert "proposed_command" in plan
        assert "proposed_brief" in plan


def test_review_pass_with_subject_signal_generates_single_safe_approve_packet():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450 subject closeout",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            description="Subject final closeout",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        local_facts.append_log(
            "review_course",
            "say",
            f"{tid} Business Studies 0450 VERDICT: PASS — 复核完成，可发布",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        approve_findings = [
            row for row in findings
            if row["task_id"] == tid
            and row.get("action_packet", {}).get("action_code") == "safe_task_review_approve"
        ]
        assert len(approve_findings) == 1


# ── V1 stale IGCSE workflow-drive reassurance packet ──────────────


def test_stale_finding_attaches_reassurance_packet_for_igcse_workflow_drive():
    """A stale IGCSE subject production task must surface a dry-run
    send_lightweight_reassurance action packet so manager-actions / panel
    can offer a one-tap ping. Non-IGCSE tasks must NOT get the packet."""
    with isolated_env():
        # IGCSE workflow-drive task → should get the packet
        igcse_tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(igcse_tid, to_status="assigned", actor="manager")
        # Non-IGCSE workflow-drive task → should NOT get the packet
        other_tid = tasks.create_flow(
            "worker_builder",
            "Fix Router",
            stage="builder",
            owner="worker_builder",
            creator="manager",
        )
        tasks.transition_flow(other_tid, to_status="assigned", actor="manager")

        # Force both to be past the stale threshold.
        data = tasks._load()
        stale_at = 1000
        for row in data["tasks"]:
            row["last_meaningful_update_at"] = stale_at
            row["updated_at"] = stale_at
        tasks._save(data)

        findings = task_event_scanner.scan_manager_anomalies(now=stale_at + task_event_scanner.STALE_TASK_THRESHOLD_MS + 60_000)

        igcse_packets = [
            row.get("action_packet")
            for row in findings
            if row["task_id"] == igcse_tid
            and row.get("category") == "stale_task"
        ]
        assert len(igcse_packets) == 1
        packet = igcse_packets[0]
        assert packet["action_code"] == "send_lightweight_reassurance"
        assert packet["apply_allowed"] is False
        assert "dry_run_only" in packet["execution_plan"]["execution_policy"]

        # Non-IGCSE task should not have a packet attached.
        other_packets = [
            row.get("action_packet")
            for row in findings
            if row["task_id"] == other_tid
            and row.get("category") == "stale_task"
            and row.get("action_packet")
        ]
        assert len(other_packets) == 0


def test_stale_reassurance_packet_blocks_real_apply():
    """Apply path rejects send_lightweight_reassurance even with --confirm
    because the action code is not in the auto-apply allowlist."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Chemistry 0620 Batch 1",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        # Confirm flow without prior packet state — apply returns not_allowed_dry_run_only.
        result = task_event_scanner.manager_action_apply(
            "send_lightweight_reassurance",
            tid,
            confirm=True,
        )
        assert result["applied"] is False
        assert result["apply_reason"] == "not_allowed_dry_run_only"
        assert "dry-run" in result["apply_summary"]


# ── package 7 (Revision-First Gate): stale_execution_context ──────


def test_supervisor_emits_stale_execution_context_when_revision_priority_unacknowledged_and_worker_producing_new_topics():
    """set revision_priority on task T-29; arrange worker_course local_facts
    showing it's producing topics outside the revision scope (e.g. status.task
    or status.blocker mentions topic 8.x or new subject 0653); call
    supervisor-check; assert a finding with type='stale_execution_context'
    exists, with task_id, workflow_id, expected_revision_scope,
    observed_new_scope, recommended_action fields."""
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        # Create a flow task and set revision_priority on it
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1 revision",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
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
        # Confirm revision_priority was set
        row = tasks.get(tid)
        assert row.get("revision_priority") == "minor"

        # Arrange worker_course local_facts showing it's producing topics
        # outside the revision scope (e.g. topic 8.x or new subject 0653)
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "已转入 Chemistry 0653 topic 8.x 开始处理",
        )

        # Call supervisor-check via CLI
        rc, out, _ = run_cli_command(["task", "supervisor-check"])

    assert rc == 0
    # Assert a finding with type='stale_execution_context' exists
    assert "stale_execution_context" in out
    assert "T-29" in out or tid in out
    assert "expected_revision_scope" in out
    assert "observed_new_scope" in out
    assert "recommended_action" in out


def test_supervisor_does_not_emit_stale_when_worker_in_revision_scope():
    """Same setup but worker's local_facts shows it is working on the
    revision scope only; no stale finding."""
    with isolated_env(), attr_patch(task_event_scanner, _watchdog_rows=_healthy_watchdog_rows):
        local_facts.touch_heartbeat("manager")
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 1 revision",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
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

        # Worker IS working on the revision scope only
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "正在修复 IGCSE Physics 0625 Batch 1 review 反馈的 QA 问题",
        )

        rc, out, _ = run_cli_command(["task", "supervisor-check"])

    assert rc == 0
    assert "stale_execution_context" not in out


def test_evidence_packet_validation_flags_missing_required_fields():
    """Call the evidence packet validator with a packet missing
    workflow_id / task_id / batch_range / items_count / qql_count /
    manifest_evidence; assert it returns a list of missing fields."""
    with isolated_env():
        incomplete_packet = {
            "files_sampled": ["Q-1.md"],
            # Missing: workflow_id, task_id, batch_range, items_count,
            # qql_count, manifest_evidence
        }
        missing = task_event_scanner.validate_evidence_packet(incomplete_packet)
        assert isinstance(missing, list)
        assert "workflow_id" in missing
        assert "task_id" in missing
        assert "batch_range" in missing
        assert "items_count" in missing
        assert "qql_count" in missing
        assert "manifest_evidence" in missing


def test_evidence_packet_validation_passes_with_complete_packet():
    """Packet with all required fields → returns empty missing list."""
    with isolated_env():
        complete_packet = {
            "workflow_id": "igcse-subject-launch",
            "task_id": "T-1",
            "batch_range": "Batch 1",
            "items_count": 50,
            "qql_count": 50,
            "manifest_evidence": "pass",
        }
        missing = task_event_scanner.validate_evidence_packet(complete_packet)
        assert isinstance(missing, list)
        assert missing == []


# ── package 7 (Revision-First Gate): cleared-revision negative + dispatch suppression + evidence_packet_incomplete ──


def test_stale_execution_context_does_not_fire_for_legitimate_0653_revision():
    """False-positive guard: when the expected scope IS `0653`, an
    observed status that mentions `0653` is NOT a pivot — the worker
    is staying on the revision scope. Codex round 4."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Combined Science 0653 topic-8",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="reject", actor="review_course",
            review_reason="changes_requested",
            scope_topic="igcse-combined-science-0653 topic-8",
        )
        assert tasks.get(tid).get("revision_priority") == "minor"
        # Worker stays on the SAME subject/scope.
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="working on 0653 topic-8 still",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
            and item.get("task_id") == tid
        ]
        assert findings == [], (
            f"unexpected stale_execution_context for legitimate 0653 revision: {findings}"
        )


def test_stale_execution_context_does_not_fire_for_legitimate_topic_8_revision():
    """False-positive guard: when the expected scope IS `topic-8`,
    an observed status that mentions `topic 8.x` is NOT a pivot —
    the worker is staying on the revision scope. Codex round 4."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 topic-8 batch-7",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="reject", actor="review_course",
            review_reason="changes_requested",
            scope_topic="igcse-physics-0625 topic-8 batch-7",
        )
        assert tasks.get(tid).get("revision_priority") == "minor"
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="continuing topic 8.x",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
            and item.get("task_id") == tid
        ]
        assert findings == [], (
            f"unexpected stale_execution_context for legitimate topic 8.x revision: {findings}"
        )


def test_manager_action_apply_blocks_closeout_when_evidence_packet_incomplete():
    """`manager_action_apply("manager_formal_closeout")` must refuse
    to apply when the supervisor surfaces an
    `evidence_packet_incomplete` (severity=error) finding for the
    subject. Codex round 4 — wire validate_evidence_packet into the
    closeout gate, not just supervisor findings."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 正式完成",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject 300 QA 正式完成",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        # Legacy REVIEW_EVIDENCE_FIELDS only — missing REQUIRED_EVIDENCE_PACKET_FIELDS.
        tasks.review_flow(
            tid,
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
        # Apply closeout — must be blocked.
        result = task_event_scanner.manager_action_apply(
            "manager_formal_closeout", tid, confirm=True,
        )
        assert result.get("applied") is False
        assert result.get("apply_reason") == "precondition_failed_evidence_packet_incomplete"
        assert "evidence_packet" in result.get("apply_summary", "")


def test_stale_execution_context_does_not_fire_after_explicit_clear():
    """T-29/T-34 negative regression: after the worker explicitly clears
    revision_priority, legitimate next-subject production must NOT
    trigger stale_execution_context."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="reject", actor="review_course",
            review_reason="changes_requested",
        )
        # Confirm the gate was raised
        assert tasks.get(tid).get("revision_priority") == "minor"
        # Operator (manager) acknowledges the revision is done.
        assert tasks.clear_revision_priority(tid, actor="manager") is True
        # Worker now legitimately moves to a new subject — must not be flagged.
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="igcse-biology-0610 batch 1",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
        ]
        assert findings == [], (
            f"unexpected stale_execution_context after clear: {findings}"
        )


def test_stale_execution_context_detects_raw_hyphenated_subject_id():
    """False-negative regression: worker pivots to a raw hyphenated
    subject ID (`igcse-physics-0625-batch-8`) that does not match the
    expected scope (`igcse-accounting-0452`) — must still trigger."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Accounting 0452 batch-7",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="reject", actor="review_course",
            review_reason="changes_requested",
            scope_topic="igcse-accounting-0452 batch-7",
        )
        # Confirm the gate was raised with scope_topic set
        assert tasks.get(tid).get("revision_priority") == "minor"
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="writing igcse-physics-0625-batch-8 now",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
            and item.get("task_id") == tid
        ]
        assert len(findings) == 1
        assert findings[0]["workflow_id"] == "igcse-subject-launch"
        assert findings[0]["severity"] == "warn"
        assert "igcse-physics-0625-batch-8" in findings[0]["observed_new_scope"]


def test_stale_execution_context_detects_topic_n_ref_outside_expected_batch():
    """Structural pattern: a `topic-3` / `batch-3` reference in the
    worker status, when the expected scope does not include that batch
    or topic, must trigger stale_execution_context."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Economics 0455",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="manager_action", actor="review_course",
            manager_action_type="clarify_scope",
            scope_topic="igcse-economics-0455 batch-1",
        )
        # Confirm the gate was raised
        assert tasks.get(tid).get("revision_priority") == "manager"
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="starting batch-3 now",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
            and item.get("task_id") == tid
        ]
        assert len(findings) == 1
        assert findings[0]["severity"] == "warn"


def test_manager_action_apply_blocks_dispatch_next_subject_under_revision_first():
    """`manager_action_apply` must refuse to apply
    `dispatch_next_subject_worker_course` while any active flow task
    has revision_priority set. Codex request-changes #1."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Accounting 0452",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.set_revision_priority(tid, value="minor", reason="simulated", actor="manager")
        result = task_event_scanner.manager_action_apply(
            "dispatch_next_subject_worker_course",
            tid,
            confirm=True,
        )
        assert result.get("applied") is False
        assert result.get("apply_reason") == "precondition_failed_revision_first"
        assert "revision-first gate" in result.get("apply_summary", "")


def test_stale_execution_context_detects_same_subject_out_of_batch():
    """False-negative regression: worker is still on the SAME subject
    (Physics 0625) but jumps to a different batch/topic
    (`topic 8.x`) while the expected scope is `Batch 1`. Must
    trigger stale_execution_context because the `8.x` marker is an
    explicit pivot that overrides the same-subject escape."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid, outcome="reject", actor="review_course",
            review_reason="changes_requested",
            scope_topic="IGCSE Physics 0625 Batch 1",
        )
        assert tasks.get(tid).get("revision_priority") == "minor"
        # Worker now produces on the SAME subject but a different topic.
        local_facts.upsert_status(
            "worker_course",
            status="进行中",
            task="IGCSE Physics 0625 topic 8.x",
            blocker="",
        )
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "stale_execution_context"
            and item.get("task_id") == tid
        ]
        assert len(findings) == 1, (
            f"expected stale_execution_context for same-subject out-of-batch, got {findings}"
        )
        assert findings[0]["severity"] == "warn"
        assert "topic 8.x" in findings[0]["observed_new_scope"].lower()


def test_manager_panel_next_executable_actions_suppress_dispatch_under_revision_first():
    """Manager-panel `Next Executable Actions` must NOT render
    `dispatch_next_subject_worker_course` while revision-first is
    active. Codex request-changes round 2."""
    with isolated_env():
        # First create a fully-deliverable subject that the scanner
        # would otherwise mark as `next_subject_rollover_ready`.
        rolled_over = tasks.create_flow(
            "worker_course", "IGCSE Chemistry 0620",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
            description="300 QA 全学科 正式完成",
        )
        tasks.assign_reviewer(rolled_over, reviewer="review_course", actor="manager")
        tasks.transition_flow(rolled_over, to_status="assigned", actor="manager")
        tasks.transition_flow(rolled_over, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(rolled_over, actor="worker_course")
        tasks.review_flow(
            rolled_over, outcome="approve", actor="review_course",
            review_reason="approved_for_delivery",
            verdict_target="IGCSE Chemistry 0620",
            evidence_packet={
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 300,
                "qa_count": 300,
                "item_count": 300,
                "q_ids_checked": ["Q-1"],
            },
        )
        # Trigger manager formal closeout so the subject is
        # closeout_completed and the scanner produces
        # next_subject_rollover_ready.
        from eduflow.store import tasks as _tasks_mod
        _tasks_mod.manager_closeout_subject(
            rolled_over, actor="manager", emit_event=False,
            skip_subject_verifier=True,
        )
        # Now create the active revision-first task.
        blocked = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        tasks.set_revision_priority(blocked, value="minor", reason="simulated", actor="manager")
        rc, out, err = run_cli_command([
            "task", "manager-panel",
        ])
        assert rc == 0, err
        # The panel must NOT recommend dispatch_next_subject_worker_course
        # anywhere (Subject Closeout, Next Executable Actions, etc.)
        # while the revision-first gate is active.
        # The 'none (revision_first_gate_holds_executable_actions)' or
        # 'revision_first_active ::' banner is acceptable.
        assert "dispatch_next_subject_worker_course" not in out, (
            f"manager-panel still recommends dispatch_next_subject_worker_course "
            f"under active revision-first:\n{out}"
        )


def test_evidence_packet_incomplete_finding_emitted_for_non_terminal_task():
    """`validate_evidence_packet` MUST be consumed by
    `scan_manager_anomalies` — tasks with a non-empty evidence_packet
    that lacks required fields must surface as
    `evidence_packet_incomplete` findings (severity=warn for active tasks)."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Accounting 0452",
            stage="curriculum", owner="worker_course", creator="manager",
            workflow_id="igcse-subject-launch",
        )
        # Inject a partial REQUIRED_EVIDENCE_PACKET_FIELDS packet onto
        # the task. We use the private _load/_save helpers because
        # there is no public setter for evidence_packet post-creation
        # (it is normally set via review_flow at submit time).
        data = tasks._load()
        for row in data.get("tasks", []):
            if row.get("id") == tid:
                row["evidence_packet"] = {
                    "workflow_id": "igcse-subject-launch",
                    # task_id, batch_range, items_count, qql_count, manifest_evidence missing
                }
        tasks._save(data)

        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "evidence_packet_incomplete"
            and item.get("task_id") == tid
        ]
        assert len(findings) == 1
        finding = findings[0]
        assert finding["severity"] == "warn"
        assert finding["workflow_id"] == "igcse-subject-launch"
        for required in ("task_id", "batch_range", "items_count", "qql_count", "manifest_evidence"):
            assert required in finding["missing_fields"]


def test_evidence_packet_incomplete_finding_escalated_for_closeout_candidate():
    """Delivered+approved closeout candidates with an incomplete
    evidence_packet must be flagged with severity=error and the
    `is_closeout_candidate` contract field, so the manager cannot
    accidentally advance closeout while the gap is open."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 正式完成",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject 300 QA 正式完成",
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
            latest_turn_summary="全部 10 批次 正式完成",
            verdict_target="IGCSE Physics 0625",
            # legacy packet (REVIEW_EVIDENCE_FIELDS only) — does NOT
            # satisfy REQUIRED_EVIDENCE_PACKET_FIELDS, so the validator
            # must flag the gap.
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
        # Task is now `delivered` + verdict=approved — a closeout
        # candidate. The validator must still flag the missing
        # REQUIRED_EVIDENCE_PACKET_FIELDS fields with severity=error.
        findings = [
            item for item in task_event_scanner.scan_manager_anomalies()
            if item.get("category") == "evidence_packet_incomplete"
            and item.get("task_id") == tid
        ]
        assert len(findings) == 1
        finding = findings[0]
        assert finding["severity"] == "error", (
            f"closeout candidate should be severity=error, got {finding['severity']}"
        )
        assert finding["is_closeout_candidate"] is True
        assert finding["verdict"] == "approved"
        assert finding["status"] == "delivered"
        for required in ("task_id", "batch_range", "items_count", "qql_count", "manifest_evidence"):
            assert required in finding["missing_fields"]


def _attach_verifier_result(tid: str, *, status="pass", items=300, qql=300, manifest=300,
                            scope="subject", blocking=None):
    data = tasks._load()
    for row in data.get("tasks", []):
        if row.get("id") == tid:
            row["verifier_result"] = {
                "scope": scope,
                "status": status,
                "items_count": items,
                "qql_count": qql,
                "manifest_rows": manifest,
                "blocking_reasons": blocking or [],
                "consistency": {
                    "drifts": [],
                    "drift_count": 0,
                    "scoped_total": manifest,
                },
            }
            break
    tasks._save(data)


def test_evidence_account_blocks_0606_items_qql_manifest_drift():
    with isolated_env():
        tid = _approved_subject_task(
            title="IGCSE Additional Mathematics 0606 正式完成",
            evidence={
                "workflow_id": "igcse-subject-launch",
                "task_id": "T-1",
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
        _attach_verifier_result(tid, items=378, qql=324, manifest=324)

        gate = tasks.subject_closeout_status(tasks.get(tid))
        account = gate["evidence_account"]

        assert gate["closeout_status"] == "evidence_account_conflict"
        assert account["closeout_ready"] is False
        assert "items_qql_count_drift:items=378:qql=324" in account["conflicting_evidence"]
        assert gate["recommended_action"] == "resolve_evidence_account_conflict"
        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid and row["category"] == "evidence_account_conflict"]
        assert len(flagged) == 1


def test_evidence_account_scoped_189_does_not_become_full_subject_closeout():
    with isolated_env():
        tid = _approved_subject_task(
            title="IGCSE Additional Mathematics 0606 Batch 1",
            evidence={
                "workflow_id": "igcse-subject-launch",
                "task_id": "T-1",
                "batch_range": "scoped_total=189",
                "items_count": 189,
                "qql_count": 189,
                "manifest_evidence": {"rows": 189},
                "files_sampled": ["Q-1.md"],
                "items_mapping_count": 189,
                "q_ids_checked": ["Q-1"],
                "calculation_or_concept_checks": ["checked"],
                "path_naming_result": "pass",
                "qa_count": 189,
                "item_count": 189,
            },
        )
        _attach_verifier_result(tid, items=189, qql=189, manifest=189)

        gate = tasks.subject_closeout_status(tasks.get(tid))
        account = gate["evidence_account"]

        assert account["closeout_ready"] is False
        assert gate["closeout_status"] != "closeout_ready"
        assert gate["recommended_action"] != "manager_formal_closeout"
        assert gate["qa_standard"] == "qa_standard_low_volume"


def test_evidence_account_blocks_0653_manifest_only_completion():
    with isolated_env():
        tid = _approved_subject_task(
            title="IGCSE Combined Science 0653 正式完成",
            evidence={
                "workflow_id": "igcse-subject-launch",
                "task_id": "T-1",
                "batch_range": "B1-B2 only",
                "manifest_evidence": {"rows": 8},
                "files_sampled": ["qa-manifest.csv"],
                "items_mapping_count": 8,
                "path_naming_result": "pass",
            },
        )
        _attach_verifier_result(
            tid,
            status="fail",
            items=0,
            qql=0,
            manifest=8,
            blocking=["missing_topic_outlines:B3-B7"],
        )

        gate = tasks.subject_closeout_status(tasks.get(tid))
        account = gate["evidence_account"]

        assert account["closeout_ready"] is False
        assert "items_count" in account["missing_evidence"]
        assert "qql_count" in account["missing_evidence"]
        assert "subject_verifier_fail" in account["conflicting_evidence"]
        assert gate["recommended_action"] != "manager_formal_closeout"


def test_evidence_account_latest_fail_overrides_old_pass():
    with isolated_env():
        tid = _approved_subject_task()
        data = tasks._load()
        for row in data.get("tasks", []):
            if row.get("id") == tid:
                row["status"] = "submitted_for_review"
                row["completed_at"] = None
                break
        tasks._save(data)
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            latest_turn_summary="latest review_course inbox FAIL",
            verdict_target="IGCSE Accounting 0452",
            evidence_packet={
                "workflow_id": "igcse-subject-launch",
                "task_id": tid,
                "batch_range": "full_subject",
                "items_count": 300,
                "qql_count": 300,
                "manifest_evidence": {"rows": 300},
            },
        )
        _attach_verifier_result(tid)

        gate = tasks.subject_closeout_status(tasks.get(tid))
        account = gate["evidence_account"]

        assert account["closeout_ready"] is False
        assert "latest_review_verdict_blocks_closeout:rejected" in account["conflicting_evidence"]
        assert gate["recommended_action"] != "manager_formal_closeout"


def test_evidence_account_incomplete_for_worker_self_report_without_machine_evidence():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 worker self-reported done",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
            workflow_id="igcse-subject-launch",
            status="delivered",
            verdict="approved",
        )

        findings = task_event_scanner.scan_manager_anomalies()
        flagged = [row for row in findings if row["task_id"] == tid and row["category"] == "evidence_account_incomplete"]

        assert len(flagged) == 1
        assert "workflow_id" not in flagged[0]["missing_evidence"]
        for field in ("batch_range_or_scope", "items_count", "qql_count", "manifest_evidence"):
            assert field in flagged[0]["missing_evidence"]
        assert flagged[0]["closeout_ready"] is False
        assert flagged[0]["recommended_action"] == "block_closeout_until_evidence_packet_complete"


def run_cli_command(argv):
    """Helper: invoke CLI and capture output."""
    import contextlib
    import io
    from eduflow import cli
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()
