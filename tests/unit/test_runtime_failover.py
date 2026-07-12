"""Tests for `eduflow.runtime.failover`."""
from __future__ import annotations

import pytest

from eduflow.runtime import failover, config


def _install_chain(monkeypatch):
    """Install a deterministic runtime chain + env profiles for tests.

    Chain: primary (pool=qoder) → deepseek (pool=deepseek) → qwen_plus
    (pool=dashscope_coding) → deepseek (ring wrap). All switch on
    rate_limit / auth_failure.
    """
    registry = {
        "primary": {"cli": "qoderclicn", "model": "Qwen3.7-Max", "provider": "qoder",
                    "env_profile": "", "fallback_to": "deepseek",
                    "switch_on": ["rate_limit", "auth_failure"]},
        "deepseek": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
                     "env_profile": "ds", "fallback_to": "qwen_plus",
                     "switch_on": ["rate_limit", "auth_failure"]},
        "qwen_plus": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
                      "env_profile": "qw", "fallback_to": "deepseek",
                      "switch_on": ["rate_limit", "auth_failure"]},
    }
    profiles = {
        "ds": {"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
               "pool_id": "deepseek", "provider_family": "deepseek"},
        "qw": {"ANTHROPIC_BASE_URL": "https://coding.dashscope.aliyuncs.com/apps/anthropic",
               "pool_id": "dashscope_coding", "provider_family": "dashscope_qwen"},
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: dict(profiles))
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"a": {"cli": "qoderclicn", "runtime": "primary"}},
        "default_model": "opus",
    })


def test_runtime_pool_id_resolves_through_env_profile(monkeypatch):
    _install_chain(monkeypatch)
    assert failover.runtime_pool_id("deepseek") == "deepseek"
    assert failover.runtime_pool_id("qwen_plus") == "dashscope_coding"
    assert failover.runtime_pool_id("primary") == ""  # no env_profile
    assert failover.runtime_pool_id("no_such") == ""
    assert failover.runtime_pool_id("inline") == ""


def test_first_successful_outcome_picks_ready_over_drift():
    assert failover._first_successful_outcome(["env_drift", "smoke_failed", "ready"]) == "ready"
    assert failover._first_successful_outcome(["env_drift", "smoke_failed"]) == "env_drift"
    assert failover._first_successful_outcome([]) == failover.EXHAUSTED


def test_execute_fallback_loop_first_attempt_ready(monkeypatch):
    _install_chain(monkeypatch)
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append((runtime_name, prove_ready))
        return "ready"

    recorded = []
    result = failover.execute_fallback_loop(
        "a", "target", "primary", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: recorded.append(kw),
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
        trigger="test",
    )
    assert result["outcome"] == "ready"
    assert result["to_runtime"] == "deepseek"
    assert result["best_outcome"] == "ready"
    assert result["pool_switched"] is True
    assert result["exhausted"] is False
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["outcome"] == "ready"
    assert len(recorded) == 1
    assert recorded[0]["trigger"] == "test"
    assert recorded[0]["cross_pool"] is True


def test_takeover_guard_runs_immediately_before_every_restart(monkeypatch):
    order = []
    fallbacks = iter([{"name": "r2"}, {"name": "r3"}])
    monkeypatch.setattr(failover.config, "fallback_runtime", lambda *a, **k: next(fallbacks, None))
    monkeypatch.setattr(failover, "runtime_pool_id", lambda name: name)

    def guard():
        order.append("guard")
        if order.count("guard") == 2:
            raise failover.human_takeover.AutomationBlocked("takeover")

    def restart(*args, **kwargs):
        order.append("restart")
        return "env_drift"

    with pytest.raises(failover.human_takeover.AutomationBlocked):
        failover.execute_fallback_loop(
            "manager", object(), "r1", "failed", restart_fn=restart,
            record_fn=lambda **event: None, can_switch_fn=lambda pool: True,
            record_switch_fn=lambda pool, agent: None, automation_guard_fn=guard,
        )
    assert order == ["guard", "restart", "guard"]


