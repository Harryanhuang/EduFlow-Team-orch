"""Tests for `eduflow team` and `eduflow workspace` (read-side)."""
from __future__ import annotations

import json

from helpers import attr_patch, isolated_env, run_cli
from eduflow.store import local_facts


# ── team ──────────────────────────────────────────────────────────


def test_team_empty_when_no_agents():
    with isolated_env():
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        assert "no agents have reported status yet" in out


def test_team_lists_all_agents_sorted_by_name():
    with isolated_env():
        run_cli(["status", "worker_b", "进行中", "doing b"])
        run_cli(["status", "worker_a", "已完成", "done a"])
        run_cli(["status", "worker_c", "阻塞", "stuck", "no api key"])
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 3
        # alphabetical
        assert lines[0].startswith("worker_a")
        assert lines[1].startswith("worker_b")
        assert lines[2].startswith("worker_c")
        # blocker shown for worker_c
        assert "⛔ no api key" in lines[2]


def test_team_appends_heartbeat_marker_when_recorded():
    with isolated_env():
        run_cli(["status", "agent", "进行中", "task"])
        # status command auto-touches heartbeat
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        assert "♥" in out


def test_team_shows_relative_age():
    with isolated_env():
        run_cli(["status", "agent", "进行中", "task"])
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        # latest write is < 1m ago
        assert "ago)" in out


