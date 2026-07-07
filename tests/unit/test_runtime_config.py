"""Tests for runtime registry resolution in runtime/config.py."""
from __future__ import annotations

from helpers import env_patch, isolated_env
from eduflow.runtime import config, tunables


def _write_toml(tmp, text: str) -> None:
    path = tmp / "eduflow.toml"
    path.write_text(text, encoding="utf-8")
    tunables.reset_cache()


def test_agent_cli_and_model_fall_back_to_legacy_agent_fields():
    team = {
        "session": "T",
        "default_model": "opus",
        "agents": {
            "worker": {"cli": "codex-cli", "model": "gpt-5.5"},
        },
    }
    with isolated_env(team=team):
        assert config.agent_cli("worker") == "codex-cli"
        assert config.agent_model("worker") == "gpt-5.5"


def test_runtime_registry_resolves_agent_runtime_from_toml():
    team = {"session": "T", "agents": {"worker": {"runtime": "course_primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "course_primary"
role = "worker"

[runtime_registry.course_primary]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "claude_proxy_primary"
fallback_to = "curriculum_backup"
switch_on = ["spawn_failed", "ready_timeout"]

[runtime_registry.curriculum_backup]
cli = "codex-cli"
model = "gpt-5.5"
provider = "openai"
env_profile = "codex_primary"
switch_on = ["spawn_failed", "ready_timeout"]
""")
        resolved = config.resolved_agent_config("worker")
        assert resolved["selected_runtime"] == "course_primary"
        assert resolved["cli"] == "claude-code"
        assert resolved["model"] == "sonnet"
        assert resolved["provider"] == "anthropic-proxy"
        assert len(resolved["runtime_chain"]) == 2


def test_load_team_filters_archived_agents_from_toml():
    with isolated_env() as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.Sophon]
runtime = "sophon_primary"
role = "ops"

[team.agents.auto_ops]
archived = "renamed to Sophon"
enabled_for_dispatch = false
""")
        team = config.load_team()
        assert sorted(team["agents"]) == ["Sophon"]
        assert config.agent_names() == ["Sophon"]


def test_runtime_registry_selects_fallback_when_reason_matches():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["spawn_failed", "ready_timeout"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["spawn_failed"]
""")
        resolved = config.resolved_agent_config("worker", reason="spawn_failed")
        assert resolved["selected_runtime"] == "backup"
        assert resolved["cli"] == "codex-cli"
        assert resolved["model"] == "gpt-5.5"


def test_runtime_registry_keeps_primary_when_reason_has_no_matching_fallback():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["spawn_failed", "ready_timeout"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["spawn_failed"]
""")
        resolved = config.resolved_agent_config("worker", reason="rate_limit")
        assert resolved["selected_runtime"] == "primary"
        assert resolved["cli"] == "claude-code"


def test_runtime_registry_can_resolve_a_specific_live_runtime_by_name():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["auth_failure"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["auth_failure"]
""")
        resolved = config.resolved_agent_config("worker", runtime_name="backup")
        assert resolved["selected_runtime"] == "backup"
        assert resolved["cli"] == "codex-cli"
        assert resolved["model"] == "gpt-5.5"


def test_env_profile_config_reads_named_profile_from_toml():
    team = {"session": "T", "agents": {"worker": {"cli": "claude-code"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
cli = "claude-code"

[env_profiles.claude_proxy_primary]
ANTHROPIC_BASE_URL = "http://127.0.0.1:15721"
ANTHROPIC_MODEL = "qwen3.7-plus"
""")
        profile = config.env_profile_config("claude_proxy_primary")
        assert profile["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:15721"
        assert profile["ANTHROPIC_MODEL"] == "qwen3.7-plus"


def test_env_profile_config_expands_reference_syntax():
    """Profile values like ${VAR} pull from a distinct env var name so
    multiple providers can keep their own secrets in .env.
    """
    team = {"session": "T", "agents": {"worker": {"cli": "claude-code"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
cli = "claude-code"

[env_profiles.claude_proxy_kimi_primary]
ANTHROPIC_BASE_URL = "https://api.kimi.com/coding/"
ANTHROPIC_AUTH_TOKEN = "${KIMI_AUTH_TOKEN}"
ANTHROPIC_MODEL = "kimi-k2.7-code"
""")
        with env_patch(KIMI_AUTH_TOKEN="sk-kimi-secret"):
            profile = config.env_profile_config("claude_proxy_kimi_primary")
            assert profile["ANTHROPIC_BASE_URL"] == "https://api.kimi.com/coding/"
            assert profile["ANTHROPIC_AUTH_TOKEN"] == "sk-kimi-secret"
            assert profile["ANTHROPIC_MODEL"] == "kimi-k2.7-code"


def test_env_profile_config_falls_back_to_global_auth_when_reference_unset():
    """An unset ${VAR} reference leaves the key empty, so the existing
    backfill to ANTHROPIC_AUTH_TOKEN keeps older configs working.
    """
    team = {"session": "T", "agents": {"worker": {"cli": "claude-code"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
cli = "claude-code"

[env_profiles.claude_proxy_primary]
ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
ANTHROPIC_AUTH_TOKEN = "${QWEN_AUTH_TOKEN}"
""")
        with env_patch(ANTHROPIC_AUTH_TOKEN="sk-global-secret", QWEN_AUTH_TOKEN=None):
            profile = config.env_profile_config("claude_proxy_primary")
            assert profile["ANTHROPIC_AUTH_TOKEN"] == "sk-global-secret"


def test_fallback_runtime_returns_next_matching_runtime_after_current():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup_a"
switch_on = ["spawn_failed", "rate_limit"]

[runtime_registry.backup_a]
cli = "codex-cli"
model = "gpt-5.5"
fallback_to = "backup_b"
switch_on = ["auth_failure"]

[runtime_registry.backup_b]
cli = "qwen-code"
model = "qwen-max"
switch_on = ["rate_limit"]
""")
        fallback = config.fallback_runtime("worker", current_runtime="primary", reason="rate_limit")
        assert fallback is not None
        assert fallback["name"] == "backup_b"


def test_hermes_agent_cannot_be_lazy():
    team = {"session": "T", "agents": {"Hermes": {"cli": "hermes-agent", "lazy": True}}}
    with isolated_env(team=team):
        try:
            config.agent_config("Hermes")
        except ValueError as exc:
            assert "Hermes must not be lazy" in str(exc)
        else:
            raise AssertionError("expected Hermes lazy config to fail")


def test_fallback_runtime_allows_backup_ring_without_returning_primary():
    team = {"session": "T", "agents": {"worker": {"runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        _write_toml(tmp, """
[team]
session = "T"

[team.agents.worker]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "qoderclicn"
model = "Qwen3.7-Max"
fallback_to = "backup_deepseek"
switch_on = ["rate_limit"]

[runtime_registry.backup_deepseek]
cli = "claude-code"
model = "sonnet"
env_profile = "claude_proxy_deepseek_backup"
fallback_to = "backup_qwen_plus"
switch_on = ["rate_limit"]

[runtime_registry.backup_qwen_plus]
cli = "claude-code"
model = "sonnet"
env_profile = "claude_proxy_primary"
fallback_to = "backup_deepseek"
switch_on = ["rate_limit"]
""")
        chain = config.resolve_runtime_chain("worker")
        assert [item["name"] for item in chain] == [
            "primary",
            "backup_deepseek",
            "backup_qwen_plus",
        ]

        fallback = config.fallback_runtime("worker", current_runtime="backup_deepseek", reason="rate_limit")
        assert fallback is not None
        assert fallback["name"] == "backup_qwen_plus"

        fallback = config.fallback_runtime("worker", current_runtime="backup_qwen_plus", reason="rate_limit")
        assert fallback is not None
        assert fallback["name"] == "backup_deepseek"
