"""Tests for skill_evolution (V3 P3-3 skeleton)."""
from __future__ import annotations

import pytest

from eduflow.memory import (
    aggregate_frequent_rules,
    generate_suggestions,
    reject_suggestion,
    accept_suggestion,
    list_active_cooldowns,
    clear_all_cooldowns,
    render_suggestion_report,
)
from eduflow.memory import db, items
from flow_memory.storage import SqliteBackend


@pytest.fixture(autouse=True)
def _clean_db(tmp_path):
    """Use a fresh SqliteBackend instance bound to the test DB."""
    db_path = tmp_path / "test_memory.db"

    # Reset all module-level singletons
    import flow_memory.storage as st
    import flow_memory.storage.paths as pp
    import flow_memory.storage.sql as sql_mod
    st._backend = None
    pp._provider = None
    sql_mod._backend = None

    # Create the backend and force-init it
    backend = SqliteBackend(db_path=db_path)
    backend.init_schema()

    # Inject into the singleton so get_backend() returns this one
    sql_mod._backend = backend
    st._backend = backend

    # Also set the legacy path so db.init_schema() works correctly
    db._local.conn = backend.connect()

    yield

    db._local.conn = None
    st._backend = None
    pp._provider = None
    sql_mod._backend = None


def test_aggregate_frequent_rules():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="always use plan mode",
                     status="confirmed", importance=8)
    items.add_memory(scope="team", kind="note",
                     content="just a note",
                     status="confirmed", importance=3)

    rules = aggregate_frequent_rules(min_importance=7, min_age_days=0)
    assert len(rules) == 1
    assert rules[0]["kind"] == "workflow_rule"


def test_aggregate_frequent_rules_by_scope():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="team rule", status="confirmed", importance=9)
    items.add_memory(scope="lane:course", kind="workflow_rule",
                     content="lane rule", status="confirmed", importance=9)

    team_rules = aggregate_frequent_rules(scope="team", min_age_days=0)
    assert len(team_rules) == 1
    assert "team" in team_rules[0]["scope"]


def test_generate_suggestions_format():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="important rule", status="confirmed", importance=9)

    suggestions = generate_suggestions(min_importance=7, min_age_days=0)
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s["rule_id"].startswith("MI-")
    assert "important rule" in s["content"]
    assert "+" in s["diff_text"]  # unified diff format


def test_reject_suggestion_enters_cooldown():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="x", status="confirmed", importance=8)

    suggestions = generate_suggestions(min_age_days=0)
    rule_id = suggestions[0]["rule_id"]
    reject_suggestion(rule_id, reason="not relevant", cooldown_hours=24)

    new_suggestions = generate_suggestions(min_age_days=0)
    assert all(s["rule_id"] != rule_id for s in new_suggestions)

    cooldowns = list_active_cooldowns()
    assert any(c["rule_id"] == rule_id for c in cooldowns)


def test_reject_suggestion_exponential_backoff():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="x", status="confirmed", importance=8)
    rule_id = items.list_memories(scope="team")[0]["id"]

    reject_suggestion(rule_id, cooldown_hours=24)
    reject_suggestion(rule_id, cooldown_hours=24)
    reject_suggestion(rule_id, cooldown_hours=24)

    cooldowns = list_active_cooldowns()
    matching = [c for c in cooldowns if c["rule_id"] == rule_id]
    assert len(matching) == 1
    assert matching[0]["reject_count"] == 3


def test_accept_suggestion_clears_cooldown():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="x", status="confirmed", importance=8)
    rule_id = items.list_memories(scope="team")[0]["id"]

    reject_suggestion(rule_id, cooldown_hours=24)
    assert any(c["rule_id"] == rule_id for c in list_active_cooldowns())

    cleared = accept_suggestion(rule_id)
    assert cleared is True
    assert not any(c["rule_id"] == rule_id for c in list_active_cooldowns())


def test_clear_all_cooldowns():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="x", status="confirmed", importance=8)
    rule_id = items.list_memories(scope="team")[0]["id"]
    reject_suggestion(rule_id, cooldown_hours=24)

    count = clear_all_cooldowns()
    assert count >= 1
    assert list_active_cooldowns() == []


def test_render_report_includes_sections():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="important", status="confirmed", importance=9)

    report = render_suggestion_report()
    assert "# 🧬 Skill Evolution Suggestions" in report
    assert "Pending Suggestions" in report
    assert "Active Cooldowns" in report


def test_render_report_no_suggestions():
    report = render_suggestion_report(min_importance=10)
    assert "No new suggestions" in report


def test_rule_in_cooldown_excluded_from_suggestions():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="x", status="confirmed", importance=9)
    rule_id = items.list_memories(scope="team")[0]["id"]

    s_before = generate_suggestions(min_age_days=0)
    assert any(s["rule_id"] == rule_id for s in s_before)

    reject_suggestion(rule_id, cooldown_hours=24)
    s_after = generate_suggestions(min_age_days=0)
    assert not any(s["rule_id"] == rule_id for s in s_after)

    accept_suggestion(rule_id)
    s_restored = generate_suggestions(min_age_days=0)
    assert any(s["rule_id"] == rule_id for s in s_restored)