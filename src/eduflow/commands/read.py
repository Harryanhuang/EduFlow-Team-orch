"""`eduflow read <local_id>`

Mark a message as read by its local id.  Returns 1 if no such message.
"""
from __future__ import annotations

from eduflow.store import local_facts
from eduflow.util import error_exit, usage_error


USAGE = (
    "usage: eduflow read <local_id> "
    "[--ack accepted_task|started_task|accepted_revision|completed|reconciled] "
    "[--topic <topic>] [--file <path>] [--issue <text>]"
)


def _pop_option(rest: list[str], flag: str) -> str | None:
    if flag not in rest:
        return None
    idx = rest.index(flag)
    if idx + 1 >= len(rest):
        return ""
    value = rest[idx + 1]
    del rest[idx:idx + 2]
    return value


def main(argv: list[str]) -> int:
    rest = list(argv)
    ack_kind = _pop_option(rest, "--ack")
    topic = _pop_option(rest, "--topic") or ""
    files = []
    issues = []
    while True:
        value = _pop_option(rest, "--file")
        if value is None:
            break
        files.append(value)
    while True:
        value = _pop_option(rest, "--issue")
        if value is None:
            break
        issues.append(value)
    if len(rest) < 1:
        return usage_error(USAGE)
    local_id = rest[0]
    if not local_facts.mark_read(local_id):
        return error_exit(f"❌ no such message: {local_id}")
    if ack_kind:
        if not local_facts.record_message_ack(
            local_id,
            ack_kind,
            topic=topic,
            files=files,
            issues=issues,
        ):
            return error_exit(f"❌ could not record ack: {local_id}")
        print(f"✅ marked read: {local_id}  ack={ack_kind}")
    else:
        print(f"✅ marked read: {local_id}")
    return 0
