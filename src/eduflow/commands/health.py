"""`eduflow health` — one-shot deployment-state check.

Reports, with green/red glyphs, the things that have to be true for
this team to actually deliver messages:

  - state_dir resolved (and from where: env vs default)
  - team.json + runtime_config.json present, with chat_id set
  - tmux session alive
  - per-agent: pane exists? CLI shows a ready marker?
  - router/watchdog: pid file present? process alive? cmdline matches?
  - router cursor: present? last-seen message id

Exit code: 0 if everything green, 1 if any red. Yellow (warning) does
not fail the check.
"""
from __future__ import annotations

import os
import re
import shutil
import time
from dataclasses import dataclass, field

from eduflow.agents import get_adapter
from eduflow.feishu import catchup
from eduflow.runtime import (
    config, context_monitor, paths, pidlock, tmux, tunables,
    verify as _verify_mod, wake, watchdog,
)
from eduflow.store import local_facts
from eduflow.store import scheduled_tasks
from eduflow.util import (
    ago_ms, env_str, maybe_print_help, pop_bool_flag, print_json, reject_extra_args,
)


_OK = "✅"
_BAD = "❌"
_WARN = "⚠️ "
_INFO = "ℹ️ "
# Profile-env key set is owned by runtime.verify (single source of truth);
# health only re-exports the name for the drift check. Keeping one list
# stops health and verify from drifting apart (earlier revision had 7 keys
# here vs verify's 10, silently missing ANTHROPIC_REASONING_MODEL etc.).
_PROFILE_ENV_KEYS = _verify_mod.PROFILE_ENV_KEYS
_CODEX_IDLE_STATUS_RE = re.compile(
    r"\b(?:gpt-\d\S*|o1\S*|o3\S*|o4\S*|codex\S*)\s+"
    r"(?:default|low|medium|high)\s+·\s+"
)


def _codex_text_looks_ready(text: str) -> bool:
    return (
        bool(_CODEX_IDLE_STATUS_RE.search(text))
        or "OpenAI Codex" in text
        or "permissions: YOLO" in text
        or "bypass permissions on" in text
    )


def _active_agents(team: dict) -> dict:
    return {
        name: cfg
        for name, cfg in (team.get("agents", {}) or {}).items()
        if not (isinstance(cfg, dict) and cfg.get("archived"))
    }


@dataclass
class HealthReport:
    """Accumulator handed to every `_check_*`. Emission and counting
    happen in one place so we don't string-search the formatted output
    later to figure out how many warnings we logged.
    """
    lines: list[str] = field(default_factory=list)
    bad: int = 0
    warn: int = 0

    def ok(self, msg: str) -> None:
        self.lines.append(f"  {_OK} {msg}")

    def fail(self, msg: str) -> None:
        self.lines.append(f"  {_BAD} {msg}")
        self.bad += 1

    def yellow(self, msg: str) -> None:
        self.lines.append(f"  {_WARN}{msg}")
        self.warn += 1

    def info(self, msg: str) -> None:
        self.lines.append(f"  {_INFO}{msg}")

    def note(self, msg: str) -> None:
        """Indented plain line (no glyph)."""
        self.lines.append(f"  {msg}")

    def section(self, title: str) -> None:
        """Unindented section header."""
        self.lines.append(title)

    def blank(self) -> None:
        self.lines.append("")


def _check_state_dir(rep: HealthReport) -> None:
    src = "env" if env_str("EDUFLOW_STATE_DIR") else "default (~/.eduflow)"
    rep.note(f"state_dir: {paths.state_dir()}  ({src})")



def _check_team(rep: HealthReport) -> None:
    """Verify team is loadable and has at least one agent.

    Goes through `config.load_team()` (toml-first, json fallback) so
    deployments on either shape work. Reports red only when there's
    no usable config at all, or when the loaded team has zero agents.
    Corrupt-file detection is handled by the config layer's lenient
    parse (stderr warn) rather than tripping health.
    """
    cf = paths.config_file()
    tf = config.team_file()
    if not cf.exists() and not tf.exists():
        rep.fail(f"team config missing — expected {cf} or {tf}")
        return
    try:
        team = config.load_team()
    except Exception as e:
        rep.fail(f"team config parse error: {e}")
        return
    agents = _active_agents(team)
    if agents:
        rep.ok(f"team config: {len(agents)} agent(s)")
    else:
        rep.fail("team config has no agents (set [team.agents.<name>] in eduflow.toml)")


