"""Tests for runtime/lifecycle.py — pane_env_prefix + provision_pane.

Both helpers were extracted in round-16 from `commands/start.py` /
`commands/hire.py` but never got their own unit test (CLAUDE.md rule:
every new module ships its own unit test). The behaviour was covered
transitively through start/hire integration tests; this file pins
provision_pane directly for each of its four outcomes (LAZY / READY /
READY_NO_INIT / SPAWN_FAILED).
"""
from __future__ import annotations

from pathlib import Path
import json

from helpers import attr_patch, env_patch, isolated_env, tmux_patch
from eduflow.runtime import lifecycle, tmux, wake
from eduflow.runtime.lifecycle import (
    LAZY, READY, READY_NO_INIT, SPAWN_FAILED, CONFIG_ERROR,
    pane_env_prefix, provision_pane,
)
from eduflow.store import local_facts
from eduflow.runtime import paths


# ── pane_env_prefix ───────────────────────────────────────────────


def test_pane_env_prefix_always_includes_state_dir():
    """Even with no other env set, STATE_DIR is always emitted so the
    spawned pane never falls back to ~/.eduflow."""
    with isolated_env(team={"agents": {"a": {}}}):
        prefix = pane_env_prefix()
    assert prefix.startswith("EDUFLOW_STATE_DIR=")


def test_pane_env_prefix_propagates_lark_profile_when_set():
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            LARK_CLI_PROFILE="prod"):
        prefix = pane_env_prefix()
    assert "LARK_CLI_PROFILE=prod" in prefix


def test_pane_env_prefix_propagates_config_file_when_set():
    with isolated_env(team={"agents": {"a": {}}}) as tmp, env_patch(
            EDUFLOW_CONFIG_FILE=str(tmp / "eduflow.toml")):
        prefix = pane_env_prefix()
    assert "EDUFLOW_CONFIG_FILE=" in prefix
    assert str(tmp / "eduflow.toml") in prefix


def test_pane_env_prefix_propagates_path_when_set():
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            PATH="/opt/homebrew/bin:/usr/bin:/bin"):
        prefix = pane_env_prefix()
    assert "PATH=" in prefix
    assert "/opt/homebrew/bin:/usr/bin:/bin" in prefix


def test_pane_env_prefix_skips_unset_vars():
    """Vars not present in the operator shell don't pollute the prefix."""
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            LARK_CLI_PROFILE=None,
            LARK_CLI_NO_PROXY=None,
            EDUFLOW_LARK_SEND_AS=None,
            EDUFLOW_DEFAULT_MODEL=None):
        prefix = pane_env_prefix()
    # Only state_dir survives (team_file/runtime_config are set by isolated_env)
    assert "LARK_CLI_PROFILE=" not in prefix
    assert "LARK_CLI_NO_PROXY=" not in prefix


def test_pane_env_prefix_propagates_feishu_app_credentials():
    """Bringup B5: tmux server started by an earlier checkout had its
    own global env without FEISHU_APP_*; new panes inherited that env
    and tenant_token_from_env() returned None → fell back to the saved
    lark-cli profile (an OLD app) → HTTP 400 on every eduflow say.
    Embedding the creds in the spawn-cmd prefix sidesteps the
    tmux-server-env quirk."""
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            FEISHU_APP_ID="cli_NEW",
            FEISHU_APP_SECRET="newSecret123",
            LARKSUITE_CLI_APP_ID="cli_NEW",
            LARKSUITE_CLI_APP_SECRET="newSecret123"):
        prefix = pane_env_prefix()
    assert "FEISHU_APP_ID=cli_NEW" in prefix
    assert "FEISHU_APP_SECRET=newSecret123" in prefix
    assert "LARKSUITE_CLI_APP_ID=cli_NEW" in prefix
    assert "LARKSUITE_CLI_APP_SECRET=newSecret123" in prefix


