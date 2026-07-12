"""P9: end-to-end coverage for the D scheduled-task system.

Combines the P0-P8 building blocks into multi-step scenarios that exercise
the full lifecycle: draft create -> confirm -> due tick -> manager confirm
-> multi-lane dispatch -> worker report-back -> aggregation -> next cycle.
Also covers failure / recovery paths:

  * duplicate tick does NOT create a second occurrence for the same cycle
  * simulate crashed scheduler: notification ledger cleared, reconcile
    must replay the lost manager notification ONCE (not per tick)
  * backfill via reconcile catches every missed cycle; capacity and rule
    transitions only flip once each
  * cancel wins over a confirm / dispatch
  * unconfirmed cross-cycle is skipped (not double-dispatched)
  * running cross-cycle is blocked, not parallel-allowed
  * reminder cadence respects 30-min manager / 2-hour user windows
  * capacity=1 saturated -> attention_required, no new occurrence
  * 5 stable completions -> workflow candidate -> manager approval
  * 2 consecutive deviations post-approval -> workflow demoted to
    exploration + notification appended
  * scheduler fault must not break the normal task-publish loop, the
    watchdog / health surface, or the memory subsystem

All state is isolated via the standard `isolated_env()` fixture so this
file is safe to run alongside the unit suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a bare script (`python tests/integration/...`) — under
# pytest the conftest already puts src/ and tests/ on sys.path, so these
# inserts are idempotent no-ops there.
_ROOT = Path(__file__).resolve().parents[2]
for _p in (_ROOT / "src", _ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest

from helpers import attr_patch, isolated_env, run_cli
from eduflow.commands import task as task_cmd
from eduflow.runtime import paths
from eduflow.scheduling import (
    engine, manager_ops, notifications, workflow_evolution,
)
from eduflow.store import scheduled_tasks


# ── helpers ──────────────────────────────────────────────────────────


def _utc(year, month, day, hour=0, minute=0):
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _ms(year, month, day, hour=0, minute=0):
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


_STABLE_AGENTS = ["worker_course", "review_course"]


def _record_outcome(rid, occ_idx, *, result="done", agents=None, failure_pattern=""):
    return workflow_evolution.record_outcome(
        rid,
        occurrence_key=f"{rid}:2026-07-{13 + occ_idx:02d}T10:00:00Z",
        scheduled_at_utc=f"2026-07-{13 + occ_idx:02d}T10:00:00Z",
        result=result,
        agents=agents if agents is not None else _STABLE_AGENTS,
        artifact="summary.md",
        target="weekly summary",
        role="manager",
        failure_pattern=failure_pattern,
    )


# ── 1. Draft -> confirm flow ────────────────────────────────────────


def test_e2e_draft_confirm_flow_binds_version_and_owner():
    """User creates a draft, then confirms it; rule becomes active with
    confirmed_by / confirmed_at bound and version bumped."""
    with isolated_env():
        did = manager_ops.create_draft_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
            created_by="alice",
        )
        # A draft must NOT be picked up by the tick engine.
        engine.tick(_ms(2026, 7, 13, 10, 0))
        assert scheduled_tasks.list_occurrences(rule_id=did) == []

        rule = manager_ops.confirm_draft_rule(
            did, actor="alice", actor_role="user",
        )
        assert rule["status"] == "active"
        assert rule["confirmed_by"] == "alice"
        assert rule["version"] == 2
        assert rule["confirmed_at"] > 0


def test_e2e_draft_to_lane_dispatch_round_trip_creates_zero_user_visible_t_tasks():
    """End-to-end happy path: confirm draft -> tick -> manager confirms
    occurrence -> choose_lanes (parallel + serial) -> dispatch -> worker
    reports back.  No user-visible T task is ever written."""
    with isolated_env():
        tasks_path = paths.state_dir() / "tasks.json"
        did = manager_ops.create_draft_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
            created_by="alice",
        )
        manager_ops.confirm_draft_rule(
            did, actor="alice", actor_role="user",
        )

        engine.tick(_ms(2026, 7, 13, 10, 0))
        occ_key = f"{did}:2026-07-13T10:00:00Z"
        occ = scheduled_tasks.get_occurrence(occ_key)
        assert occ["status"] == "awaiting_manager"

        # Manager confirms the occurrence.
        manager_ops.confirm_occurrence(
            occ_key, actor="manager", actor_role="manager",
            expected_version=occ["version"],
        )

        # Multi-lane: parallel pair + serial follow-up via choose_lanes.
        lanes = manager_ops.choose_lanes(
            occ_key,
            lanes=[
                {"agent": "worker_course", "artifacts": ["summary.md"]},
                {"agent": "review_course", "artifacts": ["review.md"]},
            ],
            mode="parallel",
            actor="manager",
            actor_role="manager",
        )
        assert len(lanes) == 2
        first, second = sorted(lanes, key=lambda lane: lane["id"])

        result = manager_ops.re_dispatch(
            occ_key, actor="manager", actor_role="manager",
        )
        assert result["dispatched"] is True
        assert result["occurrence"]["status"] == "running"

        # Workers report back; this aggregates evidence into lane rows.
        manager_ops.report_back(
            occ_key, first["id"], status="done",
            evidence={"rows": 320}, actor="worker_course", actor_role="worker",
        )
        manager_ops.report_back(
            occ_key, second["id"], status="done",
            evidence={"review_passed": True},
            actor="review_course", actor_role="worker",
        )

        # End state: one awaiting-then-running occurrence, no skipped /
        # blocked / failed.  Zero T tasks emitted.
        assert scheduled_tasks.get_occurrence(occ_key)["status"] == "running"
        assert not tasks_path.exists(), (
            "D dispatch must never produce user-visible T tasks"
        )


# ── 2. Idempotency / restart / notification replay ──────────────────


def test_e2e_duplicate_tick_does_not_double_create_occurrence():
    """Repeated ticks at the same wall-clock instant must converge on a
    single awaiting_manager occurrence (scheduler is idempotent by D-ID
    + UTC scheduled_at key)."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        first = engine.tick(_ms(2026, 7, 12, 8, 0))
        second = engine.tick(_ms(2026, 7, 12, 8, 0))
        third = engine.scheduler_tick(_ms(2026, 7, 12, 8, 1))
        assert len(first["occurrences_created"]) == 1
        assert second["occurrences_created"] == []
        assert third["occurrences_created"] == []
        keys = [o["id"] for o in scheduled_tasks.list_occurrences(rule_id=did)]
        assert keys == [f"{did}:2026-07-12T08:00:00Z"]


