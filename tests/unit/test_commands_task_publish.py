"""Tests for `eduflow task-publish` loop wrapper."""
from __future__ import annotations

from helpers import attr_patch, env_patch, isolated_env, run_cli
from eduflow.commands import task as task_cmd
from eduflow.runtime import paths


def test_task_publish_once_delegates_to_publish_run():
    calls = []

    def fake_task_main(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(task_cmd, main=fake_task_main):
        rc, out, _ = run_cli(["task-publish", "--once", "--to", "user"])
        assert rc == 0
        assert out == ""
    assert calls == [["publish-run", "--to", "user"]]


def test_task_publish_once_threads_send_and_advance():
    calls = []

    def fake_task_main(argv):
        calls.append(list(argv))
        return 0

    with isolated_env(), attr_patch(task_cmd, main=fake_task_main):
        rc, _, _ = run_cli(["task-publish", "--once", "--send", "--advance"])
        assert rc == 0
    assert calls == [["publish-run", "--to", "user", "--send", "--advance"]]


def test_task_publish_loop_defaults_to_send_and_advance():
    calls = []

    def fake_task_main(argv):
        calls.append(list(argv))
        raise KeyboardInterrupt

    with isolated_env(), attr_patch(task_cmd, main=fake_task_main):
        rc, out, _ = run_cli(["task-publish"])
        assert rc == 0
        assert "send=true advance=true" in out
        assert "task-publish stopped" in out
    assert calls == [["publish-run", "--to", "user", "--send", "--advance"]]


def test_task_publish_rejects_advance_without_send():
    with isolated_env():
        rc, _, err = run_cli(["task-publish", "--once", "--advance"])
        assert rc == 1
        assert "--advance requires --send" in err


def test_task_publish_bad_interval_returns_usage_error():
    with isolated_env():
        rc, _, err = run_cli(["task-publish", "--interval-seconds", "abc"])
        assert rc == 1
        assert "usage: eduflow task-publish" in err


def test_task_publish_loop_uses_tunable_interval_and_stops_on_ctrl_c():
    calls = []
    sleeps = []

    def fake_task_main(argv):
        calls.append(list(argv))
        return 0

    def fake_sleep(seconds):
        sleeps.append(seconds)
        raise KeyboardInterrupt

    with isolated_env() as tmp, \
            attr_patch(task_cmd, main=fake_task_main), \
            attr_patch(__import__("time"), sleep=fake_sleep):
        (tmp / "eduflow.toml").write_text(
            "[task_publish]\ninterval_seconds = 7\n",
            encoding="utf-8",
        )
        with env_patch(EDUFLOW_CONFIG_FILE=str(tmp / "eduflow.toml")):
            rc, out, _ = run_cli(["task-publish", "--send"])
            assert rc == 0
            assert "interval=7s" in out
            assert "task-publish stopped" in out
    assert calls == [["publish-run", "--to", "user", "--send", "--advance"]]
    assert sleeps == [7.0]


def test_task_publish_loop_writes_and_releases_pid_file():
    calls = []

    def fake_task_main(argv):
        calls.append(list(argv))
        return 0

    def fake_sleep(seconds):
        raise KeyboardInterrupt

    with isolated_env(), \
            attr_patch(task_cmd, main=fake_task_main), \
            attr_patch(__import__("time"), sleep=fake_sleep):
        rc, out, _ = run_cli(["task-publish", "--send"])
        assert rc == 0
        assert "task-publish stopped" in out
        # PID file survives release; health/watchdog can see the stale PID
        assert paths.task_publish_pid_file().exists()
