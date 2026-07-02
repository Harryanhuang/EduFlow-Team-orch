"""Tests for V3 P3 items: AGENTS.md generator and reflect."""
from __future__ import annotations

import pytest

from eduflow.memory import db, items, agents_md_gen, reflect, candidates


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    db._local.conn = conn
    db.init_schema()
    db.migrate_pinned_column()
    yield
    conn.close()
    db._local.conn = None


# ── AGENTS.md generator (P3-2) ────────────────────────────────────────

def test_generate_agents_md_empty():
    draft = agents_md_gen.generate_agents_md("team", min_importance=5)
    assert "team" in draft
    assert "No qualifying memories" in draft


def test_generate_agents_md_with_workflow_rules():
    items.add_memory(scope="team", kind="workflow_rule",
                     content="Always use plan mode", status="confirmed",
                     importance=7)
    items.add_memory(scope="team", kind="role_rule",
                     content="Manager is sole dispatcher", status="confirmed",
                     importance=9)

    draft = agents_md_gen.generate_agents_md("team")
    assert "Must Follow" in draft
    assert "Workflow Rules" in draft
    assert "Role Rules" in draft
    assert "plan mode" in draft
    assert "Manager" in draft


def test_generate_agents_md_min_importance_filter():
    """Low importance memories should be excluded."""
    items.add_memory(scope="team", kind="workflow_rule",
                     content="low imp rule", status="confirmed",
                     importance=3)
    items.add_memory(scope="team", kind="workflow_rule",
                     content="high imp rule", status="confirmed",
                     importance=8)

    draft = agents_md_gen.generate_agents_md("team", min_importance=5)
    assert "high imp rule" in draft
    assert "low imp rule" not in draft


def test_generate_agents_md_custom_kinds():
    items.add_memory(scope="team", kind="decision",
                     content="decided to use X", status="confirmed",
                     importance=5)
    items.add_memory(scope="team", kind="mistake",
                     content="tried Y", status="confirmed",
                     importance=5)

    # Only include decisions
    draft = agents_md_gen.generate_agents_md("team", kinds=["decision"])
    assert "decided to use X" in draft
    assert "tried Y" not in draft


def test_write_agents_md(tmp_path):
    items.add_memory(scope="team", kind="workflow_rule",
                     content="test rule", status="confirmed", importance=7)

    out_path = tmp_path / "AGENTS.md"
    result = agents_md_gen.write_agents_md("team", out_path)

    assert result["written"] is True
    assert out_path.exists()
    content = out_path.read_text()
    assert "test rule" in content


def test_write_agents_md_skip_existing(tmp_path):
    items.add_memory(scope="team", kind="workflow_rule", content="x", status="confirmed")

    out_path = tmp_path / "AGENTS.md"
    out_path.write_text("# Existing file")

    result = agents_md_gen.write_agents_md("team", out_path, overwrite=False)
    assert result["written"] is False
    assert result["skipped"] is True
    # Original content preserved
    assert out_path.read_text() == "# Existing file"


def test_write_agents_md_overwrite(tmp_path):
    items.add_memory(scope="team", kind="workflow_rule", content="new rule",
                     status="confirmed", importance=7)

    out_path = tmp_path / "AGENTS.md"
    out_path.write_text("# Old content")

    result = agents_md_gen.write_agents_md("team", out_path, overwrite=True)
    assert result["written"] is True
    assert "new rule" in out_path.read_text()


# ── Reflect (P3-1 lightweight) ──────────────────────────────────────

def test_submit_reflection_basic():
    learnings = [
        {
            "kind": "note",
            "content": "Learned that plan mode is helpful",
            "proposed_scope": "agent:worker_course",
            "reason": "session-2026-06-30",
        },
    ]
    ids = reflect.submit_reflection("worker_course", learnings)
    assert len(ids) == 1

    # Check the candidate was created with source_type=reflection
    cand = candidates.get_candidate(ids[0])
    assert cand is not None
    assert cand["source_type"] == "reflection"
    assert cand["content"] == "Learned that plan mode is helpful"


def test_submit_reflection_multiple():
    learnings = [
        {"kind": "note", "content": "learning 1", "proposed_scope": "agent:worker"},
        {"kind": "mistake", "content": "learning 2", "proposed_scope": "agent:worker"},
    ]
    ids = reflect.submit_reflection("worker", learnings)
    assert len(ids) == 2


def test_submit_reflection_empty_raises():
    with pytest.raises(ValueError, match="cannot be empty"):
        reflect.submit_reflection("agent", [])


def test_submit_reflection_skips_empty_content():
    learnings = [
        {"kind": "note", "content": "valid", "proposed_scope": "agent:x"},
        {"kind": "note", "content": "  ", "proposed_scope": "agent:x"},  # empty
    ]
    ids = reflect.submit_reflection("x", learnings)
    assert len(ids) == 1


def test_list_recent_reflection_candidates():
    reflect.submit_reflection(
        "worker",
        [{"kind": "note", "content": "test", "proposed_scope": "agent:worker"}],
    )
    recent = reflect.list_recent_reflection_candidates(days=7)
    assert all(c["source_type"] == "reflection" for c in recent)
    assert len(recent) >= 1


def test_reflection_stats():
    # Add some reflection candidates
    ids = reflect.submit_reflection(
        "test_agent",
        [{"kind": "note", "content": "test1", "proposed_scope": "agent:test"}],
    )
    # Promote one
    candidates.promote_candidate(ids[0], reviewer="manager")

    stats = reflect.reflection_stats(days=30)
    assert stats["total"] >= 1
    assert stats["promote_rate"] > 0
    assert "promoted" in stats["by_status"]


def test_reflection_stats_empty():
    stats = reflect.reflection_stats(days=30)
    # No reflection candidates in this test
    assert stats["total"] == 0
    assert stats["promote_rate"] == 0.0