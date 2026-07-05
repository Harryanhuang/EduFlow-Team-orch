"""`eduflow down` — opposite of `up`: stop daemons + tear down tmux.

Order matters: kill daemons first (so the watchdog doesn't respawn the
router we just killed), then kill tmux. Pid files get unlinked once the
process is confirmed dead.

Safety: before killing, verifies a live process cmdline matches the
expected entrypoint. If a daemon's pid points to an unexpected process
(PID reuse / drift), refuses to kill and reports the drift. Use
`--force` to override.

Targeting: `eduflow down [name ...]` kills only the named daemons
(e.g. `eduflow down router`). For the router specifically, warns
that restart-with-catchup is usually safer and suggests
`eduflow up` (idempotent, will respawn dead daemons without killing
live ones). Use `--force` to suppress the warning.

Always best-effort — a missing pid file or already-dead process does
not raise. Returns 0 unless something we expected to be alive refused
to die.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

from eduflow.runtime import config, pidlock, tmux, watchdog
from eduflow.util import error_exit, maybe_print_help, warn


def _terminate_pid(name: str, pid: int) -> int:
    """Best-effort SIGTERM/SIGKILL shutdown for one pid."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        print(f"⏭  {name}: pid {pid} already dead")
        return 0
    except PermissionError as e:
        return error_exit(f"❌ {name}: not allowed to kill pid {pid}: {e}")

    # SIGTERM grace, then escalate to SIGKILL. Smoke v3: 3s wasn't enough
    # for router/watchdog mid-lark-cli to flush — 10s catches the slow
    # path; SIGKILL fallback guarantees `compose down` doesn't punt to
    # the operator.
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            print(f"🛑 {name}: pid {pid} stopped")
            return 0
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        print(f"🛑 {name}: pid {pid} stopped")
        return 0
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            print(f"🛑 {name}: pid {pid} stopped (after SIGKILL)")
            return 0
        time.sleep(0.1)
    return error_exit(
        f"⚠️  {name}: pid {pid} still alive after 12s SIGTERM+SIGKILL — investigate manually")


def _pid_cwd(pid: int) -> Path | None:
    try:
        r = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    for line in (r.stdout or "").splitlines():
        if line.startswith("n"):
            try:
                return Path(line[1:]).resolve()
            except OSError:
                return None
    return None


def _reap_duplicate_daemons(spec, *, keep_pid: int | None = None) -> int:
    """Kill same-cwd duplicate daemons missed by pidfile shutdown.

    ponytail: this exists because old pid files can be removed while the
    original daemon keeps running; if that stops happening, delete this.
    """
    try:
        r = subprocess.run(
            ["pgrep", "-f", f"eduflow.cli {spec.name}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    repo_cwd = Path.cwd().resolve()
    rc = 0
    for raw in (r.stdout or "").splitlines():
        raw = raw.strip()
        if not raw.isdigit():
            continue
        pid = int(raw)
        if keep_pid is not None and pid == keep_pid:
            continue
        if not pidlock.pid_alive(pid):
            continue
        if _pid_cwd(pid) != repo_cwd:
            continue
        rc |= _terminate_pid(f"{spec.name} duplicate", pid)
    return rc


def _kill_pid_file(name: str, pid_file, *,
                   expected_cmdline: str = "",
                   force: bool = False) -> tuple[int, int | None]:
    if not pid_file.exists():
        print(f"⏭  {name}: no pid file")
        return 0, None
    pid = pidlock.read_pid(pid_file)
    if pid is None:
        print(f"⏭  {name}: corrupt pid file, removing")
        pid_file.unlink(missing_ok=True)
        return 0, None

    # Safety: verify a live pid's cmdline matches expected entrypoint before
    # killing. Without this, a PID-reused pid file could cause us to kill an
    # unrelated process. If kill(pid, 0) says the process is already gone,
    # skip drift detection and let the normal ProcessLookupError branch clean
    # the stale pid file. If we can't read cmdline at all (e.g. /proc missing,
    # ps failed), skip the check rather than refuse to kill — the operator ran
    # `down` intentionally.
    if expected_cmdline and not force:
        from eduflow.runtime.watchdog import _read_cmdline
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError as e:
            return error_exit(f"❌ {name}: not allowed to inspect pid {pid}: {e}"), pid
        else:
            cmdline = _read_cmdline(pid)
            if cmdline and expected_cmdline not in cmdline:
                return error_exit(
                    f"❌ {name}: pid {pid} exists but cmdline doesn't match "
                    f"'{expected_cmdline}' — entrypoint drift detected. "
                    f"Refusing to kill. Use --force to override."), pid

    rc = _terminate_pid(name, pid)
    if rc == 0:
        pid_file.unlink(missing_ok=True)
    return rc, pid


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, "usage: eduflow down [--force] [daemon ...]"):
        return 0
    force = "--force" in rest
    if force:
        rest.remove("--force")

    # If specific daemons named, filter specs; otherwise kill all.
    if rest:
        named = set(rest)
        specs = [s for s in watchdog.all_known_specs() if s.name in named]
        unknown = named - {s.name for s in specs}
        if unknown:
            warn(f"⚠️  unknown daemon(s): {', '.join(sorted(unknown))}")
    else:
        specs = list(watchdog.all_known_specs())

    # Warn when targeting router specifically — usually the operator
    # wants a restart-with-catchup, not a raw kill.
    if any(s.name == "router" for s in specs) and not force:
        print("ℹ️  router: prefer `eduflow up` (idempotent respawn) or "
              "`eduflow down --force router` if you really need to kill it. "
              "Router restart triggers catchup replay, which may duplicate "
              "recent messages briefly.")

    rc = 0
    # Kill in reverse-of-startup order so the watchdog can't respawn
    # the router we just killed. all_known_specs is router-then-watchdog;
    # reversed → watchdog first.
    for spec in reversed(specs):
        kill_rc, killed_pid = _kill_pid_file(
            spec.name,
            spec.pid_file,
            expected_cmdline=spec.expected_cmdline,
            force=force,
        )
        rc |= kill_rc
        rc |= _reap_duplicate_daemons(spec, keep_pid=killed_pid)

    if rest:
        print("⏭  tmux session left running (named daemon shutdown)")
    else:
        session = config.session_name()
        if tmux.has_session(session):
            if tmux.kill_session(session):
                print(f"🛑 tmux session {session} killed")
            else:
                warn(f"⚠️  failed to kill tmux session {session}")
                rc |= 1
        else:
            print(f"⏭  tmux session {session} not running")

    print("✅ team down" if rc == 0 else "⚠️  team down with warnings")
    return rc
