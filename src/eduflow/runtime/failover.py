"""Cross-pool failover orchestration — shared by the watchdog daemon and
`feishu/deliver.py`.

Both code paths used to inline the same "detect failure → pick next
fallback → call restart_with_runtime → record state" loop. Duplicating
it meant bug fixes (e.g. cross-pool priority, proved-ready gate, event
logging) had to land in two places. This module is the single source:

    result = execute_fallback_loop(agent, target, current_runtime, reason)
    # result == {outcome, to_runtime, attempts, events, exhausted}

`outcome` is the lifecycle outcome string of the LAST attempt (so
`ready`/`ready_no_init`/`env_drift`/`smoke_failed`/`spawn_failed`/
`config_error`/`ready_unproven`). Callers that need to distinguish
"fully recovered" from "recovered-but-unverified" check `outcome ==
'ready'` directly.

Cross-pool priority: the loop asks `config.fallback_runtime` with
`avoid_pool_id` set to the original runtime's pool, so the first
attempt prefers a genuinely different provider. If no cross-pool
candidate exists, subsequent iterations drop the avoidance and allow
same-pool fallback — better to retry a degraded pool than give up.
"""
from __future__ import annotations

import time
import uuid

from eduflow.runtime import config, coordinator, human_takeover, lifecycle, verify


# Sentinel for "no fallback matched" — distinct from any lifecycle outcome.
EXHAUSTED = "fallback_exhausted"


def runtime_pool_id(runtime_name: str) -> str:
    """Return the pool_id of `runtime_name`'s env_profile, or "" if
    unresolvable. Empty string means "unknown pool" — callers treat it
    as non-matching (i.e. any fallback is cross-pool relative to it).
    """
    if not runtime_name or runtime_name == "inline":
        return ""
    try:
        rt = config.runtime_config(runtime_name)
    except KeyError:
        return ""
    env_profile_name = str(rt.get("env_profile") or "")
    if not env_profile_name:
        return ""
    try:
        profile = config.env_profile_config(env_profile_name)
    except KeyError:
        return ""
    return str(profile.get("pool_id") or "")


def _first_successful_outcome(outcomes: list[str]) -> str:
    """Pick the strongest success outcome seen across attempts.

    Lifecycle returns READY on full success and various failure strings
    on partial/total failure. When the loop retries after a soft
    failure (env_drift, smoke_failed), the operator wants the BEST
    outcome achieved, not just the last one.
    """
    priority = {
        "ready": 6,
        "ready_no_init": 5,
        "ready_unproven": 4,
        "env_drift": 3,
        "smoke_failed": 2,
        "spawn_failed": 1,
        "config_error": 0,
        EXHAUSTED: -1,
    }
    best = EXHAUSTED
    for o in outcomes:
        if priority.get(o, -1) > priority.get(best, -1):
            best = o
    return best


