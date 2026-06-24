"""LanceDB vector store for semantic memory search.

Manages a single LanceDB table (memory_items) for vector indexing
and similarity search.  All functions degrade gracefully when
lancedb is not installed — they silently no-op or return empty results.

Storage: ~/.eduflow/lancedb/
Table:   memory_items
Schema:  [memory_id(str), vector(list[float]), content(str),
          scope(str), kind(str), layer(str),
          importance(int), status(str), updated_at(str)]
"""
from __future__ import annotations

import logging
from pathlib import Path

from eduflow.memory.embeddings import get_embedding_provider

_log = logging.getLogger(__name__)

MEMORY_TABLE = "memory_items"

# Lazy imports — None when lancedb is unavailable
_lancedb = None
_lancedb_db = None
_lancedb_available: bool | None = None  # None = not checked yet


def _is_available() -> bool:
    """Check if lancedb is importable and functional."""
    global _lancedb, _lancedb_db, _lancedb_available
    if _lancedb_available is not None:
        return _lancedb_available
    try:
        import lancedb as ldb
        _lancedb = ldb
        _lancedb_available = True
    except ImportError:
        _lancedb_available = False
        _log.debug("lancedb not installed; vector store disabled")
    return _lancedb_available


def _lancedb_dir() -> Path:
    """Return the LanceDB storage directory."""
    from eduflow.runtime.paths import state_dir
    d = state_dir() / "lancedb"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_db():
    """Get or create LanceDB connection (singleton per process)."""
    global _lancedb_db
    if _lancedb_db is not None:
        return _lancedb_db
    if not _is_available():
        return None
    try:
        db_path = str(_lancedb_dir())
        _lancedb_db = _lancedb.connect(db_path)
        return _lancedb_db
    except Exception as exc:
        _log.warning("Failed to connect to LanceDB at %s: %s", _lancedb_dir(), exc)
        return None


def get_or_create_table():
    """Get or create the memory_items LanceDB table.

    Returns the Table object, or None if lancedb is unavailable.
    """
    db = _get_db()
    if db is None:
        return None
    try:
        return db.open_table(MEMORY_TABLE)
    except Exception:
        # Table doesn't exist yet — will be created on first insert
        return None


def index_memory(
    memory_id: str,
    content: str,
    metadata: dict,
) -> None:
    """Index or update a single memory in the vector store.

    metadata keys: scope, kind, layer, importance, status, updated_at
    Upserts by memory_id (old vector is replaced).
    """
    if not _is_available():
        return
    if not content or not content.strip():
        return

    try:
        provider = get_embedding_provider()
        vector = provider.encode(content)
        if not any(v != 0.0 for v in vector):
            return  # encoding failed; don't index zero vectors
    except Exception as exc:
        _log.debug("embedding failed for %s: %s", memory_id, exc)
        return

    row = {
        "memory_id": memory_id,
        "vector": vector,
        "content": content.strip()[:2000],
        "scope": metadata.get("scope", ""),
        "kind": metadata.get("kind", ""),
        "layer": metadata.get("layer", ""),
        "importance": int(metadata.get("importance", 5)),
        "status": metadata.get("status", "confirmed"),
        "updated_at": metadata.get("updated_at", ""),
    }

    try:
        db = _get_db()
        if db is None:
            return
        table = get_or_create_table()
        if table is None:
            # Create new table with this first row
            db.create_table(MEMORY_TABLE, [row])
            return
        # Upsert: delete old row then insert
        try:
            table.delete(f'memory_id = "{memory_id}"')
        except Exception:
            pass  # row may not exist yet
        table.add([row])
    except Exception as exc:
        _log.debug("index_memory failed for %s: %s", memory_id, exc)


def remove_from_index(memory_id: str) -> None:
    """Remove a memory from the vector index."""
    if not _is_available():
        return
    try:
        table = get_or_create_table()
        if table is None:
            return
        table.delete(f'memory_id = "{memory_id}"')
    except Exception as exc:
        _log.debug("remove_from_index failed for %s: %s", memory_id, exc)


