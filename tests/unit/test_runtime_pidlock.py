"""Tests for runtime/pidlock.py — single-instance daemon lock."""
from __future__ import annotations

import os
from pathlib import Path

from helpers import attr_patch, isolated_env
from eduflow.runtime import paths, pidlock


def _seed_pid(value: str) -> Path:
    """Pre-populate router.pid with `value`. Returns the path."""
    pf = paths.router_pid_file()
    paths.ensure_state_dir()
    pf.write_text(value, encoding="utf-8")
    return pf


# ── acquire ─────────────────────────────────────────────────────


def test_acquire_writes_current_pid_when_file_missing():
    with isolated_env():
        pf = paths.router_pid_file()
        assert not pf.exists()
        assert pidlock.acquire(pf) is True
        assert pf.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_acquire_overwrites_stale_pid_file():
    """A pid file pointing at a dead pid is treated as stale."""
    with isolated_env():
        pf = _seed_pid("99999")  # almost certainly dead

        # patch os.kill to simulate "no such process"
        real_kill = os.kill

        def fake_kill(pid, sig):
            if pid == 99999:
                raise ProcessLookupError()
            return real_kill(pid, sig)

        with attr_patch(os, kill=fake_kill):
            assert pidlock.acquire(pf) is True
        assert pf.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_acquire_refuses_when_live_process_holds_lock():
    """When the flock is already held (by a prior acquire in this process
    or another process), a second acquire must return False. With flock,
    the lock is on the fd/inode, not the file content."""
    with isolated_env():
        pf = paths.router_pid_file()
        # First acquire succeeds — we now hold the flock
        assert pidlock.acquire(pf, name="router", wait_for_release_s=0) is True
        # Second acquire on same file must fail — flock is held
        assert pidlock.acquire(pf, name="router", wait_for_release_s=0) is False
        # Clean up
        pidlock.release(pf)


def test_acquire_spin_waits_for_sigterm_in_progress_then_takes_over():
    """When `eduflow down` sends SIGTERM and `eduflow up` runs
    immediately, the previous router is mid-shutdown — flock still held.
    Without a spin-wait, the new router refuses with 'another already
    running'. Simulate by holding the flock, then releasing it mid-wait
    via a background thread."""
    import time as _time
    import threading
    from eduflow.runtime import pidlock as plk
    with isolated_env():
        pf = paths.router_pid_file()
        # Acquire the flock first (simulating the old router)
        assert plk.acquire(pf, name="router", wait_for_release_s=0) is True
        # Release the flock after ~150ms in a background thread
        def delayed_release():
            _time.sleep(0.15)
            plk.release(pf)
        t = threading.Thread(target=delayed_release)
        t.start()
        # New acquire should spin-wait, then succeed once flock is released
        ok = plk.acquire(pf, name="router", wait_for_release_s=2.0)
        t.join()
        assert ok is True
        assert pf.read_text(encoding="utf-8").strip() == str(os.getpid())
        plk.release(pf)


def test_acquire_gives_up_after_wait_when_old_pid_stays_alive():
    """If the flock stays held past the spin-wait window, conclude
    it really is another instance and refuse. Don't wait forever."""
    import time as _time
    from eduflow.runtime import pidlock as plk
    with isolated_env():
        pf = paths.router_pid_file()
        # Hold the flock (simulating a running router)
        assert plk.acquire(pf, name="router", wait_for_release_s=0) is True
        # Second acquire should spin-wait then give up
        t0 = _time.monotonic()
        ok = plk.acquire(pf, name="router", wait_for_release_s=0.3)
        elapsed = _time.monotonic() - t0
        assert ok is False
        assert 0.3 <= elapsed < 0.6, f"elapsed={elapsed:.3f}s outside expected band"
        plk.release(pf)


def test_acquire_creates_state_dir_lazily():
    with isolated_env() as tmp:
        sd = tmp / "state"
        assert not sd.exists()
        pidlock.acquire(paths.router_pid_file())
        assert sd.exists()


def test_acquire_handles_garbage_pid_file_as_stale():
    with isolated_env():
        pf = _seed_pid("not-a-number")
        assert pidlock.acquire(pf) is True
        assert pf.read_text(encoding="utf-8").strip() == str(os.getpid())


