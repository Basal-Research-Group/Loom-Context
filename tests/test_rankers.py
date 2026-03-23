"""Tests for AI rankers (embedding, ollama, hybrid) and ranker factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Ranker Factory
# ---------------------------------------------------------------------------


class TestRankerFactory:
    """Tests for ranker resolution by strategy."""

    def test_off_returns_heuristic(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker
        from loom_context.selector.ranker_factory import get_ranker

        ranker = get_ranker("off")
        assert isinstance(ranker, HeuristicRanker)

    def test_unknown_returns_heuristic(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker
        from loom_context.selector.ranker_factory import get_ranker

        ranker = get_ranker("nonsense")
        assert isinstance(ranker, HeuristicRanker)

    def test_local_strategy_returns_ranker(self) -> None:
        """Local strategy returns EmbeddingRanker if deps available, else HeuristicRanker."""
        from loom_context.selector.ranker import ContextRanker
        from loom_context.selector.ranker_factory import get_ranker

        ranker = get_ranker("local")
        assert isinstance(ranker, ContextRanker)
        assert ranker.name in ("embedding", "heuristic")

    def test_ollama_returns_ollama_ranker(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker
        from loom_context.selector.ranker_factory import get_ranker

        ranker = get_ranker("ollama")
        assert isinstance(ranker, OllamaRanker)

    def test_hybrid_returns_hybrid_ranker(self) -> None:
        from loom_context.selector.hybrid_ranker import HybridRanker
        from loom_context.selector.ranker_factory import get_ranker

        ranker = get_ranker("hybrid")
        assert isinstance(ranker, HybridRanker)


# ---------------------------------------------------------------------------
# OllamaRanker
# ---------------------------------------------------------------------------


class TestOllamaRanker:
    """Tests for Ollama-based ranking."""

    def test_empty_candidates(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        result = ranker.rank([], "test query")
        assert result.files == []
        assert result.total_candidates == 0

    def test_empty_query(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        result = ranker.rank(["a.py"], "")
        assert result.files == []

    def test_fallback_when_unavailable(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        # Ollama likely not running in CI
        result = ranker.rank(
            ["src/auth.py", "src/utils.py"],
            "fix auth bug",
            top_k=5,
        )
        # Should return results (either from Ollama or fallback)
        assert result.total_candidates == 2
        assert result.strategy in ("ollama", "ollama-fallback-heuristic")

    def test_parse_response_valid_json(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        candidates = ["a.py", "b.py", "c.py"]
        response = '["b.py", "a.py", "c.py"]'
        result = ranker._parse_response(response, candidates)
        assert result[0] == "b.py"
        assert result[1] == "a.py"

    def test_parse_response_invalid_json(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        candidates = ["a.py", "b.py"]
        result = ranker._parse_response("not json", candidates)
        assert result == candidates  # fallback to original order

    def test_parse_response_filters_invalid_paths(self) -> None:
        from loom_context.selector.ollama_ranker import OllamaRanker

        ranker = OllamaRanker()
        candidates = ["a.py", "b.py"]
        response = '["b.py", "nonexistent.py", "a.py"]'
        result = ranker._parse_response(response, candidates)
        assert "nonexistent.py" not in result
        assert set(result) == {"a.py", "b.py"}


# ---------------------------------------------------------------------------
# EmbeddingRanker (mocked — no real model in tests)
# ---------------------------------------------------------------------------


class TestEmbeddingRanker:
    """Tests for sentence-transformers embedding ranker."""

    def test_import_error_message(self) -> None:
        from loom_context.selector.embedding_ranker import EmbeddingRanker

        ranker = EmbeddingRanker()
        ranker._model = None

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with pytest.raises(ImportError, match="sentence-transformers"):
                ranker._get_model()

    def test_empty_candidates(self) -> None:
        from loom_context.selector.embedding_ranker import EmbeddingRanker

        ranker = EmbeddingRanker()
        result = ranker.rank([], "test")
        assert result.files == []

    def test_empty_query(self) -> None:
        from loom_context.selector.embedding_ranker import EmbeddingRanker

        ranker = EmbeddingRanker()
        result = ranker.rank(["a.py"], "")
        assert result.files == []

    def test_path_to_text(self) -> None:
        from loom_context.selector.embedding_ranker import EmbeddingRanker

        ranker = EmbeddingRanker()
        assert "auth" in ranker._path_to_text("src/auth/login.py")
        assert "login" in ranker._path_to_text("src/auth/login.py")

    def test_rank_with_mock_model(self) -> None:
        """Test ranking with a mocked embedding model."""
        pytest.importorskip("numpy")
        import numpy as np

        from loom_context.selector.embedding_ranker import EmbeddingRanker

        mock_model = MagicMock()
        mock_model.encode.side_effect = [
            np.array([[0.5, 0.5, 0.0]]),  # query
            np.array([
                [0.4, 0.6, 0.0],  # auth.py — similar
                [0.0, 0.0, 1.0],  # utils.py — different
                [0.5, 0.5, 0.0],  # login.py — identical
            ]),
        ]

        ranker = EmbeddingRanker()
        ranker._model = mock_model

        result = ranker.rank(
            ["src/auth.py", "src/utils.py", "src/login.py"],
            "fix auth",
            top_k=3,
        )
        assert result.strategy == "embedding"
        assert result.total_candidates == 3
        assert result.files[0].path == "src/login.py"


# ---------------------------------------------------------------------------
# HybridRanker
# ---------------------------------------------------------------------------


class TestHybridRanker:
    """Tests for hybrid heuristic + AI ranking."""

    def test_without_ai_ranker_uses_heuristic(self) -> None:
        from loom_context.selector.hybrid_ranker import HybridRanker

        ranker = HybridRanker(ai_ranker=None)
        result = ranker.rank(["a.py", "b.py"], "test", top_k=5)
        assert "heuristic" in result.strategy

    def test_with_mock_ai_ranker(self) -> None:
        from loom_context.selector.hybrid_ranker import HybridRanker
        from loom_context.selector.ranker import HeuristicRanker

        mock_ai = HeuristicRanker()  # Use heuristic as "AI" for testing
        ranker = HybridRanker(ai_ranker=mock_ai)
        result = ranker.rank(
            ["src/auth/login.py", "src/utils.py"],
            "auth login",
            top_k=5,
        )
        assert "hybrid" in result.strategy
        assert result.total_candidates == 2

    def test_ai_failure_falls_back(self) -> None:
        from loom_context.selector.hybrid_ranker import HybridRanker
        from loom_context.selector.ranker import ContextRanker, RankingResult

        class FailingRanker(ContextRanker):
            name = "failing"

            def rank(self, candidates, query, context=None, top_k=15):
                raise RuntimeError("AI failed")

        ranker = HybridRanker(ai_ranker=FailingRanker())
        result = ranker.rank(["a.py", "b.py"], "test")
        assert "fallback" in result.strategy
