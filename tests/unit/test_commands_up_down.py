"""Tests for `eduflow up` and `eduflow down` — composite lifecycle."""
from __future__ import annotations

import contextlib
import os
import subprocess
import sys

from helpers import attr_patch, isolated_env, run_cli, tmux_patch
from eduflow.runtime import paths, watchdog


@contextlib.contextmanager
def _fake_tmux(session_alive=False):
    state = {"session_alive": session_alive, "session_killed": False, "calls": []}

    def has_session(s):
        state["calls"].append(("has_session", s))
        return state["session_alive"]

    def kill_session(s):
        state["calls"].append(("kill_session", s))
        state["session_alive"] = False
        state["session_killed"] = True
        return True

    with tmux_patch(has_session=has_session, kill_session=kill_session):
        yield state


class _FakePopenProc:
    """subprocess.Popen-shaped fake good enough for both `watchdog.respawn`
    (which discards the proc) and `watchdog.list_orphan_pids` →
    `subprocess.run` (which uses Popen as context manager and calls
    poll/communicate/wait/kill on the result). Round-65 round-67: hoisted
    to module level so `_fake_popen` and `silent_popen` share one
    Popen-contract surface — fixing a subprocess-internal contract change
    only needs touching one class."""

    def __init__(self, argv):
        self.argv = argv
        # subprocess.run reads `.args` on the Popen result internally
        # (e.g. when constructing CompletedProcess). Without it any
        # subprocess.run call routed through this fake AttributeError's.
        self.args = argv
        self.returncode = 0
        self.stdout = ""
        self.stderr = ""

    def __enter__(self): return self
    def __exit__(self, *exc): return False
    def communicate(self, *a, **kw): return (self.stdout, self.stderr)
    def wait(self, *a, **kw): return self.returncode
    def poll(self): return self.returncode
    def kill(self): return None


@contextlib.contextmanager
def _fake_popen():
    """Replace subprocess.Popen used by up.py."""
    calls = []
    router_cmd = [sys.executable, "-m", "eduflow.cli", "router"]
    task_publish_cmd = [sys.executable, "-m", "eduflow.cli", "task-publish"]
    watchdog_cmd = [sys.executable, "-m", "eduflow.cli", "watchdog"]

    def fake_popen(argv, *args, **kwargs):
        calls.append(list(argv))
        # Simulate the daemon writing its pid file
        if list(argv[:4]) == router_cmd:
            paths.ensure_state_dir()
            paths.router_pid_file().write_text("12345", encoding="utf-8")
        elif list(argv[:4]) == task_publish_cmd:
            paths.ensure_state_dir()
            paths.task_publish_pid_file().write_text("12347", encoding="utf-8")
        elif list(argv[:4]) == watchdog_cmd:
            paths.ensure_state_dir()
            paths.watchdog_pid_file().write_text("12346", encoding="utf-8")
        return _FakePopenProc(argv)

    with attr_patch(subprocess, Popen=fake_popen):
        yield calls


def _fake_alive(answers):
    """Make watchdog.is_alive return successive scripted booleans."""
    iterator = iter(answers)

    def fake(spec, **kwargs):
        try:
            return next(iterator)
        except StopIteration:
            return False

    return attr_patch(watchdog, is_alive=fake)


# ── up ──────────────────────────────────────────────────────────


def test_up_starts_session_and_spawns_three_daemons():
    team = {"session": "S",
            "agents": {"manager": {"cli": "claude-code"}}}
    # capture_pane returns a string with claude-code's ready marker so
    # start.py's wake.wait_until_ready short-circuits without polling.
    extras = tmux_patch(
        new_session=lambda *a, **kw: True,
        new_window=lambda *a, **kw: True,
        spawn_agent=lambda *a, **kw: True,
        capture_pane=lambda target, lines=80: "bypass permissions on\n? for shortcuts\n>",
        inject=lambda *a, **kw: True,
    )
    with isolated_env(team=team), _fake_tmux(session_alive=False), \
            _fake_popen() as popen_calls, _fake_alive([False, False, False]), extras:
        rc, out, _ = run_cli(["up"])
        assert rc == 0
        assert "team up" in out
        assert [sys.executable, "-m", "eduflow.cli", "router"] in popen_calls
        assert [sys.executable, "-m", "eduflow.cli", "task-publish"] in popen_calls
        assert [sys.executable, "-m", "eduflow.cli", "watchdog"] in popen_calls


