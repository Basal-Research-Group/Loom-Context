"""Reporter: usage analytics in .loom/reports/usage.jsonl."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context.git import GitHelper


@dataclass
class UsageEntry:
    """A single command usage record."""

    timestamp: str
    command: str
    duration_ms: int
    success: bool
    git_sha: Optional[str] = None


class UsageReporter:
    """Records and reports command usage analytics."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.reports_dir = loom_dir / "reports"
        self.path = self.reports_dir / "usage.jsonl"
        self._git = GitHelper(root)

    def record(self, command: str, duration_ms: int, success: bool) -> UsageEntry:
        """Record a command execution."""
        entry = UsageEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            command=command,
            duration_ms=duration_ms,
            success=success,
            git_sha=self._git.sha(),
        )
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def read(self, count: int = 50) -> list[UsageEntry]:
        """Read recent usage entries, newest first."""
        if not self.path.exists():
            return []
        entries: list[UsageEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(UsageEntry(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
        entries.reverse()
        return entries[:count]

    def summary(self) -> dict[str, Any]:
        """Generate usage summary."""
        entries = self.read(count=1000)
        if not entries:
            return {}

        by_cmd: dict[str, list[int]] = {}
        for e in entries:
            by_cmd.setdefault(e.command, []).append(e.duration_ms)

        result: dict[str, Any] = {}
        for cmd, durations in sorted(by_cmd.items()):
            result[cmd] = {
                "runs": len(durations),
                "avg_ms": int(sum(durations) / len(durations)),
                "total_ms": sum(durations),
            }
        return result
