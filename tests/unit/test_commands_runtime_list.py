"""Tests for `eduflow runtime list` — chain resolution + output formatting."""
from __future__ import annotations

import io
import contextlib

from helpers import isolated_env
from eduflow.commands import runtime_list
from eduflow.runtime import config, tunables


def _write_toml(tmp, text: str) -> None:
    path = tmp / "eduflow.toml"
    path.write_text(text, encoding="utf-8")
    tunables.reset_cache()


def _capture_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = runtime_list.main(argv)
    return rc, out.getvalue(), err.getvalue()


def _chain_toml() -> str:
    return """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[team.agents.manager]
runtime = "manager_primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "proxy_a"
fallback_to = "backup_b"
switch_on = ["spawn_failed", "rate_limit"]

[runtime_registry.backup_b]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "proxy_b"
switch_on = ["spawn_failed", "rate_limit"]

[runtime_registry.manager_primary]
cli = "claude-code"
model = "opus"
provider = "anthropic-proxy"
env_profile = "proxy_a"
fallback_to = "manager_backup"
switch_on = ["spawn_failed"]

[runtime_registry.manager_backup]
cli = "qwen-code"
model = "qwen-max"
provider = "anthropic-proxy"
env_profile = "proxy_b"
switch_on = ["spawn_failed"]

[env_profiles.proxy_a]
ANTHROPIC_BASE_URL = "http://a.example.com"
pool_id = "pool_a"
provider_family = "provider_a"

[env_profiles.proxy_b]
ANTHROPIC_BASE_URL = "http://b.example.com"
pool_id = "pool_b"
provider_family = "provider_b"
"""


def test_list_single_agent_returns_full_chain_with_status():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        result = runtime_list._chain_for_agent("worker")
        assert result["agent"] == "worker"
        names = [rt["name"] for rt in result["chain"]]
        assert names == ["primary", "backup_b"]
        # No runtime-status.json in isolated env → current_runtime = "unknown"
        assert result["current_runtime"] == "unknown"
        # Pool ids resolved from env_profiles
        pools = [rt["pool_id"] for rt in result["chain_with_status"]]
        assert pools == ["pool_a", "pool_b"]
        # Selected flag false everywhere (no status file)
        assert all(not rt["selected"] for rt in result["chain_with_status"])


def test_list_unknown_agent_returns_error_key():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        result = runtime_list._chain_for_agent("ghost")
        assert "error" in result
        assert result["chain"] == []


def test_list_main_returns_zero_for_known_agent():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        rc, out, err = _capture_main(["worker"])
        assert rc == 0
        assert "worker" in out
        assert "primary" in out
        assert "backup_b" in out
        assert "pool_a" in out
        assert "pool_b" in out


def test_list_main_returns_one_for_unknown_agent():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        rc, out, err = _capture_main(["ghost"])
        assert rc == 1
        assert "unknown agent" in err


def test_list_main_no_args_lists_all_agents():
    team = {"session": "T",
            "agents": {"worker": {"runtime": "primary"},
                       "manager": {"runtime": "manager_primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        rc, out, err = _capture_main([])
        assert rc == 0
        assert "worker" in out
        assert "manager" in out
        assert "manager_primary" in out


def test_list_main_json_output_is_list():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        import json
        rc, out, err = _capture_main(["worker", "--json"])
        assert rc == 0
        data = json.loads(out)
        assert isinstance(data, list)
        assert data[0]["agent"] == "worker"
        assert data[0]["current_runtime"] == "unknown"
        chain = data[0]["chain"]
        assert [rt["name"] for rt in chain] == ["primary", "backup_b"]
        # selected=False when no runtime-status.json
        assert all(not rt["selected"] for rt in chain)


def test_list_main_rejects_extra_args():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, _chain_toml())
        rc, out, err = _capture_main(["worker", "bogus"])
        assert rc == 1
        assert "unexpected args" in out
