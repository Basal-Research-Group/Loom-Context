"""Ollama ranker: ranks files using a local LLM via Ollama API.

Requires: Ollama running locally (localhost:11434)
No Python deps — uses stdlib urllib.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from loom_context.selector.ranker import ContextRanker, RankedFile, RankingResult

logger = logging.getLogger("loom")

_OLLAMA_URL = "http://localhost:11434/api/generate"
_DEFAULT_MODEL = "llama3.2"


class OllamaRanker(ContextRanker):
    """Ranks files by asking a local LLM (via Ollama) to score relevance.

    Uses Ollama's /api/generate endpoint. No Python deps beyond stdlib.
    Falls back gracefully if Ollama is not running.
    """

    name = "ollama"

    def __init__(self, model: str = _DEFAULT_MODEL, timeout: int = 30) -> None:
        self._model = model
        self._timeout = timeout

    def rank(
        self,
        candidates: list[str],
        query: str,
        context: dict[str, Any] | None = None,
        top_k: int = 15,
    ) -> RankingResult:
        """Rank candidates by asking Ollama to score relevance."""
        if not candidates or not query.strip():
            return RankingResult(
                files=[], strategy=self.name,
                total_candidates=len(candidates), total_selected=0,
            )

        if not self._is_available():
            logger.warning("Ollama not available at %s — falling back", _OLLAMA_URL)
            return self._fallback_rank(candidates, query, top_k)

        # Build prompt for the LLM
        files_list = "\n".join(f"- {p}" for p in candidates[:50])  # Cap at 50 to fit context
        prompt = (
            f"Given this task: \"{query}\"\n\n"
            f"Rank these files by relevance (most relevant first). "
            f"Return ONLY a JSON array of file paths, no explanation:\n\n{files_list}"
        )

        try:
            response = self._call_ollama(prompt)
            ranked_paths = self._parse_response(response, candidates)

            ranked: list[RankedFile] = []
            for i, path in enumerate(ranked_paths[:top_k]):
                score = round(1.0 - (i / max(len(ranked_paths), 1)), 3)
                ranked.append(RankedFile(
                    path=path, score=score,
                    evidence=[f"ollama:{self._model}"],
                ))

            return RankingResult(
                files=ranked,
                strategy=self.name,
                total_candidates=len(candidates),
                total_selected=len(ranked),
            )
        except Exception as e:
            logger.warning("Ollama ranking failed: %s — falling back", e)
            return self._fallback_rank(candidates, query, top_k)

    def _is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            urllib.request.urlopen(req, timeout=3)  # noqa: S310
            return True
        except (urllib.error.URLError, OSError):
            return False

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama generate API and return response text."""
        payload = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 2000},
        }).encode()

        req = urllib.request.Request(
            _OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=self._timeout)  # noqa: S310
        data = json.loads(resp.read().decode())
        return data.get("response", "")

    def _parse_response(self, response: str, candidates: list[str]) -> list[str]:
        """Parse LLM response into ordered file paths."""
        # Try to extract JSON array from response
        try:
            # Find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                paths = json.loads(response[start:end])
                if isinstance(paths, list):
                    # Filter to only paths that exist in candidates
                    valid = [p for p in paths if p in candidates]
                    # Add any missing candidates at the end
                    remaining = [p for p in candidates if p not in valid]
                    return valid + remaining
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: return candidates in original order
        return candidates

    def _fallback_rank(self, candidates: list[str], query: str, top_k: int) -> RankingResult:
        """Fallback to heuristic when Ollama is unavailable."""
        from loom_context.selector.ranker import HeuristicRanker

        heuristic = HeuristicRanker()
        result = heuristic.rank(candidates, query, top_k=top_k)
        # Mark that we fell back
        return RankingResult(
            files=result.files,
            strategy="ollama-fallback-heuristic",
            total_candidates=result.total_candidates,
            total_selected=result.total_selected,
        )
