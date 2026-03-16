"""Session logger: persistent memory between development sessions (hippocampus)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class SessionEntry:
    """A single session log entry."""

    timestamp: str
    message: str
    branch: Optional[str] = None
    sha: Optional[str] = None
    modified_files: list[str] = field(default_factory=list)


class SessionLogger:
    """Append-only session log stored as JSONL in .context/sessions.jsonl."""

    def __init__(self, context_dir: Path, root: Path) -> None:
        self.log_path = context_dir / "sessions.jsonl"
        self.root = root
        self.context_dir = context_dir

    def append(self, message: str) -> SessionEntry:
        """Append a new session entry with git metadata."""
        entry = SessionEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=message,
            branch=self._git_branch(),
            sha=self._git_sha(),
            modified_files=self._git_modified_files(),
        )
        self.context_dir.mkdir(exist_ok=True)
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

    def _git_cmd(self, args: list[str]) -> Optional[str]:
        """Run a git command and return stdout, or None on failure."""
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.root),
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def _git_branch(self) -> Optional[str]:
        return self._git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])

    def _git_sha(self) -> Optional[str]:
        return self._git_cmd(["rev-parse", "--short", "HEAD"])

    def _git_modified_files(self) -> list[str]:
        """Get list of files modified in working tree + staged."""
        output = self._git_cmd(["diff", "--name-only", "HEAD"])
        if not output:
            # Try staged files if no HEAD diff
            output = self._git_cmd(["diff", "--name-only", "--cached"])
        if output:
            return [f for f in output.splitlines() if f.strip()]
        return []
