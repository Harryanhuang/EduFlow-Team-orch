"""`eduflow runtime verify <agent>` — runtime operational readiness.

Computes the verdict for one agent by combining:
  - declared runtime (from runtime-status.json)
  - live env match against the declared env_profile
  - API smoke against the provider gateway
  - pane-text absence of failure markers
  - live CLI process identity and ready marker
  - explicit inbox consumption (an unread item is never inferred consumed)

Verdict values:
  proved_ready         — all gates pass
  ready_unproven       — env ok + smoke ok, but pane text has failure
                         markers or inbox not consumed
  env_drift            — live env does not match env_profile
  smoke_failed         — API smoke returned non-2xx
  inbox_not_consumed   — env+smoke ok, but latest high-priority inbox
                         is still unread after the switch
  pane_missing         — tmux window absent
  unknown              — no runtime status found
"""
from __future__ import annotations

import time
from typing import Any

from eduflow.runtime import config, lifecycle, paths, tmux, verify
from eduflow.store import local_facts
from eduflow.util import (
    file_lock, maybe_print_help, pop_bool_flag, print_json, read_json,
    write_json,
)
from eduflow.agents import get_adapter


USAGE = "usage: eduflow runtime verify <agent> [--json] [--live-smoke]"
VERDICT_CACHE_TTL_SECONDS = 300


def _pane_failure_scan(target, adapter) -> tuple[bool, list[str]]:
    """Scan pane text for failure markers AFTER the ready banner.

    Returns (clean, found_markers). Imported from lifecycle's helper so
    the verdict matches what restart_with_runtime uses post-switch.
    """
    from eduflow.runtime.lifecycle import _verify_no_failure_markers
    return _verify_no_failure_markers(target, adapter, wait_s=0)


def _live_process_and_cli_ready(target, status: dict, out: dict) -> bool:
    """Require live process identity and a current CLI-ready marker."""
    try:
        cli = status.get("cli") or "claude-code"
        adapter = get_adapter(cli)
        expected_process = adapter.process_name().lower()
        panes = tmux.list_panes(target)
    except (KeyError, Exception):
        out["process_ok"] = False
        out["cli_ready"] = False
        return False

    def matches(pane) -> bool:
        current = str(pane.current_command or "").lower()
        start = str(pane.start_command or "").lower()
        return (
            current == expected_process
            or (expected_process == "codex" and current == "node" and "codex" in start)
        )

    out["process_ok"] = any(matches(pane) for pane in panes)
    if not out["process_ok"]:
        out["cli_ready"] = False
        return False
    try:
        text = tmux.capture_pane(target, lines=80)
    except Exception:
        out["cli_ready"] = False
        return False
    out["cli_ready"] = any(marker in text for marker in adapter.ready_markers())
    return bool(out["cli_ready"])


def _unread_inbox_state(agent: str) -> str:
    """Return the actual inbox-consumption state for a live agent.

    An unread delivery is evidence that the agent has not consumed it, no
    matter how long it has been waiting.  Older versions treated a missing
    timestamp as old enough to count as consumed, which inverted that fact.
    """
    try:
        rows = local_facts.list_messages(agent, unread_only=True)
    except Exception:
        return "unknown"
    if not rows:
        return "no_pending"
    # ``created_at`` is the canonical local-facts timestamp; keep this read
    # explicit so malformed legacy rows cannot silently become evidence.
    latest = rows[-1]
    if not latest.get("created_at"):
        return "unknown"
    return "not_consumed"


def _live_pane_is_clean(agent: str, target, status: dict, out: dict) -> bool:
    """Refresh pane failure evidence even when provider smoke is cached."""
    try:
        cli = status.get("cli") or config.resolved_agent_config(agent).get("cli", "claude-code")
        adapter = get_adapter(cli)
    except (KeyError, Exception):
        return False
    clean, found = _pane_failure_scan(target, adapter)
    out["pane_clean"] = clean
    out["found_markers"] = found
    return clean


