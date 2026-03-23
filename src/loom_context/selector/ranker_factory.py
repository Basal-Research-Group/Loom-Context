"""Ranker factory: resolves --ai flag to concrete ContextRanker."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from loom_context.selector.ranker import ContextRanker, HeuristicRanker

logger = logging.getLogger("loom")


def get_ranker(
    strategy: str = "off",
    cache_dir: Optional[Path] = None,
    ollama_model: str = "llama3.2",
) -> ContextRanker:
    """Get a ranker by strategy name.

    Args:
        strategy: "off" | "local" | "ollama" | "hybrid"
        cache_dir: path for embedding cache (usually .loom/cache/)
        ollama_model: model name for Ollama

    Returns:
        Configured ContextRanker instance
    """
    if strategy == "off":
        return HeuristicRanker()

    if strategy == "local":
        try:
            from loom_context.selector.embedding_ranker import EmbeddingRanker

            return EmbeddingRanker(cache_dir=cache_dir)
        except ImportError:
            logger.warning("sentence-transformers not installed — falling back to heuristic")
            return HeuristicRanker()

    if strategy == "ollama":
        from loom_context.selector.ollama_ranker import OllamaRanker

        return OllamaRanker(model=ollama_model)

    if strategy == "hybrid":
        # Try embedding first, then ollama, then heuristic-only
        ai_ranker: Optional[ContextRanker] = None
        try:
            from loom_context.selector.embedding_ranker import EmbeddingRanker

            ai_ranker = EmbeddingRanker(cache_dir=cache_dir)
        except ImportError:
            try:
                from loom_context.selector.ollama_ranker import OllamaRanker

                ai_ranker = OllamaRanker(model=ollama_model)
            except Exception:
                pass

        from loom_context.selector.hybrid_ranker import HybridRanker

        return HybridRanker(ai_ranker=ai_ranker)

    logger.warning("unknown ranker strategy '%s' — using heuristic", strategy)
    return HeuristicRanker()
