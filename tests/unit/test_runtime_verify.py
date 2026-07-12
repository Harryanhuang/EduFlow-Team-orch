"""Tests for `eduflow.runtime.verify`."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

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


def test_verify_live_env_skips_anthropic_token_for_non_anthropic_provider(monkeypatch):
    # Hermes-style profile: provider_family is "minimax" (not anthropic), so
    # auto-fill populates ANTHROPIC_AUTH_TOKEN from the shell env into the
    # expected dict, but the Hermes pane never sets it. Without the skip,
    # this reports a spurious drift warning. With the provider-aware skip,
    # it should be ok. The pane env is non-empty (truthy) but lacks the
    # ANTHROPIC key — that's the exact shape we see in real Hermes panes.
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"provider_family": "minimax",
                                           "HERMES_BASE_URL": "https://h.local",
                                           "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"HERMES_BASE_URL": "https://h.local"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is True
        assert mismatches == []


def test_verify_live_env_still_flags_anthropic_token_for_anthropic_provider(monkeypatch):
    # Anthropic-family provider with a missing live token must still report
    # drift — the provider-aware skip only fires for non-Anthropic families.
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"provider_family": "anthropic_proxy",
                                           "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"ANTHROPIC_BASE_URL": "https://x"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is False
        assert any("ANTHROPIC_AUTH_TOKEN" in m for m in mismatches)


def test_verify_live_env_skips_openai_api_key_for_codex_provider(monkeypatch):
    with isolated_env():
        monkeypatch.setattr(verify.config, "env_profile_config",
                            lambda name: ({"provider_family": "openai_codex",
                                           "OPENAI_API_KEY": "sk-real-token"}
                                          if name == "p" else {}))
        monkeypatch.setattr(verify, "pane_live_env",
                            lambda *a, **kw: {"OPENAI_BASE_URL": "https://api.openai.com/v1"})
        ok, mismatches = verify.verify_live_env_matches_profile("X:0", "p")
        assert ok is True
        assert mismatches == []


def test_api_smoke_runtime_skipped_for_codex():
    assert verify.api_smoke_runtime({"cli": "codex-cli", "provider": "openai"})[0] == "skipped"


def test_api_smoke_runtime_skipped_for_qoder():
    assert verify.api_smoke_runtime({"cli": "qoderclicn", "provider": "qoder"})[0] == "skipped"


def test_api_smoke_runtime_skipped_for_mimo():
    assert verify.api_smoke_runtime({"cli": "mimo-code", "provider": "mimo"})[0] == "skipped"


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
        verify.record_switch_event(agent="a", from_runtime="x", to_runtime="y",
                                   reason="rate_limit", outcome="ready",
                                   switch_id="id1", phase="completed",
                                   verdict="proved_ready", actor="u_admin",
                                   target="S:a", result={"status": "completed",
                                                          "outcome": "ready"})
        verify.record_switch_event(agent="b", from_runtime="p", to_runtime="q",
                                   reason="auth_failure", outcome="env_drift",
                                   switch_id="id2")
        events = verify.read_switch_events(last_n=10)
        assert len(events) == 2
        assert events[-1]["agent"] == "b"
        assert "ts" in events[-1]
        assert events[0]["switch_id"] == "id1"
        assert events[0]["phase"] == "completed"
        assert events[0]["verdict"] == "proved_ready"
        assert events[0]["actor"] == "u_admin"
        assert events[0]["target"] == "S:a"
        assert events[0]["result"] == {"status": "completed", "outcome": "ready"}
        assert events[1]["switch_id"] == "id2"
        assert "best_outcome" in events[0]
        assert "attempts" in events[0]
        assert "pool_switched" in events[0]
        assert "cross_pool" in events[0]


def test_read_switch_events_empty_when_no_file():
    with isolated_env():
        path = verify._switch_events_path()
        if path.exists():
            path.unlink()


def test_record_switch_event_auto_generates_switch_id():
    with isolated_env():
        path = verify._switch_events_path()
        # Fresh file
        if path.exists():
            path.unlink()
        assert verify.read_switch_events() == []
        verify.record_switch_event(agent="z", from_runtime="a", to_runtime="b",
                                   reason="test", outcome="ready")
        events = verify.read_switch_events(last_n=1)
        assert len(events) == 1
        sid = events[0]["switch_id"]
        assert isinstance(sid, str)
        assert len(sid) == 8  # uuid4()[:8]


def test_strict_switch_event_raises_on_persistence_failure(monkeypatch):
    with isolated_env():
        with monkeypatch.context() as patch:
            patch.setattr(verify.os, "open",
                          lambda *a, **kw: (_ for _ in ()).throw(OSError("disk full")))
            with pytest.raises(OSError, match="disk full"):
                verify.record_switch_event(agent="a", from_runtime="x", to_runtime="y",
                                           reason="manual", outcome="pending", strict=True)


def test_concurrent_short_writes_remain_distinct_valid_json_lines(monkeypatch):
    with isolated_env():
        path = verify._switch_events_path()
        if path.exists():
            path.unlink()
        real_write = verify.os.write

        def short_write(fd, payload):
            return real_write(fd, bytes(payload[:max(1, len(payload) // 4)]))

        monkeypatch.setattr(verify.os, "write", short_write)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i: verify.record_switch_event(
                agent=f"a{i}", from_runtime="x", to_runtime="y", reason="race",
                outcome="ready", switch_id=f"id-{i}", strict=True), range(20)))
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 20
        rows = [json.loads(line) for line in lines]
        assert {row["switch_id"] for row in rows} == {f"id-{i}" for i in range(20)}
