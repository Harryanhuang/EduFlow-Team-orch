"""Admin-only local operations for the durable message-delivery ledger."""
from __future__ import annotations

from eduflow.runtime import tunables
from eduflow.security import authorization
from eduflow.store import message_delivery
from eduflow.util import error_exit, pop_bool_flag, pop_flag, print_json


USAGE = (
    "usage: eduflow message-delivery list|replay|resolve|clear-hold "
    "[message_id] --actor <admin_id> [--reason <text>] [--json]"
)


def _authorized(actor: str | None) -> bool:
    config = tunables.load()
    team = config.get("team", {}) if isinstance(config, dict) else {}
    _, admins, valid = authorization.configured_roles(team)
    return bool(valid and authorization.is_provisioned_actor_id(actor) and actor in admins)


def _require_admin(actor: str | None) -> int | None:
    if _authorized(actor):
        return None
    return error_exit("unauthorized: configured admin --actor required")


def _render_rows(rows: list[dict], *, as_json: bool) -> None:
    if as_json:
        print_json(rows)
        return
    if not rows:
        print("no dead-letter deliveries")
        return
    for row in rows:
        print(
            f"{row.get('message_id') or '-'} "
            f"attempts={row.get('attempts') or 0} "
            f"reason={row.get('failure_reason') or '-'}"
        )


def main(argv: list[str]) -> int:
    rest = list(argv)
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0] in {"-h", "--help"}:
        print(USAGE)
        return 0 if rest else 1
    action = rest.pop(0)
    actor = pop_flag(rest, "--actor")
    unauthorized = _require_admin(actor)
    if unauthorized is not None:
        return unauthorized

    if action == "list":
        if rest:
            return error_exit(f"unexpected args: {rest}\n{USAGE}")
        _render_rows(message_delivery.list_dead_letters(), as_json=as_json)
        return 0

    if action == "clear-hold":
        reason = pop_flag(rest, "--reason")
        if rest or not reason:
            return error_exit(f"--reason is required\n{USAGE}")
        if not message_delivery.clear_automation_hold(actor=actor or "", reason=reason):
            return error_exit("automation hold is not active")
        result = {"status": "automation_hold_cleared"}
        if as_json:
            print_json(result)
        else:
            print("message-delivery: automation_hold_cleared")
        return 0

    if not rest:
        return error_exit(f"message_id is required\n{USAGE}")
    message_id = rest.pop(0)
    reason = pop_flag(rest, "--reason")
    if rest or not reason:
        return error_exit(f"--reason is required\n{USAGE}")
    try:
        if action == "replay":
            decision = message_delivery.replay_dead_letter(
                message_id, actor=actor or "", reason=reason)
            if decision is None:
                return error_exit(
                    "dead-letter cannot be replayed automatically; use resolve "
                    "after human verification if Slash execution/publication is uncertain"
                )
            result = {"message_id": decision.msg_id, "status": "queued_for_retry"}
        elif action == "resolve":
            if not message_delivery.resolve_uncertain_slash(
                message_id, actor=actor or "", reason=reason
            ):
                return error_exit("dead-letter is not an unresolved Slash publication")
            result = {"message_id": message_id, "status": "human_resolved_terminal"}
        else:
            return error_exit(f"unknown message-delivery action: {action}\n{USAGE}")
    except (OSError, TimeoutError, ValueError) as exc:
        return error_exit(f"message-delivery persistence failure: {exc}")

    if as_json:
        print_json(result)
    else:
        print(f"message-delivery: {result['message_id']} {result['status']}")
    return 0
