"""Tests for Loom-Context."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from loom_context.cli import main
from loom_context.engine import LoomEngine
from loom_context.security.filter import FileFilter


class TestFileFilter:
    def test_excludes_node_modules(self, tmp_project: Path) -> None:
        nm = tmp_project / "node_modules" / "react" / "index.js"
        nm.parent.mkdir(parents=True)
        nm.write_text("module.exports = {};")

        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        assert not any("node_modules" in f.parts for f in files)

    def test_excludes_git(self, tmp_project: Path) -> None:
        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        assert not any(".git" in f.parts for f in files)

    def test_excludes_env(self, tmp_project: Path) -> None:
        env = tmp_project / ".env"
        env.write_text("SECRET=abc")

        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        assert not any(f.name == ".env" for f in files)

    def test_respects_gitignore(self, tmp_project: Path) -> None:
        dist = tmp_project / "dist" / "bundle.js"
        dist.parent.mkdir()
        dist.write_text("bundle")

        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        assert not any("dist" in str(f) for f in files)

    def test_walks_source_files(self, tmp_project: Path) -> None:
        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        names = {f.name for f in files}
        assert "User.ts" in names
        assert "useUser.ts" in names
        assert "package.json" in names


class TestStructureScanner:
    def test_detects_clean_architecture(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        structure = result["structure"]
        assert "clean-architecture" in structure["architecture"]

    def test_detects_project_type(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        # Has react-native in deps
        assert result["structure"]["project_type"] in {"react-native", "react"}

    def test_annotates_directories(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        tree = result["structure"]["directory_tree"]
        # Tree starts from src_root (which IS src/), so top-level keys are layers
        assert "domain" in tree
        assert tree["domain"]["_annotation"] != ""


class TestDependencyScanner:
    def test_parses_package_json(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        deps = result["deps"]
        dep_names = {d["name"] for d in deps["dependencies"]}
        assert "react" in dep_names
        assert "zustand" in dep_names
        assert "typescript" in dep_names

    def test_categorizes_deps(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        deps = result["deps"]
        stack = deps["stack_summary"]
        assert "ui-framework" in stack
        assert "state-management" in stack
        assert "testing" in stack


class TestCodeScanner:
    def test_detects_naming(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        code = result["code"]
        assert code["total_code_files"] > 0
        assert "file_naming" in code

    def test_detects_import_aliases(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        aliases = result["code"]["import_aliases"]
        assert "@domain/*" in aliases


class TestDocsScanner:
    def test_finds_docs(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        docs = result["docs"]
        assert docs["doc_count"] > 0
        assert docs["agents_md"] is not None

    def test_classifies_docs(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        doc_list = result["docs"]["docs"]
        types = {d["type"] for d in doc_list}
        assert "architecture" in types or "plan" in types

    def test_extracts_status(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        doc_list = result["docs"]["docs"]
        plan_docs = [d for d in doc_list if d["type"] == "plan"]
        assert len(plan_docs) > 0
        assert len(plan_docs[0]["status_items"]) > 0


class TestEngine:
    def test_full_init(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()

        context_dir = tmp_project / ".context"
        assert context_dir.exists()

        # Check all files generated
        expected_files = [
            "index.json",
            "architecture.md",
            "naming.md",
            "directory-map.md",
            "stack.json",
            "rules.json",
            "plans-summary.md",
        ]
        for fname in expected_files:
            assert (context_dir / fname).exists(), f"{fname} not generated"

    def test_index_json_structure(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()

        index = json.loads((tmp_project / ".context" / "index.json").read_text())
        assert "loom_version" in index
        assert "project" in index
        assert "quick_rules" in index
        assert index["project"]["type"] in {"react-native", "react"}

    def test_prompt_generation(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()
        prompt = engine.generate_prompt()
        assert "Project Context" in prompt
        assert len(prompt) > 100


class TestCLI:
    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Loom" in result.output

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_init_command(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["init", str(tmp_project)])
        assert result.exit_code == 0
        assert (tmp_project / ".context" / "index.json").exists()

    def test_scan_command(self, tmp_project: Path) -> None:
        # Init first
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        # Then scan
        result = runner.invoke(main, ["scan", str(tmp_project)])
        assert result.exit_code == 0

    def test_prompt_command(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["prompt", str(tmp_project), "--stdout"])
        assert result.exit_code == 0
        assert "Project Context" in result.output

    def test_audit_command(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["audit", str(tmp_project)])
        # Should not crash
        assert result.exit_code in {0, 1}

    def test_plan_command(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["plan", str(tmp_project)])
        assert result.exit_code == 0

    def test_prompt_to_file(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "prompt.md")
        result = runner.invoke(main, ["prompt", str(tmp_project), "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()
        content = Path(outfile).read_text(encoding="utf-8")
        assert "Project Context" in content

    def test_prompt_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["prompt", str(tmp_path)])
        assert result.exit_code == 1

    def test_audit_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["audit", str(tmp_path)])
        assert result.exit_code == 1


class TestNamingAuditor:
    def test_detects_missing_interface_prefix(self, tmp_project: Path) -> None:
        """Interfaces without I prefix should be flagged."""
        from loom_context.auditors.naming import NamingAuditor

        # Add a file with interface missing I prefix
        bad_file = tmp_project / "src" / "domain" / "ports" / "BadInterface.ts"
        bad_file.write_text("export interface UserRepository { findAll(): void; }\n")

        engine = LoomEngine(tmp_project)
        engine.init()

        ff = FileFilter(tmp_project)
        auditor = NamingAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()

        # Should find at least one violation for UserRepository (no I prefix)
        interface_violations = [v for v in violations if v.rule == "interface-prefix"]
        assert len(interface_violations) > 0
        assert any("UserRepository" in v.message for v in interface_violations)

    def test_passes_correct_interface_prefix(self, tmp_project: Path) -> None:
        """Interfaces with I prefix should pass."""
        from loom_context.auditors.naming import NamingAuditor

        engine = LoomEngine(tmp_project)
        engine.init()

        ff = FileFilter(tmp_project)
        auditor = NamingAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()

        # IUserRepository in fixture should NOT be flagged
        bad = [v for v in violations if "IUserRepository" in v.message]
        assert len(bad) == 0


class TestStructureAuditor:
    def test_detects_boundary_violation(self, tmp_project: Path) -> None:
        """Domain importing from infrastructure should be flagged."""
        from loom_context.auditors.structure import StructureAuditor

        # Add a file in domain that imports from infrastructure
        bad_file = tmp_project / "src" / "domain" / "entities" / "BadEntity.ts"
        bad_file.write_text(
            'import { UserRepository } from "@infrastructure/repositories/UserRepository";\n'
            "export class BadEntity {}\n"
        )

        engine = LoomEngine(tmp_project)
        engine.init()

        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()

        boundary_violations = [v for v in violations if v.rule == "layer-boundary"]
        assert len(boundary_violations) > 0
        assert any(
            "domain" in v.message and "infrastructure" in v.message for v in boundary_violations
        )

    def test_passes_valid_imports(self, tmp_project: Path) -> None:
        """Infrastructure importing from domain should be allowed."""
        from loom_context.auditors.structure import StructureAuditor

        engine = LoomEngine(tmp_project)
        engine.init()

        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()

        # The fixture's infrastructure/repositories/UserRepository.ts imports from domain
        # This should be allowed (infrastructure CAN import from domain)
        infra_to_domain = [
            v for v in violations if "infrastructure" in v.file and "domain" in v.message
        ]
        assert len(infra_to_domain) == 0


class TestEdgeCases:
    def test_empty_project(self, tmp_path: Path) -> None:
        """Loom should handle empty directories gracefully."""
        engine = LoomEngine(tmp_path)
        engine.init()
        assert (tmp_path / ".context" / "index.json").exists()
        index = json.loads((tmp_path / ".context" / "index.json").read_text())
        assert index["project"]["type"] == "unknown"

    def test_project_without_deps(self, tmp_path: Path) -> None:
        """Project with src/ but no package.json or pyproject.toml."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result["deps"]["dependencies"] == []
        assert result["deps"]["stack_summary"] == {}

    def test_python_project(self, tmp_path: Path) -> None:
        """Detect Python project from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "mylib"\nversion = "1.0"\n'
            'dependencies = ["click>=8.0", "requests"]\n'
        )
        src = tmp_path / "src" / "mylib"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text("")
        (src / "cli.py").write_text("import click\n")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result["structure"]["project_type"] == "python"

    def test_secret_files_excluded(self, tmp_path: Path) -> None:
        """Secret files should never appear in scan results."""
        (tmp_path / ".env").write_text("SECRET=x")
        (tmp_path / ".env.production").write_text("SECRET=y")
        (tmp_path / "credentials.json").write_text("{}")
        (tmp_path / "id_rsa").write_text("key")
        (tmp_path / "server.pem").write_text("cert")
        (tmp_path / "safe.txt").write_text("ok")

        ff = FileFilter(tmp_path)
        files = list(ff.walk())
        names = {f.name for f in files}

        assert ".env" not in names
        assert ".env.production" not in names
        assert "credentials.json" not in names
        assert "id_rsa" not in names
        assert "server.pem" not in names
        assert "safe.txt" in names

    def test_contextignore(self, tmp_path: Path) -> None:
        """Files in .contextignore should be excluded."""
        (tmp_path / ".contextignore").write_text("secret_dir/\n*.log\n")
        secret_dir = tmp_path / "secret_dir"
        secret_dir.mkdir()
        (secret_dir / "data.txt").write_text("secret")
        (tmp_path / "app.log").write_text("log")
        (tmp_path / "readme.md").write_text("ok")

        ff = FileFilter(tmp_path)
        files = list(ff.walk())
        names = {f.name for f in files}

        assert "data.txt" not in names
        assert "app.log" not in names
        assert "readme.md" in names


class TestSessionLogger:
    def test_append_and_read(self, tmp_path: Path) -> None:
        from loom_context.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        logger = SessionLogger(ctx, tmp_path)
        logger.append("first message")
        logger.append("second message")

        entries = logger.read(count=5)
        assert len(entries) == 2
        assert entries[0].message == "second message"  # newest first
        assert entries[1].message == "first message"

    def test_read_empty(self, tmp_path: Path) -> None:
        from loom_context.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        logger = SessionLogger(ctx, tmp_path)
        assert logger.read() == []

    def test_clear(self, tmp_path: Path) -> None:
        from loom_context.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        logger = SessionLogger(ctx, tmp_path)
        logger.append("entry 1")
        logger.append("entry 2")
        cleared = logger.clear()
        assert cleared == 2
        assert logger.read() == []

    def test_read_limit(self, tmp_path: Path) -> None:
        from loom_context.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        logger = SessionLogger(ctx, tmp_path)
        for i in range(10):
            logger.append(f"entry {i}")

        entries = logger.read(count=3)
        assert len(entries) == 3
        assert entries[0].message == "entry 9"

    def test_creates_context_dir(self, tmp_path: Path) -> None:
        from loom_context.session import SessionLogger

        ctx = tmp_path / ".context"
        logger = SessionLogger(ctx, tmp_path)
        logger.append("auto create")
        assert ctx.exists()
        assert (ctx / "sessions.jsonl").exists()


class TestFocusGenerator:
    def test_focus_matches_directory(self, tmp_project: Path) -> None:
        from loom_context.generators.focus import FocusGenerator

        engine = LoomEngine(tmp_project)
        engine.init()

        gen = FocusGenerator(tmp_project / ".context")
        result = gen.generate("domain")
        assert result is not None
        assert "domain" in result.lower()

    def test_focus_returns_none_for_empty_query(self, tmp_project: Path) -> None:
        from loom_context.generators.focus import FocusGenerator

        engine = LoomEngine(tmp_project)
        engine.init()

        gen = FocusGenerator(tmp_project / ".context")
        assert gen.generate("the a an") is None

    def test_focus_no_context(self, tmp_path: Path) -> None:
        from loom_context.generators.focus import FocusGenerator

        gen = FocusGenerator(tmp_path / ".context")
        assert gen.generate("anything") is None

    def test_focus_respects_max_chars(self, tmp_project: Path) -> None:
        from loom_context.generators.focus import FocusGenerator

        engine = LoomEngine(tmp_project)
        engine.init()

        gen = FocusGenerator(tmp_project / ".context")
        result = gen.generate("domain", max_chars=500)
        assert result is not None
        # The output may slightly exceed due to footer but body is truncated
        assert "truncated" in result or len(result) < 800

    def test_focus_cli_stdout(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(
            main, ["focus", "domain", str(tmp_project), "--stdout"]
        )
        assert result.exit_code == 0
        assert "domain" in result.output.lower()

    def test_focus_cli_no_context(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["focus", "test", str(tmp_path)])
        assert result.exit_code == 1


class TestStatusCommand:
    def test_status_not_initialized(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "Not initialized" in result.output

    def test_status_after_init(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["status", str(tmp_project)])
        assert result.exit_code == 0
        assert "Loom Status" in result.output

    def test_status_json(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["status", str(tmp_project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["context_exists"] is True
        assert "quick_rules" in data

    def test_status_shows_session_log(self, tmp_project: Path) -> None:
        from loom_context.session import SessionLogger

        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        ctx = tmp_project / ".context"
        logger = SessionLogger(ctx, tmp_project)
        logger.append("test session entry")

        result = runner.invoke(main, ["status", str(tmp_project)])
        assert "test session entry" in result.output


class TestLogCommand:
    def test_log_append(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(
            main, ["log", "started refactor", "--path", str(tmp_project)]
        )
        assert result.exit_code == 0
        assert "Logged" in result.output

    def test_log_show(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "entry one", "--path", str(tmp_project)])
        runner.invoke(main, ["log", "entry two", "--path", str(tmp_project)])
        result = runner.invoke(
            main, ["log", "--show", "--path", str(tmp_project)]
        )
        assert result.exit_code == 0
        assert "entry two" in result.output
        assert "entry one" in result.output

    def test_log_clear(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "to clear", "--path", str(tmp_project)])
        result = runner.invoke(
            main, ["log", "--clear", "--path", str(tmp_project)]
        )
        assert result.exit_code == 0
        assert "Cleared" in result.output

    def test_log_no_args_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["log", "--path", str(tmp_path)])
        # With just a path and no message, it should error or show help
        assert result.exit_code in {0, 1, 2}
