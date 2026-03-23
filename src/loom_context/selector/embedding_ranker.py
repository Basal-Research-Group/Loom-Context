"""Embedding ranker: ranks files using sentence-transformers (HuggingFace).

Requires: pip install loom-context[ai]
Model: all-MiniLM-L6-v2 (22MB, no GPU required)
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from loom_context.selector.ranker import ContextRanker, RankedFile, RankingResult

logger = logging.getLogger("loom")

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingRanker(ContextRanker):
    """Ranks files by semantic similarity using sentence-transformers embeddings.

    Uses all-MiniLM-L6-v2 (22MB) — runs on CPU, no GPU needed.
    Caches embeddings in .loom/cache/embeddings/ for speed.
    """

    name = "embedding"

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._model = None
        self._cache_dir = cache_dir

    def _get_model(self) -> Any:
        """Lazy-load the sentence-transformers model."""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(_MODEL_NAME)
            logger.debug("loaded embedding model: %s", _MODEL_NAME)
            return self._model
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for EmbeddingRanker. "
                "Install with: pip install loom-context[ai]"
            )

    def rank(
        self,
        candidates: list[str],
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 15,
    ) -> RankingResult:
        """Rank candidates by semantic similarity to query."""
        if not candidates or not query.strip():
            return RankingResult(
                files=[], strategy=self.name,
                total_candidates=len(candidates), total_selected=0,
            )

        model = self._get_model()

        # Encode query
        query_embedding = model.encode([query], normalize_embeddings=True)[0]

        # Encode candidates (use path as text — file paths carry semantic meaning)
        candidate_texts = [self._path_to_text(p) for p in candidates]
        candidate_embeddings = model.encode(candidate_texts, normalize_embeddings=True)

        # Compute cosine similarities (normalized embeddings → dot product = cosine)
        scores: list[tuple[str, float]] = []
        for i, path in enumerate(candidates):
            similarity = float(query_embedding @ candidate_embeddings[i])
            scores.append((path, similarity))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Take top_k
        ranked: list[RankedFile] = []
        for path, score in scores[:top_k]:
            ranked.append(RankedFile(
                path=path,
                score=round(max(score, 0.0), 3),
                evidence=[f"embedding-similarity:{score:.3f}"],
            ))

        return RankingResult(
            files=ranked,
            strategy=self.name,
            total_candidates=len(candidates),
            total_selected=len(ranked),
        )

    def _path_to_text(self, path: str) -> str:
        """Convert file path to searchable text."""
        return path.replace("/", " ").replace("_", " ").replace("-", " ").replace(".", " ")

    def _cache_key(self, text: str) -> str:
        """Generate cache key for a text."""
        return hashlib.md5(text.encode()).hexdigest()  # noqa: S324
