"""`eduflow residency-wake <agent> [--json]`

Phase 5 (2026-07-01) — manual pre-heat for warm agents.

Plan §设计三 / 分阶段计划 Phase 4 executor note:
    可选: 对常用 warm agent 支持 manager 预热

When the boss / manager knows a burst of work is coming for a warm
agent that is currently 温备 (CLI exited, pane kept), they can
pre-heat it so the first real dispatch doesn't pay the spawn
latency.  This command reuses the exact same `wake.wake_if_dormant`
path that `commands/send.py` uses lazily, so a pre-heated agent and
a lazily-woken agent converge on identical state.

Unlike `send`, this does NOT deliver a message — it only ensures
the CLI is up + stamps `last_wake_at`.  If wake fails, it fires the
same wake-failure ALERT as the lazy path (Phase 4).
"""
from __future__ import annotations

import json

from eduflow.agents import get_adapter, identity as _identity
from eduflow.runtime import config, lifecycle, tmux, wake, tunables
from eduflow.store import agent_residency, local_facts
from eduflow.util import error_exit, pop_bool_flag, usage_error


USAGE = "usage: eduflow residency-wake <agent> [--json]"


def wake_agent(agent: str) -> dict:
    """Ensure `agent`'s CLI is up. Returns a structured result:

        {
          "agent": str,
          "woke": bool,           # True if ready marker seen
          "already_ready": bool,  # True if it was already up
          "no_pane": bool,        # True if no tmux window exists
          "errno": str,           # "" on success
        }

    Side effects on success: `agent_residency.touch_wake(agent)` +
    status 进行中.  On wake failure: fires the wake-failure ALERT.
    """
    result = {
        "agent": agent,
        "woke": False,
        "already_ready": False,
        "no_pane": False,
        "errno": "",
    }
    if agent not in config.agent_names():
        result["errno"] = "unknown_agent"
        return result

    session = config.session_name()
    window_target = tmux.Target(session, agent)
    if not tmux.has_window(window_target):
        result["no_pane"] = True
        result["errno"] = "no_pane"
        # No pane at all — fire the same ALERT the lazy path would.
        _fire_alert(agent, "no_pane")
        return result

    target = tmux.preferred_pane_target(window_target)
    resolved = config.resolved_agent_config(agent)
    cli = resolved.get("cli", "claude-code")
    adapter = get_adapter(cli)

    if wake.is_ready(target, adapter):
        result["already_ready"] = True
        result["woke"] = True
        # Even an already-ready agent gets its clock reset — pre-heat
        # is an explicit "I'm about to use you" signal.
        try:
            agent_residency.touch_wake(agent)
        except Exception:
            pass
        return result

    model = resolved.get("model", config.agent_model(agent))
    resolved["agent"] = agent
    try:
        spawn_prefix = lifecycle.pane_spawn_prefix_for_runtime(resolved)
    except PermissionError:
        result["errno"] = "credential_file_permissions"
        _fire_alert(agent, "spawn_failed")
        return result
    spawn_cmd = f"{spawn_prefix} {adapter.spawn_cmd(agent, model)}"
    wake_timeout = float(tunables.tunable("wake.lazy_wake_timeout_s", 30.0))
    def _on_woken() -> None:
        local_facts.upsert_status(agent, "进行中", "pre-heated by manager")
        _touch_wake_safely(agent)

    woke = wake.wake_if_dormant(
        target, adapter,
        spawn_cmd=spawn_cmd,
        init_msg=_identity.init_prompt(agent),
        timeout_s=wake_timeout,
        on_woken=_on_woken,
    )
    result["woke"] = bool(woke)
    if not woke:
        result["errno"] = "wake_failed"
        _fire_alert(agent, "ready_marker_timeout", wake_timeout)
    return result


def _touch_wake_safely(agent: str) -> None:
    try:
        agent_residency.touch_wake(agent)
    except Exception:
        pass


def _fire_alert(agent: str, kind: str, wake_timeout_s: float = 30.0) -> None:
    try:
        from eduflow.commands import wake_alert
        wake_alert.fire_wake_failure_alert(
            target_agent=agent,
            failure_kind=kind,
            wake_timeout_s=wake_timeout_s,
        )
    except Exception:
        pass


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    rest = list(argv)
    as_json = pop_bool_flag(rest, "--json")
    if len(rest) != 1:
        return usage_error(USAGE)
    agent = rest[0]

    result = wake_agent(agent)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result["errno"] else 1

    if result["errno"] == "unknown_agent":
        return error_exit(f"❌ unknown agent: {agent} (not in team.json)")
    if result["already_ready"]:
        print(f"✅ {agent} already ready (clock reset)")
        return 0
    if result["woke"]:
        print(f"✅ {agent} pre-heated (CLI woken)")
        return 0
    if result["no_pane"]:
        return error_exit(
            f"❌ {agent} has no pane; run `eduflow hire {agent}` or "
            f"`eduflow up` first (ALERT fired)")
    return error_exit(f"❌ {agent} wake failed within timeout (ALERT fired)")