def test_pane_env_prefix_propagates_anthropic_gateway_env():
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            ANTHROPIC_AUTH_TOKEN="sk-test",
            ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic",
            ANTHROPIC_MODEL="qwen3.7-plus",
            ANTHROPIC_REASONING_MODEL="qwen3.7-plus",
            ANTHROPIC_DEFAULT_OPUS_MODEL="qwen3.7-plus",
            ANTHROPIC_DEFAULT_SONNET_MODEL="qwen3.7-plus",
            ANTHROPIC_DEFAULT_HAIKU_MODEL="qwen3.7-plus"):
        prefix = pane_env_prefix()
    assert "ANTHROPIC_AUTH_TOKEN=sk-test" in prefix
    assert "ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic" in prefix
    assert "ANTHROPIC_MODEL=qwen3.7-plus" in prefix
    assert "ANTHROPIC_REASONING_MODEL=qwen3.7-plus" in prefix


def test_pane_env_prefix_shell_quotes_paths_with_spaces():
    """shlex.quote should wrap any value containing whitespace; otherwise
    `eval $(...)` in a downstream shell would split on the space."""
    with isolated_env(team={"agents": {"a": {}}}), env_patch(
            LARK_CLI_PROFILE="my profile"):
        prefix = pane_env_prefix()
    # quoted form: 'my profile' (single quotes) — never raw `my profile`
    assert "'my profile'" in prefix


# ── provision_pane: LAZY ──────────────────────────────────────────


def test_provision_lazy_agent_sets_待命_and_skips_spawn():
    """Lazy agents in team.json get status 待命; spawn_agent is never
    called (the pane stays at a shell prompt)."""
    team = {"agents": {"sleepy": {"cli": "claude-code", "lazy": True}}}
    spawn_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: spawn_calls.append((str(t), c)) or True):
        outcome = provision_pane("sleepy", tmux.Target("S", "sleepy"))
        assert outcome == LAZY
        assert spawn_calls == []
        snap = local_facts.get_status("sleepy")
        assert snap["status"] == "待命"
        assert "lazy" in snap["task"]


# ── provision_pane: SPAWN_FAILED ──────────────────────────────────


def test_provision_spawn_failure_returns_spawn_failed():
    team = {"agents": {"a": {"cli": "claude-code"}}}
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: False):
        outcome = provision_pane("a", tmux.Target("S", "a"))
    assert outcome == SPAWN_FAILED


# ── provision_pane: READY (happy path) ────────────────────────────


def test_provision_ready_spawns_then_injects_init_prompt():
    """Happy path: spawn succeeds, wait_until_ready true, identity init
    is injected, status flips to 进行中."""
    team = {"agents": {"alice": {"cli": "claude-code", "model": "opus"}}}
    spawn_calls = []
    inject_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: spawn_calls.append((str(t), c)) or True,
            inject=lambda t, text, **kw: inject_calls.append((str(t), text)) or True), \
            attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
        outcome = provision_pane("alice", tmux.Target("S", "alice"))
        assert outcome == READY
        assert len(spawn_calls) == 1
        # Identity init prompt was injected after spawn
        assert len(inject_calls) == 1
        assert "alice" in inject_calls[0][1]
        assert "identity.md" in inject_calls[0][1]
        snap = local_facts.get_status("alice")
        assert snap["status"] == "进行中"


def test_provision_ready_pane_env_prefix_baked_into_spawn_cmd():
    team = {"agents": {"a": {"cli": "claude-code"}}}
    spawn_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: spawn_calls.append((str(t), c)) or True,
            inject=lambda *a, **kw: True), \
            attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
        provision_pane("a", tmux.Target("S", "a"))
    cmd = spawn_calls[0][1]
    assert "EDUFLOW_STATE_DIR=" in cmd
    # Adapter contributed the actual CLI spawn after the env prefix
    assert "claude" in cmd


# ── provision_pane: READY_NO_INIT ─────────────────────────────────


def test_provision_ready_no_init_when_marker_never_appears():
    """When wait_until_ready times out, spawn already happened so the
    pane is alive — status still flips to 进行中, but the identity
    init prompt is NOT injected (no point injecting into a CLI that
    might still be loading)."""
    team = {"agents": {"a": {"cli": "claude-code"}}}
    inject_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: True,
            inject=lambda t, text, **kw: inject_calls.append((str(t), text)) or True), \
            attr_patch(wake, wait_until_ready=lambda *a, **kw: False):
        outcome = provision_pane("a", tmux.Target("S", "a"))
        assert outcome == READY_NO_INIT
        assert inject_calls == []  # no identity init when CLI not ready
        snap = local_facts.get_status("a")
        assert snap["status"] == "进行中"  # status still flips


