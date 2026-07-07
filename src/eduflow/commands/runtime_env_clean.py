"""`eduflow runtime env-clean` — print unset commands for stale env vars.

T-137 #3: helper to strip shell env that overrides toml. Some operators
run with EDUFLOW_ROUTER_STALE_S=1200 lingering from a previous session
without realizing it shadows eduflow.toml router.stale_event_threshold_s=86400
(T-130) and breaks the router's intent. Print the exact unset commands
so an operator can copy-paste them into a fresh shell, before launching
eduflow watchdog.

Usage:
  eduflow runtime env-clean              # print unset commands
  eduflow runtime env-clean --apply       # print AND unset in current shell (uses os.environ)
  eduflow runtime env-clean --json       # machine-readable list
"""
from __future__ import annotations
import json
import os
import sys

from eduflow.util import maybe_print_help, print_json


# T-137: list of env vars that override eduflow.toml and are commonly
# stale. Add new entries here when adding runtime-pool-level env aliases.
KNOWN_OVERRIDES = (
    "EDUFLOW_ROUTER_STALE_S",  # legacy alias for stale_event_threshold_s
    "EDUFLOW_LARK_SEND_AS",    # legacy alias for feishu.send_as
)


def _stale_overrides() -> list[str]:
    return [k for k in KNOWN_OVERRIDES if os.environ.get(k)]


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, "usage: eduflow runtime env-clean [--apply] [--json]"):
        return 0
    apply = "--apply" in argv
    as_json = "--json" in argv
    if [a for a in argv if a not in ("--apply", "--json")]:
        print("usage: eduflow runtime env-clean [--apply] [--json]", file=sys.stderr)
        return 1

    stale = _stale_overrides()
    if as_json:
        print_json({"stale_env": stale, "unset_commands": [f"unset {k}" for k in stale]})
        return 0
    if not stale:
        print("✅ no stale eduflow env overrides detected")
        return 0
    print(f"⚠️  detected {len(stale)} stale env override(s):")
    for k in stale:
        v = os.environ.get(k, "")
        print(f"  - {k}={v!r}  (overrides eduflow.toml)")
        print(f"    unset {k}")
    if apply:
        for k in stale:
            os.environ.pop(k, None)
        print(f"\n✅ unset {len(stale)} env var(s) in current process")
    else:
        print("\nrun with --apply to unset in the current shell, or copy-paste the unset lines above")
    return 0
