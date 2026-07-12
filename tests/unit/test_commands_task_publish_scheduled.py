"""P3: task-publish scheduler integration tests.

Verifies that the long-running task-publish loop calls the scheduler
 tick in an isolated try/except and that scheduler failures do not
break normal task publish or its cursor.
"""
from __future__ import annotations

from helpers import attr_patch, isolated_env, run_cli
from eduflow.commands import task as task_cmd
from eduflow.runtime import paths
from eduflow.scheduling import engine


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def test_task_publish_once_calls_scheduler_tick():
    scheduler_calls = []
    task_calls = []

    def fake_scheduler_tick(now_ms):
        scheduler_calls.append(now_ms)
        return {"occurrences_created": []}

    def fake_task_main(argv):
        task_calls.append(list(argv))
        return 0

    with isolated_env(), \
            attr_patch(engine, scheduler_tick=fake_scheduler_tick), \
            attr_patch(task_cmd, main=fake_task_main):
        rc, out, _ = run_cli(["task-publish", "--once", "--to", "user"])
        assert rc == 0
    assert len(scheduler_calls) == 1
    assert task_calls == [["publish-run", "--to", "user"]]


def test_task_publish_continues_when_scheduler_tick_raises():
    task_calls = []

    def fake_scheduler_tick(now_ms):
        raise ValueError("scheduler boom")

    def fake_task_main(argv):
        task_calls.append(list(argv))
        return 0

    with isolated_env(), \
            attr_patch(engine, scheduler_tick=fake_scheduler_tick), \
            attr_patch(task_cmd, main=fake_task_main):
        rc, out, err = run_cli(["task-publish", "--once", "--to", "user"])
        assert rc == 0
        assert "scheduler" in err.lower() or "scheduler" in out.lower()
    assert task_calls == [["publish-run", "--to", "user"]]


def test_task_publish_scheduler_failure_does_not_affect_task_publish_cursor():
    def fake_scheduler_tick(now_ms):
        raise ValueError("scheduler boom")

    def fake_task_main(argv):
        return 0

    with isolated_env(), \
            attr_patch(engine, scheduler_tick=fake_scheduler_tick), \
            attr_patch(task_cmd, main=fake_task_main):
        rc, _, _ = run_cli(["task-publish", "--once", "--to", "user"])
        assert rc == 0
    assert not paths.task_publish_cursor_file().exists()


def test_task_publish_loop_calls_scheduler_tick_each_cycle():
    scheduler_calls = []
    task_calls = []
    sleeps = []

    def fake_scheduler_tick(now_ms):
        scheduler_calls.append(now_ms)
        return {"occurrences_created": []}

    def fake_task_main(argv):
        task_calls.append(list(argv))
        return 0

    def fake_sleep(seconds):
        sleeps.append(seconds)
        raise KeyboardInterrupt

    with isolated_env(), \
            attr_patch(engine, scheduler_tick=fake_scheduler_tick), \
            attr_patch(task_cmd, main=fake_task_main), \
            attr_patch(__import__("time"), sleep=fake_sleep):
        rc, out, _ = run_cli(["task-publish", "--send"])
        assert rc == 0
    assert len(scheduler_calls) == 1
    assert len(task_calls) == 1
