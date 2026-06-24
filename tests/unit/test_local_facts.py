"""Tests for the local-facts store (inbox / status / log).

Each test runs inside `isolated_env()` so the state dir is fresh per test.
"""
from __future__ import annotations

import time

from eduflow.store import local_facts
from helpers import attr_patch, isolated_env


def test_append_then_list_messages():
    with isolated_env():
        mid = local_facts.append_message("worker", "manager", "hello", priority="高")
        rows = local_facts.list_messages("worker")
        assert len(rows) == 1
        assert rows[0]["local_id"] == mid
        assert rows[0]["content"] == "hello"
        assert rows[0]["priority"] == "高"
        assert rows[0]["read"] is False
        assert rows[0]["delivery_state"] == "delivered_to_inbox"
        assert rows[0]["ack_state"] == "pending"


def test_list_filters_by_agent_and_unread_only():
    with isolated_env():
        local_facts.append_message("a", "manager", "to a")
        local_facts.append_message("b", "manager", "to b")
        mid_unread = local_facts.append_message("a", "manager", "still unread")
        # mark first message read; second remains unread
        first_a = local_facts.list_messages("a")[0]
        local_facts.mark_read(first_a["local_id"])

        unread_a = local_facts.list_messages("a", unread_only=True)
        assert len(unread_a) == 1
        assert unread_a[0]["local_id"] == mid_unread

        all_b = local_facts.list_messages("b")
        assert len(all_b) == 1
        assert all_b[0]["content"] == "to b"


def test_mark_read_sets_flag_and_returns_false_on_miss():
    with isolated_env():
        mid = local_facts.append_message("a", "b", "x")
        assert local_facts.mark_read(mid) is True
        assert local_facts.list_messages("a", unread_only=True) == []
        assert local_facts.mark_read(mid) is True  # idempotent
        assert local_facts.mark_read("local_does_not_exist") is False


def test_mark_read_does_not_claim_agent_accepted_or_started():
    with isolated_env():
        mid = local_facts.append_message("worker_course", "manager", "repair 7.5")
        assert local_facts.mark_read(mid) is True
        row = local_facts.get_message(mid)
        assert row is not None
        assert row["read"] is True
        assert row["ack_state"] == "pending"
        assert row.get("ack_kind", "") == ""
        assert row.get("action_started_at") is None


def test_record_message_ack_tracks_accept_start_and_revision_details():
    with isolated_env():
        mid = local_facts.append_message("worker_course", "manager", "修 Accounting 7.5")
        assert local_facts.record_message_ack(
            mid,
            "accepted_revision",
            topic="Accounting 7.5",
            files=["IGCSE Accounting QA.md"],
            issues=["金额 $55,800 被 shell 展开"],
        ) is True
        row = local_facts.get_message(mid)
        assert row is not None
        assert row["ack_state"] == "agent_acknowledged"
        assert row["ack_kind"] == "accepted_revision"
        assert row["ack_details"]["topic"] == "Accounting 7.5"
        assert row["ack_details"]["files"] == ["IGCSE Accounting QA.md"]
        assert "shell" in row["ack_details"]["issues"][0]
        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "课程主线已接单" in snap["task"]
        logs = local_facts.list_logs("worker_course")
        assert len(logs) == 1
        assert logs[0]["type"] == "worker_course_stage_ack"

        assert local_facts.record_message_ack(mid, "started_task") is True
        row = local_facts.get_message(mid)
        assert row is not None
        assert row["ack_state"] == "action_started"
        assert row["ack_kind"] == "started_task"
        assert row["action_started_at"] is not None
        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "课程主线开始处理" in snap["task"]
        assert local_facts.record_message_ack("missing", "accepted_task") is False


def test_record_message_ack_supports_completed_and_reconciled_terminal_states():
    with isolated_env():
        mid = local_facts.append_message("manager", "worker_course", "Physics 0625 Batch 6 已完成，待收口", priority="高")
        assert local_facts.record_message_ack(mid, "completed") is True
        row = local_facts.get_message(mid)
        assert row is not None
        assert row["ack_state"] == "completed"
        assert row["ack_kind"] == "completed"
        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "已完成"

        assert local_facts.record_message_ack(mid, "reconciled") is True
        row = local_facts.get_message(mid)
        assert row is not None
        assert row["ack_state"] == "reconciled"
        assert row["ack_kind"] == "reconciled"
        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "已对账"


def test_high_priority_status_packet_nudges_collapse_previous_unread():
    with isolated_env():
        first = local_facts.append_message(
            "auto_ops", "manager", "只回三行状态包：当前真实状态", priority="高"
        )
        second = local_facts.append_message(
            "auto_ops", "codex", "只看当前真相，不补旧账。立即回 manager 三行状态包", priority="高"
        )
        rows = local_facts.list_messages("auto_ops")
        assert len(rows) == 2
        by_id = {r["local_id"]: r for r in rows}
        assert by_id[first]["read"] is True
        assert by_id[second]["read"] is False


