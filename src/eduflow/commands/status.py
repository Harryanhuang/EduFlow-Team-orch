"""`eduflow status <agent> <state> <task> [blocker]`

Upsert an agent's latest status (no history; latest wins).  Each agent
has at most one status row.  Reading is via `eduflow status <agent>`
with no further args.
"""
from __future__ import annotations

from eduflow.store import local_facts
from eduflow.util import usage_error


USAGE = (
    "usage:\n"
    "  eduflow status <agent>                       # show current\n"
    "  eduflow status <agent> <state> <task> [blocker]  # set"
)


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        return usage_error(USAGE)

    agent = argv[0]
    local_facts.touch_heartbeat(agent)

    # show mode
    if len(argv) == 1:
        snap = local_facts.get_status(agent)
        if snap is None:
            print(f"❓ {agent}: no status recorded")
            return 0
        line = f"{agent}: {snap['status']} | {snap['task']}"
        if snap.get("blocker"):
            line += f" | ⛔ {snap['blocker']}"
        print(line)
        return 0

    # set mode
    if len(argv) < 3:
        return usage_error(USAGE)
    state = argv[1]
    task = argv[2]
    blocker = argv[3] if len(argv) > 3 else ""
    local_facts.upsert_status(agent, state, task, blocker=blocker)
    print(f"✅ {agent} → {state}: {task}" + (f" ⛔ {blocker}" if blocker else ""))
    return 0
