"""Loom configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class LoomConfig:
    """Configuration for a Loom-Context session."""

    root: Path
    context_dir: Path = field(init=False)
    loom_dir: Path = field(init=False)
    project_type: Optional[str] = None
    overrides: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.context_dir = self.root / ".context"
        self.loom_dir = self.root / ".loom"
        self._load_overrides()

    def _load_overrides(self) -> None:
        """Load user overrides from .context/loom.json if it exists."""
        loom_json = self.context_dir / "loom.json"
        if loom_json.exists():
            with open(loom_json, encoding="utf-8") as f:
                self.overrides = json.load(f)
            self.project_type = self.overrides.get("project_type", self.project_type)

    def ensure_context_dir(self) -> Path:
        """Create .context/ directory if it doesn't exist."""
        self.context_dir.mkdir(exist_ok=True)
        return self.context_dir

    def ensure_loom_dir(self) -> Path:
        """Create .loom/ directory and reports/ subdirectory if they don't exist."""
        self.loom_dir.mkdir(exist_ok=True)
        (self.loom_dir / "reports").mkdir(exist_ok=True)
        return self.loom_dir

    def ensure_gitignore(self) -> bool:
        """Add Loom entries to .gitignore if missing. Returns True if modified."""
        gitignore = self.root / ".gitignore"

        # Required entries: ignore .loom/* but track .loom/reports/, ignore .context/
        loom_entries = [
            ("# Loom-Context", None),
            (".loom/*", ".loom"),
            ("!.loom/reports/", None),
            (".context/", ".context"),
        ]

        content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""

        lines = content.splitlines()
        modified = False

        for entry, check_pattern in loom_entries:
            if check_pattern is not None:
                # Check if already covered by existing rules
                already_present = any(
                    line.strip() == entry or line.strip() == check_pattern for line in lines
                )
            else:
                already_present = any(line.strip() == entry for line in lines)

            if not already_present:
                if not modified and content and not content.endswith("\n"):
                    lines.append("")
                lines.append(entry)
                modified = True

        if modified:
            gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return modified