def _check_runtime_config(rep: HealthReport) -> None:
    """Verify chat_id is set + report lark_profile.

    Reads through `config.chat_id()` / `config.lark_profile()` which
    cascade env > toml > legacy json, so the check is shape-agnostic.
    """
    if chat := config.chat_id():
        rep.ok(f"chat_id: {chat}")
    else:
        rep.fail("chat_id is empty (set it in eduflow.toml)")
    if profile := config.lark_profile():
        rep.ok(f"lark_profile: {profile}")
    else:
        rep.yellow("lark_profile blank — bot identity required for sends")


def _check_session(rep: HealthReport, session: str) -> bool:
    if tmux.has_session(session):
        rep.ok(f"tmux session: {session}")
        return True
    rep.fail(f"tmux session {session} not running (run `eduflow start`)")
    return False


def _agent_runtime_probe_config(agent: str, cfg: dict, rt: dict) -> dict:
    """Return the CLI/model/provider health should probe for an agent.

    Health is an observation surface, so it should follow the runtime that is
    actually selected in runtime-status.json. Falling back to static team
    config can mislabel a switched pane as unhealthy because the ready markers
    belong to a different CLI adapter.
    """
    out = dict(cfg)
    runtime_name = str(rt.get("runtime") or "")
    if not runtime_name:
        return out
    try:
        for item in config.resolve_runtime_chain(agent):
            if item.get("name") == runtime_name:
                out.update({
                    "cli": item.get("cli", out.get("cli", "claude-code")),
                    "model": item.get("model", out.get("model", "")),
                    "provider": item.get("provider", out.get("provider", "")),
                    "env_profile": item.get("env_profile", out.get("env_profile", "")),
                })
                return out
    except Exception:
        pass
    if rt.get("cli"):
        out["cli"] = rt.get("cli")
    if rt.get("model"):
        out["model"] = rt.get("model")
    if rt.get("provider"):
        out["provider"] = rt.get("provider")
    return out


def _check_runtime_env_drift(rep: HealthReport, agent: str, target: tmux.Target,
                             cfg: dict, rt: dict) -> None:
    """Compare the pane's live env against the declared env_profile.

    Delegates to `runtime.verify` so the key set and comparison logic
    stay in one place (used to be duplicated here with a shorter key
    list — drifted silently from verify's canonical 10-key set).
    """
    profile_name = str(rt.get("env_profile") or cfg.get("env_profile") or "")
    if not profile_name:
        return
    ok, mismatches = _verify_mod.verify_live_env_matches_profile(target, profile_name)
    if ok:
        return
    # Distinguish "profile missing / live env unreadable" (yellow) from
    # actual key mismatches (also yellow but more actionable).
    if any("live_env_unavailable" in m or "not in config" in m for m in mismatches):
        rep.yellow(f"runtime_status_env_drift: {agent} {mismatches[0]}")
        return
    rep.yellow(f"runtime_status_env_drift: {agent} " + "; ".join(mismatches))


def _is_live_codex_ready(target: tmux.Target, text: str) -> bool:
    """Codex 0.141+ can scroll its banner out of the health capture window.

    Text alone is unsafe because tmux scrollback may outlive the CLI. Require
    a live non-HUD Node/Codex pane as well.
    """
    if not _codex_text_looks_ready(text):
        return False
    try:
        panes = tmux.list_panes(target)
    except Exception:
        return False
    for pane in panes:
        start = pane.start_command.lower()
        if "omx.js' hud --watch" in start or " omx.js hud --watch" in start:
            continue
        current = pane.current_command.lower()
        if current in {"node", "codex"} or "codex" in start:
            return True
    return False


def _pane_context_signal(text: str) -> context_monitor.ContextUsageSignal | None:
    return context_monitor.detect_context_usage(text)


def _agent_inbox_recovery_needed(agent: str) -> bool:
    try:
        messages = local_facts.list_messages(agent)
    except Exception:
        return False
    for msg in messages:
        if not local_facts.is_high_priority(str(msg.get("priority") or "")):
            continue
        ack_state = str(msg.get("ack_state") or "pending")
        if (not bool(msg.get("read"))) or ack_state not in {
            "agent_acknowledged",
            "action_started",
            "completed",
            "reconciled",
        }:
            return True
    return False


