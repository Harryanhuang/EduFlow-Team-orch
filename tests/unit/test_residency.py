"""Tests for residency policy (runtime/residency.py + config loaders).

Plan 2026-07-01 §设计二: resident / warm / cold modes, per-agent
override on top of team-wide defaults, `/team` display labels.

Phase 2 is config-only — no sleep/wake machinery yet (that is
Phase 3).  These tests pin the schema, the merge semantics, and
the mode-resolution precedence:

    team default_mode  <  resident_agents membership  <  per-agent override
"""
from __future__ import annotations

import pytest

from helpers import isolated_env, run_cli
from eduflow.runtime import config, residency
from eduflow.runtime.residency import ResidencyMode, ResidencyPolicy


# ── ResidencyPolicy dataclass ─────────────────────────────────


def test_policy_accepts_valid_modes():
    for mode in ResidencyMode.ALL:
        p = ResidencyPolicy(
            mode=mode, idle_timeout_s=600, handoff_buffer_s=300,
            wake_timeout_s=60, source="default",
        )
        assert p.mode == mode


def test_policy_rejects_invalid_mode():
    with pytest.raises(ValueError, match="invalid residency mode"):
        ResidencyPolicy(
            mode="bogus", idle_timeout_s=600, handoff_buffer_s=300,
            wake_timeout_s=60, source="default",
        )


def test_policy_rejects_negative_idle_timeout():
    with pytest.raises(ValueError, match="idle_timeout_s"):
        ResidencyPolicy(
            mode="warm", idle_timeout_s=-1, handoff_buffer_s=300,
            wake_timeout_s=60, source="default",
        )


def test_policy_rejects_nonpositive_wake_timeout():
    with pytest.raises(ValueError, match="wake_timeout_s"):
        ResidencyPolicy(
            mode="warm", idle_timeout_s=600, handoff_buffer_s=300,
            wake_timeout_s=0, source="default",
        )


# ── merge_with_default ────────────────────────────────────────


def _default() -> ResidencyPolicy:
    return ResidencyPolicy(
        mode="warm", idle_timeout_s=600, handoff_buffer_s=300,
        wake_timeout_s=60, source="default",
    )


def test_merge_with_none_override_returns_default():
    d = _default()
    assert residency.merge_with_default(default_policy=d, override=None) is d


def test_merge_with_empty_override_returns_default():
    d = _default()
    assert residency.merge_with_default(default_policy=d, override={}) is d


def test_merge_applies_partial_override_field_by_field():
    d = _default()
    merged = residency.merge_with_default(
        default_policy=d, override={"idle_timeout_s": 300},
    )
    assert merged.idle_timeout_s == 300      # overridden
    assert merged.handoff_buffer_s == 300    # fell through
    assert merged.wake_timeout_s == 60       # fell through
    assert merged.mode == "warm"             # fell through
    assert merged.source == "agent_override"


def test_merge_coerces_bad_int_to_default():
    d = _default()
    merged = residency.merge_with_default(
        default_policy=d, override={"idle_timeout_s": "not-a-number"},
    )
    assert merged.idle_timeout_s == 600  # fell back to default


def test_merge_coerces_bad_mode_to_default():
    d = _default()
    merged = residency.merge_with_default(
        default_policy=d, override={"mode": "sideways"},
    )
    assert merged.mode == "warm"


# ── display labels ────────────────────────────────────────────


def test_display_label_maps_modes_to_chinese():
    assert residency.display_label("resident") == "常驻"
    assert residency.display_label("warm") == "温备"
    assert residency.display_label("cold") == "cold"


def test_display_label_unknown_returns_placeholder():
    assert residency.display_label("bogus") == "未配置"
    assert residency.display_label("") == "未配置"


# ── config loaders: no residency block → all defaults ─────────

