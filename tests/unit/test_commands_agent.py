from __future__ import annotations

from helpers import isolated_env, run_cli


def test_agent_lock_updates_existing_dispatch_flag():
    toml = """
[team.agents.worker_school]
runtime = "x"
enabled_for_dispatch = true
"""
    with isolated_env() as tmp:
        cfg = tmp / "eduflow.toml"
        cfg.write_text(toml, encoding="utf-8")

        rc, out, err = run_cli(["agent", "lock", "worker_school"])

        assert rc == 0
        assert err == ""
        assert '"action": "lock"' in out
        assert "enabled_for_dispatch = false" in cfg.read_text(encoding="utf-8")


def test_agent_lock_inserts_missing_dispatch_flag():
    toml = """
[team.agents.worker_teacher]
runtime = "x"
lazy = false

[team.agents.manager]
runtime = "y"
"""
    with isolated_env() as tmp:
        cfg = tmp / "eduflow.toml"
        cfg.write_text(toml, encoding="utf-8")

        rc, out, err = run_cli(["agent", "lock", "worker_teacher"])

        assert rc == 0
        assert err == ""
        text = cfg.read_text(encoding="utf-8")
        section = text.split("[team.agents.manager]", 1)[0]
        assert "enabled_for_dispatch = false" in section