def _cached_proof_is_fresh(status: dict) -> bool:
    try:
        verified_at = float(status.get("verified_at") or 0)
    except (TypeError, ValueError):
        return False
    return verified_at > 0 and 0 <= time.time() - verified_at <= VERDICT_CACHE_TTL_SECONDS


def compute_verdict(agent: str, *, live_smoke: bool = False) -> dict:
    """Compute the runtime operational readiness verdict for `agent`.

    By default, reads the cached env_ok / smoke_ok / verified_at written
    by `restart_with_runtime` at hard-switch time. This keeps `runtime
    verify` and `health` read-only w.r.t. the API quota — no POST
    /v1/messages unless the operator explicitly asks for `--live-smoke`.

    When `live_smoke=True` (or the cached row has no env_ok/smoke_ok —
    e.g. the runtime was provisioned before the proved-ready gate existed),
    the full probe chain runs: live env match → API smoke → pane-text
    scan → inbox consumption.

    Returns a dict:
      verdict          — one of the verdict strings above
      declared_runtime — from runtime-status.json (or "unknown")
      declared_env     — env_profile declared (or "")
      env_ok           — bool or None if not applicable
      smoke_ok         — bool or None if skipped
      smoke_verdict    — ok/failed/skipped
      process_ok        — pane process matches the configured CLI
      cli_ready         — pane shows the configured CLI ready marker
      pane_clean       — bool or None if pane missing
      inbox_state      — "consumed" / "not_consumed" / "no_pending" / "unknown"
      mismatches       — list of env-drift mismatch strings
      found_markers    — list of failure markers found
      cached           — True iff verdict came from the runtime-status cache
    """
    out: dict[str, Any] = {
        "verdict": "unknown",
        "declared_runtime": "unknown",
        "declared_env": "",
        "declared_pool_id": "",
        "env_ok": None,
        "smoke_ok": None,
        "smoke_verdict": "skipped",
        "process_ok": False,
        "cli_ready": False,
        "pane_clean": None,
        "inbox_state": "unknown",
        "mismatches": [],
        "found_markers": [],
        "cached": False,
    }
    status = lifecycle.current_runtime_status(agent)
    if not status:
        out["verdict"] = "unknown"
        return out
    declared_runtime = str(status.get("runtime") or "unknown")
    declared_env = str(status.get("env_profile") or "")
    out["declared_runtime"] = declared_runtime
    out["declared_env"] = declared_env
    from eduflow.runtime import failover as _failover
    out["declared_pool_id"] = _failover.runtime_pool_id(declared_runtime) if declared_runtime != "unknown" else ""

    # Pane existence — always checked live; a missing pane can't be cached.
    try:
        team = config.load_team()
    except Exception:
        out["verdict"] = "unknown"
        return out
    session = team.get("session", "EduFlow")
    target = tmux.Target(session, agent)
    if not tmux.has_session(session) or not tmux.has_window(target):
        out["verdict"] = "pane_missing"
        return out

    # Cache only the provider smoke. Environment and pane evidence are cheap,
    # live checks and must not be contradicted by an old status row.
    has_cached_gates = "env_ok" in status and "smoke_ok" in status
    if not live_smoke and has_cached_gates:
        if not _cached_proof_is_fresh(status):
            out["verdict"] = "ready_unproven"
            return out
        env_ok, mismatches = verify.verify_live_env_matches_profile(target, declared_env)
        out["env_ok"] = env_ok
        out["mismatches"] = mismatches
        if not env_ok:
            out["verdict"] = "env_drift"
            return out
        env_ok = bool(status.get("env_ok"))
        smoke_ok = bool(status.get("smoke_ok"))
        out["smoke_ok"] = smoke_ok
        out["smoke_verdict"] = "ok" if smoke_ok else "failed"
        out["cached"] = True
        if not env_ok:
            out["verdict"] = "env_drift"
            return out
        if not smoke_ok:
            out["verdict"] = "smoke_failed"
            return out
        if not _live_process_and_cli_ready(target, status, out):
            out["verdict"] = "ready_unproven"
            return out
        if not _live_pane_is_clean(agent, target, status, out):
            out["verdict"] = "ready_unproven"
            return out
        out["inbox_state"] = _unread_inbox_state(agent)
        if out["inbox_state"] != "no_pending":
            out["verdict"] = "inbox_not_consumed" if out["inbox_state"] == "not_consumed" else "ready_unproven"
            return out
        out["verdict"] = "proved_ready"
        return out

    # Live probe path — full chain.
    # Env match.
    env_ok, mismatches = verify.verify_live_env_matches_profile(target, declared_env)
    out["env_ok"] = env_ok
    out["mismatches"] = mismatches
    if not env_ok:
        out["verdict"] = "env_drift"
        return out

    # API smoke.
    resolved = dict(status)
    smoke_verdict, _detail = verify.api_smoke_runtime(resolved)
    out["smoke_verdict"] = smoke_verdict
    out["smoke_ok"] = smoke_verdict == "ok"
    if smoke_verdict == "skipped":
        out["verdict"] = "ready_unproven"
        return out
    if not out["smoke_ok"]:
        out["verdict"] = "smoke_failed"
        return out

    # Pane-text absence of failure markers.
    if not _live_process_and_cli_ready(target, status, out):
        out["verdict"] = "ready_unproven"
        return out
    if not _live_pane_is_clean(agent, target, status, out):
        out["verdict"] = "ready_unproven"
        return out

    # Inbox consumption.
    out["inbox_state"] = _unread_inbox_state(agent)
    if out["inbox_state"] != "no_pending":
        out["verdict"] = "inbox_not_consumed" if out["inbox_state"] == "not_consumed" else "ready_unproven"
        return out
    out["verdict"] = "proved_ready"
    return out


