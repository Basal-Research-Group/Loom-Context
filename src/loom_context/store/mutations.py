"""Mutation log: tracks changes to .context/ files in .loom/mutations.jsonl."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loom_context.git import GitHelper


@dataclass
class Mutation:
    """A record of a context change."""

    timestamp: str
    action: str  # "init" | "scan" | "enrich" | "audit"
    files_changed: list[str] = field(default_factory=list)
    summary: str = ""
    git_sha: Optional[str] = None


class MutationLog:
    """Append-only mutation log stored as JSONL in .loom/mutations.jsonl."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.path = loom_dir / "mutations.jsonl"
        self.loom_dir = loom_dir
        self._git = GitHelper(root)

    def record(self, action: str, files_changed: list[str], summary: str) -> Mutation:
        """Record a context mutation."""
        mutation = Mutation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            files_changed=files_changed,
            summary=summary,
            git_sha=self._git.sha(),
        )
        self.loom_dir.mkdir(exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(mutation), ensure_ascii=False) + "\n")
        return mutation

    def read(self, count: int = 10) -> list[Mutation]:
        """Read recent mutations, newest first."""
        if not self.path.exists():
            return []

        entries: list[Mutation] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(Mutation(**data))
            except (json.JSONDecodeError, TypeError):
                continue

        entries.reverse()
        return entries[:count]
