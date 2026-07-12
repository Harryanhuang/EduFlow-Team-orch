"""Operator CLI for the durable automation circuit breaker."""
from __future__ import annotations

from eduflow.runtime import human_takeover as takeover, tunables
from eduflow.util import error_exit, pop_bool_flag, pop_flag, print_json


USAGE = "usage: eduflow human-takeover status|enter|recover [--json]"


def _is_provisioned_actor_id(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    lowered = value.casefold()
    if any(char in value for char in "<>{}[]$*") or any(char.isspace() for char in value):
        return False
    unprovisioned_markers = ("placeholder", "changeme", "change_me", "replace_me", "your_", "todo")
    return lowered not in {"none", "null", "example"} and not any(
        marker in lowered for marker in unprovisioned_markers
    )


def _authorized_actors() -> set[str]:
    team = tunables.load().get("team", {})
    if not isinstance(team, dict):
        return set()
    operators = team.get("operators", [])
    admins = team.get("admins", [])
    if not isinstance(operators, list) or not isinstance(admins, list):
        return set()
    configured = [*operators, *admins]
    if any(not _is_provisioned_actor_id(actor) for actor in configured):
        return set()
    return set(configured)


def _authorize(actor: str | None) -> bool:
    return bool(_is_provisioned_actor_id(actor) and actor in _authorized_actors())


def main(argv: list[str]) -> int:
    rest = list(argv)
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0] in {"-h", "--help"}:
        print(USAGE)
        return 0 if rest else 1
    action = rest.pop(0)
    if action == "status":
        if rest:
            return error_exit(f"unexpected args: {rest}\n{USAGE}")
        state = takeover.status()
        print_json(state) if as_json else print(f"human-takeover: {state['state']} generation={state['generation']}")
        return 0

    actor = pop_flag(rest, "--actor")
    reason = pop_flag(rest, "--reason")
    if not _authorize(actor):
        return error_exit("unauthorized: configured operator/admin --actor required")
    if not reason:
        return error_exit("--reason is required")
    try:
        if action == "enter":
            if rest:
                return error_exit(f"unexpected args: {rest}\n{USAGE}")
            state = takeover.enter(reason=reason, source="manual_cli", actor=actor or "")
        elif action == "recover":
            generation_raw = pop_flag(rest, "--generation")
            steps: list[str] = []
            while "--step" in rest:
                step = pop_flag(rest, "--step")
                if step is not None:
                    steps.append(step)
            if generation_raw is None or rest:
                return error_exit("recover requires --generation and optional --step values")
            state = takeover.recover(actor=actor or "", reason=reason, recovery_steps=steps,
                                     expected_generation=int(generation_raw))
        else:
            return error_exit(f"unknown human-takeover action: {action}\n{USAGE}")
    except (takeover.InvalidTransition, takeover.StaleGeneration, ValueError) as exc:
        return error_exit(str(exc))
    except (OSError, TimeoutError) as exc:
        current = takeover.status()
        return error_exit(
            f"human-takeover persistence failure ({type(exc).__name__}); "
            f"state={current['state']} generation={current['generation']}; "
            "run `eduflow human-takeover status`, repair storage/locking, then retry"
        )
    print_json(state) if as_json else print(f"human-takeover: {state['state']} generation={state['generation']}")
    return 0