def _check_agents(rep: HealthReport, session: str, agents: list[str],
                  session_alive: bool) -> None:
    heartbeats = local_facts.all_heartbeats()
    from eduflow.util import read_json
    runtime_status = read_json(paths.runtime_status_file(), {"agents": {}}).get("agents", {})
    # Hoist load_team() out of the per-agent loop — each
    # `config.agent_cli` / `agent_config` would otherwise re-read
    # the team config (2-3 disk reads per agent). One read here, dict
    # probes inside the loop with `agents_dict.get(agent, {})` for
    # unknown-agent defaults.
    agents_dict = _active_agents(config.load_team())
    for agent in agents:
        target = tmux.Target(session, agent)
        hb = heartbeats.get(agent)
        hb_suffix = f"  ♥ {ago_ms(hb)}" if hb else "  ♥ never"
        if not session_alive:
            rep.yellow(f"  {agent}: session down, skip{hb_suffix}")
            continue
        if not tmux.has_window(target):
            rep.fail(f"  {agent}: no tmux window{hb_suffix}")
            continue
        rt = runtime_status.get(agent, {})
        cfg = _agent_runtime_probe_config(agent, agents_dict.get(agent, {}), rt)
        cli = cfg.get("cli", "claude-code")
        runtime_suffix = ""
        if rt:
            runtime_suffix = (
                f"  runtime={rt.get('runtime', '?')}"
                f" provider={rt.get('provider', '')}"
                f" model={rt.get('model', '')}"
            )
        try:
            # Resolve adapter from `cli` directly — not via
            # `adapter_for_agent(agent)`, which would re-read the team
            # config inside the loop.
            adapter = get_adapter(cli)
            text = tmux.capture_pane(target, lines=80)
            if cli == "codex-cli" and _is_live_codex_ready(target, text):
                rep.ok(f"  {agent}: pane ready ({cli}){hb_suffix}{runtime_suffix}")
            elif cli != "codex-cli" and any(m in text for m in adapter.ready_markers()):
                rep.ok(f"  {agent}: pane ready ({cli}){hb_suffix}{runtime_suffix}")
            elif cfg.get("lazy") and wake.is_clean_dormant_pane(text):
                rep.ok(f"  {agent}: lazy pane (CLI starts on first message){hb_suffix}{runtime_suffix}")
                continue
            elif cfg.get("lazy"):
                rep.yellow(f"  {agent}: stale lazy pane — respawn on next wake or rehire now{hb_suffix}{runtime_suffix}")
            else:
                rep.yellow(f"  {agent}: pane up but CLI not ready yet — wait a few seconds or check the pane{hb_suffix}{runtime_suffix}")
            context_signal = _pane_context_signal(text)
            if context_signal and context_signal.exhausted:
                rep.fail(
                    f"  {agent}: context_exhausted — pane contains context limit markers; "
                    "do not continue original long task until worker reads inbox / runtime is restarted"
                )
            elif context_signal and context_signal.compact_recommended:
                rep.yellow(
                    f"  {agent}: context_compact_recommended — "
                    f"{context_signal.marker}; run /compact + reidentify before long work"
                )
            elif context_signal and context_signal.warning:
                rep.yellow(
                    f"  {agent}: context_usage_warning — "
                    f"{context_signal.marker}; avoid growing the current pane unchecked"
                )
            _check_runtime_env_drift(rep, agent, target, cfg, rt)
        except Exception as e:
            rep.yellow(f"  {agent}: probe failed — {e}")


def _check_daemon(rep: HealthReport, spec: watchdog.ProcessSpec) -> None:
    if not spec.pid_file.exists():
        rep.yellow(f"{spec.name}: no pid file (not running?)")
        return
    # Check for entrypoint drift first: pid alive but cmdline mismatch.
    if watchdog.check_entrypoint_drift(spec):
        rep.fail(f"{spec.name}: entrypoint_drift — pid alive but cmdline doesn't "
                 f"match '{spec.expected_cmdline}'")
        return
    if watchdog.is_alive(spec):
        rep.ok(f"{spec.name}: alive ({spec.pid_file.read_text().strip()})")
        return
    # PID file present but process dead — watchdog will detect and respawn.
    # This is a transient state during graceful exit or crash recovery.
    rep.yellow(f"{spec.name}: pid file present but process dead (watchdog will respawn)")