def test_mark_all_read_can_keep_latest_unread():
    with isolated_env():
        local_facts.append_message("auto_ops", "manager", "old-1", priority="高")
        local_facts.append_message("auto_ops", "manager", "old-2", priority="高")
        local_facts.append_message("auto_ops", "codex", "latest", priority="高")
        changed = local_facts.mark_all_read("auto_ops", keep_last_unread=1)
        assert changed == 2
        unread = local_facts.list_messages("auto_ops", unread_only=True)
        assert len(unread) == 1
        assert unread[0]["content"] == "latest"


def test_latest_unread_message_returns_freshest_unread():
    with isolated_env():
        local_facts.append_message("auto_ops", "manager", "old", priority="高")
        newest = local_facts.append_message("auto_ops", "manager", "new", priority="高")
        row = local_facts.latest_unread_message("auto_ops")
        assert row is not None
        assert row["local_id"] == newest
        assert row["content"] == "new"


def test_record_auto_ops_min_ack_writes_status_heartbeat_and_log():
    with isolated_env():
        msg_id = local_facts.append_message(
            "auto_ops", "manager", "当前卡在 review ACK，请先回三行状态包", priority="高"
        )
        local_facts.record_auto_ops_min_ack(
            "auto_ops", msg_id, "当前卡在 review ACK，请先回三行状态包"
        )
        snap = local_facts.get_status("auto_ops")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "盯盘中" in snap["task"]
        assert local_facts.get_heartbeat("auto_ops") is not None
        logs = local_facts.list_logs("auto_ops")
        assert len(logs) == 1
        assert logs[0]["type"] == "ack"
        assert logs[0]["ref"] == f"inbox:{msg_id}"


def test_record_auto_ops_min_ack_is_idempotent_for_same_inbox_ref():
    with isolated_env():
        msg_id = local_facts.append_message(
            "auto_ops", "manager", "当前最大协作缺口是什么", priority="高"
        )
        local_facts.record_auto_ops_min_ack("auto_ops", msg_id, "当前最大协作缺口是什么")
        local_facts.record_auto_ops_min_ack("auto_ops", msg_id, "当前最大协作缺口是什么")
        logs = local_facts.list_logs("auto_ops")
        assert len(logs) == 1


def test_record_worker_qbank_followup_writes_status_heartbeat_and_log():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_qbank", "manager", "请基于 Batch 7 最新通过结果继续做 qbank follow-up", priority="高"
        )
        local_facts.record_worker_qbank_followup(
            "worker_qbank", msg_id, "请基于 Batch 7 最新通过结果继续做 qbank follow-up"
        )
        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "题库校验已接单" in snap["task"]
        assert local_facts.get_heartbeat("worker_qbank") is not None
        logs = local_facts.list_logs("worker_qbank")
        assert len(logs) == 1
        assert logs[0]["type"] == "qbank_followup"
        assert logs[0]["ref"] == f"inbox:{msg_id}"


def test_record_message_ack_started_writes_started_log_for_review_course():
    with isolated_env():
        mid = local_facts.append_message("review_course", "manager", "请复核 Physics Batch 1", priority="高")
        assert local_facts.record_message_ack(mid, "started_task", topic="Physics Batch 1") is True
        snap = local_facts.get_status("review_course")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "课程 review 开始处理" in snap["task"]
        logs = local_facts.list_logs("review_course")
        assert len(logs) == 1
        assert logs[0]["type"] == "review_course_started"


def test_record_worker_qbank_followup_is_idempotent_for_same_inbox_ref():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_qbank", "manager", "继续校验最新批次 QA 是否满足最低导入条件", priority="高"
        )
        local_facts.record_worker_qbank_followup("worker_qbank", msg_id, "继续校验最新批次 QA 是否满足最低导入条件")
        local_facts.record_worker_qbank_followup("worker_qbank", msg_id, "继续校验最新批次 QA 是否满足最低导入条件")
        logs = local_facts.list_logs("worker_qbank")
        assert len(logs) == 1


def test_status_upsert_then_get():
    with isolated_env():
        assert local_facts.get_status("a") is None
        assert local_facts.get_raw_status("a") is None
        local_facts.upsert_status("a", "进行中", "do thing")
        snap = local_facts.get_status("a")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert snap["task"] == "do thing"
        assert snap["blocker"] == ""

        # update overwrites
        local_facts.upsert_status("a", "已完成", "done", blocker="")
        snap = local_facts.get_status("a")
        assert snap["status"] == "已完成"
        raw = local_facts.get_raw_status("a")
        assert raw is not None
        assert raw["status"] == "已完成"
        assert raw["task"] == "done"


def test_get_status_projects_weak_ready_status_from_newer_log():
    with isolated_env():
        local_facts.upsert_status("worker_builder", "进行中", "ready")
        local_facts.append_log("worker_builder", "say", "收到运行态更新：当前 runtime/CLI/收发消息均正常，worker_builder 已同步该状态并保持待命。")
        snap = local_facts.get_status("worker_builder")
        assert snap is not None
        assert snap["status"] == "待命"
        assert "保持待命" in snap["task"]


