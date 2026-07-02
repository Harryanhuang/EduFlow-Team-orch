"""Tests for `eduflow runtime-guard`."""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.runtime import paths


def test_runtime_guard_reports_empty_state():
    with isolated_env():
        rc, out, _ = run_cli(["runtime-guard"])
        assert rc == 0
        assert "no agent state" in out


def test_runtime_guard_json_outputs_state():
    with isolated_env():
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"agents": {"worker_a": {"needs_manager_action": True}}}), encoding="utf-8")
        rc, out, _ = run_cli(["runtime-guard", "--json"])
        assert rc == 0
        assert '"worker_a"' in out
        assert '"needs_manager_action": true' in out


def test_runtime_guard_clear_agent():
    with isolated_env():
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"agents": {"worker_a": {}, "worker_b": {}}}), encoding="utf-8")
        rc, out, _ = run_cli(["runtime-guard", "clear", "worker_a"])
        assert rc == 0
        assert "cleared worker_a" in out
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "worker_a" not in data["agents"]
        assert "worker_b" in data["agents"]


def test_runtime_guard_clear_all():
    with isolated_env():
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"agents": {"worker_a": {}, "worker_b": {}}}), encoding="utf-8")
        rc, out, _ = run_cli(["runtime-guard", "clear", "--all"])
        assert rc == 0
        assert "cleared all" in out
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"agents": {}}


def test_runtime_guard_text_shows_escalation_fields():
    with isolated_env():
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "agents": {
                "worker_a": {
                    "needs_manager_action": True,
                    "escalation_needed": True,
                    "last_switch_outcome": "fallback_exhausted",
                    "last_failure_reason": "rate_limit",
                    "escalation_reason": "fallback_chain_exhausted",
                }
            }
        }), encoding="utf-8")
        rc, out, _ = run_cli(["runtime-guard"])
        assert rc == 0
        assert "needs_manager_action=true" in out
        assert "escalation_needed=true" in out
        assert "outcome=fallback_exhausted" in out
        assert "failure=rate_limit" in out
        assert "escalation=fallback_chain_exhausted" in out


# ── health scoring tests ───────────────────────────────────────────


def test_compute_health_healthy_agent():
    from eduflow.commands.runtime_guard import _compute_health
    now = 1000.0
    score, penalties = _compute_health({}, now)
    assert score == 100
    assert penalties == []


def test_compute_health_recent_switch_penalty():
    from eduflow.commands.runtime_guard import _compute_health
    now = 1000.0
    row = {"switch_times": [str(now - 100)]}  # 100s ago, within 600s window
    score, penalties = _compute_health(row, now)
    assert score == 80
    assert "recent_switch(1)" in penalties


def test_compute_health_cooldown_penalty():
    from eduflow.commands.runtime_guard import _compute_health
    now = 1000.0
    row = {"cooldown_until": str(now + 500)}  # still in cooldown
    score, penalties = _compute_health(row, now)
    assert score == 50
    assert "cooldown" in penalties


def test_compute_health_fallback_penalty():
    from eduflow.commands.runtime_guard import _compute_health
    now = 1000.0
    row = {"failback": {"in_fallback_since": str(now - 30)}}
    score, penalties = _compute_health(row, now)
    assert score == 70
    assert "in_fallback" in penalties


def test_compute_health_multiple_penalties():
    from eduflow.commands.runtime_guard import _compute_health
    now = 1000.0
    row = {
        "switch_times": [str(now - 50)],
        "failback": {"in_fallback_since": str(now - 30)},
        "cooldown_until": str(now + 200),
    }
    score, penalties = _compute_health(row, now)
    assert score == 0  # 100 - 20 - 30 - 50 = 0, clamped
    assert len(penalties) == 3


def test_watch_once_outputs_table(capsys):
    from eduflow.commands.runtime_guard import _watch_once
    data = {
        "agents": {
            "worker_a": {
                "last_switch_to": "deepseek",
                "last_failure_reason": "rate_limit",
                "switch_times": ["100"],
            },
            "worker_b": {},
        }
    }
    _watch_once(data, now=500.0)
    out = capsys.readouterr().out
    assert "worker_a" in out
    assert "worker_b" in out
    assert "deepseek" in out
    assert "rate_limit" in out
