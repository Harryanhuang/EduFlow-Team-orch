"""Embedding providers for semantic memory search.

Primary: SiliconFlow OpenAI-compatible embeddings API
Fallback: DummyProvider (zero vectors) — used when API key is missing or
          API calls fail.

Configuration (env vars):
    SILICONFLOW_API_KEY      required for SiliconFlow provider
    EDUFLOW_EMBEDDING_MODEL  default "Qwen/Qwen3-VL-Embedding-8B"
    SILICONFLOW_API_BASE     default "https://api.siliconflow.cn/v1"
    EDUFLOW_EMBEDDING_DIM    default 4096 (actual dim for the Qwen model)
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

_log = logging.getLogger(__name__)

DEFAULT_MODEL = "Qwen/Qwen3-VL-Embedding-8B"
DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"
DEFAULT_DIMENSION = 4096  # confirmed by live API test
DEFAULT_TIMEOUT = 30
DEFAULT_BATCH_SIZE = 32


class EmbeddingProvider(ABC):
    """Abstract base for text → vector embedding providers."""

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Single text → embedding vector. Never raises."""

    @abstractmethod
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch encode. Returns same list length as input. Never raises."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality."""

    @property
    @abstractmethod
    def backend(self) -> str:
        """Provider/backend name."""


class DummyProvider(EmbeddingProvider):
    """Fallback provider that returns zero vectors.

    Used when no API key is configured or when API calls fail.
    """

    def __init__(self, dimension: int = DEFAULT_DIMENSION) -> None:
        self._dimension = int(dimension or DEFAULT_DIMENSION)

    def encode(self, text: str) -> list[float]:
        return [0.0] * self._dimension

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._dimension for _ in texts]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def backend(self) -> str:
        return "dummy"


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """SiliconFlow OpenAI-compatible embeddings API provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
        dimension: int | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY", "")
        self.model = model or os.environ.get("EDUFLOW_EMBEDDING_MODEL", DEFAULT_MODEL)
        self.api_base = (api_base or os.environ.get("SILICONFLOW_API_BASE", DEFAULT_API_BASE)).rstrip("/")
        self._dimension = int(dimension or os.environ.get("EDUFLOW_EMBEDDING_DIM", DEFAULT_DIMENSION) or DEFAULT_DIMENSION)
        self.timeout = timeout
        self.batch_size = batch_size

    def encode(self, text: str) -> list[float]:
        """Single text → embedding vector."""
        if not text or not text.strip():
            return [0.0] * self._dimension
        results = self.encode_batch([text])
        return results[0] if results else [0.0] * self._dimension

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch encode via SiliconFlow API with automatic batch splitting."""
        if not texts:
            return []

        cleaned = [t.strip() if t else "" for t in texts]
        out: list[list[float]] = [[] for _ in cleaned]
        pending_indices: list[int] = [i for i, t in enumerate(cleaned) if t]

        if not pending_indices:
            return [[0.0] * self._dimension for _ in cleaned]

        pending_texts = [cleaned[i] for i in pending_indices]
        start = 0
        while start < len(pending_texts):
            batch = pending_texts[start : start + self.batch_size]
            try:
                vectors = self._call_api(batch)
            except Exception as exc:
                _log.warning("SiliconFlow embedding batch failed: %s", exc)
                # Return dummy vectors for this batch
                vectors = [[0.0] * self._dimension for _ in batch]

            for offset, vec in enumerate(vectors):
                original_idx = pending_indices[start + offset]
                out[original_idx] = vec
            start += self.batch_size

        # Any index that did not get filled (shouldn't happen) gets zeros
        for i in pending_indices:
            if not out[i]:
                out[i] = [0.0] * self._dimension

        return out

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        """Call SiliconFlow embeddings endpoint.

        Raises on non-recoverable errors. Handles 413 by splitting batch.
        """
        if not self.api_key:
            raise RuntimeError("SiliconFlow API key not configured")

        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.read else ""
            if exc.code == 413 and len(texts) > 1:
                _log.debug("Batch too large (413); splitting and retrying")
                return self._split_and_retry(texts)
            _log.warning("SiliconFlow API HTTP error %s: %s", exc.code, body)
            raise
        except urllib.error.URLError as exc:
            _log.warning("SiliconFlow API URL error: %s", exc)
            raise

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            _log.warning("SiliconFlow API returned invalid JSON: %s", exc)
            raise

        embeddings = []
        for item in result.get("data", []):
            emb = item.get("embedding", [])
            if emb:
                if len(emb) != self._dimension:
                    _log.warning(
                        "Embedding dimension mismatch: expected %d, got %d; using actual",
                        self._dimension, len(emb),
                    )
                    self._dimension = len(emb)
                embeddings.append(emb)
            else:
                embeddings.append([0.0] * self._dimension)

        if len(embeddings) != len(texts):
            _log.warning(
                "Embedding count mismatch: sent %d, received %d",
                len(texts), len(embeddings),
            )
            while len(embeddings) < len(texts):
                embeddings.append([0.0] * self._dimension)

        return embeddings

    def _split_and_retry(self, texts: list[str]) -> list[list[float]]:
        """Split a batch in half and retry each half."""
        if len(texts) <= 1:
            # Cannot split further; return dummy vectors
            return [[0.0] * self._dimension for _ in texts]
        mid = len(texts) // 2
        first = self.encode_batch(texts[:mid])
        second = self.encode_batch(texts[mid:])
        return first + second

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def backend(self) -> str:
        return f"siliconflow:{self.model}"


# Global provider instance (lazy, cached per process)
_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider.

    1. If SILICONFLOW_API_KEY or EDUFLOW_EMBEDDING_API_KEY is set,
       return SiliconFlowEmbeddingProvider.
    2. Otherwise return DummyProvider.
    """
    global _provider
    if _provider is not None:
        return _provider

    api_key = os.environ.get("SILICONFLOW_API_KEY") or os.environ.get("EDUFLOW_EMBEDDING_API_KEY", "")
    if api_key.strip():
        _provider = SiliconFlowEmbeddingProvider(api_key=api_key.strip())
    else:
        _log.info("No embedding API key configured; using DummyProvider")
        _provider = DummyProvider()
    return _provider


def set_embedding_provider(provider: EmbeddingProvider) -> None:
    """Override the global provider (for testing)."""
    global _provider
    _provider = provider


def reset_embedding_provider() -> None:
    """Reset the global provider cache (for testing)."""
    global _provider
    _provider = None