def test_list_all_statuses_projects_initializing_from_newer_started_log():
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "initializing")
        local_facts.append_log("worker_course", "worker_course_started", "开始处理：课程主线开始处理：Physics 0625 Batch 2+ 生产（topics 2.5-7.5）")
        rows = local_facts.list_all_statuses()
        row = next(item for item in rows if item["agent"] == "worker_course")
        assert row["status"] == "进行中"
        assert "Physics 0625 Batch 2+" in row["task"]


def test_get_status_projects_weak_initializing_from_older_process_log():
    with isolated_env():
        local_facts.append_log(
            "worker_course",
            "say",
            "收到最新指令：Business Studies 0450 保持 12 items/topic，仅调整难度标签至 F:3|S:5|C:4。正在处理中。",
        )
        local_facts.upsert_status("worker_course", "进行中", "initializing")
        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "Business Studies 0450" in snap["task"]
        assert snap["task"] != "initializing"


def test_get_status_projects_waiting_review_after_visible_pass():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "T-10 Business Studies 0450 已恢复 12-item F:3|S:5|C:4，等待 review_course 复检",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-10 Business Studies 0450 复检结果：Verdict: PASS — 可发布。25 topics × 12 QA = 300。",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "空闲"
        assert "review_course 已 PASS" in snap["task"]
        assert "等待 manager 收口/下一步" in snap["task"]


def test_get_status_projects_course_in_progress_after_manager_closeout():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "T-7 Batch 3 二次返修: QA+items 全面同步 F:3|S:3|C:3",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-7 Accounting 0452 Batch 3 三次复检结果：Verdict: PASS — 可发布，交 manager closeout。",
        )
        local_facts.append_log(
            "manager",
            "say",
            "T-7 Accounting 0452 Batch 3 三次复检正式 PASS closeout。待命下一学科。",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "空闲"
        assert "manager 已 closeout" in snap["task"]
        assert "二次返修" not in snap["task"]


def test_get_status_suppresses_course_read_unacked_after_later_review_pass():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "进行中",
            "T-8 Physics 0625 Batch 1 manifest 修复",
        )
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

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] != "已读待确认"
        assert "尚未 ACK/started" not in snap["task"]


def test_get_status_projects_worker_course_from_newer_self_log():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "已交付：manager 已 closeout，待下一步。旧批次收口。",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发任务已接单：IGCSE Physics 0625 Batch 2 topic-outline + QA seed（T-11）",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "Physics 0625 Batch 2" in snap["task"]


def test_get_status_projects_worker_course_completed_self_log_as_delivered():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "已交付：manager 已 closeout，待下一步。旧批次收口。",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发已完成并交付：IGCSE Physics 0625 Batch 2 topic-outline + QA seed（T-11）",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "Physics 0625 Batch 2" in snap["task"]


def test_get_status_projects_worker_course_submitted_for_review_as_delivered():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "已接单",
            "课程主线已接单：T-12 Physics 0625 Batch 3",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "T-12 Physics 0625 Batch 3 submitted for review. 5 topics x 9 items each.",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "submitted for review" in snap["task"]


def test_get_status_projects_review_course_reviewing_self_log_as_in_progress():
    with isolated_env():
        local_facts.upsert_status(
            "review_course",
            "待命",
            "T-11 Physics Batch 2 PASS。待新任务。",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-12 Physics 0625 Batch 3（5 topics 2.4/2.5/2.6/3.1/3.2）复核中",
        )

        snap = local_facts.get_status("review_course")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "T-12 Physics 0625 Batch 3" in snap["task"]


def test_get_status_recovers_legacy_body_worker_course_completion_log():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "已交付：manager 已 closeout，待下一步。旧批次收口。",
        )
        local_facts.append_log(
            "--body",
            "say",
            "[worker_course] T-8 Physics 0625 Batch 2 COMPLETE. 4 new topics, each with outline + 9 items. Sending to review_course.",
        )

        logs = local_facts.list_logs("worker_course")
        assert len(logs) == 1
        assert logs[0]["agent"] == "--body"

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "Physics 0625 Batch 2" in snap["task"]
        assert "旧批次收口" not in snap["task"]


def test_legacy_body_log_without_explicit_agent_prefix_is_not_reassigned():
    with isolated_env():
        local_facts.append_log("--body", "say", "unscoped COMPLETE line")
        assert local_facts.list_logs("worker_course") == []


