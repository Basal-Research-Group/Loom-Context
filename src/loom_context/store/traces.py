"""Resolution trace store: records task resolution outcomes in .loom/traces.jsonl."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context.git import GitHelper


@dataclass
class ResolutionTrace:
    """A record of how a task was resolved — who, what, why, outcome."""

    task_id: str
    timestamp: str
    query: str
    domain: str
    agent: str = "generic"  # claude | codex | cursor | copilot | generic
    selected_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    outcome: str = "pending"  # success | partial | failed | pending
    duration_ms: int = 0
    tokens_used: int = 0
    confidence: float = 0.0
    selection_strategy: str = "heuristic"
    why_selected: list[str] = field(default_factory=list)
    fallback_used: bool = False
    validation_result: str = "pending"  # pass | warn | fail | pending
    git_sha: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)


class TraceStore:
    """Append-only trace store in .loom/traces.jsonl."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.path = loom_dir / "traces.jsonl"
        self.loom_dir = loom_dir
        self._git = GitHelper(root)

    def record(
        self,
        query: str,
        domain: str = "unknown",
        agent: str = "generic",
        selected_files: Optional[list[str]] = None,
        changed_files: Optional[list[str]] = None,
        outcome: str = "pending",
        duration_ms: int = 0,
        tokens_used: int = 0,
        confidence: float = 0.0,
        selection_strategy: str = "heuristic",
        why_selected: Optional[list[str]] = None,
        fallback_used: bool = False,
        validation_result: str = "pending",
        notes: str = "",
    ) -> ResolutionTrace:
        """Record a resolution trace."""
        trace = ResolutionTrace(
            task_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query,
            domain=domain,
            agent=agent,
            selected_files=selected_files or [],
            changed_files=changed_files or [],
            outcome=outcome,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            confidence=confidence,
            selection_strategy=selection_strategy,
            why_selected=why_selected or [],
            fallback_used=fallback_used,
            validation_result=validation_result,
            git_sha=self._git.sha(),
            notes=notes,
        )
        self.loom_dir.mkdir(exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        return trace

    def read(self, count: int = 20) -> list[ResolutionTrace]:
        """Read recent traces, newest first."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").strip().split("\n")
        traces: list[ResolutionTrace] = []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                traces.append(ResolutionTrace(**data))
            except (json.JSONDecodeError, TypeError):
                continue
            if len(traces) >= count:
                break
        return traces

    def stats(self) -> dict[str, Any]:
        """Get summary stats from all traces."""
        traces = self.read(count=1000)
        if not traces:
            return {"total": 0}

        outcomes = {"success": 0, "partial": 0, "failed": 0, "pending": 0}
        agents: dict[str, int] = {}
        strategies: dict[str, int] = {}
        total_tokens = 0
        total_duration = 0

        for t in traces:
            outcomes[t.outcome] = outcomes.get(t.outcome, 0) + 1
            agents[t.agent] = agents.get(t.agent, 0) + 1
            strategies[t.selection_strategy] = strategies.get(t.selection_strategy, 0) + 1
            total_tokens += t.tokens_used
            total_duration += t.duration_ms

        return {
            "total": len(traces),
            "outcomes": outcomes,
            "agents": agents,
            "strategies": strategies,
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration,
            "avg_confidence": round(
                sum(t.confidence for t in traces) / len(traces), 3
            ) if traces else 0,
        }
