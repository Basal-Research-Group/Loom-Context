"""Tests for BackupStore."""

from __future__ import annotations

from pathlib import Path

from loom_context.store.backups import BackupStore


class TestBackupStore:
    def test_backup_creates_file(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        target = tmp_path / "CLAUDE.md"
        target.write_text("# My hand-crafted rules")

        backup = store.backup(target)
        assert backup is not None
        assert backup.exists()
        assert backup.read_text() == "# My hand-crafted rules"
        assert ".bak" in backup.name

    def test_backup_returns_none_for_nonexistent(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        result = store.backup(tmp_path / "does-not-exist.md")
        assert result is None

    def test_backup_filename_contains_timestamp(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        target = tmp_path / "CLAUDE.md"
        target.write_text("content")

        backup = store.backup(target)
        assert backup is not None
        # Format: CLAUDE.md.2026-03-18T143022.bak
        assert backup.name.startswith("CLAUDE.md.")
        assert backup.name.endswith(".bak")

    def test_list_backups(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        target = tmp_path / "CLAUDE.md"
        target.write_text("v1")
        store.backup(target)

        # Create a second backup for a different file to test listing
        target2 = tmp_path / "AGENTS.md"
        target2.write_text("agents")
        store.backup(target2)

        backups = store.list_backups()
        assert len(backups) == 2

    def test_list_backups_filters_by_name(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        (tmp_path / "CLAUDE.md").write_text("claude")
        store.backup(tmp_path / "CLAUDE.md")

        (tmp_path / "AGENTS.md").write_text("agents")
        store.backup(tmp_path / "AGENTS.md")

        claude_backups = store.list_backups("CLAUDE.md")
        assert len(claude_backups) == 1
        assert claude_backups[0]["original"] == "CLAUDE.md"

    def test_restore(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)

        target = tmp_path / "CLAUDE.md"
        target.write_text("original content")
        backup = store.backup(target)
        assert backup is not None

        target.write_text("overwritten")
        store.restore(backup, target)
        assert target.read_text() == "original content"

    def test_backups_dir_created_automatically(self, tmp_path: Path) -> None:
        loom_dir = tmp_path / ".loom"
        loom_dir.mkdir()
        store = BackupStore(loom_dir)
        assert store.backups_dir.exists()
