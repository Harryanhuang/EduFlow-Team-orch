"""`eduflow runtime <subcommand>` — runtime management surface.

Subcommands:
  runtime switch <agent> <runtime> [--reason <r>] [--no-smoke] [--json]
      Hard-switch a running agent pane to the given runtime. Runs the
      proved-ready gate by default (live env + API smoke + pane-text
      scan). Use --no-smoke to skip the gate for emergency overrides.

  runtime verify <agent> [--json]
      Compute and display the runtime operational readiness verdict for
      one agent: proved_ready / ready_unproven / env_drift /
      smoke_failed / inbox_not_consumed / pane_missing.

  runtime list [<agent>] [--json]
      Show the resolved runtime chain for one agent (or all agents).
      Highlights the currently-selected runtime with `→`. Useful for
      discovering which runtime names are valid targets for
      `runtime switch`.

  runtime events [--last N] [--json]
      Show the most recent switch events from runtime-switch-events.jsonl.

All output is JSON-friendly so operator tooling (and the manager agent
reading the feed) can branch on verdicts.
"""
from __future__ import annotations

from eduflow.util import (
    maybe_print_help,
)


USAGE = (
    "usage:\n"
    "  eduflow runtime switch <agent> <runtime> [--reason <r>] [--no-smoke] [--json]\n"
    "  eduflow runtime verify <agent> [--json] [--live-smoke]\n"
    "  eduflow runtime list [<agent>] [--json]\n"
    "  eduflow runtime events [--last N] [--json]"
)


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    if not rest:
        print(USAGE)
        return 1
    sub = rest[0]
    args = rest[1:]
    if sub == "switch":
        from eduflow.commands import runtime_switch
        return runtime_switch.main(args)
    if sub == "verify":
        from eduflow.commands import runtime_verify
        return runtime_verify.main(args)
    if sub == "list":
        from eduflow.commands import runtime_list
        return runtime_list.main(args)
    if sub == "events":
        from eduflow.commands import runtime_events
        return runtime_events.main(args)
    print(f"unknown runtime subcommand: {sub!r}\n{USAGE}")
    return 1