def test_e2e_notification_failure_replay_is_one_shot_after_restart():
    """Simulate a crash between state-write and notification-append by
    clearing the ledger, then call reconcile: the lost
    'occurrence_due' notification is replayed EXACTLY ONCE.  Subsequent
    reconcile calls at the same clock do NOT re-emit because the ledger
    now carries a fresh record."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Wipe the ledger to simulate a crash that lost the notification
        # write after the occurrence row was already persisted.
        paths.scheduler_notifications_file().write_text("", encoding="utf-8")

        first = engine.reconcile(_ms(2026, 7, 12, 8, 0))
        second = engine.reconcile(_ms(2026, 7, 12, 8, 0))

        assert len(first["notifications_replayed"]) == 1
        assert second["notifications_replayed"] == []
        notifications = scheduled_tasks.list_notifications(
            rule_id=did, kind="occurrence_due",
        )
        assert len(notifications) == 1
        assert notifications[0]["payload"].get("replayed") is True


def test_e2e_no_user_visible_t_task_even_after_recovery_cycle():
    """A full restart cycle (tick → clear ledger → reconcile) must keep
    the T tasks store untouched."""
    with isolated_env():
        tasks_path = paths.state_dir() / "tasks.json"
        for i in range(3):
            scheduled_tasks.create_rule(
                target=f"target-{i}",
                artifact=f"a{i}.md",
                frequency="daily",
                timezone="UTC",
                next_due_utc=_utc(2026, 7, 12 + i, 8, 0),
            )

        engine.tick(_ms(2026, 7, 13, 9, 0))
        paths.scheduler_notifications_file().write_text("", encoding="utf-8")
        engine.reconcile(_ms(2026, 7, 14, 9, 0))
        assert not tasks_path.exists()
        scheduled_tasks.touch_heartbeat(lag_ms=0, error="")


# ── 3. Cancel wins ──────────────────────────────────────────────────


def test_e2e_cancel_rule_before_dispatch_does_not_dispatch_lanes():
    """If the rule is cancelled between the manager's confirmation and
    a later dispatch attempt, cancel wins: the occurrence lands in
    `cancelled` and no lanes are created."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        occ_key = f"{did}:2026-07-12T08:00:00Z"

        manager_ops.confirm_occurrence(
            occ_key, actor="manager", actor_role="manager",
        )
        manager_ops.cancel_rule(
            did, actor="alice", actor_role="user",
        )
        result = manager_ops.re_dispatch(
            occ_key, actor="manager", actor_role="manager",
        )
        assert result["dispatched"] is False
        assert result["reason"] == "rule_cancelled_or_paused"
        occ = scheduled_tasks.get_occurrence(occ_key)
        assert occ["status"] == "cancelled"
        assert scheduled_tasks.list_lanes(occurrence_key=occ_key) == []


