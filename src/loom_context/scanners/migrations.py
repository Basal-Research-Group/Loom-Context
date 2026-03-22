"""Migration scanner: parse SQL migration files and extract structure."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class MigrationInfo:
    """A single parsed migration."""

    name: str
    timestamp: str
    sql_lines: int = 0
    tables_created: list[str] = field(default_factory=list)
    indices_created: list[str] = field(default_factory=list)
    functions_created: list[str] = field(default_factory=list)
    triggers_created: list[str] = field(default_factory=list)
    policies_created: list[str] = field(default_factory=list)
    tables_altered: list[str] = field(default_factory=list)
    rls_enabled: list[str] = field(default_factory=list)


@dataclass
class MigrationScanResult:
    """Complete migration scan output."""

    migrations: list[MigrationInfo] = field(default_factory=list)
    total_sql_lines: int = 0
    total_tables: int = 0
    total_functions: int = 0
    total_triggers: int = 0
    total_policies: int = 0
    total_indices: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MigrationScanner:
    """Scans Prisma migration SQL files and extracts database object inventory."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def scan(self, migrations_path: Optional[str] = None) -> MigrationScanResult:
        """Parse all migration SQL files and return structured results."""
        path = self._resolve_migrations_path(migrations_path)
        if not path or not path.exists():
            return MigrationScanResult()

        migrations: list[MigrationInfo] = []
        all_tables: set[str] = set()
        all_functions: set[str] = set()
        all_triggers: set[str] = set()
        all_policies: set[str] = set()
        all_indices: set[str] = set()
        total_lines = 0

        for migration_dir in sorted(path.iterdir()):
            if not migration_dir.is_dir():
                continue
            sql_file = migration_dir / "migration.sql"
            if not sql_file.exists():
                continue

            content = sql_file.read_text(encoding="utf-8")
            lines = len(content.splitlines())
            total_lines += lines

            # Extract timestamp and name from folder: YYYYMMDDHHMMSS_name
            folder = migration_dir.name
            parts = folder.split("_", 1)
            timestamp = parts[0] if parts else folder
            name = parts[1] if len(parts) > 1 else folder

            info = self._parse_migration(content, name, timestamp, lines)
            migrations.append(info)

            all_tables.update(info.tables_created)
            all_functions.update(info.functions_created)
            all_triggers.update(info.triggers_created)
            all_policies.update(info.policies_created)
            all_indices.update(info.indices_created)

        return MigrationScanResult(
            migrations=migrations,
            total_sql_lines=total_lines,
            total_tables=len(all_tables),
            total_functions=len(all_functions),
            total_triggers=len(all_triggers),
            total_policies=len(all_policies),
            total_indices=len(all_indices),
        )

    def _resolve_migrations_path(self, explicit: Optional[str] = None) -> Optional[Path]:
        """Find the migrations directory."""
        if explicit:
            p = Path(explicit)
            return p if p.is_absolute() else self.root / p

        loom_json = self.root / ".context" / "loom.json"
        if loom_json.exists():
            try:
                data = json.loads(loom_json.read_text(encoding="utf-8"))
                mp = data.get("database", {}).get("migrations_path")
                if mp:
                    return self.root / mp
            except (json.JSONDecodeError, OSError):
                pass

        for candidate in [
            "prisma/migrations",
            "packages/core/database/prisma/migrations",
        ]:
            p = self.root / candidate
            if p.exists():
                return p

        return None

    def _parse_migration(
        self, content: str, name: str, timestamp: str, lines: int
    ) -> MigrationInfo:
        """Parse a single migration SQL file."""
        info = MigrationInfo(name=name, timestamp=timestamp, sql_lines=lines)
        _if_not = r"(?:IF NOT EXISTS\s+)?"
        _name = r'"?(\w+)"?'

        for m in re.finditer(
            rf"CREATE TABLE\s+{_if_not}{_name}", content, re.IGNORECASE
        ):
            info.tables_created.append(m.group(1))

        for m in re.finditer(
            rf"CREATE INDEX\s+{_if_not}{_name}", content, re.IGNORECASE
        ):
            info.indices_created.append(m.group(1))

        for m in re.finditer(
            rf"CREATE UNIQUE INDEX\s+{_if_not}{_name}", content, re.IGNORECASE
        ):
            info.indices_created.append(m.group(1))

        _or_replace = r"(?:OR REPLACE\s+)?"
        for m in re.finditer(
            rf"CREATE\s+{_or_replace}FUNCTION\s+{_name}", content, re.IGNORECASE
        ):
            info.functions_created.append(m.group(1))

        for m in re.finditer(
            rf"CREATE\s+TRIGGER\s+{_name}", content, re.IGNORECASE
        ):
            info.triggers_created.append(m.group(1))

        for m in re.finditer(
            rf"CREATE\s+POLICY\s+{_name}", content, re.IGNORECASE
        ):
            info.policies_created.append(m.group(1))

        for m in re.finditer(
            rf"ALTER TABLE\s+{_name}", content, re.IGNORECASE
        ):
            table = m.group(1)
            if table not in info.tables_altered:
                info.tables_altered.append(table)

        _rls = r"ENABLE ROW LEVEL SECURITY"
        for m in re.finditer(
            rf"ALTER TABLE\s+{_name}\s+{_rls}", content, re.IGNORECASE
        ):
            info.rls_enabled.append(m.group(1))

        return info