def test_execute_fallback_loop_avoids_initial_pool(monkeypatch):
    # Start from deepseek (pool=deepseek). First attempt should skip
    # qwen_plus? No — qwen_plus is dashscope_coding, different pool, so
    # it IS the preferred fallback. But the ring wraps back to deepseek
    # which is same pool — that should be the avoided one.
    _install_chain(monkeypatch)
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append(runtime_name)
        return "ready" if runtime_name == "qwen_plus" else "env_drift"

    result = failover.execute_fallback_loop(
        "a", "target", "deepseek", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    # First call should be qwen_plus (cross-pool relative to deepseek).
    assert calls[0] == "qwen_plus"
    assert result["outcome"] == "ready"
    assert result["to_runtime"] == "qwen_plus"


def test_execute_fallback_loop_falls_through_on_env_drift(monkeypatch):
    _install_chain(monkeypatch)
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append(runtime_name)
        # deepseek: env drift; qwen_plus: ready
        return "env_drift" if runtime_name == "deepseek" else "ready"

    result = failover.execute_fallback_loop(
        "a", "target", "primary", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    assert calls == ["deepseek", "qwen_plus"]
    assert result["outcome"] == "ready"
    assert result["best_outcome"] == "ready"
    assert len(result["attempts"]) == 2


def test_execute_fallback_loop_exhausted_when_all_fail(monkeypatch):
    _install_chain(monkeypatch)

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        return "env_drift"  # everything drifts

    result = failover.execute_fallback_loop(
        "a", "target", "primary", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
        max_attempts=2,
    )
    assert result["exhausted"] is True
    assert result["outcome"] == "env_drift"
    assert result["best_outcome"] == "env_drift"
    assert len(result["attempts"]) == 2


def test_execute_fallback_loop_no_fallback_at_all(monkeypatch):
    # Agent with no runtime chain → no fallback candidates.
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"a": {"cli": "claude-code"}}, "default_model": "opus",
    })
    monkeypatch.setattr(config, "load_runtime_registry", lambda: {})
    monkeypatch.setattr(config, "load_env_profiles", lambda: {})
    calls = []
    result = failover.execute_fallback_loop(
        "a", "target", "inline", "rate_limit",
        restart_fn=lambda *a, **kw: (calls.append(1), "ready")[1],
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    assert result["outcome"] == failover.EXHAUSTED
    assert result["exhausted"] is True
    assert calls == []


def test_execute_fallback_loop_prefers_cross_pool_then_allows_same_pool(monkeypatch):
    # Chain: A (pool=p1) → B (pool=p1, same) → C (pool=p2). From A, first
    # try should pick C (cross-pool) if possible; if not, then B.
    registry = {
        "A": {"cli": "claude-code", "model": "opus", "provider": "anthropic-proxy",
              "env_profile": "p1", "fallback_to": "B",
              "switch_on": ["rate_limit"]},
        "B": {"cli": "claude-code", "model": "opus", "provider": "anthropic-proxy",
              "env_profile": "p1", "fallback_to": "C",
              "switch_on": ["rate_limit"]},
        "C": {"cli": "claude-code", "model": "opus", "provider": "anthropic-proxy",
              "env_profile": "p2", "fallback_to": "",
              "switch_on": ["rate_limit"]},
    }
    profiles = {
        "p1": {"ANTHROPIC_BASE_URL": "https://p1", "pool_id": "p1"},
        "p2": {"ANTHROPIC_BASE_URL": "https://p2", "pool_id": "p2"},
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: dict(profiles))
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"a": {"cli": "claude-code", "runtime": "A"}},
        "default_model": "opus",
    })
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append(runtime_name)
        return "ready"

    result = failover.execute_fallback_loop(
        "a", "target", "A", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    # First pick should be C (cross-pool), NOT B (same pool as A).
    assert calls[0] == "C", f"expected cross-pool first, got {calls}"
    assert result["outcome"] == "ready"
    assert result["pool_switched"] is True


def test_execute_fallback_loop_empty_initial_pool_prefers_nonempty_pool(monkeypatch):
    """When the starting runtime has no pool (env_profile=""), the first
    fallback should prefer a candidate that HAS a pool over one without.
    Chain: A(pool="") → B(pool="") → C(pool="p2"). From A, first pick
    should be C (cross-pool), not B (same un-pooled category)."""
    registry = {
        "A": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
              "env_profile": "", "fallback_to": "B",
              "switch_on": ["rate_limit"]},
        "B": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
              "env_profile": "", "fallback_to": "C",
              "switch_on": ["rate_limit"]},
        "C": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
              "env_profile": "p2", "fallback_to": "",
              "switch_on": ["rate_limit"]},
    }
    profiles = {
        "p2": {"ANTHROPIC_BASE_URL": "https://p2", "pool_id": "p2"},
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: dict(profiles))
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"a": {"cli": "claude-code", "runtime": "A"}},
        "default_model": "opus",
    })
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append(runtime_name)
        return "ready"

    result = failover.execute_fallback_loop(
        "a", "target", "A", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    # C has a pool; B doesn't. Cross-pool priority should pick C first.
    assert calls[0] == "C", f"expected nonempty-pool first, got {calls}"
    assert result["pool_switched"] is True


def test_execute_fallback_loop_falls_back_when_no_nonempty_pool_candidate(monkeypatch):
    """When all fallback candidates also have empty pool, fall through to
    Pass 2 and pick the first matching candidate."""
    registry = {
        "A": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
              "env_profile": "", "fallback_to": "B",
              "switch_on": ["rate_limit"]},
        "B": {"cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
              "env_profile": "", "fallback_to": "",
              "switch_on": ["rate_limit"]},
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: {})
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"a": {"cli": "claude-code", "runtime": "A"}},
        "default_model": "opus",
    })
    calls = []

    def fake_restart(agent, target, runtime_name, reason="", prove_ready=False):
        calls.append(runtime_name)
        return "ready"

    result = failover.execute_fallback_loop(
        "a", "target", "A", "rate_limit",
        restart_fn=fake_restart,
        record_fn=lambda **kw: None,
        now_fn=lambda: 100.0,
        can_switch_fn=lambda pool_id: True,
        record_switch_fn=lambda pool_id, agent: None,
    )
    # Both A and B have no pool. No cross-pool candidate exists, so
    # Pass 2 picks B (the only option).
    assert calls[0] == "B"
    assert result["pool_switched"] is False


