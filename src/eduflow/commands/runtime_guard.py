"""`eduflow runtime-guard`

Inspect and clear runtime guard state:
  - `eduflow runtime-guard`
  - `eduflow runtime-guard --json`
  - `eduflow runtime-guard clear <agent>`
  - `eduflow runtime-guard clear --all`
"""
from __future__ import annotations

from eduflow.runtime import paths
from eduflow.util import maybe_print_help, pop_bool_flag, print_json, read_json, reject_extra_args, write_json


USAGE = (
    "usage: eduflow runtime-guard [--json]\n"
    "   or: eduflow runtime-guard clear <agent>\n"
    "   or: eduflow runtime-guard clear --all"
)


def _state() -> dict:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    return read_json(path, {"agents": {}})


def _save(data: dict) -> None:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)


def _emit_text(data: dict) -> None:
    agents = data.get("agents", {})
    if not agents:
        print("runtime-guard: no agent state")
        return
    for agent in sorted(agents):
        row = agents[agent]
        cooldown_until = row.get("cooldown_until", 0)
        needs = row.get("needs_manager_action", False)
        switches = len(row.get("switch_times", []))
        line = f"{agent}  switches={switches}"
        if cooldown_until:
            line += f"  cooldown_until={cooldown_until}"
        if needs:
            line += "  needs_manager_action=true"
        if row.get("escalation_needed", False):
            line += "  escalation_needed=true"
        if row.get("last_switch_outcome"):
            line += f"  outcome={row['last_switch_outcome']}"
        if row.get("last_failure_reason"):
            line += f"  failure={row['last_failure_reason']}"
        if row.get("escalation_reason"):
            line += f"  escalation={row['escalation_reason']}"
        print(line)


def _clear_agent(agent: str) -> int:
    data = _state()
    agents = data.setdefault("agents", {})
    if agent not in agents:
        print(f"runtime-guard: {agent} not found")
        return 1
    del agents[agent]
    _save(data)
    print(f"runtime-guard: cleared {agent}")
    return 0


def _clear_all() -> int:
    _save({"agents": {}})
    print("runtime-guard: cleared all")
    return 0


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    if not rest:
        data = _state()
        if as_json:
            print_json(data)
        else:
            _emit_text(data)
        return 0
    if rest[0] != "clear":
        print(USAGE)
        return 1
    if len(rest) == 2 and rest[1] == "--all":
        return _clear_all()
    if len(rest) == 2:
        return _clear_agent(rest[1])
    if (rc := reject_extra_args(rest, USAGE)) is not None:
        return rc
    return 1