def _check_stall_reason(rep: HealthReport) -> None:
    """Report the last router stall reason if the sentinel file exists.

    The router writes `router.stall_reason` (JSON) just before self-SIGTERM
    due to subscribe stall or child exit. The file is cleared on successful
    restart. If it exists, the router hasn't yet recovered — or died again.
    """
    import json as _json
    path = paths.router_stall_reason_file()
    if not path.exists():
        rep.ok("router stall reason: none (last startup clean)")
        return
    try:
        data = _json.loads(path.read_text(encoding="utf-8"))
        reason = data.get("reason", "?")
        detail = data.get("detail", "")
        ts = data.get("ts", 0)
        ago = ago_ms(ts * 1000) if ts else "?"
        router_pid = pidlock.read_pid(paths.router_pid_file())
        if router_pid is not None and pidlock.pid_alive(router_pid):
            rep.info(f"router stall reason: last recovered {reason} ({detail}) — {ago} ago")
            return
        rep.yellow(f"router stall reason: {reason} ({detail}) — {ago} ago")
    except (OSError, ValueError):
        rep.yellow("router stall reason: file present but unreadable")


def _check_hermes_supervisor(rep: HealthReport) -> None:
    """Check if the hermes-supervisor-loop.sh process is alive.

    Hermes supervisor runs as an external shell loop (not supervised by
    watchdog). Its PID file is `hermes-supervisor.pid`. If the file exists
    but the process is dead, report it. If the file doesn't exist, report
    that hermes is not running (informational).
    """
    pid_path = paths.hermes_supervisor_pid_file()
    if not pid_path.exists():
        rep.info("hermes-supervisor: not running (no pid file)")
        return
    pid = pidlock.read_pid(pid_path)
    if pid is None:
        rep.yellow("hermes-supervisor: corrupt pid file")
        return
    if pidlock.pid_alive(pid):
        rep.ok(f"hermes-supervisor: alive (pid {pid})")
    else:
        rep.yellow(f"hermes-supervisor: pid file present but process dead (pid {pid})")


def _check_one_daemon_stability(rep: HealthReport, name: str, log_path) -> None:
    """Scan a daemon log for recent respawn markers."""
    if not log_path or not log_path.exists():
        rep.info(f"{name} stability: no {name}.log yet")
        return
    try:
        # Read last 200 lines to avoid loading huge logs. Treat the file mtime
        # as the current observation window: these daemon logs are append-only
        # and do not timestamp each line, so an old quiet log should not keep
        # health yellow forever.
        window_s = int(tunables.tunable("health.daemon_stability_window_s", 7200))
        if window_s > 0 and time.time() - log_path.stat().st_mtime > window_s:
            rep.ok(f"{name} stability: no recent daemon log activity")
            return
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
        if name == "watchdog":
            lines = [
                l for l in lines
                if not re.search(r"\brouter respawned\b", l, re.IGNORECASE)
            ]
        respawn_count = sum(1 for l in lines if "respawn" in l.lower())
        stall_count = sum(1 for l in lines if "stall" in l.lower() or "stale" in l.lower())
        if respawn_count == 0:
            rep.ok(f"{name} stability: no respawns in recent log")
        elif respawn_count <= 2:
            rep.info(f"{name} stability: {respawn_count} respawn(s) in recent log")
        else:
            benign_idle = (
                name == "router"
                and stall_count >= respawn_count
                and all(
                    ("no events for" in l and "threshold" in l)
                    or "subscribing on chat" in l
                    or "catching up" in l
                    for l in lines
                    if "respawn" in l.lower() or "stall" in l.lower() or "stale" in l.lower()
                    or "no events for" in l
                )
            )
            if benign_idle:
                rep.info(
                    f"{name} stability: {respawn_count} planned idle respawn(s) in recent log"
                )
            else:
                rep.yellow(f"{name} stability: {respawn_count} respawns, {stall_count} stalls in recent log — possible flapping")
    except OSError:
        rep.info(f"{name} stability: could not read {log_path.name}")


def _check_daemon_stability(rep: HealthReport) -> None:
    """Scan known daemon logs for respawn markers and report frequency."""
    for spec in watchdog.all_known_specs():
        _check_one_daemon_stability(rep, spec.name, spec.log_file)


