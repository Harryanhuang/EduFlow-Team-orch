"""Team and runtime configuration.

Two files:
  team.json       — static team layout (which agents, which CLI, which model)
  runtime_config.json — per-deployment runtime values (chat_id, lark profile)

Both paths come from env so tests get isolation by setting EDUFLOW_TEAM_FILE
and EDUFLOW_RUNTIME_CONFIG.

Schema (team.json):
    {
      "session": "EduFlow",
      "agents": {
        "manager":      {"cli": "claude-code", "model": "opus", "role": "..."},
        "worker_cc":    {"cli": "claude-code", "model": "sonnet"},
        "worker_codex": {"cli": "codex-cli",   "model": "gpt-5.5"},
        "worker_kimi":  {"cli": "kimi-code"}
      },
      "default_model": "opus"
    }

Reading is no-cache (re-read on every call) so editing team.json picks up
without restart.  Writes are explicit via save_runtime_config().
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from eduflow.util import env_path, env_str, read_json, write_json


# ── path resolution ───────────────────────────────────────────────


def team_file() -> Path:
    return env_path("EDUFLOW_TEAM_FILE") or Path.cwd() / "team.json"


def runtime_config_file() -> Path:
    return env_path("EDUFLOW_RUNTIME_CONFIG") or Path.cwd() / "runtime_config.json"


# ── team.json ────────────────────────────────────────────────────


_DEFAULT_TEAM: dict = {"session": "EduFlow", "agents": {}, "default_model": "opus"}


def _read_json_lenient(path: Path, default: dict, label: str) -> dict:
    """Like util.read_json but degrades gracefully on parse / I/O errors —
    prints a stderr warning and returns the default dict instead of
    raising. Used at config load points where a malformed or unreadable
    team.json / runtime_config.json shouldn't kill every eduflow
    command; the operator sees the warning + can still run
    `eduflow health` to get a structured corruption report.

    Catches:
      - JSONDecodeError: file present but not valid JSON
      - OSError: PermissionError, file vanished mid-read, encoding
        errors. Ditto for "cannot access this config file"; CLI
        should still answer.
    """
    try:
        return read_json(path, dict(default))
    except json.JSONDecodeError as e:
        print(f"  ⚠️ {label} ({path}) is not valid JSON: {e}", file=sys.stderr)
    except OSError as e:
        print(f"  ⚠️ {label} ({path}) unreadable: {e}", file=sys.stderr)
    return dict(default)


def load_team() -> dict:
    """Return team config in legacy shape `{session, agents, default_model}`.

    Prefers `eduflow.toml` `[team]` section; falls back to legacy
    `team.json` so existing deployments keep working until they migrate
    via `eduflow init --upgrade`.
    """
    from eduflow.runtime import tunables
    toml_team = tunables.load().get("team")
    if isinstance(toml_team, dict) and toml_team:
        return {
            "session": toml_team.get("session", "EduFlow"),
            "agents": dict(toml_team.get("agents", {})),
            "default_model": toml_team.get("default_model", "opus"),
        }
    return _read_json_lenient(team_file(), _DEFAULT_TEAM, "team.json")


def session_name() -> str:
    return load_team().get("session", "EduFlow")


def agent_names() -> list[str]:
    return sorted(load_team().get("agents", {}))


def agent_config(agent: str) -> dict:
    """Return the per-agent dict from team.json. Raises KeyError on miss."""
    agents = load_team().get("agents", {})
    if agent not in agents:
        raise KeyError(f"agent {agent!r} not in team.json")
    cfg = dict(agents[agent])
    if agent == "Hermes" and cfg.get("lazy") is True:
        raise ValueError("Hermes must not be lazy; set team.agents.Hermes.lazy = false")
    return cfg


def load_runtime_registry() -> dict[str, dict]:
    """Return the configured runtime registry from eduflow.toml.

    Shape:
      [runtime_registry.<name>]
      cli = "claude-code"
      model = "opus"
      provider = "anthropic-proxy"
      env_profile = "claude_proxy_primary"
      fallback_to = "other_runtime"
      switch_on = ["spawn_failed", "ready_timeout"]

    Returns an empty dict when the table is missing so older configs keep
    working unchanged.
    """
    from eduflow.runtime import tunables
    data = tunables.load().get("runtime_registry")
    if not isinstance(data, dict):
        return {}
    return {str(name): dict(cfg) for name, cfg in data.items() if isinstance(cfg, dict)}


def load_env_profiles() -> dict[str, dict]:
    """Return named environment profiles from eduflow.toml."""
    from eduflow.runtime import tunables
    data = tunables.load().get("env_profiles")
    if not isinstance(data, dict):
        return {}
    return {str(name): dict(cfg) for name, cfg in data.items() if isinstance(cfg, dict)}


# Sensitive profile keys that must never live in versioned config. When
# a profile leaves one of these empty, we back-fill from the process
# environment (populated by `.env` via `scripts/eduflow-team-env.sh` or
# an outer shell export). This keeps `eduflow.toml` safe to commit
# while still letting the runtime switch path inject real credentials.
_SENSITIVE_PROFILE_KEYS = (
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
)


_ENV_REF_RE = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def _resolve_env_reference(value: Any) -> Any:
    """Expand a value of the form ${VAR} from os.environ.

    If the referenced variable is unset, the original value is returned so
    downstream code can fall back to a global default. Non-string values are
    returned unchanged.
    """
    if not isinstance(value, str):
        return value
    match = _ENV_REF_RE.match(value)
    if not match:
        return value
    env_val = env_str(match.group(1))
    return env_val if env_val is not None else value


def env_profile_config(name: str) -> dict:
    """Return the merged profile for `name`.

    Values written as ${VAR} are resolved from os.environ, allowing each
    provider profile to reference its own secret (e.g. ${KIMI_AUTH_TOKEN})
    while the real credentials stay in the gitignored `.env`.

    Sensitive keys (ANTHROPIC_AUTH_TOKEN etc.) are filled from os.environ
    when the profile leaves them empty after reference expansion — that way
    older configs that omit the key entirely still work via the global env
    variable.
    """
    profiles = load_env_profiles()
    if name not in profiles:
        raise KeyError(f"env profile {name!r} not in env_profiles")
    out = {k: _resolve_env_reference(v) for k, v in profiles[name].items()}
    # Sensitive keys: prefer secrets file over os.environ backfill.
    from eduflow.runtime import agent_auth
    secrets = agent_auth.load_secrets()
    for key in _SENSITIVE_PROFILE_KEYS:
        if not out.get(key):
            secret_val = secrets.get(key) or env_str(key)
            if secret_val:
                out[key] = secret_val
    return out


def runtime_config(name: str) -> dict:
    registry = load_runtime_registry()
    if name not in registry:
        raise KeyError(f"runtime {name!r} not in runtime_registry")
    cfg = dict(registry[name])
    cfg.setdefault("name", name)
    return cfg


def _default_switch_on() -> list[str]:
    return ["spawn_failed", "ready_timeout", "conversation_history_corrupt"]


_HERMES_CLI_NAMES = {"hermes-agent", "hermes-cli"}


def _validate_runtime_chain(chain: list[dict]) -> None:
    """Validate runtime-chain invariants that protect role boundaries."""
    if not chain:
        return
    primary_cli = str(chain[0].get("cli") or "")
    if primary_cli not in _HERMES_CLI_NAMES:
        return
    for item in chain:
        cli = str(item.get("cli") or "")
        if cli not in _HERMES_CLI_NAMES:
            name = item.get("name", "")
            raise ValueError(
                "Hermes runtime chains must keep cli='hermes-agent'; "
                f"runtime {name!r} uses cli={cli!r}"
            )


def resolve_runtime_chain(agent: str) -> list[dict]:
    """Resolve the runtime chain for an agent.

    If the agent declares `runtime = "<name>"`, follow that runtime plus its
    `fallback_to` chain. Otherwise synthesize a single-entry chain from the
    agent's legacy `cli` / `model` config.
    """
    cfg = agent_config(agent)
    team = load_team()
    default_model = (
        env_str("EDUFLOW_DEFAULT_MODEL")
        or team.get("default_model", "opus")
    )
    runtime_name = cfg.get("runtime")
    if not runtime_name:
        chain = [{
            "name": "inline",
            "cli": cfg.get("cli", "claude-code"),
            "model": cfg.get("model") or default_model,
            "provider": cfg.get("provider", ""),
            "env_profile": cfg.get("env_profile", ""),
            "switch_on": list(cfg.get("switch_on", _default_switch_on())),
            "fallback_to": "",
        }]
        _validate_runtime_chain(chain)
        return chain

    chain: list[dict] = []
    seen: set[str] = set()
    current = str(runtime_name)
    while current:
        if current in seen:
            break
        seen.add(current)
        rt = runtime_config(current)
        chain.append({
            "name": current,
            "cli": rt.get("cli", cfg.get("cli", "claude-code")),
            "model": rt.get("model") or cfg.get("model") or default_model,
            "provider": rt.get("provider", ""),
            "env_profile": rt.get("env_profile", ""),
            "switch_on": list(rt.get("switch_on", _default_switch_on())),
            "fallback_to": rt.get("fallback_to", ""),
        })
        next_rt = rt.get("fallback_to", "")
        current = str(next_rt) if next_rt else ""
    _validate_runtime_chain(chain)
    return chain


def resolved_agent_config(
    agent: str,
    *,
    reason: str | None = None,
    runtime_name: str | None = None,
) -> dict[str, Any]:
    """Return the effective runtime config for an agent.

    `reason` is one of the switch signals such as `spawn_failed` or
    `ready_timeout`. The first runtime whose `switch_on` contains that reason
    is selected after the primary entry.

    `runtime_name`, when provided, pins selection to that concrete runtime in
    the agent's resolved chain. This is used by live-pane consumers such as
    watchdog / deliver, which must inspect the adapter for the runtime that is
    actually running now rather than the chain primary.
    """
    cfg = agent_config(agent)
    chain = resolve_runtime_chain(agent)
    selected = chain[0]
    if runtime_name:
        for item in chain:
            if item.get("name") == runtime_name:
                selected = item
                break
    elif reason:
        for idx, item in enumerate(chain):
            if idx == 0:
                continue
            if reason in item.get("switch_on", []):
                selected = item
                break
    resolved = dict(cfg)
    resolved.update({
        "runtime_chain": chain,
        "selected_runtime": selected.get("name", "inline"),
        "cli": selected.get("cli", cfg.get("cli", "claude-code")),
        "model": selected.get("model")
                 or cfg.get("model")
                 or env_str("EDUFLOW_DEFAULT_MODEL")
                 or load_team().get("default_model", "opus"),
        "provider": selected.get("provider", cfg.get("provider", "")),
        "env_profile": selected.get("env_profile", cfg.get("env_profile", "")),
    })
    return resolved


def fallback_runtime(agent: str, *, current_runtime: str, reason: str,
                     avoid_pool_id: str = "",
                     prefer_nonempty_pool: bool = False) -> dict | None:
    """Return the next eligible runtime after `current_runtime` for `reason`.

    Used by runtime switching paths after the pane is already running and the
    system has observed a concrete failure signal in-band.

    `avoid_pool_id`, when non-empty, makes the function prefer candidates
    whose `env_profile.pool_id` differs from it — i.e. a genuinely
    different provider quota pool. When no cross-pool candidate exists,
    the function falls back to the original "first matching switch_on"
    behavior (same-pool included) so callers still get *some* recovery
    path rather than escalation.

    `prefer_nonempty_pool=True` activates Pass 1 in "any known pool is
    better than unknown" mode: candidates with a non-empty pool_id win
    over candidates with no pool_id, regardless of which specific pool.
    Used when the starting runtime has no pool (e.g. primary with no
    env_profile) — a fallback into pool="deepseek" is meaningfully
    cross-pool relative to pool="" because they can't share quota.
    """
    chain = resolve_runtime_chain(agent)
    current_idx = -1
    for idx, item in enumerate(chain):
        if item.get("name", "") == current_runtime:
            current_idx = idx
            break
    if current_idx < 0:
        return None

    def _pool_of(item: dict) -> str:
        env_profile_name = str(item.get("env_profile") or "")
        if not env_profile_name:
            return ""
        try:
            profile = env_profile_config(env_profile_name)
        except KeyError:
            return ""
        return str(profile.get("pool_id") or "")

    def _pass1_match(item: dict) -> bool:
        """Return True iff `item` satisfies the cross-pool preference."""
        pool = _pool_of(item)
        if avoid_pool_id:
            return bool(pool and pool != avoid_pool_id)
        if prefer_nonempty_pool:
            return bool(pool)
        return False

    # Pass 1: forward scan, cross-pool priority.
    if avoid_pool_id or prefer_nonempty_pool:
        for item in chain[current_idx + 1:]:
            if reason not in item.get("switch_on", []):
                continue
            if _pass1_match(item):
                return dict(item)

    # Pass 2: forward scan, no pool avoidance.
    for item in chain[current_idx + 1:]:
        if reason in item.get("switch_on", []):
            return dict(item)

    # Allow backup runtimes to form a ring, e.g.
    # primary -> deepseek -> qwen_plus -> deepseek. A failure in qwen_plus
    # should return to deepseek, but the primary runtime and unrelated earlier
    # backups are intentionally not part of this wraparound path.
    wrap_to = str(chain[current_idx].get("fallback_to") or "")
    if current_idx > 1 and wrap_to:
        # Ring wrap: cross-pool priority applies here too.
        if avoid_pool_id or prefer_nonempty_pool:
            for item in chain[1:current_idx]:
                if item.get("name") == wrap_to and reason in item.get("switch_on", []):
                    if _pass1_match(item):
                        return dict(item)
        for item in chain[1:current_idx]:
            if item.get("name") == wrap_to and reason in item.get("switch_on", []):
                return dict(item)
    return None


def agent_cli(agent: str) -> str:
    """Return the CLI identifier for an agent (defaults to 'claude-code')."""
    return resolved_agent_config(agent).get("cli", "claude-code")


def agent_model(agent: str) -> str:
    """Resolve model: agent-specific → EDUFLOW_DEFAULT_MODEL → team default → 'opus'."""
    return resolved_agent_config(agent).get("model", "opus")


# ── runtime_config.json ──────────────────────────────────────────


def load_runtime_config() -> dict:
    return _read_json_lenient(runtime_config_file(), {}, "runtime_config.json")


def save_runtime_config(cfg: dict) -> None:
    write_json(runtime_config_file(), cfg)


def chat_id() -> str:
    """Prefer eduflow.toml `chat_id` (top-level), fall back to legacy
    runtime_config.json."""
    from eduflow.runtime import tunables
    toml_val = tunables.load().get("chat_id")
    if toml_val:
        return str(toml_val)
    return load_runtime_config().get("chat_id", "")


def lark_profile() -> str:
    """Resolve the lark-cli profile name. Priority: env > toml > legacy json."""
    if env := env_str("LARK_CLI_PROFILE"):
        return env
    from eduflow.runtime import tunables
    toml_val = tunables.load().get("lark_profile")
    if toml_val is not None:
        return str(toml_val)
    return load_runtime_config().get("lark_profile", "")


def supervisor_chat_id() -> str:
    """Optional dedicated chat for supervisor / watchdog alerts.

    Priority:
      1. `EDUFLOW_SUPERVISOR_CHAT_ID`
      2. `eduflow.toml` `[feishu.supervisor].chat_id`
      3. main `chat_id()`
    """
    if env := env_str("EDUFLOW_SUPERVISOR_CHAT_ID"):
        return env
    from eduflow.runtime import tunables
    feishu_cfg = tunables.load().get("feishu")
    if isinstance(feishu_cfg, dict):
        supervisor_cfg = feishu_cfg.get("supervisor")
        if isinstance(supervisor_cfg, dict):
            chat = supervisor_cfg.get("chat_id")
            if chat:
                return str(chat)
    return chat_id()


def supervisor_lark_profile() -> str:
    """Optional dedicated lark-cli profile for supervisor alerts.

    Priority:
      1. `LARK_CLI_SUPERVISOR_PROFILE`
      2. `eduflow.toml` `[feishu.supervisor].lark_profile`
      3. main `lark_profile()`
    """
    if env := env_str("LARK_CLI_SUPERVISOR_PROFILE"):
        return env
    from eduflow.runtime import tunables
    feishu_cfg = tunables.load().get("feishu")
    if isinstance(feishu_cfg, dict):
        supervisor_cfg = feishu_cfg.get("supervisor")
        if isinstance(supervisor_cfg, dict):
            profile = supervisor_cfg.get("lark_profile")
            if profile is not None and str(profile) != "":
                return str(profile)
    return lark_profile()


def supervisor_sender_config() -> dict[str, str]:
    """Optional display-only identity for supervisor channel messages.

    Supported keys under `[feishu.supervisor]`:
      - sender_name
      - sender_role
      - sender_emoji
      - sender_color
    """
    from eduflow.runtime import tunables
    feishu_cfg = tunables.load().get("feishu")
    if not isinstance(feishu_cfg, dict):
        return {}
    supervisor_cfg = feishu_cfg.get("supervisor")
    if not isinstance(supervisor_cfg, dict):
        return {}
    out: dict[str, str] = {}
    for key in ("sender_name", "sender_role", "sender_emoji", "sender_color"):
        value = supervisor_cfg.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            out[key] = text
    return out


# ── residency policy ─────────────────────────────────────────
#
# Per plan 2026-07-01 §设计二:
#   [team.residency]
#   default_mode = "warm"
#   resident_agents = ["manager", "auto_ops", "Luke_recorder"]
#   warm_idle_timeout_s = 600
#   handoff_buffer_s = 300
#   wake_timeout_s = 60
#
#   [team.agents.<name>.residency]
#   mode = "warm"        # resident | warm | cold
#   idle_timeout_s = 300
#   handoff_buffer_s = 300
#
# Phase 2 implements the config side only; Phase 3 wires the runtime
# sleep / wake machinery on top of this.


def _load_residency_default() -> "ResidencyPolicy":
    """Read the [team.residency] block from eduflow.toml and return
    a `ResidencyPolicy` populated from its keys (with sensible
    fallbacks when the block is missing or partial)."""
    from eduflow.runtime import residency as _res
    from eduflow.runtime import tunables
    team_cfg = tunables.load().get("team")
    if not isinstance(team_cfg, dict):
        team_cfg = {}
    block = team_cfg.get("residency")
    if not isinstance(block, dict):
        block = {}
    return _res.ResidencyPolicy(
        mode=_res._coerce_mode(block.get("default_mode"), _res.DEFAULT_MODE),
        idle_timeout_s=_res._coerce_int(
            block.get("warm_idle_timeout_s"), _res.DEFAULT_IDLE_TIMEOUT_S,
        ),
        handoff_buffer_s=_res._coerce_int(
            block.get("handoff_buffer_s"), _res.DEFAULT_HANDOFF_BUFFER_S,
        ),
        wake_timeout_s=_res._coerce_int(
            block.get("wake_timeout_s"), _res.DEFAULT_WAKE_TIMEOUT_S,
            min_value=1,
        ),
        source="default",
    )


def _load_agent_residency_override(agent: str) -> dict | None:
    """Read [team.agents.<name>.residency] from eduflow.toml, or
    None when no per-agent block exists.  Returning the raw dict
    (not a `ResidencyPolicy`) lets `merge_with_default` apply the
    field-by-field merge semantics so missing keys fall through
    cleanly."""
    from eduflow.runtime import tunables
    team_cfg = tunables.load().get("team")
    if not isinstance(team_cfg, dict):
        return None
    agents = team_cfg.get("agents")
    if not isinstance(agents, dict):
        return None
    agent_block = agents.get(agent)
    if not isinstance(agent_block, dict):
        return None
    override = agent_block.get("residency")
    if not isinstance(override, dict) or not override:
        return None
    return dict(override)


def _resolve_resident_agents() -> tuple[str, ...]:
    """Return the configured list of always-on agents.

    Reads `[team.residency].resident_agents` if present; otherwise
    falls back to `residency.DEFAULT_RESIDENT_AGENTS`.  Unknown
    agent names (not in team) are filtered out so a stale
    `resident_agents = ["manager", "ghost"]` doesn't cause a later
    `KeyError` on a runtime path that asks for `cfg.cli`.
    """
    from eduflow.runtime import residency as _res
    from eduflow.runtime import tunables
    team_cfg = tunables.load().get("team")
    block = team_cfg.get("residency") if isinstance(team_cfg, dict) else None
    if not isinstance(block, dict):
        return _res.DEFAULT_RESIDENT_AGENTS
    raw = block.get("resident_agents")
    if raw is None:
        return _res.DEFAULT_RESIDENT_AGENTS
    fallback = _res.DEFAULT_RESIDENT_AGENTS
    return _res._coerce_resident_list(raw, fallback)


def load_residency_policy(agent: str) -> "ResidencyPolicy":
    """Return the effective `ResidencyPolicy` for `agent`.

    Mode-resolution order (highest priority last):
      1. team-wide `default_mode` (warm)
      2. `resident_agents` list membership → resident
      3. `[team.agents.<name>.residency].mode` per-agent override
         (wins over the list — lets a boss mark an agent `cold`
         even if it was previously in `resident_agents`)

    Timeout fields follow the same precedence: per-agent override
    wins field-by-field, with team defaults for missing keys.

    `agent` does NOT need to be a known team member — an unknown
    agent still gets a sensible warm default rather than a
    KeyError, because the lazy-wake path calls this for agents
    that may not have been configured when `eduflow up` was last
    run.
    """
    from eduflow.runtime import residency as _res
    default = _load_residency_default()
    override = _load_agent_residency_override(agent) or {}

    # 1) start with list-membership-or-default mode
    resident_set = set(load_resident_agents())
    if agent in resident_set:
        base_mode = ResidencyMode.RESIDENT if "ResidencyMode" in dir() else "resident"  # noqa
        # Avoid forward-ref import cycle: do it the clean way.
        base_mode = _res.ResidencyMode.RESIDENT
    else:
        base_mode = default.mode

    # 2) apply per-agent override (mode + timeouts)
    if "mode" in override:
        base_mode = _res._coerce_mode(override.get("mode"), base_mode)
    merged_default = _res.ResidencyPolicy(
        mode=base_mode,
        idle_timeout_s=default.idle_timeout_s,
        handoff_buffer_s=default.handoff_buffer_s,
        wake_timeout_s=default.wake_timeout_s,
        source=default.source,
    )
    return _res.merge_with_default(
        default_policy=merged_default, override=override,
    )


def load_resident_agents() -> tuple[str, ...]:
    """Return the always-on agent list, with unknown names dropped
    against the current `team.agents` set."""
    resident_list = _resolve_resident_agents()
    known = set(agent_names())
    return tuple(name for name in resident_list if name in known)
