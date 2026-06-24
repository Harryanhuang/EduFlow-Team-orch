"""`eduflow task-publish`

Minimal task publish loop over store-produced task events.
"""
from __future__ import annotations

import signal
import time

from eduflow.commands import task as task_cmd
from eduflow.runtime import paths, pidlock, tunables
from eduflow.util import (
    error_exit, maybe_print_help, pop_bool_flag, pop_flag, usage_error,
)


USAGE = (
    "usage: eduflow task-publish "
    "[--to user|manager|worker_<name>] [--once] [--send] [--advance] [--interval-seconds N]"
)


def _run_once(*, to_target: str, do_send: bool, advance: bool) -> int:
    argv = ["publish-run", "--to", to_target]
    if do_send:
        argv.append("--send")
    if advance:
        argv.append("--advance")
    return task_cmd.main(argv)


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, USAGE):
        return 0
    rest = list(argv)
    to_target = pop_flag(rest, "--to") or "user"
    once = pop_bool_flag(rest, "--once")
    do_send_flag = pop_bool_flag(rest, "--send")
    advance_flag = pop_bool_flag(rest, "--advance")
    interval_explicit = pop_flag(rest, "--interval-seconds")
    if rest:
        return usage_error(USAGE)
    do_send = do_send_flag or not once
    advance = advance_flag or not once

    if advance and not do_send:
        return error_exit("❌ --advance requires --send")

    if interval_explicit is not None:
        try:
            interval_s = max(1.0, float(interval_explicit))
        except ValueError:
            return usage_error(USAGE)
    else:
        interval_s = float(tunables.tunable("task_publish.interval_seconds", 15.0))

    if once:
        return _run_once(to_target=to_target, do_send=do_send, advance=advance)

    pid_file = paths.task_publish_pid_file()
    if not pidlock.acquire(pid_file, name="task-publish"):
        return 1
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(SystemExit(0)))
    print(
        f"🔁 task-publish loop started: to={to_target} "
        f"send={str(do_send).lower()} advance={str(advance).lower()} "
        f"interval={interval_s:g}s"
    )
    try:
        while True:
            rc = _run_once(to_target=to_target, do_send=do_send, advance=advance)
            if rc != 0:
                return rc
            time.sleep(interval_s)
    except KeyboardInterrupt:
        print("task-publish stopped")
        return 0
    finally:
        pidlock.release(pid_file)
