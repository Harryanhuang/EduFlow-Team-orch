"""P8: D scheduled-task workflow evolution.

Workflow evolution is observation + promotion logic only.  It never
dispatches agents, never writes T tasks, never touches the T state
machine, and never promotes a candidate into the active workflow
registry on its own.  Manager confirmation stays external: every D
cycle still requires manager confirmation, even after this module
returns a candidate payload.

Per-rule phases:

    exploration ──≥5 stable completions──▶ candidate
        ▲                                      │
        │                                  approve (manager closeout)
        │                                      ▼
       demotion ◀────2 consecutive dev/fail──── approved

A run is "stable" when the most recent
``DEFAULT_STABLE_RUN_THRESHOLD`` (default 5) completion entries share
the same signature ``(target, artifact, role, ordered lane agents)``
AND no ``failure_pattern`` is repeated across ≥2 of those entries
(which would indicate an unresolved repeat failure).

A deviation is either:

  * ``major_deviation`` — recorded signature differs from the frozen
    snapshot signature;
  * ``major_failure``   — outcome ``failed`` or non-empty
                         ``failure_pattern``;
  * ``explicit``        — manager / operator explicitly called
                         ``record_deviation``.

When the rule is in ``approved`` phase and the deviation streak
reaches ``DEFAULT_DEVIATION_THRESHOLD`` (default 2), the rule
auto-demotes back to ``exploration`` and a ``workflow_demoted``
notification is appended to the manager_ops ledger so the user is
informed.

Healthy review is flagged when, in ``approved`` phase, EITHER
``now - last_review_at`` ≥ 30 days, OR
``since_review_count`` ≥ 10 successful runs.  ``record_health_review``
resets both counters.

``worker_builder`` maintenance of T workflow assets
(``docs/workflows/<id>``) is a separate domain.  This module observes
D-side outcomes only and returns a candidate payload dict that
operator tooling hands to ``worker_builder`` for asset drafting.
"""
from __future__ import annotations

import re
from pathlib import Path

from eduflow.runtime import paths
from eduflow.store import scheduled_tasks
from eduflow.util import flock, now_ms, read_json, write_json


PHASES = ("exploration", "candidate", "approved")

DEFAULT_STABLE_RUN_THRESHOLD = 5
DEFAULT_DEVIATION_THRESHOLD = 2
DEFAULT_HEALTH_REVIEW_RUNS = 10
DEFAULT_HEALTH_REVIEW_DAYS_MS = 30 * 24 * 60 * 60 * 1000
REPEAT_FAILURE_THRESHOLD = 2

# Outcomes routed through ``record_outcome``.
VALID_RESULTS = frozenset({"done", "skipped", "failed", "cancelled"})

SUCCESS_RESULTS = frozenset({"done"})
FAILURE_RESULTS = frozenset({"failed"})


TRANSITIONS = {
    "exploration": frozenset({"candidate", "exploration"}),
    "candidate": frozenset({"approved", "exploration"}),
    "approved": frozenset({"exploration"}),
}


class PhaseError(Exception):
    """Raised when an evolution phase transition is not allowed."""


class NotFound(Exception):
    """Raised when the rule has no evolution record."""


# ── storage ──────────────────────────────────────────────────────────


def _evolution_file() -> Path:
    return paths.scheduler_dir() / "evolution.json"


def _evolution_lock():
    return flock(_evolution_file().with_suffix(".lock"))


def _load_evolution() -> dict:
    return read_json(
        _evolution_file(),
        {"_meta": {"version_counter": 0}, "rules": {}},
    )


def _save_evolution(state: dict) -> None:
    state.setdefault("_meta", {})["version_counter"] = (
        state["_meta"].get("version_counter", 0) + 1
    )
    write_json(_evolution_file(), state)


def _empty_record() -> dict:
    return {
        "phase": "exploration",
        "completion_history": [],
        "candidate": None,
        "approved": None,
        "demotions": [],
        "deviation_streak": {"count": 0, "last_kind": "", "events": []},
        "health_review": {
            "since_review_count": 0,
            "last_review_at": 0,
            "last_review_by": "",
            "history": [],
        },
        "created_at": now_ms(),
        "updated_at": now_ms(),
    }


def _get_record(state: dict, rule_id: str, *, create: bool = False) -> dict | None:
    rules = state.setdefault("rules", {})
    record = rules.get(rule_id)
    if record is None and create:
        record = _empty_record()
        rules[rule_id] = record
    return record


def _stable_signature(target: str, artifact: str, role: str, agents: list[str]) -> str:
    return f"{target}|{artifact}|{role}|{','.join(agents or [])}"