def test_provision_retries_claude_ready_once_after_initial_timeout():
    team = {"agents": {"a": {"cli": "claude-code"}}}
    inject_calls = []
    waits = iter([False, True])

    def fake_wait(*args, **kwargs):
        return next(waits)

    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: True,
            inject=lambda t, text, **kw: inject_calls.append((str(t), text)) or True), \
            attr_patch(wake, wait_until_ready=fake_wait), \
            attr_patch(lifecycle.time, sleep=lambda s: None):
        outcome = provision_pane("a", tmux.Target("S", "a"))
        assert outcome == READY
        assert len(inject_calls) == 1


def test_provision_falls_back_to_next_runtime_on_spawn_failure():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "T"

[team.agents.a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["spawn_failed"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["spawn_failed"]
""", encoding="utf-8")
        spawn_calls = []
        inject_calls = []

        def fake_spawn(_target, cmd):
            spawn_calls.append(cmd)
            return len(spawn_calls) > 1

        with tmux_patch(
                spawn_agent=fake_spawn,
                inject=lambda t, text, **kw: inject_calls.append(text) or True), \
                attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            outcome = provision_pane("a", tmux.Target("S", "a"))

        assert outcome == READY
        assert len(spawn_calls) == 2
        assert "claude" in spawn_calls[0]
        assert "codex" in spawn_calls[1]


def test_provision_writes_runtime_status_file():
    team = {"agents": {"alice": {"cli": "claude-code", "model": "opus"}}}
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: True,
            inject=lambda *a, **kw: True), \
            attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
        outcome = provision_pane("alice", tmux.Target("S", "alice"))
        assert outcome == READY
        data = json.loads(paths.runtime_status_file().read_text(encoding="utf-8"))
        snap = data["agents"]["alice"]
        assert snap["runtime"] == "inline"
        assert snap["cli"] == "claude-code"
        assert snap["model"] == "opus"


def test_pane_spawn_prefix_for_runtime_injects_env_profile_vars():
    with isolated_env(team={"agents": {"a": {"cli": "claude-code"}}}) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "T"

[team.agents.a]
cli = "claude-code"

[env_profiles.claude_proxy_primary]
ANTHROPIC_BASE_URL = "http://127.0.0.1:15721"
ANTHROPIC_MODEL = "qwen3.7-plus"
""", encoding="utf-8")
        resolved = {
            "env_profile": "claude_proxy_primary",
            "cli": "claude-code",
            "model": "sonnet",
        }
        prefix = lifecycle.pane_spawn_prefix_for_runtime(resolved)
        assert "ANTHROPIC_BASE_URL=http://127.0.0.1:15721" in prefix
        assert "ANTHROPIC_MODEL=qwen3.7-plus" in prefix


def test_provision_does_not_retry_non_claude_on_timeout():
    team = {"agents": {"a": {"cli": "codex-cli", "model": "gpt-5.5"}}}
    inject_calls = []
    waits = []

    def fake_wait(*args, **kwargs):
        waits.append(1)
        return False

    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda t, c: True,
            inject=lambda t, text, **kw: inject_calls.append((str(t), text)) or True), \
            attr_patch(wake, wait_until_ready=fake_wait), \
            attr_patch(lifecycle.time, sleep=lambda s: None):
        outcome = provision_pane("a", tmux.Target("S", "a"))
        assert outcome == READY_NO_INIT
        assert inject_calls == []
        assert len(waits) == 1


def test_restart_with_runtime_ready_no_init_still_persists_runtime_and_nudges_latest_inbox():
    from helpers import attr_patch

    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["rate_limit"]
