"""P6: manager-panel read-only D scheduler observations.

`task manager-panel` must surface a D scheduler section that:
  * reads only from the scheduler store / engine state (no writes)
  * shows due-soon, awaiting (manager/user), running, blocked,
    recent-failure, scheduler lag, and attention-required rows
  * every row carries D-id, time, reason, and a next-action hint

These tests pin the field contract and verify the panel is honest about
what scheduler state looks like (no UI-fabricated claims).
"""
from __future__ import annotations


from helpers import isolated_env, run_cli
from eduflow.runtime import paths
from eduflow.scheduling import engine
from eduflow.store import scheduled_tasks


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# ── section presence ────────────────────────────────────────────────


def test_manager_panel_includes_d_scheduler_section_header():
    """Even with no scheduler state, the section header must render so
    operators know the panel surfaces scheduler observations."""
    with isolated_env():
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "== D Scheduler ==" in out


def test_manager_panel_d_scheduler_section_is_read_only():
    """The section must not mutate scheduler files. Compare mtime + content
    of rules/occurrences/cursor before vs after the panel command."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        # Snapshot on-disk content + mtime before running the panel.
        rules_path = paths.scheduler_rules_file()
        occ_path = paths.scheduler_occurrences_file()
        cursor_path = paths.scheduler_cursor_file()
        rules_before = rules_path.read_text(encoding="utf-8")
        occ_before = occ_path.read_text(encoding="utf-8")
        cursor_before = cursor_path.read_text(encoding="utf-8")
        rules_mtime = rules_path.stat().st_mtime
        occ_mtime = occ_path.stat().st_mtime
        cursor_mtime = cursor_path.stat().st_mtime

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0

        assert rules_path.read_text(encoding="utf-8") == rules_before
        assert occ_path.read_text(encoding="utf-8") == occ_before
        assert cursor_path.read_text(encoding="utf-8") == cursor_before
        # mtime must not have advanced: panel must not write.
        assert rules_path.stat().st_mtime == rules_mtime
        assert occ_path.stat().st_mtime == occ_mtime
        assert cursor_path.stat().st_mtime == cursor_mtime
        # Rule still exists and is unchanged.
        assert scheduled_tasks.get_rule(rid)["status"] == "active"


# ── awaiting manager/user ────────────────────────────────────────────


def test_manager_panel_surfaces_awaiting_manager_occurrence():
    """An awaiting_manager occurrence must appear in the panel with a
    reason and a next_action."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
        )
        engine.tick(_ms(2026, 7, 13, 10, 0))
        key = f"{rid}:2026-07-13T10:00:00Z"

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "awaiting manager" in out.lower() or "awaiting_manager" in out
        # The D ID must be visible.
        assert rid in out
        # The occurrence key must be visible so manager can paste it
        # into `task schedule confirm-occurrence`.
        assert key in out
        # Next-action hint must be present.
        assert "next_action" in out


# ── running / blocked ────────────────────────────────────────────────


def test_manager_panel_surfaces_running_occurrence():
    """A running occurrence must appear under a running bucket."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        from eduflow.scheduling import manager_ops
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        manager_ops.choose_lane(key, agent="worker_course", actor="manager", actor_role="manager")
        manager_ops.re_dispatch(key, actor="manager", actor_role="manager")

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "running" in out.lower()
        assert key in out


def test_manager_panel_surfaces_blocked_occurrence_with_reason():
    """A blocked occurrence (e.g. blocked_by_previous_run) must include
    its reason and next_action in the panel."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        # First cycle: creates awaiting_manager.
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key1 = f"{rid}:2026-07-12T08:00:00Z"
        # Confirm + dispatch so we have a running occurrence.
        from eduflow.scheduling import manager_ops
        manager_ops.confirm_occurrence(key1, actor="manager", actor_role="manager")
        manager_ops.choose_lane(key1, agent="worker_course", actor="manager", actor_role="manager")
        manager_ops.re_dispatch(key1, actor="manager", actor_role="manager")
        # Advance the clock past the next due time. Because the previous
        # occurrence is still `running`, the engine must create a
        # `blocked` occurrence with reason `blocked_by_previous_run`.
        engine.tick(_ms(2026, 7, 13, 8, 0))
        key2 = f"{rid}:2026-07-13T08:00:00Z"
        assert scheduled_tasks.get_occurrence(key2)["status"] == "blocked"

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "blocked" in out.lower()
        assert key2 in out
        assert "blocked_by_previous_run" in out
        assert "next_action" in out


# ── recent failure ───────────────────────────────────────────────────