def _emit_text(v: dict) -> None:
    verdict = v["verdict"]
    glyph = {"proved_ready": "✅", "no_pending": "✅", "consumed": "✅"}.get(verdict, "❌")
    if verdict in {"ready_unproven", "inbox_not_consumed"}:
        glyph = "⚠️ "
    cache_tag = " (cached)" if v.get("cached") else ""
    print(f"{glyph} runtime verdict: {verdict}{cache_tag}")
    print(f"  declared_runtime: {v['declared_runtime']}")
    print(f"  declared_env:     {v['declared_env'] or '(none)'}")
    if v["declared_pool_id"]:
        print(f"  declared_pool:    {v['declared_pool_id']}")
    if v["env_ok"] is not None:
        print(f"  env_ok:           {v['env_ok']}")
    print(f"  process_ok:       {v['process_ok']}")
    print(f"  cli_ready:        {v['cli_ready']}")
    if v["mismatches"]:
        for m in v["mismatches"]:
            print(f"    - {m}")
    if v["smoke_verdict"] != "skipped":
        print(f"  smoke:            {v['smoke_verdict']}")
    if v["pane_clean"] is not None:
        print(f"  pane_clean:       {v['pane_clean']}")
    if v["found_markers"]:
        for m in v["found_markers"]:
            print(f"    - {m}")
    print(f"  inbox_state:      {v['inbox_state']}")


def _clear_stale_runtime_guard(agent: str, verdict: str) -> None:
    """Drop stale guard escalation after a fresh proved-ready verdict."""
    if verdict != "proved_ready":
        return
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = read_json(path, {"agents": {}})
        agents = data.setdefault("agents", {})
        if agent not in agents:
            return
        del agents[agent]
        write_json(path, data)


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    live_smoke = pop_bool_flag(rest, "--live-smoke")
    if len(rest) < 1:
        print(USAGE)
        return 1
    agent = rest[0]
    extra = rest[1:]
    if extra:
        print(f"❌ unexpected args: {extra}\n{USAGE}")
        return 1
    v = compute_verdict(agent, live_smoke=live_smoke)
    _clear_stale_runtime_guard(agent, str(v.get("verdict") or ""))
    if as_json:
        print_json(v)
    else:
        _emit_text(v)
    return 0 if v["verdict"] == "proved_ready" else 1
