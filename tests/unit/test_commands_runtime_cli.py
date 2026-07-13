"""Tests for `eduflow runtime switch/verify/events` CLI."""
from __future__ import annotations

import json

from helpers import isolated_env, run_cli
from eduflow.runtime import verify, lifecycle


def _patch_runtime_verdict_dependencies(monkeypatch, status: dict) -> None:
    from eduflow.commands import runtime_verify as rv
    from eduflow.runtime import tmux as tmux_mod

    monkeypatch.setattr(lifecycle, "current_runtime_status", lambda _agent: dict(status))
    monkeypatch.setattr(rv.config, "load_team", lambda: {"session": "S"})
    monkeypatch.setattr(tmux_mod, "has_session", lambda _session: True)
    monkeypatch.setattr(tmux_mod, "has_window", lambda _target: True)
    cli = str(status.get("cli") or "claude-code")
    if cli == "codex-cli":
        pane = tmux_mod.PaneInfo("0", True, "codex", "codex --model test")
        text = "OpenAI Codex\npermissions: YOLO"
    else:
        pane = tmux_mod.PaneInfo("0", True, "claude", "claude --model test")
        text = "bypass permissions on"
    monkeypatch.setattr(tmux_mod, "list_panes", lambda _target: [pane])
    monkeypatch.setattr(tmux_mod, "capture_pane", lambda *_args, **_kwargs: text)


def test_runtime_verify_skipped_provider_smoke_is_ready_unproven(monkeypatch):
    from eduflow.commands import runtime_verify as rv

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "codex", "cli": "codex-cli", "env_profile": "",
    })
    monkeypatch.setattr(rv.verify, "verify_live_env_matches_profile", lambda *_args: (True, []))
    monkeypatch.setattr(rv.verify, "api_smoke_runtime", lambda _resolved: ("skipped", "unsupported"))
    monkeypatch.setattr(rv, "_pane_failure_scan", lambda *_args: (True, []))

    verdict = rv.compute_verdict("worker_a", live_smoke=True)

    assert verdict["smoke_verdict"] == "skipped"
    assert verdict["verdict"] == "ready_unproven"


def test_runtime_verify_uses_created_at_for_an_unread_probe(monkeypatch):
    from eduflow.commands import runtime_verify as rv
    from eduflow.store import local_facts

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "primary", "cli": "claude-code", "env_profile": "",
        "env_ok": True, "smoke_ok": True, "verified_at": rv.time.time(),
    })
    local_facts.append_message("worker_a", "manager", "fresh readiness probe", priority="高")

    verdict = rv.compute_verdict("worker_a")

    assert verdict["inbox_state"] == "not_consumed"
    assert verdict["verdict"] == "inbox_not_consumed"


def test_runtime_verify_expires_a_stale_cached_proof(monkeypatch):
    from eduflow.commands import runtime_verify as rv

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "primary", "cli": "claude-code", "env_profile": "",
        "env_ok": True, "smoke_ok": True,
        "verified_at": rv.time.time() - 3600,
    })

    verdict = rv.compute_verdict("worker_a")

    assert verdict["verdict"] == "ready_unproven"
    assert verdict["cached"] is False


def test_runtime_verify_cached_proof_still_rejects_live_env_drift(monkeypatch):
    from eduflow.commands import runtime_verify as rv

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "primary", "cli": "claude-code", "env_profile": "profile",
        "env_ok": True, "smoke_ok": True, "verified_at": rv.time.time(),
    })
    monkeypatch.setattr(rv.verify, "verify_live_env_matches_profile", lambda *_args: (False, ["live drift"]))

    verdict = rv.compute_verdict("worker_a")

    assert verdict["verdict"] == "env_drift"
    assert verdict["mismatches"] == ["live drift"]


