"""Tests for loom setup command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from loom_context.cli import main


class TestSetupCommand:
    def test_setup_preset_full_force(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--preset", "full", "--force"])
        assert result.exit_code == 0
        assert "Setup complete" in result.output
        assert (tmp_project / "CLAUDE.md").exists()
        assert (tmp_project / ".cursorrules").exists()

    def test_setup_preset_minimal(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--preset", "minimal", "--force"])
        assert result.exit_code == 0
        assert "No agents selected" in result.output
        assert not (tmp_project / "CLAUDE.md").exists()

    def test_setup_preset_claude(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--preset", "claude", "--force"])
        assert result.exit_code == 0
        assert (tmp_project / "CLAUDE.md").exists()
        assert not (tmp_project / ".cursorrules").exists()

    def test_setup_agent_flag(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--agent", "codex", "--force"])
        assert result.exit_code == 0
        assert "Installed codex" in result.output

    def test_setup_backs_up_existing_file(self, tmp_project: Path) -> None:
        # tmp_project already has AGENTS.md from conftest
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--agent", "codex", "--force"])
        assert result.exit_code == 0
        assert "backup" in result.output
        backups = list((tmp_project / ".loom" / "backups").glob("AGENTS.md.*.bak"))
        assert len(backups) >= 1

    def test_setup_no_backup_skips_backup(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["setup", str(tmp_project), "--agent", "codex", "--force", "--no-backup"]
        )
        assert result.exit_code == 0
        # No backup file should be created
        backups_dir = tmp_project / ".loom" / "backups"
        if backups_dir.exists():
            assert len(list(backups_dir.glob("AGENTS.md.*.bak"))) == 0

    def test_setup_no_install_exports_to_context(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["setup", str(tmp_project), "--agent", "claude", "--force", "--no-install"]
        )
        assert result.exit_code == 0
        assert (tmp_project / ".context" / "exports" / "CLAUDE.md").exists()
        # Should NOT install to root
        assert not (tmp_project / "CLAUDE.md").exists()

    def test_setup_interactive_yes(self, tmp_project: Path) -> None:
        runner = CliRunner()
        # Simulate: yes to claude, cursor, codex (overwrite AGENTS.md=yes), copilot; no to generic
        # tmp_project has AGENTS.md from conftest, so codex triggers overwrite confirm
        result = runner.invoke(
            main,
            ["setup", str(tmp_project)],
            input="y\ny\ny\ny\ny\nn\n",
        )
        assert result.exit_code == 0
        assert "Setup complete" in result.output
        assert (tmp_project / "CLAUDE.md").exists()

    def test_setup_interactive_skip_overwrite(self, tmp_project: Path) -> None:
        """When user says no to overwriting an existing file, it's skipped."""
        # Create CLAUDE.md first
        (tmp_project / "CLAUDE.md").write_text("# My rules")
        runner = CliRunner()
        # First confirm: yes to install claude, then no to overwrite
        # Actually with existing file, the flow is:
        # 1. confirm install for claude (yes) -> then confirm overwrite (no)
        # The interactive selection asks for each agent, then overwrite prompt is separate
        result = runner.invoke(
            main,
            ["setup", str(tmp_project), "--agent", "claude"],
            input="n\n",  # no to overwrite
        )
        assert result.exit_code == 0
        # Original content preserved
        assert (tmp_project / "CLAUDE.md").read_text() == "# My rules"

    def test_setup_detects_existing_agents(self, tmp_project: Path) -> None:
        runner = CliRunner()
        # tmp_project has AGENTS.md from conftest
        result = runner.invoke(main, ["setup", str(tmp_project), "--preset", "minimal", "--force"])
        assert result.exit_code == 0
        assert "AGENTS.md exists" in result.output

    def test_setup_shows_scan_results(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_project), "--preset", "minimal", "--force"])
        assert result.exit_code == 0
        assert "Project Type" in result.output
        assert ".context/" in result.output


class TestSetupInfraDetection:
    def test_detects_redis_dependency(self, tmp_path: Path) -> None:
        """Projects with redis in deps should show infrastructure warning."""
        import json

        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("console.log('hello');")
        pkg = {
            "name": "test",
            "dependencies": {"redis": "^4.0.0", "express": "^4.0.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / ".gitignore").write_text("node_modules/\n")

        runner = CliRunner()
        result = runner.invoke(main, ["setup", str(tmp_path), "--preset", "minimal", "--force"])
        assert result.exit_code == 0
        assert "Infrastructure" in result.output or "redis" in result.output.lower()
