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


@dataclass
class DeltaReport:
    """Difference between two audit snapshots."""

    timestamp: str
    git_sha: Optional[str]
    before: int
    after: int
    resolved: int
    new: int
    resolved_files: list[str] = field(default_factory=list)
    new_files: list[str] = field(default_factory=list)


class FindingsStore:
    """Persists audit findings in .loom/inconsistencies.json."""

    def __init__(self, loom_dir: Path, root: Path) -> None:
        self.path = loom_dir / "inconsistencies.json"
        self.loom_dir = loom_dir
        self.reports_dir = loom_dir / "reports"
        self._git = GitHelper(root)

    def save(self, violations: list[Violation]) -> AuditFindings:
        """Save audit violations to disk, computing delta if previous findings exist."""
        # Load previous findings before overwriting
        previous = self.load()

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

        # Compute and save delta if previous findings exist
        if previous is not None:
            self._save_delta(previous, findings)

        return findings

    def load(self) -> Optional[AuditFindings]:
        """Load findings from disk."""
        if not self.path.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
            return AuditFindings(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            return None

    def has_findings(self) -> bool:
        """Check if findings file exists and has violations."""
        findings = self.load()
        if findings is None:
            return False
        return len(findings.violations) > 0

    def _save_delta(self, previous: AuditFindings, current: AuditFindings) -> None:
        """Compute and save delta between two findings snapshots."""
        prev_keys = self._violation_keys(previous.violations)
        curr_keys = self._violation_keys(current.violations)

        resolved_keys = prev_keys - curr_keys
        new_keys = curr_keys - prev_keys

        # Extract file paths for resolved and new violations
        prev_by_key = self._index_by_key(previous.violations)
        curr_by_key = self._index_by_key(current.violations)

        resolved_files = sorted({prev_by_key[k].get("file", "") for k in resolved_keys})
        new_files = sorted({curr_by_key[k].get("file", "") for k in new_keys})

        delta = DeltaReport(
            timestamp=current.timestamp,
            git_sha=current.git_sha,
            before=len(previous.violations),
            after=len(current.violations),
            resolved=len(resolved_keys),
            new=len(new_keys),
            resolved_files=[f for f in resolved_files if f],
            new_files=[f for f in new_files if f],
        )

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self.reports_dir / f"delta-{date_str}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(delta), f, indent=2, ensure_ascii=False)

    def _violation_keys(self, violations: list[dict[str, Any]]) -> set[str]:
        """Create unique keys for violations to enable diffing."""
        keys: set[str] = set()
        for v in violations:
            key = f"{v.get('file', '')}:{v.get('rule', '')}:{v.get('message', '')}"
            keys.add(key)
        return keys

    def _index_by_key(self, violations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Index violations by their unique key."""
        index: dict[str, dict[str, Any]] = {}
        for v in violations:
            key = f"{v.get('file', '')}:{v.get('rule', '')}:{v.get('message', '')}"
            index[key] = v
        return index
