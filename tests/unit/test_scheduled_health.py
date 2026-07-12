"""P6: health read-only D scheduler observations.

`eduflow health` must surface a D scheduler section that:
  * reports heartbeat status, last-success age, lag
  * reports pending (awaiting_manager) and running counts
  * counts consecutive skip / failure streaks
  * reads only from the scheduler store / engine state - no writes

These tests pin the field contract and verify the health section is
honest about what scheduler state looks like.
"""
from __future__ import annotations

import time

from helpers import isolated_env, run_cli, tmux_patch
from eduflow.runtime import paths
from eduflow.scheduling import engine, manager_ops
from eduflow.store import scheduled_tasks
from eduflow.util import write_json


_TEAM = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
_RUNTIME = {"chat_id": "oc_x"}


def _stub_tmux(*, session_alive: bool = True,
               panes_with_cli: list[str] = ("manager",),
               panes_without_cli: list[str] = ()):
    """Stub tmux so the per-agent / runtime-readiness probes pass green.
    Default keeps `manager` in panes_with_cli (avoids the red
    `manager: no tmux window`). The D scheduler section does not probe
    panes, so capture_pane can return empty."""
    all_panes = list(panes_with_cli) + list(panes_without_cli)
    return tmux_patch(
        has_session=lambda s: session_alive,
        has_window=lambda target: target.window in all_panes,
        capture_pane=lambda target, lines=80: "bypass permissions on\n? for shortcuts\n>",
        list_panes=lambda target: [],
    )


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# - section presence -


def test_health_includes_d_scheduler_section_header():
    """Even with no scheduler state, the section header must render so
    operators know the health surface covers scheduler observations."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "D scheduler:" in out or "d scheduler:" in out.lower()


def test_health_d_scheduler_section_is_read_only():
    """The section must not mutate scheduler files. Pin the on-disk
    content + mtime before/after the health command."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        rules_path = paths.scheduler_rules_file()
        occ_path = paths.scheduler_occurrences_file()
        heartbeat_path = paths.scheduler_heartbeat_file()
        cursor_path = paths.scheduler_cursor_file()
        rules_before = rules_path.read_text(encoding="utf-8")
        occ_before = occ_path.read_text(encoding="utf-8")
        heartbeat_before = heartbeat_path.read_text(encoding="utf-8")
        cursor_before = cursor_path.read_text(encoding="utf-8")
        rules_mtime = rules_path.stat().st_mtime

        rc, out, _ = run_cli(["health"])
        assert rc == 0

        assert rules_path.read_text(encoding="utf-8") == rules_before
        assert occ_path.read_text(encoding="utf-8") == occ_before
        assert heartbeat_path.read_text(encoding="utf-8") == heartbeat_before
        assert cursor_path.read_text(encoding="utf-8") == cursor_before
        assert rules_path.stat().st_mtime == rules_mtime
        assert scheduled_tasks.get_rule(rid)["status"] == "active"


# - heartbeat status -


def test_health_d_scheduler_heartbeat_ok_after_recent_tick():
    """Recent tick with no error must surface as heartbeat_ok."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        from eduflow.util import now_ms
        scheduled_tasks.touch_heartbeat(lag_ms=0, error="")
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "heartbeat=" in out
        assert "heartbeat=ok" in out


def test_health_d_scheduler_heartbeat_error_when_last_tick_errored():
    """When the last heartbeat has a non-empty error, health must surface
    it. The exit code may stay 0 (warning) - the field must be present."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        from eduflow.util import now_ms
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "ValueError: bad timezone",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0  # warning, not red
        assert "heartbeat=" in out
        assert "heartbeat=error" in out
        assert "ValueError" in out


def test_health_d_scheduler_heartbeat_never_when_no_record():
    """If no heartbeat file exists, report it explicitly."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "heartbeat=" in out
        assert "heartbeat=missing" in out or "last_tick=never" in out


# - last success / lag -


def test_health_d_scheduler_last_success_reported():
    """last_tick must appear so operators can see how long since the
    last clean tick."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        from eduflow.util import now_ms
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "last_tick" in out


def test_health_d_scheduler_lag_field_present():
    """Lag must be present."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        from eduflow.util import now_ms
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "lag=" in out


def test_health_d_scheduler_lag_warns_when_stale():
    """When last_tick_at is well in the past, surface scheduler_lag with
    a warn value."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        stale_ms = int((time.time() - 3 * 3600) * 1000)
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": stale_ms,
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "lag=warn" in out


# - pending / running counts -


def test_health_d_scheduler_counters_present_when_state_present():
    """When awaiting/running occurrences exist, counters must reflect them."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        manager_ops.choose_lane(key, agent="worker_course", actor="manager", actor_role="manager")
        manager_ops.re_dispatch(key, actor="manager", actor_role="manager")

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "running=" in out
        assert "running=1" in out
        assert "pending=" in out


def test_health_d_scheduler_counters_zero_when_no_state():
    """Empty scheduler state must report zero counters, not crash."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "D scheduler:" in out or "d scheduler:" in out.lower()
        assert "pending=0" in out
        assert "running=0" in out


# - consecutive skip / failure streaks -


def test_health_d_scheduler_consecutive_failure_streak():
    """A streak of failed occurrences must be reported."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.fail_pause_occurrence(
            key, actor="manager", actor_role="manager", reason="x",
        )

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "consecutive_failure" in out
        assert "consecutive_failure=1" in out


def test_health_d_scheduler_consecutive_skip_streak():
    """A streak of skipped occurrences must be reported."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.skip_occurrence(
            key, actor="manager", actor_role="manager", reason="holiday",
        )

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "consecutive_skip" in out
        assert "consecutive_skip=1" in out


# - field contract -


def test_health_d_scheduler_field_contract():
    """All D scheduler health fields must appear together in one report."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        from eduflow.util import now_ms
        write_json(paths.scheduler_heartbeat_file(), {
            "last_tick_at": now_ms(),
            "lag_ms": 0,
            "error": "",
        })

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        for needle in ("heartbeat=", "lag=", "pending=", "running="):
            assert needle in out, f"D scheduler health missing {needle}"


def test_health_d_scheduler_section_does_not_crash_when_store_corrupt():
    """If the scheduler files are unparseable, the health section must
    degrade gracefully - not raise."""
    with isolated_env(team=_TEAM, runtime_config=_RUNTIME), _stub_tmux():
        rules_path = paths.scheduler_rules_file()
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rules_path.write_text("{not valid json", encoding="utf-8")

        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "D scheduler:" in out or "d scheduler:" in out.lower()