def _check_binaries(rep: HealthReport, agents: list[str]) -> None:
    """For each unique CLI process_name (claude/codex/kimi/...), verify the
    binary is on PATH. Missing binaries don't crash eduflow, but every
    pane spawn will fail to launch its CLI."""
    # Same hoist as `_check_agents` — load team config once, look up
    # each agent's `cli` from the cached dict, get_adapter(cli)
    # skips the per-agent config bounce.
    from eduflow.agents import get_adapter
    agents_dict = _active_agents(config.load_team())
    from eduflow.util import read_json
    runtime_status = read_json(paths.runtime_status_file(), {"agents": {}}).get("agents", {})
    seen: dict[str, list[str]] = {}
    for agent in agents:
        cfg = _agent_runtime_probe_config(agent, agents_dict.get(agent, {}), runtime_status.get(agent, {}))
        cli = cfg.get("cli", "claude-code")
        try:
            name = get_adapter(cli).process_name()
        except Exception:
            continue
        seen.setdefault(name, []).append(agent)
    for binary, used_by in sorted(seen.items()):
        users = ", ".join(used_by)
        path = shutil.which(binary)
        if path:
            rep.ok(f"{binary}: {path}  (used by {users})")
        else:
            rep.fail(f"{binary}: not on PATH  (used by {users})")


def _check_proxy_env(rep: HealthReport) -> None:
    """If HTTPS_PROXY/HTTP_PROXY is set without LARK_CLI_NO_PROXY=1, lark-cli
    requests transit through the proxy — usually fatal on host networks.
    Warning only (not fatal): user may genuinely want the proxy."""
    proxy = env_str("HTTPS_PROXY") or env_str("HTTP_PROXY")
    if not proxy:
        return
    if env_str("LARK_CLI_NO_PROXY").lower() in {"1", "true", "yes", "on"}:
        rep.info(f"HTTPS_PROXY set ({proxy}) but LARK_CLI_NO_PROXY=1 — wrapper will strip")
    else:
        rep.yellow(
            f"HTTPS_PROXY={proxy} set without LARK_CLI_NO_PROXY=1; "
            "lark-cli requests may fail. `export LARK_CLI_NO_PROXY=1` to strip.")


def _check_cursor(rep: HealthReport) -> None:
    cur = catchup.read_cursor()
    if cur:
        rep.ok(f"router cursor: {cur.get('message_id', '?')} (create_time={cur.get('create_time', '?')})")
    else:
        # Empty cursor is normal until the first inbound event lands;
        # advancement only happens for events coming OFF the wire, not
        # for self-originated `say` calls. Informational, not warning.
        rep.info("router cursor: empty (advances on first inbound event)")


def _check_memory(rep: HealthReport) -> None:
    """Round-132: list agents that have written memory entries. Empty
    is normal on a fresh deploy; informational only. Surfaces
    persisted state that would otherwise need a `find facts/ -name
    memory.jsonl` to discover."""
    from eduflow.store import memory
    agents = sorted(memory.all_agents_with_memory())
    if not agents:
        rep.info("memory: no agent has written entries yet")
        return
    # One-liner if few agents; line-per-agent if many (>5)
    if len(agents) <= 5:
        rep.info(f"memory: {len(agents)} agent(s) with entries — "
                 f"{', '.join(agents)}")
    else:
        rep.info(f"memory: {len(agents)} agent(s) with entries:")
        for a in agents:
            rep.note(f"  - {a}")


def _check_runtime_guard(rep: HealthReport) -> None:
    from eduflow.util import read_json
    data = read_json(paths.runtime_guard_state_file(), {"agents": {}})
    agents = data.get("agents", {})
    try:
        active_agents = set(config.agent_names())
    except Exception:
        active_agents = set()
    if active_agents:
        agents = {
            agent: row
            for agent, row in agents.items()
            if agent in active_agents
        }
    if not agents:
        rep.info("runtime guard: no agent guard state")
        return
    cooling = []
    needs = []
    escalating = []
    for agent, row in sorted(agents.items()):
        if row.get("cooldown_until", 0):
            cooling.append(agent)
        if row.get("needs_manager_action", False):
            needs.append(agent)
        if row.get("escalation_needed", False):
            escalating.append(agent)
    if not cooling and not needs:
        rep.info(f"runtime guard: {len(agents)} agent record(s), none cooling down")
    else:
        if cooling:
            rep.yellow(f"runtime guard cooldown: {', '.join(cooling)}")
        if needs:
            rep.yellow(f"runtime guard needs_manager_action: {', '.join(needs)}")
        if escalating:
            rep.yellow(f"runtime guard escalation_needed: {', '.join(escalating)}")
    for agent, row in sorted(agents.items()):
        detail_bits = []
        if row.get("last_failure_reason"):
            detail_bits.append(f"failure={row['last_failure_reason']}")
        if row.get("last_switch_reason"):
            detail_bits.append(f"switch_reason={row['last_switch_reason']}")
        if row.get("last_switch_outcome"):
            detail_bits.append(f"outcome={row['last_switch_outcome']}")
        if row.get("last_best_outcome"):
            detail_bits.append(f"best={row['last_best_outcome']}")
        if row.get("last_attempts"):
            detail_bits.append(f"attempts={row['last_attempts']}")
        if row.get("last_pool_switched"):
            detail_bits.append("cross_pool=true")
        if row.get("from_runtime") or row.get("to_runtime"):
            detail_bits.append(
                f"route={row.get('from_runtime') or '-'}->{row.get('to_runtime') or '-'}"
            )
        if row.get("escalation_reason"):
            detail_bits.append(f"escalation={row['escalation_reason']}")
        if detail_bits:
            rep.note(f"  {agent}: {' '.join(detail_bits)}")


