"""Hybrid ranker: combines heuristic scores with AI-boosted ranking."""

from __future__ import annotations

import logging
from typing import Any, Optional

from loom_context.selector.ranker import ContextRanker, RankedFile, RankingResult

logger = logging.getLogger("loom")


class HybridRanker(ContextRanker):
    """Combines heuristic ranking with an AI ranker for boosted relevance.

    Strategy: run heuristic first, then use AI ranker to re-score top candidates.
    If AI ranker is unavailable, falls back to pure heuristic.
    """

    name = "hybrid"

    def __init__(self, ai_ranker: Optional[ContextRanker] = None) -> None:
        self._ai_ranker = ai_ranker

    def rank(
        self,
        candidates: list[str],
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 15,
    ) -> RankingResult:
        """Rank using heuristic + AI boost."""
        from loom_context.selector.ranker import HeuristicRanker

        # Step 1: heuristic pre-filter (get 2x candidates)
        heuristic = HeuristicRanker()
        pre_filtered = heuristic.rank(candidates, query, context, top_k=top_k * 2)

        if not self._ai_ranker or not pre_filtered.files:
            return RankingResult(
                files=pre_filtered.files[:top_k],
                strategy="hybrid-heuristic-only",
                total_candidates=len(candidates),
                total_selected=min(len(pre_filtered.files), top_k),
            )

        # Step 2: AI re-rank the pre-filtered candidates
        pre_paths = pre_filtered.paths
        try:
            ai_result = self._ai_ranker.rank(pre_paths, query, context, top_k=top_k)

            # Merge scores: 0.4 * heuristic + 0.6 * AI
            heuristic_scores = {f.path: f.score for f in pre_filtered.files}
            merged: list[RankedFile] = []
            for f in ai_result.files:
                h_score = heuristic_scores.get(f.path, 0.0)
                combined = round(0.4 * h_score + 0.6 * f.score, 3)
                evidence = list(f.evidence) + [f"heuristic:{h_score:.3f}"]
                merged.append(RankedFile(path=f.path, score=combined, evidence=evidence))

            merged.sort(key=lambda x: x.score, reverse=True)

            return RankingResult(
                files=merged[:top_k],
                strategy=f"hybrid-{self._ai_ranker.name}",
                total_candidates=len(candidates),
                total_selected=min(len(merged), top_k),
            )
        except Exception as e:
            logger.warning("AI ranker failed in hybrid mode: %s — using heuristic only", e)
            return RankingResult(
                files=pre_filtered.files[:top_k],
                strategy="hybrid-fallback-heuristic",
                total_candidates=len(candidates),
                total_selected=min(len(pre_filtered.files), top_k),
            )
