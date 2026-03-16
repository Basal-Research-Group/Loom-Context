"""Session logger: persistent memory between development sessions (hippocampus)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loom_context.git import GitHelper


@dataclass
class SessionEntry:
    """A single session log entry."""

    timestamp: str
    message: str
    branch: Optional[str] = None
    sha: Optional[str] = None
    modified_files: list[str] = field(default_factory=list)


class SessionLogger:
    """Append-only session log stored as JSONL in .loom/sessions.jsonl."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.log_path = loom_dir / "sessions.jsonl"
        self.root = root
        self.loom_dir = loom_dir
        self._git = GitHelper(root)

    def append(self, message: str) -> SessionEntry:
        """Append a new session entry with git metadata."""
        entry = SessionEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=message,
            branch=self._git.branch(),
            sha=self._git.sha(),
            modified_files=self._git.modified_files(),
        )
        self.loom_dir.mkdir(exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def read(
        self,
        count: int = 5,
        branch: Optional[str] = None,
        since: Optional[str] = None,
    ) -> list[SessionEntry]:
        """Read recent session entries, newest first."""
        if not self.log_path.exists():
            return []

        entries: list[SessionEntry] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entries.append(SessionEntry(**data))
            except (json.JSONDecodeError, TypeError):
                continue

        # Apply filters
        if branch:
            entries = [e for e in entries if e.branch == branch]
        if since:
            entries = [e for e in entries if e.timestamp >= since]

        # Return newest first, limited by count
        entries.reverse()
        return entries[:count]

    def clear(self) -> int:
        """Clear all session entries. Returns count of cleared entries."""
        if not self.log_path.exists():
            return 0
        content = self.log_path.read_text(encoding="utf-8")
        count = len([ln for ln in content.splitlines() if ln.strip()])
        self.log_path.write_text("", encoding="utf-8")
        return count

    def migrate_from_context(self, context_dir: Path) -> bool:
        """Migrate sessions.jsonl from .context/ to .loom/ if it exists."""
        old_path = context_dir / "sessions.jsonl"
        if not old_path.exists():
            return False
        if self.log_path.exists():
            # Append old entries to new file
            old_content = old_path.read_text(encoding="utf-8").strip()
            if old_content:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(old_content + "\n")
        else:
            self.loom_dir.mkdir(exist_ok=True)
            old_path.rename(self.log_path)
            return True
        old_path.unlink()
        return True