def test_hermes_runtime_chain_allows_model_fallback_on_same_cli(monkeypatch):
    registry = {
        "hermes_primary": {
            "cli": "hermes-agent", "model": "minimax-m3", "provider": "minimax",
            "env_profile": "hm1", "fallback_to": "hermes_backup_model",
            "switch_on": ["rate_limit"],
        },
        "hermes_backup_model": {
            "cli": "hermes-agent", "model": "backup-model", "provider": "backup",
            "env_profile": "hm2", "fallback_to": "",
            "switch_on": ["rate_limit"],
        },
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: {})
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"Hermes": {"cli": "hermes-agent", "runtime": "hermes_primary"}},
        "default_model": "opus",
    })

    chain = config.resolve_runtime_chain("Hermes")
    assert [item["cli"] for item in chain] == ["hermes-agent", "hermes-agent"]
    fallback = config.fallback_runtime(
        "Hermes", current_runtime="hermes_primary", reason="rate_limit")
    assert fallback is not None
    assert fallback["name"] == "hermes_backup_model"
    assert fallback["cli"] == "hermes-agent"
    assert fallback["model"] == "backup-model"


def test_hermes_runtime_chain_rejects_cli_base_fallback(monkeypatch):
    registry = {
        "hermes_primary": {
            "cli": "hermes-agent", "model": "minimax-m3", "provider": "minimax",
            "env_profile": "hm1", "fallback_to": "bad_fallback",
            "switch_on": ["rate_limit"],
        },
        "bad_fallback": {
            "cli": "claude-code", "model": "sonnet", "provider": "anthropic-proxy",
            "env_profile": "claude_proxy_primary", "fallback_to": "",
            "switch_on": ["rate_limit"],
        },
    }
    monkeypatch.setattr(config, "load_runtime_registry", lambda: dict(registry))
    monkeypatch.setattr(config, "load_env_profiles", lambda: {})
    monkeypatch.setattr(config, "load_team", lambda: {
        "session": "T", "agents": {"Hermes": {"cli": "hermes-agent", "runtime": "hermes_primary"}},
        "default_model": "opus",
    })

    try:
        config.resolve_runtime_chain("Hermes")
    except ValueError as exc:
        assert "Hermes runtime chains must keep cli='hermes-agent'" in str(exc)
        assert "bad_fallback" in str(exc)
    else:
        raise AssertionError("expected Hermes chain with non-Hermes CLI to fail")
