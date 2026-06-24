"""`eduflow remember <agent> <kind> <content> [--ref <ref>]`

Append an entry to `<agent>`'s durable memory (`store/memory.py`).
Memory survives tmux pane restart / `/clear`, gets injected into the
agent's identity init prompt on wake so context carries over.

Example:
    eduflow remember manager task_assigned "implement remember cmd" --ref om_xx
    eduflow remember worker_cc learning "auth uses bcrypt; salt rounds=12"
    eduflow remember worker_codex blocker "blocked on missing GH PAT" --ref T-42

Convention for `kind` (not enforced):
    task_assigned / task_completed / learning / blocker / decision / note
"""
from __future__ import annotations

from eduflow.store import memory
from eduflow.util import maybe_print_help, pop_flag, usage_error


USAGE = (
    "usage: eduflow remember <agent> <kind> <content> [--ref <ref>]\n"
    f"       known kinds: {memory.kinds_summary()}\n"
    "       (any string accepted; unknown kinds get a stderr nudge)"
)


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    ref = pop_flag(rest, "--ref") or ""
    if len(rest) < 3:
        return usage_error(USAGE)
    agent = rest[0]
    kind = rest[1]
    # Join everything after kind into a single content string (so callers
    # can pass an unquoted message without surprising arg-count errors).
    content = " ".join(rest[2:])
    record = memory.append(agent, kind, content, ref=ref)
    suffix = f" (ref={ref})" if ref else ""
    print(f"🧠 remembered: {agent}/{kind}{suffix}  [{record['created_at']}]")
    return 0
