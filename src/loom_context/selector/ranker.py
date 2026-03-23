"""Context ranker: strategy pattern for ranking files in bundles."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RankedFile:
    """A file with relevance score and ranking evidence."""

    path: str
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RankingResult:
    """Result of ranking a set of candidate files."""

    files: list[RankedFile]
    strategy: str = "heuristic"
    total_candidates: int = 0
    total_selected: int = 0

    @property
    def paths(self) -> list[str]:
        """Just the file paths, ordered by score."""
        return [f.path for f in self.files]


class ContextRanker(ABC):
    """Interface for ranking files by relevance to a task.

    Strategy pattern: swap implementations without changing callers.
    - HeuristicRanker: keyword + path matching (default, no deps)
    - OllamaRanker: local LLM ranking (v0.9.0, optional)
    - EmbeddingRanker: sentence-transformers (v0.9.0, optional)
    - HybridRanker: heuristic + AI boost (v0.9.0, optional)
    """

    name: str = "base"

    @abstractmethod
    def rank(
        self,
        candidates: list[str],
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 15,
    ) -> RankingResult:
        """Rank candidates by relevance to query.

        Args:
            candidates: list of file paths to rank
            query: task description or search query
            context: optional scan_result or domain info
            top_k: max files to return

        Returns:
            RankingResult with ranked files and metadata
        """
        ...


class HeuristicRanker(ContextRanker):
    """Ranks files using keyword matching and path heuristics. No AI, no deps."""

    name = "heuristic"

    def rank(
        self,
        candidates: list[str],
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 15,
    ) -> RankingResult:
        """Rank by keyword overlap between query and file paths."""
        from loom_context.knowledge import get_registry

        registry = get_registry()
        stop_words = set(registry.get_stop_words())

        # Tokenize query
        query_tokens = {
            t.lower()
            for t in query.replace("/", " ").replace("_", " ").replace("-", " ").split()
            if t.lower() not in stop_words and len(t) > 2
        }

        if not query_tokens:
            # No useful tokens — return first top_k candidates
            ranked = [RankedFile(path=p, score=0.5, evidence=["no-query-tokens"]) for p in candidates[:top_k]]
            return RankingResult(
                files=ranked,
                strategy=self.name,
                total_candidates=len(candidates),
                total_selected=len(ranked),
            )

        scored: list[RankedFile] = []
        for path in candidates:
            path_tokens = {
                t.lower()
                for t in path.replace("/", " ").replace("_", " ").replace("-", " ").replace(".", " ").split()
                if len(t) > 2
            }
            overlap = query_tokens & path_tokens
            if overlap:
                score = len(overlap) / len(query_tokens)
                scored.append(RankedFile(
                    path=path,
                    score=round(min(score, 1.0), 3),
                    evidence=[f"matched:{','.join(sorted(overlap))}"],
                ))
            else:
                scored.append(RankedFile(path=path, score=0.0))

        # Sort by score descending, take top_k
        scored.sort(key=lambda f: f.score, reverse=True)
        selected = scored[:top_k]

        return RankingResult(
            files=selected,
            strategy=self.name,
            total_candidates=len(candidates),
            total_selected=len(selected),
        )