def execute_fallback_loop(
    agent: str,
    target,
    current_runtime: str,
    reason: str,
    *,
    max_attempts: int = 3,
    restart_fn=None,
    record_fn=None,
    now_fn=None,
    can_switch_fn=None,
    record_switch_fn=None,
    trigger: str = "auto",
    automation_guard_fn=None,
) -> dict:
    """Run the failover loop for one agent and return a structured report.

    Returns a dict:
      outcome      — lifecycle outcome of the LAST attempt (or EXHAUSTED)
      to_runtime   — runtime name of the LAST attempt (or "")
      best_outcome — strongest outcome across all attempts
      attempts     — list of {to_runtime, outcome, env_ok, smoke_ok, ts}
      events       — list of event dicts actually recorded
      exhausted    — True iff no further fallback candidates remain
      pool_switched— True iff at least one attempt had a different pool_id
                     than the starting runtime

    Injectable callables for tests:
      restart_fn(agent, target, runtime_name, reason, prove_ready) → str
      record_fn(event_dict) → None
      now_fn() → float
      can_switch_fn(pool_id) → bool
      record_switch_fn(pool_id, agent) → None
    """
    restart_fn = restart_fn or lifecycle.restart_with_runtime
    record_fn = record_fn or verify.record_switch_event
    now_fn = now_fn or time.time
    can_switch_fn = can_switch_fn or coordinator.can_switch_to_pool
    record_switch_fn = record_switch_fn or coordinator.record_pool_switch
    automation_guard_fn = automation_guard_fn or human_takeover.ensure_automation_allowed

    initial_pool = runtime_pool_id(current_runtime)
    outcomes: list[str] = []
    attempts: list[dict] = []
    events: list[dict] = []
    pool_switched = False
    switch_id = str(uuid.uuid4())[:8]

    last_runtime = current_runtime
    # First pass: prefer cross-pool fallbacks. If the starting runtime has
    # a known pool, avoid it explicitly. If it has no pool (e.g. qoder
    # with no env_profile), prefer any candidate that does have a pool —
    # they can't share quota with an un-pooled runtime. If none exists,
    # we'll fall back to same-pool / un-pooled below.
    avoid_pool = initial_pool
    prefer_nonempty = not initial_pool

    for attempt_idx in range(max_attempts):
        try:
            fallback = config.fallback_runtime(
                agent,
                current_runtime=last_runtime,
                reason=reason,
                avoid_pool_id=avoid_pool,
                prefer_nonempty_pool=prefer_nonempty if not avoid_pool else False,
            )
        except KeyError:
            fallback = None

        # If the cross-pool-avoiding lookup returned nothing but we were
        # avoiding, retry once without avoidance so a same-pool fallback
        # is still tried before giving up entirely.
        if fallback is None and (avoid_pool or prefer_nonempty):
            try:
                fallback = config.fallback_runtime(
                    agent,
                    current_runtime=last_runtime,
                    reason=reason,
                    avoid_pool_id="",
                    prefer_nonempty_pool=False,
                )
            except KeyError:
                fallback = None
            avoid_pool = ""
            prefer_nonempty = False  # only retry once

        if not fallback:
            break

        fallback_name = str(fallback.get("name", ""))
        if not fallback_name:
            break

        fallback_pool = runtime_pool_id(fallback_name)
        # Cross-pool detection: when the starting runtime has no pool
        # (e.g. qoder with no env_profile), any fallback with a known
        # pool is treated as cross-pool — they can't share quota.
        if (initial_pool and fallback_pool and fallback_pool != initial_pool) or \
           (not initial_pool and fallback_pool):
            pool_switched = True

        # Pool-level rate limit: prevent multiple agents from flooding the
        # same fallback pool when they all fail at once.
        if not can_switch_fn(fallback_pool):
            outcomes.append("pool_rate_limited")
            attempts.append({
                "to_runtime": fallback_name,
                "outcome": "pool_rate_limited",
                "env_ok": False,
                "smoke_ok": False,
                "pool_id": fallback_pool,
                "ts": now_fn(),
            })
            last_runtime = fallback_name
            avoid_pool = ""
            prefer_nonempty = False
            continue

        # Shared last-moment circuit breaker.  This lives in the common loop,
        # not in a caller, so watchdog and deliver (and every retry) are
        # protected from a takeover race before the restart side effect.
        automation_guard_fn()
        now = now_fn()
        outcome = restart_fn(
            agent,
            target,
            fallback_name,
            reason=f"{trigger}:{reason}" if trigger else reason,
            prove_ready=True,
        )

        env_ok = outcome in {"ready", "ready_no_init", "ready_unproven"}
        smoke_ok = outcome in {"ready", "ready_no_init"}
        attempt = {
            "to_runtime": fallback_name,
            "outcome": outcome,
            "env_ok": env_ok,
            "smoke_ok": smoke_ok,
            "pool_id": fallback_pool,
            "ts": now,
        }
        attempts.append(attempt)
        outcomes.append(outcome)

        event = {
            "ts": now,
            "switch_id": switch_id,
            "agent": agent,
            "from_runtime": last_runtime,
            "to_runtime": fallback_name,
            "reason": reason,
            "trigger": trigger,
            "outcome": outcome,
            "best_outcome": _first_successful_outcome(outcomes),
            "attempts": [dict(a) for a in attempts],
            "pool_switched": pool_switched,
            "cross_pool": bool((initial_pool and fallback_pool and fallback_pool != initial_pool)
                               or (not initial_pool and fallback_pool)),
            "env_ok": env_ok,
            "smoke_ok": smoke_ok,
            "pool_id": fallback_pool,
        }
        record_fn(**event)
        events.append(event)

        if outcome in {"ready", "ready_no_init"}:
            record_switch_fn(fallback_pool, agent)
            return {
                "outcome": outcome,
                "to_runtime": fallback_name,
                "best_outcome": outcome,
                "attempts": attempts,
                "events": events,
                "exhausted": False,
                "pool_switched": pool_switched,
            }
        # Outcome was a failure — continue with this runtime as the new
        # `current`, but DO NOT avoid its pool on the next iteration
        # (the whole point of the next iteration is to try somewhere
        # else).
        last_runtime = fallback_name
        avoid_pool = ""  # don't re-avoid; the chain pointer advances naturally
        prefer_nonempty = False

    # Loop ended without a clean READY — compose a failure report.
    best = _first_successful_outcome(outcomes) if outcomes else EXHAUSTED
    return {
        "outcome": outcomes[-1] if outcomes else EXHAUSTED,
        "to_runtime": attempts[-1]["to_runtime"] if attempts else "",
        "best_outcome": best,
        "attempts": attempts,
        "events": events,
        "exhausted": True,
        "pool_switched": pool_switched,
    }