""", encoding="utf-8")
        local_facts.append_message("manager", "review_course", "latest verdict", priority="高")
        inject_calls = []
        with tmux_patch(
            send_keys=lambda *a, **kw: True,
            inject=lambda t, text, **kw: inject_calls.append(text) or True,
        ), attr_patch(
            lifecycle, _spawn_once=lambda agent, target, resolved, **kw: (READY_NO_INIT, "")
        ):
            outcome = lifecycle.restart_with_runtime(
                "manager", tmux.Target("S", "manager"), "backup", reason="watchdog:rate_limit"
            )
        assert outcome == READY_NO_INIT
        data = json.loads(paths.runtime_status_file().read_text(encoding="utf-8"))
        snap = data["agents"]["manager"]
        assert snap["runtime"] == "backup"
        assert snap["cli"] == "codex-cli"
        assert inject_calls
        assert "latest inbox" in inject_calls[0] or "恢复后先处理最新 inbox" in inject_calls[0]


def test_restart_with_runtime_respawns_instead_of_typing_into_degraded_cli():
    """A degraded CLI may still capture input after Ctrl-C, so runtime
    fallback must replace the pane command instead of typing a new spawn
    command into the old UI.
    """
    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["rate_limit"]
""", encoding="utf-8")
        respawn_calls = []
        spawn_calls = []
        send_key_calls = []
        with tmux_patch(
            respawn_agent=lambda target, cmd: respawn_calls.append((str(target), cmd)) or True,
            spawn_agent=lambda target, cmd: spawn_calls.append((str(target), cmd)) or True,
            send_keys=lambda target, *keys, **kw: send_key_calls.append((str(target), keys)) or True,
            inject=lambda *a, **kw: True,
        ), attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            outcome = lifecycle.restart_with_runtime(
                "manager",
                tmux.Target("S", "manager"),
                "backup",
                reason="watchdog:rate_limit",
                nudge_latest_inbox=False,
            )
        assert outcome == READY
        assert len(respawn_calls) == 1
        assert "codex" in respawn_calls[0][1]
        assert spawn_calls == []
        assert all(keys != ("C-c",) for _target, keys in send_key_calls)


# ── provision_pane: CONFIG_ERROR (round-61) ──────────────────────


def test_provision_returns_config_error_on_unknown_cli():
    """REGRESSION: a typo in team.json's `cli` field (e.g. 'claude-cod'
    missing the e) used to raise KeyError straight through start.py,
    killing the entire eduflow start. Now returns CONFIG_ERROR so
    the caller can warn + skip + continue with the rest of the team."""
    import io
    import contextlib
    team = {"agents": {"typo_agent": {"cli": "claude-cod"}}}  # unknown CLI
    err = io.StringIO()
    with isolated_env(team=team), \
            contextlib.redirect_stderr(err):
        outcome = provision_pane("typo_agent", tmux.Target("S", "typo_agent"))
    assert outcome == CONFIG_ERROR
    # Stderr explains which agent + what's wrong
    assert "typo_agent" in err.getvalue()
    assert "claude-cod" in err.getvalue() or "unknown cli" in err.getvalue()


# ── _ensure_claude_agent_home (R172.b) ───────────────────────────


def test_ensure_claude_agent_home_does_not_raise_when_data_missing():
    """On hosts without /data (macOS, test runners), the helper falls
    back to <state_dir>/agent-home/<agent>. Boss-flagged 2026-05-05:
    don't crash eduflow start outside Docker."""
    import os
    if os.path.exists("/data"):
        return  # skip on Linux containers; helper does real work there
    # Must not raise on missing /data — falls back to state_dir
    lifecycle._ensure_claude_agent_home("manager")
    lifecycle._ensure_claude_agent_home("worker_cc")


def test_ensure_claude_agent_home_seeds_local_claude_shim():
    """Host multi-HOME setup: Claude Code expects ~/.local/bin/claude
    under the agent HOME and exits if it is missing. Provisioning should
    seed a shim that points at the real installed binary."""
    import shutil
    import os
    real_which = shutil.which
    try:
        shutil.which = lambda name: "/opt/homebrew/bin/claude" if name == "claude" else None
        with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
            lifecycle._ensure_claude_agent_home("manager")
            from eduflow.agents.claude_code import agent_home
            shim = Path(agent_home("manager")) / ".local" / "bin" / "claude"
            assert shim.exists(), "expected ~/.local/bin/claude shim"
            assert shim.is_symlink(), "expected shim to be a symlink"
            assert os.readlink(shim) == "/opt/homebrew/bin/claude"
    finally:
        shutil.which = real_which


