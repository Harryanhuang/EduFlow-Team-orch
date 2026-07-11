"""P0: 不可回归契约 — D scheduler 域不得改变 T 任务语义。

本包不实现 scheduler，只把现有 T 任务系统的真实行为锁定为契约，
供 P1-P9 作为隔离基线。
"""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.runtime import paths
from eduflow.store import tasks


# ── T-ID / 状态机契约 ───────────────────────────────────────────────


def test_ordinary_task_still_generates_t_id():
    with isolated_env():
        tid = tasks.create("worker", "do thing")
        assert tid == "T-1"
        row = tasks.get(tid)
        assert row is not None
        assert row["status"] == "待处理"


def test_task_ids_increment_and_do_not_reuse():
    with isolated_env():
        assert tasks.create("w1", "first") == "T-1"
        assert tasks.create("w2", "second") == "T-2"
        assert tasks.create("w3", "third") == "T-3"


def test_task_state_machine_rejects_invalid_status():
    with isolated_env():
        tid = tasks.create("w", "x")
        try:
            tasks.update(tid, status="not-a-status")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for invalid status")


# ── JSON / lock 模式契约 ────────────────────────────────────────────


def test_tasks_json_shape_has_meta_and_list():
    with isolated_env():
        tasks.create("w", "x")
        raw = paths.state_dir() / "tasks.json"
        assert raw.exists(), "tasks.json must be created on first write"
        data = json.loads(raw.read_text(encoding="utf-8"))
        assert "_meta" in data
        assert "tasks" in data
        assert data["_meta"].get("last_id") == 1
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "T-1"


def test_tasks_json_uses_separate_lock_file():
    with isolated_env():
        tasks.create("w", "x")
        lock_file = paths.state_dir() / "tasks.lock"
        assert lock_file.exists(), "tasks.lock must accompany tasks.json"


# ── publish cursor 契约 ─────────────────────────────────────────────


def test_task_publish_cursor_file_is_private_to_task_publish():
    with isolated_env():
        cursor_path = paths.task_publish_cursor_file()
        assert "task-publish" in cursor_path.name, (
            "normal publish cursor must be named task-publish.cursor"
        )
        # cursor 初始不存在，scheduler 不能复用它；
        # scheduler 必须有自己独立的 cursor / heartbeat 文件。
        assert not cursor_path.exists()


def test_task_publish_cursor_format_is_event_based():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course", "IGCSE Physics 0625 Batch 1",
            stage="curriculum", owner="worker_course", creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        # publish-scan --advance 推进普通任务 publish cursor
        rc, out, _ = run_cli([
            "task", "publish-scan", "--to", "user", "--include-silent", "--advance",
        ])
        assert rc == 0
        assert "advanced task publish cursor" in out
        cursor_path = paths.task_publish_cursor_file()
        assert cursor_path.exists()
        data = json.loads(cursor_path.read_text(encoding="utf-8"))
        assert "event_id" in data
        assert "created_at" in data
        # scheduler 的 cursor 语义不同，不能使用同一个文件。


# ── scheduler import 隔离契约 ────────────────────────────────────────


def test_scheduler_import_does_not_consume_task_ids():
    with isolated_env():
        tid1 = tasks.create("w", "first")
        # P0  scheduler 模块可能尚不存在；导入失败不得产生副作用，
        # 若已存在则导入过程不得分配 T-ID。
        try:
            from eduflow.scheduling import engine  # noqa: F401
        except ImportError:
            pass
        tid2 = tasks.create("w", "second")
        assert tid1 == "T-1"
        assert tid2 == "T-2"


# ── manager-panel 入口契约 ──────────────────────────────────────────


def test_manager_panel_entry_still_works():
    with isolated_env():
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "manager panel" in out
        assert "== Workflow Drive ==" in out
        assert "== Task Buckets ==" in out