def _check_import_path(rep: HealthReport) -> None:
    """Show the actual import path of the `eduflow` package.

    Catches the import-drift bug where the running binary loads the old
    /Volumes/Halobster/Codex相关/EduFlow/src/eduflow/ package
    instead of the current EduFlow-Team-orch/src/eduflow/ tree —
    edits to the new tree would silently have no effect.
    """
    import eduflow as _ct
    mod_path = getattr(_ct, "__file__", "") or ""
    rep.note(f"eduflow.__file__: {mod_path}")
    root = os.environ.get("EDUFLOW_ROOT") or ""
    if root and mod_path:
        # Expect the module to live under $ROOT/src/eduflow/. Resolve
        # symlinks on both sides first — a symlinked EDUFLOW_ROOT (e.g.
        # a convenience path pointing at the real worktree) otherwise
        # false-positives as drift even though it's the same tree.
        import pathlib
        expected_prefix = os.path.realpath(
            str(pathlib.Path(root) / "src" / "eduflow"))
        if not os.path.realpath(mod_path).startswith(expected_prefix):
            rep.fail(f"import drift: eduflow loaded from {mod_path}, "
                     f"expected under {expected_prefix}")
        else:
            rep.ok("eduflow import path matches EDUFLOW_ROOT")
    elif mod_path:
        rep.yellow("eduflow import path set but EDUFLOW_ROOT unset; "
                   "cannot verify drift")


def _check_runtime_operational_readiness(rep: HealthReport, session: str,
                                         agents: list[str],
                                         session_alive: bool) -> None:
    """Per-agent runtime operational readiness verdict.

    Uses `runtime_verify.compute_verdict` to combine env drift / smoke /
    pane-text / inbox state into a single verdict per agent. Critical
    agents (manager, review_course, worker_course, worker_builder,
    worker_qbank) must show `proved_ready` — anything else is red.
    Non-critical agents (auto_ops, anna) only warn.
    """
    from eduflow.commands import runtime_verify
    from eduflow.runtime import failover as _failover
    critical = {"manager", "review_course", "worker_course",
                "worker_builder", "worker_qbank"}
    if not session_alive:
        rep.yellow("runtime readiness: session down")
        return
    any_critical_bad = False
    for agent in agents:
        try:
            v = runtime_verify.compute_verdict(agent)
        except Exception as e:
            rep.yellow(f"  {agent}: runtime readiness probe failed — {e}")
            continue
        # Fill in pool_id from failover module if compute_verdict didn't.
        if not v.get("declared_pool_id") and v.get("declared_runtime"):
            try:
                v["declared_pool_id"] = _failover.runtime_pool_id(v["declared_runtime"])
            except Exception:
                pass
        verdict = v["verdict"]
        is_critical = agent in critical
        if verdict == "proved_ready":
            rep.ok(f"  {agent}: proved_ready "
                   f"(runtime={v['declared_runtime']}, pool={v['declared_pool_id'] or '?'})")
        elif verdict == "unknown":
            if is_critical:
                rep.yellow(f"  {agent}: no runtime status recorded")
            else:
                rep.info(f"  {agent}: no runtime status recorded")
        else:
            detail_bits = [f"env_ok={v['env_ok']}",
                           f"smoke={v['smoke_verdict']}",
                           f"pane_clean={v['pane_clean']}",
                           f"inbox={v['inbox_state']}"]
            if verdict == "ready_unproven":
                detail_bits.append("proved_ready=false")
            if (
                verdict == "inbox_not_consumed"
                or v.get("inbox_state") == "not_consumed"
                or _agent_inbox_recovery_needed(agent)
            ):
                detail_bits.append("inbox_recovery_needed=true")
            line = f"  {agent}: {verdict}  ({', '.join(detail_bits)})"
            if is_critical:
                rep.fail(line)
                any_critical_bad = True
            else:
                rep.yellow(line)
    if not any_critical_bad:
        rep.info("runtime readiness: all critical agents verified")


