"""`eduflow watchdog`

Long-running supervisor that keeps the router (and any future daemons)
alive. Runs `runtime.watchdog.supervise` every
`watchdog.check_interval_s` seconds (eduflow.toml; default 30) until
SIGTERM / Ctrl-C.

Self-locks via state_dir/watchdog.pid so two watchdogs can't fight.

Cooldown alerts:
- When a supervised daemon enters cooldown (max_retries respawns
  failed), the watchdog posts to Feishu chat so the boss sees the
  death without tailing the watchdog log.
- The alert is a red Feishu card with a 3-step recovery checklist
  (`eduflow health` / read daemon log / `eduflow down && up`
  after fix). Falls back to plain `send_text` on card schema
  rejection so the alert still lands.
- alert_fn is None when chat_id is unset — alerts are pointless
  without a delivery target; boot banner says "no chat alerts" so
  the operator knows.

Claude OAuth keep-alive:
- Bind-mounted claude .credentials.json expires during idle and
  the in-pane claude only refreshes on API call (not idle), which
  killed boss-message routing after long silences. Watchdog now
  proactively reads `expiresAt` every
  `watchdog.cred_check_interval_s` seconds (default 300); if
  the token's < `watchdog.cred_refresh_ahead_s` (default 1800) from
  expiry, run `claude -p "Return only OK"` once. That triggers
  claude to refresh the token in-place (file is bind-mounted RW so
  the new token persists back to host). All agent panes share the
  same file via per-agent symlink, so one refresh covers the whole
  team.

All alert paths are best-effort: chat send / card send failures are
swallowed at the alert_fn level (and runtime/watchdog's supervise
also try/excepts alert_fn). A broken alert path mustn't kill the
supervisor.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from eduflow.feishu import chat as _chat
from eduflow.feishu.cards import simple_card
from eduflow.runtime import (
    config, context_monitor, lifecycle, paths, pidlock, tmux, tunables,
    watchdog, wake,
)
from eduflow.agents import get_adapter
from eduflow.util import maybe_print_help, read_json, write_json


_CRED_PATH = Path.home() / ".claude" / ".credentials.json"
# Resolves to /root/.claude/.credentials.json in Docker (HOME=/root) — same
# path the host-keychain bind-mount lands on — and to ~/.claude/... on host.
# Hardcoding /root broke host non-root deploys: Path("/root/...").exists()
# raised PermissionError (Linux /root is 700) instead of returning False
# under Python 3.10–3.12, killing `eduflow up`. Caught 2026-05-08.


def _make_alert_fn():
    """Build the alert callable handed to `supervise`. Captures chat_id +
    profile at construction time (cheap reads of runtime_config.json)
    so each cooldown event sends without re-reading config.

    Returns None when chat_id is unset — alerts are pointless without a
    delivery target, and a None alert_fn is the supervise default.

    Sends as a red Feishu card so the cooldown event is visually
    distinct from normal /team / /health cards. Falls back to plain
    text if send_card raises (schema mismatch on older lark builds).
    """
    chat_id = config.chat_id()
    if not chat_id:
        return None
    profile = config.lark_profile()

    def alert(name: str, failed_at: int, cooldown_secs: int) -> None:
        title = f"🚨 watchdog: {name} entered cooldown"
        body = (
            f"daemon **{name}** entered **{cooldown_secs}s cooldown** "
            f"after **{failed_at}** failed respawns.\n\n"
            f"- `eduflow health` for current state\n"
            f"- check daemon log for root cause\n"
            f"- after fix: `eduflow down && eduflow up`"
        )
        from eduflow.runtime import tunables
        alarm_color = str(tunables.tunable("router.alarm_card_color", "red"))
        card = simple_card(title, body, color=alarm_color)
        try:
            _chat.send_card(chat_id, card, profile=profile, as_user=False)
        except Exception as e:
            # Card delivery shouldn't kill the watchdog. Fall back to
            # plain text so the alert still lands somehow; if THAT also
            # fails the supervise outer try/except logs it.
            print(f"  ⚠️ watchdog: card alert send failed ({e}); falling back to text")
            _chat.send_text(chat_id,
                            f"🚨 watchdog: {name} entered {cooldown_secs}s cooldown "
                            f"after {failed_at} failed respawns",
                            profile=profile, as_user=False)

    return alert


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, "usage: eduflow watchdog"):
        return 0
    pid_file = paths.watchdog_pid_file()
    if not pidlock.acquire(pid_file, name="watchdog"):
        return 1
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    specs = watchdog.default_specs()
    states: dict = {}
    alert_fn = _make_alert_fn()
    alert_msg = "with chat alerts" if alert_fn else "no chat alerts (chat_id unset)"
    check_interval_s = int(tunables.tunable("watchdog.check_interval_s", 30))
    cred_check_interval_s = int(tunables.tunable("watchdog.cred_check_interval_s", 300))
    runtime_guard_interval_s = int(tunables.tunable("watchdog.runtime_guard_interval_s", 30))
    print(f"🐕 watchdog supervising {[s.name for s in specs]} every {check_interval_s}s ({alert_msg})")

    last_cred_check = 0.0
    last_runtime_guard = 0.0
    last_pid_repair = 0.0
    pid_repair_interval_s = 300.0  # every 5 min — catch unlinked pid files
    try:
        while True:
            watchdog.supervise(specs, states, alert_fn=alert_fn)
            now = time.time()
            if now - last_cred_check >= cred_check_interval_s:
                _maybe_refresh_claude_oauth(now)
                last_cred_check = now
            if now - last_runtime_guard >= runtime_guard_interval_s:
                _guard_agent_runtimes()
                _maybe_emit_auto_ops_presence(now)
                last_runtime_guard = now
            if now - last_pid_repair >= pid_repair_interval_s:
                pidlock.repair_pid_file(pid_file, name="watchdog")
                last_pid_repair = now
            time.sleep(check_interval_s)
    except KeyboardInterrupt:
        print("watchdog stopped")
        return 0
    finally:
        pidlock.release(pid_file)


_AUTH_FAILURE_MARKERS = (
    "Invalid auth credentials",
    "auth required",
    "Unauthorized",
    "401",
    "/login",
    # Quota / billing / subscription expired — access denied even though
    # credentials are valid. Treat as auth_failure so the runtime guard
    # can switch to a fallback.
    "FORBIDDEN",
    "quota exceeded",
    "billing required",
    "subscription expired",
    "code\":\"112",
)


_PROVIDER_UNAVAILABLE_MARKERS = (
    "provider unavailable",
    "service unavailable",
    "temporarily unavailable",
    "502",
    "503",
    "504",
    "gateway timeout",
    "connection refused",
    # 403 with rate-limit connotation — distinct from auth/quota.
    "403",
)


_CONVERSATION_HISTORY_CORRUPT_MARKERS = (
    "Repetitive tool calls detected",
    "InternalError.Algo.InvalidParameter",
)

_CONTEXT_ACTION_COOLDOWN_S = 600.0


def _guard_state() -> dict:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    return read_json(path, {"agents": {}})


def _write_guard_state(data: dict) -> None:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)


def _update_guard_agent(agent: str, **fields) -> dict:
    """Patch one agent row in runtime guard state and persist it."""
    from eduflow.util import file_lock
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = _guard_state()
        row = data.setdefault("agents", {}).setdefault(agent, {})
        row.update(fields)
        _write_guard_state(data)
    return data


def _auto_ops_presence_state_file() -> Path:
    return paths.state_file("auto-ops-presence.json")


def _auto_ops_presence_state() -> dict:
    return read_json(_auto_ops_presence_state_file(), {})


def _write_auto_ops_presence_state(data: dict) -> None:
    path = _auto_ops_presence_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)


def _latest_auto_ops_surface_s() -> float:
    """Return the latest user-visible auto_ops signal timestamp in seconds."""
    last = float(_auto_ops_presence_state().get("last_sent_at", 0) or 0)
    try:
        from eduflow.store import local_facts
        for row in local_facts.list_logs("auto_ops", limit=50):
            if str(row.get("type") or "") in {"say", "auto_ops_presence"}:
                last = max(last, int(row.get("created_at") or 0) / 1000)
    except Exception:
        pass
    return last


def _presence_agent_summary(agent: str, row: dict | None) -> str:
    if not row:
        return f"{agent} 无状态"
    status = str(row.get("status") or "未知").strip() or "未知"
    task = " ".join(str(row.get("task") or "").split())
    if task.startswith("外显陈旧："):
        return f"{agent} 外显陈旧"
    if status in {"阻塞", "异常"}:
        return f"{agent} {status}"
    if task:
        if len(task) > 24:
            task = task[:24] + "..."
        return f"{agent} {status}（{task}）"
    return f"{agent} {status}"


def _build_auto_ops_presence_message() -> str:
    agents = ["manager", "worker_course", "review_course", "worker_builder", "worker_qbank"]
    try:
        from eduflow.store import local_facts
        rows = {str(r.get("agent") or ""): r for r in local_facts.list_all_statuses()}
    except Exception:
        rows = {}
    parts = [_presence_agent_summary(agent, rows.get(agent)) for agent in agents]
    return "运行态简报：auto_ops 盯盘中；" + "；".join(parts) + "。"


def _maybe_emit_auto_ops_presence(now_s: float | None = None) -> bool:
    """Post a low-noise auto_ops presence signal to the main chat.

    Phase 5 (2026-07-01) 主群体验收敛: the default cadence changed
    from "every 30 min regardless" to "stage-driven + long fallback".

    Behaviour now:
      - `presence_enabled=false` (Phase 5 default) → the fixed-cadence
        card is OFF; auto_ops only surfaces on real stage changes /
        ALERTs (that traffic goes through `say --card`, not here).
      - BUT a long silence is still bad — the boss worries the team
        went dark.  So when `stage_driven=true`, we keep a MUCH longer
        fallback (`presence_fallback_after_s`, default 2h): if nothing
        from auto_ops has hit the main chat for that long, emit one
        short "在岗" heartbeat card.
      - `presence_enabled=true` (legacy) → old 30-min cadence.
    """
    enabled = bool(tunables.tunable("auto_ops.presence_enabled", True))
    stage_driven = bool(tunables.tunable("auto_ops.stage_driven", False))
    if not enabled and not stage_driven:
        return False
    if enabled:
        interval_s = int(tunables.tunable("auto_ops.presence_interval_s", 1800))
    else:
        # Phase 5 stage-driven mode: only the long fallback heartbeat.
        interval_s = int(tunables.tunable("auto_ops.presence_fallback_after_s", 7200))
    if interval_s <= 0:
        return False
    now_s = time.time() if now_s is None else float(now_s)
    last_surface = _latest_auto_ops_surface_s()
    if not enabled and stage_driven and last_surface <= 0:
        # Phase 5 stage-driven mode only: no auto_ops surface has ever
        # been recorded. Don't fire the long fallback immediately on a
        # fresh boot — establish `now` as the baseline so the silence
        # clock starts from here. (Legacy presence_enabled=true keeps
        # its original "fire on first tick" behavior.)
        _write_auto_ops_presence_state({"last_sent_at": now_s, "message": "baseline"})
        return False
    if now_s - last_surface < interval_s:
        return False
    chat_id = config.chat_id()
    if not chat_id:
        return False
    message = _build_auto_ops_presence_message()
    card = simple_card("auto_ops · 运行态值守", message, color="red")
    try:
        _chat.send_card(
            chat_id,
            card,
            profile=config.lark_profile(),
            as_user=False,
        )
    except Exception as e:
        print(f"  ⚠️ auto_ops presence send failed: {e}")
        return False
    try:
        from eduflow.store import local_facts
        local_facts.touch_heartbeat("auto_ops")
        local_facts.upsert_status("auto_ops", "进行中", message)
        local_facts.append_log("auto_ops", "auto_ops_presence", message)
    except Exception as e:
        print(f"  ⚠️ auto_ops presence local record failed: {e}")
    _write_auto_ops_presence_state({"last_sent_at": now_s, "message": message})
    return True


def _notify_runtime_switch(agent: str, from_runtime: str, to_runtime: str, reason: str) -> None:
    mode = str(tunables.tunable(f"runtime_guard.notify.{agent}", "")).strip() or str(
        tunables.tunable("runtime_guard.notify.default", "manager")
    ).strip()
    if mode in {"", "silent", "none"}:
        return
    chat_id = config.chat_id()
    if not chat_id:
        return
    text = (
        f"[runtime-guard] {agent} 已自动切换 runtime："
        f"{from_runtime} -> {to_runtime}，原因：{reason}"
    )
    try:
        _chat.send_text(
            chat_id,
            text,
            profile=config.lark_profile(),
            as_user=False,
        )
    except Exception as e:
        print(f"  ⚠️ runtime-guard notify failed for {agent}: {e}")


def _manager_policy(agent: str) -> str:
    return str(
        tunables.tunable(f"runtime_guard.manager_policy.{agent}", "")
    ).strip() or str(
        tunables.tunable("runtime_guard.manager_policy.default", "continue")
    ).strip()


def _apply_manager_policy(agent: str) -> None:
    """Apply post-switch / post-cooldown manager policy to local status.

    `continue`: keep current workload posture
    `pause`: mark agent paused for manager review
    """
    policy = _manager_policy(agent)
    if policy != "pause":
        return
    try:
        from eduflow.store import local_facts
        local_facts.upsert_status(
            agent,
            "阻塞",
            "runtime guard paused intake",
            blocker="needs_manager_action",
        )
    except Exception as e:
        print(f"  ⚠️ runtime-guard policy apply failed for {agent}: {e}")


def _runtime_guard_limits() -> tuple[int, int]:
    max_switches = int(tunables.tunable("runtime_guard.cooldown.max_switches", 3))
    window_s = int(tunables.tunable("runtime_guard.cooldown.window_s", 600))
    return max_switches, window_s


def _cooldown_secs() -> int:
    return int(tunables.tunable("runtime_guard.cooldown.cooldown_s", 900))


def _record_switch_and_check_cooldown(agent: str, now_s: float) -> tuple[bool, dict]:
    from eduflow.util import file_lock
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = _guard_state()
        agents = data.setdefault("agents", {})
        row = agents.setdefault(agent, {})
        history = [float(x) for x in row.get("switch_times", [])]
        max_switches, window_s = _runtime_guard_limits()
        history = [ts for ts in history if now_s - ts <= window_s]
        history.append(now_s)
        row["switch_times"] = history
        row["last_switch_at"] = now_s
        if len(history) >= max_switches:
            row["cooldown_until"] = now_s + _cooldown_secs()
            row["needs_manager_action"] = True
            row["manager_policy"] = _manager_policy(agent)
            row["escalation_needed"] = True
            row["escalation_reason"] = "repeated_switches_entered_cooldown"
            row["last_alert_level"] = "escalation_repair_in_progress"
            _write_guard_state(data)
            return True, data
        _write_guard_state(data)
    return False, data


def _agent_in_cooldown(agent: str, now_s: float) -> bool:
    data = _guard_state()
    row = data.get("agents", {}).get(agent, {})
    return float(row.get("cooldown_until", 0) or 0) > now_s


def _detect_runtime_failure_reason(target: tmux.Target, adapter) -> str:
    text = tmux.capture_pane(target, lines=120)
    ready_markers = list(adapter.ready_markers())
    ready_at = max((text.rfind(m) for m in ready_markers), default=-1)
    current_text = text[ready_at:] if ready_at >= 0 else text
    if wake.is_rate_limited(target, adapter, capture=lambda *_a, **_kw: current_text):
        return "rate_limit"
    auth_at = max((current_text.rfind(m) for m in _AUTH_FAILURE_MARKERS), default=-1)
    if auth_at >= 0:
        return "auth_failure"
    low = current_text.lower()
    corrupt_at = max((low.rfind(m.lower()) for m in _CONVERSATION_HISTORY_CORRUPT_MARKERS), default=-1)
    if corrupt_at >= 0:
        return "conversation_history_corrupt"
    provider_at = max((low.rfind(m.lower()) for m in _PROVIDER_UNAVAILABLE_MARKERS), default=-1)
    if provider_at >= 0:
        return "provider_unavailable"
    return ""


def _maybe_recover_context_pressure(agent: str, target: tmux.Target,
                                    adapter, resolved: dict,
                                    now_s: float) -> bool:
    """Act on pane context pressure before normal runtime failover.

    At 90-99% the CLI is still usually healthy enough to accept a real
    `/compact`, so run the existing command in a background child and let that
    command handle post-compact reidentify. At 100% / hard limit markers,
    compact is often rejected or too late; respawn the same runtime instead.

    Returns True when this guard already took an action for this tick.
    """
    text = tmux.capture_pane(target, lines=120)
    signal = context_monitor.detect_context_usage(text)
    if not signal:
        return False

    row = _guard_state().get("agents", {}).get(agent, {})
    last_action_at = float(row.get("last_context_action_at", 0) or 0)
    if now_s - last_action_at < _CONTEXT_ACTION_COOLDOWN_S:
        return True

    current = (
        lifecycle.current_runtime_status(agent).get("runtime")
        or resolved.get("selected_runtime")
        or "inline"
    )
    if signal.exhausted:
        outcome = lifecycle.restart_with_runtime(
            agent, target, str(current),
            reason=f"context_exhausted:{signal.marker}",
            prove_ready=True,
        )
        _update_guard_agent(
            agent,
            last_context_action="restart",
            last_context_action_at=now_s,
            last_context_signal=signal.marker,
            last_context_outcome=outcome,
        )
        print(f"  🔄 context-guard: {agent} restarted at {signal.marker} "
              f"(outcome={outcome})")
        return True

    if signal.compact_recommended:
        env = dict(os.environ)
        src_path = str(Path.cwd() / "src")
        old_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_path}:{old_pythonpath}" if old_pythonpath else src_path
        )
        try:
            subprocess.Popen(
                [sys.executable, "-m", "eduflow.cli", "compact", agent],
                cwd=str(Path.cwd()),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            outcome = "compact_started"
        except OSError as e:
            outcome = f"compact_spawn_failed:{e}"
        _update_guard_agent(
            agent,
            last_context_action="compact",
            last_context_action_at=now_s,
            last_context_signal=signal.marker,
            last_context_outcome=outcome,
        )
        print(f"  🧹 context-guard: {agent} {outcome} at {signal.marker}")
        return True

    if signal.warning:
        _update_guard_agent(
            agent,
            last_context_warning_at=now_s,
            last_context_signal=signal.marker,
        )
    return False


def _failback_tunables() -> dict:
    return {
        "min_fallback_s": float(tunables.tunable("runtime_guard.failback.min_fallback_s", 300)),
        "min_healthy_streak": int(tunables.tunable("runtime_guard.failback.min_healthy_streak", 3)),
        "probe_interval_s": float(tunables.tunable("runtime_guard.failback.probe_interval_s", 30)),
        "rate_limit_reasons": set(tunables.tunable(
            "runtime_guard.failback.rate_limit_reasons",
            ["rate_limit", "429", "token_plan_exhausted"],
        )),
        "rate_limit_min_healthy_streak": int(tunables.tunable(
            "runtime_guard.failback.rate_limit_min_healthy_streak", 5
        )),
        "rate_limit_min_fallback_s": float(tunables.tunable(
            "runtime_guard.failback.rate_limit_min_fallback_s", 900
        )),
        "rate_limit_require_real_smoke": bool(tunables.tunable(
            "runtime_guard.failback.rate_limit_require_real_smoke", True
        )),
    }


def _maybe_failback(agent: str, target, current: str, primary: str,
                    now_s: float) -> None:
    """Probe whether the primary runtime has recovered and, if so, canary-
    switch the agent back.

    Uses a streak counter: the primary must pass `api_smoke_runtime` at
    least `min_healthy_streak` times (default 3, interval `probe_interval_s`
    default 30s) AND the agent must have been on fallback for at least
    `min_fallback_s` (default 300s) before the canary switch is attempted.

    If the original failure reason was rate-limit / token-plan exhaustion,
    the required streak and fallback duration are raised to
    `rate_limit_min_healthy_streak` (default 5) and
    `rate_limit_min_fallback_s` (default 900s), and a real "ok" smoke is
    required ("skipped" does not count).

    The canary switch uses `lifecycle.restart_with_runtime` with
    `prove_ready=True` (same safety as failover).  On success the failback
    state is cleared; on failure the streak resets and we wait for the next
    guard tick.  Other agents are NOT switched immediately — the next guard
    tick handles them (natural staggering).
    """
    from eduflow.runtime import verify
    t = _failback_tunables()
    probe_interval_s = t["probe_interval_s"]

    data = _guard_state()
    fb = data.get("agents", {}).get(agent, {}).get("failback", {})
    last_probe = float(fb.get("last_primary_smoke_at", 0) or 0)
    if now_s - last_probe < probe_interval_s:
        return  # too soon to probe again

    resolved = config.resolved_agent_config(agent)
    chain = resolved.get("runtime_chain", [])
    if not chain:
        return
    primary_name = str(chain[0].get("name", "inline"))
    if current == primary_name:
        return  # already on primary; nothing to do

    # Build a resolved-like dict for the primary runtime's smoke test.
    primary_rt = chain[0]
    primary_resolved = dict(resolved)
    primary_resolved.update({
        "selected_runtime": primary_name,
        "cli": primary_rt.get("cli", resolved.get("cli", "claude-code")),
        "model": primary_rt.get("model", resolved.get("model", "opus")),
        "provider": primary_rt.get("provider", ""),
        "env_profile": primary_rt.get("env_profile", ""),
    })

    verdict, _detail = verify.api_smoke_runtime(primary_resolved)

    # Be conservative when the original failure was rate-limit / token-plan
    # related: small 1-token smoke probes may pass while real requests still
    # hit 429, so we require a longer streak and a real "ok" smoke.
    primary_failure_reason = str(fb.get("primary_failure_reason") or "")
    is_rate_limit = primary_failure_reason in t["rate_limit_reasons"]
    if is_rate_limit and t["rate_limit_require_real_smoke"]:
        healthy = verdict == "ok"
    else:
        healthy = verdict in {"ok", "skipped"}

    required_streak = t["rate_limit_min_healthy_streak"] if is_rate_limit else t["min_healthy_streak"]
    required_fallback_s = t["rate_limit_min_fallback_s"] if is_rate_limit else t["min_fallback_s"]

    streak = int(fb.get("primary_healthy_streak", 0) or 0)
    in_fallback_since = float(fb.get("in_fallback_since", 0) or 0)
    if healthy:
        streak += 1
    else:
        streak = 0

    _update_guard_agent(
        agent,
        failback={
            "primary_runtime": primary_name,
            "primary_failure_reason": primary_failure_reason,
            "primary_healthy_streak": streak,
            "last_primary_smoke_at": now_s,
            "in_fallback_since": in_fallback_since,
        },
    )

    if not healthy:
        return

    if streak < required_streak:
        return
    if in_fallback_since and (now_s - in_fallback_since) < required_fallback_s:
        return

    # ── Canary failback: switch agent back to primary ──────────────
    outcome = lifecycle.restart_with_runtime(
        agent, target, primary_name,
        reason="failback", prove_ready=True,
    )
    if outcome in {lifecycle.READY, lifecycle.READY_NO_INIT}:
        _update_guard_agent(
            agent,
            failback={},  # clear failback state
            from_runtime=str(current),
            to_runtime=primary_name,
            last_switch_reason="failback",
            last_switch_outcome=outcome,
            last_switch_at=now_s,
        )
        verify.record_switch_event(**{
            "ts": now_s,
            "agent": agent,
            "from_runtime": str(current),
            "to_runtime": primary_name,
            "reason": "failback",
            "outcome": outcome,
            "trigger": "watchdog",
        })
        _notify_runtime_switch(
            agent, str(current), primary_name,
            f"failback (primary recovered, streak={streak})",
        )
        print(f"  🔀 agent-runtime-guard failback: {agent} switched "
              f"{current} -> {primary_name} (streak={streak})")
    else:
        # Canary failed — reset streak, wait for next tick.
        _update_guard_agent(
            agent,
            failback={
                "primary_runtime": primary_name,
                "primary_healthy_streak": 0,
                "last_primary_smoke_at": now_s,
                "in_fallback_since": in_fallback_since,
            },
        )
        verify.record_switch_event(**{
            "ts": now_s,
            "agent": agent,
            "from_runtime": str(current),
            "to_runtime": primary_name,
            "reason": "failback",
            "outcome": outcome,
            "trigger": "watchdog",
        })
        print(f"  ⚠️ agent-runtime-guard failback: {agent} canary "
              f"{current} -> {primary_name} failed (outcome={outcome})")


def _guard_agent_runtimes() -> None:
    """Best-effort runtime guard for agent panes.

    This sits above daemon supervision: the process can be alive while the
    current provider/runtime is effectively dead. In that case we run
    `runtime.failover.execute_fallback_loop` which:
      1. picks the next cross-pool fallback (when possible),
      2. hard-switches the pane via lifecycle.restart_with_runtime with
         prove_ready=True (live env + API smoke + pane-text checks),
      3. records one switch event per attempt to runtime-switch-events.jsonl,
      4. retries up to 3 times before marking the agent escalated.
    """
    from eduflow.runtime import failover
    team = config.load_team()
    session = team.get("session", "EduFlow")
    if not tmux.has_session(session):
        return
    for agent in sorted(team.get("agents", {})):
        now_s = time.time()
        if _agent_in_cooldown(agent, now_s):
            continue
        target = tmux.Target(session, agent)
        if not tmux.has_window(target):
            continue
        resolved = config.resolved_agent_config(agent)
        cli = resolved.get("cli", "claude-code")
        try:
            adapter = get_adapter(cli)
        except KeyError:
            continue
        if _maybe_recover_context_pressure(agent, target, adapter, resolved, now_s):
            continue
        reason = _detect_runtime_failure_reason(target, adapter)
        if not reason:
            # No failure on current runtime — check if agent is on
            # fallback and primary might have recovered.
            chain = resolved.get("runtime_chain", [])
            primary_name = str(chain[0].get("name", "inline")) if chain else "inline"
            current = lifecycle.current_runtime_status(agent).get("runtime") or resolved.get("selected_runtime", "inline")
            if str(current) != primary_name:
                _maybe_failback(agent, target, str(current), primary_name, now_s)
            continue
        current = lifecycle.current_runtime_status(agent).get("runtime") or resolved.get("selected_runtime", "inline")
        _update_guard_agent(
            agent,
            last_failure_reason=reason,
            last_runtime=current,
            last_checked_at=now_s,
        )
        result = failover.execute_fallback_loop(
            agent,
            target,
            str(current),
            reason,
            trigger="watchdog",
        )
        outcome = result["outcome"]
        to_runtime = result["to_runtime"]
        attempts = len(result["attempts"])
        best = result["best_outcome"]
        pool_switched = result["pool_switched"]
        exhausted = result["exhausted"]
        _update_guard_agent(
            agent,
            from_runtime=str(current),
            to_runtime=str(to_runtime),
            last_switch_reason=reason,
            last_switch_outcome=outcome,
            last_best_outcome=best,
            last_attempts=attempts,
            last_pool_switched=pool_switched,
        )
        if outcome == lifecycle.READY:
            hit_cooldown, _ = _record_switch_and_check_cooldown(agent, now_s)
            _notify_runtime_switch(agent, str(current), str(to_runtime),
                                   f"{reason} (best={best}, attempts={attempts}, cross_pool={pool_switched})")
            # Record failback state so the guard can probe the original
            # primary for recovery.  Preserve existing in_fallback_since
            # if the agent was already on a fallback chain.
            existing_fb = _guard_state().get("agents", {}).get(agent, {}).get("failback", {})
            _update_guard_agent(
                agent,
                escalation_needed=False,
                escalation_reason="",
                last_alert_level="auto_switched_recovered",
                failback={
                    "primary_runtime": str(current),
                    "primary_failure_reason": reason,
                    "primary_healthy_streak": 0,
                    "last_primary_smoke_at": 0.0,
                    "in_fallback_since": existing_fb.get("in_fallback_since") or now_s,
                },
            )
            print(f"  🔀 agent-runtime-guard: {agent} switched {current} -> {to_runtime} "
                  f"({reason}, attempts={attempts}, cross_pool={pool_switched})")
            if hit_cooldown:
                _apply_manager_policy(agent)
                print(f"  ⛔ agent-runtime-guard: {agent} entered cooldown after repeated runtime switches")
        elif exhausted:
            _update_guard_agent(
                agent,
                needs_manager_action=True,
                escalation_needed=True,
                escalation_reason="fallback_chain_exhausted",
                last_alert_level="escalation_repair_in_progress",
            )
            print(f"  ⏸ agent-runtime-guard: {agent} hit {reason} but all fallback runtimes failed "
                  f"(best={best}, attempts={attempts})")
        else:
            # Non-READY but not exhausted — one of the intermediate
            # outcomes (env_drift, smoke_failed, ready_unproven). Still
            # counts as a switch for cooldown purposes.
            hit_cooldown, _ = _record_switch_and_check_cooldown(agent, now_s)
            _update_guard_agent(
                agent,
                needs_manager_action=True,
                escalation_needed=True,
                escalation_reason=f"switch_unverified:{outcome}",
                last_alert_level="escalation_repair_in_progress",
            )
            print(f"  ⚠️ agent-runtime-guard: {agent} switched {current} -> {to_runtime} "
                  f"but outcome={outcome} (best={best}); needs repair")
            if hit_cooldown:
                _apply_manager_policy(agent)


def _maybe_refresh_claude_oauth(now: float) -> None:
    """If the bind-mounted claude .credentials.json expires within
    `watchdog.cred_refresh_ahead_s` (eduflow.toml; default 1800),
    force-refresh by spawning a brief `claude -p "Return only OK"`.
    That subprocess hits the Anthropic API which makes claude rotate
    the access token in-place. File is bind-mounted RW so the new
    token persists to host.

    Best-effort: any failure (file missing, parse error, claude crashes,
    network down) logs a warning but doesn't kill the watchdog. Worst
    case the boss still sees expired-token errors next cycle and runs
    `make creds` manually.
    """
    if not _CRED_PATH.exists():
        # Host deploy (macOS): no /root mount, claude OAuth lives in
        # keychain not file. Silent skip — printing every 5min spams
        # watchdog.log with hundreds of false alarms.
        return
    try:
        oauth = json.loads(_CRED_PATH.read_text())["claudeAiOauth"]
        expires_ms = int(oauth.get("expiresAt", 0))
    except (OSError, ValueError, KeyError) as e:
        print(f"  ⚠️ cred-refresh: read {_CRED_PATH} failed: {e}")
        return
    remaining = expires_ms / 1000 - now
    cred_refresh_ahead_s = int(tunables.tunable("watchdog.cred_refresh_ahead_s", 1800))
    if remaining > cred_refresh_ahead_s:
        return  # plenty of time; skip
    print(f"  🔑 claude token expires in {int(remaining)}s — forcing refresh")
    try:
        r = subprocess.run(
            ["claude", "-p", "Return only OK"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"  ⚠️ cred-refresh: `claude -p` failed: {e}")
        return
    if r.returncode != 0:
        snippet = (r.stderr or r.stdout or "").strip()[:120]
        print(f"  ⚠️ cred-refresh: claude rc={r.returncode}: {snippet}")
        return
    print("  ✅ claude token refreshed")