def test_get_status_prefers_new_unread_task_over_old_waiting_review_pass():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "空闲",
            "T-10 Business Studies 0450 已恢复 12-item F:3|S:5|C:4，等待 review_course 复检",
        )
        local_facts.append_log(
            "review_course",
            "say",
            "T-10 Business Studies 0450 复检结果：Verdict: PASS — 可发布。25 topics × 12 QA = 300。",
        )
        local_facts.append_message(
            "worker_course",
            "manager",
            "正式恢复课程主线 T-7 Accounting 0452。请从 backlog 继续生产 Batch 3。",
            priority="高",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "待接单"
        assert "T-7 Accounting 0452" in snap["task"]
        assert "review_course 已 PASS" not in snap["task"]


def test_get_status_projects_read_unacked_high_priority_as_waiting_confirmation():
    with isolated_env():
        local_facts.upsert_status("worker_qbank", "空闲", "qbank验证v2已交付, 等待下一轮派单")
        msg_id = local_facts.append_message(
            "worker_qbank",
            "manager",
            "老板要求：做 39 个同层重复的 dry-run 去重方案（只分析、不改动任何文件）。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已读待确认"
        assert "尚未 ACK/started" in snap["task"]
        assert "dry-run 去重方案" in snap["task"]


def test_get_status_projects_new_high_priority_unread_over_active_ack():
    with isolated_env():
        local_facts.upsert_status(
            "worker_course",
            "已接单",
            "课程主线已接单：T-13 Batch 4 续做",
        )
        local_facts.append_message(
            "worker_course",
            "manager",
            "[T-14 / igcse-subject-launch] 请立即执行 IGCSE Physics 0625 Batch 5；T-13 已 PASS closeout。",
            priority="high",
        )

        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "待接单"
        assert "新的高优任务未读" in snap["task"]
        assert "T-14" in snap["task"]
        assert "T-13 Batch 4 续做" not in snap["task"]


def test_get_status_projects_new_high_priority_unread_over_qbank_delivered_projection():
    with isolated_env():
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "待命中: manifest盘点已交付",
        )
        local_facts.append_message(
            "worker_qbank",
            "manager",
            "请立即做 Physics Batch 5 qbank readiness check，只回现状，不 apply。",
            priority="高",
        )

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "待接单"
        assert "qbank readiness check" in snap["task"]
        assert "manifest盘点已交付" not in snap["task"]


def test_get_status_projects_high_priority_unread_over_newer_lazy_idle_status():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.append_message(
                "anna",
                "manager",
                "请做 QBank 导入就绪检查，只读输出 readiness 报告。",
                priority="高",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 60_000):
            local_facts.upsert_status("anna", "待命", "lazy: CLI starts on first message")

        snap = local_facts.get_status("anna")

        assert snap is not None
        assert snap["status"] == "待接单"
        assert "新的高优任务未读" in snap["task"]
        assert "QBank 导入就绪检查" in snap["task"]
        assert "lazy: CLI starts on first message" not in snap["task"]


def test_get_status_projects_runtime_guard_block_over_unread_lazy_agent():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.append_message(
                "anna",
                "manager",
                "请做 QBank 导入就绪检查，只读输出 readiness 报告。",
                priority="高",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 60_000):
            local_facts.upsert_status("anna", "待命", "lazy: CLI starts on first message")
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

        snap = local_facts.get_status("anna")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert "runtime guard 已升级" in snap["task"]
        assert "QBank 导入就绪检查" in snap["task"]
        assert snap["blocker"] == "runtime guard escalation: provider_unavailable"


def test_get_status_does_not_project_read_unacked_after_direct_visibility():
    with isolated_env():
        local_facts.upsert_status("worker_qbank", "空闲", "qbank验证v2已交付, 等待下一轮派单")
        msg_id = local_facts.append_message(
            "worker_qbank",
            "manager",
            "老板要求：做 39 个同层重复的 dry-run 去重方案。",
            priority="高",
        )
        assert local_facts.mark_read(msg_id)
        local_facts.append_log("worker_qbank", "say", "已接单：qbank dry-run 去重方案正在分析，不改动文件。")

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "qbank dry-run 去重方案正在分析" in snap["task"]
        assert "等待下一轮派单" not in snap["task"]


def test_get_status_does_not_blame_manager_for_worker_visible_report_without_ack():
    with isolated_env():
        local_facts.upsert_status("manager", "进行中", "QBank v3.1 等待复检")
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

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "已读待确认" not in snap["task"]
        assert "QBank v3.1" in snap["task"]


def test_get_status_does_not_blame_manager_when_worker_status_proves_report():
    with isolated_env():
        local_facts.upsert_status("manager", "进行中", "responding to first message")
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

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "已读待确认" not in snap["task"]


def test_get_status_does_not_downgrade_manager_from_secondhand_worker_ack():
    with isolated_env():
        local_facts.upsert_status("manager", "进行中", "T-12 IGCSE Physics 0625 Batch 3 跟进中")
        time.sleep(0.01)
        local_facts.append_log(
            "manager",
            "say",
            "📊 进展：worker_course 已接单 T-12（IGCSE Physics 0625 Batch 3），开始处理中。",
        )

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "worker_course 已接单 T-12" in snap["task"]


def test_get_status_projects_manager_from_newer_worker_process_visibility():
    with isolated_env():
        local_facts.upsert_status(
            "manager",
            "待命",
            "T-12 Physics 0625 Batch 3 已 closeout，等待老板下一步。",
        )
        time.sleep(0.01)
        local_facts.append_log(
            "worker_course",
            "say",
            "课程研发任务已开始处理：IGCSE Physics 0625 Batch 4 topic-outline + QA seed（T-13）",
        )

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "团队推进中" in snap["task"]
        assert "worker_course" in snap["task"]
        assert "T-13" in snap["task"]


def test_get_status_does_not_project_manager_from_delivered_worker_visibility():
    with isolated_env():
        local_facts.upsert_status(
            "manager",
            "待命",
            "T-12 Physics 0625 Batch 3 已 closeout，等待老板下一步。",
        )
        time.sleep(0.01)
        local_facts.append_log(
            "worker_course",
            "say",
            "T-12 Physics 0625 Batch 3 submitted for review. 5 topics x 9 items each.",
        )

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "待命"
        assert "团队推进中" not in snap["task"]


def test_get_status_projects_manager_from_newer_review_delivery_visibility():
    with isolated_env():
        local_facts.upsert_status(
            "manager",
            "进行中",
            "T-16 Physics 0625 Batch 7 已 closeout，T-17 执行中。",
        )
        time.sleep(0.01)
        local_facts.append_log(
            "review_course",
            "task_completed",
            "T-17 Physics 0625 Batch 8 复核 PASS — 54 QA items，manifest/topic-outline 一致",
        )

        snap = local_facts.get_status("manager")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "团队待收口" in snap["task"]
        assert "review_course" in snap["task"]
        assert "T-17" in snap["task"]
        assert "等待 manager closeout" in snap["task"]


def test_get_status_projects_idle_manager_from_team_runtime_blockers():
    with isolated_env():
        local_facts.upsert_status("manager", "待命", "收口完成，等老板新指令")
        local_facts.append_log(
            "manager",
            "say",
            "Hermes 监控发现运行监督异常，已进入监督处理：runtime_unhealthy、agent_failover_escalation。",
        )
        local_facts.upsert_status("anna", "待命", "lazy: CLI starts on first message")
        local_facts.upsert_status("worker_qbank", "进行中", "initializing")
        local_facts.append_log(
            "manager",
            "say",
            "已核实 worker_qbank 是 Qoder API FORBIDDEN code=112 + Credits exhausted，无法执行任何操作。",
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

        snap = local_facts.get_status("manager")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert snap["blocker"] == "team runtime blockers"
        assert "团队阻塞待处理" in snap["task"]
        assert "Hermes 监控发现" not in snap["task"]
        assert "anna=runtime guard escalation: provider_unavailable" in snap["task"]
        assert "worker_qbank=Qoder provider credits exhausted" in snap["task"]


def test_get_status_manager_team_blocker_summary_includes_all_blocked_workers():
    with isolated_env():
        local_facts.upsert_status("manager", "待命", "收口完成，等老板新指令")
        local_facts.upsert_status("anna", "待命", "lazy: CLI starts on first message")
        local_facts.upsert_status("worker_builder", "进行中", "initializing")
        local_facts.upsert_status(
            "worker_course",
            "已交付",
            "课程研发已完成并交付：IGCSE Physics 0625 Batch 9 final topic-outline + QA seed（T-18）",
        )
        local_facts.upsert_status("worker_qbank", "进行中", "initializing")
        local_facts.append_log(
            "manager",
            "say",
            "已核实全部 3 个 Qoder worker (worker_builder / worker_course / worker_qbank) "
            "都是 Qoder API FORBIDDEN code=112 + Credits exhausted，无法执行任何操作。",
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json

        paths.runtime_guard_state_file().parent.mkdir(parents=True, exist_ok=True)
        write_json(paths.runtime_guard_state_file(), {
            "agents": {
                "anna": {
                    "last_failure_reason": "provider_unavailable",
                    "needs_manager_action": True,
                    "escalation_needed": True,
                }
            }
        })

        snap = local_facts.get_status("manager")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert "anna=runtime guard escalation: provider_unavailable" in snap["task"]
        assert "worker_builder=Qoder provider credits exhausted" in snap["task"]
        assert "worker_course=Qoder provider credits exhausted" in snap["task"]
        assert "worker_qbank=Qoder provider credits exhausted" in snap["task"]


def test_get_status_projects_idle_qbank_from_newer_completion_log():
    with isolated_env():
        local_facts.upsert_status("worker_qbank", "空闲", "qbank v2 已交付，等待后续")
        local_facts.append_log(
            "worker_qbank",
            "task_completed",
            "v3.1: 12个A4/A5条目方向反转修正, JSON全部33个collision校准.",
        )

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "v3.1" in snap["task"]


def test_get_status_projects_qbank_waiting_approval_as_delivered_not_active():
    with isolated_env():
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "待命中: v3.2去重方案已交付等待审批, inbox空",
        )

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "等待审批" in snap["task"]


def test_get_status_projects_qbank_delivered_standby_as_delivered_not_active():
    with isolated_env():
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "待命中: manifest盘点已交付",
        )

        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已交付"
        assert "manifest盘点已交付" in snap["task"]


def test_get_status_marks_facts_only_qbank_active_surface_as_stale():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_qbank",
                "进行中",
                "QBank manifest 盘点：Physics 0625 manifest 不完整，继续分析。",
            )

        stale_now = current_now + 11 * 60 * 1000
        with attr_patch(local_facts, now_ms=lambda: stale_now):
            snap = local_facts.get_status("worker_qbank")

        assert snap is not None
        assert snap["status"] == "进行中"
        assert snap["task"].startswith("外显陈旧：worker_qbank")
        assert "原状态=进行中" in snap["task"]
        assert "QBank manifest 盘点" in snap["task"]


