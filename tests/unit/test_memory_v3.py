"""Tests for V3 P0 features: pin, decay-in-packet, subject hierarchy."""
from __future__ import annotations

import pytest

from eduflow.memory import db, items, scope_aliases, storage_budget, packet


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    db._local.conn = conn
    db.init_schema()

    # Apply V3 schema migration (add pinned column)
    try:
        conn.execute("ALTER TABLE memory_items ADD COLUMN pinned INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass  # column already exists

    yield
    conn.close()
    db._local.conn = None


# ── Pin ─────────────────────────────────────────────────────────────

def test_pin_memory_basic():
    mid = items.add_memory(scope="team", kind="note", content="important", status="confirmed")
    assert items.pin_memory(mid) is True
    m = items.get_memory(mid)
    assert m["pinned"] == 1


def test_pin_idempotent():
    mid = items.add_memory(scope="team", kind="note", content="x", status="confirmed")
    assert items.pin_memory(mid) is True
    # Second pin returns False (no state change)
    assert items.pin_memory(mid) is False


def test_unpin_memory():
    mid = items.add_memory(scope="team", kind="note", content="x", status="confirmed")
    items.pin_memory(mid)
    assert items.unpin_memory(mid) is True
    m = items.get_memory(mid)
    assert m["pinned"] == 0


def test_unpin_cli_returns_nonzero_when_memory_is_not_pinned(monkeypatch, capsys):
    from eduflow.commands import memory_cli

    monkeypatch.setattr(items, "unpin_memory", lambda memory_id: False)

    assert memory_cli._cmd_pin_unpin(["MI-missing"]) == 1
    assert "Not pinned or not found" in capsys.readouterr().out


def test_list_pinned_memories():
    mid1 = items.add_memory(scope="team", kind="note", content="pin me", status="confirmed")
    mid2 = items.add_memory(scope="team", kind="note", content="not pinned", status="confirmed")
    items.pin_memory(mid1)

    pinned = items.list_pinned_memories()
    assert len(pinned) == 1
    assert pinned[0]["id"] == mid1
    assert mid2 not in [p["id"] for p in pinned]


def test_budget_protects_pinned():
    """Pinned memories should NOT be evicted even when budget exceeded."""
    from eduflow.memory.storage_budget import LIMITS

    # Temporarily lower the limit to force eviction
    original_limit = LIMITS["memory_items"]
    LIMITS["memory_items"] = 3

    try:
        # Add 5 confirmed memories, pin 1 of them
        ids = []
        for i in range(5):
            mid = items.add_memory(
                scope="team", kind="note", content=f"item {i}",
                status="confirmed",
            )
            ids.append(mid)
        pinned_id = ids[0]
        items.pin_memory(pinned_id)

        # Run budget enforcement
        result = storage_budget.enforce_budget("memory_items")
        assert result["evicted"] > 0  # some evicted

        # Pinned memory should still exist
        assert items.get_memory(pinned_id) is not None
        assert items.get_memory(pinned_id)["pinned"] == 1
    finally:
        LIMITS["memory_items"] = original_limit


# ── Decay in packet ────────────────────────────────────────────────

def test_packet_includes_curated_core_section():
    """Pinned memories should appear in dedicated curated core section."""
    items.add_memory(scope="agent:worker_course", kind="note", content="pinned rule",
                     status="confirmed")
    items.add_memory(scope="agent:worker_course", kind="note", content="another pinned rule",
                     status="confirmed")

    # Pin the second one (just-added memories get ID at this point)
    all_items = items.list_memories(scope="agent:worker_course", status="confirmed")
    pinned_id = all_items[-1]["id"]
    items.pin_memory(pinned_id)

    p = packet.assemble_memory_packet("worker_course")
    assert "Curated Core" in p
    assert "📌" in p
    assert "another pinned rule" in p
    assert "pinned rule" in p


def test_packet_sorts_by_effective_confidence():
    """Memories in the relevant segment should be sorted by effective_confidence."""
    # Add a few memories (all with same created_at = now, so same age factor)
    items.add_memory(scope="agent:worker_course", kind="note", content="high confidence",
                     status="confirmed", confidence=1.0)
    items.add_memory(scope="agent:worker_course", kind="note", content="low confidence",
                     status="confirmed", confidence=0.3)

    p = packet.assemble_memory_packet("worker_course")
    assert "high confidence" in p
    assert "low confidence" in p


def test_packet_touch_marks_recently_used():
    """Assembling a packet should touch the included memories."""
    mid = items.add_memory(scope="agent:worker_course", kind="note", content="x",
                          status="confirmed")

    original = items.get_memory(mid)
    original_updated = original["updated_at"]

    packet.assemble_memory_packet("worker_course")
    refreshed = items.get_memory(mid)
    # updated_at should have changed (touched)
    assert refreshed["updated_at"] != original_updated


# ── Subject hierarchy ──────────────────────────────────────────────

def test_get_subject_parents():
    parents = scope_aliases.get_subject_parents("ap-calculus-bc")
    assert "ap-math" in parents
    assert "ap-stem" in parents


def test_get_subject_hierarchy():
    hierarchy = scope_aliases.get_subject_hierarchy("ap-calculus-bc")
    assert hierarchy[0] == "ap-calculus-bc"
    assert "ap-math" in hierarchy
    assert "ap-stem" in hierarchy


def test_resolve_subject_scopes():
    scopes = scope_aliases.resolve_subject_scopes("ap-calculus-bc")
    assert "subject:ap-calculus-bc" in scopes
    assert "subject:ap-math" in scopes
    assert "subject:ap-stem" in scopes


def test_subject_hierarchy_no_cycles():
    """Adding a parent should not create infinite recursion."""
    scope_aliases.add_subject_parent("test-child", "test-parent")
    scope_aliases.add_subject_parent("test-parent", "test-child")
    hierarchy = scope_aliases.get_subject_hierarchy("test-child")
    assert len(hierarchy) == 2  # child + parent, no infinite loop
    assert "test-child" in hierarchy
    assert "test-parent" in hierarchy


def test_list_subject_hierarchy():
    hierarchy = scope_aliases.list_subject_hierarchy()
    assert "ap-calculus-bc" in hierarchy
    assert "ap-math" in hierarchy["ap-calculus-bc"]


def test_unknown_subject_empty():
    parents = scope_aliases.get_subject_parents("nonexistent-subject")
    assert parents == []
    hierarchy = scope_aliases.get_subject_hierarchy("nonexistent-subject")
    assert hierarchy == ["nonexistent-subject"]
    scopes = scope_aliases.resolve_subject_scopes("nonexistent-subject")
    assert scopes == ["subject:nonexistent-subject"]