def test_up_skips_session_when_already_running():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=True), \
            _fake_popen() as popen_calls, _fake_alive([False, False, False]):
        rc, out, _ = run_cli(["up"])
        assert rc == 0
        assert "already running, skipping start" in out
        assert [sys.executable, "-m", "eduflow.cli", "router"] in popen_calls
        assert [sys.executable, "-m", "eduflow.cli", "task-publish"] in popen_calls


def test_up_skips_alive_daemons():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=True), \
            _fake_popen() as popen_calls, _fake_alive([True, True, True]):
        rc, out, _ = run_cli(["up"])
        assert rc == 0
        assert "router already alive" in out
        assert "task-publish already alive" in out
        assert "watchdog already alive" in out
        assert popen_calls == []


def test_up_help():
    rc, out, _ = run_cli(["up", "--help"])
    assert rc == 0
    assert "usage: eduflow up" in out


def test_up_returns_one_when_daemon_fast_fails_no_pid_file():
    """REGRESSION (round-62, real bug): a daemon that fast-fails at
    startup (e.g. chat_id missing in runtime_config) error_exits
    BEFORE writing its pid file. up.py used to print
    '⚠️ launched but no pid file yet' and STILL return 0, masking
    the boot failure. Now treats absence-of-pidfile as failure."""
    team = {"session": "S", "agents": {"manager": {}}}

    def silent_popen(argv, *args, **kwargs):
        # Popen succeeds but the daemon fast-fails — never writes a pid
        return _FakePopenProc(argv)

    with isolated_env(team=team), _fake_tmux(session_alive=True), \
            attr_patch(subprocess, Popen=silent_popen), \
            _fake_alive([False, False, False]):
        rc, out, err = run_cli(["up"])
    # Must return non-zero; warning explains what to do
    assert rc != 0, f"up rc={rc} should be non-zero on no-pid-file"
    combined = out + err
    assert "didn't write a pid file" in combined
    assert "fast-failed at startup" in combined


def test_up_warns_when_daemon_spawn_fails():
    """REGRESSION (round 7 D4): up was printing '✅ team up' even when
    router/watchdog Popen raised OSError (e.g. 'eduflow' not on PATH).
    Now must say 'team up with errors' and return non-zero."""
    team = {"session": "S", "agents": {"manager": {}}}

    def boom_popen(argv, *args, **kwargs):
        raise OSError(2, "No such file or directory: 'eduflow'")

    with isolated_env(team=team), _fake_tmux(session_alive=True), \
            attr_patch(subprocess, Popen=boom_popen), \
            _fake_alive([False, False, False]):
        rc, out, err = run_cli(["up"])
        assert rc != 0
        # Specific failure shown
        assert "failed to spawn" in (out + err)
        # Footer reflects the failure, NOT "✅ team up"
        assert "✅ team up" not in out
        assert "team up with errors" in out


# ── down ────────────────────────────────────────────────────────


def test_down_skips_when_no_pid_files_and_no_session():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=False):
        rc, out, _ = run_cli(["down"])
        assert rc == 0
        assert "router: no pid file" in out
        assert "task-publish: no pid file" in out
        assert "watchdog: no pid file" in out
        assert "tmux session S not running" in out


