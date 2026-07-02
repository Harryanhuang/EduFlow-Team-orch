"""Tests for V3 P1: dual_query and daily_summary."""
from __future__ import annotations

import pytest

from eduflow.memory import db, items, dual_query, daily_summary, packet, scope_aliases


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


# ── Dual query (P1-4) ───────────────────────────────────────────────

def test_dual_query_topic_only():
    """Memories only matching topic should have _source='topic'."""
    items.add_memory(scope="team", kind="note", content="closeout workflow",
                     status="confirmed")

    results = dual_query.dual_query_memories("closeout", limit=5)
    assert len(results) >= 1
    assert all(r.get("_source") in ("topic", "both") for r in results)


def test_dual_query_background_only():
    """Memories only matching workflow scope should have _source='background'."""
    items.add_memory(scope="workflow:igcse-subject-launch", kind="note",
                     content="IGCSE launch procedure",
                     status="confirmed")

    results = dual_query.dual_query_memories(
        "some query",
        workflow_id="igcse-subject-launch",
        limit=5,
    )
    # The workflow-scoped memory should be in background results
    has_bg = any(r.get("_source") == "background" for r in results)
    assert has_bg


def test_dual_query_both_paths():
    """Memory matching both paths should have _source='both'."""
    items.add_memory(scope="workflow:igcse", kind="note",
                     content="closeout checklist for IGCSE",
                     status="confirmed")

    results = dual_query.dual_query_memories(
        "closeout",
        workflow_id="igcse",
        limit=5,
    )
    assert len(results) >= 1
    assert any(r.get("_source") == "both" for r in results)


def test_dual_query_dedup():
    """Same memory in both paths should appear once with _source='both'."""
    items.add_memory(scope="workflow:test", kind="note",
                     content="unique marker xyz123",
                     status="confirmed")

    results = dual_query.dual_query_memories(
        "xyz123",
        workflow_id="test",
        limit=10,
    )
    # Should appear once
    matching = [r for r in results if "xyz123" in r.get("content", "")]
    assert len(matching) == 1
    assert matching[0]["_source"] == "both"


def test_dual_query_empty_topic():
    """Empty topic query returns only background results."""
    items.add_memory(scope="workflow:abc", kind="note", content="background only",
                     status="confirmed")

    results = dual_query.dual_query_memories(
        "",
        workflow_id="abc",
        limit=5,
    )
    assert all(r.get("_source") == "background" for r in results)


def test_dual_query_no_paths():
    """No topic + no workflow = empty."""
    results = dual_query.dual_query_memories("", limit=5)
    assert results == []


def test_packet_includes_dual_query_lines():
    """assemble_memory_packet should include [dual:...] lines when applicable."""
    scope_aliases.add_alias("agent_test", "agent:test_agent")

    items.add_memory(scope="agent:test_agent", kind="note",
                     content="agent closeout rule",
                     status="confirmed")
    items.add_memory(scope="workflow:project_alpha", kind="note",
                     content="project_alpha context",
                     status="confirmed")

    # Create a capsule with workflow_id
    from eduflow.memory.capsules import upsert_capsule
    upsert_capsule(
        task_id="T-TEST-DUAL",
        workflow_id="project_alpha",
        goal="do something",
    )

    p = packet.assemble_memory_packet("test_agent", task_id="T-TEST-DUAL")
    # Should include content from both paths
    assert "agent closeout rule" in p
    assert "project_alpha context" in p


# ── Daily summary (P1-5) ────────────────────────────────────────────

def test_daily_summary_upsert_new():
    """New summary is created."""
    key = daily_summary.upsert_summary(
        date="2026-06-30",
        agent="worker_course",
        summary="Tested IGCSE module review",
        key_decisions=["use FTS for search"],
        open_questions=["why FTS so slow?"],
    )
    assert key == "2026-06-30::worker_course"


def test_daily_summary_upsert_update():
    """Updating existing summary overwrites content."""
    daily_summary.upsert_summary("2026-06-30", "agent1", "first")
    daily_summary.upsert_summary("2026-06-30", "agent1", "second")

    s = daily_summary.get_summary("2026-06-30", "agent1")
    assert s["summary"] == "second"


def test_daily_summary_get_missing():
    assert daily_summary.get_summary("2099-01-01", "nonexistent") is None


def test_daily_summary_list():
    """List returns summaries sorted by date desc."""
    daily_summary.upsert_summary("2026-06-28", "a1", "first day")
    daily_summary.upsert_summary("2026-06-29", "a1", "second day")
    daily_summary.upsert_summary("2026-06-30", "a1", "third day")
    daily_summary.upsert_summary("2026-06-30", "a2", "different agent")

    summaries = daily_summary.list_summaries()
    assert len(summaries) >= 4


def test_daily_summary_list_filtered_by_agent():
    daily_summary.upsert_summary("2026-06-30", "agent_a", "a")
    daily_summary.upsert_summary("2026-06-30", "agent_b", "b")

    a_summaries = daily_summary.list_summaries(agent="agent_a")
    assert all(s["agent"] == "agent_a" for s in a_summaries)


def test_daily_summary_delete():
    daily_summary.upsert_summary("2026-06-30", "tmp", "test")
    assert daily_summary.delete_summary("2026-06-30", "tmp") is True
    assert daily_summary.get_summary("2026-06-30", "tmp") is None


def test_daily_summary_archive():
    daily_summary.upsert_summary("2020-01-01", "old", "ancient")
    daily_summary.upsert_summary("2026-06-30", "new", "recent")

    count = daily_summary.archive_old_summaries(retention_days=30)
    assert count >= 1

    # Old one gone, new one kept
    assert daily_summary.get_summary("2020-01-01", "old") is None
    assert daily_summary.get_summary("2026-06-30", "new") is not None


def test_daily_summary_empty_summary_raises():
    with pytest.raises(ValueError, match="cannot be empty"):
        daily_summary.upsert_summary("2026-06-30", "x", "  ")