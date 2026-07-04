"""`eduflow runtime-guard`

Inspect and clear runtime guard state:
  - `eduflow runtime-guard`
  - `eduflow runtime-guard --json`
  - `eduflow runtime-guard clear <agent>`
  - `eduflow runtime-guard clear --all`
  - `eduflow runtime-guard reset-flags <agent>`
  - `eduflow runtime-guard reset-flags --all`
  - `eduflow runtime-guard watch`
"""
from __future__ import annotations

import time

from eduflow.runtime import paths
from eduflow.util import file_lock, maybe_print_help, pop_bool_flag, print_json, read_json, reject_extra_args, write_json


USAGE = (
    "usage: eduflow runtime-guard [--json]\n"
    "   or: eduflow runtime-guard clear <agent>\n"
    "   or: eduflow runtime-guard clear --all\n"
    "   or: eduflow runtime-guard reset-flags <agent>\n"
    "   or: eduflow runtime-guard reset-flags --all\n"
    "   or: eduflow runtime-guard watch"
)


def _state() -> dict:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    return read_json(path, {"agents": {}})


def _save(data: dict) -> None:
    path = paths.runtime_guard_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)


def _emit_text(data: dict) -> None:
    agents = data.get("agents", {})
    if not agents:
        print("runtime-guard: no agent state")
        return
    for agent in sorted(agents):
        row = agents[agent]
        cooldown_until = row.get("cooldown_until", 0)
        needs = row.get("needs_manager_action", False)
        switches = len(row.get("switch_times", []))
        line = f"{agent}  switches={switches}"
        if cooldown_until:
            line += f"  cooldown_until={cooldown_until}"
        if needs:
            line += "  needs_manager_action=true"
        if row.get("escalation_needed", False):
            line += "  escalation_needed=true"
        if row.get("last_switch_outcome"):
            line += f"  outcome={row['last_switch_outcome']}"
        if row.get("last_failure_reason"):
            line += f"  failure={row['last_failure_reason']}"
        if row.get("escalation_reason"):
            line += f"  escalation={row['escalation_reason']}"
        print(line)


def _clear_agent(agent: str) -> int:
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = _state()
        agents = data.setdefault("agents", {})
        if agent not in agents:
            print(f"runtime-guard: {agent} not found")
            return 1
        del agents[agent]
        _save(data)
    print(f"runtime-guard: cleared {agent}")
    return 0


def _clear_all() -> int:
    _save({"agents": {}})
    print("runtime-guard: cleared all")
    return 0


# ── reset-flags: clear escalation flags only, keep failback tracking ──

_ESCALATION_FLAGS = {
    "escalation_needed",
    "needs_manager_action",
    "escalation_reason",
    "cooldown_until",
    "last_alert_level",
}


def _reset_flags(agent: str) -> int:
    """Clear escalation flags for *agent*, preserving failback/switch tracking."""
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = _state()
        agents = data.setdefault("agents", {})
        if agent not in agents:
            print(f"runtime-guard: {agent} not found")
            return 1
        row = agents[agent]
        cleared = [k for k in _ESCALATION_FLAGS if k in row]
        for key in cleared:
            del row[key]
        _save(data)
    if cleared:
        print(f"runtime-guard: reset flags for {agent} (cleared: {', '.join(cleared)})")
    else:
        print(f"runtime-guard: {agent} had no escalation flags to reset")
    return 0


def _reset_flags_all() -> int:
    """Clear escalation flags for all agents."""
    path = paths.runtime_guard_state_file()
    with file_lock(path):
        data = _state()
        agents = data.setdefault("agents", {})
        total_cleared = 0
        for agent, row in agents.items():
            cleared = [k for k in _ESCALATION_FLAGS if k in row]
            for key in cleared:
                del row[key]
            total_cleared += len(cleared)
        _save(data)
    agent_count = len(agents)
    print(f"runtime-guard: reset flags for {agent_count} agents ({total_cleared} flags cleared)")
    return 0


# ── ANSI helpers ───────────────────────────────────────────────────

