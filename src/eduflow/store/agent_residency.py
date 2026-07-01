"""Per-agent residency bookkeeping.

Plan 2026-07-01 §设计二: persisting `last_active_at` /
`last_handoff_at` so the idle sweep can compute `idle_age_s` and
`since_handoff_s` without scanning the inbox / logs every cycle.

The store mirrors the schema in `runtime/residency.py`.  Two design
choices worth noting:

  - `last_active_at` is an explicit field, NOT derived from
    `heartbeats.json`.  Heartbeat is "did anything happen", but the
    sweep needs "since the last meaningful action" which is more
    conservative.  Worker-side `eduflow say` / `read --ack` /
    `send` paths bump this; the sweep reads it.

  - `last_handoff_at` is only stamped by callers (Phase 4 will wire
    the HandoffCard handler) — the sweep itself never sets it.  If
    it is missing, the sweep treats `since_handoff_s` as +inf and
    the handoff-buffer check is skipped (warm agent can sleep as
    soon as the idle threshold is crossed).

File-backed via `runtime/paths.facts_dir() / agent_residency.json`
(no DB, no extra dep).  All writes go through `util.write_json` so
they survive a power cycle.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from eduflow.runtime.paths import facts_dir as _facts_dir
from eduflow.util import read_json, write_json


def _file() -> Path:
    return _facts_dir() / "agent_residency.json"


def _now_s() -> float:
    return time.time()


def _load() -> dict[str, Any]:
    return read_json(_file(), {"agents": {}})


def _save(data: dict[str, Any]) -> None:
    write_json(_file(), data)


def get(agent: str) -> dict[str, Any] | None:
    """Return the residency row for `agent`, or None if never touched.

    The row shape is:
        {
          "last_active_at":  <epoch_s, optional>,
          "last_handoff_at": <epoch_s, optional>,
          "last_sleep_at":   <epoch_s, optional>,
          "last_wake_at":    <epoch_s, optional>,
        }
    Missing keys are absent, not None — callers must use `.get(key)`.
    """
    rows = _load().get("agents", {})
    row = rows.get(agent)
    if not isinstance(row, dict):
        return None
    return dict(row)


def all_rows() -> dict[str, dict[str, Any]]:
    return {name: dict(row) for name, row in _load().get("agents", {}).items()}


def touch_active(agent: str, *, when: float | None = None) -> None:
    """Stamp `last_active_at = now`.  Called by anything that wants
    to keep a warm agent awake: `eduflow say`, `read --ack started`,
    `send` to the agent, `task publish` that hands off to it, etc."""
    data = _load()
    row = data.setdefault("agents", {}).setdefault(agent, {})
    row["last_active_at"] = float(when if when is not None else _now_s())
    _save(data)


def touch_handoff(agent: str, *, when: float | None = None) -> None:
    """Stamp `last_handoff_at = now`.  Called when a HANDOFF or
    CLOSEOUT card lands for `agent` — starts the handoff buffer
    clock that delays the next sleep."""
    data = _load()
    row = data.setdefault("agents", {}).setdefault(agent, {})
    row["last_handoff_at"] = float(when if when is not None else _now_s())
    # A handoff is also an activity signal by definition.
    row["last_active_at"] = float(when if when is not None else _now_s())
    _save(data)


def touch_sleep(agent: str, *, when: float | None = None) -> None:
    """Stamp `last_sleep_at = now`.  Called by the sweep right before
    it sends Ctrl-C to the agent's pane.  Audit-only — does not gate
    the sleep decision (the sweep already decided)."""
    data = _load()
    row = data.setdefault("agents", {}).setdefault(agent, {})
    row["last_sleep_at"] = float(when if when is not None else _now_s())
    _save(data)


def touch_wake(agent: str, *, when: float | None = None) -> None:
    """Stamp `last_wake_at = now` AND `last_active_at = now`.  Called
    by `commands/send.py` and the lazy-wake path right after the
    CLI ready marker comes up.  Waking = activity, by definition."""
    data = _load()
    row = data.setdefault("agents", {}).setdefault(agent, {})
    now = float(when if when is not None else _now_s())
    row["last_wake_at"] = now
    row["last_active_at"] = now
    _save(data)


def age_since_active(agent: str, *, now: float | None = None) -> float:
    """Seconds since `last_active_at`.  Returns +inf when no row
    exists — a never-touched agent is treated as "idle forever" so
    the sweep retires it on the first cycle (that's the desired
    behaviour for a warm agent whose CLI is sitting idle from
    boot)."""
    row = get(agent)
    if not row:
        return float("inf")
    ts = row.get("last_active_at")
    if not isinstance(ts, (int, float)):
        return float("inf")
    return float(now if now is not None else _now_s()) - float(ts)


def age_since_handoff(agent: str, *, now: float | None = None) -> float:
    """Seconds since `last_handoff_at`.  Returns +inf when no
    handoff has been recorded — the sweep then skips the handoff-
    buffer check and lets the idle-timeout rule decide."""
    row = get(agent)
    if not row:
        return float("inf")
    ts = row.get("last_handoff_at")
    if not isinstance(ts, (int, float)):
        return float("inf")
    return float(now if now is not None else _now_s()) - float(ts)
