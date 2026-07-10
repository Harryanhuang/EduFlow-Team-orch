"""Pane provisioning shared between `start` and `hire`.

`provision_pane(agent, target)` writes identity, handles lazy panes,
spawns the configured CLI, waits for the ready banner, injects the
identity init prompt, and updates the agent's status row. Both
`commands/start.py` (looping over the team) and `commands/hire.py`
(single agent) call into this so the spawn-and-init contract lives in
one place.

Returns one of five outcome strings (callers render differently):
  LAZY            agent has `lazy: true` in team.json; no spawn attempted,
                  status set to 待命
  READY           CLI spawned + ready marker seen + identity init injected
  READY_NO_INIT   CLI spawned but ready marker didn't appear in 20s;
                  identity init skipped (caller surfaces a warning)
  SPAWN_FAILED    `tmux.spawn_agent` returned False (tmux send-keys failed)
  CONFIG_ERROR    bad `cli` value (typo, dropped adapter) caught as
                  KeyError on adapter lookup; caller logs + skips this
                  agent, keeps going for the rest of the team rather
                  than aborting the whole `eduflow start`.

Also home for `pane_env_prefix()` — the shell env-var prefix prepended
to every spawn_cmd so worker agents inherit `EDUFLOW_STATE_DIR` and
the Feishu env into their `eduflow say` shell-outs.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import time
from pathlib import Path

from eduflow.agents import get_adapter, identity
from eduflow.agents.codex_cli import ensure_workdir_trusted
from eduflow.runtime import config, paths, tmux, wake
from eduflow.store import local_facts
from eduflow.util import env_str


# env vars to propagate from the operator's shell into every spawned pane
# so worker agents' shell-out calls (via Bash tool) see the deployment's
# state dir instead of falling back to ~/.eduflow.
#
# FEISHU_APP_*/LARKSUITE_CLI_APP_* added 2026-05-08 (bringup B5): when
# tmux server was started by an earlier checkout's `eduflow up`, new
# panes inherit *its* global env (no FEISHU_APP_ID/SECRET). lark.py's
# tenant_token_from_env() returned None and fell back to the saved
# lark-cli profile — a different app — yielding HTTP 400 "Bot/User can
# NOT be out of the chat" on every `eduflow say`. Embedding the creds
# in the spawn-cmd prefix sidesteps the tmux-server-env quirk entirely.
_PROPAGATED_ENV = (
    "LARK_CLI_PROFILE",
    "LARK_CLI_NO_PROXY",
    "EDUFLOW_LARK_SEND_AS",
    "EDUFLOW_CONFIG_FILE",
    "EDUFLOW_TEAM_FILE",
    "EDUFLOW_RUNTIME_CONFIG",
    "EDUFLOW_DEFAULT_MODEL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_REASONING_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "HERMES_AUTH_TOKEN",
    "HERMES_API_KEY",
    "HERMES_BASE_URL",
    "HERMES_MODEL",
    "HERMES_PROVIDER",
    "FEISHU_APP_ID",
    "FEISHU_APP_SECRET",
    "LARKSUITE_CLI_APP_ID",
    "LARKSUITE_CLI_APP_SECRET",
)


_PROFILE_ENV_KEYS = (
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_REASONING_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HERMES_AUTH_TOKEN",
    "HERMES_API_KEY",
    "HERMES_BASE_URL",
    "HERMES_MODEL",
    "HERMES_PROVIDER",
)

_CLAUDE_RUNTIME_SETTINGS_KEYS = {
    "env",
    "model",
    "apiKeyHelper",
    "forceLoginMethod",
}


def _dotenv_values() -> dict[str, str]:
    """Best-effort load of `<config_dir>/.env` without mutating os.environ.

    Host bringup often keeps Anthropic-compatible gateway vars in the
    project-local `.env`. When `eduflow start` is launched from a
    clean shell, tmux panes still need those values to inherit the same
    provider auth/model path as the operator shell.
    """
    env_file = paths.config_file().parent / ".env"
    if not env_file.exists():
        return {}
    values: dict[str, str] = {}
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    except OSError:
        return {}
    return values


def _path_readable(p: Path) -> bool:
    """Returns True iff `p` can be stat'd. False on PermissionError /
    not-found / any OSError. deploy-issues 2026-05-08 #1: on Linux host
    where /root is mode 700, Path("/root/...").exists() raised
    PermissionError instead of returning False (Python <3.13 behavior),
    killing `eduflow up` for non-root deployers. Three /root probes
    in this module need the soft semantic."""
    try:
        return p.exists()
    except OSError:
        return False


def _merge_json_file(path: Path, updates: dict) -> None:
    """Best-effort shallow JSON merge for Claude state files."""
    data = {}
    if _path_readable(path):
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (OSError, json.JSONDecodeError):
            data = {}
    data.update(updates)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _ensure_claude_bypass_acceptance(home: Path) -> None:
    """Pre-seed Claude Code's bypass-permissions confirmation state.

    Claude Code 2.1.181 checks both the current settings key and a legacy
    top-level ~/.claude.json key during startup/migration. Seed both so pane
    startup does not depend on fragile tmux keypresses into the TUI dialog.
    """
    _merge_json_file(
        home / ".claude" / "settings.json",
        {"skipDangerousModePermissionPrompt": True},
    )
    _merge_json_file(
        home / ".claude.json",
        {"bypassPermissionsModeAccepted": True},
    )


def _ensure_claude_workdir_trusted(home: Path, workdir: Path) -> None:
    """Pre-seed Claude Code's per-project trust bit for the current repo."""
    claude_json = home / ".claude.json"
    data = {}
    if _path_readable(claude_json):
        try:
            loaded = json.loads(claude_json.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (OSError, json.JSONDecodeError):
            data = {}
    projects = data.setdefault("projects", {})
    row = projects.get(str(workdir))
    if not isinstance(row, dict):
        row = {}
        projects[str(workdir)] = row
    row["hasTrustDialogAccepted"] = True
    row.setdefault("hasCompletedProjectOnboarding", True)
    row.setdefault("projectOnboardingSeenCount", 1)
    try:
        claude_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    except OSError:
        pass


def _ensure_claude_agent_home(agent: str) -> None:
    """Materialise a per-agent claude state dir at /data/agent-home/<agent>.

    Each claude pane spawns with `HOME=/data/agent-home/<agent>` so
    each agent has its own `~/.claude.json` (avoids the shared-file
    write-race that corrupts a single-mount setup). The directory
    contains:
      .claude/settings.json     — silent-launch flags (theme, perms)
      .claude/.credentials.json — symlink to /root/.claude/.credentials.json
                                  so OAuth tokens stay bind-mount shared
      .claude/projects          — symlink to /root/.claude/projects
                                  so ccusage in /usage finds session logs
    Best-effort: if /data isn't writable (host tests where the path
    doesn't exist), silently skip and let claude fall back to its
    default `$HOME` discovery.
    """
    from eduflow.agents.claude_code import agent_home as _agent_home
    home = Path(_agent_home(agent))
    claude_dir = home / ".claude"
    try:
        claude_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    # Host fallback: claude on macOS keys keychain lookup by $HOME, so a
    # per-agent HOME with no .credentials.json gets "Not logged in" even
    # though the keychain entry exists for the user. Export it to a file
    # the first time so each pane has working OAuth.
    cred_link = claude_dir / ".credentials.json"
    # macOS host: prefer the live keychain over a (potentially-stale) host
    # ~/.claude/.credentials.json. Claude refreshes OAuth into the keychain
    # but only writes the file occasionally, so a symlink to the host file
    # can hand the pane a `refreshToken` the server has already revoked.
    # 2026-05-07 caught: pane symlinked to stale host file, refresh
    # round-tripped 401, claude blanked the field, pane logged "401
    # Invalid auth credentials". Re-extract on every provision and write
    # a *regular file* — not a symlink — because claude's atomic-write
    # of credentials replaces the symlink target with a plain file on
    # first refresh anyway, defeating the original sharing intent.
    import platform
    keychain_extracted = False
    if platform.system() == "Darwin":
        import subprocess
        try:
            out = subprocess.run(
                ["security", "find-generic-password",
                 "-s", "Claude Code-credentials", "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                if cred_link.is_symlink() or cred_link.exists():
                    cred_link.unlink()
                cred_link.write_text(out.stdout)
                keychain_extracted = True
        except (OSError, subprocess.TimeoutExpired):
            # `security` missing / keychain locked / subprocess timeout →
            # silent skip and fall through to the host-file branch below.
            pass
    if not keychain_extracted and not cred_link.exists():
        user_creds = Path.home() / ".claude" / ".credentials.json"
        if user_creds.exists():
            try:
                # Copy, not symlink: claude's atomic-write replaces the
                # symlink with a plain file anyway, so start with one.
                cred_link.write_bytes(user_creds.read_bytes())
            except OSError:
                pass
    user_claude_json = Path.home() / ".claude.json"
    claude_json = home / ".claude.json"
    if _path_readable(user_claude_json) and not claude_json.exists():
        try:
            claude_json.write_bytes(user_claude_json.read_bytes())
        except OSError:
            pass
    settings = claude_dir / "settings.json"
    host_settings = Path.home() / ".claude" / "settings.json"
    if _path_readable(host_settings):
        try:
            settings.write_bytes(host_settings.read_bytes())
        except OSError:
            pass
    # Strip runtime-authority keys from agent settings.json — eduflow's
    # env_profile/model are the sole authorities for provider credentials
    # and model choice. Host settings may carry proxy/model choices
    # injected by CC Switch or similar tools; if left in place they can
    # silently override eduflow and cause auth failures or model drift.
    # Caught 2026-06-26/27: all agents inherited PROXY_MANAGED token → 401.
    if settings.exists():
        try:
            import json as _json
            from eduflow.util import write_json as _write_json
            _d = _json.loads(settings.read_text(encoding="utf-8"))
            removed = False
            if isinstance(_d, dict):
                for key in _CLAUDE_RUNTIME_SETTINGS_KEYS:
                    if key in _d:
                        del _d[key]
                        removed = True
            if removed:
                _write_json(settings, _d)
        except (OSError, _json.JSONDecodeError, ValueError):
            pass
    host_local_settings = Path.home() / ".claude" / "settings.local.json"
    local_settings = claude_dir / "settings.local.json"
    if _path_readable(host_local_settings):
        try:
            local_settings.write_bytes(host_local_settings.read_bytes())
        except OSError:
            pass
    if not settings.exists():
        settings.write_text(
            '{\n'
            '  "skipDangerousModePermissionPrompt": true,\n'
            '  "hasCompletedOnboarding": true,\n'
            '  "theme": "dark",\n'
            '  "permissions": {\n'
            '    "allow": ["Bash", "Edit", "Read", "Write"]\n'
            '  }\n'
            '}\n'
        )
    cred_link = claude_dir / ".credentials.json"
    cred_target = Path("/root/.claude/.credentials.json")
    if _path_readable(cred_target) and not cred_link.exists():
        try:
            cred_link.symlink_to(cred_target)
        except OSError:
            pass
    projects_link = claude_dir / "projects"
    projects_target = Path("/root/.claude/projects")
    if _path_readable(projects_target) and not projects_link.exists():
        try:
            projects_link.symlink_to(projects_target)
        except OSError:
            pass
    # Seed ~/.claude.json from host's read-only mount once. Without
    # `userID` + `oauthAccount` keys claude pops the OAuth login
    # dialog (the credentials.json alone isn't enough — claude checks
    # ~/.claude.json for "you've completed login" state). After the
    # initial copy, the per-agent file is writable so claude can
    # update its own session counters without affecting other agents.
    claude_json = home / ".claude.json"
    host_claude_json = Path("/root/host-claude.json")
    if _path_readable(host_claude_json) and not claude_json.exists():
        try:
            claude_json.write_bytes(host_claude_json.read_bytes())
        except OSError:
            pass
    _ensure_claude_bypass_acceptance(home)
    _ensure_claude_workdir_trusted(home, Path.cwd())
    # Host multi-HOME workaround: Claude Code self-checks for the
    # installed binary under ~/.local/bin/claude. When we give each
    # agent its own HOME, that path no longer exists unless we seed it.
    # Without this shim, the CLI paints "missing or broken" and exits
    # back to the shell even though `claude` is on the real PATH.
    local_bin = home / ".local" / "bin"
    local_claude = local_bin / "claude"
    claude_bin = shutil.which("claude")
    if claude_bin and not local_claude.exists():
        try:
            local_bin.mkdir(parents=True, exist_ok=True)
            local_claude.symlink_to(Path(claude_bin))
        except OSError:
            pass


def pane_env_prefix() -> str:
    """Build a shell env prefix that, prepended to a spawn_cmd, makes the
    spawned process inherit EDUFLOW_STATE_DIR and the Feishu env so
    worker agents calling `eduflow say` write to the project state
    dir, not `~/.eduflow`.
    """
    parts = [f"EDUFLOW_STATE_DIR={shlex.quote(str(paths.state_dir()))}"]
    path_val = env_str("PATH")
    venv_bin = paths.config_file().parent / ".venv" / "bin"
    if venv_bin.exists():
        if path_val:
            path_val = f"{venv_bin}:{path_val}"
        else:
            path_val = str(venv_bin)
    if path_val:
        parts.append(f"PATH={shlex.quote(path_val)}")
    dotenv = _dotenv_values()
    for var in _PROPAGATED_ENV:
        val = env_str(var) or dotenv.get(var, "")
        if val:
            parts.append(f"{var}={shlex.quote(val)}")
    return " ".join(parts)


def pane_spawn_prefix() -> str:
    """Short shell prefix for pane startup.

    tmux `send-keys -l` is fragile with very long one-line env prefixes.
    Prefer a checked-in helper script when present so panes can `source`
    the runtime env first, then run the actual CLI command.
    """
    env_script = paths.config_file().parent / "scripts" / "eduflow-team-env.sh"
    if env_script.exists():
        return f". {shlex.quote(str(env_script))} &&"
    return pane_env_prefix()


def _write_spawn_env_file(agent: str, env_line: str) -> Path | None:
    """Write env vars to a 0600 private file under spawn-env/.

    Returns the path if successful, None on any I/O error. The file is
    sourced by the pane prefix so credentials never enter tmux scrollback.
    """
    spawn_dir = paths.state_dir() / "spawn-env"
    try:
        spawn_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    env_file = spawn_dir / f"{agent}.sh"
    try:
        env_file.write_text(env_line + "\n", encoding="utf-8")
        env_file.chmod(0o600)
    except OSError:
        return None
    return env_file


def pane_spawn_prefix_for_runtime(resolved: dict) -> str:
    """Build the shell prefix for a specific resolved runtime.

    If the runtime points at an `env_profile`, inject those vars inline so the
    selected provider really follows the runtime decision rather than only
    changing labels in config.  Also injects per-agent credentials via
    agent_auth so each pane gets the right API key without leaking into
    tmux scrollback.
    """
    base = pane_spawn_prefix()
    profile_name = resolved.get("env_profile", "")
    profile_vars: dict[str, str] = {}
    if profile_name:
        try:
            profile = config.env_profile_config(profile_name)
            for key in _PROFILE_ENV_KEYS:
                value = profile.get(key)
                if value:
                    profile_vars[key] = str(value)
        except KeyError:
            pass

    # agent_auth per-agent credential priority
    auth_prefix = ""
    try:
        cli = resolved.get("cli", "claude-code")
        adapter = get_adapter(cli)
        from eduflow.runtime import agent_auth
        auth_prefix = agent_auth.spawn_env_prefix(
            resolved.get("agent", ""), adapter
        )
    except (KeyError, ImportError):
        pass

    parts = [f"{k}={shlex.quote(v)}" for k, v in profile_vars.items()]
    if auth_prefix:
        # Avoid overriding env_profile credentials: if the profile already
        # sets ANTHROPIC_AUTH_TOKEN, skip agent_auth's token (it resolves
        # from .env which may carry a different provider's key).
        profile_keys = set(profile_vars.keys())
        if "ANTHROPIC_AUTH_TOKEN" in profile_keys and "ANTHROPIC_AUTH_TOKEN" in auth_prefix:
            # Strip agent_auth's ANTHROPIC_AUTH_TOKEN to let env_profile win
            import re as _re
            auth_prefix = _re.sub(r'ANTHROPIC_AUTH_TOKEN=\S+\s*', '', auth_prefix).strip()
        if auth_prefix:
            parts.append(auth_prefix)
    if not parts:
        return base

    # 0600 private file injection
    agent_name = resolved.get("agent", "")
    if agent_name:
        env_file = _write_spawn_env_file(agent_name, " ".join(parts))
        if env_file and env_file.exists():
            # Use set -a to auto-export all vars sourced from the file
            return f"{base} set -a && . {shlex.quote(str(env_file))} && set +a &&"

    # Fallback: inline (secrets may enter scrollback)
    return f"{base} {' '.join(parts)}"


# Outcome strings returned by provision_pane. Callers print/log differently
# (start uses loop-style "  → spawned", hire uses "✅ hired") so the helper
# stays I/O-free and lets the caller render.
LAZY = "lazy"
READY = "ready"
READY_NO_INIT = "ready_no_init"
SPAWN_FAILED = "spawn_failed"
CONFIG_ERROR = "config_error"
# Extra outcomes returned by restart_with_runtime when prove_ready=True.
# They let watchdog/deliver distinguish "fully recovered" from
# "recovered-but-unverified" so health can show a real verdict.
ENV_DRIFT = "env_drift"
SMOKE_FAILED = "smoke_failed"
READY_UNPROVEN = "ready_unproven"


def _write_runtime_status(agent: str, resolved: dict, *, reason: str = "",
                          env_ok: bool | None = None,
                          smoke_ok: bool | None = None,
                          inbox_verified: bool | None = None,
                          verified_at: float | None = None) -> None:
    """Persist which runtime was selected for this agent.

    This makes runtime switching visible in local state instead of silently
    changing the execution substrate underneath the operator. The optional
    `env_ok`/`smoke_ok`/`inbox_verified`/`verified_at` fields record the
    result of the proved-ready gate so `eduflow runtime verify` can
    distinguish proved_ready from ready_unproven without re-running the
    full probe.
    """
    from eduflow.util import file_lock, read_json, write_json
    import time as _time
    path = paths.runtime_status_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(path):
        data = read_json(path, {"agents": {}})
        data.setdefault("agents", {})
        row = {
            "runtime": resolved.get("selected_runtime", "inline"),
            "cli": resolved.get("cli", "claude-code"),
            "model": resolved.get("model", ""),
            "provider": resolved.get("provider", ""),
            "env_profile": resolved.get("env_profile", ""),
            "reason": reason,
        }
        if env_ok is not None:
            row["env_ok"] = env_ok
        if smoke_ok is not None:
            row["smoke_ok"] = smoke_ok
        if inbox_verified is not None:
            row["inbox_verified"] = inbox_verified
        # verified_at is written ONLY when the caller explicitly passes it —
        # the READY success path in restart_with_runtime. Earlier impl stamped
        # verified_at whenever env_ok or smoke_ok was set, which polluted
        # env_drift / smoke_failed / ready_unproven states with a timestamp
        # that semantically means "proved_ready". Now: no explicit value, no
        # stamp. Callers that mean "full proof" pass verified_at=time.time().
        if verified_at is not None:
            row["verified_at"] = verified_at
        data["agents"][agent] = row
        write_json(path, data)


def current_runtime_status(agent: str) -> dict:
    """Return the persisted runtime status for an agent, or {} if missing."""
    from eduflow.util import read_json
    data = read_json(paths.runtime_status_file(), {"agents": {}})
    return dict(data.get("agents", {}).get(agent, {}))


def restart_with_runtime(agent: str, target: tmux.Target, runtime_name: str,
                         *, reason: str = "", nudge_latest_inbox: bool = True,
                         prove_ready: bool = True) -> str:
    """Hard-switch an already running pane to a specific runtime.

    Used when the pane is alive but the current provider/runtime is degraded
    (rate limit, auth failure, provider unavailable). We send Ctrl-C, then
    spawn the selected replacement runtime into the same pane.

    When `prove_ready=True` (default), after the spawn returns READY the
    function additionally runs:
      1. live-env match against the target env_profile
      2. minimal API smoke against the provider gateway (anthropic-proxy
         only in v1; other CLIs are smoke_skipped → treated as pass)
      3. pane-text absence of failure markers post-spawn
    If any step fails, the outcome is ENV_DRIFT / SMOKE_FAILED /
    READY_UNPROVEN rather than READY. Callers that need to force a
    best-effort switch (e.g. the old watchdog path before the proved-
    ready gate existed) can pass prove_ready=False.
    """
    from eduflow.runtime import verify as _verify
    resolved = config.resolved_agent_config(agent)
    selected = None
    for item in resolved.get("runtime_chain", []):
        if item.get("name") == runtime_name:
            selected = dict(resolved)
            selected.update({
                "selected_runtime": item.get("name", runtime_name),
                "cli": item.get("cli", resolved.get("cli", "claude-code")),
                "model": item.get("model", resolved.get("model", "opus")),
                "provider": item.get("provider", ""),
                "env_profile": item.get("env_profile", ""),
            })
            break
    if selected is None:
        return CONFIG_ERROR
    outcome, _ = _spawn_once(agent, target, selected, respawn=True)
    if outcome not in {READY, READY_NO_INIT}:
        return outcome
    if not prove_ready or outcome != READY:
        # prove_ready only applies to clean READY; READY_NO_INIT means
        # the CLI didn't paint its ready banner, so further smoke would
        # just amplify the failure. Keep original behavior: persist +
        # nudge + return the outcome as-is.
        _write_runtime_status(agent, selected, reason=reason or "runtime_switch")
        if nudge_latest_inbox:
            _nudge_latest_high_priority_inbox(agent, target)
        return outcome

    # proved-ready gate — only escalate to READY if all three checks pass.
    env_profile = str(selected.get("env_profile") or "")
    env_ok, env_mismatches = _verify.verify_live_env_matches_profile(target, env_profile)
    if not env_ok:
        _write_runtime_status(agent, selected,
                              reason=reason or "runtime_switch",
                              env_ok=False)
        return ENV_DRIFT
    smoke_verdict, _smoke_detail = _verify.api_smoke_runtime(selected)
    smoke_ok = smoke_verdict in {"ok", "skipped"}
    if not smoke_ok:
        _write_runtime_status(agent, selected,
                              reason=reason or "runtime_switch",
                              env_ok=True, smoke_ok=False)
        return SMOKE_FAILED
    # Failure-marker scan (with a short wait to let the CLI paint any
    # immediate error).
    try:
        adapter = get_adapter(selected.get("cli", "claude-code"))
    except KeyError:
        adapter = None
    if adapter is not None:
        clean, _found = _verify_no_failure_markers(target, adapter, wait_s=3.0)
        if not clean:
            _write_runtime_status(agent, selected,
                                  reason=reason or "runtime_switch",
                                  env_ok=True, smoke_ok=True)
            return READY_UNPROVEN
    _write_runtime_status(agent, selected,
                          reason=reason or "runtime_switch",
                          env_ok=True, smoke_ok=True,
                          verified_at=time.time())
    if nudge_latest_inbox:
        _nudge_latest_high_priority_inbox(agent, target)
    return READY


def _verify_no_failure_markers(target: tmux.Target, adapter, *, wait_s: float = 3.0,
                                capture_fn=None) -> tuple[bool, list[str]]:
    """Wait briefly then capture pane text; return `(clean, found_markers)`.

    `clean=True` means no known failure marker was seen AFTER the ready
    banner — i.e. the spawn appears healthy. Used as a cheap post-spawn
    smoke: the ready banner itself doesn't tell us the provider is
    reachable, but if 429/auth-error/quota strings immediately reappear
    we know it isn't.
    """
    from eduflow.runtime import failure_detector
    from eduflow.runtime.failure_detector import _CONVERSATION_HISTORY_CORRUPT_MARKERS
    capture_fn = capture_fn or (lambda t, lines: tmux.capture_pane(t, lines=lines))
    if wait_s > 0:
        time.sleep(wait_s)
    text = capture_fn(target, 120)
    ready_markers = list(adapter.ready_markers())
    ready_at = max((text.rfind(m) for m in ready_markers), default=-1)
    current_text = text[ready_at:] if ready_at >= 0 else text
    reason = failure_detector.detect_failure(target, adapter, pane_text=text, lines=120)
    found: list[str] = []
    if reason == "rate_limit":
        found.append("rate_limit")
    elif reason == "conversation_history_corrupt":
        low = current_text.lower()
        for marker in _CONVERSATION_HISTORY_CORRUPT_MARKERS:
            if marker.lower() in low:
                found.append(f"conversation_history_corrupt:{marker}")
                break
    elif reason == "auth_failure":
        found.append("auth_failure")
    elif reason == "provider_unavailable":
        found.append("provider_unavailable")
    return (not found), found


def _nudge_latest_high_priority_inbox(agent: str, target: tmux.Target) -> None:
    """After a runtime recovery, prompt the pane to consume its freshest inbox.

    This avoids the common half-recovered state where the shell/CLI is alive
    again but the agent will not notice the waiting high-priority message until
    a human manually types `eduflow inbox <agent>`.
    """
    try:
        rows = local_facts.list_messages(agent, unread_only=True)
        if not rows:
            return
        latest = rows[-1]
        local_id = str(latest.get("local_id") or "")
        if not local_id:
            return
        runtime_name = (
            current_runtime_status(agent).get("runtime")
            or config.resolved_agent_config(agent).get("selected_runtime", "inline")
        )
        adapter = get_adapter(
            config.resolved_agent_config(agent, runtime_name=runtime_name).get("cli", "claude-code")
        )
        nudge = (
            f"恢复后先处理最新 inbox。`eduflow inbox {agent}` → "
            f"`eduflow read {local_id}` → 必要时 "
            f"`eduflow send manager {agent} \"三行最小状态包\" 高`。"
        )
        tmux.inject(target, nudge, submit_keys=adapter.submit_keys())
    except Exception:
        return


def _wait_for_pid_exit(pid: int, *, timeout_s: float = 3.0) -> None:
    """Block until *pid* exits or *timeout_s* elapses.

    Uses ``os.kill(pid, 0)`` which succeeds (no-op signal) when the process
    exists and raises ``ProcessLookupError`` once it has exited.  Polls every
    100 ms.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return  # pid is gone
        except PermissionError:
            return  # pid exists but we can't signal it — good enough
        time.sleep(0.1)


def _spawn_once(agent: str, target: tmux.Target, resolved: dict, *,
                respawn: bool = False) -> tuple[str, str]:
    """Try to provision the pane with one resolved runtime.

    Returns `(outcome, switch_reason)` where `switch_reason` is the signal that
    may justify moving to the next runtime in the fallback chain.
    """
    resolved.setdefault("agent", agent)
    cli = resolved.get("cli", "claude-code")
    model = resolved.get("model", "opus")
    identity.write(agent, role=resolved.get("role") or agent, cli=cli, model=model)
    if resolved.get("lazy"):
        local_facts.upsert_status(agent, "待命", "lazy: CLI starts on first message")
        _write_runtime_status(agent, resolved)
        return LAZY, ""
    if cli == "codex-cli":
        from eduflow.agents.claude_code import agent_home as _agent_home
        ensure_workdir_trusted(
            Path.cwd(),
            Path(_agent_home(agent)) / ".codex" / "config.toml",
        )
    if cli == "claude-code":
        _ensure_claude_agent_home(agent)
    try:
        adapter = get_adapter(cli)
    except KeyError as e:
        import sys
        print(f"  ⚠️ {agent}: {e}", file=sys.stderr)
        return CONFIG_ERROR, ""
    cmd = f"{pane_spawn_prefix_for_runtime(resolved)} {adapter.spawn_cmd(agent, model)}"
    # Capture old pane PID before respawn so we can wait for it to exit.
    # `respawn-pane -k` is async — the old process may still be tearing down
    # when the new one starts, causing stale output in the pane.
    old_pid = tmux.get_pane_pid(target) if respawn else None
    spawned = tmux.respawn_agent(target, cmd) if respawn else tmux.spawn_agent(target, cmd)
    if not spawned:
        return SPAWN_FAILED, "spawn_failed"
    # Wait for the old process to fully exit before checking for the ready
    # marker, so stale output from the dying process is not misinterpreted.
    if respawn and old_pid is not None:
        _wait_for_pid_exit(old_pid, timeout_s=3.0)
    from eduflow.runtime import tunables
    ready_timeout = float(tunables.tunable("wake.ready_marker_timeout_s", 60.0))
    if wake.wait_until_ready(target, adapter, timeout_s=ready_timeout):
        tmux.inject(target, identity.init_prompt(agent),
                    submit_keys=adapter.submit_keys())
        local_facts.upsert_status(agent, "进行中", "initializing")
        _write_runtime_status(agent, resolved)
        return READY, ""
    if _post_spawn_ready_retry(agent, target, adapter, cli=cli, timeout_s=ready_timeout):
        local_facts.upsert_status(agent, "进行中", "initializing")
        _write_runtime_status(agent, resolved, reason="ready_retry")
        return READY, ""
    local_facts.upsert_status(agent, "进行中", "initializing")
    _write_runtime_status(agent, resolved, reason="ready_timeout")
    return READY_NO_INIT, "ready_timeout"


def _post_spawn_ready_retry(agent: str, target: tmux.Target, adapter, *,
                            cli: str, timeout_s: float) -> bool:
    """Best-effort second chance for startup races.

    Claude panes on macOS occasionally miss the first ready window during
    batch start even though the CLI settles successfully a beat later.
    For that narrow case, wait once more and, if the pane becomes ready,
    inject the identity prompt retroactively.
    """
    if cli != "claude-code":
        return False
    time.sleep(1.5)
    _accept_claude_startup_gate(target)
    if not wake.wait_until_ready(target, adapter, timeout_s=max(8.0, timeout_s / 3)):
        return False
    tmux.inject(target, identity.init_prompt(agent),
                submit_keys=adapter.submit_keys())
    return True


def _accept_claude_startup_gate(target: tmux.Target) -> bool:
    """Advance Claude Code's first-run safety screen when it blocks startup."""
    text = tmux.capture_pane(target, lines=120)
    if "Press Enter to continue" not in text:
        return False
    return tmux.send_keys(target, "Enter")


def provision_pane(agent: str, target: tmux.Target) -> str:
    """Provision a freshly-created pane for `agent`.

    Pre-conditions: tmux window for `target` already exists and is empty
    (a shell prompt). Caller is responsible for window creation.

    Steps:
      1. Render + persist agent's identity.md (`agents/<name>/identity.md`).
      2. If agent is `lazy` in team.json: set status 待命, return LAZY.
      3. For codex CLI: ensure cwd is trusted in ~/.codex/config.toml.
      4. Spawn the adapter's CLI in the pane (with pane_env_prefix).
      5. Wait up to 20s for the adapter's ready marker to appear.
      6. Inject the identity init prompt so the agent reads identity.md
         and reports for duty.
      7. Set status 进行中.

    Returns one of:
      LAZY            — status set to 待命, no CLI spawn attempted
      READY           — CLI spawned + identity init injected
      READY_NO_INIT   — CLI spawned but ready marker didn't appear in 20s
      SPAWN_FAILED    — tmux.spawn_agent returned False
      CONFIG_ERROR    — agent's `cli` value isn't registered (typo /
                        missing adapter); caller should warn + continue
                        with the rest of the team, NOT kill the whole start.
    """
    # Load team config once. start.py loops over N agents calling this
    # helper, so paying 3-4 disk reads here per agent (one for cfg, one
    # for adapter resolution, one for model fallback) compounds. Cache
    # locally and derive cfg / cli / model from the same dict.
    team = config.load_team()
    if agent not in team.get("agents", {}):
        import sys
        print(f"  ⚠️ {agent}: agent {agent!r} not in team.json", file=sys.stderr)
        return CONFIG_ERROR
    resolved = config.resolved_agent_config(agent)
    outcome, switch_reason = _spawn_once(agent, target, resolved)
    if outcome not in {SPAWN_FAILED, READY_NO_INIT}:
        return outcome
    for fallback in resolved.get("runtime_chain", [])[1:]:
        if switch_reason and switch_reason not in fallback.get("switch_on", []):
            continue
        retry_cfg = dict(resolved)
        retry_cfg.update({
            "selected_runtime": fallback.get("name", fallback.get("runtime", "inline")),
            "cli": fallback.get("cli", resolved.get("cli", "claude-code")),
            "model": fallback.get("model", resolved.get("model", "opus")),
            "provider": fallback.get("provider", ""),
            "env_profile": fallback.get("env_profile", ""),
        })
        retry_outcome, retry_reason = _spawn_once(agent, target, retry_cfg)
        if retry_outcome not in {SPAWN_FAILED, READY_NO_INIT}:
            return retry_outcome
        outcome = retry_outcome
        switch_reason = retry_reason or switch_reason
    return outcome