def _set_phase(record: dict, new_phase: str) -> None:
    allowed = TRANSITIONS.get(record["phase"], frozenset())
    if new_phase not in allowed:
        raise PhaseError(
            f"cannot transition {record['phase']} -> {new_phase} "
            f"(allowed: {sorted(allowed)})"
        )
    record["phase"] = new_phase
    record["updated_at"] = now_ms()


def _slug_candidate(rule_id: str, target: str) -> str:
    """Produce a candidate ``workflow_id`` hint from a D rule and target.

    The result is a hint only — the manager / worker_builder pick the
    final id during promotion.  Slug keeps D-rule lineage visible in
    the active registry.
    """
    suffix = re.sub(r"[^a-z0-9-]+", "-", (target or "").lower()).strip("-")
    if not suffix:
        suffix = "d-rule"
    if len(suffix) > 40:
        suffix = suffix[:40].rstrip("-")
    rule_slug = (rule_id or "").lower().replace(" ", "-")
    return f"{rule_slug}-{suffix}"


# ── public API ───────────────────────────────────────────────────────


def evolution_status(rule_id: str) -> dict | None:
    """Return the raw evolution record for a rule, or ``None`` if no
    outcome has been recorded yet.  Read-only; no side effects."""
    state = _load_evolution()
    record = _get_record(state, rule_id)
    return dict(record) if record is not None else None


def frozen_snapshot(rule_id: str) -> dict | None:
    """Return the approved frozen snapshot dict, or ``None`` when the
    rule has not been approved.  A frozen snapshot is a reference
    asset only — this module never executes it."""
    record = evolution_status(rule_id)
    if record is None:
        return None
    approved = record.get("approved")
    return dict(approved) if approved else None


def record_outcome(
    rule_id: str, *,
    occurrence_key: str,
    scheduled_at_utc: str,
    result: str,
    agents: list[str] | None = None,
    artifact: str = "",
    target: str = "",
    role: str = "manager",
    failure_pattern: str = "",
) -> dict:
    """Record a confirmed D occurrence outcome.

    Routing per outcome (in ``approved`` phase):
      * ``done``   — increments the success counter; resets deviation
                     streak to 0 (since the previous window cleared);
      * ``failed`` — increments deviation streak; if streak ≥ 2 the
                     rule auto-demotes and a ``workflow_demoted``
                     notification is appended;
      * ``skipped`` / ``cancelled`` — neutral, no streak change.

    Signature mismatch against the frozen snapshot counts as a
    major_deviation too (even when ``result`` is ``done``).

    Returns the updated evolution record.  This function never
    dispatches agents and never writes T tasks.
    """
    if not rule_id:
        raise ValueError("rule_id is required")
    if result not in VALID_RESULTS:
        raise ValueError(f"invalid result: {result!r}")
    agents = list(agents or [])

    with _evolution_lock():
        state = _load_evolution()
        record = _get_record(state, rule_id, create=True)
        signature = _stable_signature(target, artifact, role, agents)
        entry = {
            "occurrence_key": occurrence_key,
            "scheduled_at_utc": scheduled_at_utc,
            "recorded_at": now_ms(),
            "result": result,
            "signature": signature,
            "target": target,
            "artifact": artifact,
            "role": role,
            "agents": list(agents),
            "failure_pattern": failure_pattern,
        }
        record["completion_history"].append(entry)

        streak = record["deviation_streak"]
        if record["phase"] == "approved":
            approved = record.get("approved") or {}
            frozen_sig = approved.get("frozen_signature", "")
            sig_deviation = bool(frozen_sig) and signature != frozen_sig
            failure_signal = result in FAILURE_RESULTS or bool(failure_pattern)
            if sig_deviation or failure_signal:
                streak["count"] = int(streak.get("count", 0)) + 1
                if failure_signal and sig_deviation:
                    streak["last_kind"] = "major_deviation+major_failure"
                elif failure_signal:
                    streak["last_kind"] = "major_failure"
                else:
                    streak["last_kind"] = "major_deviation"
                streak.setdefault("events", []).append({
                    "kind": streak["last_kind"],
                    "occurrence_key": occurrence_key,
                    "at": entry["recorded_at"],
                })
                if streak["count"] >= DEFAULT_DEVIATION_THRESHOLD:
                    demotion_reason = (
                        f"{streak['count']}_consecutive_{streak['last_kind']}"
                    )
                    _set_phase(record, "exploration")
                    record["demotions"].append({
                        "reason": demotion_reason,
                        "at": entry["recorded_at"],
                        "last_kind": streak["last_kind"],
                        "occurrence_key": occurrence_key,
                    })
                    scheduled_tasks.append_notification(
                        rule_id, "user", "workflow_demoted",
                        occurrence_key=occurrence_key,
                        payload={
                            "phase": "exploration",
                            "reason": streak["last_kind"],
                            "rule_id": rule_id,
                        },
                    )
                    # Reset transient counters; demotion audit
                    # preserves the event for review.
                    streak["count"] = 0
                    streak["last_kind"] = ""
            elif result in SUCCESS_RESULTS:
                streak["count"] = 0
                streak["last_kind"] = ""

        # Health-review counter: only counts done outcomes while in
        # approved phase.
        if record["phase"] == "approved" and result in SUCCESS_RESULTS:
            hr = record["health_review"]
            hr["since_review_count"] = (
                int(hr.get("since_review_count", 0)) + 1
            )

        record["updated_at"] = now_ms()
        _save_evolution(state)
        return dict(record)