def test_ensure_claude_agent_home_copies_host_settings_when_present():
    """Host Claude may rely on settings.json entries such as the local proxy-
    managed auth bridge, but eduflow's env_profile/model are the sole runtime
    authority. Agent homes should inherit host settings, then strip runtime
    authority keys (env/model/apiKeyHelper/forceLoginMethod) and add the
    bypass-confirmation key required for non-interactive Claude Code startup.
    """
    host_settings = Path.home() / ".claude" / "settings.json"
    if not host_settings.exists():
        return
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        copied = Path(agent_home("manager")) / ".claude" / "settings.json"
        assert copied.exists(), "expected agent settings.json"
        copied_data = json.loads(copied.read_text())
        host_data = json.loads(host_settings.read_text())
        runtime_authority_keys = {"env", "model", "apiKeyHelper", "forceLoginMethod"}
        for key, value in host_data.items():
            if key in runtime_authority_keys:
                assert key not in copied_data
            else:
                assert copied_data[key] == value
        assert copied_data["skipDangerousModePermissionPrompt"] is True


def test_ensure_claude_agent_home_copies_host_local_settings_when_present():
    """Per-agent HOME isolation must not drop the operator's user-local
    Claude permissions allowlist. Otherwise panes can re-enter manual
    confirmation loops even though the host profile already allows tools."""
    host_local_settings = Path.home() / ".claude" / "settings.local.json"
    if not host_local_settings.exists():
        return
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        copied = Path(agent_home("manager")) / ".claude" / "settings.local.json"
        assert copied.exists(), "expected agent settings.local.json"
        copied_data = json.loads(copied.read_text())
        host_data = json.loads(host_local_settings.read_text())
        assert copied_data == host_data


def test_ensure_claude_agent_home_seeds_bypass_acceptance_state():
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        home = Path(agent_home("manager"))
        settings = json.loads((home / ".claude" / "settings.json").read_text())
        claude_json = json.loads((home / ".claude.json").read_text())
        assert settings["skipDangerousModePermissionPrompt"] is True
        assert claude_json["bypassPermissionsModeAccepted"] is True


def test_ensure_claude_agent_home_marks_current_workdir_trusted():
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        home = Path(agent_home("manager"))
        claude_json = json.loads((home / ".claude.json").read_text())
        project = claude_json["projects"][str(Path.cwd())]
        assert project["hasTrustDialogAccepted"] is True
        assert project["hasCompletedProjectOnboarding"] is True


def test_ensure_claude_agent_home_writes_keychain_extract_as_regular_file():
    """macOS host: when `security find-generic-password` succeeds, write
    the result as a *regular file* (not a symlink). Earlier impl
    symlinked to ~/.claude/.credentials.json which (a) goes stale
    versus the live keychain and (b) gets atomic-replaced by claude on
    refresh, defeating the share intent. 2026-05-07 host smoke ate
    'refreshToken: ""' for breakfast — pin the regular-file invariant."""
    import platform
    if platform.system() != "Darwin":
        return  # macOS-only path
    import subprocess
    fresh_creds = ('{"claudeAiOauth":{"accessToken":"a-tok",'
                   '"refreshToken":"r-tok","expiresAt":9999999999000}}')
    def fake_run(argv, **kw):
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout=fresh_creds, stderr="")
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}), \
            attr_patch(subprocess, run=fake_run):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        cred = Path(agent_home("manager")) / ".claude" / ".credentials.json"
        assert cred.exists(), "creds file not materialised"
        assert not cred.is_symlink(), "expected regular file, got symlink"
        assert "r-tok" in cred.read_text(), \
            "expected fresh keychain content, got stale"


