"""Fail-closed authorization policy for the Feishu Slash control plane."""
from __future__ import annotations

from dataclasses import dataclass


READ_ONLY = "read_only"
OPERATOR = "operator"
ADMIN = "admin"


@dataclass(frozen=True)
class CommandPolicy:
    required_role: str
    mutating: bool = False


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    required_role: str
    reason: str


COMMAND_POLICIES: dict[str, CommandPolicy] = {
    "/help": CommandPolicy(READ_ONLY),
    "/team": CommandPolicy(OPERATOR),
    "/home": CommandPolicy(OPERATOR),
    "/employees": CommandPolicy(OPERATOR),
    "/employee": CommandPolicy(OPERATOR),
    "/sophon": CommandPolicy(OPERATOR),
    "/ops": CommandPolicy(OPERATOR),
    "/ops-dashboard": CommandPolicy(OPERATOR),
    "/health": CommandPolicy(OPERATOR),
    "/usage": CommandPolicy(OPERATOR),
    "/tmux": CommandPolicy(OPERATOR),
    "/review-queue": CommandPolicy(OPERATOR),
    "/manager-overview": CommandPolicy(OPERATOR),
    "/send": CommandPolicy(OPERATOR, mutating=True),
    "/dispatch": CommandPolicy(ADMIN, mutating=True),
    "/submit": CommandPolicy(ADMIN, mutating=True),
    "/assign-reviewer": CommandPolicy(ADMIN, mutating=True),
    "/compact": CommandPolicy(ADMIN, mutating=True),
    "/stop": CommandPolicy(ADMIN, mutating=True),
    "/clear": CommandPolicy(ADMIN, mutating=True),
}

MEMBER_READ_COMMANDS = frozenset(
    command
    for command, policy in COMMAND_POLICIES.items()
    if policy.required_role == READ_ONLY
)

WRITE_COMMANDS = frozenset(
    command
    for command, policy in COMMAND_POLICIES.items()
    if policy.mutating
)


def is_provisioned_actor_id(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    lowered = value.casefold()
    if any(char in value for char in "<>{}[]$*") or any(
        char.isspace() for char in value
    ):
        return False
    markers = (
        "placeholder",
        "changeme",
        "change_me",
        "replace_me",
        "your_",
        "todo",
    )
    return lowered not in {"none", "null", "example"} and not any(
        marker in lowered for marker in markers
    )


def configured_roles(team: object) -> tuple[set[str], set[str], bool]:
    if not isinstance(team, dict):
        return set(), set(), False

    resolved: dict[str, set[str]] = {}
    for key in ("operators", "admins"):
        value = team.get(key, [])
        if not isinstance(value, list) or any(
            not is_provisioned_actor_id(actor) for actor in value
        ):
            return set(), set(), False
        resolved[key] = set(value)
    return resolved["operators"], resolved["admins"], True


def authorize_slash(
    command: str,
    *,
    sender_id: str,
    team: object,
) -> AuthorizationDecision:
    policy = COMMAND_POLICIES.get(command)
    if policy is None:
        return AuthorizationDecision(False, "unregistered", "unregistered_command")
    if policy.required_role == READ_ONLY:
        return AuthorizationDecision(True, READ_ONLY, "read_only_allowlist")
    if not is_provisioned_actor_id(sender_id):
        return AuthorizationDecision(False, policy.required_role, "missing_sender_id")

    operators, admins, valid = configured_roles(team)
    if not valid:
        return AuthorizationDecision(
            False, policy.required_role, "invalid_authorization_config"
        )
    if policy.required_role == OPERATOR:
        if sender_id in operators or sender_id in admins:
            return AuthorizationDecision(True, OPERATOR, "authorized")
        return AuthorizationDecision(False, OPERATOR, "operator_required")
    if sender_id in admins:
        return AuthorizationDecision(True, ADMIN, "authorized")
    return AuthorizationDecision(False, ADMIN, "admin_required")
