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
    project_type: Optional[str] = None
    overrides: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.context_dir = self.root / ".context"
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
