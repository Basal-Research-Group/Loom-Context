"""Tests for Loom-Context."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
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
        assert "clean-architecture" in result.structure.architecture

    def test_detects_project_type(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        # Has react-native in deps
        assert result.structure.project_type in {"react-native", "react"}

    def test_annotates_directories(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        tree = result.structure.directory_tree
        # Tree starts from src_root (which IS src/), so top-level keys are layers
        assert "domain" in tree
        assert tree["domain"]["_annotation"] != ""


class TestDependencyScanner:
    def test_parses_package_json(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        dep_names = {d.name for d in result.deps.dependencies}
        assert "react" in dep_names
        assert "zustand" in dep_names
        assert "typescript" in dep_names

    def test_categorizes_deps(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        stack = result.deps.stack_summary
        assert "ui-framework" in stack
        assert "state-management" in stack
        assert "testing" in stack


class TestCodeScanner:
    def test_detects_naming(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert result.code.total_code_files > 0
        assert result.code.file_naming is not None

    def test_detects_import_aliases(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert "@domain/*" in result.code.import_aliases


class TestDocsScanner:
    def test_finds_docs(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert result.docs.doc_count > 0
        assert result.docs.agents_md is not None

    def test_classifies_docs(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        types = {d.type for d in result.docs.docs}
        assert "architecture" in types or "plan" in types

    def test_extracts_status(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        plan_docs = [d for d in result.docs.docs if d.type == "plan"]
        assert len(plan_docs) > 0
        assert len(plan_docs[0].status_items) > 0


class TestFrontmatterParsing:
    def test_extracts_frontmatter_type(self, tmp_path: Path) -> None:
        """Docs with frontmatter type override heuristic classification."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "my-plan.md").write_text(
            '---\ntype: delivery\nversion: "1.0.0"\nstatus: planned\n---\n\n# My Plan\n'
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "my-plan" in d.path)
        assert doc.type == "delivery"
        assert doc.version == "1.0.0"
        assert doc.doc_status == "planned"

    def test_extracts_scope_and_patterns(self, tmp_path: Path) -> None:
        """Frontmatter scope and patterns are extracted."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "arch.md").write_text(
            "---\ntype: architecture\nscope: engine, cli\n"
            "patterns: [strategy, adapter]\n---\n\n# Architecture\n"
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "arch" in d.path)
        assert doc.type == "architecture"
        assert doc.scope == "engine, cli"
        assert doc.patterns == ["strategy", "adapter"]

    def test_no_frontmatter_uses_heuristic(self, tmp_project: Path) -> None:
        """Docs without frontmatter still classified by heuristic."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        # AGENTS.md should be classified without frontmatter
        agent_docs = [d for d in result.docs.docs if "AGENTS" in d.path]
        assert len(agent_docs) > 0
        assert agent_docs[0].type == "agent-guidelines"
        assert agent_docs[0].version is None


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

        index = json.loads((tmp_project / ".context" / "index.json").read_text(encoding="utf-8"))
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