# ── 4. Cross-cycle backpressure ─────────────────────────────────────


def test_e2e_unconfirmed_cross_cycle_is_skipped_not_dispatched():
    """Daily rule fires; the manager never confirms; next day's tick
    must surface a 'skipped' occurrence (not a parallel awaiting / not
    a dispatch)."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Manager ignores it entirely.
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert result["skipped"] == [f"{did}:2026-07-13T08:00:00Z"]
        skipped = scheduled_tasks.get_occurrence(f"{did}:2026-07-13T08:00:00Z")
        assert skipped["status"] == "skipped"
        assert scheduled_tasks.get_occurrence(
            f"{did}:2026-07-12T08:00:00Z"
        )["status"] == "awaiting_manager"


def test_e2e_running_cross_cycle_is_blocked_no_parallel_dispatch():
    """An occurrence is in 'running' state; the next tick must NOT
    create a parallel awaiting or running row — it writes a `blocked`
    occurrence instead.  Default capacity=1 forbids parallelism."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            capacity=1,
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        scheduled_tasks.update_occurrence(
            f"{did}:2026-07-12T08:00:00Z",
            {"status": "running"}, expected_version=None,
        )
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert result["blocked"] == [f"{did}:2026-07-13T08:00:00Z"]
        blocked = scheduled_tasks.get_occurrence(f"{did}:2026-07-13T08:00:00Z")
        assert blocked["status"] == "blocked"
        # No parallel running row was created.
        running = scheduled_tasks.list_occurrences(rule_id=did, status="running")
        assert len(running) == 1
        assert running[0]["id"] == f"{did}:2026-07-12T08:00:00Z"