_TEAM_NO_RESIDENCY = """
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


def test_load_residency_default_when_block_absent():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_NO_RESIDENCY, encoding="utf-8")
        p = config.load_residency_policy("worker_course")
        assert p.mode == "warm"
        assert p.idle_timeout_s == residency.DEFAULT_IDLE_TIMEOUT_S
        assert p.source == "default"


def test_load_resident_agents_default_when_block_absent():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_NO_RESIDENCY, encoding="utf-8")
        # manager is in DEFAULT_RESIDENT_AGENTS and known → included;
        # auto_ops / Luke_recorder not in team → filtered out.
        resident = config.load_resident_agents()
        assert "manager" in resident
        assert "auto_ops" not in resident  # not in this team


# ── config loaders: full residency block ──────────────────────

_TEAM_WITH_RESIDENCY = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlow"

[team.residency]
default_mode = "warm"
resident_agents = ["manager", "auto_ops", "Luke_recorder"]
warm_idle_timeout_s = 600
handoff_buffer_s = 300
wake_timeout_s = 60

[team.agents.manager]
cli = "claude-code"
role = "manager"

[team.agents.auto_ops]
cli = "claude-code"
role = "ops"

[team.agents.Luke_recorder]
cli = "claude-code"
role = "recorder"

[team.agents.worker_course]
cli = "claude-code"
role = "course"

[team.agents.worker_syllabus]
cli = "claude-code"
role = "syllabus"

[team.agents.worker_syllabus.residency]
mode = "warm"
idle_timeout_s = 300
"""


def test_resident_agents_are_resident_mode():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_WITH_RESIDENCY, encoding="utf-8")
        for agent in ("manager", "auto_ops", "Luke_recorder"):
            p = config.load_residency_policy(agent)
            assert p.mode == "resident", f"{agent} should be resident"


def test_non_resident_agents_are_warm_mode():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_WITH_RESIDENCY, encoding="utf-8")
        p = config.load_residency_policy("worker_course")
        assert p.mode == "warm"


def test_per_agent_override_wins_on_idle_timeout():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_WITH_RESIDENCY, encoding="utf-8")
        p = config.load_residency_policy("worker_syllabus")
        assert p.mode == "warm"
        assert p.idle_timeout_s == 300  # from per-agent override
        assert p.handoff_buffer_s == 300  # fell through to default
        assert p.source == "agent_override"


def test_resident_agents_list_filters_unknown_names():
    team = _TEAM_WITH_RESIDENCY.replace(
        'resident_agents = ["manager", "auto_ops", "Luke_recorder"]',
        'resident_agents = ["manager", "ghost_agent"]',
    )
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team, encoding="utf-8")
        resident = config.load_resident_agents()
        assert "manager" in resident
        assert "ghost_agent" not in resident  # not a real team member


def test_per_agent_override_can_promote_to_resident():
    """A per-agent `mode = "resident"` override wins even when the
    agent is not in `resident_agents`."""
    team = _TEAM_WITH_RESIDENCY + """
[team.agents.worker_course.residency]
mode = "resident"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team, encoding="utf-8")
        p = config.load_residency_policy("worker_course")
        assert p.mode == "resident"


def test_per_agent_override_can_demote_from_resident():
    """A per-agent `mode = "warm"` override wins even when the agent
    IS in resident_agents — lets the boss carve out an exception."""
    team = _TEAM_WITH_RESIDENCY + """
[team.agents.manager.residency]
mode = "warm"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team, encoding="utf-8")
        p = config.load_residency_policy("manager")
        assert p.mode == "warm"


# ── /team display integration ─────────────────────────────────


def test_team_text_shows_residency_column():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_WITH_RESIDENCY, encoding="utf-8")
        # Seed a status row so /team has something to render.
        from eduflow.store import local_facts
        local_facts.upsert_status("manager", "进行中", "派单中")
        local_facts.upsert_status("worker_course", "待命", "ready")
        rc, out, err = run_cli(["team"])
        assert rc == 0, err
        assert "常驻" in out   # manager is resident
        assert "温备" in out   # worker_course is warm


def test_team_json_includes_residency_field():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(_TEAM_WITH_RESIDENCY, encoding="utf-8")
        from eduflow.store import local_facts
        local_facts.upsert_status("manager", "进行中", "派单中")
        rc, out, err = run_cli(["team", "--json"])
        assert rc == 0, err
        import json
        data = json.loads(out)
        manager_row = next(r for r in data if r["agent"] == "manager")
        assert manager_row["residency"] == "常驻"
        # Old schema keys still present (backward compat)
        assert "status" in manager_row
        assert "updated_at_ms" in manager_row
        assert "heartbeat_ms" in manager_row