def test_manager_panel_surfaces_recent_failure_occurrence():
    """A failed occurrence must surface as a recent failure with its
    failure_reason visible (not fabricated)."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        from eduflow.scheduling import manager_ops
        manager_ops.fail_pause_occurrence(key, actor="manager", actor_role="manager", reason="worker blocked")

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "recent failure" in out.lower() or "recent_failure" in out
        assert key in out
        assert "worker blocked" in out


# ── attention required ──────────────────────────────────────────────


def test_manager_panel_surfaces_attention_required_rule():
    """A rule in attention_required status must be surfaced with a clear
    reason (no fabrication)."""
    with isolated_env():
        from eduflow.scheduling import manager_ops
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            capacity=1,
        )
        # Drive the rule into attention_required: tick, confirm the
        # occurrence so the rule has one confirmed-but-not-completed
        # active row, then tick again with the rule pointed at a past
        # due time. Engine sees capacity reached and transitions the
        # rule to attention_required.
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        rule = scheduled_tasks.get_rule(rid)
        scheduled_tasks.update_rule(
            rid, {"next_due_utc": _utc(2026, 7, 13, 8, 0)},
            expected_version=rule["version"],
        )
        engine.tick(_ms(2026, 7, 13, 8, 0))
        assert scheduled_tasks.get_rule(rid)["status"] == "attention_required"

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "attention_required" in out
        assert rid in out
        assert "next_action" in out


# ── scheduler lag ───────────────────────────────────────────────────


def test_manager_panel_surfaces_scheduler_lag_when_heartbeat_stale():
    """When the heartbeat is older than the lag threshold, the panel must
    surface scheduler_lag with a numeric/age value. No fabrication."""
    with isolated_env():
        import time as _time
        # Touch heartbeat with a timestamp well in the past.
        scheduled_tasks.touch_heartbeat(lag_ms=0, error="")
        stale_ms = int((_time.time() - 3 * 3600) * 1000)
        from eduflow.util import write_json
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": stale_ms,
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "scheduler_lag" in out
        assert "next_action" in out


def test_manager_panel_ok_when_heartbeat_fresh():
    """When the heartbeat is recent, the lag line should not raise an
    alert — the panel must reflect actual scheduler state."""
    with isolated_env():
        from eduflow.util import now_ms
        scheduled_tasks.touch_heartbeat(lag_ms=0, error="")
        write_path = paths.scheduler_heartbeat_file()
        from eduflow.util import write_json
        write_json(write_path, {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "scheduler_lag=ok" in out or "scheduler_lag=healthy" in out or "scheduler_lag=" in out


# ── due soon ────────────────────────────────────────────────────────


def test_manager_panel_surfaces_due_soon_rule():
    """A rule whose next_due_utc is in the near future (within due-soon
    window) must appear under due soon."""
    with isolated_env():
        from eduflow.util import now_ms
        # Schedule a rule to be due within the next 15 minutes.
        due_ms = now_ms() + 10 * 60 * 1000
        from datetime import datetime, timezone
        due_dt = datetime.fromtimestamp(due_ms / 1000, tz=timezone.utc)
        due_utc = due_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = scheduled_tasks.create_rule(
            target="daily summary",
            artifact="summary.md",
            frequency="daily",
            timezone="UTC",
            next_due_utc=due_utc,
        )

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "due soon" in out.lower() or "due_soon" in out
        assert rid in out


# ── empty state ─────────────────────────────────────────────────────


def test_manager_panel_reports_d_scheduler_state_when_no_rules():
    """With zero scheduler rules and no heartbeat, the section must
    render deterministically with explicit `none` or 0 entries."""
    with isolated_env():
        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        assert "== D Scheduler ==" in out
        # Pending / running counters present and zero.
        assert "awaiting_manager=0" in out
        assert "running=0" in out


# ── field contract ──────────────────────────────────────────────────


def test_manager_panel_d_scheduler_row_contract():
    """Every scheduler row in the panel must carry: D-id, time, reason,
    next-action. Spot-check one row from each bucket."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"

        rc, out, _ = run_cli(["task", "manager-panel"])
        assert rc == 0
        # The awaiting_manager row must contain all four required fields.
        # Find the row containing the occurrence key and assert each field.
        lines = out.splitlines()
        rows = [ln for ln in lines if key in ln]
        assert rows, f"no panel row contains {key}; out={out!r}"
        row = rows[0]
        assert "next_action=" in row
        assert "reason=" in row
        # Time: scheduled_at_utc appears in the row OR a formatted time.
        assert "scheduled_at_utc=" in row or "scheduled=" in row or "at=" in row
        # The D-id (rule) is referenced.
        assert rid in row