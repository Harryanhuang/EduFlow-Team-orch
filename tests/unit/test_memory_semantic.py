"""Tests for EduFlow Memory semantic search (SiliconFlow API + LanceDB).

Covers: EmbeddingProvider, vector_store, packet semantic recall, CLI commands,
graceful degradation when deps/API unavailable.

Run with pytest:  python3 -m pytest tests/unit/test_memory_semantic.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env, run_cli


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


def _deterministic_encode(text: str, dim: int = 4096) -> list[float]:
    """Deterministic embedding vector for tests.

    Uses a simple bag-of-keywords approach so semantically related
    texts get higher cosine similarity than unrelated texts.
    """
    import numpy as np
    keywords = [
        "neural", "network", "networks", "deep", "learning", "training",
        "python", "list", "comprehension", "tutorial",
        "thread", "threading", "concurrency", "practices",
        "knowledge", "shared", "team", "agent", "private", "note",
        "removed", "alpha", "beta",
    ]
    vec = np.zeros(dim, dtype=np.float32)
    text_lower = text.lower()
    for i, kw in enumerate(keywords):
        if kw in text_lower:
            vec[i % dim] += 1.0
    if np.linalg.norm(vec) == 0:
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        vec = rng.random(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _make_fake_provider(dim: int = 4096):
    """Create a SiliconFlowEmbeddingProvider with fake encode (no API)."""
    from eduflow.memory.embeddings import SiliconFlowEmbeddingProvider, set_embedding_provider
    provider = SiliconFlowEmbeddingProvider.__new__(SiliconFlowEmbeddingProvider)
    provider.api_key = "test-key-not-real"
    provider.model = "test-model"
    provider.api_base = "https://test.example.com/v1"
    provider._dimension = dim
    provider.timeout = 5
    provider.batch_size = 32
    provider.encode = lambda text: _deterministic_encode(text, dim)  # type: ignore
    provider.encode_batch = lambda texts: [_deterministic_encode(t, dim) for t in texts]  # type: ignore
    set_embedding_provider(provider)
    return provider


def _make_dummy_provider(dim: int = 4096):
    """Create a DummyProvider instance."""
    from eduflow.memory.embeddings import DummyProvider, set_embedding_provider
    provider = DummyProvider(dimension=dim)
    set_embedding_provider(provider)
    return provider


def _mock_lancedb_table(rows: list[dict] | None = None):
    """Return a fake LanceDB table backed by an in-memory list."""
    if rows is None:
        rows = []

    import numpy as np
    import pandas as pd

    class FakeTable:
        def __init__(self, data):
            self._rows = list(data)

        def add(self, new_rows):
            for nr in new_rows:
                mid = nr.get("memory_id")
                self._rows = [r for r in self._rows if r.get("memory_id") != mid]
            self._rows.extend(new_rows)

        def delete(self, expr):
            import re
            m = re.search(r'memory_id = "([^"]+)"', expr)
            if m:
                mid = m.group(1)
                self._rows = [r for r in self._rows if r.get("memory_id") != mid]

        def count_rows(self):
            return len(self._rows)

        def search(self, query_vec):
            return FakeQuery(query_vec, self._rows)

    class FakeQuery:
        def __init__(self, query_vec, rows):
            self.query_vec = query_vec
            self.rows = rows
            self.metric_name = "l2"

        def metric(self, name):
            self.metric_name = name
            return self

        def limit(self, n):
            if not self.rows:
                return FakeResult(pd.DataFrame())
            q = np.array(self.query_vec)
            scored = []
            for r in self.rows:
                v = np.array(r.get("vector", []))
                if len(v) == 0 or len(v) != len(q):
                    continue
                if self.metric_name == "cosine":
                    dist = 1.0 - float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9))
                else:
                    dist = float(np.linalg.norm(q - v))
                row = dict(r)
                row["_distance"] = dist
                scored.append(row)
            scored.sort(key=lambda x: x["_distance"])
            df = pd.DataFrame(scored[:n])
            return FakeResult(df)

    class FakeResult:
        def __init__(self, df):
            self.df = df

        def to_pandas(self):
            return self.df

    return FakeTable(rows)


def _enable_vector_store(table_rows=None):
    """Patch vector_store so it thinks LanceDB is available with a fake table."""
    from eduflow.memory import vector_store as vs
    table = _mock_lancedb_table(table_rows)

    class FakeDB:
        def __init__(self, table):
            self._table = table

        def open_table(self, name):
            return self._table

        def create_table(self, name, data, mode="create"):
            self._table._rows = list(data)
            return self._table

        def drop_table(self, name):
            self._table._rows = []

    fake_db = FakeDB(table)
    vs._lancedb_available = True
    vs._lancedb_db = fake_db
    return vs, table


# ── SiliconFlowEmbeddingProvider tests ────────────────────────────

class TestSiliconFlowProvider:
    def test_encode_returns_correct_dimension(self, monkeypatch=None):
        """Provider returns vector of expected dimension."""
        from eduflow.memory.embeddings import SiliconFlowEmbeddingProvider
        provider = SiliconFlowEmbeddingProvider.__new__(SiliconFlowEmbeddingProvider)
        provider.api_key = "test"
        provider.model = "test-model"
        provider.api_base = "https://test.example.com/v1"
        provider._dimension = 4096
        provider.timeout = 5
        provider.batch_size = 32
        provider.encode = lambda text: _deterministic_encode(text, 4096)  # type: ignore
        provider.encode_batch = lambda texts: [_deterministic_encode(t, 4096) for t in texts]  # type: ignore
        vec = provider.encode("hello world")
        assert len(vec) == 4096
        assert all(isinstance(x, float) for x in vec)

    def test_encode_batch_matches_single_encode(self, monkeypatch=None):
        """Batch results match individual encode results."""
        from eduflow.memory.embeddings import SiliconFlowEmbeddingProvider
        provider = SiliconFlowEmbeddingProvider.__new__(SiliconFlowEmbeddingProvider)
        provider.api_key = "test"
        provider.model = "test-model"
        provider.api_base = "https://test.example.com/v1"
        provider._dimension = 4096
        provider.timeout = 5
        provider.batch_size = 32
        provider.encode = lambda text: _deterministic_encode(text, 4096)  # type: ignore
        provider.encode_batch = lambda texts: [_deterministic_encode(t, 4096) for t in texts]  # type: ignore
        texts = ["hello", "world", "test"]
        batch = provider.encode_batch(texts)
        single = [provider.encode(t) for t in texts]
        assert len(batch) == len(single)
        for b, s in zip(batch, single):
            assert b == s

    def test_dummy_provider_returns_zero_vectors(self, monkeypatch=None):
        """DummyProvider returns zero vectors of correct dimension."""
        from eduflow.memory.embeddings import DummyProvider
        provider = DummyProvider(dimension=4096)
        vec = provider.encode("hello")
        assert vec == [0.0] * 4096
        batch = provider.encode_batch(["a", "b"])
        assert batch == [[0.0] * 4096, [0.0] * 4096]
        assert provider.backend == "dummy"
        assert provider.dimension == 4096

    def test_provider_factory_with_key(self, monkeypatch=None):
        """get_embedding_provider returns SiliconFlow provider when key is set."""
        from eduflow.memory.embeddings import get_embedding_provider, reset_embedding_provider
        import os
        old = os.environ.get("SILICONFLOW_API_KEY")
        try:
            os.environ["SILICONFLOW_API_KEY"] = "test-key-123"
            reset_embedding_provider()
            provider = get_embedding_provider()
            assert "siliconflow" in provider.backend
        finally:
            if old is None:
                os.environ.pop("SILICONFLOW_API_KEY", None)
            else:
                os.environ["SILICONFLOW_API_KEY"] = old
            reset_embedding_provider()

    def test_provider_factory_without_key(self, monkeypatch=None):
        """get_embedding_provider returns DummyProvider when no key."""
        from eduflow.memory.embeddings import get_embedding_provider, reset_embedding_provider
        import os
        old_sk = os.environ.get("SILICONFLOW_API_KEY")
        old_ek = os.environ.get("EDUFLOW_EMBEDDING_API_KEY")
        try:
            os.environ.pop("SILICONFLOW_API_KEY", None)
            os.environ.pop("EDUFLOW_EMBEDDING_API_KEY", None)
            reset_embedding_provider()
            provider = get_embedding_provider()
            assert provider.backend == "dummy"
        finally:
            if old_sk is not None:
                os.environ["SILICONFLOW_API_KEY"] = old_sk
            if old_ek is not None:
                os.environ["EDUFLOW_EMBEDDING_API_KEY"] = old_ek
            reset_embedding_provider()


# ── Vector store tests ────────────────────────────────────────────

class TestVectorStore:
    def test_index_memory_then_search_similar(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            vs.index_memory(
                "MI-001", "python threading best practices",
                {"scope": "team", "kind": "workflow_rule", "layer": "core", "importance": 8, "status": "confirmed"},
            )
            results = vs.search_similar("threading concurrency", top_k=3)
            assert len(results) >= 1
            assert results[0]["memory_id"] == "MI-001"
            _reset_db()

    def test_search_similar_sorted_by_similarity(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            vs.index_memory("MI-A", "deep learning neural networks",
                            {"scope": "team", "kind": "domain_fact", "layer": "core", "importance": 5, "status": "confirmed"})
            vs.index_memory("MI-B", "python list comprehension tutorial",
                            {"scope": "team", "kind": "domain_fact", "layer": "core", "importance": 5, "status": "confirmed"})
            results = vs.search_similar("neural network training", top_k=2)
            assert len(results) == 2
            assert results[0]["memory_id"] == "MI-A"
            assert results[0]["score"] >= results[1]["score"]
            _reset_db()

    def test_search_similar_scope_filter(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            vs.index_memory("MI-team", "shared team knowledge",
                            {"scope": "team", "kind": "workflow_rule", "layer": "core", "importance": 5, "status": "confirmed"})
            vs.index_memory("MI-agent", "agent private note",
                            {"scope": "agent:worker", "kind": "note", "layer": "episode", "importance": 5, "status": "confirmed"})
            results = vs.search_similar("knowledge note", scope_filter="team", top_k=5)
            assert all(r["scope"] == "team" for r in results)
            assert any(r["memory_id"] == "MI-team" for r in results)
            _reset_db()

    def test_remove_from_index(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            vs.index_memory("MI-rm", "to be removed",
                            {"scope": "team", "kind": "note", "layer": "episode", "importance": 5, "status": "confirmed"})
            assert len(vs.search_similar("removed", top_k=5)) == 1
            vs.remove_from_index("MI-rm")
            assert vs.search_similar("removed", top_k=5) == []
            _reset_db()

    def test_index_all_confirmed_rebuild(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            add_memory(scope="team", kind="domain_fact", content="alpha", status="confirmed", importance=5)
            add_memory(scope="team", kind="domain_fact", content="beta", status="confirmed", importance=5)
            add_memory(scope="team", kind="note", content="candidate only", status="candidate", importance=5)
            count = vs.index_all_confirmed()
            assert count == 2
            assert vs.index_status()["row_count"] == 2
            _reset_db()

    def test_index_memory_upsert_no_duplicates(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            _make_fake_provider(dim=4096)
            _enable_vector_store()
            vs.index_memory("MI-up", "content v1",
                            {"scope": "team", "kind": "note", "layer": "episode", "importance": 5, "status": "confirmed"})
            vs.index_memory("MI-up", "content v2 updated",
                            {"scope": "team", "kind": "note", "layer": "episode", "importance": 5, "status": "confirmed"})
            assert vs.index_status()["row_count"] == 1
            _reset_db()


# ── Packet integration tests ──────────────────────────────────────

class TestPacketSemanticRecall:
    def test_semantic_recall_supplements_scope_match(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet

            add_alias("worker_test", "agent:worker_test")
            add_memory(scope="agent:worker_test", kind="note",
                       content="scope matched note", status="confirmed", importance=5)
            add_memory(scope="team", kind="domain_fact",
                       content="cross scope shared knowledge", status="confirmed", importance=9)

            with mock.patch("eduflow.memory.packet._semantic_recall") as mock_recall:
                mock_recall.return_value = ["- [semantic][domain_fact] cross scope shared knowledge (importance=9)"]
                packet = assemble_memory_packet("worker_test")
                assert "[semantic]" in packet
                assert "cross scope shared knowledge" in packet
                assert "scope matched note" in packet
            _reset_db()

    def test_semantic_recall_does_not_duplicate_scope_match(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet

            add_alias("worker_test", "agent:worker_test")
            add_memory(scope="agent:worker_test", kind="note",
                       content="scope matched note", status="confirmed", importance=5)

            with mock.patch("eduflow.memory.packet._semantic_recall") as mock_recall:
                mock_recall.return_value = []
                packet = assemble_memory_packet("worker_test")
                assert "scope matched note" in packet
                assert "[semantic]" not in packet
            _reset_db()

    def test_semantic_lines_dropped_first_on_budget_overflow(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet

            add_alias("worker_test", "agent:worker_test")
            for i in range(5):
                add_memory(
                    scope="agent:worker_test", kind="note",
                    content="x", summary="x" * 200,
                    status="confirmed", importance=5,
                )

            with mock.patch("eduflow.memory.packet._semantic_recall") as mock_recall:
                mock_recall.return_value = ["- [semantic][note] should be dropped first (importance=9)"]
                packet = assemble_memory_packet("worker_test")
                assert "[semantic]" not in packet
            _reset_db()

    def test_packet_works_without_vector_index(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory.items import add_memory
            from eduflow.memory.scope_aliases import add_alias
            from eduflow.memory.packet import assemble_memory_packet

            add_alias("worker_test", "agent:worker_test")
            add_memory(scope="agent:worker_test", kind="note",
                       content="scope matched note", status="confirmed", importance=5)

            with mock.patch("eduflow.memory.vector_store.search_similar", side_effect=ImportError("no lancedb")):
                packet = assemble_memory_packet("worker_test")
                assert "scope matched note" in packet
                assert "Relevant Confirmed Memories" in packet
            _reset_db()


# ── CLI tests ─────────────────────────────────────────────────────

class TestSemanticCLI:
    def test_cli_search_outputs_top5_results(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            fake_results = [
                {"memory_id": f"MI-{i}", "content": f"result {i}", "score": 0.9 - i * 0.05,
                 "scope": "team", "kind": "note", "layer": "episode", "importance": 5, "status": "confirmed"}
                for i in range(5)
            ]
            with mock.patch("eduflow.memory.vector_store.index_status") as mock_status, \
                 mock.patch("eduflow.memory.vector_store.search_similar") as mock_search:
                mock_status.return_value = {"available": True, "backend": "siliconflow", "dimension": 4096, "row_count": 100, "lancedb_dir": "/tmp/lancedb"}
                mock_search.return_value = fake_results
                rc, out, err = run_cli(["memory", "search", "test query"])
                assert rc == 0
                assert "Semantic search results" in out
                assert "MI-0" in out
                assert out.count("MI-") >= 5
            _reset_db()

    def test_cli_reindex_count(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            with mock.patch("eduflow.memory.vector_store.index_status") as mock_status, \
                 mock.patch("eduflow.memory.vector_store.index_all_confirmed") as mock_reindex:
                mock_status.return_value = {"available": True, "backend": "siliconflow", "dimension": 4096, "row_count": 0, "lancedb_dir": "/tmp/lancedb"}
                mock_reindex.return_value = 7
                rc, out, err = run_cli(["memory", "reindex"])
                assert rc == 0
                assert "7" in out
            _reset_db()

    def test_cli_test_embedding_output(self, monkeypatch=None):
        with isolated_env():
            import os
            os.environ["SILICONFLOW_API_KEY"] = "test-key-not-real"
            from eduflow.memory.embeddings import reset_embedding_provider, set_embedding_provider, SiliconFlowEmbeddingProvider
            reset_embedding_provider()
            fake_provider = SiliconFlowEmbeddingProvider.__new__(SiliconFlowEmbeddingProvider)
            fake_provider.api_key = "test-key"
            fake_provider.model = "test-model"
            fake_provider.api_base = "https://test.example.com/v1"
            fake_provider._dimension = 4096
            fake_provider.timeout = 5
            fake_provider.batch_size = 32
            fake_provider.encode = lambda text: _deterministic_encode(text, 4096)  # type: ignore
            set_embedding_provider(fake_provider)
            rc, out, err = run_cli(["memory", "test-embedding", "hello"])
            assert rc == 0
            assert "4096" in out
            assert "siliconflow" in out
            from eduflow.memory.embeddings import reset_embedding_provider
            reset_embedding_provider()


# ── Graceful degradation tests ────────────────────────────────────

class TestGracefulDegradation:
    def test_vector_store_noop_when_lancedb_unavailable(self, monkeypatch=None):
        with isolated_env():
            _init_db()
            from eduflow.memory import vector_store as vs
            vs._lancedb_available = False
            vs._lancedb_db = None
            assert vs.search_similar("query") == []
            assert vs.index_all_confirmed() == 0
            assert vs.index_status()["available"] is False
            vs.index_memory("MI-x", "content", {})
            vs.remove_from_index("MI-x")
            _reset_db()

    def test_dummy_provider_dimension(self, monkeypatch=None):
        with isolated_env():
            from eduflow.memory.embeddings import DummyProvider
            provider = DummyProvider(dimension=4096)
            assert provider.dimension == 4096
            assert provider.backend == "dummy"
            assert provider.encode("hello") == [0.0] * 4096
            assert provider.encode_batch(["a", "b"]) == [[0.0] * 4096, [0.0] * 4096]
