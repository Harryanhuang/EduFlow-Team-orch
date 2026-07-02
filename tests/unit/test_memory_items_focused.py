"""Focused tests for eduflow.memory.items — CRUD, filtering, scope isolation.

Covers:
- add_memory: basic insert, returns ID, validation
- get_memory: fetch correct item, missing returns None
- list_memories: status/kind/scope/layer filters, ordering
- update_memory: allowed fields, rejected fields
- deprecate_memory: status transition, idempotent
- supersede_memory: old deprecated, new linked
- Sequence ID generation (MI-YYYYMMDD-NNN)
- Scope isolation: items in different scopes don't leak
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── add_memory ─────────────────────────────────────────────────────

class TestAddMemory:
    def test_basic_insert_returns_id(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            mid = add_memory(
                scope="team", kind="note", content="hello world",
            )
            assert mid.startswith("MI-")
            _reset_db()

    def test_invalid_kind_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="invalid kind"):
                add_memory(scope="team", kind="bogus", content="x")
            _reset_db()

    def test_invalid_layer_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="invalid layer"):
                add_memory(
                    scope="team", kind="note", content="x", layer="bogus",
                )
            _reset_db()

    def test_invalid_status_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="invalid status"):
                add_memory(
                    scope="team", kind="note", content="x", status="bogus",
                )
            _reset_db()

    def test_empty_content_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="content cannot be empty"):
                add_memory(scope="team", kind="note", content="   ")
            _reset_db()

    def test_importance_out_of_range_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="importance"):
                add_memory(
                    scope="team", kind="note", content="x", importance=0,
                )
            with pytest.raises(ValueError, match="importance"):
                add_memory(
                    scope="team", kind="note", content="x", importance=11,
                )
            _reset_db()

    def test_confidence_out_of_range_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            with pytest.raises(ValueError, match="confidence"):
                add_memory(
                    scope="team", kind="note", content="x", confidence=1.5,
                )
            _reset_db()

    def test_all_valid_kinds_accepted(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            kinds = [
                "role_rule", "workflow_rule", "decision", "mistake",
                "preference", "handoff", "domain_fact", "runtime_rule", "note",
            ]
            for kind in kinds:
                mid = add_memory(
                    scope="team", kind=kind, content=f"test {kind}",
                )
                assert mid.startswith("MI-")
            _reset_db()

    def test_all_valid_layers_accepted(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            layers = [
                "core", "task", "episode", "decision", "reflection", "archive",
            ]
            for layer in layers:
                mid = add_memory(
                    scope="team", kind="note", content=f"test {layer}",
                    layer=layer,
                )
                assert mid.startswith("MI-")
            _reset_db()


# ── get_memory ─────────────────────────────────────────────────────

class TestGetMemory:
    def test_fetches_correct_item(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, get_memory
            mid = add_memory(
                scope="team", kind="note", content="fetch me",
                importance=7,
            )
            item = get_memory(mid)
            assert item is not None
            assert item["content"] == "fetch me"
            assert item["importance"] == 7
            assert item["scope"] == "team"
            _reset_db()

    def test_missing_id_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import get_memory
            assert get_memory("MI-00000000-999") is None
            _reset_db()


# ── sequence ID ────────────────────────────────────────────────────

class TestSequenceId:
    def test_ids_increment(self):
        """Multiple inserts on the same day produce incrementing sequence numbers."""
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            id1 = add_memory(scope="team", kind="note", content="first")
            id2 = add_memory(scope="team", kind="note", content="second")
            id3 = add_memory(scope="team", kind="note", content="third")
            seq1 = int(id1.split("-")[-1])
            seq2 = int(id2.split("-")[-1])
            seq3 = int(id3.split("-")[-1])
            assert seq2 == seq1 + 1
            assert seq3 == seq2 + 1
            _reset_db()


# ── list_memories ──────────────────────────────────────────────────

class TestListMemories:
    def test_default_returns_confirmed_only(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="conf",
                status="confirmed",
            )
            add_memory(
                scope="team", kind="note", content="cand",
                status="candidate",
            )
            result = list_memories()
            assert len(result) == 1
            assert result[0]["status"] == "confirmed"
            _reset_db()

    def test_filter_by_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="a", status="confirmed",
            )
            add_memory(
                scope="team", kind="note", content="b", status="candidate",
            )
            add_memory(
                scope="team", kind="note", content="c", status="deprecated",
            )
            confirmed = list_memories(status="confirmed")
            candidates = list_memories(status="candidate")
            deprecated = list_memories(status="deprecated")
            assert len(confirmed) == 1
            assert len(candidates) == 1
            assert len(deprecated) == 1
            _reset_db()

    def test_filter_by_kind(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="n", status="confirmed",
            )
            add_memory(
                scope="team", kind="decision", content="d",
                status="confirmed",
            )
            notes = list_memories(kind="note")
            decisions = list_memories(kind="decision")
            assert len(notes) == 1
            assert len(decisions) == 1
            _reset_db()

    def test_filter_by_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="t", status="confirmed",
            )
            add_memory(
                scope="agent:alice", kind="note", content="a",
                status="confirmed",
            )
            team = list_memories(scope="team")
            alice = list_memories(scope="agent:alice")
            assert len(team) == 1
            assert len(alice) == 1
            _reset_db()

    def test_filter_by_layer(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="c", status="confirmed",
                layer="core",
            )
            add_memory(
                scope="team", kind="note", content="e", status="confirmed",
                layer="episode",
            )
            core = list_memories(layer="core")
            episode = list_memories(layer="episode")
            assert len(core) == 1
            assert len(episode) == 1
            _reset_db()

    def test_ordering_by_importance_desc(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="low", status="confirmed",
                importance=2,
            )
            add_memory(
                scope="team", kind="note", content="high", status="confirmed",
                importance=9,
            )
            result = list_memories()
            assert result[0]["importance"] >= result[1]["importance"]
            _reset_db()

    def test_limit(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            for i in range(10):
                add_memory(
                    scope="team", kind="note", content=f"item {i}",
                    status="confirmed",
                )
            result = list_memories(limit=3)
            assert len(result) == 3
            _reset_db()

    def test_no_status_filter(self):
        """Passing status=None returns all items regardless of status."""
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="c", status="confirmed",
            )
            add_memory(
                scope="team", kind="note", content="p", status="candidate",
            )
            result = list_memories(status="")
            assert len(result) == 2
            _reset_db()


# ── scope isolation ────────────────────────────────────────────────

class TestScopeIsolation:
    def test_different_scopes_do_not_leak(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="agent:alice", kind="note", content="alice secret",
                status="confirmed",
            )
            add_memory(
                scope="agent:bob", kind="note", content="bob secret",
                status="confirmed",
            )
            alice_items = list_memories(scope="agent:alice")
            bob_items = list_memories(scope="agent:bob")
            assert len(alice_items) == 1
            assert alice_items[0]["content"] == "alice secret"
            assert len(bob_items) == 1
            assert bob_items[0]["content"] == "bob secret"
            _reset_db()

    def test_team_scope_does_not_include_agent_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, list_memories
            add_memory(
                scope="team", kind="note", content="team rule",
                status="confirmed",
            )
            add_memory(
                scope="agent:alice", kind="note", content="alice rule",
                status="confirmed",
            )
            team = list_memories(scope="team")
            agent = list_memories(scope="agent:alice")
            assert len(team) == 1
            assert len(agent) == 1
            _reset_db()


# ── update_memory ──────────────────────────────────────────────────

class TestUpdateMemory:
    def test_update_content(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, get_memory, update_memory
            mid = add_memory(
                scope="team", kind="note", content="original",
            )
            ok = update_memory(mid, content="updated content")
            assert ok is True
            item = get_memory(mid)
            assert item["content"] == "updated content"
            _reset_db()

    def test_update_importance(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, get_memory, update_memory
            mid = add_memory(
                scope="team", kind="note", content="x", importance=3,
            )
            update_memory(mid, importance=8)
            item = get_memory(mid)
            assert item["importance"] == 8
            _reset_db()

    def test_update_invalid_field_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, update_memory
            mid = add_memory(scope="team", kind="note", content="x")
            with pytest.raises(ValueError, match="cannot update fields"):
                update_memory(mid, scope="new_scope")
            _reset_db()

    def test_update_missing_id_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import update_memory
            ok = update_memory("MI-00000000-999", content="nope")
            assert ok is False
            _reset_db()

    def test_update_evidence_refs_list(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import (
                add_memory, get_memory, update_memory,
            )
            import json
            mid = add_memory(scope="team", kind="note", content="x")
            update_memory(mid, evidence_refs=["ref1", "ref2"])
            item = get_memory(mid)
            assert json.loads(item["evidence_refs"]) == ["ref1", "ref2"]
            _reset_db()


# ── deprecate_memory ───────────────────────────────────────────────

class TestDeprecateMemory:
    def test_deprecate_changes_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import (
                add_memory, get_memory, deprecate_memory,
            )
            mid = add_memory(
                scope="team", kind="note", content="x", status="confirmed",
            )
            ok = deprecate_memory(mid)
            assert ok is True
            item = get_memory(mid)
            assert item["status"] == "deprecated"
            _reset_db()

    def test_deprecate_already_deprecated_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import (
                add_memory, deprecate_memory,
            )
            mid = add_memory(
                scope="team", kind="note", content="x",
                status="confirmed",
            )
            deprecate_memory(mid)
            ok = deprecate_memory(mid)
            assert ok is False
            _reset_db()

    def test_deprecate_missing_id_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import deprecate_memory
            ok = deprecate_memory("MI-00000000-999")
            assert ok is False
            _reset_db()


# ── supersede_memory ───────────────────────────────────────────────

class TestSupersedeMemory:
    def test_supersede_deprecates_old_links_new(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import (
                add_memory, get_memory, supersede_memory,
            )
            old_id = add_memory(
                scope="team", kind="note", content="old", status="confirmed",
            )
            new_id = add_memory(
                scope="team", kind="note", content="new", status="confirmed",
            )
            ok = supersede_memory(old_id, new_id)
            assert ok is True
            old_item = get_memory(old_id)
            new_item = get_memory(new_id)
            assert old_item["status"] == "deprecated"
            assert new_item["supersedes"] == old_id
            _reset_db()

    def test_supersede_missing_old_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, supersede_memory
            new_id = add_memory(
                scope="team", kind="note", content="new", status="confirmed",
            )
            ok = supersede_memory("MI-00000000-999", new_id)
            assert ok is False
            _reset_db()

    def test_supersede_missing_new_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory, supersede_memory
            old_id = add_memory(
                scope="team", kind="note", content="old", status="confirmed",
            )
            ok = supersede_memory(old_id, "MI-00000000-999")
            assert ok is False
            _reset_db()
