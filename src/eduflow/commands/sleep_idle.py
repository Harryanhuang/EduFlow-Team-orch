"""`eduflow residency-sleep [--agent <name>] [--apply]`

Per-agent CLI-retire helper used by the Phase 3 idle sweep.

By default (`--dry-run`, the default flag) the command prints which
agents WOULD be retired and why, without actually sending Ctrl-C to
any pane.  Pass `--apply` to make it real.  This two-step rollout
keeps the boss's trust intact — a typo in the idle threshold
shouldn't take down the worker on the first cycle.

The "sleep" action itself is intentionally lightweight:
  1. Send C-c to the pane (Claude / Codex / Kimi / Qwen all exit on
     Ctrl-C and drop back to the shell prompt)
  2. Do NOT kill the tmux window — the pane stays
  3. Stamp `温备` in local_facts so `/team` shows the new state
  4. Stamp `last_sleep_at` in `agent_residency.json`

A subsequent `eduflow send <agent> <msg>` (Phase 4 wake path) re-
spawns the CLI via the existing `wake_if_dormant` machinery; the
window target is unchanged.

The function form `sleep_if_idle(agent, *, dry_run, ...)` is the
side-effect-carrying entry point the auto_ops loop calls.  The CLI
shells out to it.
"""
from __future__ import annotations

import json
import sys
from typing import Callable

from eduflow.runtime import config, residency, tmux
from eduflow.store import agent_residency, local_facts
from eduflow.util import error_exit, pop_bool_flag, pop_flag, usage_error


USAGE = (
    "usage: eduflow residency-sleep [--agent <name>] [--apply] "
    "[--json]"
)


# Reasons a sweep iteration can return. Mirrors `residency.sleep_decision`
# but as a structured result so the CLI can render it without re-deriving.
_SLEEP_REASONS = {
    "ok": "sleep_ok",
    "keep_resident": "keep_resident",
    "keep_cold": "keep_cold",
    "keep_active_task": "keep_active_task",
    "keep_unread_inbox": "keep_unread_inbox",
    "keep_cooldown": "keep_cooldown",
    "keep_handoff_buffer": "keep_handoff_buffer",
    "keep_under_idle_timeout": "keep_under_idle_timeout",
}


_ACTIVE_STATUS_BLOCKLIST = {
    "进行中",
    "已接单",
    "待接单",
    "已读待确认",
}


def _has_active_task(agent: str) -> bool:
    """True iff `agent` has an open task or pending acceptance.

    Conservative for warm standby: a stale `已接单` row is safer to
    keep running than to retire, because it usually means the task
    truth has not been closed out yet.  A `待命` / `空闲` / `已交付`
    agent is NOT considered active.
    """
    snap = local_facts.get_status(agent) or {}
    return str(snap.get("status") or "") in _ACTIVE_STATUS_BLOCKLIST


def _has_unread_inbox(agent: str) -> bool:
    rows = local_facts.list_messages(agent, unread_only=True)
    return bool(rows)


def _in_cooldown(agent: str) -> bool:
    """True iff runtime guard has escalated this agent or it is
    currently inside a runtime fallback chain.

    The data lives in `runtime-guard-state.json` (same file
    `local_facts.runtime_guard_block_evidence` reads) so the
    semantics are consistent with the "运行时受阻" projection
    in `/team`."""
    try:
        from eduflow.runtime.paths import facts_dir
    except Exception:
        return False
    from eduflow.util import read_json
    data = read_json(facts_dir() / "runtime-guard-state.json", {"agents": {}})
    row = data.get("agents", {}).get(agent) or {}
    return bool(row.get("escalation_needed") or row.get("needs_manager_action"))


def _collect_signals(agent: str, *, now: float | None = None) -> residency.SleepSignals:
    return residency.SleepSignals(
        has_active_task=_has_active_task(agent),
        has_unread_inbox=_has_unread_inbox(agent),
        in_cooldown=_in_cooldown(agent),
        idle_age_s=agent_residency.age_since_active(agent, now=now),
        since_handoff_s=agent_residency.age_since_handoff(agent, now=now),
    )