# ── D scheduler (P6) ──────────────────────────────────────────────────


_D_SCHEDULER_LAG_WARN_MS = 30 * 60 * 1000  # 30 minutes


def _now_ms_for_health() -> int:
    """Wall-clock ms for health comparisons. Inlined helper so tests can
    patch the module-level clock without touching util.now_ms."""
    import time as _time
    return int(_time.time() * 1000)


def _safe_scheduled_tasks_call(label: str, fn, default):
    """Read-only wrapper that swallows store errors so health stays green
    on a corrupt scheduler file. The original exception is logged on the
    HealthReport as a degraded note — never silently dropped."""
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001
        return default, (label, type(exc).__name__, str(exc))


def _collect_d_scheduler_health(now_ms_value: int) -> dict:
    """Read-only view of D scheduler state. Returns a dict so callers can
    format the section deterministically.
    """
    heartbeat, hb_err = _safe_scheduled_tasks_call(
        "heartbeat", scheduled_tasks.get_heartbeat,
        {"last_tick_at": 0, "lag_ms": 0, "error": ""},
    )
    occurrences, occ_err = _safe_scheduled_tasks_call(
        "occurrences", scheduled_tasks.list_occurrences, [],
    )
    rules, rules_err = _safe_scheduled_tasks_call(
        "rules", scheduled_tasks.list_rules, [],
    )

    hb_status = "missing"
    lag = "missing"
    last_success_ms = 0
    error_text = ""
    last_tick = int(heartbeat.get("last_tick_at") or 0)
    error_text = str(heartbeat.get("error") or "")
    if last_tick > 0:
        age = now_ms_value - last_tick
        lag = "warn" if age >= _D_SCHEDULER_LAG_WARN_MS else "ok"
        last_success_ms = 0 if error_text else last_tick
        hb_status = "error" if error_text else "ok"

    counts = {"awaiting_manager": 0, "running": 0, "blocked": 0}
    for occ in occurrences:
        s = str(occ.get("status") or "")
        if s in counts:
            counts[s] += 1

    # Consecutive skip/failure streaks: walk occurrences sorted by
    # updated_at desc and stop at the first non-terminal status.
    sorted_occs = sorted(
        occurrences,
        key=lambda o: int(o.get("updated_at") or 0),
        reverse=True,
    )
    skip_streak = 0
    failure_streak = 0
    for occ in sorted_occs:
        s = str(occ.get("status") or "")
        if s == "skipped":
            skip_streak += 1
            continue
        if s == "failed":
            failure_streak += 1
            continue
        break

    attention_required = sum(
        1 for r in rules if str(r.get("status") or "") == "attention_required"
    )

    return {
        "heartbeat_status": hb_status,
        "lag": lag,
        "last_tick": last_tick,
        "last_success_ms": last_success_ms,
        "error": error_text,
        "counts": counts,
        "skip_streak": skip_streak,
        "failure_streak": failure_streak,
        "attention_required": attention_required,
        "degraded": [err for err in (hb_err, occ_err, rules_err) if err],
    }


