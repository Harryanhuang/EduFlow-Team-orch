"""`eduflow router`

Long-running event subscriber: spawns `lark-cli event +subscribe`
(direct binary preferred, npx fallback — see
`feishu/lark.resolve_cli_prefix`) and feeds each NDJSON line into
the routing loop (`feishu/subscribe.process_lines`).

Boot order:
  1. Validate chat_id + agents (fast-fail BEFORE pidlock so up.py
     can detect "no pid written" and surface the boot error).
  2. Acquire `state_dir/router.pid` via pidlock so two routers
     can't fight.
  3. Replay `pending_lines(chat_id)` to backfill anything received
     while the daemon was down (catchup-on-restart cursor).
  4. Spawn the subscribe subprocess in its own session (so
     SIGTERMing the daemon kills the entire npx → node → lark-cli
     tree via killpg).
  5. Spawn a daemon thread that polls the subscribe child's exit
     code every ~20s and self-SIGTERMs when it dies (lark-cli
     occasionally exits silently while npm-exec parent keeps
     stdout open, blocking readline forever).
  6. Drive `process_lines` over the subscribe stdout iterator.

Stops on:
  - Ctrl-C → SIGINT
  - SIGTERM → handler reaps subscribe group, releases pidlock, exit 0
  - subscribe child dies → watchdog thread SIGTERMs us; same cleanup.

Writes pid to `state_dir/router.pid` so `runtime.watchdog.is_alive`
can supervise. Watchdog separately reaps orphan `+subscribe`
processes left by a SIGKILL'd predecessor before respawning.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from typing import Callable

from eduflow.feishu import catchup, lark
from eduflow.feishu.deliver import apply as _deliver_apply
from eduflow.feishu.subscribe import process_lines
from eduflow.runtime import config, paths, pidlock, tunables, wake
from eduflow.util import error_exit, maybe_print_help, warn


def _build_subscribe_cmd(profile: str, *,
                         resolve_prefix=lark.resolve_cli_prefix) -> list[str]:
    """Build the lark-cli `event +subscribe` argv.

    Prefix comes from `lark.resolve_cli_prefix` (direct binary first,
    `npx @larksuite/cli` fallback). Tests inject `resolve_prefix=`
    so the argv shape is deterministic regardless of what's
    installed locally.

    Note on --force: previously included to bypass the single-instance
    lock from a possibly-zombie previous daemon. lark-cli 1.0.21+ docs
    that flag explicitly: "UNSAFE: server randomly splits events across
    connections, each instance only receives a subset". Removing it
    means events flow to one connection (ours); the lock file at
    ~/.lark-cli/locks/subscribe_<app_id>.lock is fcntl-advisory, so it
    auto-releases on process exit. eduflow's own pidlock + the
    watchdog respawn keep us at one daemon at a time, so the
    single-instance lock is harmless.
    """
    return [
        *resolve_prefix(),
        *(["--profile", profile] if profile else []),
        "event", "+subscribe",
        "--event-types", "im.message.receive_v1",
        "--compact", "--quiet",
        "--as", "bot",
    ]


def _build_agent_adapters(agents_dict: dict) -> dict:
    """Resolve every team-known agent to its CliAdapter once.

    Pre-building this map keeps `_inject_to_pane`'s per-target adapter
    lookup disk-read-free for cached agents. Adapters whose `cli`
    value is bogus get skipped (no entry); the apply call falls back
    to the config-driven lookup which surfaces the KeyError as a
    per-agent warning instead of a build-time abort.
    """
    from eduflow.agents import get_adapter
    adapters: dict = {}
    for name, cfg in agents_dict.items():
        cli = cfg.get("cli", "claude-code")
        try:
            adapters[name] = get_adapter(cli)
        except KeyError:
            continue
    return adapters


def _make_apply_with_wake(*, session: str, chat_id: str, profile: str,
                          team_agents: list[str], agent_adapters: dict,
                          lazy_agents: frozenset):
    """Build the per-event deliver wrapper with hot-path config pre-bound.

    chat_id / lark_profile / session are deployment-stable; binding
    them in a closure here saves 2-4 disk reads per inbound message
    compared to letting `deliver.apply` re-resolve via `config.<getter>()`
    each time. The pre-built `agent → CliAdapter` map plays the same
    role for `_inject_to_pane` — unknown agents (not in the cached
    map) fall back to a config-driven lookup so a typo surfaces as a
    per-agent warning instead of dropping the whole event.

    Operator edits to `chat_id` need a `eduflow down + up` to take
    effect (subscribe is bound to the startup chat_id, pidlock
    prevents a parallel daemon). Per-agent fields like `lazy` /
    `card_color` / `specialty` ARE live-readable through other code
    paths (slash handlers via `_live_agents()`, identity via
    `eduflow reidentify`).
    """
    def lookup_adapter(agent: str):
        cached = agent_adapters.get(agent)
        if cached is not None:
            return cached
        from eduflow.agents import adapter_for_agent
        return adapter_for_agent(agent)

    def _apply_with_wake(decision):
        return _deliver_apply(decision, wake_fn=wake.wake_if_dormant,
                              session=session, chat_id=chat_id,
                              profile=profile, team_agents=team_agents,
                              lazy_agents=lazy_agents,
                              adapter_for_agent=lookup_adapter)
    return _apply_with_wake


def _terminate_subscribe_group(proc: subprocess.Popen) -> None:
    """Kill the entire subscribe process group (npx + node + lark-cli).

    Round 7 D2: router's plain proc.terminate() only signaled npx; the
    lark-cli grandchild lived on as an orphan after each up/down cycle.
    Putting the subprocess in its own session (start_new_session=True at
    Popen time) means we can take the whole group out with one killpg.
    """
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def _load_seen_msg_ids() -> set[str]:
    """Load persisted dedup set from disk, truncating to
    `router.seen_max_lines` (eduflow.toml; default 5000) to bound the
    file. Returns empty set if missing or unreadable — best-effort,
    never fails the daemon."""
    path = paths.router_seen_file()
    try:
        if not path.exists():
            return set()
        with path.open("r", encoding="utf-8") as f:
            ids = [line.strip() for line in f if line.strip()]
    except OSError:
        return set()
    seen_max = int(tunables.tunable("router.seen_max_lines", 5000))
    if len(ids) > seen_max:
        # Truncate file in place so it doesn't grow unbounded.
        try:
            kept = ids[-seen_max:]
            path.write_text("\n".join(kept) + "\n", encoding="utf-8")
            ids = kept
        except OSError:
            pass
    return set(ids)


def _make_on_progress(last_event_at: list[float]) -> Callable:
    """Build the on_progress callback bound to a mutable timestamp slot.

    Every successfully handled (non-DROP) event:
    - refreshes `last_event_at[0]` so the subscribe-watchdog thread can
      detect "lark-cli subprocess alive but events stopped flowing" —
      the silent-failure mode that bouncing the router fixes.
    - appends the message_id to `state/router.seen` so the dedup set
      survives across process restarts. Without this, router self-
      restarts (driven by stale-detect or watchdog) re-apply messages
      that catchup re-fetches because seen_msg_ids was an in-memory
      set (host_smoke 2026-05-06: /tmux manager card forwarded into
      manager inbox every ~3.5min on every restart cycle).
    """
    def _on_progress(decision, stats):
        catchup.record_decision(decision)
        last_event_at[0] = time.monotonic()
        msg_id = getattr(decision, "msg_id", "")
        if msg_id:
            try:
                seen_path = paths.router_seen_file()
                seen_path.parent.mkdir(parents=True, exist_ok=True)
                with seen_path.open("a", encoding="utf-8") as f:
                    f.write(msg_id + "\n")
            except OSError:
                pass  # best-effort; in-memory set still dedups in this run
    return _on_progress


def _platform_default_stale_event_threshold_s() -> float:
    """Default stale-event threshold split by platform — root cause
    of the previous 180/600 churn was platform-specific WebSocket
    behaviour, not a single-knob tuning problem.

    macOS (Darwin) → 120s. lark-cli 1.0.23 WebSocket subscribe silently
    drops on macOS without reconnecting (verified 2026-05-09 host smoke:
    subscribe child stayed alive but stopped delivering events; only
    self-SIGTERM + watchdog respawn + catchup recovers). A tighter
    threshold lets recovery happen in ~2 min instead of ~10. Quiet-chat
    overhead is acceptable on a dev laptop.

    Linux (and everything else) → 600s. WebSocket is stable here; quiet
    chats shouldn't churn through respawns. History on this platform:
    1200s → too lax (2026-05-06 caught manager not seeing user msg for
    7+ min); 180s → too tight (2026-05-07 fresh-user smoke caught a
    genuinely quiet chat respawning every ~3 min, churning router.log
    into a wall of "no events for 180s; respawning"). 600s is the
    calibrated middle.
    """
    import platform
    return 120.0 if platform.system() == "Darwin" else 600.0


def _stale_event_threshold_s() -> float:
    """Max seconds router will tolerate with no inbound event before
    self-SIGTERM'ing for a watchdog respawn.

    Resolved via runtime.tunables — priority env > eduflow.toml >
    platform-aware default (see `_platform_default_stale_event_threshold_s`).
    Legacy `EDUFLOW_ROUTER_STALE_S` env (without `_EVENT_THRESHOLD`) is
    still honored as a backwards-compat alias since it shipped first.

    Per-process ±jitter is applied once at module import so multiple
    router instances don't all expire on the same wall-clock tick
    (which previously caused 'thundering herd' respawn storms on quiet
    chats). Set `router.stale_event_threshold_jitter_pct = 0` in
    eduflow.toml to disable for testing.
    """
    # Legacy env-var alias (shipped before the tunables framework).
    legacy = os.environ.get("EDUFLOW_ROUTER_STALE_S", "").strip()
    if legacy:
        try:
            v = float(legacy)
            if v >= 60:
                return v
        except ValueError:
            pass
    configured = float(tunables.tunable(
        "router.stale_event_threshold_s",
        _platform_default_stale_event_threshold_s()))
    if configured < 60:
        configured = _platform_default_stale_event_threshold_s()
    return _jittered_threshold(configured)


# Cache the jittered threshold per process so it stays stable for the
# whole router lifetime (rather than flapping on every poll). Without
# this, two router instances reading the same toml value would both
# pick independent jitters — fine in theory, but if any caller does
# `if idle > threshold` in a tight loop, jitter noise makes the value
# flapping enough to matter for tests.
_JITTER_CACHE: dict[float, float] = {}


def _jittered_threshold(base: float) -> float:
    """Apply ±jitter_pct to `base` once per process. Range is
    [base * (1 - pct), base * (1 + pct)]."""
    jitter_pct = float(tunables.tunable(
        "router.stale_event_threshold_jitter_pct", 0.10))  # ±10% default
    if jitter_pct <= 0:
        return base
    if base in _JITTER_CACHE:
        return _JITTER_CACHE[base]
    import random as _random
    factor = 1.0 + _random.uniform(-jitter_pct, jitter_pct)
    jittered = base * factor
    _JITTER_CACHE[base] = jittered
    return jittered


def _write_stall_reason(reason: str, detail: str = "") -> None:
    """Persist why the router is about to self-SIGTERM.

    Writes a small JSON file to `state_dir/router.stall_reason` so the
    watchdog / health command can report the actual cause of the last
    router death instead of just "process not alive".  The file is
    cleared on successful startup by `main()`.
    """
    import json as _json
    path = paths.router_stall_reason_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"reason": reason, "detail": detail,
                   "ts": time.time()}
        path.write_text(_json.dumps(payload), encoding="utf-8")
    except OSError:
        pass  # best-effort; health degrades gracefully if missing


def _watch_subscribe_health(proc: subprocess.Popen, stop_event: threading.Event,
                            last_event_at: list[float]) -> None:
    """Background thread: kill the daemon if the subscribe child dies OR
    stops delivering events.

    Two failure modes covered:

    (a) `lark-cli event +subscribe` exits silently — the lark-cli
        grandchild can vanish while npm-exec parent stays running.
        With npm-exec still holding stdout open, the main thread's
        `process_lines(proc.stdout, ...)` would block forever on
        readline, never noticing.

    (b) `lark-cli` subprocess stays alive but the WebSocket silently
        stops delivering events.
        proc.poll() is None, the npm tree looks healthy in `ps`, but
        no inbound events reach process_lines for hours. Detected by
        comparing `last_event_at[0]` to wall-clock; threshold from
        `EDUFLOW_ROUTER_STALE_S` env or 1200s default.

    Both modes terminate via SIGTERM-to-self so the registered handler
    reaps the subscribe group cleanly. Watchdog respawns from there.
    """
    threshold = _stale_event_threshold_s()
    # Short enough to detect a silent subscribe death in <30s, long
    # enough not to busy-loop. Toml-overridable via
    # router.subscribe_watchdog_period_s.
    period_s = float(tunables.tunable("router.subscribe_watchdog_period_s", 20.0))
    while not stop_event.wait(period_s):
        if proc.poll() is not None:
            _write_stall_reason("subscribe_child_exited",
                                f"rc={proc.returncode}")
            print(f"  ⚠️ subscribe child exited (rc={proc.returncode}); router will exit so watchdog can respawn")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        idle = time.monotonic() - last_event_at[0]
        if idle > threshold:
            _write_stall_reason("subscribe_idle",
                                f"idle={idle:.0f}s threshold={threshold:.0f}s")
            print(f"  ⚠️ no events for {idle:.0f}s (threshold {threshold:.0f}s); subscribe likely silently stalled, exiting for respawn")
            os.kill(os.getpid(), signal.SIGTERM)
            return


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, "usage: eduflow router"):
        return 0

    chat = config.chat_id()
    if not chat:
        return error_exit("❌ chat_id not set in runtime_config.json")

    agents = config.agent_names()
    if not agents:
        return error_exit("❌ team.json has no agents")

    pid_file = paths.router_pid_file()
    if not pidlock.acquire(pid_file, name="router"):
        return 1

    # Clear last stall reason — router is alive and well.
    try:
        paths.router_stall_reason_file().unlink(missing_ok=True)
    except OSError:
        pass

    profile = config.lark_profile()
    cmd = _build_subscribe_cmd(profile)
    print(f"🚀 router subscribing on chat {chat} (profile={profile or '<default>'})")

    try:
        # Two precautions on the subscribe child:
        # - env=lark.subprocess_env() strips HTTPS_PROXY under LARK_CLI_NO_PROXY=1
        #   (round 6 D-class bug — lark-cli long-poll dies behind a proxy).
        # - start_new_session=True puts the npx → node → lark-cli chain in its
        #   own process group so SIGTERMing the router can kill the whole tree
        #   in one killpg call (round 7 D2 — orphaned grandchildren).
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line-buffered
            env=lark.subprocess_env(),
            start_new_session=True,
        )
    except FileNotFoundError:
        pidlock.release(pid_file)
        return error_exit("❌ npx / lark-cli not found in PATH")

    # Now that proc exists, install a SIGTERM handler that reaps the
    # subscribe group before exiting. (Plain sys.exit propagates SystemExit
    # past the except blocks, never running proc.terminate.)
    def _on_sigterm(*_):
        _terminate_subscribe_group(proc)
        sys.exit(0)
    signal.signal(signal.SIGTERM, _on_sigterm)

    # Spawn the subscribe-health watchdog thread. It exits the daemon
    # cleanly if lark-cli dies under us — without it, process_lines would
    # block forever on stdout that npm-exec parent keeps open after the
    # lark-cli grandchild vanishes. Also self-terminates if events stop
    # flowing for too long (silent-subscribe-stall mode).
    stop_watchdog = threading.Event()
    last_event_at = [time.monotonic()]
    threading.Thread(
        target=_watch_subscribe_health,
        args=(proc, stop_watchdog, last_event_at),
        daemon=True,
    ).start()

    try:
        if proc.stdout is None:
            return error_exit("❌ lark-cli started without stdout pipe")

        # Bind deployment-stable config values into apply_fn at daemon
        # startup so deliver.apply doesn't re-resolve them on every
        # inbound event (saves 1-4 disk reads per message). The
        # agent→adapter map plays the same role for the inject path.
        # `lazy_agents` is still pre-computed and threaded into
        # SlashContext for back-compat, but slash handlers now use
        # `_live_agents()` themselves so config edits are live.
        team_data = config.load_team()
        agents_dict = team_data.get("agents", {})
        apply_fn = _make_apply_with_wake(
            session=team_data.get("session", "EduFlow"),
            chat_id=chat,
            profile=profile,
            team_agents=agents,
            agent_adapters=_build_agent_adapters(agents_dict),
            lazy_agents=frozenset(name for name, cfg in agents_dict.items()
                                  if cfg.get("lazy")),
        )

        # Persisted dedup set — survives daemon restarts so catchup
        # replay after stale-detect / watchdog respawn doesn't re-apply
        # already-handled messages (host_smoke 2026-05-06 caught it).
        seen = _load_seen_msg_ids()

        def _bump_subscribe_alive():
            last_event_at[0] = time.monotonic()

        loop_kwargs = dict(
            team_agents=agents,
            chat_id=chat,
            default_target="manager",
            apply_fn=apply_fn,
            on_progress=_make_on_progress(last_event_at),
            on_line_received=_bump_subscribe_alive,
            seen_msg_ids=seen,
        )

        # Catchup: replay anything newer than the cursor before going live
        try:
            pending = catchup.pending_lines(chat, profile=profile)
        except Exception as e:
            warn(f"⚠️  catchup fetch failed: {e}")
            pending = []
        if pending:
            print(f"📥 catching up {len(pending)} missed message(s)")
            process_lines(iter(pending), **loop_kwargs)

        _subscribe_start = time.monotonic()
        stats = process_lines(proc.stdout, **loop_kwargs)
        rc = proc.wait()

        # Subscribe-child quick-death retry: if lark-cli exited within
        # 15s of spawn with zero handled events, it's likely a transient
        # lock race from a stale-event restart.  Sleep briefly for the
        # lock file to auto-release, then spawn ONE retry child.
        # The watchdog flap-guard (watchdog.py) is the outer safety net;
        # this retry is the fast-path that avoids a full respawn cycle.
        _subscribe_alive_secs = time.monotonic() - _subscribe_start
        if (rc != 0
                and stats.handled == 0
                and _subscribe_alive_secs < 15):
            print(f"  ⚠️ subscribe child exited rc={rc} in "
                  f"{_subscribe_alive_secs:.1f}s with 0 handled; "
                  f"retrying once after 5s settle")
            _terminate_subscribe_group(proc)
            time.sleep(5)
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=lark.subprocess_env(),
                    start_new_session=True,
                )
            except FileNotFoundError:
                return error_exit("❌ npx / lark-cli not found on retry")
            # Re-install SIGTERM handler for new proc
            def _on_sigterm_retry(*_):
                _terminate_subscribe_group(proc)
                sys.exit(0)
            signal.signal(signal.SIGTERM, _on_sigterm_retry)
            # Re-start watchdog thread for new proc
            stop_watchdog.set()
            stop_watchdog = threading.Event()
            last_event_at[0] = time.monotonic()
            threading.Thread(
                target=_watch_subscribe_health,
                args=(proc, stop_watchdog, last_event_at),
                daemon=True,
            ).start()
            if proc.stdout is not None:
                stats = process_lines(proc.stdout, **loop_kwargs)
            rc = proc.wait()

        print(f"router exited: handled={stats.handled} dropped={stats.dropped}")
        return 0 if rc == 0 else 1
    except KeyboardInterrupt:
        print("router stopped (Ctrl-C)")
        return 0
    finally:
        # Reap the subscribe tree on EVERY exit path so we don't leak a
        # node + lark-cli pair per up/down cycle.
        stop_watchdog.set()
        _terminate_subscribe_group(proc)
        pidlock.release(pid_file)
