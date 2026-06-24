"""Tests for EduFlow Memory Phase 1: Memory Core.

Covers: memory_items CRUD, scope_aliases, FTS search, packet integration.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── Schema & Items CRUD ──────────────────────────────────────────

class TestSchemaNewTables:
    def test_schema_creates_new_tables(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.db import get_conn
            conn = get_conn()
            tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "memory_items" in tables
            assert "memory_scope_aliases" in tables
            assert "memory_candidates" in tables
            _reset_db()


class TestMemoryItemsCRUD:
    def test_add_and_get_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, get_memory
            mid = add_memory(
                scope="team", kind="domain_fact",
                content="IGCSE课程体系包含5个学科",
                layer="core", summary="IGCSE 5 subjects",
                importance=8, created_by="test",
                status="confirmed",
            )
            assert mid.startswith("MI-")
            m = get_memory(mid)
            assert m is not None
            assert m["content"] == "IGCSE课程体系包含5个学科"
            assert m["layer"] == "core"
            assert m["kind"] == "domain_fact"
            assert m["status"] == "confirmed"
            assert m["importance"] == 8
            _reset_db()

    def test_add_memory_validates_kind(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="invalid kind"):
                add_memory(scope="team", kind="invalid_kind", content="test")
            _reset_db()

    def test_add_memory_validates_layer(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="invalid layer"):
                add_memory(scope="team", kind="note", content="test", layer="invalid")
            _reset_db()

    def test_list_memories_by_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(scope="team", kind="note", content="team note", status="confirmed")
            add_memory(scope="agent:worker_course", kind="note", content="worker note", status="confirmed")
            team_memories = list_memories(scope="team", status="confirmed")
            assert len(team_memories) == 1
            assert team_memories[0]["content"] == "team note"
            _reset_db()

    def test_list_memories_by_kind(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(scope="team", kind="domain_fact", content="fact", status="confirmed")
            add_memory(scope="team", kind="note", content="note", status="confirmed")
            facts = list_memories(kind="domain_fact", status="confirmed")
            assert len(facts) == 1
            assert facts[0]["kind"] == "domain_fact"
            _reset_db()

    def test_list_memories_by_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(scope="team", kind="note", content="confirmed", status="confirmed")
            add_memory(scope="team", kind="note", content="candidate", status="candidate")
            confirmed = list_memories(status="confirmed")
            assert len(confirmed) == 1
            assert confirmed[0]["content"] == "confirmed"
            _reset_db()

    def test_list_memories_by_layer(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(scope="team", kind="note", content="core", layer="core", status="confirmed")
            add_memory(scope="team", kind="note", content="episode", layer="episode", status="confirmed")
            core = list_memories(layer="core", status="confirmed")
            assert len(core) == 1
            assert core[0]["layer"] == "core"
            _reset_db()

    def test_deprecate_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, deprecate_memory, get_memory
            mid = add_memory(scope="team", kind="note", content="test", status="confirmed")
            ok = deprecate_memory(mid)
            assert ok is True
            m = get_memory(mid)
            assert m["status"] == "deprecated"
            _reset_db()

    def test_deprecate_nonexistent(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import deprecate_memory
            ok = deprecate_memory("MI-99999999-999")
            assert ok is False
            _reset_db()

    def test_supersede_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, supersede_memory, get_memory
            old_id = add_memory(scope="team", kind="note", content="old", status="confirmed")
            new_id = add_memory(scope="team", kind="note", content="new", status="confirmed")
            ok = supersede_memory(old_id, new_id)
            assert ok is True
            old = get_memory(old_id)
            assert old["status"] == "deprecated"
            new = get_memory(new_id)
            assert new["supersedes"] == old_id
            _reset_db()

    def test_update_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, update_memory, get_memory
            mid = add_memory(scope="team", kind="note", content="test", status="confirmed")
            ok = update_memory(mid, content="updated content", importance=9)
            assert ok is True
            m = get_memory(mid)
            assert m["content"] == "updated content"
            assert m["importance"] == 9
            _reset_db()


# ── Scope Aliases ─────────────────────────────────────────────────

class TestScopeAliases:
    def test_add_and_resolve_alias(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.scope_aliases import add_alias, resolve_alias
            add_alias("worker_course", "agent:worker_course")
            resolved = resolve_alias("worker_course")
            assert resolved == "agent:worker_course"
            _reset_db()

    def test_alias_inactive_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.scope_aliases import add_alias, resolve_alias, deactivate_alias
            add_alias("worker_course", "agent:worker_course")
            deactivate_alias("worker_course")
            resolved = resolve_alias("worker_course")
            assert resolved is None
            _reset_db()

    def test_list_aliases(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.scope_aliases import add_alias, list_aliases
            add_alias("a1", "scope:a1")
            add_alias("a2", "scope:a2")
            aliases = list_aliases()
            assert len(aliases) == 2
            _reset_db()

    def test_deactivate_alias(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.scope_aliases import add_alias, deactivate_alias, get_alias
            add_alias("test_alias", "scope:test")
            ok = deactivate_alias("test_alias")
            assert ok is True
            a = get_alias("test_alias")
            assert a["active"] == 0
            _reset_db()


# ── FTS Search ────────────────────────────────────────────────────

class TestFTSSearch:
    def test_fts_search_chinese(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.search import search_memories
            add_memory(scope="team", kind="domain_fact",
                      content="IGCSE课程体系包含数学、物理、化学、生物、英语",
                      status="confirmed")
            results = search_memories("IGCSE")
            assert len(results) >= 1
            assert "IGCSE" in results[0]["content"]
            _reset_db()

    def test_fts_search_like_fallback(self):
        """Test that search works even if we force LIKE fallback."""
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory import search as search_mod
            # Force LIKE fallback by disabling FTS
            original = search_mod._FTS_AVAILABLE
            search_mod._FTS_AVAILABLE = False
            try:
                add_memory(scope="team", kind="note",
                          content="测试LIKE回退搜索",
                          status="confirmed")
                results = search_mod.search_memories("LIKE回退")
                assert len(results) >= 1
            finally:
                search_mod._FTS_AVAILABLE = original
            _reset_db()

    def test_search_with_scope_filter(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.search import search_memories
            add_memory(scope="team", kind="note", content="team searchable item", status="confirmed")
            add_memory(scope="agent:worker", kind="note", content="worker searchable item", status="confirmed")
            results = search_memories("searchable", scope="team")
            assert all(r["scope"] == "team" for r in results)
            _reset_db()

    def test_search_with_kind_filter(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.search import search_memories
            add_memory(scope="team", kind="domain_fact", content="filterable fact", status="confirmed")
            add_memory(scope="team", kind="note", content="filterable note", status="confirmed")
            results = search_memories("filterable", kind="domain_fact")
            assert all(r["kind"] == "domain_fact" for r in results)
            _reset_db()

    def test_search_empty_query(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.search import search_memories
            results = search_memories("")
            assert results == []
            _reset_db()


# ── Memory Packet Integration ─────────────────────────────────────

class TestPacketIntegration:
    def test_packet_includes_confirmed_memories(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet
            add_alias("worker_test", "agent:worker_test")
            add_memory(scope="agent:worker_test", kind="domain_fact",
                      content="important fact", summary="imp fact",
                      status="confirmed", importance=8)
            packet = assemble_memory_packet("worker_test")
            assert "Relevant Confirmed Memories" in packet
            assert "important fact" in packet or "imp fact" in packet
            _reset_db()

    def test_packet_excludes_candidate_memories(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet
            add_alias("worker_test", "agent:worker_test")
            add_memory(scope="agent:worker_test", kind="note",
                      content="candidate memory", status="candidate")
            packet = assemble_memory_packet("worker_test")
            assert "candidate memory" not in (packet or "")
            _reset_db()

    def test_packet_empty_when_no_memories(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.packet import assemble_memory_packet
            packet = assemble_memory_packet("nonexistent_agent")
            assert packet == ""
            _reset_db()