def test_runtime_verify_cached_proof_still_rejects_live_pane_failure(monkeypatch):
    from eduflow.commands import runtime_verify as rv

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "primary", "cli": "claude-code", "env_profile": "",
        "env_ok": True, "smoke_ok": True, "verified_at": rv.time.time(),
    })
    monkeypatch.setattr(rv, "_pane_failure_scan", lambda *_args: (False, ["auth_failure"]))

    verdict = rv.compute_verdict("worker_a")

    assert verdict["found_markers"] == ["auth_failure"]
    assert verdict["verdict"] == "ready_unproven"


def test_runtime_verify_requires_live_cli_process_and_ready_marker(monkeypatch):
    from eduflow.commands import runtime_verify as rv
    from eduflow.runtime import tmux as tmux_mod

    _patch_runtime_verdict_dependencies(monkeypatch, {
        "runtime": "primary", "cli": "claude-code", "env_profile": "",
        "env_ok": True, "smoke_ok": True, "verified_at": rv.time.time(),
    })
    monkeypatch.setattr(
        tmux_mod,
        "list_panes",
        lambda _target: [tmux_mod.PaneInfo("0", True, "zsh", "claude --model test")],
    )
    monkeypatch.setattr(tmux_mod, "capture_pane", lambda *_args, **_kwargs: "bypass permissions on")
    monkeypatch.setattr(rv, "_pane_failure_scan", lambda *_args: (True, []))

    verdict = rv.compute_verdict("worker_a")

    assert verdict["process_ok"] is False
    assert verdict["cli_ready"] is False
    assert verdict["verdict"] == "ready_unproven"


def test_runtime_dispatch_unknown_subcommand():
    with isolated_env():
        rc, out, err = run_cli(["runtime", "banana"])
        assert rc == 1
        assert "unknown runtime subcommand" in (out + err)


def test_runtime_dispatch_no_args():
    with isolated_env():
        rc, out, err = run_cli(["runtime"])
        assert rc == 1
        assert "usage:" in (out + err)


def test_runtime_switch_requires_two_positional_args():
    with isolated_env():
        rc, _, _ = run_cli(["runtime", "switch", "worker_a"])
        assert rc == 1


def test_runtime_switch_unknown_agent():
    with isolated_env(team={"agents": {"worker_a": {"cli": "claude-code"}}}):
        rc, _, err = run_cli(["runtime", "switch", "nobody", "backup"])
        assert rc != 0
        assert "unknown agent" in err


def test_runtime_switch_unknown_runtime():
    with isolated_env(team={"agents": {"worker_a": {"cli": "claude-code"}}}):
        rc, _, err = run_cli(["runtime", "switch", "worker_a", "no_such_runtime"])
        assert rc != 0
        assert "unknown runtime" in err


def test_runtime_switch_json_emits_outcome(monkeypatch):
    with isolated_env(team={"agents": {"worker_a": {"cli": "claude-code"}}}) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"
admins = ["u_test_admin"]

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["rate_limit"]

[runtime_registry.backup]
cli = "claude-code"
model = "sonnet"
env_profile = "ds"
switch_on = ["rate_limit"]