# ── release ─────────────────────────────────────────────────────


def test_release_closes_fd_keeps_pid_file():
    with isolated_env():
        pf = paths.router_pid_file()
        pidlock.acquire(pf)
        assert pf.exists()
        pidlock.release(pf)
        # PID file survives so health/watchdog can distinguish graceful exit
        # (file present, process dead) from crash (no file).
        assert pf.exists()


def test_release_skips_when_pid_belongs_to_someone_else():
    with isolated_env():
        pf = _seed_pid("12345")  # not ours
        pidlock.release(pf)
        # untouched
        assert pf.exists()
        assert pf.read_text(encoding="utf-8").strip() == "12345"


def test_release_is_safe_when_file_missing():
    with isolated_env():
        pf = paths.router_pid_file()
        assert not pf.exists()
        pidlock.release(pf)  # must not raise


# ── repair_pid_file ──────────────────────────────────────────────


def test_repair_returns_false_when_no_held_fd():
    """Without a prior acquire(), repair is a noop that returns False."""
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.repair_pid_file(pf) is False


def test_repair_fast_path_when_file_healthy():
    """When the pid file exists and contains our PID, repair returns
    True without touching anything."""
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        mtime_before = pf.stat().st_mtime
        assert pidlock.repair_pid_file(pf, name="test") is True
        assert pf.stat().st_mtime == mtime_before  # untouched
        pidlock.release(pf)


def test_repair_recreates_missing_pid_file():
    """When the pid file was unlinked externally, repair re-creates it
    and the content matches our PID."""
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        # Simulate external unlink
        pf.unlink()
        assert not pf.exists()
        assert pidlock.repair_pid_file(pf, name="test") is True
        assert pf.exists()
        assert int(pf.read_text(encoding="utf-8").strip()) == os.getpid()
        pidlock.release(pf)


def test_repair_fixes_wrong_pid_content():
    """When the pid file exists but contains a different PID, repair
    overwrites it with our PID."""
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        # Corrupt the content to a different PID
        pf.write_text("99999", encoding="utf-8")
        assert pidlock.repair_pid_file(pf, name="test") is True
        assert int(pf.read_text(encoding="utf-8").strip()) == os.getpid()
        pidlock.release(pf)


def test_repair_handles_garbage_content():
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        # Corrupt the content to non-int garbage
        pf.write_text("not-a-pid", encoding="utf-8")
        assert pidlock.repair_pid_file(pf, name="test") is True
        assert int(pf.read_text(encoding="utf-8").strip()) == os.getpid()
        pidlock.release(pf)


def test_repair_with_orphaned_inode():
    """When the file was unlinked and a DIFFERENT file re-created by
    another process (so old fd points to orphaned inode), repair
    writes to the new inode and closes the orphaned fd."""
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        # Simulate: file was unlinked + a new empty file created (different inode)
        pf.unlink()
        pf.write_text("0", encoding="utf-8")  # fresh inode
        assert pidlock.repair_pid_file(pf, name="test") is True
        assert int(pf.read_text(encoding="utf-8").strip()) == os.getpid()
        pidlock.release(pf)


def test_repair_refuses_when_another_process_holds_new_lock():
    """Simulate: our pid file was unlinked, another daemon started fresh
    and claimed the new inode's flock. repair must return False — we
    mustn't overwrite the new daemon's pid."""
    import fcntl
    with isolated_env():
        pf = paths.router_pid_file()
        assert pidlock.acquire(pf, name="test") is True
        old_fd = pidlock._held_fds.pop(pf)
        # Unlink our file, create a fresh one with someone else's lock
        pf.unlink()
        fd2 = os.open(str(pf), os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(fd2, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(fd2, b"54321")
        # Our old fd still holds the orphaned inode lock → both locks
        # are on *different* inodes so both succeed. But repair should
        # fail because the new inode is already locked.
        pidlock._held_fds[pf] = old_fd  # restore
        assert pidlock.repair_pid_file(pf, name="test") is False
        # Content untouched (still 54321)
        assert pf.read_text(encoding="utf-8").strip() == "54321"
        os.close(fd2)
        pidlock._held_fds.pop(pf, None)
