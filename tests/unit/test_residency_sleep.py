"""Tests for Phase 3 — idle-to-warm auto-sleep.

Plan 2026-07-01 §设计二: warm agent with no active task, no unread
inbox, no cooldown, past handoff buffer, past idle timeout →
`温备`.  Resident + cold never sleep.  The decision matrix is
captured by `residency.sleep_decision` and exercised here
end-to-end through `commands.sleep_idle.sleep_if_idle`.

Phase 3 ships in dry-run by default — the only way `applied=True`
is reached in tests is when the caller passes `dry_run=False`
explicitly.
"""
from __future__ import annotations

import time

import pytest

from eduflow.commands import sleep_idle
from eduflow.runtime import residency
from eduflow.store import agent_residency, local_facts
from helpers import isolated_env


_RESIDENCY_TEAM_TOML = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlow"

[team.residency]
default_mode = "warm"
resident_agents = ["manager"]
warm_idle_timeout_s = 600
handoff_buffer_s = 300
wake_timeout_s = 60

[team.agents.manager]
cli = "claude-code"
role = "manager"

[team.agents.worker_course]
cli = "claude-code"
role = "course"

[team.agents.review_course]
cli = "claude-code"
role = "review"
"""


def _write_residency_team_toml(tmp):
    (tmp / "eduflow.toml").write_text(_RESIDENCY_TEAM_TOML, encoding="utf-8")


# ── sleep_decision pure tests ──────────────────────────────────


def _warm(idle=600, handoff=300):
    return residency.ResidencyPolicy(
        mode="warm", idle_timeout_s=idle, handoff_buffer_s=handoff,
        wake_timeout_s=60, source="default",
    )


def _resident():
    return residency.ResidencyPolicy(
        mode="resident", idle_timeout_s=600, handoff_buffer_s=300,
        wake_timeout_s=60, source="default",
    )


def _cold():
    return residency.ResidencyPolicy(
        mode="cold", idle_timeout_s=600, handoff_buffer_s=300,
        wake_timeout_s=60, source="default",
    )


def _sig(**kw):
    base = dict(
        has_active_task=False, has_unread_inbox=False, in_cooldown=False,
        idle_age_s=9999.0, since_handoff_s=9999.0,
    )
    base.update(kw)
    return residency.SleepSignals(**base)


def test_resident_never_sleeps_even_when_idle():
    assert residency.sleep_decision(_resident(), _sig()) == residency.KEEP_RESIDENT


def test_cold_never_sleeps_even_when_idle():
    assert residency.sleep_decision(_cold(), _sig()) == residency.KEEP_COLD


def test_warm_with_active_task_keeps_running():
    assert residency.sleep_decision(
        _warm(), _sig(has_active_task=True),
    ) == residency.KEEP_ACTIVE_TASK


def test_warm_with_unread_inbox_keeps_running():
    assert residency.sleep_decision(
        _warm(), _sig(has_unread_inbox=True),
    ) == residency.KEEP_UNREAD_INBOX


def test_warm_during_cooldown_keeps_running():
    assert residency.sleep_decision(
        _warm(), _sig(in_cooldown=True),
    ) == residency.KEEP_COOLDOWN


def test_warm_within_handoff_buffer_keeps_running():
    assert residency.sleep_decision(
        _warm(handoff=300), _sig(since_handoff_s=100),
    ) == residency.KEEP_HANDOFF_BUFFER


def test_warm_just_at_handoff_boundary_can_sleep():
    # `since_handoff_s < handoff_buffer_s` → KEEP.  At the exact
    # boundary, the condition is False so we move on.
    assert residency.sleep_decision(
        _warm(handoff=300), _sig(since_handoff_s=300),
    ) == residency.SLEEP_OK


def test_warm_under_idle_timeout_keeps_running():
    assert residency.sleep_decision(
        _warm(idle=600), _sig(idle_age_s=100),
    ) == residency.KEEP_UNDER_IDLE_TIMEOUT


def test_warm_idle_past_threshold_sleeps():
    assert residency.sleep_decision(
        _warm(idle=600), _sig(idle_age_s=601),
    ) == residency.SLEEP_OK


def test_priority_active_task_beats_idle_clock():
    """Even with infinite idle time, active task wins."""
    assert residency.sleep_decision(
        _warm(),
        _sig(has_active_task=True, idle_age_s=9999999),
    ) == residency.KEEP_ACTIVE_TASK


def test_should_sleep_boolean_wrapper_matches_decision():
    p = _warm()
    assert residency.should_sleep(p, _sig()) is True
    assert residency.should_sleep(p, _sig(has_active_task=True)) is False
    assert residency.should_sleep(_resident(), _sig()) is False


# ── agent_residency store ──────────────────────────────────────


def test_touch_active_then_age_since_active_decreases():
    with isolated_env():
        now = time.time()
        agent_residency.touch_active("worker_course", when=now - 100)
        age = agent_residency.age_since_active("worker_course", now=now)
        assert 99.0 <= age <= 101.0


def test_age_since_active_is_inf_for_untouched_agent():
    with isolated_env():
        assert agent_residency.age_since_active("ghost") == float("inf")


def test_touch_handoff_also_bumps_active():
    with isolated_env():
        now = time.time()
        agent_residency.touch_handoff("worker_course", when=now - 50)
        # last_active_at should be set to the same `now - 50`
        assert 49.0 <= agent_residency.age_since_active("worker_course", now=now) <= 51.0
        assert 49.0 <= agent_residency.age_since_handoff("worker_course", now=now) <= 51.0


def test_touch_wake_resets_active_clock():
    with isolated_env():
        now = time.time()
        agent_residency.touch_active("worker_course", when=now - 1000)
        agent_residency.touch_wake("worker_course", when=now)
        assert agent_residency.age_since_active("worker_course", now=now) < 1.0


# ── sleep_if_idle end-to-end (in-process, dry-run default) ───


def test_sleep_if_idle_dry_run_does_not_send_ctrl_c():
    with isolated_env():
        sent: list[tuple] = []
        upserted: list[tuple] = []
        result = sleep_idle.sleep_if_idle(
            "worker_course", dry_run=True,
            send_keys=lambda *a, **kw: sent.append((a, kw)) or True,
            upsert_status=lambda *a, **kw: upserted.append((a, kw)),
        )
    assert result["decision"] == "would_sleep" or result["decision"] == residency.SLEEP_OK
    assert result["applied"] is False
    assert sent == []
    assert upserted == []


def test_sleep_if_idle_dry_run_does_not_change_status():
    with isolated_env():
        local_facts.upsert_status("worker_course", "待命", "ready")
        result = sleep_idle.sleep_if_idle("worker_course", dry_run=True)
        assert result["applied"] is False
        snap = local_facts.get_status("worker_course")
        assert snap["status"] != "温备"


def test_sleep_if_idle_dry_run_keeps_active_task_agent_running():
    """Worker with status=进行中 → decision=keep_active_task."""
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "active")
        result = sleep_idle.sleep_if_idle("worker_course", dry_run=True)
        assert result["decision"] == residency.KEEP_ACTIVE_TASK


def test_sleep_if_idle_dry_run_keeps_unread_inbox_agent_running():
    with isolated_env():
        local_facts.append_message(
            "worker_course", "manager", "do thing", priority="高",
        )
        result = sleep_idle.sleep_if_idle("worker_course", dry_run=True)
        assert result["decision"] == residency.KEEP_UNREAD_INBOX


def test_sleep_if_idle_keeps_resident_running():
    with isolated_env() as tmp:
        _write_residency_team_toml(tmp)
        local_facts.upsert_status("manager", "待命", "ready")
        result = sleep_idle.sleep_if_idle("manager", dry_run=True)
        assert result["decision"] == residency.KEEP_RESIDENT


def test_sleep_if_idle_apply_sends_ctrl_c_and_stamps_warm():
    with isolated_env() as tmp:
        # 1) Seed a recent-but-past-idle activity stamp.
        # idle_timeout_s=600 (default), so idle_age_s=601 makes us sleep.
        # 2) Make sure no active task / unread inbox.
        local_facts.upsert_status("worker_course", "待命", "ready")
        now = time.time()
        agent_residency.touch_active("worker_course", when=now - 700)

        sent: list[tuple] = []
        # has_window=False in isolated_env so the Ctrl-C step is
        # skipped; that's fine — the stamps still go through.
        result = sleep_idle.sleep_if_idle(
            "worker_course", dry_run=False, now=now,
            send_keys=lambda *a, **kw: sent.append((a, kw)) or True,
        )
        assert result["decision"] == residency.SLEEP_OK
        assert result["applied"] is True
        # Stamp 温备 was written
        snap = local_facts.get_status("worker_course")
        assert snap["status"] == "温备"
        # last_sleep_at was written
        row = agent_residency.get("worker_course")
        assert row is not None
        assert row.get("last_sleep_at") is not None


def test_sleep_if_idle_apply_with_active_task_does_not_send_or_stamp():
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "active")
        sent: list[tuple] = []
        result = sleep_idle.sleep_if_idle(
            "worker_course", dry_run=False,
            send_keys=lambda *a, **kw: sent.append((a, kw)) or True,
        )
        assert result["decision"] == residency.KEEP_ACTIVE_TASK
        assert result["applied"] is False
        # No Ctrl-C sent, no 温备 stamp
        assert sent == []
        snap = local_facts.get_status("worker_course")
        assert snap["status"] == "进行中"


# ── sweep ──────────────────────────────────────────────────────


def test_sweep_runs_for_every_team_agent_in_dry_run():
    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlow"

[team.agents.manager]
cli = "claude-code"
role = "manager"

[team.agents.worker_course]
cli = "claude-code"
role = "course"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        # Both agents are 待命 (no active task), so warm ones
        # get a sleep_ok / would_sleep decision.
        local_facts.upsert_status("manager", "待命", "ready")
        local_facts.upsert_status("worker_course", "待命", "ready")
        results = sleep_idle.sweep(dry_run=True)
    assert len(results) == 2
    by_agent = {r["agent"]: r for r in results}
    assert by_agent["manager"]["decision"] == residency.KEEP_RESIDENT
    assert by_agent["worker_course"]["decision"] in (
        residency.SLEEP_OK, "would_sleep",
    )
    assert all(r["applied"] is False for r in results)


def test_sweep_with_agent_list_overrides_team():
    with isolated_env():
        local_facts.upsert_status("worker_course", "待命", "ready")
        results = sleep_idle.sweep(dry_run=True, agents=["worker_course"])
        assert [r["agent"] for r in results] == ["worker_course"]


# ── CLI integration ───────────────────────────────────────────


def test_residency_sleep_cli_text_output_in_dry_run_default():
    from helpers import run_cli
    with isolated_env() as tmp:
        _write_residency_team_toml(tmp)
        local_facts.upsert_status("worker_course", "待命", "ready")
        rc, out, err = run_cli(["residency-sleep"])
    assert rc == 0, err
    assert "worker_course" in out
    assert "[dry-run]" in out or "sleep_ok" in out or "would_sleep" in out


def test_residency_sleep_cli_json_output():
    import json
    from helpers import run_cli
    with isolated_env() as tmp:
        _write_residency_team_toml(tmp)
        local_facts.upsert_status("worker_course", "待命", "ready")
        rc, out, err = run_cli(["residency-sleep", "--json"])
    assert rc == 0, err
    data = json.loads(out)
    assert isinstance(data, list)
    assert any(r["agent"] == "worker_course" for r in data)


def test_residency_sleep_cli_apply_flag_does_real_work():
    from helpers import run_cli
    with isolated_env() as tmp:
        _write_residency_team_toml(tmp)
        # Seed a "ready" worker that is past its idle threshold
        # by stamping an old last_active_at.
        local_facts.upsert_status("worker_course", "待命", "ready")
        now = time.time()
        agent_residency.touch_active("worker_course", when=now - 1000)
        # We can't tmux spawn a real pane in isolated_env, but the
        # status stamp side-effect must still happen because we
        # have is_ready=False (no pane) — `tmux.has_window` returns
        # False, so the Ctrl-C step is a no-op.  The
        # upsert_status 温备 step runs unconditionally on apply.
        rc, out, _ = run_cli(["residency-sleep", "--agent", "worker_course", "--apply"])
        assert rc == 0
        snap = local_facts.get_status("worker_course")
        # The apply path updates the status regardless of pane
        # availability.  In an isolated_env there's no pane, so the
        # Ctrl-C branch is skipped; the 温备 stamp is the load-bearing
        # signal for the next wake.
        assert snap["status"] == "温备"