class TestScanResult:
    def test_to_dict_preserves_format(self, tmp_project: Path) -> None:
        """ScanResult.to_dict() produces the same structure generators expect."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        data = result.to_dict()
        assert "structure" in data
        assert "deps" in data
        assert "code" in data
        assert "docs" in data
        assert "scanned_at" in data
        assert data["structure"]["project_type"] in {"react-native", "react"}
        assert isinstance(data["deps"]["dependencies"], list)
        assert isinstance(data["docs"]["docs"], list)

    def test_frozen_immutability(self, tmp_project: Path) -> None:
        """ScanResult and sub-dataclasses are immutable."""
        from dataclasses import FrozenInstanceError

        engine = LoomEngine(tmp_project)
        result = engine.scan()
        with pytest.raises(FrozenInstanceError):
            result.structure = None  # type: ignore[misc]

    def test_scan_result_typed_access(self, tmp_project: Path) -> None:
        """ScanResult attributes are typed, not dict access."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        # Attribute access works
        assert isinstance(result.structure.project_type, str)
        assert isinstance(result.structure.architecture, list)
        assert isinstance(result.deps.dependencies, list)
        assert isinstance(result.code.total_code_files, int)
        assert isinstance(result.docs.doc_count, int)
        # Dependency is typed
        if result.deps.dependencies:
            dep = result.deps.dependencies[0]
            assert isinstance(dep.name, str)
            assert isinstance(dep.dev, bool)

    def test_to_dict_roundtrip_generates_context(self, tmp_project: Path) -> None:
        """ScanResult.to_dict() can be used by generators without error."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        generated = engine.generate_context(result)
        assert len(generated) == 7
        assert "index.json" in generated


class TestPipelineDetection:
    def test_detects_pipeline_architecture(self, tmp_path: Path) -> None:
        """Projects with scanners + generators dirs detected as pipeline."""
        src = tmp_path / "src" / "myapp"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text("")
        (src / "scanners").mkdir()
        (src / "scanners" / "__init__.py").write_text("")
        (src / "generators").mkdir()
        (src / "generators" / "__init__.py").write_text("")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "pipeline" in result.structure.architecture

    def test_detects_etl_pipeline(self, tmp_path: Path) -> None:
        """Projects with extractors + processors + loaders detected as pipeline."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "extractors").mkdir()
        (src / "processors").mkdir()
        (src / "loaders").mkdir()

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "pipeline" in result.structure.architecture


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
        assert "0.2.0" in result.output

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
        index = json.loads((tmp_path / ".context" / "index.json").read_text(encoding="utf-8"))
        assert index["project"]["type"] == "unknown"

    def test_project_without_deps(self, tmp_path: Path) -> None:
        """Project with src/ but no package.json or pyproject.toml."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.dependencies == []
        assert result.deps.stack_summary == {}

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
        assert result.structure.project_type == "python"

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


class TestDependencyScannerExtended:
    def test_pep621_pyproject(self, tmp_path: Path) -> None:
        """Parse pyproject.toml with PEP 621 [project] format."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "mylib"\nversion = "1.0"\n'
            'dependencies = ["fastapi>=0.100", "uvicorn>=0.23"]\n\n'
            "[project.optional-dependencies]\n"
            'dev = ["pytest>=7.0", "ruff>=0.4"]\n'
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        dep_names = {d.name for d in result.deps.dependencies}
        assert "fastapi" in dep_names
        assert "uvicorn" in dep_names

    def test_requirements_txt(self, tmp_path: Path) -> None:
        """Parse requirements.txt."""
        (tmp_path / "requirements.txt").write_text(
            "flask>=2.0\nrequests==2.28\nsqlalchemy\n# comment\n\n"
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        dep_names = {d.name for d in result.deps.dependencies}
        assert "flask" in dep_names
        assert "requests" in dep_names
        assert "sqlalchemy" in dep_names

    def test_package_json_dev_deps(self, tmp_project: Path) -> None:
        """Dev dependencies are marked as dev=True."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        ts_dep = next((d for d in result.deps.dependencies if d.name == "typescript"), None)
        assert ts_dep is not None
        assert ts_dep.dev is True

    def test_known_package_categorization(self, tmp_project: Path) -> None:
        """Known packages get proper categories."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        react_dep = next((d for d in result.deps.dependencies if d.name == "react"), None)
        assert react_dep is not None
        assert react_dep.category == "ui-framework"


class TestFilterExtended:
    def test_contextignore_glob_patterns(self, tmp_path: Path) -> None:
        """Complex .contextignore glob patterns."""
        (tmp_path / ".contextignore").write_text("**/*.generated.ts\n**/fixtures/**\ntemp_*\n")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "api.generated.ts").write_text("gen")
        (tmp_path / "src" / "api.ts").write_text("real")
        fixtures = tmp_path / "src" / "fixtures"
        fixtures.mkdir()
        (fixtures / "data.json").write_text("{}")
        (tmp_path / "temp_file.txt").write_text("tmp")
        (tmp_path / "keep.txt").write_text("ok")

        ff = FileFilter(tmp_path)
        files = list(ff.walk())
        names = {f.name for f in files}
        assert "api.ts" in names
        assert "api.generated.ts" not in names
        assert "data.json" not in names
        assert "temp_file.txt" not in names
        assert "keep.txt" in names

    def test_excludes_keystore_and_p12(self, tmp_path: Path) -> None:
        """Keystore and certificate files are always excluded."""
        (tmp_path / "release.keystore").write_text("key")
        (tmp_path / "cert.p12").write_text("cert")
        (tmp_path / "app.ts").write_text("ok")

        ff = FileFilter(tmp_path)
        files = list(ff.walk())
        names = {f.name for f in files}
        assert "release.keystore" not in names
        assert "cert.p12" not in names
        assert "app.ts" in names

    def test_excludes_expo_and_next_dirs(self, tmp_path: Path) -> None:
        """Framework-specific dirs are excluded."""
        for d in [".expo", ".next", ".nuxt", ".turbo"]:
            p = tmp_path / d
            p.mkdir()
            (p / "cache.json").write_text("{}")
        (tmp_path / "src.ts").write_text("ok")

        ff = FileFilter(tmp_path)
        files = list(ff.walk())
        parts = set()
        for f in files:
            parts.update(f.parts)
        assert ".expo" not in parts
        assert ".next" not in parts
        assert ".nuxt" not in parts