def test_down_kills_alive_pid_then_tmux():
    """When pid files point to a fake process, down should SIGTERM and clean up."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team) as tmp, _fake_tmux(session_alive=True) as tx:
        # Use *our* pid as the pid in the file — we know we're alive,
        # and we'll intercept os.kill so we don't actually die.
        my_pid = os.getpid()
        paths.ensure_state_dir()
        paths.router_pid_file().write_text(str(my_pid), encoding="utf-8")
        paths.task_publish_pid_file().write_text(str(my_pid), encoding="utf-8")
        paths.watchdog_pid_file().write_text(str(my_pid), encoding="utf-8")

        kill_calls = []
        check_calls = []

        def fake_kill(pid, sig):
            kill_calls.append((pid, sig))
            if sig == 0:
                check_calls.append(pid)
                # After SIGTERM, simulate process exit on second probe
                if check_calls.count(pid) >= 2:
                    raise ProcessLookupError()
                return None
            # SIGTERM — pretend it was delivered
            return None

        # Patch _read_cmdline to return a matching cmdline so the
        # entrypoint-drift safety check passes in the test environment.
        # In production, this reads /proc or ps output; here we fake it.
        from eduflow.runtime import watchdog as _wd
        with attr_patch(os, kill=fake_kill), \
             attr_patch(_wd, _read_cmdline=lambda pid: "python -m eduflow.cli router"):
            rc, out, _ = run_cli(["down"])
        assert rc == 0
        assert "router: pid" in out and "stopped" in out
        assert "task-publish: pid" in out
        assert "watchdog: pid" in out
        assert tx["session_killed"]
        assert not paths.router_pid_file().exists()
        assert not paths.task_publish_pid_file().exists()
        assert not paths.watchdog_pid_file().exists()


def test_down_handles_already_dead_pid():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        paths.router_pid_file().write_text("99999", encoding="utf-8")

        def fake_kill(pid, sig):
            raise ProcessLookupError()

        with attr_patch(os, kill=fake_kill):
            rc, out, _ = run_cli(["down"])
        assert rc == 0
        assert "already dead" in out
        assert not paths.router_pid_file().exists()


def test_down_help():
    rc, out, _ = run_cli(["down", "--help"])
    assert rc == 0
    assert "usage: eduflow down" in out


def test_down_handles_corrupt_pid_file():
    """A pid file with non-int garbage (e.g. partial write from a crash)
    should be removed and not blow up the down sequence — this is the
    pidlock.read_pid → None branch."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        paths.router_pid_file().write_text("garbage-not-an-int", encoding="utf-8")

        rc, out, _ = run_cli(["down"])
        assert rc == 0
        assert "corrupt pid file" in out
        assert not paths.router_pid_file().exists()


def test_down_returns_one_when_pid_refuses_to_die():
    """SIGTERM delivered, then SIGKILL escalation, then surface the
    warning — when both signals appear ineffective (kill -0 keeps
    succeeding), down should warn + return non-zero. Smoke v3 bumped
    grace 3s→10s SIGTERM + 2s post-SIGKILL = 12s total."""
    import time as _time
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        paths.router_pid_file().write_text("99999", encoding="utf-8")

        signals_seen = []
        def fake_kill(pid, sig):
            signals_seen.append(sig)
            return None

        with attr_patch(os, kill=fake_kill), attr_patch(_time, sleep=lambda _s: None):
            rc, _, err = run_cli(["down"])
        assert rc != 0
        assert "still alive" in err
        # pid file is NOT removed — operator needs to investigate
        assert paths.router_pid_file().exists()
        # Both SIGTERM and SIGKILL must have been attempted (escalation
        # loop survived the smoke-v3 finding that 3s SIGTERM-only grace
        # left daemons orphaned).
        import signal as _signal
        assert _signal.SIGTERM in signals_seen
        assert _signal.SIGKILL in signals_seen


# ── down: force flag & drift checks ───────────────────────────────


def test_down_with_force_flag_skips_drift_check():
    """When --force is passed, even a cmdline-mismatched pid should be killed."""
    import signal as _signal
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team) as tmp, _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        my_pid = os.getpid()
        paths.router_pid_file().write_text(str(my_pid), encoding="utf-8")

        kill_calls = []
        def fake_kill(pid, sig):
            if sig == 0:  # check if alive
                raise ProcessLookupError()  # simulate process gone after SIGTERM
            kill_calls.append((pid, sig))
            return None

        # Patch _read_cmdline to return a non-matching cmdline
        from eduflow.runtime import watchdog as _wd
        with attr_patch(os, kill=fake_kill), \
             attr_patch(_wd, _read_cmdline=lambda pid: "/usr/bin/firefox"):
            rc, out, _ = run_cli(["down", "--force"])

        assert rc == 0
        # Should still kill despite drift because --force bypasses check
        assert any(pid == my_pid for pid, sig in kill_calls if sig == _signal.SIGTERM)


