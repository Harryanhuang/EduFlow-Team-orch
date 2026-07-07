"""`eduflow daemon restart --all` / `eduflow daemon heal`

Graceful one-key recovery for the router / task-publish / watchdog
daemons. Sends SIGTERM, waits up to 5s for clean exit, then asks the
watchdog runtime to `respawn()` (which reaps orphans + spawns fresh
detached child). Print summary on the way out so the operator sees
which daemons were touched.
"""
from __future__ import annotations

import os
import signal
import time
from pathlib import Path

from eduflow.runtime import watchdog
from eduflow.util import maybe_print_help, usage_error


USAGE = "usage: eduflow daemon restart --all | eduflow daemon heal"


def _alive(spec: watchdog.ProcessSpec) -> bool:
    return watchdog.is_alive(spec)


def _terminate(spec: watchdog.ProcessSpec, *, grace_s: float = 5.0) -> bool:
    """SIGTERM → wait up to grace_s. Returns True if exited cleanly."""
    if not spec.pid_file.exists():
        return True
    try:
        pid = int(spec.pid_file.read_text().strip())
    except (OSError, ValueError):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    deadline = time.time() + grace_s
    while time.time() < deadline:
        if not _alive(spec):
            return True
        time.sleep(0.1)
    return not _alive(spec)


def _restart_one(spec: watchdog.ProcessSpec) -> tuple[str, str]:
    """Returns (name, status) where status ∈ {ok, restart_only, noop, fail}."""
    if not _alive(spec) and not spec.pid_file.exists():
        # Cold start: just respawn
        if watchdog.respawn(spec):
            return (spec.name, "started")
        return (spec.name, "fail: respawn failed")
    if not _alive(spec):
        # stale pid file → reap + respawn
        spec.pid_file.unlink(missing_ok=True)
        if watchdog.respawn(spec):
            return (spec.name, "respawned")
        return (spec.name, "fail: respawn after stale pid")
    if _terminate(spec):
        if watchdog.respawn(spec):
            return (spec.name, "restarted")
        return (spec.name, "fail: respawn after sigterm")
    return (spec.name, "fail: process did not exit")


def _print_rows(title: str, rows: list[tuple[str, str]]) -> int:
    print(title)
    for name, status in rows:
        glyph = "✅" if status.startswith("ok") or status in {
            "alive", "started", "restarted", "respawned",
        } else "❌"
        print(f"  {glyph} {name}: {status}")
    failed = [r for r in rows if r[1].startswith("fail")]
    if failed:
        print(f"❌ {len(failed)} daemon(s) failed")
        return 1
    return 0


def _heal(specs: list[watchdog.ProcessSpec]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for spec in specs:
        if _alive(spec):
            rows.append((spec.name, "alive"))
        else:
            rows.append(_restart_one(spec))
    return rows


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, USAGE):
        return 0
    if not argv:
        return usage_error(USAGE)
    sub = argv[0]
    specs = watchdog.all_known_specs()
    if sub == "heal":
        if len(argv) != 1:
            return usage_error(USAGE)
        return _print_rows("🩺 daemon heal summary:", _heal(specs))

    if sub != "restart":
        return usage_error(USAGE)
    flags = [a for a in argv[1:] if not a.startswith("-")]
    if flags:
        return usage_error(USAGE + " (no positional names when --all is set)")
    want_all = "--all" in argv

    if want_all:
        targets = specs
    else:
        # direct single-name form, but USAGE only shows the |all path; bail
        return usage_error(USAGE)

    rows = [_restart_one(s) for s in targets]
    return _print_rows("🔄 daemon restart summary:", rows)