def test_team_json_dumps_machine_readable_records():
    """`--json` emits a list[dict] consumable by CI / smoke conductors
    / peer agents — no emoji, no relative timestamps to parse."""
    with isolated_env():
        run_cli(["status", "worker_a", "进行中", "task A"])
        run_cli(["status", "worker_b", "已完成", "task B", "blocked on review"])
        rc, out, _ = run_cli(["team", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 2
        # Sorted alphabetically: worker_a before worker_b
        assert data[0]["agent"] == "worker_a"
        assert data[0]["status"] == "进行中"
        assert data[0]["task"] == "task A"
        assert data[0]["heartbeat_ms"] > 0  # status command touched it
        assert data[1]["agent"] == "worker_b"
        assert data[1]["blocker"] == "blocked on review"


def test_team_prefers_newer_workspace_fact_over_stale_status_task():
    with isolated_env():
        local_facts.upsert_status("review_course", "进行中", "T-7 Batch 4 通过，待后续批次")
        local_facts.append_log(
            "review_course",
            "say",
            "T-7 Accounting Batch 5 复核 verdict：【通过】。",
        )
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        assert "Batch 5" in out
        assert "Batch 4 通过" not in out


def test_team_keeps_read_unacked_task_ahead_of_old_verdict_fact():
    with isolated_env():
        with attr_patch(local_facts, now_ms=lambda: 500):
            local_facts.upsert_status(
                "review_course",
                "待命",
                "T-10 Business Studies 0450 PASS",
            )
        with attr_patch(local_facts, now_ms=lambda: 1000):
            local_facts.append_log(
                "review_course",
                "say",
                "T-10 Business Studies 0450 复检结果：Verdict: PASS — 可发布。",
            )
        with attr_patch(local_facts, now_ms=lambda: 2000):
            msg_id = local_facts.append_message(
                "review_course",
                "manager",
                "老板要求：对 qbank dry-run 去重方案做独立复核 gate。",
                priority="高",
            )
        assert local_facts.mark_read(msg_id)

        rc, out, _ = run_cli(["team", "--json"])
        assert rc == 0
        row = json.loads(out)[0]
        assert row["status"] == "已读待确认"
        assert "qbank dry-run 去重方案" in row["task"]
        assert "Business Studies 0450" not in row["task"]


def test_team_projects_weak_ready_status_from_newer_log():
    with isolated_env():
        local_facts.upsert_status("worker_builder", "进行中", "ready")
        local_facts.append_log(
            "worker_builder",
            "say",
            "收到运行态更新：当前 runtime/CLI/收发消息均正常，worker_builder 已同步该状态并保持待命。",
        )
        rc, out, _ = run_cli(["team"])
        assert rc == 0
        assert "worker_builder" in out
        assert "保持待命" in out
        assert "ready" not in out


def test_team_json_empty_returns_empty_list_not_message():
    """When no agents have reported, JSON mode emits `[]`, not the
    "no agents" friendly text — consumers can iterate without
    string-checking."""
    with isolated_env():
        rc, out, _ = run_cli(["team", "--json"])
        assert rc == 0
        assert json.loads(out) == []


def test_team_filters_flag_shaped_status_rows_by_default():
    team = {"session": "S", "agents": {"worker": {}}}
    with isolated_env(team=team):
        local_facts.upsert_status("worker", "待命", "ready")
        local_facts.upsert_status("--help", "已停止", "fired")
        rc, out, _ = run_cli(["team", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert [r["agent"] for r in data] == ["worker"]


def test_team_current_filters_status_rows_not_in_current_team():
    team = {"session": "S", "agents": {"worker": {}}}
    with isolated_env(team=team):
        local_facts.upsert_status("worker", "待命", "ready")
        local_facts.upsert_status("retired_worker", "已停止", "retired")
        rc, out, _ = run_cli(["team", "--json", "--current"])
        assert rc == 0
        data = json.loads(out)
        assert [r["agent"] for r in data] == ["worker"]


def test_team_all_includes_legacy_status_rows_for_audit():
    team = {"session": "S", "agents": {"worker": {}}}
    with isolated_env(team=team):
        local_facts.upsert_status("worker", "待命", "ready")
        local_facts.upsert_status("--help", "已停止", "fired")
        local_facts.upsert_status("retired_worker", "已停止", "retired")
        rc, out, _ = run_cli(["team", "--json", "--all"])
        assert rc == 0
        data = json.loads(out)
        assert [r["agent"] for r in data] == ["--help", "retired_worker", "worker"]


# ── workspace ─────────────────────────────────────────────────────


def test_workspace_empty_returns_zero_with_message():
    with isolated_env():
        rc, out, _ = run_cli(["workspace", "nobody"])
        assert rc == 0
        assert "nobody: no log entries" in out


def test_workspace_lists_recent_log_entries():
    with isolated_env():
        run_cli(["log", "a", "info", "first"])
        run_cli(["log", "a", "task", "second", "TASK-1"])
        run_cli(["log", "b", "info", "should not appear"])
        rc, out, _ = run_cli(["workspace", "a"])
        assert rc == 0
        assert "a: last 2 log entries" in out
        assert "first" in out and "second" in out
        assert "(TASK-1)" in out
        assert "should not appear" not in out


def test_team_and_workspace_surface_auto_ops_min_ack():
    with isolated_env():
        msg_id = local_facts.append_message(
            "auto_ops", "manager", "当前卡在 review ACK", priority="高"
        )
        local_facts.record_auto_ops_min_ack("auto_ops", msg_id, "当前卡在 review ACK")
        rc, team_out, _ = run_cli(["team"])
        assert rc == 0
        assert "auto_ops" in team_out
        assert "当前卡在 review ACK" in team_out
        rc, workspace_out, _ = run_cli(["workspace", "auto_ops"])
        assert rc == 0
        assert "最小 ACK" in workspace_out


def test_team_and_workspace_surface_worker_qbank_followup():
    with isolated_env():
        msg_id = local_facts.append_message(
            "worker_qbank", "manager", "请基于 Batch 7 最新通过结果继续做 qbank follow-up", priority="高"
        )
        local_facts.record_worker_qbank_followup(
            "worker_qbank", msg_id, "请基于 Batch 7 最新通过结果继续做 qbank follow-up"
        )
        rc, team_out, _ = run_cli(["team"])
        assert rc == 0
        assert "worker_qbank" in team_out
        assert "Batch 7" in team_out
        rc, workspace_out, _ = run_cli(["workspace", "worker_qbank"])
        assert rc == 0
        assert "最小跟进" in workspace_out


def test_workspace_limit_caps_returned_rows():
    with isolated_env():
        for i in range(5):
            run_cli(["log", "a", "info", f"entry-{i}"])
        rc, out, _ = run_cli(["workspace", "a", "--limit", "2"])
        assert rc == 0
        assert "last 2 log entries" in out
        assert "entry-3" in out and "entry-4" in out
        assert "entry-0" not in out


def test_workspace_invalid_limit_returns_one():
    with isolated_env():
        rc, _, err = run_cli(["workspace", "a", "--limit", "abc"])
        assert rc == 1
        assert "usage:" in err


def test_workspace_zero_args_returns_one():
    rc, _, err = run_cli(["workspace"])
    assert rc == 1
    assert "usage:" in err


# ── store helper ───────────────────────────────────────────────────


def test_list_all_statuses_returns_sorted_rows():
    with isolated_env():
        local_facts.upsert_status("z", "进行中", "z task")
        local_facts.upsert_status("a", "已完成", "a task")
        rows = local_facts.list_all_statuses()
        assert [r["agent"] for r in rows] == ["a", "z"]


def test_list_all_statuses_empty_when_no_writes():
    with isolated_env():
        assert local_facts.list_all_statuses() == []