def test_down_with_named_daemon_only_kills_that_daemon():
    """`down router` should only kill router, not task-publish/watchdog."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team) as tmp, _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        my_pid = os.getpid()
        paths.router_pid_file().write_text(str(my_pid), encoding="utf-8")
        paths.task_publish_pid_file().write_text(str(my_pid + 1), encoding="utf-8")
        paths.watchdog_pid_file().write_text(str(my_pid + 2), encoding="utf-8")

        kill_calls = []
        def fake_kill(pid, sig):
            if sig == 0:  # check if alive
                raise ProcessLookupError()  # simulate process gone after SIGTERM
            kill_calls.append((pid, sig))
            return None

        from eduflow.runtime import watchdog as _wd
        with attr_patch(os, kill=fake_kill), \
             attr_patch(_wd, _read_cmdline=lambda pid: f"eduflow router"):
            rc, out, _ = run_cli(["down", "router"])

        assert rc == 0
        # Only router's PID should be killed (SIGTERM first)
        import signal as _signal
        assert any(pid == my_pid and sig == _signal.SIGTERM for pid, sig in kill_calls)
        # Output should mention router but not others
        assert "router:" in out
        assert "task-publish:" not in out
        assert "watchdog:" not in out


def test_down_with_unknown_daemon_name_warns():
    """`down foobar` should warn about unknown daemon."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team):
        rc, out, err = run_cli(["down", "foobar"])
        # Unknown daemons produce a warning but continue with down
        combined = out + err
        assert "unknown" in combined.lower() or "foobar" in combined


def test_down_refuses_kill_on_entrypoint_drift():
    """When cmdline doesn't match, refuses to kill with error message."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team) as tmp, _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        my_pid = os.getpid()
        paths.router_pid_file().write_text(str(my_pid), encoding="utf-8")

        kill_calls = []
        def fake_kill(pid, sig):
            kill_calls.append((pid, sig))
            return None

        # Patch _read_cmdline to return a non-matching cmdline
        from eduflow.runtime import watchdog as _wd
        with attr_patch(os, kill=fake_kill), \
             attr_patch(_wd, _read_cmdline=lambda pid: "/usr/bin/firefox"):
            rc, out, err = run_cli(["down"])

        # Should fail due to drift detection (without --force)
        combined = out + err
        assert "drift" in combined.lower() or "refusing" in combined.lower()
        # Should inspect liveness but NOT send a terminating signal.
        import signal as _signal
        assert not any(sig in {_signal.SIGTERM, _signal.SIGKILL}
                       for _pid, sig in kill_calls)


def test_down_treats_dead_pid_as_dead_before_cmdline_drift_check():
    """A stale pid file should be cleaned even if cmdline lookup returns junk.

    Regression coverage for the PID-reuse guard: drift only makes sense for a
    live pid. If kill(pid, 0) says the process is gone, down should remove the
    stale pid file instead of failing on a misleading cmdline read.
    """
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team), _fake_tmux(session_alive=False):
        paths.ensure_state_dir()
        paths.router_pid_file().write_text("99999", encoding="utf-8")

        def fake_kill(pid, sig):
            raise ProcessLookupError()

        from eduflow.runtime import watchdog as _wd
        with attr_patch(os, kill=fake_kill), \
             attr_patch(_wd, _read_cmdline=lambda pid: "/usr/bin/firefox"):
            rc, out, err = run_cli(["down"])

        assert rc == 0
        assert "already dead" in out
        assert "drift" not in (out + err).lower()
        assert not paths.router_pid_file().exists()