def test_ensure_claude_agent_home_overwrites_stale_creds_each_call():
    """Re-extract on every call: prior stale snapshot is overwritten so
    `eduflow down && eduflow up` actually re-materialises from
    keychain. Old impl gated on `if not cred_link.exists()` so the
    file never refreshed once written."""
    import platform
    if platform.system() != "Darwin":
        return
    import subprocess
    tokens = iter(["v1-tok", "v2-tok"])
    def fake_run(argv, **kw):
        tok = next(tokens, "vN-tok")
        body = ('{"claudeAiOauth":{"accessToken":"a","refreshToken":"%s",'
                '"expiresAt":9999999999000}}' % tok)
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout=body, stderr="")
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}), \
            attr_patch(subprocess, run=fake_run):
        lifecycle._ensure_claude_agent_home("manager")
        from eduflow.agents.claude_code import agent_home
        cred = Path(agent_home("manager")) / ".claude" / ".credentials.json"
        assert "v1-tok" in cred.read_text()
        lifecycle._ensure_claude_agent_home("manager")
        # Second call must replace the file with v2's content
        assert "v2-tok" in cred.read_text(), \
            "stale snapshot not overwritten on re-provision"


# ── restart_with_runtime: proved-ready gate ─────────────────────


def test_restart_with_runtime_prove_ready_returns_env_drift_on_mismatch(monkeypatch):
    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "claude-code"
model = "sonnet"
env_profile = "ds"
switch_on = ["rate_limit"]

[env_profiles.ds]
ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_MODEL = "deepseek-v4-pro"
""", encoding="utf-8")
        with tmux_patch(
            respawn_agent=lambda target, cmd: True,
            spawn_agent=lambda target, cmd: True,
            send_keys=lambda target, *keys, **kw: True,
            inject=lambda *a, **kw: True,
        ), attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            # live env says wrong BASE_URL → env_drift
            from eduflow.runtime import verify as verify_mod
            monkeypatch.setattr(verify_mod, "verify_live_env_matches_profile",
                                lambda target, name: (False, ["ANTHROPIC_BASE_URL expected=X live=Y"]))
            monkeypatch.setattr(lifecycle, "_verify_no_failure_markers",
                                lambda target, adapter, **kw: (True, []))
            outcome = lifecycle.restart_with_runtime(
                "manager", tmux.Target("S", "manager"), "backup",
                reason="watchdog:rate_limit", nudge_latest_inbox=False,
            )
        assert outcome == lifecycle.ENV_DRIFT
        data = json.loads(paths.runtime_status_file().read_text(encoding="utf-8"))
        snap = data["agents"]["manager"]
        assert snap["env_ok"] is False
        # verified_at must NOT be written on env_drift (partial proof).
        assert "verified_at" not in snap


def test_restart_with_runtime_prove_ready_returns_smoke_failed_on_429(monkeypatch):
    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "claude-code"
model = "sonnet"
env_profile = "ds"
switch_on = ["rate_limit"]

[env_profiles.ds]
ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_MODEL = "deepseek-v4-pro"
""", encoding="utf-8")
        with tmux_patch(
            respawn_agent=lambda target, cmd: True,
            spawn_agent=lambda target, cmd: True,
            send_keys=lambda target, *keys, **kw: True,
            inject=lambda *a, **kw: True,
        ), attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            from eduflow.runtime import verify as verify_mod
            monkeypatch.setattr(verify_mod, "verify_live_env_matches_profile",
                                lambda target, name: (True, []))
            # api smoke returns 429 → smoke_failed
            monkeypatch.setattr(verify_mod, "api_smoke_runtime",
                                lambda resolved, **kw: ("failed", "http 429"))
            outcome = lifecycle.restart_with_runtime(
                "manager", tmux.Target("S", "manager"), "backup",
                reason="watchdog:rate_limit", nudge_latest_inbox=False,
            )
        assert outcome == lifecycle.SMOKE_FAILED
        data = json.loads(paths.runtime_status_file().read_text(encoding="utf-8"))
        snap = data["agents"]["manager"]
        assert snap["smoke_ok"] is False
        # verified_at must NOT be written on smoke_failed (partial proof).
        assert "verified_at" not in snap