_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _color_for_score(score: int) -> str:
    if score >= 80:
        return _GREEN
    if score >= 50:
        return _YELLOW
    return _RED


# ── health scoring ─────────────────────────────────────────────────


def _compute_health(row: dict, now: float) -> tuple[int, list[str]]:
    """Return (score, [penalty labels]) for one agent's guard row.

    Scoring:
      100  base
      -20  recent switch (switch_times within last 600 s)
      -30  currently in fallback (failback.in_fallback_since set)
      -50  in cooldown (cooldown_until > now)
    """
    score = 100
    penalties: list[str] = []

    # Recent switch penalty
    switch_times = row.get("switch_times") or []
    if switch_times:
        recent_cutoff = now - 600
        recent = [t for t in switch_times if float(t) > recent_cutoff]
        if recent:
            score -= 20
            penalties.append(f"recent_switch({len(recent)})")

    # Fallback penalty
    failback = row.get("failback") or {}
    if failback.get("in_fallback_since"):
        score -= 30
        penalties.append("in_fallback")

    # Cooldown penalty
    cooldown_until = float(row.get("cooldown_until") or 0)
    if cooldown_until > now:
        score -= 50
        penalties.append("cooldown")

    return max(score, 0), penalties


# ── watch mode ─────────────────────────────────────────────────────


def _fmt_cooldown(row: dict, now: float) -> str:
    cooldown_until = float(row.get("cooldown_until") or 0)
    if cooldown_until <= now:
        return "-"
    remaining = int(cooldown_until - now)
    return f"{remaining}s"


def _watch_once(data: dict, now: float) -> None:
    """Print one snapshot table of all guarded agents."""
    agents = data.get("agents", {})
    if not agents:
        print("runtime-guard watch: no agent state")
        return

    # Header
    print(f"\n{_BOLD}{'Agent':<18} {'Runtime':<22} {'Last Reason':<22} "
          f"{'Cooldown':<10} {'Health':<8} {'Penalties'}{_RESET}")
    print("-" * 100)

    for agent in sorted(agents):
        row = agents[agent]
        # Determine current runtime: prefer last_switch_outcome context,
        # fall back to from_runtime of last switch
        runtime = str(row.get("last_switch_to") or row.get("current_runtime") or "-")
        reason = str(row.get("last_switch_reason") or row.get("last_failure_reason") or "-")
        cooldown = _fmt_cooldown(row, now)
        score, penalties = _compute_health(row, now)
        color = _color_for_score(score)
        penalty_str = ", ".join(penalties) if penalties else ""
        score_str = f"{color}{score:>4}{_RESET}"

        extra = ""
        if row.get("needs_manager_action"):
            extra += " [MANAGER]"
        if row.get("escalation_needed"):
            extra += " [ESCALATE]"

        print(f"{agent:<18} {runtime:<22} {reason:<22} "
              f"{cooldown:<10} {score_str:<18} {penalty_str}{extra}")

    print()


def _watch() -> int:
    """Poll loop: print guard table every N seconds, Ctrl-C to exit."""
    try:
        from eduflow.runtime import tunables
        interval = int(tunables.tunable("runtime_guard.watch_interval_s", 5))
    except Exception:
        interval = 5

    print(f"runtime-guard watch: polling every {interval}s (Ctrl-C to stop)")
    try:
        while True:
            now = time.time()
            data = _state()
            _watch_once(data, now)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nruntime-guard watch: stopped")
    return 0


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    if not rest:
        data = _state()
        if as_json:
            print_json(data)
        else:
            _emit_text(data)
        return 0
    if rest[0] == "watch":
        return _watch()
    if rest[0] == "reset-flags":
        if len(rest) == 2 and rest[1] == "--all":
            return _reset_flags_all()
        if len(rest) == 2:
            return _reset_flags(rest[1])
        print(USAGE)
        return 1
    if rest[0] != "clear":
        print(USAGE)
        return 1
    if len(rest) == 2 and rest[1] == "--all":
        return _clear_all()
    if len(rest) == 2:
        return _clear_agent(rest[1])
    if (rc := reject_extra_args(rest, USAGE)) is not None:
        return rc
    return 1
