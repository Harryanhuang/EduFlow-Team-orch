"""`eduflow inbox <agent>`

List unread messages for an agent. Read messages don't appear by default.

Subcommands:
  `eduflow inbox <agent>`          – list unread messages
  `eduflow inbox prune [--json]`   – archive orphan messages
  `eduflow inbox stats [--json]`   – per-agent inbox statistics
"""
from __future__ import annotations

from eduflow.runtime import config
from eduflow.store import local_facts
from eduflow.util import fmt_time_ms, pop_bool_flag, print_json, usage_error


USAGE = (
    "usage: eduflow inbox <agent>\n"
    "   or: eduflow inbox prune [--json]\n"
    "   or: eduflow inbox stats [--json]"
)


def _list_agent(agent: str) -> int:
    local_facts.touch_heartbeat(agent)
    msgs = local_facts.list_messages(agent, unread_only=True)
    if not msgs:
        print(f"📭 {agent}: no unread messages")
        return 0
    print(f"📬 {agent}: {len(msgs)} unread")
    for m in msgs:
        ts = fmt_time_ms(m.get("created_at", 0))
        local_id = m.get("local_id", "")
        frm = m.get("from", "?")
        priority = m.get("priority", "?")
        content = m.get("content", "")
        delivery_state = str(m.get("delivery_state") or "delivered_to_inbox")
        print(f"── [{ts}] {frm} → {agent}  [{priority}]  {local_id}")
        print(f"   delivery={delivery_state}")
        print(f"   {content}")
    return 0


def _prune(as_json: bool) -> int:
    # Build valid agent set from TOML config + agents directory
    valid = set(config.agent_names())
    from eduflow.runtime import paths as runtime_paths
    agents_dir = runtime_paths.state_dir() / "agents"
    if agents_dir.is_dir():
        for child in agents_dir.iterdir():
            if child.is_dir():
                valid.add(child.name)
    result = local_facts.prune_orphan_messages(valid)
    if as_json:
        print_json(result)
    else:
        pruned = result["pruned"]
        affected = result["agents_affected"]
        if pruned:
            print(f"🧹 pruned {pruned} orphan messages from: {', '.join(affected)}")
        else:
            print("✅ no orphan messages to prune")
    return 0


def _stats(as_json: bool) -> int:
    result = local_facts.inbox_stats()
    if as_json:
        print_json(result)
    else:
        print(f"📊 inbox: {result['total']} total messages")
        for agent, counts in sorted(result["agents"].items()):
            unread = counts["unread"]
            total = counts["total"]
            marker = f" ({unread} unread)" if unread else ""
            print(f"  {agent}: {total}{marker}")
    return 0


def main(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error(USAGE)
    as_json = pop_bool_flag(rest, "--json")
    if not rest:
        return usage_error(USAGE)
    if rest[0] == "prune":
        return _prune(as_json)
    if rest[0] == "stats":
        return _stats(as_json)
    return _list_agent(rest[0])
