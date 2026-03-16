"""Findings store: persists audit results in .loom/inconsistencies.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context.git import GitHelper
from loom_context.models import Violation


@dataclass
class AuditFindings:
    """Snapshot of audit results."""

    timestamp: str
    git_sha: Optional[str]
    errors: int
    warnings: int
    violations: list[dict[str, Any]] = field(default_factory=list)


class FindingsStore:
    """Persists audit findings in .loom/inconsistencies.json."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.path = loom_dir / "inconsistencies.json"
        self.loom_dir = loom_dir
        self._git = GitHelper(root)

    def save(self, violations: list[Violation]) -> AuditFindings:
        """Save audit violations to disk."""
        errors = sum(1 for v in violations if v.severity == "error")
        warnings = sum(1 for v in violations if v.severity == "warning")

        findings = AuditFindings(
            timestamp=datetime.now(timezone.utc).isoformat(),
            git_sha=self._git.sha(),
            errors=errors,
            warnings=warnings,
            violations=[asdict(v) for v in violations],
        )

        self.loom_dir.mkdir(exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(findings), f, indent=2, ensure_ascii=False)

        return findings

    def load(self) -> Optional[AuditFindings]:
        """Load findings from disk."""
        if not self.path.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            return AuditFindings(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            return None

    def has_findings(self) -> bool:
        """Check if findings file exists and has violations."""
        findings = self.load()
        if findings is None:
            return False
        return len(findings.violations) > 0