def candidate_payload(rule_id: str) -> dict | None:
    """Return a candidate workflow spec when ≥5 stable completions exist.

    Stability rules:
      * The last ``DEFAULT_STABLE_RUN_THRESHOLD`` (default 5) entries
        in ``completion_history`` share a single signature.
      * No ``failure_pattern`` repeats across ≥2 of those entries
        (which would indicate an unresolved repeat failure).

    Idempotent: once the rule enters ``candidate`` phase, repeated
    calls return the same stored payload until manager approval or
    manual reset.  Returns ``None`` when the rule is not in
    ``exploration`` (or ``candidate``, in the idempotent return sense
    returns the stored payload).
    """
    with _evolution_lock():
        state = _load_evolution()
        record = _get_record(state, rule_id)
        if record is None:
            return None
        if record["phase"] == "candidate":
            existing = record.get("candidate")
            return dict(existing) if existing else None
        if record["phase"] != "exploration":
            return None
        history = list(record.get("completion_history", []))
        if len(history) < DEFAULT_STABLE_RUN_THRESHOLD:
            return None
        window = history[-DEFAULT_STABLE_RUN_THRESHOLD:]
        signatures = {entry["signature"] for entry in window}
        if len(signatures) != 1:
            return None
        failure_counts: dict[str, int] = {}
        for entry in window:
            pattern = entry.get("failure_pattern", "") or ""
            if pattern:
                failure_counts[pattern] = failure_counts.get(pattern, 0) + 1
        if any(c >= REPEAT_FAILURE_THRESHOLD for c in failure_counts.values()):
            return None
        first = window[0]
        candidate = {
            "workflow_id_hint": _slug_candidate(rule_id, first["target"]),
            "stable_signature": first["signature"],
            "target": first["target"],
            "artifact": first["artifact"],
            "role": first["role"],
            "agents": list(first["agents"]),
            "primary_chain": (
                "manager -> " + " -> ".join(first["agents"]) + " -> manager"
            ),
            "evidence_occurrence_keys": [
                e["occurrence_key"] for e in window
            ],
            "produced_at": now_ms(),
            "boundary": (
                "candidate workflow only; worker_builder drafts the asset "
                "and manager closeout must approve promotion before this "
                "workflow becomes active. The active workflow is a frozen "
                "snapshot, not an auto-dispatcher; every D cycle still "
                "requires manager confirmation."
            ),
        }
        _set_phase(record, "candidate")
        record["candidate"] = candidate
        record["updated_at"] = now_ms()
        _save_evolution(state)
        return dict(candidate)


def approve_candidate(rule_id: str, *, actor: str, approved_at: int | None = None) -> dict:
    """Move a rule from ``candidate`` → ``approved`` and store the
    frozen snapshot.

    After this call, the workflow is a FROZEN SNAPSHOT only — every
    D cycle still requires manager confirmation.  Two consecutive
    major deviations or failures auto-demote the rule back to
    ``exploration``.

    ``approved_at`` overrides the wall-clock timestamp stored on the
    frozen payload and on the health-review baseline.  When omitted,
    ``now_ms()`` is used.  The test layer relies on this injection
    point to drive time-based thresholds (healthy review windows,
    demotion timestamps) deterministically.

    Raises ``PhaseError`` when the rule is not in ``candidate``
    phase, and ``ValueError`` when ``actor`` is empty.
    """
    if not actor:
        raise ValueError("actor is required")
    at = int(approved_at) if approved_at is not None else now_ms()
    with _evolution_lock():
        state = _load_evolution()
        record = _get_record(state, rule_id)
        if record is None or record["phase"] != "candidate":
            current = record["phase"] if record is not None else "missing"
            raise PhaseError(
                f"cannot approve when phase={current!r} "
                f"(must be 'candidate')"
            )
        candidate = record.get("candidate") or {}
        frozen_signature = candidate.get("stable_signature", "")
        approved_payload = {
            "approved_by": actor,
            "approved_at": at,
            "frozen_signature": frozen_signature,
            "frozen_target": candidate.get("target", ""),
            "frozen_artifact": candidate.get("artifact", ""),
            "frozen_role": candidate.get("role", ""),
            "frozen_agents": list(candidate.get("agents", [])),
            "frozen_primary_chain": candidate.get("primary_chain", ""),
            "workflow_id_hint": candidate.get("workflow_id_hint", ""),
            "evidence_occurrence_keys": list(
                candidate.get("evidence_occurrence_keys", [])
            ),
            "boundary": (
                "frozen snapshot only; not an auto-dispatcher. Every D "
                "cycle still requires manager confirmation. 2 "
                "consecutive major deviations or failures auto-demote "
                "back to exploration."
            ),
        }
        _set_phase(record, "approved")
        record["approved"] = approved_payload
        record["deviation_streak"] = {
            "count": 0, "last_kind": "", "events": [],
        }
        record["health_review"] = {
            "since_review_count": 0,
            "last_review_at": at,
            "last_review_by": "",
            "history": [],
        }
        record["updated_at"] = at
        _save_evolution(state)
        return dict(record)


