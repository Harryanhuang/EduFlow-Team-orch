"""T-104: task archive (A physical move + B soft mark) — unit tests.

Covers the four contract pieces the manager named:
  1. archive_dry_run    — plans without writing
  2. archive_real_move  — physically moves + soft-marks archived=true
  3. list_default_filter — list_tasks hides archived by default
  4. include_archived_flag — explicit opt-in shows them again
Plus a watchdog daily-archive tick test (idempotent same-day, runs once).
"""
from __future__ import annotations

import contextlib
import datetime
import json
from pathlib import Path
from unittest import mock

from helpers import isolated_env, run_cli

from eduflow.runtime import paths
from eduflow.store import tasks as task_store


# ── helpers ───────────────────────────────────────────────────────────

@contextlib.contextmanager
def _noop_cm():
    yield


def _state_dir_of(outer_tmp: Path) -> Path:
    """isolated_env() pins EDUFLOW_STATE_DIR to <outer_tmp>/state."""
    return outer_tmp / "state"


def _seed_terminal_tasks(outer_tmp: Path, *, n: int = 3,
                         status: str = "delivered") -> list[str]:
    """Write N terminal tasks straight into the isolated state dir."""
    state = _state_dir_of(outer_tmp)
    state.mkdir(parents=True, exist_ok=True)
    data: dict = {"tasks": [], "_meta": {"last_id": 0}}
    ids: list[str] = []
    for i in range(n):
        tid = f"T-{i + 1}"
        data["tasks"].append({
            "id": tid,
            "title": f"terminal task {i + 1}",
            "description": "",
            "assignee": "worker_test",
            "creator": "test",
            "status": status,
            "created_at": 1_000_000_000_000,
            "updated_at": 1_000_000_000_000,
            "completed_at": 1_000_000_000_000,  # far past → eligible
        })
        data["_meta"]["last_id"] = i + 1
        ids.append(tid)
    (state / "tasks.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    return ids


# ── 1. dry-run: plans, doesn't write ─────────────────────────────────

def test_archive_dry_run_does_not_mutate(tmp_path: Path):
    with isolated_env() as outer:
        _seed_terminal_tasks(outer, n=3, status="delivered")
        state = _state_dir_of(outer)
        with mock.patch.object(task_store, "_locked", lambda: _noop_cm()):
            summary = task_store.archive_tasks(older_than_days=90, dry_run=True)

        assert summary["dry_run"] is True
        assert summary["archived_count"] == 3
        assert sorted(summary["task_ids"]) == ["T-1", "T-2", "T-3"]
        after = json.loads((state / "tasks.json").read_text(encoding="utf-8"))
        assert [t["id"] for t in after["tasks"]] == ["T-1", "T-2", "T-3"]
        assert not (state / "archive").exists()


# ── 2. real move: physical JSONL slice + soft mark + drop from tasks ──

def test_archive_real_move_physical_and_soft(tmp_path: Path):
    with isolated_env() as outer:
        _seed_terminal_tasks(outer, n=2, status="delivered")
        state = _state_dir_of(outer)
        archive_dir = state / "archive"
        with mock.patch.object(task_store, "_locked", lambda: _noop_cm()):
            summary = task_store.archive_tasks(older_than_days=90, dry_run=False)

        assert summary["archived_count"] == 2
        assert summary["by_month"]  # at least one month bucket
        slices = list(archive_dir.glob("tasks-*.jsonl"))
        assert len(slices) == 1, f"expected 1 slice, got {slices}"
        lines = [ln for ln in slices[0].read_text(encoding="utf-8").splitlines()
                 if ln.strip()]
        assert len(lines) == 2
        parsed = [json.loads(ln) for ln in lines]
        assert {r["id"] for r in parsed} == {"T-1", "T-2"}
        for r in parsed:
            assert r["archived"] is True
            assert r["archived_at"]
        after = json.loads((state / "tasks.json").read_text(encoding="utf-8"))
        assert after["tasks"] == []


# ── 3. list_tasks default filter hides archived ──────────────────────

def test_list_tasks_default_filter_hides_archived(tmp_path: Path):
    with isolated_env() as outer:
        _seed_terminal_tasks(outer, n=2, status="delivered")
        state = _state_dir_of(outer)
        data = json.loads((state / "tasks.json").read_text(encoding="utf-8"))
        data["tasks"][0]["archived"] = True  # soft mark only, no move
        (state / "tasks.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

        assert {t["id"] for t in task_store.list_tasks()} == {"T-2"}
        assert {t["id"] for t in task_store.list_tasks(include_archived=True)} == {
            "T-1", "T-2"
        }


# ── 4. CLI `--include-archived` flag wires through ───────────────────

def test_cli_list_include_archived_flag(tmp_path: Path):
    with isolated_env() as outer:
        _seed_terminal_tasks(outer, n=1, status="已完成")  # legacy vocabulary
        state = _state_dir_of(outer)
        data = json.loads((state / "tasks.json").read_text(encoding="utf-8"))
        data["tasks"][0]["archived"] = True
        (state / "tasks.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

        rc, out_default, _ = run_cli(["task", "list"])
        assert rc == 0
        assert "no matching tasks" in out_default

        rc, out_all, _ = run_cli(["task", "list", "--include-archived"])
        assert rc == 0
        assert "T-1" in out_all
        assert "1 tasks" in out_all


# ── 5. watchdog daily-archive state machine ──────────────────────────

def test_daily_archive_state_machine_idempotent(tmp_path: Path):
    """watchdog._maybe_daily_archive: disabled → skip; enabled + past
    local_hour → run + record; second call same day → skip; before
    local_hour → skip even if not yet run.
    """
    from eduflow.commands import watchdog as wd

    # Build a fake facts dir that lives INSIDE the isolated state, so any
    # helper that walks paths.facts_dir() finds our config.
    with isolated_env() as outer:
        facts = _state_dir_of(outer) / "facts"
        facts.mkdir(parents=True, exist_ok=True)

        # disabled first → no run regardless of hour
        (facts / "archive-schedule.json").write_text(json.dumps({
            "enabled": False, "interval": "daily",
            "older_than_days": 90, "local_hour": 3,
        }), encoding="utf-8")
        (facts / "archive-last-run.json").write_text("{}", encoding="utf-8")

        today_4am = datetime.datetime.now().replace(
            hour=4, minute=0, second=0, microsecond=0
        ).timestamp()

        # paths is imported by watchdog at function-call time (inside the
        # function), so monkey-patching the module's `paths` reference is
        # enough — no rebind needed.
        with mock.patch.object(wd, "paths", paths), \
             mock.patch("eduflow.store.tasks.archive_tasks",
                        return_value={"archived_count": 0, "by_month": {}}):
            assert wd._maybe_daily_archive(today_4am) is False  # disabled

            (facts / "archive-schedule.json").write_text(json.dumps({
                "enabled": True, "interval": "daily",
                "older_than_days": 90, "local_hour": 3,
            }), encoding="utf-8")
            assert wd._maybe_daily_archive(today_4am) is True   # first run
            assert wd._maybe_daily_archive(today_4am) is False  # same day

            before_hour = datetime.datetime.now().replace(
                hour=2, minute=30, second=0, microsecond=0
            ).timestamp()
            (facts / "archive-last-run.json").write_text("{}", encoding="utf-8")
            assert wd._maybe_daily_archive(before_hour) is False  # before hour
