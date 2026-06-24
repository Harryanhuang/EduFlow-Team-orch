"""`eduflow runtime events` — show recent runtime switch events.

Reads the JSONL log at $STATE/facts/runtime-switch-events.jsonl and
prints the most recent N entries (default 20). Useful for postmortems
and for the manager agent to see the failover chain.
"""
from __future__ import annotations

from eduflow.runtime import verify
from eduflow.util import (
    maybe_print_help, pop_bool_flag, pop_flag, print_json, reject_extra_args,
)


USAGE = "usage: eduflow runtime events [--last N] [--json]"


def _fmt_time(ts: float) -> str:
    import datetime
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except (OSError, ValueError, TypeError):
        return "?"


def _emit_text(events: list[dict]) -> None:
    if not events:
        print("no switch events recorded yet")
        return
    for e in events:
        ts = _fmt_time(float(e.get("ts") or 0))
        agent = e.get("agent", "?")
        from_rt = e.get("from_runtime") or "-"
        to_rt = e.get("to_runtime") or "-"
        reason = e.get("reason") or "-"
        outcome = e.get("outcome") or "-"
        trigger = e.get("trigger") or "-"
        cross_pool = "cross_pool" if e.get("cross_pool") else ""
        env_ok = "env_ok" if e.get("env_ok") else ("env_bad" if e.get("env_ok") is False else "")
        smoke_ok = "smoke_ok" if e.get("smoke_ok") else ("smoke_bad" if e.get("smoke_ok") is False else "")
        tags = " ".join(filter(None, [cross_pool, env_ok, smoke_ok]))
        print(f"  {ts}  {agent:<16}  {from_rt} -> {to_rt:<30}  "
              f"reason={reason:<20}  outcome={outcome:<18}  trigger={trigger:<10} {tags}")


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    last = int(pop_flag(rest, "--last") or 20)
    if rest:
        print(f"❌ unexpected args: {rest}\n{USAGE}")
        return 1
    events = verify.read_switch_events(last_n=last)
    if as_json:
        print_json(events)
    else:
        _emit_text(events)
    return 0
