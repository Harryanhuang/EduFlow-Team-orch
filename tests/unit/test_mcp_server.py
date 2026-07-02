"""Tests for EduFlow Memory MCP server tools."""
from __future__ import annotations

import pytest

pytestmark = []

try:
    from eduflow.memory import mcp_server as mcp_srv
except ImportError as exc:
    pytestmark.append(pytest.mark.skip(reason=f"mcp dependency not installed: {exc}"))
    mcp_srv = None  # type: ignore


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    """Use a temporary DB for each test."""
    from eduflow.memory import db

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


@pytest.mark.skipif(mcp_srv is None, reason="mcp not installed")
def test_memory_search_returns_empty_when_no_data():
    result = mcp_srv.memory_search("closeout")
    assert result == []


@pytest.mark.skipif(mcp_srv is None, reason="mcp not installed")
def test_memory_profile_round_trip():
    mcp_srv.memory_set_profile("output_language", "bilingual")
    entry = mcp_srv.memory_get_profile("output_language")
    assert entry is not None
    assert entry["value"] == "bilingual"
    assert entry["value_type"] == "text"


@pytest.mark.skipif(mcp_srv is None, reason="mcp not installed")
def test_memory_candidate_lifecycle():
    result = mcp_srv.memory_add_candidate(
        scope="team",
        kind="note",
        content="test candidate from mcp",
        reason="unit test",
    )
    assert result["status"] == "proposed"
    candidate_id = result["candidate_id"]

    candidates = mcp_srv.memory_list_candidates()
    assert any(c["candidate_id"] == candidate_id for c in candidates)

    result = mcp_srv.memory_promote(candidate_id, reviewer="manager")
    memory_id = result["memory_id"]
    assert memory_id.startswith("MI-")

    item = mcp_srv.memory_get(memory_id)
    assert item is not None
    assert item["status"] == "confirmed"


@pytest.mark.skipif(mcp_srv is None, reason="mcp not installed")
def test_memory_assemble_packet_includes_profile():
    mcp_srv.memory_set_profile("output_language", "bilingual")
    # Add a confirmed memory so packet is non-empty.
    cand = mcp_srv.memory_add_candidate(scope="team", kind="note", content="always use plan mode")
    mcp_srv.memory_promote(cand["candidate_id"], reviewer="manager")

    packet = mcp_srv.memory_assemble_packet("worker_course")
    assert "User Preferences" in packet
    assert "output_language: bilingual" in packet
    assert "always use plan mode" in packet
