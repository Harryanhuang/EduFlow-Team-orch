"""`eduflow runtime switch <agent> <runtime>` — manual hard-switch.

Operator-facing form of the same path the watchdog daemon uses
automatically. Runs the proved-ready gate by default so the operator
sees exactly what the auto-guard sees: live env match, API smoke,
pane-text absence of failure markers.

Exit codes:
  0 — runtime switched, outcome is READY (fully proved)
  1 — usage error / unknown agent / unknown runtime / panic
  2 — switch attempted but gate failed (env_drift / smoke_failed /
      ready_unproven); operator can retry with --no-smoke for an
      emergency override
"""
from __future__ import annotations

import sys
import uuid

from eduflow.runtime import config, human_takeover, lifecycle, paths, tmux, tunables, verify
from eduflow.util import (
    error_exit, maybe_print_help, pop_bool_flag, pop_flag, print_json,
    reject_extra_args, write_json,
)


USAGE = (
    "usage: eduflow runtime switch <agent> <runtime>\n"
    "              [--reason <r>] [--actor <operator-id>] [--no-smoke] [--json]"
)


def _authorized_actors() -> set[str]:
    team = tunables.load().get("team", {})
    if not isinstance(team, dict):
        return set()
    def identities(key: str) -> list[str]:
        value = team.get(key, [])
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return [item for item in value if item]
        return []  # malformed authorization configuration fails closed

    values = [*identities("admins"), *identities("runtime_operators"),
              *identities("runtime_operator")]
    return set(values)


def _manual_trigger(takeover_state: dict, actor: str | None) -> str:
    if takeover_state.get("state") == "inactive":
        return "manual_cli"
    if not actor or actor not in _authorized_actors():
        raise PermissionError(
            "human takeover active: configured operator/admin --actor required"
        )
    # record_switch_event currently persists trigger but intentionally ignores
    # unknown extension fields, so bind the authorized identity into the
    # persisted trigger rather than pretending an ``actor`` kwarg is stored.
    return f"manual_cli_takeover_override:{actor}"


def _emit(outcome: str, agent: str, to_runtime: str, reason: str,
          as_json: bool, detail: dict) -> int:
    if as_json:
        print_json({
            "agent": agent,
            "to_runtime": to_runtime,
            "reason": reason,
            "outcome": outcome,
            **detail,
        })
        return 0 if outcome == lifecycle.READY else 2
    if outcome == lifecycle.READY:
        print(f"✅ {agent} switched to {to_runtime} ({reason}); proved_ready")
        return 0
    if outcome == lifecycle.READY_NO_INIT:
        print(f"⚠️  {agent} switched to {to_runtime} ({reason}); ready_no_init")
        return 2
    print(f"❌ {agent} switch to {to_runtime} ({reason}) failed: {outcome}")
    return 2


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    no_smoke = pop_bool_flag(rest, "--no-smoke")
    reason = pop_flag(rest, "--reason") or "manual_cli"
    actor = pop_flag(rest, "--actor")
    if len(rest) < 2:
        print(USAGE)
        return 1
    agent, to_runtime = rest[0], rest[1]
    extra = rest[2:]
    if extra:
        print(f"❌ unexpected args: {extra}\n{USAGE}")
        return 1

    # Resolve team + validate agent + runtime exist.
    try:
        team = config.load_team()
    except Exception as e:
        return error_exit(f"❌ team config load failed: {e}")
    if agent not in team.get("agents", {}):
        return error_exit(f"❌ unknown agent: {agent!r}")
    try:
        config.runtime_config(to_runtime)
    except KeyError:
        return error_exit(f"❌ unknown runtime: {to_runtime!r}")
    session = team.get("session", "EduFlow")
    target = tmux.Target(session, agent)
    if not tmux.has_session(session) or not tmux.has_window(target):
        return error_exit(f"❌ agent pane not running: {session}:{agent}")

    # Serialize authorization, audit intent, and the restart with takeover
    # entry.  `enter()` uses the same blocking lock, so either takeover wins
    # first and this switch is rejected, or it is durably entered immediately
    # after this in-flight switch completes; it is never lost in a TOCTOU gap.
    with human_takeover.transition_lock():
        current = lifecycle.current_runtime_status(agent).get("runtime") or "inline"
        takeover_state = human_takeover.status()
        try:
            trigger = _manual_trigger(takeover_state, actor)
        except PermissionError as exc:
            return error_exit(str(exc))
        switch_id = str(uuid.uuid4())
        common_event = {
            "agent": agent, "from_runtime": current, "to_runtime": to_runtime,
            "reason": reason, "trigger": trigger, "switch_id": switch_id,
        }
        verify.record_switch_event(**common_event, outcome="pending", phase="prepared")
        outcome = lifecycle.restart_with_runtime(
            agent, target, to_runtime,
            reason=f"manual_cli:{reason}",
            prove_ready=not no_smoke,
        )
        # Post-switch live probe so the operator sees the actual verdict,
        # not just the lifecycle outcome.
        from eduflow.commands import runtime_verify
        probe = runtime_verify.compute_verdict(agent) if outcome in {
            lifecycle.READY, lifecycle.READY_NO_INIT,
            lifecycle.ENV_DRIFT, lifecycle.SMOKE_FAILED,
            lifecycle.READY_UNPROVEN,
        } else {"verdict": outcome}
        # Completion is a second append-only event with the same correlation
        # id.  Never rewrite a possibly interleaved process's last JSONL row.
        verify.record_switch_event(
            **common_event, outcome=outcome,
            verdict=probe.get("verdict", outcome), phase="completed",
        )
    return _emit(outcome, agent, to_runtime, reason, as_json,
                 {"verdict": probe.get("verdict", outcome),
                  "from_runtime": current})
