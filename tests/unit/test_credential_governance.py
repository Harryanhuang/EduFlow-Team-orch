"""G0.3 credential-governance regression tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from helpers import captured_stderr, env_patch, isolated_env
from eduflow.runtime import agent_auth, config, tunables


def test_config_load_warns_when_group_or_world_writable():
    """A writable deployment config is an integrity boundary violation."""
    with isolated_env() as tmp:
        config_path = tmp / "eduflow.toml"
        config_path.write_text("[team]\nsession = \"T\"\n", encoding="utf-8")
        config_path.chmod(0o666)
        tunables.reset_cache()

        with captured_stderr() as stderr:
            assert tunables.load()["team"]["session"] == "T"

    warning = stderr.getvalue()
    assert "insecure config permissions" in warning
    assert "group/other writable" in warning


def test_secret_file_rejects_group_or_world_readable_permissions():
    """A secrets source must not silently load when other users can read it."""
    with isolated_env() as tmp:
        secrets_path = tmp / "operator.env"
        secrets_path.write_text(
            "OPENAI_API_KEY=unit-test-placeholder\n", encoding="utf-8")
        secrets_path.chmod(0o644)
        with env_patch(EDUFLOW_SECRETS_FILE=str(secrets_path)):
            agent_auth._cached_load_secrets.cache_clear()
            try:
                with pytest.raises(PermissionError, match="secrets file permissions"):
                    agent_auth.load_secrets()
            finally:
                agent_auth._cached_load_secrets.cache_clear()


def test_runtime_dotenv_rejects_group_or_world_readable_permissions():
    """The project-local source used for pane startup has the same rule."""
    from eduflow.runtime import lifecycle

    with isolated_env() as tmp:
        dotenv_path = tmp / ".env"
        dotenv_path.write_text(
            "ANTHROPIC_AUTH_TOKEN=unit-test-placeholder\n", encoding="utf-8")
        dotenv_path.chmod(0o644)

        with pytest.raises(PermissionError, match="secrets file permissions"):
            lifecycle._dotenv_values()


def test_local_credential_inputs_are_ignored_by_git():
    """Only the tracked example config may represent credential setup."""
    repo_root = Path(__file__).parents[2]
    expected = {
        "eduflow.toml",
        "eduflow.local.toml",
        ".env",
        "secrets/provider.env",
    }
    result = subprocess.run(
        [
            "git", "check-ignore", "--stdin",
            "--no-index",
        ],
        cwd=repo_root,
        check=False,
        input="\n".join(sorted(expected)) + "\n",
        text=True,
        stdout=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert set(result.stdout.splitlines()) == expected


def test_example_config_supplies_the_loader_chat_id_and_no_tracked_deployment_file():
    repo_root = Path(__file__).parents[2]
    example_path = repo_root / "eduflow.example.toml"
    with env_patch(EDUFLOW_CONFIG_FILE=str(example_path)):
        tunables.reset_cache()
        assert config.chat_id() == "oc_replace_me"
        assert config.agent_names() == ["manager", "worker"]
        assert config.env_profile_config("provider_primary")["ANTHROPIC_BASE_URL"] == "https://provider.example"
    tunables.reset_cache()

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "eduflow.toml"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert tracked.returncode == 1