def sleep_if_idle(
    agent: str,
    *,
    dry_run: bool = True,
    now: float | None = None,
    send_keys: Callable | None = None,
    upsert_status: Callable | None = None,
) -> dict:
    """Decide + (optionally) retire `agent`'s CLI.

    Returns a structured result:
        {
          "agent": str,
          "decision": "sleep_ok" | <keep_* reason>,
          "applied": bool,
          "policy_mode": str,
          "policy_source": str,
          "idle_age_s": float,
          "since_handoff_s": float,
        }

    `dry_run=True` (default) never touches the pane; it just returns
    what the decision would be.  `dry_run=False` sends Ctrl-C to
    the agent's pane and stamps `温备` in local_facts.

    The `send_keys` / `upsert_status` overrides exist so tests can
    substitute the real `tmux.send_keys` / `local_facts.upsert_status`
    with a recorder.  Default behaviour hits the real I/O.
    """
    policy = config.load_residency_policy(agent)
    signals = _collect_signals(agent, now=now)
    decision = residency.sleep_decision(policy, signals)

    result = {
        "agent": agent,
        "decision": decision,
        "applied": False,
        "policy_mode": policy.mode,
        "policy_source": policy.source,
        "idle_age_s": signals.idle_age_s,
        "since_handoff_s": signals.since_handoff_s,
    }
    if decision != residency.SLEEP_OK:
        return result

    if dry_run:
        result["decision"] = "would_sleep"
        return result

    # Real sleep: graceful-exit the CLI but keep the pane.  We do
    # NOT kill the tmux window — Phase 4 wake reuses the same
    # window target via the existing `wake_if_dormant` path.
    _send = send_keys or tmux.send_keys
    target = tmux.Target(config.session_name(), agent)
    if tmux.has_window(target):
        try:
            _send(target, "C-c")
        except Exception:
            # The pane might already be at a shell; the signal is
            # best-effort.  We still stamp 温备 below so `/team`
            # reflects the intended state.
            pass

    _upsert = upsert_status or local_facts.upsert_status
    _upsert(agent, "温备", "sleep: idle > policy.idle_timeout_s")
    agent_residency.touch_sleep(agent, when=now)

    result["applied"] = True
    return result


def sweep(
    *,
    dry_run: bool = True,
    agents: list[str] | None = None,
    now: float | None = None,
    send_keys: Callable | None = None,
    upsert_status: Callable | None = None,
) -> list[dict]:
    """Run `sleep_if_idle` for every warm agent (or every agent in
    `agents` if given).  Resident + cold agents are skipped by the
    decision matrix; unknown agents get the warm default. Returns
    one result dict per agent in input order.

    Plan §设计二 calls this "auto_ops / runtime_guard 周期检查".
    Today the auto_ops daemon is the natural caller; this function
    is daemon-agnostic so tests can drive it directly.
    """
    team_agents = agents if agents is not None else config.agent_names()
    return [
        sleep_if_idle(
            agent,
            dry_run=dry_run,
            now=now,
            send_keys=send_keys,
            upsert_status=upsert_status,
        )
        for agent in team_agents
    ]


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    rest = list(argv)
    as_json = pop_bool_flag(rest, "--json")
    only = pop_flag(rest, "--agent")
    apply = pop_bool_flag(rest, "--apply")
    if rest:
        return usage_error(USAGE)
    dry_run = not apply

    if only:
        agents = [only]
    else:
        agents = config.agent_names()
    if not agents:
        return error_exit("❌ no team configured (load_residency_policy needs team.json)")

    results = sweep(
        dry_run=dry_run,
        agents=agents,
    )
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            applied = "[applied]" if r["applied"] else "[dry-run]"
            print(
                f"{applied} {r['agent']:<20} "
                f"mode={r['policy_mode']:<8} "
                f"decision={r['decision']:<24} "
                f"idle={r['idle_age_s']:.0f}s "
                f"since_handoff={r['since_handoff_s']:.0f}s"
            )
    return 0
