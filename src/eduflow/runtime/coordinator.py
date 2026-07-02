"""Pool-level switch rate limiting for failover coordination.

When multiple agents hit failures simultaneously, they may all try to
switch into the same fallback pool at once, exhausting that pool's
quota instantly.  This module tracks recent pool switches and gates
new ones behind a sliding-window rate limit.

State lives in `coordinator_state.json` under the eduflow state dir.
Missing file means "no prior switches" — all switches allowed — so
existing deployments keep working unchanged.
"""
from __future__ import annotations

import time

from eduflow.runtime import paths, tunables
from eduflow.util import file_lock, read_json, write_json


def _state_path():
    return paths.state_file("coordinator_state.json")


def _load():
    try:
        return read_json(_state_path(), {})
    except Exception:
        return {}


def _save(data):
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, data)


def _pool_window_s() -> int:
    return int(tunables.tunable("coordinator.pool_window_s", 60))


def _pool_max_switches() -> int:
    return int(tunables.tunable("coordinator.pool_max_switches", 2))


def can_switch_to_pool(pool_id: str, *, window_s: int | None = None,
                       max_switches: int | None = None) -> bool:
    """True if another agent can switch to this pool within the rate limit window.

    Returns True when the pool has fewer than `max_switches` switches
    recorded within the last `window_s` seconds.  Empty pool_id always
    returns True (un-pooled runtimes have no shared quota to protect).
    """
    if not pool_id:
        return True
    window_s = window_s if window_s is not None else _pool_window_s()
    max_switches = max_switches if max_switches is not None else _pool_max_switches()
    with file_lock(_state_path()):
        data = _load()
        row = data.get("pools", {}).get(pool_id, {})
        ts = time.time()
        recent = [t for t in row.get("switches", []) if ts - t <= window_s]
        return len(recent) < max_switches


def record_pool_switch(pool_id: str, agent: str) -> None:
    """Record that `agent` switched into `pool_id` right now.

    Prunes the switch history to the last 20 entries per pool so the
    state file doesn't grow without bound.
    """
    if not pool_id:
        return
    with file_lock(_state_path()):
        data = _load()
        pools = data.setdefault("pools", {})
        row = pools.setdefault(pool_id, {"switches": [], "agents": {}})
        row["switches"].append(time.time())
        row["switches"] = row["switches"][-20:]
        row["agents"][agent] = time.time()
        _save(data)
