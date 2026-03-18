"""Git utilities: shared helpers for extracting git metadata."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


class GitHelper:
    """Lightweight wrapper for read-only git commands."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def cmd(self, args: list[str]) -> Optional[str]:
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

    def branch(self) -> Optional[str]:
        """Get current branch name."""
        return self.cmd(["rev-parse", "--abbrev-ref", "HEAD"])

    def sha(self) -> Optional[str]:
        """Get current short commit SHA."""
        return self.cmd(["rev-parse", "--short", "HEAD"])

    def modified_files(self) -> list[str]:
        """Get list of files modified in working tree + staged."""
        output = self.cmd(["diff", "--name-only", "HEAD"])
        if not output:
            output = self.cmd(["diff", "--name-only", "--cached"])
        if output:
            return [f for f in output.splitlines() if f.strip()]
        return []