def test_get_status_does_not_nest_facts_only_stale_prefix():
    with isolated_env():
        stale_now = 2_000_000
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "外显陈旧：worker_qbank 上次直接过程信号约 42 分钟前；原状态=进行中。QBank manifest 盘点：Physics 0625 manifest 不完整。",
        )
        with attr_patch(local_facts, now_ms=lambda: stale_now + 11 * 60 * 1000):
            snap = local_facts.get_status("worker_qbank")

        assert snap is not None
        assert snap["task"].count("外显陈旧：") == 1
        assert "QBank manifest 盘点" in snap["task"]


def test_get_status_projects_qoder_quota_block_over_stale_qbank_running():
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

        snap = local_facts.get_status("worker_qbank")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert snap["blocker"] == "Qoder provider credits exhausted"
        assert "运行时受阻" in snap["task"]
        assert "不能执行或产生真实过程信号" in snap["task"]
        assert "QBank manifest 盘点" in snap["task"]


def test_get_status_projects_newer_qoder_quota_block_over_course_delivery():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_course",
                "已交付",
                "课程研发已完成并交付：IGCSE Physics 0625 Batch 9 final topic-outline + QA seed（T-18）",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 5 * 60 * 1000):
            local_facts.append_log(
                "manager",
                "say",
                "已核实全部 3 个 Qoder worker (worker_builder / worker_course / worker_qbank) "
                "全部卡在 Qoder API FORBIDDEN code=112 + Credits exhausted，无法执行任何操作。",
            )

        snap = local_facts.get_status("worker_course")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert snap["blocker"] == "Qoder provider credits exhausted"
        assert "运行时受阻" in snap["task"]
        assert "当前不能执行或产生真实过程信号" in snap["task"]
        assert "上一交付线索" in snap["task"]
        assert "Physics 0625 Batch 9" in snap["task"]


