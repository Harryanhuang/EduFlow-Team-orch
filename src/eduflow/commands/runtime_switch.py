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

import uuid

from eduflow.commands.human_takeover import runtime_authorized_actor_ids
from eduflow.runtime import config, human_takeover, lifecycle, tmux, tunables, verify
from eduflow.util import (
    error_exit, maybe_print_help, pop_bool_flag, pop_flag, print_json,
)


USAGE = (
    "usage: eduflow runtime switch <agent> <runtime>\n"
    "              [--reason <r>] [--actor <operator-id>] [--no-smoke] [--json]"
)


def _authorized_actors() -> set[str]:
    configured = tunables.load()
    team = configured.get("team", {}) if isinstance(configured, dict) else {}
    return runtime_authorized_actor_ids(team)


def _manual_trigger(takeover_state: dict, actor: str | None) -> str:
    if not actor or actor not in _authorized_actors():
        raise PermissionError(
            "configured admin/runtime_operator --actor required"
        )
    if takeover_state.get("state") == "inactive":
        return "manual_cli"
    # Keep trigger as the action category; record_switch_event persists the
    # authorized identity separately in its structured ``actor`` field.
    return "manual_cli_takeover_override"


def _emit(outcome: str, agent: str, to_runtime: str, reason: str,
          as_json: bool, detail: dict) -> int:
    verdict = str(detail.get("verdict") or outcome)
    proved_ready = outcome == lifecycle.READY and verdict == "proved_ready"
    if as_json:
        print_json({
            "agent": agent,
            "to_runtime": to_runtime,
            "reason": reason,
            "outcome": outcome,
            **detail,
        })
        return 0 if proved_ready else 2
    if proved_ready:
        print(f"✅ {agent} switched to {to_runtime} ({reason}); proved_ready")
        return 0
    if outcome == lifecycle.READY:
        print(f"⚠️  {agent} switched to {to_runtime} ({reason}); verdict={verdict}")
        return 2
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
    terminal_audit_error: OSError | None = None
    failure_result: dict | None = None
    with human_takeover.transition_lock():
        current = lifecycle.current_runtime_status(agent).get("runtime") or "inline"
        takeover_state = human_takeover.status()
        try:
            trigger = _manual_trigger(takeover_state, actor)
        except PermissionError as exc:
            return error_exit(str(exc))
        switch_id = str(uuid.uuid4())
        try:
            verify.record_switch_event(
                agent=agent, from_runtime=str(current), to_runtime=to_runtime,
                reason=reason, trigger=trigger, switch_id=switch_id,
                actor=actor or "", target=str(target),
                outcome="pending", phase="prepared", strict=True,
                result={"status": "pending"},
            )
        except OSError as exc:
            return error_exit(
                f"runtime switch audit failed before restart ({type(exc).__name__}); "
                "restart was not attempted; fix audit storage and retry"
            )
        outcome = "exception"
        probe = {"verdict": "unknown"}
        try:
            outcome = lifecycle.restart_with_runtime(
                agent, target, to_runtime,
                reason=f"manual_cli:{reason}",
                prove_ready=not no_smoke,
            )
        except Exception as exc:
            failure_result = {
                "status": "failed", "stage": "restart",
                "exception_class": type(exc).__name__,
                "detail": f"runtime restart raised {type(exc).__name__}",
                # A raised lifecycle call cannot prove whether tmux/provider
                # mutation occurred before the exception.
                "side_effect": "unknown",
            }
        if failure_result is None:
            # Post-switch live probe so the operator sees the actual verdict,
            # not just the lifecycle outcome.
            from eduflow.commands import runtime_verify
            try:
                probe = runtime_verify.compute_verdict(agent) if outcome in {
                    lifecycle.READY, lifecycle.READY_NO_INIT,
                    lifecycle.ENV_DRIFT, lifecycle.SMOKE_FAILED,
                    lifecycle.READY_UNPROVEN,
                } else {"verdict": outcome}
            except Exception as exc:
                failure_result = {
                    "status": "failed", "stage": "probe",
                    "exception_class": type(exc).__name__,
                    "detail": f"runtime verification raised {type(exc).__name__}",
                    "side_effect": "restart_completed",
                    "restart_outcome": outcome,
                }
        terminal_result = failure_result or {
            "status": "completed", "outcome": outcome,
            "verdict": probe.get("verdict", outcome),
        }
        # Completion is a second append-only event with the same correlation
        # id.  Never rewrite a possibly interleaved process's last JSONL row.
        try:
            verify.record_switch_event(
                agent=agent, from_runtime=str(current), to_runtime=to_runtime,
                reason=reason, trigger=trigger, switch_id=switch_id,
                actor=actor or "", target=str(target), outcome=outcome,
                verdict=probe.get("verdict", outcome), phase="completed",
                strict=True, result=terminal_result,
            )
        except OSError as exc:
            terminal_audit_error = exc
    if failure_result is not None or terminal_audit_error is not None:
        stage = failure_result.get("stage", "completion_audit") if failure_result else "completion_audit"
        attention_reason = (
            f"runtime_switch_attention stage={stage} switch_id={switch_id} "
            f"agent={agent} outcome={outcome} "
            f"terminal_audit={'failed' if terminal_audit_error else 'recorded'}"
        )
        try:
            attention = human_takeover.enter(
                reason=attention_reason, source="manual_runtime_switch_audit",
                actor=actor or "system",
            )
        except (OSError, TimeoutError) as takeover_exc:
            current_state = human_takeover.status()
            return error_exit(
                "runtime switch encountered a controlled failure and human-takeover persistence failed; "
                f"stage={stage} terminal_audit={'failed' if terminal_audit_error else 'recorded'} "
                f"takeover_error={type(takeover_exc).__name__}; "
                f"state={current_state['state']} generation={current_state['generation']}; "
                "stop automation, inspect audit storage, run `eduflow human-takeover status`, and retry"
            )
        return error_exit(
            "runtime switch requires human attention; human takeover entered "
            f"stage={stage} terminal_audit={'failed' if terminal_audit_error else 'recorded'} "
            f"state={attention['state']} generation={attention['generation']}; "
            "inspect audit storage, verify live runtime, then recover explicitly",
            rc=2,
        )
    return _emit(outcome, agent, to_runtime, reason, as_json,
                 {"verdict": probe.get("verdict", outcome),
                  "from_runtime": current})
