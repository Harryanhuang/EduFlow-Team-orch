"""Tests for user_profile module."""
from __future__ import annotations

import pytest

from eduflow.memory import user_profile as up


@pytest.fixture(autouse=True)
def _clean_profile(tmp_path, monkeypatch):
    """Use a temporary DB for each test."""
    from eduflow.memory import db

    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    # Bind the same connection to db._local so all modules importing
    # db.get_conn share it.
    db._local.conn = conn
    db.init_schema()
    yield
    conn.close()
    db._local.conn = None


def test_set_and_get_text():
    up.set_profile("output_language", "bilingual")
    entry = up.get_profile("output_language")
    assert entry is not None
    assert entry["value"] == "bilingual"
    assert entry["value_type"] == "text"
    assert entry["confidence"] == 1.0


def test_set_and_get_json():
    up.set_profile(
        "preferred_course_systems",
        ["IGCSE", "CAIE"],
        value_type="json",
        confidence=0.9,
    )
    entry = up.get_profile("preferred_course_systems")
    assert entry["value"] == ["IGCSE", "CAIE"]
    assert entry["value_type"] == "json"
    assert entry["confidence"] == 0.9


def test_set_overwrites():
    up.set_profile("output_language", "english")
    up.set_profile("output_language", "bilingual")
    entry = up.get_profile("output_language")
    assert entry["value"] == "bilingual"


def test_list_profile_sorted_by_confidence():
    up.set_profile("aaa", "low", confidence=0.5)
    up.set_profile("bbb", "high", confidence=0.9)
    entries = up.list_profile()
    assert len(entries) == 2
    assert entries[0]["key"] == "bbb"
    assert entries[1]["key"] == "aaa"


def test_list_profile_prefix_filter():
    up.set_profile("course_igcse", "yes")
    up.set_profile("course_ap", "yes")
    entries = up.list_profile(prefix="course_igcse")
    assert len(entries) == 1
    assert entries[0]["key"] == "course_igcse"


def test_delete_profile():
    up.set_profile("tmp", "value")
    assert up.delete_profile("tmp") is True
    assert up.get_profile("tmp") is None
    assert up.delete_profile("tmp") is False


def test_render_profile_block_respects_budget():
    up.set_profile("k1", "a" * 100)
    up.set_profile("k2", "b" * 100)
    block = up.render_profile_block(max_chars=80)
    # Budget too small for header + any long entry, so entire block is omitted.
    assert block == ""

    # With a larger budget the header and at least one entry appear.
    block = up.render_profile_block(max_chars=200)
    assert block.startswith("## User Preferences")
    assert "k1" in block or "k2" in block
    assert len(block) <= 200


def test_invalid_value_type_raises():
    with pytest.raises(ValueError):
        up.set_profile("x", "y", value_type="invalid")


def test_invalid_confidence_raises():
    with pytest.raises(ValueError):
        up.set_profile("x", "y", confidence=1.5)
