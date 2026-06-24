"""Pid file primitives + single-instance daemon lock.

Public surface:
  - `read_pid(pid_file)`     → int | None — parse a pid file safely
  - `pid_alive(pid)`         → bool       — kill -0 wrapper, OSError = False
  - `acquire(pid_file)`      → bool       — claim or reject based on liveness
  - `repair_pid_file(pid_file)` → bool    — self-heal pid file unlinked after acquire
  - `release(pid_file)`      → None       — drop the lock on graceful exit

`acquire` / `release` are the daemon lifecycle pair (`eduflow router`
and `eduflow watchdog` use them). `read_pid` / `pid_alive` are the
primitives that grew out — `commands/down._kill_pid_file`,
`watchdog.is_alive`, `commands/health._check_daemon` all need to
inspect "the pid that owns this file, if any" without claiming the
lock, and they used to each reimplement the int-parse + os.kill(0)
fences.

The lock uses `fcntl.flock(LOCK_EX | LOCK_NB)` for true OS-level mutual
exclusion. The previous PID-file-content + kill-0 approach had a TOCTOU
race: two processes could both check the old PID as dead, both overwrite
the file, and both start running simultaneously. flock is atomic at the
kernel level — only one fd can hold LOCK_EX at a time.

Stale locks (pid file present but the recorded pid is dead, e.g. after
a crash) are handled automatically: when a process exits, the OS closes
all its fds, releasing the flock. The next acquire() gets the lock
immediately.
"""
from __future__ import annotations

import fcntl
import os
import time
from pathlib import Path

from eduflow.runtime import paths
from eduflow.util import warn

_held_fds: dict[Path, int] = {}