def test_verify_no_failure_markers_flags_repetitive_tool_call_history():
    class _Adapter:
        def ready_markers(self):
            return ["bypass permissions on"]

        def rate_limit_markers(self):
            return []

    target = tmux.Target("S", "manager")
    text = (
        "old auth required before ready\n"
        "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
        "API Error: 400 <400> InternalError.Algo.InvalidParameter: "
        "Repetitive tool calls detected in the conversation history.\n"
    )
    clean, found = lifecycle._verify_no_failure_markers(
        target,
        _Adapter(),
        wait_s=0,
        capture_fn=lambda _target, _lines: text,
    )
    assert clean is False
    assert found == ["conversation_history_corrupt:Repetitive tool calls detected"]


def test_verify_no_failure_markers_ignores_codex_unauthorized_transcript():
    class _Adapter:
        def ready_markers(self):
            return ["OpenAI Codex", "permissions: YOLO"]

        def rate_limit_markers(self):
            return []

        def process_name(self):
            return "codex"

    target = tmux.Target("S", "manager")
    text = (
        "╭─────────────────────────────────────────────────────╮\n"
        "│ >_ OpenAI Codex (v0.142.0)                          │\n"
        "│ permissions: YOLO mode                              │\n"
        "╰─────────────────────────────────────────────────────╯\n"
        "上一轮 route probe 返回 Unauthorized，我继续排查。\n"
        "› 下一步\n"
    )
    clean, found = lifecycle._verify_no_failure_markers(
        target,
        _Adapter(),
        wait_s=0,
        capture_fn=lambda _target, _lines: text,
    )
    assert clean is True
    assert found == []


def test_restart_with_runtime_prove_ready_returns_ready_when_all_pass(monkeypatch):
    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["rate_limit"]
""", encoding="utf-8")
        with tmux_patch(
            respawn_agent=lambda target, cmd: True,
            spawn_agent=lambda target, cmd: True,
            send_keys=lambda target, *keys, **kw: True,
            inject=lambda *a, **kw: True,
        ), attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            from eduflow.runtime import verify as verify_mod
            monkeypatch.setattr(verify_mod, "verify_live_env_matches_profile",
                                lambda target, name: (True, []))
            monkeypatch.setattr(verify_mod, "api_smoke_runtime",
                                lambda resolved, **kw: ("skipped", "codex v1"))
            monkeypatch.setattr(lifecycle, "_verify_no_failure_markers",
                                lambda target, adapter, **kw: (True, []))
            outcome = lifecycle.restart_with_runtime(
                "manager", tmux.Target("S", "manager"), "backup",
                reason="watchdog:rate_limit", nudge_latest_inbox=False,
            )
        assert outcome == READY
        data = json.loads(paths.runtime_status_file().read_text(encoding="utf-8"))
        snap = data["agents"]["manager"]
        assert snap["env_ok"] is True
        assert snap["smoke_ok"] is True
        assert "verified_at" in snap


def test_restart_with_runtime_prove_ready_false_skips_gate(monkeypatch):
    """Opt-out: prove_ready=False keeps old behavior for callers that
    need best-effort switching without verification."""
    team = {"agents": {"manager": {"cli": "claude-code", "runtime": "primary"}}}
    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.manager]
runtime = "primary"
role = "manager"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"

[runtime_registry.backup]
cli = "claude-code"
model = "sonnet"
env_profile = "ds"
switch_on = ["rate_limit"]

[env_profiles.ds]
ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_MODEL = "deepseek-v4-pro"
""", encoding="utf-8")
        with tmux_patch(
            respawn_agent=lambda target, cmd: True,
            spawn_agent=lambda target, cmd: True,
            send_keys=lambda target, *keys, **kw: True,
            inject=lambda *a, **kw: True,
        ), attr_patch(wake, wait_until_ready=lambda *a, **kw: True):
            from eduflow.runtime import verify as verify_mod
            # Even with env drift, prove_ready=False returns READY.
            monkeypatch.setattr(verify_mod, "verify_live_env_matches_profile",
                                lambda target, name: (False, ["mismatch"]))
            outcome = lifecycle.restart_with_runtime(
                "manager", tmux.Target("S", "manager"), "backup",
                reason="watchdog:rate_limit", nudge_latest_inbox=False,
                prove_ready=False,
            )
        assert outcome == READY
