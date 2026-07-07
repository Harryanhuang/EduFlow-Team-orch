"""`eduflow agent unlock <name> [--duration 30m]` / `eduflow agent lock <name>`

T-120: manager 显式解锁/锁回 warm-standby agent 的临时开关。
- unlock: 把 agent 的 enabled_for_dispatch 切到 true + 写 audit log
- lock: 切回 false + 写 audit log
- 默认 unlock 30 分钟自动 lock（防止忘关），用 --duration 调整
- audit 写 facts/agent-unlock-audit.jsonl (每行: ts, agent, action, by, duration_s, expires_at)
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from eduflow.runtime import config, paths
from eduflow.util import error_exit, maybe_print_help, usage_error


USAGE = "usage: eduflow agent unlock <name> [--duration 30m] [--by <caller>] | eduflow agent lock <name> [--by <caller>]"


def _audit_file() -> Path:
    return paths.facts_dir() / "agent-unlock-audit.jsonl"


def _append_audit(entry: dict) -> None:
    f = _audit_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _parse_duration(spec: str) -> int:
    """Accept 30m / 2h / 3600s / 1800 (raw seconds) → int seconds."""
    text = str(spec or "").strip().lower()
    if not text:
        return 1800
    for suffix, mult in (("h", 3600), ("m", 60), ("s", 1)):
        if text.endswith(suffix):
            try:
                return int(text[:-1]) * mult
            except ValueError:
                pass
    try:
        return int(text)
    except ValueError:
        return 1800


def _set_agent_dispatch_flag(agent: str, value: bool) -> None:
    """Set team.agents.<agent>.enabled_for_dispatch in eduflow.toml.

    ponytail: this only writes the one boolean this CLI owns; use a real TOML
    writer if agent config editing grows beyond this single field.
    """
    path = paths.config_file()
    text = path.read_text(encoding="utf-8")
    header = f"[team.agents.{agent}]"
    start = text.find(header)
    if start < 0:
        raise KeyError(agent)
    next_match = re.search(r"(?m)^\[", text[start + len(header):])
    end = len(text) if next_match is None else start + len(header) + next_match.start()
    section = text[start:end]
    line = f"enabled_for_dispatch = {'true' if value else 'false'}"
    if re.search(r"(?m)^enabled_for_dispatch\s*=", section):
        section = re.sub(r"(?m)^enabled_for_dispatch\s*=.*$", line, section, count=1)
    else:
        insert_at = len(section.rstrip("\n"))
        section = section[:insert_at] + "\n" + line + section[insert_at:]
    path.write_text(text[:start] + section + text[end:], encoding="utf-8")
    try:
        from eduflow.runtime import tunables
        tunables.reset_cache()
    except Exception:
        pass


def _set_enabled(agent: str, value: bool, *, by: str, duration_s: int | None) -> dict:
    """Flip the runtime_registry override for enabled_for_dispatch."""
    if not config.agent_config(agent):
        raise KeyError(agent)
    _set_agent_dispatch_flag(agent, value)
    now = time.time()
    entry = {
        "ts": now,
        "agent": agent,
        "action": "unlock" if value else "lock",
        "by": by,
        "duration_s": duration_s,
        "expires_at": now + duration_s if (value and duration_s) else None,
    }
    _append_audit(entry)
    return entry


def _pop_flag(rest: list[str], flag: str) -> str | None:
    """Pop `flag <value>` from `rest`; return value or None. Removes both items."""
    if flag not in rest:
        return None
    i = rest.index(flag)
    if i + 1 >= len(rest):
        return None
    val = rest[i + 1]
    del rest[i:i + 2]
    return val


def main(argv: list[str]) -> int:
    if maybe_print_help(argv, USAGE):
        return 0
    if not argv:
        return usage_error(USAGE)
    sub = argv[0]
    if sub not in ("unlock", "lock"):
        return usage_error(USAGE)
    rest = list(argv[1:])

    # Flags can appear before or after the agent name; extract first.
    duration = None
    duration_raw = _pop_flag(rest, "--duration")
    if duration_raw is not None:
        duration = _parse_duration(duration_raw)
    explicit_by = _pop_flag(rest, "--by")

    if not rest or len(rest) != 1:
        return usage_error(USAGE)
    name = rest[0]

    try:
        cfg = config.agent_config(name)
    except KeyError:
        return error_exit(f"❌ unknown agent: {name}")
    value = (sub == "unlock")
    if duration is None and value:
        duration = 1800  # default 30min auto-lock

    # T-132: caller ID for audit. Source priority:
    #   1. --by <name> explicit flag (operator override)
    #   2. EDUFLOW_AGENT_CALLER env var (set by auto-spawned agents)
    #   3. EDUFLOW_USER or USER env var (human operator at terminal)
    #   4. "unknown" (caller can't be identified — better than the old
    #      hardcoded "manager" which silently mis-attributes every action)
    import os as _os
    caller = (
        explicit_by
        or _os.environ.get("EDUFLOW_AGENT_CALLER")
        or _os.environ.get("EDUFLOW_USER")
        or _os.environ.get("USER")
        or "unknown"
    )
    try:
        entry = _set_enabled(name, value, by=caller, duration_s=duration)
    except Exception as e:
        return error_exit(f"❌ failed: {e}")
    import eduflow.util as _u
    _u.print_json(entry)
    return 0
