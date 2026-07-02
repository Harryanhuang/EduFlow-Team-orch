"""`eduflow compact <agent>` — inject literal /compact into an agent pane."""
from __future__ import annotations

import time

from eduflow.agents import adapter_for_agent, identity
from eduflow.runtime import config, tmux
from eduflow.util import error_exit, pop_bool_flag, pop_flag, usage_error


USAGE = "usage: eduflow compact <agent> [--delay seconds] [--no-reidentify]"
_COMPACT_REJECT_MARKER = "can't be triggered from inside a response"


def main(argv: list[str]) -> int:
    rest = list(argv)
    no_reidentify = pop_bool_flag(rest, "--no-reidentify")
    delay_s = float(pop_flag(rest, "--delay") or 45.0)
    if len(rest) != 1:
        return usage_error(USAGE)

    agent = rest[0]
    try:
        config.agent_config(agent)
    except KeyError:
        return error_exit(f"❌ unknown agent: {agent} (not in team.json)")

    session = config.session_name()
    if not tmux.has_session(session):
        return error_exit(
            f"❌ tmux session {session} not running; run `eduflow up` first")

    target = tmux.Target(session, agent)
    if not tmux.has_window(target):
        return error_exit(
            f"❌ {agent} has no pane in session {session} "
            f"(was it fired? try `eduflow hire {agent}`)")

    adapter = adapter_for_agent(agent)
    if not tmux.inject(target, "/compact", submit_keys=adapter.submit_keys()):
        return error_exit(f"❌ failed to inject /compact into {agent}")

    # Same guard as the Feishu slash path: if the CLI treated the slash as
    # plain prompt text, do not claim recovery or inject identity afterward.
    time.sleep(2.0)
    pane = tmux.capture_pane(target, lines=20) or ""
    if _COMPACT_REJECT_MARKER in pane:
        return error_exit(
            f"⚠️ /compact was rejected by {agent}; interrupt or retry when idle")

    print(f"✅ injected literal /compact into {agent} (pane: {target})")
    if no_reidentify:
        return 0

    time.sleep(delay_s)
    try:
        identity.write(agent)
    except Exception as e:
        return error_exit(f"❌ identity write failed for {agent}: {e}")
    if not tmux.inject(target, identity.init_prompt(agent),
                       submit_keys=adapter.submit_keys()):
        return error_exit(f"❌ failed to inject post-compact identity into {agent}")
    print(f"✅ re-injected identity after /compact into {agent}")
    return 0