def record_deviation(rule_id: str, *, note: str = "") -> dict:
    """Manager / operator explicit deviation marker.

    Counts only when the rule is in ``approved`` phase.  Mirrors the
    streak semantics inside ``record_outcome``: when the streak
    reaches ``DEFAULT_DEVIATION_THRESHOLD`` (default 2), the rule
    auto-demotes back to ``exploration`` and a ``workflow_demoted``
    notification is appended.
    """
    with _evolution_lock():
        state = _load_evolution()
        record = _get_record(state, rule_id, create=True)
        if record["phase"] != "approved":
            record["updated_at"] = now_ms()
            _save_evolution(state)
            return dict(record)
        streak = record["deviation_streak"]
        streak["count"] = int(streak.get("count", 0)) + 1
        streak["last_kind"] = "explicit"
        streak.setdefault("events", []).append({
            "kind": "explicit",
            "note": note,
            "at": now_ms(),
        })
        if streak["count"] >= DEFAULT_DEVIATION_THRESHOLD:
            _set_phase(record, "exploration")
            record["demotions"].append({
                "reason": f"{streak['count']}_consecutive_explicit",
                "at": now_ms(),
                "last_kind": "explicit",
                "note": note,
            })
            scheduled_tasks.append_notification(
                rule_id, "user", "workflow_demoted",
                occurrence_key=None,
                payload={"phase": "exploration", "reason": "explicit"},
            )
            streak["count"] = 0
            streak["last_kind"] = ""
        record["updated_at"] = now_ms()
        _save_evolution(state)
        return dict(record)


def health_review_due(
    rule_id: str, *,
    now: int,
    review_run_threshold: int = DEFAULT_HEALTH_REVIEW_RUNS,
    review_window_ms: int = DEFAULT_HEALTH_REVIEW_DAYS_MS,
) -> bool:
    """Return ``True`` when an approved rule needs a healthy review.

    Triggers when EITHER:
      * ``now - last_review_at`` (or approval time when never
        reviewed) ≥ ``DEFAULT_HEALTH_REVIEW_DAYS_MS`` (default 30
        days), OR
      * ``since_review_count`` ≥ ``DEFAULT_HEALTH_REVIEW_RUNS``
        (default 10).

    Rules in other phases always return ``False``.
    """
    state = _load_evolution()
    record = _get_record(state, rule_id)
    if record is None or record["phase"] != "approved":
        return False
    hr = record.get("health_review") or {}
    last_review_at = int(hr.get("last_review_at", 0) or 0)
    since_count = int(hr.get("since_review_count", 0) or 0)
    if last_review_at <= 0:
        approved = record.get("approved") or {}
        last_review_at = int(approved.get("approved_at", 0) or 0)
    if last_review_at <= 0:
        return since_count >= review_run_threshold
    if int(now) - last_review_at >= review_window_ms:
        return True
    if since_count >= review_run_threshold:
        return True
    return False


def record_health_review(rule_id: str, *, actor: str, now: int) -> dict:
    """Reset health-review counters so the next review window starts
    at ``now``.  No-op when the rule is not in ``approved`` phase.
    Returns the updated record (or a synthetic stub when no record
    exists yet)."""
    if not actor:
        raise ValueError("actor is required")
    with _evolution_lock():
        state = _load_evolution()
        record = _get_record(state, rule_id)
        if record is None or record["phase"] != "approved":
            if record is None:
                return {"phase": "missing", "rule_id": rule_id}
            return dict(record)
        hr = record["health_review"]
        hr["since_review_count"] = 0
        hr["last_review_at"] = int(now)
        hr["last_review_by"] = actor
        hr.setdefault("history", []).append({
            "actor": actor,
            "at": int(now),
        })
        record["updated_at"] = now_ms()
        _save_evolution(state)
        return dict(record)
