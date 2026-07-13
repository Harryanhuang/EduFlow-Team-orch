"""Concurrency contracts for the per-agent runtime switch boundary."""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from helpers import isolated_env
from eduflow.runtime import lifecycle, paths, tmux, verify
from eduflow.util import file_lock, read_json


_TEAM_TOML = '''
[team]
session = "S"

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "claude-code"
model = "sonnet"
'''


def test_concurrent_switches_for_one_agent_allow_only_one_spawn(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    spawn_calls = 0
    spawn_lock = threading.Lock()

    def fake_spawn(*_args, **_kwargs):
        nonlocal spawn_calls
        with spawn_lock:
            spawn_calls += 1
            call_number = spawn_calls
        if call_number == 1:
            started.set()
            assert release.wait(2)
        return lifecycle.READY, ""

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        monkeypatch.setattr(verify, "verify_live_env_matches_profile", lambda *_args: (True, []))
        monkeypatch.setattr(verify, "api_smoke_runtime", lambda *_args: ("ok", "200"))
        monkeypatch.setattr(lifecycle, "_verify_no_failure_markers", lambda *_args, **_kwargs: (True, []))
        monkeypatch.setattr(lifecycle, "_live_cli_process_and_ready", lambda *_args: True)

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                lifecycle.restart_with_runtime,
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
            assert started.wait(1)
            second = pool.submit(
                lifecycle.restart_with_runtime,
                "worker_a", tmux.Target("S", "worker_a"), "backup",
                nudge_latest_inbox=False,
            )
            assert second.result(timeout=1) == "switch_busy"
            release.set()
            assert first.result(timeout=2) == lifecycle.READY
        status = read_json(paths.runtime_status_file(), {"agents": {}})["agents"]["worker_a"]
        assert status["generation"] == 1
        assert status["switch_id"]
        events = verify.read_switch_events(last_n=10)
        assert [event["outcome"] for event in events] == [
            "switch_started", "switch_completed",
        ]
        assert events[0]["switch_id"] == events[1]["switch_id"] == status["switch_id"]

    assert spawn_calls == 1


def test_switch_start_audit_failure_prevents_spawn(monkeypatch):
    spawn_calls = 0

    def fake_spawn(*_args, **_kwargs):
        nonlocal spawn_calls
        spawn_calls += 1
        return lifecycle.READY, ""

    def fail_audit(**_event):
        raise OSError("audit volume unavailable")

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        monkeypatch.setattr(verify, "record_switch_event", fail_audit)

        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except OSError as exc:
            assert "audit volume unavailable" in str(exc)
        else:
            raise AssertionError("audit failure must abort the switch")

    assert spawn_calls == 0


def test_switch_start_audit_timeout_prevents_spawn(monkeypatch):
    spawn_calls = 0

    def fake_spawn(*_args, **_kwargs):
        nonlocal spawn_calls
        spawn_calls += 1
        return lifecycle.READY, ""

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        monkeypatch.setattr(
            verify, "record_switch_event",
            lambda **_event: (_ for _ in ()).throw(TimeoutError("audit lock timed out")),
        )

        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except TimeoutError as exc:
            assert "audit lock timed out" in str(exc)
        else:
            raise AssertionError("strict audit timeout must abort the switch")

    assert spawn_calls == 0


def test_strict_audit_lock_contention_times_out_before_spawn(monkeypatch):
    held = threading.Event()
    release = threading.Event()
    spawn_calls = 0

    def hold_audit_lock(path):
        with file_lock(path):
            held.set()
            assert release.wait(1)

    def fake_spawn(*_args, **_kwargs):
        nonlocal spawn_calls
        spawn_calls += 1
        return lifecycle.SPAWN_FAILED, ""

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(verify, "STRICT_SWITCH_EVENT_LOCK_TIMEOUT_S", 0.01)
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        path = verify._switch_events_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        holder = threading.Thread(target=hold_audit_lock, args=(path,))
        holder.start()
        assert held.wait(1)
        started_at = time.monotonic()
        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except TimeoutError:
            pass
        else:
            raise AssertionError("strict audit lock contention must abort the switch")
        finally:
            release.set()
            holder.join(1)

    assert time.monotonic() - started_at < 0.1
    assert spawn_calls == 0


def test_switch_exception_stamps_generation_and_one_failed_terminal_event(monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError("spawn transport failed")

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", explode)

        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except RuntimeError as exc:
            assert "spawn transport failed" in str(exc)
        else:
            raise AssertionError("spawn exception must reach the caller")

        status = read_json(paths.runtime_status_file(), {"agents": {}})["agents"]["worker_a"]
        events = verify.read_switch_events(last_n=10)

    assert status["generation"] == 1
    assert status["switch_outcome"] == "exception"
    assert [event["outcome"] for event in events] == [
        "switch_started", "switch_failed",
    ]
    assert events[0]["switch_id"] == events[1]["switch_id"] == status["switch_id"]


@pytest.mark.parametrize("error_type", [OSError, TimeoutError])
def test_terminal_audit_failure_propagates_after_status_is_stamped(monkeypatch, error_type):
    calls = 0
    spawn_calls = 0

    def fake_spawn(*_args, **_kwargs):
        nonlocal spawn_calls
        spawn_calls += 1
        return lifecycle.SPAWN_FAILED, ""

    def fail_terminal(**_event):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise error_type("terminal audit unavailable")

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        monkeypatch.setattr(verify, "record_switch_event", fail_terminal)

        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except error_type as exc:
            assert "terminal audit unavailable" in str(exc)
        else:
            raise AssertionError("terminal audit failure must reach the caller")

        status = read_json(paths.runtime_status_file(), {"agents": {}})["agents"]["worker_a"]

    assert spawn_calls == 1
    assert status["generation"] == 1
    assert status["switch_outcome"] == lifecycle.SPAWN_FAILED


def test_status_stamp_timeout_records_failure_instead_of_switch_busy(monkeypatch):
    events = []

    def fake_spawn(*_args, **_kwargs):
        return lifecycle.SPAWN_FAILED, ""

    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_TOML, encoding="utf-8")
        monkeypatch.setattr(lifecycle, "_spawn_once", fake_spawn)
        monkeypatch.setattr(
            lifecycle, "_stamp_switch_generation",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("status lock timed out")),
        )
        monkeypatch.setattr(verify, "record_switch_event", lambda **event: events.append(event))

        try:
            lifecycle.restart_with_runtime(
                "worker_a", tmux.Target("S", "worker_a"), "primary",
                nudge_latest_inbox=False,
            )
        except TimeoutError as exc:
            assert "status lock timed out" in str(exc)
        else:
            raise AssertionError("status timeout must not become switch_busy")

    assert [event["outcome"] for event in events] == [
        "switch_started", "switch_failed",
    ]
    assert events[1]["result"]["stage"] == "status_stamp"


def test_stale_switch_generation_cannot_replace_newer_runtime_status():
    with isolated_env():
        lifecycle._write_runtime_status(
            "worker_a",
            {"selected_runtime": "newer", "cli": "claude-code"},
            reason="newer_switch",
        )
        lifecycle._stamp_switch_generation(
            "worker_a", 2, "newer-id", requested_runtime="newer", outcome="ready",
        )
        lifecycle._stamp_switch_generation(
            "worker_a", 1, "stale-id", requested_runtime="stale", outcome="ready",
        )
        status = lifecycle.current_runtime_status("worker_a")

    assert status["runtime"] == "newer"
    assert status["generation"] == 2
    assert status["switch_id"] == "newer-id"