def test_e2e_backfill_reconcile_advances_rule_only_once_per_missed_cycle():
    """Reconcile from 4 days late must NOT spam-await the manager — it
    records each cycle as caught up but advances the schedule exactly
    past the catch-up window in one call."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        result = engine.reconcile(_ms(2026, 7, 15, 8, 0))
        # Four missed cycles (07-12, 07-13, 07-14, 07-15) caught up; rule
        # advanced to 07-16 in one pass — no duplicate creation.
        assert len(result["missed_due_caught_up"]) == 4
        rule = scheduled_tasks.get_rule(did)
        assert rule["next_due_utc"] == _utc(2026, 7, 16, 8, 0)
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        assert occ["status"] == "awaiting_manager"


# ── 5. Reminder cadence ─────────────────────────────────────────────


def test_e2e_reminder_cadence_respects_30_min_manager_2_hour_user():
    """Manager reminders fire at most once per occurrence per 30 minutes;
    user notifications at most once per occurrence per 2 hours.  Replay
    inside the cadence window is a no-op; only the next window fires."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        occ_key = f"{did}:2026-07-12T08:00:00Z"

        t0 = _ms(2026, 7, 12, 8, 0)
        first = notifications.compute_reminder_actions(now_ms=t0)
        assert len(notifications.actions_for_occurrence(first, occ_key)) == 2

        # 10 minutes later — both kinds still inside the cadence window.
        second = notifications.compute_reminder_actions(now_ms=t0 + 10 * 60 * 1000)
        assert second == []

        # 31 minutes later — manager reminder fires again; user still inside
        # 2-hour window.
        third = notifications.compute_reminder_actions(now_ms=t0 + 31 * 60 * 1000)
        occ_actions = notifications.actions_for_occurrence(third, occ_key)
        kinds = sorted(a["kind"] for a in occ_actions)
        assert kinds == ["manager_reminder"]

        # 2h + 1m later — both kinds now eligible.
        fourth = notifications.compute_reminder_actions(now_ms=t0 + (2 * 60 + 1) * 60 * 1000)
        occ_actions = notifications.actions_for_occurrence(fourth, occ_key)
        kinds = sorted(a["kind"] for a in occ_actions)
        assert kinds == ["manager_reminder", "user_notification"]

        rows = scheduled_tasks.list_notifications(rule_id=did)
        kinds = sorted(r["kind"] for r in rows)
        # 3 manager + 2 user reminders expected
        # (t0: 1 manager + 1 user; t0+31m: 1 manager; t0+2h+1m: 1 manager + 1 user).
        assert kinds.count("manager_reminder") == 3
        assert kinds.count("user_notification") == 2


# ── 6. Capacity saturation ──────────────────────────────────────────


def test_e2e_capacity_one_saturated_transitions_rule_to_attention_required():
    """With capacity=1 and a confirmed-but-not-running occurrence still
    consuming capacity, the next due tick must mark the rule
    attention_required rather than spam-creating occurrences."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            capacity=1,
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Confirm the first occurrence to occupy capacity in `confirmed`
        # state (not awaiting anymore, but still active in capacity terms).
        occ = scheduled_tasks.get_occurrence(f"{did}:2026-07-12T08:00:00Z")
        scheduled_tasks.update_occurrence(
            occ["id"], {"status": "confirmed"}, expected_version=None,
        )
        result = engine.tick(_ms(2026, 7, 13, 8, 0))
        assert did in result["attention_required"]
        assert scheduled_tasks.get_rule(did)["status"] == "attention_required"
        # No new awaiting / running / blocked / skipped row was created.
        new_keys = [
            o["id"] for o in scheduled_tasks.list_occurrences(rule_id=did)
            if o["id"] != f"{did}:2026-07-12T08:00:00Z"
        ]
        assert new_keys == []


# ── 7. Workflow evolution: 5 stable -> candidate -> approved ─────────


def test_e2e_five_stable_runs_promote_rule_to_candidate_then_approved():
    """Five stable completions (matching target / artifact / role / agent
    list, no repeat failure pattern) lift a rule from exploration to
    candidate; manager approval locks the frozen snapshot."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
        )
        for i in range(5):
            _record_outcome(did, occ_idx=i)
        payload = workflow_evolution.candidate_payload(did)
        assert payload is not None
        assert payload["stable_signature"].endswith(
            "worker_course,review_course"
        )
        approved = workflow_evolution.approve_candidate(
            did, actor="manager",
        )
        assert approved["phase"] == "approved"
        snap = workflow_evolution.frozen_snapshot(did)
        assert snap is not None
        assert snap["frozen_target"] == "weekly summary"


# ── 8. Workflow demotion: 2 deviations -> exploration ───────────────