def test_get_status_projects_qoder_quota_block_over_unread_builder_task():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status("worker_builder", "进行中", "initializing")
        with attr_patch(local_facts, now_ms=lambda: current_now + 60_000):
            local_facts.append_message(
                "worker_builder",
                "manager",
                "老板问能否切换到备用模型绕过 Qoder API FORBIDDEN，请调查 worker_builder。",
                priority="高",
            )
        with attr_patch(local_facts, now_ms=lambda: current_now + 2 * 60_000):
            local_facts.append_log(
                "manager",
                "say",
                "已核实 worker_builder / worker_course / worker_qbank 都是 "
                "Qoder API FORBIDDEN code=112 + Credits exhausted，无法执行任何操作。",
            )

        snap = local_facts.get_status("worker_builder")

        assert snap is not None
        assert snap["status"] == "受阻"
        assert snap["blocker"] == "Qoder provider credits exhausted"
        assert "运行时受阻" in snap["task"]
        assert not snap["task"].startswith("待接单")


def test_get_status_does_not_mark_auto_ops_continuing_watch_as_stale():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "auto_ops",
                "进行中",
                "Hermes 告警已接管，auto_ops 继续盯盘。",
            )

        with attr_patch(local_facts, now_ms=lambda: current_now + 11 * 60 * 1000):
            snap = local_facts.get_status("auto_ops")

        assert snap is not None
        assert snap["status"] == "进行中"
        assert not snap["task"].startswith("外显陈旧：")


def test_get_status_uses_half_hour_stale_window_for_auto_ops_presence():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "auto_ops",
                "进行中",
                "运行态简报：auto_ops 盯盘中；manager 待命。",
            )

        with attr_patch(local_facts, now_ms=lambda: current_now + 29 * 60 * 1000):
            snap = local_facts.get_status("auto_ops")
        assert snap is not None
        assert not snap["task"].startswith("外显陈旧：")

        with attr_patch(local_facts, now_ms=lambda: current_now + 31 * 60 * 1000):
            snap = local_facts.get_status("auto_ops")
        assert snap is not None
        assert snap["task"].startswith("外显陈旧：")


def test_get_status_projects_auto_ops_watchdog_alert_after_runtime_recovers():
    with isolated_env(), attr_patch(local_facts, _runtime_watchdog_recovered=lambda: True):
        local_facts.upsert_status(
            "auto_ops",
            "进行中",
            "盯盘: watchdog持续缺失(4轮/50min), 已4次催办manager仍未派发worker_builder",
        )

        snap = local_facts.get_status("auto_ops")

        assert snap is not None
        assert snap["status"] == "进行中"
        assert "router/watchdog 当前已恢复" in snap["task"]
        assert "旧 watchdog 缺失告警已过期" in snap["task"]


