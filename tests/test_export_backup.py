"""Tests for export command backup behavior."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from loom_context.cli import main


class TestExportBackup:
    def test_export_install_backs_up_existing(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        # Create existing CLAUDE.md
        claude = tmp_project / "CLAUDE.md"
        claude.write_text("# My hand-crafted rules")

        # Install with force (skip prompt) but allow backup
        result = runner.invoke(
            main, ["export", str(tmp_project), "--agent", "claude", "--install", "--force"]
        )
        assert result.exit_code == 0
        assert "backup" in result.output
        backups = list((tmp_project / ".loom" / "backups").glob("CLAUDE.md.*.bak"))
        assert len(backups) == 1
        assert backups[0].read_text() == "# My hand-crafted rules"

    def test_export_install_force_no_prompt(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        (tmp_project / "CLAUDE.md").write_text("old")

        result = runner.invoke(
            main, ["export", str(tmp_project), "--agent", "claude", "--install", "--force"]
        )
        assert result.exit_code == 0
        assert "Installed" in result.output

    def test_export_install_no_backup_skips(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        (tmp_project / "CLAUDE.md").write_text("old")

        args = [
            "export",
            str(tmp_project),
            "--agent",
            "claude",
            "--install",
            "--force",
            "--no-backup",
        ]
        result = runner.invoke(main, args)
        assert result.exit_code == 0
        assert "backup" not in result.output.lower()
        backups_dir = tmp_project / ".loom" / "backups"
        if backups_dir.exists():
            assert len(list(backups_dir.glob("CLAUDE.md.*.bak"))) == 0

    def test_export_install_prompts_when_exists(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        (tmp_project / "CLAUDE.md").write_text("old")

        # Simulate saying "no" to overwrite prompt
        result = runner.invoke(
            main,
            ["export", str(tmp_project), "--agent", "claude", "--install"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "Skipped" in result.output
        # Original preserved
        assert (tmp_project / "CLAUDE.md").read_text() == "old"

    def test_export_install_no_existing_no_prompt(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        # No existing CLAUDE.md
        assert not (tmp_project / "CLAUDE.md").exists()

        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "claude", "--install"])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (tmp_project / "CLAUDE.md").exists()