def _check_d_scheduler(rep: HealthReport, now_ms_value: int) -> None:
    """Surface D scheduler heartbeat, lag, pending/running counts, and
    consecutive skip/failure streaks. Read-only via scheduled_tasks APIs
    — never writes the store. Degraded note is appended when any read
    raised (e.g. corrupt rules.json)."""
    rep.section("D scheduler:")
    try:
        snapshot = _collect_d_scheduler_health(now_ms_value)
    except Exception as exc:  # noqa: BLE001 — defensive
        rep.yellow(f"degraded ({type(exc).__name__}: {exc})")
        return

    hb = snapshot["heartbeat_status"]
    lag = snapshot["lag"]
    counts = snapshot["counts"]
    last_tick = snapshot["last_tick"]
    if last_tick:
        hb_line = (
            f"heartbeat={hb} last_tick={ago_ms(last_tick)} "
            f"lag={lag} pending={counts['awaiting_manager']} "
            f"running={counts['running']} blocked={counts['blocked']} "
            f"attention_required={snapshot['attention_required']}"
        )
    else:
        hb_line = (
            f"heartbeat={hb} last_tick=never lag={lag} "
            f"pending={counts['awaiting_manager']} "
            f"running={counts['running']} blocked={counts['blocked']} "
            f"attention_required={snapshot['attention_required']}"
        )
    if snapshot["error"]:
        # Surface the underlying exception kind so operators can grep
        # without matching the full payload.
        kind = snapshot["error"].split(":", 1)[0] or "error"
        hb_line += f" error={kind}"
    if hb == "missing":
        rep.yellow(hb_line)
    elif hb == "error":
        rep.yellow(hb_line)
    elif lag == "warn":
        rep.yellow(hb_line)
    else:
        rep.ok(hb_line)

    streak_line = (
        f"  consecutive_skip={snapshot['skip_streak']} "
        f"consecutive_failure={snapshot['failure_streak']}"
    )
    if snapshot["skip_streak"] or snapshot["failure_streak"]:
        rep.note(streak_line)
    else:
        rep.info(streak_line)

    if snapshot["degraded"]:
        for label, kind, msg in snapshot["degraded"]:
            rep.yellow(f"  degraded_source={label} ({kind}: {msg})")


def _build_report() -> HealthReport:
    """Run every check and return the populated HealthReport. Pure
    enumeration — main() picks the renderer (text or JSON) and the
    exit code based on rep.bad."""
    rep = HealthReport()

    rep.section("paths:")
    _check_state_dir(rep)
    rep.blank()

    rep.section("config:")
    _check_team(rep)
    _check_runtime_config(rep)
    rep.blank()

    try:
        team = config.load_team()
        session = team.get("session", "EduFlow")
        agents = sorted(_active_agents(team))
    except Exception:
        session, agents = "EduFlow", []

    if agents:
        rep.section("binaries:")
        _check_binaries(rep, agents)
        rep.blank()

    rep.section("env:")
    _check_proxy_env(rep)
    rep.blank()

    rep.section("tmux:")
    session_alive = _check_session(rep, session)
    if agents:
        _check_agents(rep, session, agents, session_alive)
    rep.blank()

    rep.section("daemons:")
    for spec in watchdog.all_known_specs():
        _check_daemon(rep, spec)
    rep.blank()

    rep.section("daemon stability:")
    _check_daemon_stability(rep)
    _check_stall_reason(rep)
    rep.blank()

    rep.section("hermes-supervisor:")
    _check_hermes_supervisor(rep)
    rep.blank()

    rep.section("router state:")
    _check_cursor(rep)
    rep.blank()

    rep.section("memory:")
    _check_memory(rep)
    rep.blank()

    rep.section("runtime guard:")
    _check_runtime_guard(rep)
    rep.blank()

    rep.section("D scheduler:")
    _check_d_scheduler(rep, _now_ms_for_health())
    rep.blank()

    rep.section("runtime operational readiness:")
    if agents:
        _check_runtime_operational_readiness(rep, session, agents, session_alive)
    else:
        rep.info("no agents in team config")
    rep.blank()

    rep.section("import path:")
    _check_import_path(rep)

    return rep


def _emit_text(rep: HealthReport) -> None:
    """Default renderer: the formatted lines + a summary footer."""
    print("\n".join(rep.lines))
    if rep.bad:
        print(f"\n{_BAD} {rep.bad} red check(s) — see above")
    elif rep.warn:
        print(f"\n{_WARN}no errors, {rep.warn} warning(s) — see above")
    else:
        print(f"\n{_OK} all green")


def _emit_json(rep: HealthReport) -> None:
    """Machine-readable shape:
        {"ok": bool, "bad": int, "warn": int, "lines": [str, ...]}
    Smoke conductors / CI can branch on `ok` and inspect `lines` for
    the rendered glyphs (which still appear in `lines`, just packaged)."""
    print_json({
        "ok": rep.bad == 0,
        "bad": rep.bad,
        "warn": rep.warn,
        "lines": list(rep.lines),
    })


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, "usage: eduflow health [--json]"):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    if (rc := reject_extra_args(rest, "usage: eduflow health [--json]")) is not None:
        return rc

    rep = _build_report()
    if as_json:
        _emit_json(rep)
    else:
        _emit_text(rep)
    return 1 if rep.bad else 0