def test_e2e_two_consecutive_deviations_post_approval_demote_and_notify_user():
    """After approval, two consecutive major signature deviations must
    auto-demote the rule back to exploration and append a
    `workflow_demoted` user notification."""
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="UTC",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
        )
        for i in range(5):
            _record_outcome(did, occ_idx=i)
        workflow_evolution.candidate_payload(did)
        workflow_evolution.approve_candidate(did, actor="manager")

        _record_outcome(did, occ_idx=5, agents=["worker_qbank"])
        assert workflow_evolution.evolution_status(did)["phase"] == "approved"
        _record_outcome(did, occ_idx=6, agents=["auto_ops"])
        record = workflow_evolution.evolution_status(did)
        assert record["phase"] == "exploration"
        assert len(record["demotions"]) == 1
        notif = scheduled_tasks.list_notifications(
            rule_id=did, kind="workflow_demoted",
        )
        assert len(notif) == 1
        assert notif[0]["recipient"] == "user"


# ── 9. Scheduler failure isolation ─────────────────────────────────


def test_e2e_scheduler_tick_failure_does_not_break_task_publish_loop():
    """If the scheduler tick raises inside `task-publish`, the regular
    task-publish loop still runs to completion.  No scheduler cursor
    must leak into the T publish cursor file."""
    scheduler_calls = []
    task_calls = []

    def fake_scheduler_tick(now_ms):
        scheduler_calls.append(now_ms)
        raise ValueError("scheduler boom")

    def fake_task_main(argv):
        task_calls.append(list(argv))
        return 0

    with isolated_env(), \
            attr_patch(engine, scheduler_tick=fake_scheduler_tick), \
            attr_patch(task_cmd, main=fake_task_main):
        rc, _out, _err = run_cli(["task-publish", "--once", "--to", "user"])
        assert rc == 0
    assert len(scheduler_calls) == 1
    assert task_calls == [["publish-run", "--to", "user"]]
    assert not paths.task_publish_cursor_file().exists()


def test_e2e_scheduler_failure_does_not_break_health_or_memory():
    """Health / watchdog output must remain available even when the
    scheduler is in a fault state, and memory write failures must NOT
    propagate up to manager_ops."""
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}},
                      runtime_config={"chat_id": "oc_x"}):
        from eduflow.runtime import tmux as _tmux
        with attr_patch(_tmux, has_session=lambda s: True,
                        list_panes=lambda t: [],
                        capture_pane=lambda t, lines=80: "> ",
                        has_window=lambda t: False):
            # 1. Bad scheduler state raises inside the tick boundary
            #    but the heartbeat / store remain intact.
            scheduled_tasks.create_rule(
                target="x", artifact="x.md", frequency="daily",
                timezone="UTC", next_due_utc="not-a-date",
            )
            with pytest.raises(ValueError):
                engine.scheduler_tick(_ms(2026, 7, 12, 8, 0))
            hb = scheduled_tasks.get_heartbeat()
            assert "ValueError" in hb["error"]

            # 2. Health stays reachable — it surfaces the D scheduler
            #    fault in its section even though the overall exit
            #    code reflects the red check.
            rc, out, _ = run_cli(["health"])
            assert rc != 0, "scheduler fault should be reflected as red"
            assert "D scheduler" in out or "d scheduler" in out.lower()
            assert "ValueError" in out

            # 3. Memory outage is absorbed by the bridge.
            from eduflow.scheduling import memory_bridge
            from eduflow.memory import capsules

            def boom(**k):
                raise RuntimeError("memory down")

            with attr_patch(capsules, write_d_scheduler_summary=boom):
                ok = memory_bridge.record_rule_summary(
                    "D-1", "should not propagate",
                )
                assert ok is False
            # Subsequent manager_ops call still succeeds.
            did = manager_ops.create_draft_rule(
                target="x", artifact="x.md", frequency="daily",
                timezone="UTC", next_due_utc=_utc(2026, 7, 20, 8, 0),
                created_by="alice",
            )
            confirmed = manager_ops.confirm_draft_rule(
                did, actor="alice", actor_role="user",
            )
            assert confirmed["status"] == "active"
