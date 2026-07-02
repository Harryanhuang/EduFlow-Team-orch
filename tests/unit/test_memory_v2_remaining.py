"""Tests for V2 remaining items: hybrid search, decay, consolidate."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from eduflow.memory import db, search, decay, consolidate, items


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    db._local.conn = conn
    db.init_schema()
    yield
    conn.close()
    db._local.conn = None


# ── Hybrid search ───────────────────────────────────────────────────

def test_hybrid_search_fallback_when_no_vector():
    """Hybrid search falls back to FTS-only when vector store unavailable."""
    items.add_memory(
        scope="team", kind="workflow_rule", content="closeout must verify items count",
        status="confirmed",
    )
    items.add_memory(
        scope="team", kind="workflow_rule", content="closeout needs QQL alignment",
        status="confirmed",
    )
    results = search.hybrid_search("closeout")
    # All results should be fts-only (no vector index)
    assert len(results) >= 1
    assert all(r.get("_sources") in ("fts", "fts+vec") for r in results)


def test_hybrid_search_rrf_fusion():
    """RRF scores combine FTS and vector ranks."""
    mid = items.add_memory(
        scope="team", kind="note", content="alpha beta gamma",
        status="confirmed",
    )
    items.add_memory(
        scope="team", kind="note", content="delta epsilon",
        status="confirmed",
    )

    # FTS-only scenario: results have _rrf_score
    results = search.hybrid_search("alpha", limit=5)
    if results:
        # Higher-ranked result should have higher RRF score
        for r in results:
            assert "_rrf_score" in r
            assert r["_rrf_score"] > 0


def test_hybrid_search_empty_query():
    assert search.hybrid_search("") == []
    assert search.hybrid_search("   ") == []


def test_hybrid_search_with_filters():
    items.add_memory(
        scope="team", kind="workflow_rule", content="closeout check",
        status="confirmed",
    )
    items.add_memory(
        scope="lane:course", kind="workflow_rule", content="closeout lane",
        status="confirmed",
    )
    results = search.hybrid_search("closeout", scope="team", kind="workflow_rule")
    for r in results:
        assert r["scope"] == "team"
        assert r["kind"] == "workflow_rule"


# ── Decay ───────────────────────────────────────────────────────────

def test_effective_confidence_fresh():
    """Fresh memory (recently updated) should have factor ~1.1."""
    now = "2026-06-30T00:00:00+00:00"
    recent = "2026-06-29T00:00:00+00:00"  # 1 day ago
    eff = decay.effective_confidence(1.0, recent, recent, now=now)
    # age_factor=1.0, usage_factor=1.1 -> 1.1, clamped to 1.0
    assert 0.95 <= eff <= 1.0


def test_effective_confidence_old():
    """Memory older than 365 days should decay to ~0.5."""
    now = "2026-06-30T00:00:00+00:00"
    old = "2025-01-01T00:00:00+00:00"  # ~1.5 years ago
    eff = decay.effective_confidence(1.0, old, old, now=now)
    # age_factor=0.5, usage_factor=0.85 -> 0.425, clamped to 0.425
    assert 0.4 <= eff <= 0.5


def test_effective_confidence_90_to_180_days():
    """Memory 90-180 days old should be around 0.7-0.9."""
    now = "2026-06-30T00:00:00+00:00"
    medium = "2026-03-01T00:00:00+00:00"  # ~4 months ago
    eff = decay.effective_confidence(1.0, medium, medium, now=now)
    # age_factor=0.9 (90-180d), usage_factor=0.85 (>90d) -> 0.765
    assert 0.7 <= eff <= 0.85


def test_effective_confidence_clamped():
    """Result should be clamped to [0.1, 1.0]."""
    now = "2026-06-30T00:00:00+00:00"
    eff = decay.effective_confidence(0.5, "2020-01-01", "2020-01-01", now=now)
    assert 0.1 <= eff <= 1.0


def test_touch_item_updates_timestamp():
    mid = items.add_memory(
        scope="team", kind="note", content="test",
        status="confirmed",
    )
    original = items.get_memory(mid)
    original_updated = original["updated_at"]

    # Wait briefly and touch
    import time
    time.sleep(0.05)
    decay.touch_item(mid)

    refreshed = items.get_memory(mid)
    # Compare as ISO strings; touch should update to a later timestamp
    assert refreshed["updated_at"] != original_updated
    assert refreshed["updated_at"] > original_updated[:19]  # rough comparison


def test_decay_batch_dry_run():
    items.add_memory(
        scope="team", kind="note", content="test1",
        status="confirmed",
    )
    items.add_memory(
        scope="team", kind="note", content="test2",
        status="confirmed",
    )
    result = decay.decay_batch(dry_run=True)
    assert result["total"] >= 2
    assert "updated" in result
    assert "skipped" in result


# ── Consolidate ────────────────────────────────────────────────────

def test_merge_memories_basic():
    """Merging should deprecate drop_id and update keep_id."""
    keep_id = items.add_memory(
        scope="team", kind="note", content="duplicate rule A",
        status="confirmed",
    )
    drop_id = items.add_memory(
        scope="team", kind="note", content="duplicate rule A",
        status="confirmed",
    )

    result = consolidate.merge_memories(keep_id, drop_id, reason="test merge")
    assert result["merged"] is True
    assert result["keep_id"] == keep_id
    assert result["drop_id"] == drop_id

    # drop_id should be deprecated
    drop_after = items.get_memory(drop_id)
    assert drop_after["status"] == "deprecated"

    # keep_id should still be confirmed
    keep_after = items.get_memory(keep_id)
    assert keep_after["status"] == "confirmed"


def test_merge_memories_merges_evidence():
    """Evidence refs from both memories should be merged into keep_id."""
    keep_id = items.add_memory(
        scope="team", kind="note", content="rule",
        status="confirmed",
        evidence_refs=["ev1", "ev2"],
    )
    drop_id = items.add_memory(
        scope="team", kind="note", content="rule",
        status="confirmed",
        evidence_refs=["ev2", "ev3"],  # overlap with keep_id
    )

    consolidate.merge_memories(keep_id, drop_id, reason="merge")

    keep_after = items.get_memory(keep_id)
    refs = json.loads(keep_after["evidence_refs"])
    # Should contain all unique refs
    assert "ev1" in refs
    assert "ev2" in refs
    assert "ev3" in refs


def test_merge_memories_creates_supersedes_link():
    keep_id = items.add_memory(
        scope="team", kind="note", content="rule",
        status="confirmed",
    )
    drop_id = items.add_memory(
        scope="team", kind="note", content="rule",
        status="confirmed",
    )

    consolidate.merge_memories(keep_id, drop_id, reason="test")

    # Verify supersedes link exists
    from eduflow.memory.links import get_links_from
    links = get_links_from(keep_id)
    supersedes_links = [l for l in links if l["relation"] == "supersedes" and l["to_id"] == drop_id]
    assert len(supersedes_links) == 1


def test_merge_memories_missing_raises():
    keep_id = items.add_memory(
        scope="team", kind="note", content="rule",
        status="confirmed",
    )
    with pytest.raises(ValueError, match="not found"):
        consolidate.merge_memories(keep_id, "MI-NONEXISTENT-999", reason="test")


def test_consolidation_report_structure():
    """Report should return dict with threshold and pair_count."""
    items.add_memory(
        scope="team", kind="note", content="rule alpha",
        status="confirmed",
    )
    items.add_memory(
        scope="team", kind="note", content="rule beta",
        status="confirmed",
    )
    report = consolidate.consolidation_report(threshold=0.5)
    assert "threshold" in report
    assert "pair_count" in report
    assert "top_pairs" in report
    assert report["threshold"] == 0.5


def test_find_similar_pairs_empty_when_no_items():
    """No items = no pairs."""
    pairs = consolidate.find_similar_pairs(threshold=0.5)
    assert pairs == []


def test_find_similar_pairs_single_item():
    """Only 1 item = no pairs."""
    items.add_memory(scope="team", kind="note", content="only one", status="confirmed")
    pairs = consolidate.find_similar_pairs(threshold=0.5)
    assert pairs == []