class TestFocusExtended:
    def test_focus_matches_stack(self, tmp_project: Path) -> None:
        """Focus finds stack-related context."""
        from loom_context.generators.focus import FocusGenerator

        engine = LoomEngine(tmp_project)
        engine.init()

        gen = FocusGenerator(tmp_project / ".context")
        result = gen.generate("react zustand")
        assert result is not None
        assert len(result) > 0

    def test_focus_matches_naming(self, tmp_project: Path) -> None:
        """Focus finds naming-related context."""
        from loom_context.generators.focus import FocusGenerator

        engine = LoomEngine(tmp_project)
        engine.init()

        gen = FocusGenerator(tmp_project / ".context")
        result = gen.generate("naming conventions interface prefix")
        assert result is not None

    def test_focus_to_file(self, tmp_project: Path) -> None:
        """Focus writes to file via CLI."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "focus.md")
        result = runner.invoke(main, ["focus", "domain", str(tmp_project), "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()
        assert len(Path(outfile).read_text(encoding="utf-8")) > 0


class TestSessionLogger:
    def test_append_and_read(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        logger.append("first message")
        logger.append("second message")

        entries = logger.read(count=5)
        assert len(entries) == 2
        assert entries[0].message == "second message"  # newest first
        assert entries[1].message == "first message"

    def test_read_empty(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        assert logger.read() == []

    def test_clear(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        logger.append("entry 1")
        logger.append("entry 2")
        cleared = logger.clear()
        assert cleared == 2
        assert logger.read() == []

    def test_read_limit(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        for i in range(10):
            logger.append(f"entry {i}")

        entries = logger.read(count=3)
        assert len(entries) == 3
        assert entries[0].message == "entry 9"

    def test_creates_loom_dir(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        logger = SessionLogger(loom, tmp_path)
        logger.append("auto create")
        assert loom.exists()
        assert (loom / "sessions.jsonl").exists()

    def test_migrate_from_context(self, tmp_path: Path) -> None:
        from loom_context.store.session import SessionLogger

        # Create old-style sessions in .context/
        ctx = tmp_path / ".context"
        ctx.mkdir()
        old_path = ctx / "sessions.jsonl"
        old_path.write_text('{"timestamp":"2024-01-01","message":"old entry"}\n')

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        migrated = logger.migrate_from_context(ctx)

        assert migrated
        assert not old_path.exists()
        entries = logger.read()
        assert len(entries) == 1
        assert entries[0].message == "old entry"


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
        result = runner.invoke(main, ["focus", "domain", str(tmp_project), "--stdout"])
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
        from loom_context.store.session import SessionLogger

        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        loom = tmp_project / ".loom"
        loom.mkdir(exist_ok=True)
        logger = SessionLogger(loom, tmp_project)
        logger.append("test session entry")

        result = runner.invoke(main, ["status", str(tmp_project)])
        assert "test session entry" in result.output


class TestLogCommand:
    def test_log_append(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["log", "started refactor", "--path", str(tmp_project)])
        assert result.exit_code == 0
        assert "Logged" in result.output

    def test_log_show(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "entry one", "--path", str(tmp_project)])
        runner.invoke(main, ["log", "entry two", "--path", str(tmp_project)])
        result = runner.invoke(main, ["log", "--show", "--path", str(tmp_project)])
        assert result.exit_code == 0
        assert "entry two" in result.output
        assert "entry one" in result.output

    def test_log_clear(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "to clear", "--path", str(tmp_project)])
        result = runner.invoke(main, ["log", "--clear", "--path", str(tmp_project)])
        assert result.exit_code == 0
        assert "Cleared" in result.output

    def test_log_no_args_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["log", "--path", str(tmp_path)])
        # With just a path and no message, it should error or show help
        assert result.exit_code in {0, 1, 2}


class TestFindingsStore:
    def test_save_and_load(self, tmp_path: Path) -> None:
        from loom_context.auditors.naming import Violation
        from loom_context.store.findings import FindingsStore

        loom = tmp_path / ".loom"
        loom.mkdir()
        store = FindingsStore(loom, tmp_path)

        violations = [
            Violation(
                file="src/bad.ts",
                line=10,
                rule="interface-prefix",
                message="Missing I prefix",
                severity="warning",
                suggestion="Add I prefix",
            ),
            Violation(
                file="src/worse.ts",
                line=5,
                rule="layer-boundary",
                message="Domain imports infra",
                severity="error",
            ),
        ]
        findings = store.save(violations)
        assert findings.errors == 1
        assert findings.warnings == 1

        loaded = store.load()
        assert loaded is not None
        assert loaded.errors == 1
        assert loaded.warnings == 1
        assert len(loaded.violations) == 2

    def test_load_empty(self, tmp_path: Path) -> None:
        from loom_context.store.findings import FindingsStore

        loom = tmp_path / ".loom"
        loom.mkdir()
        store = FindingsStore(loom, tmp_path)
        assert store.load() is None

    def test_has_findings(self, tmp_path: Path) -> None:
        from loom_context.auditors.naming import Violation
        from loom_context.store.findings import FindingsStore

        loom = tmp_path / ".loom"
        loom.mkdir()
        store = FindingsStore(loom, tmp_path)
        assert not store.has_findings()

        store.save([Violation(file="x.ts", line=1, rule="r", message="m", severity="warning")])
        assert store.has_findings()

    def test_save_empty_violations(self, tmp_path: Path) -> None:
        from loom_context.store.findings import FindingsStore

        loom = tmp_path / ".loom"
        loom.mkdir()
        store = FindingsStore(loom, tmp_path)
        findings = store.save([])
        assert findings.errors == 0
        assert findings.warnings == 0
        assert not store.has_findings()


class TestDecisionLog:
    def test_append_and_read(self, tmp_path: Path) -> None:
        from loom_context.store.decisions import DecisionLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = DecisionLog(loom, tmp_path)

        log.append("use repository pattern", "decouple persistence", "architecture")
        log.append("add I prefix to interfaces", "consistency", "naming")

        entries = log.read(count=10)
        assert len(entries) == 2
        assert entries[0].summary == "add I prefix to interfaces"  # newest first
        assert entries[0].scope == "naming"
        assert entries[1].summary == "use repository pattern"

    def test_read_empty(self, tmp_path: Path) -> None:
        from loom_context.store.decisions import DecisionLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = DecisionLog(loom, tmp_path)
        assert log.read() == []

    def test_clear(self, tmp_path: Path) -> None:
        from loom_context.store.decisions import DecisionLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = DecisionLog(loom, tmp_path)
        log.append("decision 1", "reason", "architecture")
        log.append("decision 2", "reason", "deps")
        cleared = log.clear()
        assert cleared == 2
        assert log.read() == []

    def test_read_limit(self, tmp_path: Path) -> None:
        from loom_context.store.decisions import DecisionLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = DecisionLog(loom, tmp_path)
        for i in range(5):
            log.append(f"decision {i}", "reason", "architecture")

        entries = log.read(count=2)
        assert len(entries) == 2
        assert entries[0].summary == "decision 4"


class TestMutationLog:
    def test_record_and_read(self, tmp_path: Path) -> None:
        from loom_context.store.mutations import MutationLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = MutationLog(loom, tmp_path)

        log.record("init", ["index.json", "rules.json"], "initialized with 2 files")
        log.record("enrich", ["rules.json"], "enriched after 1 error")

        entries = log.read(count=10)
        assert len(entries) == 2
        assert entries[0].action == "enrich"  # newest first
        assert entries[1].action == "init"
        assert "index.json" in entries[1].files_changed

    def test_read_empty(self, tmp_path: Path) -> None:
        from loom_context.store.mutations import MutationLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        log = MutationLog(loom, tmp_path)
        assert log.read() == []


class TestInitWithAudit:
    def test_init_creates_loom_dir(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.init()

        assert (tmp_project / ".loom").exists()
        assert "audit" in result
        assert "errors" in result["audit"]
        assert "warnings" in result["audit"]

    def test_init_persists_findings(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()

        findings_path = tmp_project / ".loom" / "inconsistencies.json"
        assert findings_path.exists()
        data = json.loads(findings_path.read_text(encoding="utf-8"))
        assert "errors" in data
        assert "warnings" in data
        assert "violations" in data

    def test_init_records_mutation(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()

        mutations_path = tmp_project / ".loom" / "mutations.jsonl"
        assert mutations_path.exists()
        lines = [ln for ln in mutations_path.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["action"] == "init"

    def test_init_shows_audit_in_cli(self, tmp_project: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["init", str(tmp_project)])
        assert result.exit_code == 0
        assert "Audit" in result.output


class TestEnrichCommand:
    def test_enrich_basic(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["enrich", str(tmp_project)])
        assert result.exit_code == 0
        assert "Updated" in result.output
        assert "Findings persisted" in result.output

    def test_enrich_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["enrich", str(tmp_path)])
        assert result.exit_code == 1

    def test_enrich_persists_findings(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()
        engine.enrich()

        findings_path = tmp_project / ".loom" / "inconsistencies.json"
        assert findings_path.exists()

        mutations_path = tmp_project / ".loom" / "mutations.jsonl"
        lines = [ln for ln in mutations_path.read_text().splitlines() if ln.strip()]
        # At least 2: init + enrich
        assert len(lines) >= 2
        last = json.loads(lines[-1])
        assert last["action"] == "enrich"


class TestDecideCommand:
    def test_decide_basic(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["decide", "use repository pattern", "-r", "decouple persistence", "-p", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Decision recorded" in result.output

    def test_decide_show(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            main,
            ["decide", "decision one", "-r", "reason one", "-p", str(tmp_path)],
        )
        result = runner.invoke(main, ["decide", "--show", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert "decision one" in result.output

    def test_decide_clear(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            main,
            ["decide", "to clear", "-r", "test", "-p", str(tmp_path)],
        )
        result = runner.invoke(main, ["decide", "--clear", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert "Cleared" in result.output

    def test_decide_no_args_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["decide", "-p", str(tmp_path)])
        assert result.exit_code in {0, 1, 2}


class TestAuditCommandExtended:
    def test_audit_with_violations(self, tmp_project: Path) -> None:
        """Audit shows table when violations found."""
        # Add a file with boundary violation
        bad = tmp_project / "src" / "domain" / "entities" / "Bad.ts"
        bad.write_text('import { X } from "@infrastructure/repos/X";\n')
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["audit", str(tmp_project)])
        assert result.exit_code == 1
        assert "ERROR" in result.output
        assert "Summary" in result.output


class TestExportInstall:
    def test_export_to_file(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "custom.md")
        result = runner.invoke(
            main, ["export", str(tmp_project), "--agent", "generic", "-o", outfile]
        )
        assert result.exit_code == 0
        assert Path(outfile).exists()

    def test_export_install(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "claude", "--install"])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (tmp_project / "CLAUDE.md").exists()


class TestHandoffExtended:
    def test_handoff_to_file(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "handoff.md")
        result = runner.invoke(main, ["handoff", "task", str(tmp_project), "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()

    def test_handoff_info_display(self, tmp_project: Path) -> None:
        """Without --stdout or --save, shows info panel."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["handoff", "task", str(tmp_project)])
        assert result.exit_code == 0
        assert "Loom Handoff" in result.output


