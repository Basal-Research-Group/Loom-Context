"""Backup store: manages .loom/backups/ for safe file overwrites."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class BackupStore:
    """Manages backups of agent files before overwriting."""

    def __init__(self, loom_dir: Path) -> None:
        self.backups_dir = loom_dir / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, file_path: Path) -> Optional[Path]:
        """Copy file to .loom/backups/{name}.{timestamp}.bak.

        Returns the backup path, or None if the source file doesn't exist.
        """
        if not file_path.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.bak"
        backup_path = self.backups_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def list_backups(self, filename: Optional[str] = None) -> list[dict[str, str]]:
        """List backups, optionally filtered by original filename.

        Returns list of dicts with 'name', 'path', and 'original' keys.
        """
        if not self.backups_dir.exists():
            return []

        entries: list[dict[str, str]] = []
        for path in sorted(self.backups_dir.glob("*.bak"), reverse=True):
            # Format: CLAUDE.md.2026-03-18T143022.bak
            parts = path.name.rsplit(".", 3)  # [name, ext, timestamp, 'bak']
            if len(parts) >= 3:
                original = f"{parts[0]}.{parts[1]}" if len(parts) == 4 else parts[0]
            else:
                original = path.stem

            if filename is None or original == filename:
                entries.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "original": original,
                    }
                )

        return entries

    def restore(self, backup_path: Path, target: Path) -> Path:
        """Restore a backup file to the target location."""
        shutil.copy2(backup_path, target)
        return target
