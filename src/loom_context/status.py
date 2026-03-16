"""Status collector: quick project health dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loom_context.security.filter import FileFilter
from loom_context.session import SessionEntry, SessionLogger


@dataclass
class ProjectStatus:
    """Snapshot of project health."""

    context_exists: bool
    project_name: str = ""
    project_type: str = ""
    architecture: list[str] = field(default_factory=list)
    last_scan: Optional[str] = None
    is_stale: bool = False
    stale_file_count: int = 0
    audit_errors: int = 0
    audit_warnings: int = 0
    recent_logs: list[SessionEntry] = field(default_factory=list)
    quick_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        from dataclasses import asdict
        return asdict(self)


class StatusCollector:
    """Collects project status from .context/ files without re-scanning."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / ".context"

    def collect(self) -> ProjectStatus:
        """Collect project status."""
        if not self.context_dir.exists():
            return ProjectStatus(context_exists=False)

        index = self._read_index()
        status = ProjectStatus(
            context_exists=True,
            project_name=index.get("project", {}).get("name", ""),
            project_type=index.get("project", {}).get("type", "unknown"),
            architecture=index.get("project", {}).get("architecture", []),
            last_scan=index.get("generated_at"),
            quick_rules=index.get("quick_rules", []),
        )

        # Check staleness
        status.is_stale, status.stale_file_count = self._check_staleness(
            status.last_scan
        )

        # Audit violations count
        status.audit_errors, status.audit_warnings = self._count_violations()

        # Recent session logs
        logger = SessionLogger(self.context_dir, self.root)
        status.recent_logs = logger.read(count=5)

        return status

    def _read_index(self) -> dict[str, Any]:
        index_path = self.context_dir / "index.json"
        if not index_path.exists():
            return {}
        try:
            with open(index_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _check_staleness(
        self, last_scan: Optional[str]
    ) -> tuple[bool, int]:
        """Check if project files are newer than last scan."""
        if not last_scan:
            return True, 0

        try:
            scan_dt = datetime.fromisoformat(last_scan)
        except ValueError:
            return True, 0

        scan_ts = scan_dt.timestamp()

        # Find src root
        file_filter = FileFilter(self.root)
        stale_count = 0
        checked = 0
        for filepath in file_filter.walk():
            # Only check source-like files for performance
            if filepath.suffix in {
                ".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go",
                ".java", ".kt", ".cs", ".rb", ".php", ".swift",
            }:
                try:
                    if filepath.stat().st_mtime > scan_ts:
                        stale_count += 1
                except OSError:
                    continue
                checked += 1
                if checked > 500:  # Cap for performance
                    break

        return stale_count > 0, stale_count

    def _count_violations(self) -> tuple[int, int]:
        """Count audit violations without full output."""
        try:
            from loom_context.auditors.naming import NamingAuditor
            from loom_context.auditors.structure import StructureAuditor

            file_filter = FileFilter(self.root)

            naming = NamingAuditor(self.root, file_filter)
            naming.load_rules()
            naming_v = naming.audit()

            structure = StructureAuditor(self.root, file_filter)
            structure.load_rules()
            structure_v = structure.audit()

            all_v = naming_v + structure_v
            errors = sum(1 for v in all_v if v.severity == "error")
            warnings = sum(1 for v in all_v if v.severity == "warning")
            return errors, warnings
        except Exception:
            return 0, 0