[env_profiles.ds]
ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_MODEL = "deepseek-v4-pro"
""", encoding="utf-8")
        # Stub the tmux and lifecycle layers so we don't touch real panes.
        from eduflow.runtime import tmux as tmux_mod
        monkeypatch.setattr(tmux_mod, "has_session", lambda s: True)
        monkeypatch.setattr(tmux_mod, "has_window", lambda t: True)
        monkeypatch.setattr(lifecycle, "restart_with_runtime",
                            lambda *a, **kw: "ready")
        monkeypatch.setattr(lifecycle, "current_runtime_status",
                            lambda agent: {"runtime": "primary"})
        from eduflow.commands import runtime_verify as rv
        monkeypatch.setattr(rv, "compute_verdict",
                            lambda agent, **kw: {"verdict": "proved_ready"})
        rc, out, _ = run_cli(["runtime", "switch", "worker_a", "backup",
                              "--actor", "u_test_admin", "--reason", "manual_test", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert data["agent"] == "worker_a"
        assert data["outcome"] == "ready"
        assert data["verdict"] == "proved_ready"


def test_runtime_verify_json_verdict(monkeypatch):
    with isolated_env(team={"agents": {"worker_a": {"cli": "claude-code"}}}):
        from eduflow.commands import runtime_verify as rv
        monkeypatch.setattr(rv, "compute_verdict",
                            lambda agent, **kw: {"verdict": "proved_ready",
                                           "declared_runtime": "primary",
                                           "declared_env": "ds",
                                           "declared_pool_id": "deepseek",
                                           "env_ok": True,
                                           "smoke_ok": True,
                                           "smoke_verdict": "ok",
                                           "pane_clean": True,
                                           "inbox_state": "no_pending",
                                           "mismatches": [],
                                           "found_markers": [],
                                           "cached": False})
        rc, out, _ = run_cli(["runtime", "verify", "worker_a", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert data["verdict"] == "proved_ready"
        assert data["declared_pool_id"] == "deepseek"


def test_runtime_verify_proved_ready_clears_stale_guard(monkeypatch):
    with isolated_env(team={"agents": {"worker_a": {"cli": "claude-code"}}}):
        from eduflow.commands import runtime_verify as rv
        from eduflow.runtime import paths

        paths.runtime_guard_state_file().parent.mkdir(parents=True, exist_ok=True)
        paths.runtime_guard_state_file().write_text(json.dumps({
            "agents": {
                "worker_a": {
                    "needs_manager_action": True,
                    "escalation_needed": True,
                    "escalation_reason": "fallback_chain_exhausted",
                },
                "worker_b": {"needs_manager_action": True},
            }
        }), encoding="utf-8")
        monkeypatch.setattr(rv, "compute_verdict",
                            lambda agent, **kw: {"verdict": "proved_ready",
                                           "declared_runtime": "primary",
                                           "declared_env": "ds",
                                           "declared_pool_id": "deepseek",
                                           "env_ok": True,
                                           "smoke_ok": True,
                                           "smoke_verdict": "ok",
                                           "pane_clean": True,
                                           "inbox_state": "no_pending",
                                           "mismatches": [],
                                           "found_markers": [],
                                           "cached": False})

        rc, _, _ = run_cli(["runtime", "verify", "worker_a", "--json"])
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))

    assert rc == 0
    assert "worker_a" not in data["agents"]
    assert "worker_b" in data["agents"]


def test_runtime_verify_unknown_agent_returns_unknown():
    with isolated_env():
        rc, out, _ = run_cli(["runtime", "verify", "no_agent", "--json"])
        data = json.loads(out)
        assert data["verdict"] == "unknown"
        assert rc == 1


def test_runtime_events_empty_returns_empty_list():
    with isolated_env():
        path = verify._switch_events_path()
        if path.exists():
            path.unlink()
        rc, out, _ = run_cli(["runtime", "events", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert data == []


def test_runtime_events_lists_recent(monkeypatch):
    with isolated_env():
        path = verify._switch_events_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"ts": 100.0, "agent": "a", "from_runtime": "x",
                        "to_runtime": "y", "reason": "rate_limit",
                        "outcome": "ready", "trigger": "watchdog"}) + "\n"
            + json.dumps({"ts": 200.0, "agent": "b", "from_runtime": "p",
                          "to_runtime": "q", "reason": "auth_failure",
                          "outcome": "env_drift", "trigger": "manual_cli"}) + "\n",
            encoding="utf-8",
        )
        rc, out, _ = run_cli(["runtime", "events", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert len(data) == 2
        assert data[1]["agent"] == "b"


def test_runtime_events_last_n():
    with isolated_env():
        path = verify._switch_events_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for i in range(5):
            lines.append(json.dumps({"ts": float(i), "agent": f"a{i}",
                                     "outcome": "ready"}))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rc, out, _ = run_cli(["runtime", "events", "--last", "2", "--json"])
        data = json.loads(out)
        assert len(data) == 2
        assert data[-1]["agent"] == "a4"
