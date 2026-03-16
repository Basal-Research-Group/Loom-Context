"""Decision log: explicit architectural decision records in .loom/decisions.jsonl."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loom_context.git import GitHelper


@dataclass
class Decision:
    """An architectural decision record."""

    timestamp: str
    summary: str
    rationale: str
    scope: str  # "architecture" | "naming" | "deps" | "security"
    branch: Optional[str] = None
    sha: Optional[str] = None


class DecisionLog:
    """Append-only decision log stored as JSONL in .loom/decisions.jsonl."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.path = loom_dir / "decisions.jsonl"
        self.loom_dir = loom_dir
        self._git = GitHelper(root)

    def append(self, summary: str, rationale: str, scope: str) -> Decision:
        """Append a new decision with git metadata."""
        decision = Decision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            rationale=rationale,
            scope=scope,
            branch=self._git.branch(),
            sha=self._git.sha(),
        )
        self.loom_dir.mkdir(exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(decision), ensure_ascii=False) + "\n")
        return decision

    def read(self, count: int = 10) -> list[Decision]:
        """Read recent decisions, newest first."""
        if not self.path.exists():
            return []

        entries: list[Decision] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(Decision(**data))
            except (json.JSONDecodeError, TypeError):
                continue

        entries.reverse()
        return entries[:count]

    def clear(self) -> int:
        """Clear all decisions. Returns count of cleared entries."""
        if not self.path.exists():
            return 0
        content = self.path.read_text(encoding="utf-8")
        count = len([ln for ln in content.splitlines() if ln.strip()])
        self.path.write_text("", encoding="utf-8")
        return count