def index_all_confirmed() -> int:
    """Full rebuild: clear table, re-index all confirmed memories.

    Returns the number of memories indexed.
    """
    if not _is_available():
        return 0

    try:
        from eduflow.memory.items import list_memories

        confirmed = list_memories(status="confirmed", limit=10000)
        if not confirmed:
            return 0

        provider = get_embedding_provider()

        db = _get_db()
        if db is None:
            return 0

        # Drop existing table for clean rebuild
        try:
            db.drop_table(MEMORY_TABLE)
        except Exception:
            pass

        rows = []
        for m in confirmed:
            content = m.get("content", "")
            if not content or not content.strip():
                continue
            try:
                vector = provider.encode(content)
                if not any(v != 0.0 for v in vector):
                    continue
            except Exception:
                continue
            rows.append({
                "memory_id": m.get("id", ""),
                "vector": vector,
                "content": content.strip()[:2000],
                "scope": m.get("scope", ""),
                "kind": m.get("kind", ""),
                "layer": m.get("layer", ""),
                "importance": int(m.get("importance", 5)),
                "status": m.get("status", "confirmed"),
                "updated_at": m.get("updated_at", ""),
            })

        if rows:
            db.create_table(MEMORY_TABLE, rows)

        return len(rows)
    except Exception as exc:
        _log.warning("index_all_confirmed failed: %s", exc)
        return 0


def search_similar(
    query_text: str,
    top_k: int = 5,
    scope_filter: str | None = None,
    min_importance: int = 0,
) -> list[dict]:
    """Semantic similarity search.

    Returns list of dicts: {memory_id, content, score, scope, kind,
    layer, importance, status}, sorted by score descending.
    score is cosine similarity (0–1, higher = more similar).
    """
    if not _is_available():
        return []
    if not query_text or not query_text.strip():
        return []

    try:
        provider = get_embedding_provider()
        query_vec = provider.encode(query_text)
        if not any(v != 0.0 for v in query_vec):
            return []
    except Exception as exc:
        _log.debug("query encoding failed: %s", exc)
        return []

    try:
        table = get_or_create_table()
        if table is None:
            return []
        # LanceDB cosine returns distance (lower = more similar)
        results = (
            table.search(query_vec)
            .metric("cosine")
            .limit(top_k * 2)  # over-fetch to allow filtering
        )
        df = results.to_pandas()
    except Exception:
        try:
            # Fallback: L2 distance
            results = table.search(query_vec).limit(top_k * 2)
            df = results.to_pandas()
        except Exception as exc:
            _log.debug("vector search failed: %s", exc)
            return []

    if df.empty:
        return []

    out: list[dict] = []
    for _, row in df.iterrows():
        # Filter by scope if requested
        if scope_filter:
            row_scope = row.get("scope", "")
            if row_scope != scope_filter:
                continue
        # Filter by importance
        row_imp = int(row.get("importance", 0))
        if row_imp < min_importance:
            continue

        # LanceDB cosine returns distance (lower = more similar)
        # Convert to similarity score (higher = more similar)
        raw_score = float(row.get("_distance", 1.0))
        score = max(0.0, 1.0 - raw_score) if raw_score <= 2.0 else 0.0

        out.append({
            "memory_id": row.get("memory_id", ""),
            "content": row.get("content", ""),
            "score": round(score, 4),
            "scope": row.get("scope", ""),
            "kind": row.get("kind", ""),
            "layer": row.get("layer", ""),
            "importance": row_imp,
            "status": row.get("status", ""),
        })

    # Sort by score descending
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:top_k]


def index_status() -> dict:
    """Return index status: row count, backend, lancedb availability."""
    provider = get_embedding_provider()
    status: dict = {
        "available": _is_available(),
        "backend": provider.backend,
        "dimension": provider.dimension,
        "row_count": 0,
        "lancedb_dir": str(_lancedb_dir()),
    }
    if not _is_available():
        return status

    try:
        table = get_or_create_table()
        if table is not None:
            status["row_count"] = table.count_rows()
    except Exception:
        pass

    return status