def read_pid(pid_file: Path) -> int | None:
    """Parse `pid_file` as an integer. Returns None when the file is
    missing, unreadable, or contains non-int content.

    Used wherever code needs "the pid that owns this file, if any" —
    `acquire` here, `watchdog.is_alive`, `commands/down._kill_pid_file`,
    `commands/health._check_daemon`. Centralised so any future tweak
    (e.g. trimming a pid+timestamp format) lands in one place.
    """
    try:
        return int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def pid_alive(pid: int) -> bool:
    """True if `pid` exists and we can signal it (kill 0).

    OSError covers ProcessLookupError (no such pid), PermissionError
    (not ours — but daemons here are always owned by the same user
    so this rarely fires), and other variants. Either way: not usable.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire(pid_file: Path, *, name: str = "",
            wait_for_release_s: float = 3.0) -> bool:
    """Claim `pid_file` for the current process via flock(LOCK_EX).

    Returns True on success. Returns False if another **live** process
    already owns the lock — prints to stderr in that case. Stale locks
    (pid file present but flock available because the old holder exited)
    are quietly overwritten.

    Uses `fcntl.flock(LOCK_EX | LOCK_NB)` for true OS-level mutual
    exclusion. The previous PID-file-content + kill-0 approach had a
    TOCTOU race: two processes could both check the old PID as dead,
    both overwrite the file, and both start running simultaneously —
    causing interleaved log writes, cursor rename races, and dropped
    messages. flock is atomic at the kernel level.

    `wait_for_release_s` handles the SIGTERM-in-progress race: when an
    operator does `eduflow down` immediately followed by `eduflow
    up`, the previous router is mid-shutdown (signal handler running,
    flock not yet released) when the new router runs `acquire`. Without
    a wait, the new router sees the still-held lock and refuses. Spin-
    poll flock for up to a few seconds — long enough to ride out the
    typical sigterm cleanup, short enough that a genuinely-stuck other-
    instance still surfaces an error promptly.
    """
    paths.ensure_state_dir()
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        fd = os.open(str(pid_file), os.O_RDWR | os.O_CREAT, 0o644)
    except OSError as e:
        warn(f"❌ {name or 'pidlock'}: cannot open pid file ({e})")
        return False

    try:
        deadline = time.monotonic() + max(wait_for_release_s, 0)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (IOError, OSError):
                if time.monotonic() >= deadline:
                    os.lseek(fd, 0, os.SEEK_SET)
                    data = os.read(fd, 100).decode("utf-8", errors="ignore").strip()
                    try:
                        old_pid = int(data)
                    except ValueError:
                        old_pid = "unknown"
                    warn(f"❌ another {name or 'instance'} already running (pid {old_pid})")
                    os.close(fd)
                    return False
                time.sleep(0.1)

        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, (str(os.getpid()) + "\n").encode("utf-8"))
        os.fsync(fd)

        # Verify our fd still points to the same inode as the path.
        # A concurrent release() may have unlinked the file while we
        # waited for the flock, leaving our fd pointing at an orphaned
        # inode. Re-open to ensure writes land on the current file.
        try:
            fd_ino = os.fstat(fd).st_ino
            path_ino = os.stat(str(pid_file)).st_ino
        except (OSError, FileNotFoundError):
            path_ino = 0
            fd_ino = 1
        if fd_ino != path_ino:
            os.close(fd)
            fd = os.open(str(pid_file), os.O_RDWR | os.O_CREAT, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, (str(os.getpid()) + "\n").encode("utf-8"))
            os.fsync(fd)

        _held_fds[pid_file] = fd
        return True
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def repair_pid_file(pid_file: Path, *, name: str = "") -> bool:
    """Self-heal a pid file that was unlinked or corrupted after acquire().

    Called periodically by long-running daemons (watchdog, router) to
    recover from an external `eduflow down` that unlinks the pid file
    without killing this process — or from a race where `release()`
    (another process) unlinked the file after our acquire() wrote it.

    Returns True if the file is healthy (exists and contains our PID) or
    was successfully repaired. Returns False if we don't hold a flock fd
    for this file, or if repair failed (e.g., another live process now
    holds the lock on a fresh inode — genuine conflict).

    Edge cases handled:
    - File missing entirely → close old fd, re-create, re-flock, write PID
    - File present but empty/wrong PID → close old fd, re-open, re-flock, write
    - Another process claimed the new inode → flock fails, return False
    """
    old_fd = _held_fds.get(pid_file)
    if old_fd is None:
        return False

    # Fast path: file exists and contains our PID — nothing to repair.
    if pid_file.exists():
        try:
            if int(pid_file.read_text(encoding="utf-8").strip()) == os.getpid():
                return True
        except (OSError, ValueError):
            pass

    # Release the old flock, then re-open and re-acquire. If another
    # process grabbed the lock in between, flock will fail and we
    # return False — genuine conflict.
    try:
        os.close(old_fd)
    except OSError:
        pass
    _held_fds.pop(pid_file, None)

    try:
        paths.ensure_state_dir()
        fd = os.open(str(pid_file), os.O_RDWR | os.O_CREAT, 0o644)
    except OSError as e:
        warn(f"⚠️ {name or 'pidlock'}: repair pid file open failed ({e})")
        return False

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        os.close(fd)
        warn(f"⚠️ {name or 'pidlock'}: repair flock failed — "
             "another process holds the pid file lock")
        return False

    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, (str(os.getpid()) + "\n").encode("utf-8"))
    os.fsync(fd)

    _held_fds[pid_file] = fd
    return True


def release(pid_file: Path) -> None:
    """Release the flock and close the fd holding it. Best-effort — swallows
    any I/O exception since this runs in a `finally` clause.

    Only closes if we hold the flock (fd in _held_fds). A release()
    without a prior acquire() is a noop.

    The PID file is left on disk with the stale PID. This is intentional:
    health checks and the watchdog can distinguish "process exited
    gracefully" (pid file present but process dead) from "crash / never
    started" (no pid file). The next `acquire()` overwrites the file
    normally since the flock is released when the fd is closed.
    """
    fd = _held_fds.pop(pid_file, None)
    if fd is None:
        return
    try:
        os.close(fd)
    except Exception:
        pass