def test_get_status_keeps_auto_ops_watchdog_alert_when_runtime_still_unhealthy():
    with isolated_env(), attr_patch(local_facts, _runtime_watchdog_recovered=lambda: False):
        local_facts.upsert_status(
            "auto_ops",
            "进行中",
            "盯盘: watchdog持续缺失(4轮/50min), 已4次催办manager仍未派发worker_builder",
        )

        snap = local_facts.get_status("auto_ops")

        assert snap is not None
        assert "watchdog持续缺失" in snap["task"]


def test_get_status_suppresses_stale_watchdog_repair_unread_after_recovery():
    with isolated_env(), attr_patch(local_facts, _runtime_watchdog_recovered=lambda: True):
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_builder",
                "待命",
                "等待下一步",
            )
            local_facts.append_message(
                "worker_builder",
                "manager",
                "watchdog 未启动(no pid file)，请排查并恢复 router/watchdog 兜底保障。",
                priority="高",
            )

        snap = local_facts.get_status("worker_builder")

        assert snap is not None
        assert snap["status"] == "待命"
        assert "watchdog 未启动" not in snap["task"]


def test_get_status_suppresses_stale_watchdog_repair_read_without_ack_after_recovery():
    with isolated_env(), attr_patch(local_facts, _runtime_watchdog_recovered=lambda: True):
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_builder",
                "待命",
                "等待下一步",
            )
            msg_id = local_facts.append_message(
                "worker_builder",
                "manager",
                "watchdog 未启动(no pid file)，请排查并恢复 router/watchdog 兜底保障。",
                priority="高",
            )
            assert local_facts.mark_read(msg_id)

        snap = local_facts.get_status("worker_builder")

        assert snap is not None
        assert snap["status"] == "待命"
        assert "已读待确认" not in snap["task"]


def test_get_status_suppresses_watchdog_repair_read_after_later_closeout_even_if_runtime_flaps():
    with isolated_env(), attr_patch(local_facts, _runtime_watchdog_recovered=lambda: False):
        local_facts.upsert_status(
            "worker_builder",
            "待命",
            "等待下一步",
        )
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

        snap = local_facts.get_status("worker_builder")

        assert snap is not None
        assert snap["status"] == "待命"
        assert "已读待确认" not in snap["task"]


def test_get_status_suppresses_old_builder_runtime_course_read_after_closeout():
    with isolated_env():
        local_facts.upsert_status(
            "worker_builder",
            "进行中",
            "initializing",
        )
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

        snap = local_facts.get_status("worker_builder")

        assert snap is not None
        assert "已读待确认" not in snap["task"]


def test_get_status_keeps_fresh_qbank_process_surface_active():
    with isolated_env():
        current_now = 2_000_000
        with attr_patch(local_facts, now_ms=lambda: current_now):
            local_facts.upsert_status(
                "worker_qbank",
                "进行中",
                "QBank manifest 盘点：Physics 0625 manifest 不完整，继续分析。",
            )
            local_facts.append_log(
                "worker_qbank",
                "say",
                "QBank manifest 盘点仍在推进，当前核对 Physics 0625 batch-02+。",
            )

        fresh_now = current_now + 2 * 60 * 1000
        with attr_patch(local_facts, now_ms=lambda: fresh_now):
            snap = local_facts.get_status("worker_qbank")

        assert snap is not None
        assert snap["status"] == "进行中"
        assert not snap["task"].startswith("外显陈旧：")


def test_get_status_projects_idle_agent_with_new_unread_task_as_waiting_acceptance():
    with isolated_env():
        local_facts.upsert_status("review_course", "待命", "Economics 0455 PASS。待新任务。")
        local_facts.append_message(
            "review_course",
            "manager",
            "送审 Business Studies 0450 T-10：请正式复核并返回 verdict",
            priority="高",
        )
        snap = local_facts.get_status("review_course")
        assert snap is not None
        assert snap["status"] == "待接单"
        assert "Business Studies 0450" in snap["task"]
        assert "Economics 0455 PASS" not in snap["task"]


def test_get_status_projects_waiting_followup_text_as_idle_not_in_progress():
    with isolated_env():
        local_facts.upsert_status(
            "worker_qbank",
            "进行中",
            "题库验证方案已交付，待命后续去重+补manifest",
        )
        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "待命"
        assert "待命后续" in snap["task"]


def test_log_append_then_list():
    with isolated_env():
        local_facts.append_log("a", "info", "first")
        local_facts.append_log("a", "info", "second", ref="REF-1")
        local_facts.append_log("b", "info", "other agent")
        rows = local_facts.list_logs("a")
        assert len(rows) == 2
        assert rows[0]["content"] == "first"
        assert rows[1]["content"] == "second"
        assert rows[1]["ref"] == "REF-1"


def test_log_returns_empty_when_no_log_file():
    with isolated_env():
        # never appended → no log file
        assert local_facts.list_logs("a") == []