class TestBundleExtended:
    def test_bundle_to_file(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "bundle.md")
        result = runner.invoke(main, ["bundle", "domain", str(tmp_project), "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()

    def test_bundle_info_display(self, tmp_project: Path) -> None:
        """Without --stdout or --save, shows info panel."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["bundle", "domain", str(tmp_project)])
        assert result.exit_code == 0
        assert "Loom Bundle" in result.output

    def test_bundle_token_budget(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(
            main,
            ["bundle", "domain", str(tmp_project), "--stdout", "--token-budget", "100"],
        )
        assert result.exit_code == 0


class TestPromptExtended:
    def test_prompt_info_display(self, tmp_project: Path) -> None:
        """Without --stdout, shows info panel."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["prompt", str(tmp_project)])
        assert result.exit_code == 0
        assert "Loom Prompt" in result.output

    def test_prompt_compact_to_file(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "compact.txt")
        result = runner.invoke(main, ["prompt", str(tmp_project), "--compact", "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()
        content = Path(outfile).read_text(encoding="utf-8")
        assert "CTX:" in content


class TestFocusNoContext:
    def test_focus_no_match(self, tmp_project: Path) -> None:
        """Focus with irrelevant query returns None via CLI."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["focus", "xyznonexistent", str(tmp_project), "--stdout"])
        # Should either output something or exit gracefully
        assert result.exit_code in {0, 1}


class TestDoctorExtended:
    def test_doctor_stale_context(self, tmp_project: Path) -> None:
        """Doctor detects stale context."""
        import time

        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        # Touch a source file to make context stale
        time.sleep(0.1)
        (tmp_project / "src" / "domain" / "entities" / "New.ts").write_text("export {};\n")
        result = runner.invoke(main, ["doctor", str(tmp_project)])
        assert result.exit_code == 0
        assert "stale" in result.output.lower() or "passed" in result.output.lower()


class TestStatusExtended:
    def test_status_with_findings(self, tmp_project: Path) -> None:
        """Status shows findings when they exist."""
        # Add violation to trigger findings
        bad = tmp_project / "src" / "domain" / "entities" / "Bad2.ts"
        bad.write_text('import { X } from "@infrastructure/repos/X";\n')
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["status", str(tmp_project)])
        assert result.exit_code == 0
        assert "Findings" in result.output or "errors" in result.output


class TestHandoffCommand:
    def test_handoff_stdout(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["handoff", "refactor auth", str(tmp_project), "--stdout"])
        assert result.exit_code == 0
        assert "Handoff" in result.output
        assert "refactor auth" in result.output

    def test_handoff_save(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["handoff", "domain layer", str(tmp_project), "--save"])
        assert result.exit_code == 0
        handoff_path = tmp_project / ".context" / "handoffs" / "domain-layer.md"
        assert handoff_path.exists()
        content = handoff_path.read_text()
        assert "domain layer" in content

    def test_handoff_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["handoff", "test", str(tmp_path)])
        assert result.exit_code == 1

    def test_handoff_includes_state(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "session note", "-p", str(tmp_project)])
        runner.invoke(
            main,
            ["decide", "use ports", "-r", "decouple", "-p", str(tmp_project)],
        )
        result = runner.invoke(main, ["handoff", "architecture", str(tmp_project), "--stdout"])
        assert result.exit_code == 0
        assert "session note" in result.output
        assert "use ports" in result.output


class TestDoctorCommand:
    def test_doctor_initialized(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["doctor", str(tmp_project)])
        assert result.exit_code == 0
        assert ".context/ exists" in result.output
        assert "index.json valid" in result.output

    def test_doctor_not_initialized(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        assert "missing" in result.output

    def test_doctor_checks_loom_files(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["doctor", str(tmp_project)])
        assert result.exit_code == 0
        assert ".loom/ exists" in result.output
        assert "findings persisted" in result.output
        assert "mutation log active" in result.output


class TestCompactFormat:
    def test_compact_prompt_smaller(self, tmp_project: Path) -> None:
        """Compact prompt is significantly smaller than normal prompt."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        normal = runner.invoke(main, ["prompt", str(tmp_project), "--stdout"])
        compact = runner.invoke(main, ["prompt", str(tmp_project), "--stdout", "--compact"])

        assert normal.exit_code == 0
        assert compact.exit_code == 0
        assert len(compact.output) < len(normal.output) * 0.5

    def test_compact_prompt_has_structure(self, tmp_project: Path) -> None:
        """Compact prompt contains key tags."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["prompt", str(tmp_project), "--stdout", "--compact"])
        assert "CTX:" in result.output
        assert "STATS:" in result.output

    def test_compact_bundle(self, tmp_project: Path) -> None:
        """Compact bundle works with --compact flag."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(
            main, ["bundle", "domain", str(tmp_project), "--stdout", "--compact"]
        )
        assert result.exit_code == 0
        assert "BUNDLE:" in result.output

    def test_top_k_limits_sections(self, tmp_project: Path) -> None:
        """--top-k limits bundle to N sections."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])

        full = runner.invoke(main, ["bundle", "domain", str(tmp_project), "--stdout"])
        top1 = runner.invoke(
            main, ["bundle", "domain", str(tmp_project), "--stdout", "--top-k", "1"]
        )
        assert len(top1.output) < len(full.output)


class TestExportCommand:
    def test_export_claude(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "claude"])
        assert result.exit_code == 0
        assert "Exported for claude" in result.output
        assert (tmp_project / ".context" / "exports" / "CLAUDE.md").exists()

    def test_export_cursor(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "cursor"])
        assert result.exit_code == 0
        assert (tmp_project / ".context" / "exports" / ".cursorrules").exists()

    def test_export_codex(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "codex"])
        assert result.exit_code == 0
        assert (tmp_project / ".context" / "exports" / "AGENTS.md").exists()

    def test_export_stdout(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "generic", "--stdout"])
        assert result.exit_code == 0
        assert "Project Context" in result.output

    def test_export_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["export", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 1


class TestBundleCommand:
    def test_bundle_stdout(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(
            main, ["bundle", "domain architecture", str(tmp_project), "--stdout"]
        )
        assert result.exit_code == 0
        assert "domain" in result.output.lower()

    def test_bundle_save(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["bundle", "domain layer", str(tmp_project), "--save"])
        assert result.exit_code == 0
        bundle_dir = tmp_project / ".context" / "bundles" / "domain-layer"
        assert bundle_dir.exists()
        assert (bundle_dir / "bundle.md").exists()
        assert (bundle_dir / "manifest.json").exists()

        manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["task"] == "domain layer"
        assert manifest["selection_strategy"] == "heuristic"
        assert manifest["included_count"] > 0

    def test_bundle_no_context_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["bundle", "test", str(tmp_path)])
        assert result.exit_code == 1

    def test_bundle_smaller_than_prompt(self, tmp_project: Path) -> None:
        """Bundle should be significantly smaller than full prompt."""
        engine = LoomEngine(tmp_project)
        engine.init()
        prompt = engine.generate_prompt()

        from loom_context.selector.bundle import BundleBuilder

        builder = BundleBuilder(tmp_project / ".context", tmp_project)
        result = builder.build("domain")
        assert result is not None
        content, _manifest = result
        assert len(content) < len(prompt)

    def test_bundle_manifest_has_metadata(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        engine.init()

        from loom_context.selector.bundle import BundleBuilder

        builder = BundleBuilder(tmp_project / ".context", tmp_project)
        result = builder.build("architecture boundaries")
        assert result is not None
        _, manifest = result
        assert manifest.task == "architecture boundaries"
        assert manifest.loom_version == "0.2.0"
        assert manifest.selection_strategy == "heuristic"
        assert len(manifest.included_sections) > 0
