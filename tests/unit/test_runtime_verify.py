"""Tests for `eduflow.runtime.verify`."""
from __future__ import annotations

import json
import os

from helpers import FakeProc, isolated_env
from eduflow.runtime import verify


def _fake_tmux_display(pid: str):
    def _run(args, **_kw):
        if "#{pane_pid}" in args:
            return FakeProc(stdout=f"{pid}\n")
        return FakeProc(stdout="")
    return _run


def test_profile_env_keys_has_anthropic_and_openai():
    assert "ANTHROPIC_BASE_URL" in verify.PROFILE_ENV_KEYS
    assert "ANTHROPIC_MODEL" in verify.PROFILE_ENV_KEYS
    assert "OPENAI_BASE_URL" in verify.PROFILE_ENV_KEYS


def test_pane_live_env_returns_empty_when_tmux_fails():
    def bad_display(args, **_kw):
        return FakeProc(returncode=1, stdout="")
    assert verify.pane_live_env("X:0", tmux_display=bad_display) == {}


def test_pane_live_env_walks_process_tree(monkeypatch):
    def fake_profile_env(pid, **_kw):
        return {"ANTHROPIC_BASE_URL": "https://x"} if pid == "42" else {}
    def fake_child_pids(pid, **_kw):
        return ["42"] if pid == "1" else []
    monkeypatch.setattr(verify, "_profile_env_for_pid", fake_profile_env)
    monkeypatch.setattr(verify, "_child_pids", fake_child_pids)
    display = _fake_tmux_display("1")
    env = verify.pane_live_env("S:0", tmux_display=display)
    assert env == {"ANTHROPIC_BASE_URL": "https://x"}


def test_verify_live_env_matches_profile_no_profile_is_ok():
    assert verify.verify_live_env_matches_profile("X:0", "") == (True, [])


def test_verify_live_env_matches_profile_missing_profile():
    with isolated_env():
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "no_such_profile")
        assert ok is False
        assert any("not in config" in m for m in mismatches)


def test_verify_live_env_matches_profile_unavailable_live_env(monkeypatch):
    with isolated_env():
        monkeypatch.setattr(verify, "pane_live_env", lambda *a, **kw: {})
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: {"ANTHROPIC_BASE_URL": "https://x"} if name == "p" else {})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is False
        assert any("live_env_unavailable" in m for m in mismatches)


def test_verify_live_env_matches_profile_match(monkeypatch):
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"ANTHROPIC_BASE_URL": "https://x", "ANTHROPIC_MODEL": "m1"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"ANTHROPIC_BASE_URL": "https://x", "ANTHROPIC_MODEL": "m1"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is True
        assert mismatches == []


def test_verify_live_env_matches_profile_mismatch(monkeypatch):
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"ANTHROPIC_BASE_URL": "https://x", "ANTHROPIC_MODEL": "m1"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"ANTHROPIC_BASE_URL": "https://y", "ANTHROPIC_MODEL": "m1"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is False
        assert any("ANTHROPIC_BASE_URL" in m and "expected=https://x" in m and "live=https://y" in m
                   for m in mismatches)


def test_verify_live_env_matches_profile_proxy_managed_token_is_ok(monkeypatch):
    # Pane runs with the PROXY_MANAGED sentinel instead of the literal token;
    # the gateway injects real auth, so this is not drift.
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"ANTHROPIC_BASE_URL": "https://x",
                                           "ANTHROPIC_AUTH_TOKEN": "sk-real-token"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"ANTHROPIC_BASE_URL": "https://x",
                                             "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is True
        assert mismatches == []


def test_api_smoke_runtime_skipped_for_codex():
    assert verify.api_smoke_runtime({"cli": "codex-cli", "provider": "openai"})[0] == "skipped"


def test_api_smoke_runtime_skipped_for_qoder():
    assert verify.api_smoke_runtime({"cli": "qoderclicn", "provider": "qoder"})[0] == "skipped"


def test_api_smoke_runtime_unknown_cli():
    assert verify.api_smoke_runtime({"cli": "weird-cli"})[0] == "skipped"


def test_api_smoke_runtime_ok(monkeypatch):
    def fake_run(args, **_kw):
        return FakeProc(stdout="200")
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                                           "ANTHROPIC_AUTH_TOKEN": "sk-x",
                                           "ANTHROPIC_MODEL": "deepseek-v4-pro"}
                                          if name == "ds" else {}))
        verdict, detail = verify.api_smoke_runtime(
            {"cli": "claude-code", "provider": "anthropic-proxy", "env_profile": "ds"},
            run=fake_run,
        )
        assert verdict == "ok"
        assert "200" in detail


def test_api_smoke_runtime_failed_on_429(monkeypatch):
    def fake_run(args, **_kw):
        return FakeProc(stdout="429")
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"ANTHROPIC_BASE_URL": "https://x",
                                           "ANTHROPIC_AUTH_TOKEN": "sk",
                                           "ANTHROPIC_MODEL": "m"}
                                          if name == "p" else {}))
        verdict, detail = verify.api_smoke_runtime(
            {"cli": "claude-code", "provider": "anthropic-proxy", "env_profile": "p"},
            run=fake_run,
        )
        assert verdict == "failed"
        assert "429" in detail


def test_record_and_read_switch_events_roundtrip():
    with isolated_env():
        path = verify._switch_events_path()
        if path.exists():
            path.unlink()
        verify.record_switch_event({"agent": "a", "from_runtime": "x", "to_runtime": "y",
                                    "reason": "rate_limit", "outcome": "ready"})
        verify.record_switch_event({"agent": "b", "from_runtime": "p", "to_runtime": "q",
                                    "reason": "auth_failure", "outcome": "env_drift"})
        events = verify.read_switch_events(last_n=10)
        assert len(events) == 2
        assert events[-1]["agent"] == "b"
        assert "ts" in events[-1]


def test_read_switch_events_empty_when_no_file():
    with isolated_env():
        path = verify._switch_events_path()
        if path.exists():
            path.unlink()
        assert verify.read_switch_events() == []