def test_facts_dir_uses_state_dir_env():
    with isolated_env() as tmp:
        facts_dir = tmp / "state" / "facts"
        local_facts.append_message("a", "b", "x")
        assert facts_dir.exists()
        assert (facts_dir / "inbox.json").exists()


# ── heartbeat ────────────────────────────────────────────────────


def test_touch_heartbeat_records_now_for_agent():
    with isolated_env():
        local_facts.touch_heartbeat("worker")
        ts = local_facts.get_heartbeat("worker")
        assert ts is not None and ts > 0


def test_touch_heartbeat_overwrites_previous_timestamp():
    with isolated_env():
        local_facts.touch_heartbeat("w")
        first = local_facts.get_heartbeat("w")
        time.sleep(0.01)
        local_facts.touch_heartbeat("w")
        second = local_facts.get_heartbeat("w")
        assert second >= first


def test_touch_heartbeat_skips_blank_agent():
    with isolated_env():
        local_facts.touch_heartbeat("")
        assert local_facts.all_heartbeats() == {}


def test_all_heartbeats_returns_each_recorded_agent():
    with isolated_env():
        local_facts.touch_heartbeat("alice")
        local_facts.touch_heartbeat("bob")
        beats = local_facts.all_heartbeats()
        assert set(beats) == {"alice", "bob"}


def test_get_heartbeat_returns_none_for_unknown_agent():
    with isolated_env():
        assert local_facts.get_heartbeat("ghost") is None


def test_touch_heartbeat_swallows_oserror_so_callers_dont_die():
    """REGRESSION: touch_heartbeat is called early in send/inbox/log/say/
    status. A disk-full OSError there shouldn't kill those commands —
    heartbeat is auxiliary, the underlying message/log/status update is
    the actual user intent. Verify the swallow path."""
    import io
    import contextlib
    from helpers import attr_patch
    from eduflow.store import local_facts as lf

    def boom(*a, **kw):
        raise OSError("[Errno 28] No space left on device")

    err = io.StringIO()
    with isolated_env(), attr_patch(lf, write_json=boom), \
            contextlib.redirect_stderr(err):
        # Should NOT raise — caller continues
        local_facts.touch_heartbeat("alice")

    # Warning was logged so the operator knows heartbeat is broken
    assert "heartbeat write failed" in err.getvalue()
    assert "alice" in err.getvalue()


# ── external-status-staleness (heartbeat-aware) ───────────────────


def _stale_project(agent: str) -> dict | None:
    """Helper: build a status row and run it through the stale projection."""
    row = local_facts.get_status(agent)
    if row is None:
        return None
    return local_facts._project_facts_process_visibility_stale(row)


def test_heartbeat_prevents_stale_flag_when_no_process_log():
    """Worker only calls `eduflow status` (which touches heartbeat).
    No say/task_completed log exists.  Heartbeat is fresh → no stale flag."""
    with isolated_env():
        local_facts.touch_heartbeat("worker_course")
        local_facts.upsert_status(
            "worker_course", "进行中", "IGCSE Chemistry 0620 — QA generation"
        )
        result = _stale_project("worker_course")
        assert result is None  # fresh heartbeat → not stale


def test_heartbeat_fresh_keeps_status_not_stale_even_after_long_gap():
    """Status was set 30 min ago (old updated_at) but heartbeat is fresh.
    Agent is alive (calling other eduflow CLIs) — should NOT show stale."""
    with isolated_env():
        now_ms = local_facts.now_ms()
        old = now_ms - 30 * 60 * 1000  # 30 minutes ago
        local_facts.upsert_status(
            "worker_builder", "进行中", "watchdog config tweak"
        )
        # Overwrite updated_at to simulate old status row
        local_facts.touch_heartbeat("worker_builder")  # fresh heartbeat
        from eduflow.store.local_facts import (
            _status_file, read_json, write_json, _locked,
        )
        with _locked():
            data = read_json(_status_file(), {"agents": {}})
            data["agents"]["worker_builder"]["updated_at"] = old
            write_json(_status_file(), data)

        result = _stale_project("worker_builder")
        # Heartbeat is fresh → no stale despite old updated_at
        assert result is None


def test_stale_flag_applies_when_heartbeat_also_old():
    """Both status updated_at AND heartbeat are >10 min old → stale."""
    with isolated_env():
        local_facts.touch_heartbeat("worker_course")
        local_facts.upsert_status(
            "worker_course", "进行中", "IGCSE Biology 0610 Batch 5"
        )
        # Overwrite heartbeat to be 20 min old
        from eduflow.store.local_facts import (
            _heartbeat_file, _status_file, read_json, write_json, _locked,
        )
        old_hb = local_facts.now_ms() - 20 * 60 * 1000
        with _locked():
            write_json(_heartbeat_file(), {"worker_course": old_hb})
        # Also overwrite updated_at to be old
        with _locked():
            data = read_json(_status_file(), {"agents": {}})
            data["agents"]["worker_course"]["updated_at"] = old_hb
            write_json(_status_file(), data)

        result = _stale_project("worker_course")
        assert result is not None
        assert "外显陈旧" in result["task"]
