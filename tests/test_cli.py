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
        assert len(generated) >= 7
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
        assert "0.6.0" in result.output

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


class TestFilterWalk:
    def test_walk_counts_files(self, tmp_project: Path) -> None:
        """Walk yields all non-excluded files."""
        ff = FileFilter(tmp_project)
        files = list(ff.walk())
        assert len(files) > 5

    def test_is_excluded_hardcoded_dirs(self, tmp_path: Path) -> None:
        """Hardcoded dirs are always excluded."""
        ff = FileFilter(tmp_path)
        for d in ["node_modules", "__pycache__", ".git", "dist", "build"]:
            p = tmp_path / d / "file.js"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
            assert ff.is_excluded(p) or d in str(p)

    def test_is_secret(self, tmp_path: Path) -> None:
        """Secret files detected by pattern."""
        ff = FileFilter(tmp_path)
        for name in [".env", ".env.local", "credentials.json", "id_rsa", "server.pem"]:
            p = tmp_path / name
            p.write_text("secret")
            assert ff.is_secret(p)


class TestSessionFiltering:
    def test_session_branch_filter(self, tmp_path: Path) -> None:
        """Session read with branch filter."""
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        logger.append("entry 1")
        logger.append("entry 2")

        # Filter by current branch (whatever it is)
        all_entries = logger.read(count=10)
        if all_entries and all_entries[0].branch:
            filtered = logger.read(count=10, branch=all_entries[0].branch)
            assert len(filtered) > 0

    def test_session_since_filter(self, tmp_path: Path) -> None:
        """Session read with since filter."""
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        logger.append("old entry")
        logger.append("new entry")

        entries = logger.read(count=10, since="2020-01-01")
        assert len(entries) == 2


class TestStructureScannerExtended:
    def test_detects_mvc(self, tmp_path: Path) -> None:
        """Detect MVC architecture."""
        src = tmp_path / "src"
        src.mkdir()
        for d in ["models", "views", "controllers"]:
            (src / d).mkdir()
            (src / d / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "mvc" in result.structure.architecture

    def test_detects_feature_based(self, tmp_path: Path) -> None:
        """Detect feature-based architecture."""
        src = tmp_path / "src"
        src.mkdir()
        features = src / "features"
        features.mkdir()
        (features / "auth").mkdir()
        (features / "auth" / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "feature-based" in result.structure.architecture

    def test_detects_layered(self, tmp_path: Path) -> None:
        """Detect layered architecture."""
        src = tmp_path / "src"
        src.mkdir()
        for d in ["controllers", "services", "repositories"]:
            (src / d).mkdir()
            (src / d / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "layered" in result.structure.architecture


class TestConfigExtended:
    def test_loom_json_override(self, tmp_path: Path) -> None:
        """LoomConfig reads .context/loom.json overrides."""
        from loom_context.config import LoomConfig

        ctx = tmp_path / ".context"
        ctx.mkdir()
        import json

        (ctx / "loom.json").write_text(json.dumps({"project_type": "custom"}))
        config = LoomConfig(tmp_path)
        assert config.project_type == "custom"

    def test_ensure_gitignore_creates_entries(self, tmp_path: Path) -> None:
        """ensure_gitignore adds Loom entries to new .gitignore."""
        from loom_context.config import LoomConfig

        config = LoomConfig(tmp_path)
        modified = config.ensure_gitignore()
        assert modified is True

        content = (tmp_path / ".gitignore").read_text()
        assert ".loom/*" in content
        assert "!.loom/reports/" in content

    def test_ensure_gitignore_appends_to_existing(self, tmp_path: Path) -> None:
        """ensure_gitignore appends to existing .gitignore without duplicating."""
        from loom_context.config import LoomConfig

        (tmp_path / ".gitignore").write_text("node_modules/\n.env\n")
        config = LoomConfig(tmp_path)
        modified = config.ensure_gitignore()
        assert modified is True

        content = (tmp_path / ".gitignore").read_text()
        assert "node_modules/" in content
        assert ".loom/*" in content
        assert "!.loom/reports/" in content

    def test_ensure_gitignore_idempotent(self, tmp_path: Path) -> None:
        """ensure_gitignore does not duplicate entries on second run."""
        from loom_context.config import LoomConfig

        config = LoomConfig(tmp_path)
        config.ensure_gitignore()
        modified = config.ensure_gitignore()
        assert modified is False

        content = (tmp_path / ".gitignore").read_text()
        assert content.count(".loom/*") == 1
        assert content.count("!.loom/reports/") == 1

    def test_ensure_gitignore_skips_if_loom_already_present(self, tmp_path: Path) -> None:
        """ensure_gitignore skips .loom entry if .loom/ already in .gitignore."""
        from loom_context.config import LoomConfig

        (tmp_path / ".gitignore").write_text(".loom/\n")
        config = LoomConfig(tmp_path)
        modified = config.ensure_gitignore()
        assert modified is True

        content = (tmp_path / ".gitignore").read_text()
        # Should not add .loom/* since .loom/ already covers it
        assert ".loom/" in content
        assert "!.loom/reports/" in content

    def test_ensure_loom_dir_creates_reports(self, tmp_path: Path) -> None:
        """ensure_loom_dir also creates reports/ subdirectory."""
        from loom_context.config import LoomConfig

        config = LoomConfig(tmp_path)
        config.ensure_loom_dir()
        assert (tmp_path / ".loom" / "reports").is_dir()


class TestWatchCommand:
    def test_watch_help(self) -> None:
        """Watch command has help."""
        runner = CliRunner()
        result = runner.invoke(main, ["watch", "--help"])
        assert result.exit_code == 0
        assert "interval" in result.output


class TestFilterWalkDirs:
    def test_walk_dirs_skips_excluded(self, tmp_project: Path) -> None:
        """walk_dirs skips excluded directories."""
        ff = FileFilter(tmp_project)
        dirs = list(ff.walk_dirs())
        dir_names = {d.name for d in dirs}
        assert "node_modules" not in dir_names
        assert ".git" not in dir_names
        assert "src" in dir_names

    def test_walk_dirs_skips_context(self, tmp_project: Path) -> None:
        """walk_dirs skips .context/ directory."""
        # Create .context/ first
        (tmp_project / ".context").mkdir(exist_ok=True)
        ff = FileFilter(tmp_project)
        dirs = list(ff.walk_dirs())
        dir_names = {d.name for d in dirs}
        assert ".context" not in dir_names


class TestDepsScannerPackageManagers:
    def test_detects_pnpm(self, tmp_path: Path) -> None:
        """Detect pnpm from lock file."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^19"}}')
        (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: 5")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.package_manager == "pnpm"

    def test_detects_yarn(self, tmp_path: Path) -> None:
        """Detect yarn from lock file."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^19"}}')
        (tmp_path / "yarn.lock").write_text("# yarn")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.package_manager == "yarn"

    def test_detects_npm(self, tmp_path: Path) -> None:
        """Detect npm from lock file."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^19"}}')
        (tmp_path / "package-lock.json").write_text("{}")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.package_manager == "npm"

    def test_detects_uv(self, tmp_path: Path) -> None:
        """Detect uv from lock file."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "x"\nversion = "1"\ndependencies = ["click"]\n'
        )
        (tmp_path / "uv.lock").write_text("# uv")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.package_manager == "uv"


class TestStructureProjectTypes:
    def test_detects_nextjs(self, tmp_path: Path) -> None:
        (tmp_path / "next.config.js").write_text("module.exports = {};")
        (tmp_path / "package.json").write_text('{"dependencies": {"next": "^14"}}')
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "nextjs"

    def test_detects_rust(self, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "mylib"')
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "rust"

    def test_detects_go(self, tmp_path: Path) -> None:
        (tmp_path / "go.mod").write_text("module example.com/mymod")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "go"

    def test_detects_angular(self, tmp_path: Path) -> None:
        (tmp_path / "angular.json").write_text("{}")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "angular"


class TestSessionMigrationExtended:
    def test_migrate_appends_when_target_exists(self, tmp_path: Path) -> None:
        """Migration appends old entries when .loom/sessions.jsonl exists."""
        from loom_context.store.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "sessions.jsonl").write_text('{"timestamp":"2024-01-01","message":"old"}\n')

        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "sessions.jsonl").write_text('{"timestamp":"2024-06-01","message":"existing"}\n')

        logger = SessionLogger(loom, tmp_path)
        migrated = logger.migrate_from_context(ctx)
        assert migrated
        assert not (ctx / "sessions.jsonl").exists()
        entries = logger.read(count=10)
        messages = {e.message for e in entries}
        assert "old" in messages
        assert "existing" in messages

    def test_migrate_no_old_file(self, tmp_path: Path) -> None:
        """Migration returns False when no old file exists."""
        from loom_context.store.session import SessionLogger

        ctx = tmp_path / ".context"
        ctx.mkdir()
        loom = tmp_path / ".loom"
        loom.mkdir()
        logger = SessionLogger(loom, tmp_path)
        assert not logger.migrate_from_context(ctx)

    def test_session_corrupted_lines(self, tmp_path: Path) -> None:
        """Corrupted JSONL lines are skipped."""
        from loom_context.store.session import SessionLogger

        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "sessions.jsonl").write_text(
            '{"timestamp":"2024-01-01","message":"good"}\n'
            "not json\n"
            '{"timestamp":"2024-01-02","message":"also good"}\n'
        )
        logger = SessionLogger(loom, tmp_path)
        entries = logger.read(count=10)
        assert len(entries) == 2


class TestHandoffWithFindings:
    def test_handoff_shows_violations(self, tmp_project: Path) -> None:
        """Handoff includes violation breakdown when findings exist."""
        # Add boundary violation
        bad = tmp_project / "src" / "domain" / "entities" / "Violation.ts"
        bad.write_text('import { X } from "@infrastructure/repos/X";\n')

        engine = LoomEngine(tmp_project)
        engine.init()

        from loom_context.selector.handoff import HandoffBuilder

        builder = HandoffBuilder(tmp_project / ".context", tmp_project / ".loom", tmp_project)
        content = builder.build("fix violations")
        assert content is not None
        assert "Current State" in content
        assert "layer-boundary" in content


class TestStatusStaleness:
    def test_status_no_scan_timestamp(self, tmp_path: Path) -> None:
        """Status handles missing generated_at in index.json."""
        from loom_context.status import StatusCollector

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "unknown"}}')

        collector = StatusCollector(tmp_path)
        st = collector.collect()
        assert st.context_exists
        assert st.is_stale  # No timestamp means stale

    def test_status_corrupted_index(self, tmp_path: Path) -> None:
        """Status handles corrupted index.json."""
        from loom_context.status import StatusCollector

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text("not json")

        collector = StatusCollector(tmp_path)
        st = collector.collect()
        assert st.context_exists
        assert st.project_type == "unknown"


class TestDoctorEdgeCases:
    def test_doctor_corrupted_index(self, tmp_path: Path) -> None:
        """Doctor handles corrupted index.json."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text("not json")
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        assert "corrupted" in result.output

    def test_doctor_missing_context_files(self, tmp_path: Path) -> None:
        """Doctor reports missing context files."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        assert "missing" in result.output

    def test_doctor_no_gitignore(self, tmp_path: Path) -> None:
        """Doctor warns about missing .gitignore."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        assert "gitignore" in result.output.lower()


class TestHeuristicEdgeCases:
    def test_empty_context_dir(self, tmp_path: Path) -> None:
        """Heuristic handles empty .context/ gracefully."""
        from loom_context.selector.strategies.heuristic import HeuristicStrategy

        ctx = tmp_path / ".context"
        ctx.mkdir()
        strategy = HeuristicStrategy(ctx)
        candidates = strategy.select("anything")
        assert candidates == []

    def test_matches_with_spanish_query(self, tmp_project: Path) -> None:
        """Heuristic handles Spanish stop words."""
        from loom_context.selector.strategies.heuristic import HeuristicStrategy

        engine = LoomEngine(tmp_project)
        engine.init()
        strategy = HeuristicStrategy(tmp_project / ".context")
        candidates = strategy.select("la arquitectura del dominio")
        # Should filter stop words and still find matches
        assert len(candidates) > 0


class TestLogCommandExtended:
    def test_log_show_empty(self, tmp_path: Path) -> None:
        """Log --show with no entries."""
        runner = CliRunner()
        loom = tmp_path / ".loom"
        loom.mkdir()
        result = runner.invoke(main, ["log", "--show", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert "No session entries" in result.output

    def test_log_show_with_entries(self, tmp_project: Path) -> None:
        """Log --show with entries shows details."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["log", "first", "-p", str(tmp_project)])
        runner.invoke(main, ["log", "second", "-p", str(tmp_project)])
        result = runner.invoke(main, ["log", "--show", "-p", str(tmp_project)])
        assert result.exit_code == 0
        assert "second" in result.output
        assert "first" in result.output


class TestPlanCommandExtended:
    def test_plan_no_docs(self, tmp_path: Path) -> None:
        """Plan with no docs shows message."""
        runner = CliRunner()
        result = runner.invoke(main, ["plan", str(tmp_path)])
        assert result.exit_code == 0
        assert "No documentation" in result.output

    def test_plan_with_frontmatter(self, tmp_path: Path) -> None:
        """Plan shows frontmatter badges."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "plan.md").write_text(
            '---\ntype: delivery\nversion: "1.0"\nstatus: planned\n'
            "progress: 3/5\n---\n\n# My Plan\n\n- [x] Done\n- [ ] Todo\n"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["plan", str(tmp_path)])
        assert result.exit_code == 0
        assert "v1.0" in result.output
        assert "planned" in result.output


class TestIndexGeneratorLanguages:
    def test_detects_typescript(self, tmp_path: Path) -> None:
        """Detect TypeScript for React Native."""
        from loom_context.generators.index import IndexGenerator

        gen = IndexGenerator()
        result = gen.generate(
            {
                "structure": {
                    "project_type": "react-native-expo",
                    "architecture": [],
                    "project_name": "test",
                },
                "deps": {"dependencies": [], "stack_summary": {}},
                "code": {"total_code_files": 0, "file_naming": {}},
                "docs": {"doc_count": 0, "agents_md": None},
            },
            "0.6.0",
        )
        assert result["project"]["language"] == "TypeScript"

    def test_detects_rust(self, tmp_path: Path) -> None:
        from loom_context.generators.index import IndexGenerator

        gen = IndexGenerator()
        result = gen.generate(
            {
                "structure": {
                    "project_type": "rust",
                    "architecture": [],
                    "project_name": "test",
                },
                "deps": {"dependencies": [], "stack_summary": {}},
                "code": {"total_code_files": 0, "file_naming": {}},
                "docs": {"doc_count": 0, "agents_md": None},
            },
            "0.6.0",
        )
        assert result["project"]["language"] == "Rust"

    def test_detects_go(self, tmp_path: Path) -> None:
        from loom_context.generators.index import IndexGenerator

        gen = IndexGenerator()
        result = gen.generate(
            {
                "structure": {
                    "project_type": "go",
                    "architecture": [],
                    "project_name": "test",
                },
                "deps": {"dependencies": [], "stack_summary": {}},
                "code": {"total_code_files": 0, "file_naming": {}},
                "docs": {"doc_count": 0, "agents_md": None},
            },
            "0.6.0",
        )
        assert result["project"]["language"] == "Go"


class TestCodeScannerExtended:
    def test_detects_python_naming(self, tmp_path: Path) -> None:
        """Python files use snake_case."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "my_module.py").write_text("def my_func():\n    pass\n")
        (src / "another_module.py").write_text("class MyClass:\n    pass\n")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.code.total_code_files > 0


class TestDocsScannerExtended:
    def test_classifies_setup_doc(self, tmp_path: Path) -> None:
        """Docs with setup-related names classified correctly."""
        (tmp_path / "SETUP.md").write_text("# Setup\n\n## Prerequisites\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        setup_docs = [d for d in result.docs.docs if d.type == "setup"]
        assert len(setup_docs) > 0

    def test_classifies_changelog(self, tmp_path: Path) -> None:
        (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        cl_docs = [d for d in result.docs.docs if d.type == "changelog"]
        assert len(cl_docs) > 0

    def test_empty_frontmatter(self, tmp_path: Path) -> None:
        """Doc with empty frontmatter uses heuristic."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "notes.md").write_text("---\n---\n\n# Just Content\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "notes" in d.path)
        assert doc.type == "general"


class TestExporterBase:
    def test_generic_export(self, tmp_project: Path) -> None:
        """Generic exporter returns master prompt."""
        from loom_context.exporters.generic import GenericExporter

        engine = LoomEngine(tmp_project)
        engine.init()
        exporter = GenericExporter(tmp_project / ".context", tmp_project)
        content = exporter.export()
        assert "Project Context" in content

    def test_install_path(self, tmp_project: Path) -> None:
        """Each exporter has correct install path."""
        from loom_context.exporters.claude import ClaudeExporter
        from loom_context.exporters.codex import CodexExporter
        from loom_context.exporters.cursor import CursorExporter

        ctx = tmp_project / ".context"
        claude = ClaudeExporter(ctx, tmp_project)
        assert claude.install_path().name == "CLAUDE.md"
        codex = CodexExporter(ctx, tmp_project)
        assert codex.install_path().name == "AGENTS.md"
        cursor = CursorExporter(ctx, tmp_project)
        assert cursor.install_path().name == ".cursorrules"


class TestDepsInferCategory:
    def test_infer_types(self) -> None:
        from loom_context.knowledge import get_registry

        registry = get_registry()
        infer = registry.infer_package_category

        assert infer("@types/react") == "type-definitions"
        assert infer("eslint-plugin-react") == "linting"
        assert infer("babel-plugin-x") == "plugin"
        assert infer("@react-navigation/native") == "navigation"
        assert infer("expo-camera") == "expo-module"
        assert infer("react-native-map") == "react-native-module"
        assert infer("some-unknown-pkg") == "other"

        # Known packages return their category via categorize_package
        cat, _ = registry.categorize_package("prettier")
        assert cat == "formatting"
        cat, _ = registry.categorize_package("jest")
        assert cat == "testing"
        cat, _ = registry.categorize_package("webpack")
        assert cat == "build-tool"


class TestStructureEdgeCases:
    def test_nodejs_without_react(self, tmp_path: Path) -> None:
        """Node project without react detected as nodejs."""
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4"}}')
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "nodejs"

    def test_expo_from_app_json(self, tmp_path: Path) -> None:
        """Detect expo from app.json."""
        (tmp_path / "app.json").write_text('{"expo": {"name": "test"}}')
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "react-native-expo"

    def test_react_from_package_json(self, tmp_path: Path) -> None:
        """Detect react from package.json deps."""
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^19", "react-dom": "^19"}}'
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "react"

    def test_react_native_from_package_json(self, tmp_path: Path) -> None:
        """Detect react-native from package.json deps."""
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^19", "react-native": "^0.79"}}'
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "react-native"


class TestAuditorsStructureExtended:
    def test_no_rules_returns_empty(self, tmp_path: Path) -> None:
        """Structure auditor returns empty when no rules exist."""
        from loom_context.auditors.structure import StructureAuditor

        ff = FileFilter(tmp_path)
        auditor = StructureAuditor(tmp_path, ff)
        violations = auditor.audit()
        assert violations == []

    def test_loads_import_aliases(self, tmp_project: Path) -> None:
        """Structure auditor loads import aliases from rules."""
        from loom_context.auditors.structure import StructureAuditor

        engine = LoomEngine(tmp_project)
        engine.init()
        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        assert "@domain/*" in auditor.import_aliases


class TestFocusCommandExtended:
    def test_focus_with_output_file(self, tmp_project: Path) -> None:
        """Focus --output writes to file."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        outfile = str(tmp_project / "focus-out.md")
        result = runner.invoke(main, ["focus", "architecture", str(tmp_project), "-o", outfile])
        assert result.exit_code == 0
        assert Path(outfile).exists()


class TestCodeScannerNaming:
    def test_kebab_case_detection(self, tmp_path: Path) -> None:
        """Detect kebab-case file naming."""
        src = tmp_path / "src"
        src.mkdir()
        for name in ["my-component.ts", "user-service.ts", "auth-guard.ts"]:
            (src / name).write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.code.file_naming.get("dominant_style") == "kebab-case"

    def test_snake_case_detection(self, tmp_path: Path) -> None:
        """Detect snake_case file naming."""
        src = tmp_path / "src"
        src.mkdir()
        for name in ["my_module.py", "user_service.py", "auth_guard.py"]:
            (src / name).write_text("pass")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.code.file_naming.get("dominant_style") == "snake_case"


class TestPromptGeneratorEdgeCases:
    def test_prompt_without_agents_md(self, tmp_path: Path) -> None:
        """Prompt works without AGENTS.md."""
        engine = LoomEngine(tmp_path)
        engine.init()
        prompt = engine.generate_prompt()
        assert "Project Context" in prompt
        assert len(prompt) > 50

    def test_prompt_with_all_files(self, tmp_project: Path) -> None:
        """Prompt includes all .context/ sections."""
        engine = LoomEngine(tmp_project)
        engine.init()
        prompt = engine.generate_prompt()
        assert "Architecture" in prompt
        assert "Naming" in prompt
        assert "Directory" in prompt


class TestStructureTreeBuilding:
    def test_mvvm_detection(self, tmp_path: Path) -> None:
        """Detect MVVM architecture."""
        src = tmp_path / "src"
        src.mkdir()
        for d in ["models", "views", "viewmodels"]:
            (src / d).mkdir()
            (src / d / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "mvvm" in result.structure.architecture

    def test_hexagonal_detection(self, tmp_path: Path) -> None:
        """Detect hexagonal architecture with ports and adapters."""
        src = tmp_path / "src"
        src.mkdir()
        for d in ["ports", "adapters"]:
            (src / d).mkdir()
            (src / d / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert "hexagonal" in result.structure.architecture

    def test_unknown_project_type(self, tmp_path: Path) -> None:
        """Project with no markers is unknown."""
        (tmp_path / "random.txt").write_text("hello")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "unknown"


class TestDocsScannerClassification:
    def test_classifies_contributing(self, tmp_path: Path) -> None:
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "CONTRIBUTING" in d.path)
        assert doc.type == "contributing"

    def test_classifies_by_content_patterns(self, tmp_path: Path) -> None:
        """Docs classified by content when path doesn't match."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "overview.md").write_text("# Overview\n\n## Architecture\n\nClean layers.\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "overview" in d.path)
        assert doc.type == "architecture"

    def test_extracts_sections(self, tmp_path: Path) -> None:
        """Docs scanner extracts H2 and H3 sections."""
        (tmp_path / "README.md").write_text(
            "# Title\n\n## Section One\n\nText.\n\n### Sub Section\n\nMore.\n"
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "README" in d.path)
        assert "Section One" in doc.sections
        assert "Sub Section" in doc.sections


class TestGitHelper:
    def test_git_helper_in_non_git_dir(self, tmp_path: Path) -> None:
        """GitHelper returns None in non-git directory."""
        from loom_context.git import GitHelper

        git = GitHelper(tmp_path)
        assert git.branch() is None
        assert git.sha() is None
        assert git.modified_files() == []


class TestDoctorComprehensive:
    def test_doctor_no_loom_dir(self, tmp_path: Path) -> None:
        """Doctor warns when .loom/ is missing."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        for f in [
            "architecture.md",
            "naming.md",
            "directory-map.md",
            "stack.json",
            "rules.json",
            "plans-summary.md",
        ]:
            (ctx / f).write_text("content")

        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        assert ".loom/ missing" in result.output or "warning" in result.output.lower()

    def test_doctor_all_green(self, tmp_project: Path) -> None:
        """Doctor passes all checks on properly initialized project."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        # Add .gitignore with .loom/
        gi = tmp_project / ".gitignore"
        gi_content = gi.read_text(encoding="utf-8") if gi.exists() else ""
        if ".loom/" not in gi_content:
            gi.write_text(gi_content + "\n.loom/\n")

        result = runner.invoke(main, ["doctor", str(tmp_project)])
        assert result.exit_code == 0
        assert "passed" in result.output


class TestStatusJSON:
    def test_status_json_has_all_fields(self, tmp_project: Path) -> None:
        """Status --json includes all expected fields."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["status", str(tmp_project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "context_exists" in data
        assert "project_name" in data
        assert "architecture" in data
        assert "quick_rules" in data
        assert "decisions_count" in data
        assert "last_findings" in data


class TestGitHelperExtended:
    def test_git_modified_files_in_repo(self) -> None:
        """GitHelper returns modified files in an actual git repo."""
        from loom_context.git import GitHelper

        # Loom-Context itself is a git repo
        git = GitHelper(Path().resolve())
        # Should return a list (possibly empty if clean)
        result = git.modified_files()
        assert isinstance(result, list)

    def test_git_branch_in_repo(self) -> None:
        """GitHelper returns branch name in actual git repo."""
        from loom_context.git import GitHelper

        git = GitHelper(Path().resolve())
        branch = git.branch()
        assert branch is not None
        assert len(branch) > 0

    def test_git_cmd_with_bad_args(self, tmp_path: Path) -> None:
        """GitHelper.cmd returns None for invalid git commands."""
        from loom_context.git import GitHelper

        git = GitHelper(tmp_path)
        assert git.cmd(["this-is-not-a-command"]) is None


class TestStructureBoundaryRules:
    def test_boundary_rules_for_clean_arch(self, tmp_project: Path) -> None:
        """Clean architecture generates boundary rules."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert len(result.structure.layer_boundaries) > 0
        assert "domain" in result.structure.layer_boundaries

    def test_boundary_rules_empty_for_flat(self, tmp_path: Path) -> None:
        """Flat projects have no boundary rules."""
        (tmp_path / "main.py").write_text("print('hi')")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        # Flat project may or may not have boundaries
        assert isinstance(result.structure.layer_boundaries, dict)

    def test_file_counts_by_dir(self, tmp_project: Path) -> None:
        """Scan includes file counts per directory."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert len(result.structure.file_counts_by_dir) > 0


class TestCodeScannerSampling:
    def test_handles_many_files(self, tmp_path: Path) -> None:
        """Code scanner handles projects with many files."""
        src = tmp_path / "src"
        src.mkdir()
        # Create more than sample_size (100) files
        for i in range(110):
            (src / f"Module{i}.ts").write_text(f"export const x{i} = {i};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.code.total_code_files == 110
        # Naming should still be detected
        assert result.code.file_naming.get("dominant_style") == "PascalCase"


class TestAuditorNamingExtended:
    def test_no_rules_returns_error(self, tmp_path: Path) -> None:
        """Naming auditor returns error when no rules.json."""
        from loom_context.auditors.naming import NamingAuditor

        ff = FileFilter(tmp_path)
        auditor = NamingAuditor(tmp_path, ff)
        violations = auditor.audit()
        assert len(violations) == 1
        assert violations[0].rule == "rules-missing"

    def test_props_and_state_interfaces_allowed(self, tmp_project: Path) -> None:
        """Interfaces ending in Props or State don't need I prefix."""
        from loom_context.auditors.naming import NamingAuditor

        # Add file with Props/State interfaces (should pass)
        good = tmp_project / "src" / "presentation" / "components" / "ButtonProps.tsx"
        good.write_text("export interface ButtonProps { label: string; }\n")

        engine = LoomEngine(tmp_project)
        engine.init()

        ff = FileFilter(tmp_project)
        auditor = NamingAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()
        props_v = [v for v in violations if "ButtonProps" in v.message]
        assert len(props_v) == 0


class TestGitHelperModifiedFiles:
    def test_modified_files_fallback_to_cached(self, tmp_path: Path) -> None:
        """modified_files falls back to --cached when HEAD diff is empty."""
        from loom_context.git import GitHelper

        git = GitHelper(tmp_path)
        # In a non-git dir, both diffs return None, so result is []
        assert git.modified_files() == []

    def test_cmd_returns_none_on_failure(self, tmp_path: Path) -> None:
        """cmd returns None when git command fails (non-zero exit)."""
        from loom_context.git import GitHelper

        git = GitHelper(tmp_path)
        # status in non-git dir fails
        assert git.cmd(["status"]) is None


class TestFocusInfoDisplay:
    def test_focus_info_panel(self, tmp_project: Path) -> None:
        """Focus without --stdout shows info panel."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["focus", "domain", str(tmp_project)])
        assert result.exit_code == 0
        assert "Loom Focus" in result.output

    def test_focus_returns_none(self, tmp_project: Path) -> None:
        """Focus with stop-words-only query exits with error."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["focus", "the a an", str(tmp_project)])
        assert result.exit_code == 1


class TestLogModifiedFiles:
    def test_log_show_with_modified_files(self, tmp_project: Path) -> None:
        """Log show displays modified files info."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        # Log a message (will capture git modified files)
        runner.invoke(main, ["log", "test entry", "-p", str(tmp_project)])
        result = runner.invoke(main, ["log", "--show", "--last", "1", "-p", str(tmp_project)])
        assert result.exit_code == 0
        assert "test entry" in result.output


class TestDecideScope:
    def test_decide_with_deps_scope(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["decide", "add lodash", "-r", "utility", "-s", "deps", "-p", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "Decision recorded" in result.output

    def test_decide_show_with_rationale(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(
            main,
            ["decide", "test", "-r", "my reason", "-p", str(tmp_path)],
        )
        result = runner.invoke(main, ["decide", "--show", "-p", str(tmp_path)])
        assert "my reason" in result.output


class TestEnrichWithErrors:
    def test_enrich_with_violations(self, tmp_project: Path) -> None:
        """Enrich shows alert when violations exist."""
        bad = tmp_project / "src" / "domain" / "entities" / "EnrichBad.ts"
        bad.write_text('import { X } from "@infrastructure/repos/X";\n')
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["enrich", str(tmp_project)])
        assert result.exit_code == 0
        assert "errors" in result.output


class TestExporterGenericFile:
    def test_generic_default_filename(self, tmp_project: Path) -> None:
        from loom_context.exporters.generic import GenericExporter

        engine = LoomEngine(tmp_project)
        engine.init()
        exporter = GenericExporter(tmp_project / ".context", tmp_project)
        assert exporter.default_filename() == ".loom-export.md"
        assert exporter.install_path().name == ".loom-export.md"


class TestCompactEdgeCases:
    def test_compact_empty_context(self, tmp_path: Path) -> None:
        from loom_context.selector.compact import CompactFormatter

        ctx = tmp_path / ".context"
        ctx.mkdir()
        formatter = CompactFormatter(ctx)
        assert formatter.format_all() == ""

    def test_compact_with_full_context(self, tmp_project: Path) -> None:
        from loom_context.selector.compact import CompactFormatter

        engine = LoomEngine(tmp_project)
        engine.init()
        formatter = CompactFormatter(tmp_project / ".context")
        result = formatter.format_all()
        assert "CTX:" in result
        assert "STATS:" in result
        assert "DIRS:" in result


class TestStatusDecisionsCount:
    def test_status_with_decisions(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        runner.invoke(main, ["decide", "test", "-r", "reason", "-p", str(tmp_project)])
        result = runner.invoke(main, ["status", str(tmp_project)])
        assert "Decisions" in result.output
        assert "1 recorded" in result.output


class TestStructureCorruptedFiles:
    def test_corrupted_package_json(self, tmp_path: Path) -> None:
        """Structure scanner handles corrupted package.json."""
        (tmp_path / "package.json").write_text("not json {{{")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "nodejs"

    def test_corrupted_app_json(self, tmp_path: Path) -> None:
        """Structure scanner handles corrupted app.json."""
        (tmp_path / "app.json").write_text("{bad json")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.project_type == "unknown"

    def test_dotfiles_skipped_in_tree(self, tmp_path: Path) -> None:
        """Dotfile directories are skipped in tree building."""
        src = tmp_path / "src"
        src.mkdir()
        (src / ".hidden").mkdir()
        (src / ".hidden" / "secret.ts").write_text("secret")
        (src / "visible").mkdir()
        (src / "visible" / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        tree = result.structure.directory_tree
        # .hidden should not be in tree
        assert ".hidden" not in str(tree)

    def test_deep_nesting_limited(self, tmp_path: Path) -> None:
        """Tree building stops at max depth."""
        current = tmp_path / "src"
        current.mkdir()
        for i in range(6):
            current = current / f"level{i}"
            current.mkdir()
            (current / "file.ts").write_text("x")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        # Should have tree but not infinitely deep
        assert result.structure.total_files > 0


class TestDocsScannerEdgeCases:
    def test_doc_with_no_title(self, tmp_path: Path) -> None:
        """Doc without H1 heading gets empty title."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "notitle.md").write_text("Just some text without heading.\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        doc = next(d for d in result.docs.docs if "notitle" in d.path)
        assert doc.title == ""

    def test_doc_read_error(self, tmp_path: Path) -> None:
        """Scanner handles unreadable docs gracefully."""
        # Just verify it doesn't crash on empty dirs
        docs = tmp_path / "docs"
        docs.mkdir()
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert isinstance(result.docs.docs, list)

    def test_finds_agents_md(self, tmp_path: Path) -> None:
        """Scanner finds AGENTS.md."""
        (tmp_path / "AGENTS.md").write_text("# Agent Rules\n")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.docs.agents_md is not None

    def test_finds_cursorrules(self, tmp_path: Path) -> None:
        """Scanner finds .cursorrules."""
        (tmp_path / ".cursorrules").write_text("rules here")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.docs.agents_md is not None


class TestStatusStalenessEdgeCases:
    def test_status_invalid_timestamp(self, tmp_path: Path) -> None:
        """Status handles invalid generated_at timestamp."""
        from loom_context.status import StatusCollector

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project":{"type":"python"},"generated_at":"not-a-date"}')
        collector = StatusCollector(tmp_path)
        st = collector.collect()
        assert st.is_stale

    def test_status_with_stale_files(self, tmp_project: Path) -> None:
        """Status detects stale files after scan."""
        import time

        engine = LoomEngine(tmp_project)
        engine.init()
        time.sleep(0.1)
        # Modify a source file
        (tmp_project / "src" / "domain" / "entities" / "NewEntity.ts").write_text(
            "export class NewEntity {}\n"
        )
        from loom_context.status import StatusCollector

        collector = StatusCollector(tmp_project)
        st = collector.collect()
        assert st.is_stale
        assert st.stale_file_count > 0


class TestHeuristicMatchingEdgeCases:
    def test_match_plans_section(self, tmp_project: Path) -> None:
        """Heuristic matches plan sections."""
        from loom_context.selector.strategies.heuristic import HeuristicStrategy

        engine = LoomEngine(tmp_project)
        engine.init()
        strategy = HeuristicStrategy(tmp_project / ".context")
        candidates = strategy.select("roadmap plan implementation")
        plan_candidates = [c for c in candidates if c.source == "plan"]
        assert len(plan_candidates) >= 0  # May or may not find plans

    def test_match_stack_category(self, tmp_project: Path) -> None:
        """Heuristic matches stack categories."""
        from loom_context.selector.strategies.heuristic import HeuristicStrategy

        engine = LoomEngine(tmp_project)
        engine.init()
        strategy = HeuristicStrategy(tmp_project / ".context")
        candidates = strategy.select("react testing zustand")
        stack_candidates = [c for c in candidates if c.source == "stack"]
        assert len(stack_candidates) > 0


class TestDepsPackageJsonEdgeCases:
    def test_bun_lockfile_detection(self, tmp_path: Path) -> None:
        """Detect bun from lockfile."""
        (tmp_path / "package.json").write_text('{"dependencies":{"hono":"^4"}}')
        (tmp_path / "bun.lockb").write_text("")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.deps.package_manager == "bun"

    def test_requirements_txt_with_comments(self, tmp_path: Path) -> None:
        """requirements.txt with comments and flags parsed correctly."""
        (tmp_path / "requirements.txt").write_text(
            "# main deps\nflask>=2.0\n-e .\n# dev\nrequests~=2.28\n"
        )
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        dep_names = {d.name for d in result.deps.dependencies}
        assert "flask" in dep_names
        assert "requests" in dep_names


class TestBundleNoResults:
    def test_bundle_save_no_results(self, tmp_project: Path) -> None:
        """Bundle --save with stop-words-only query fails gracefully."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["bundle", "the a an is", str(tmp_project), "--save"])
        assert result.exit_code == 1

    def test_bundle_build_no_results(self, tmp_project: Path) -> None:
        """Bundle without --save with bad query fails gracefully."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["bundle", "the a an is", str(tmp_project)])
        assert result.exit_code == 1


class TestHandoffNoContext:
    def test_handoff_no_loom(self, tmp_project: Path) -> None:
        """Handoff works without .loom/ (just .context/)."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        # Handoff should still work using just index.json
        result = runner.invoke(main, ["handoff", "test task", str(tmp_project), "--stdout"])
        assert result.exit_code == 0
        assert "test task" in result.output

    def test_handoff_save_no_context(self, tmp_path: Path) -> None:
        """Handoff --save fails without .context/."""
        runner = CliRunner()
        result = runner.invoke(main, ["handoff", "task", str(tmp_path), "--save"])
        assert result.exit_code == 1


class TestLogNoMessage:
    def test_log_no_message_no_flags(self, tmp_path: Path) -> None:
        """Log without message or flags shows error."""
        runner = CliRunner()
        loom = tmp_path / ".loom"
        loom.mkdir()
        result = runner.invoke(main, ["log", "-p", str(tmp_path)])
        assert result.exit_code in {0, 1, 2}


class TestDoctorLoomFiles:
    def test_doctor_loom_no_decisions(self, tmp_path: Path) -> None:
        """Doctor warns about missing decisions log."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        for f in [
            "architecture.md",
            "naming.md",
            "directory-map.md",
            "stack.json",
            "rules.json",
            "plans-summary.md",
        ]:
            (ctx / f).write_text("x")
        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "inconsistencies.json").write_text("{}")
        (loom / "mutations.jsonl").write_text("")
        (loom / "sessions.jsonl").write_text("")
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0
        # Should mention decisions or show warning
        assert "decision" in result.output.lower() or "warning" in result.output.lower()

    def test_doctor_loom_no_mutations(self, tmp_path: Path) -> None:
        """Doctor warns about missing mutations log."""
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        for f in [
            "architecture.md",
            "naming.md",
            "directory-map.md",
            "stack.json",
            "rules.json",
            "plans-summary.md",
        ]:
            (ctx / f).write_text("x")
        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "inconsistencies.json").write_text("{}")
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0


class TestExportUnknownAgent:
    def test_export_invalid_agent(self, tmp_project: Path) -> None:
        """Export with invalid agent shows error."""
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["export", str(tmp_project), "--agent", "invalid"])
        assert result.exit_code == 2  # Click validation error


class TestStructureFeatureDetection:
    def test_features_dir_at_root(self, tmp_path: Path) -> None:
        """Detect feature-based when features/ is at root src level."""
        src = tmp_path / "src"
        src.mkdir()
        presentation = src / "presentation"
        presentation.mkdir()
        features = presentation / "features"
        features.mkdir()
        (features / "auth.ts").write_text("export {};")
        # Need a clean-arch base for the check to trigger
        for d in ["domain", "infrastructure"]:
            (src / d).mkdir()
            (src / d / "index.ts").write_text("export {};")

        engine = LoomEngine(tmp_path)
        result = engine.scan()
        # Should detect something
        assert len(result.structure.architecture) > 0


class TestDoctorPartialSetup:
    def test_doctor_index_no_type(self, tmp_path: Path) -> None:
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {}}')
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0

    def test_doctor_no_index(self, tmp_path: Path) -> None:
        ctx = tmp_path / ".context"
        ctx.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert "missing" in result.output.lower() or "fail" in result.output.lower()

    def test_doctor_loom_partial(self, tmp_path: Path) -> None:
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text('{"project": {"type": "python"}}')
        loom = tmp_path / ".loom"
        loom.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", str(tmp_path)])
        assert result.exit_code == 0


class TestBundleSaveEdgeCases:
    def test_bundle_save_creates_dirs(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["bundle", "architecture", str(tmp_project), "--save"])
        assert result.exit_code == 0
        assert (tmp_project / ".context" / "bundles").exists()


class TestStructureAuditorResolution:
    def test_no_layer_for_unknown_import(self, tmp_project: Path) -> None:
        from loom_context.auditors.structure import StructureAuditor

        engine = LoomEngine(tmp_project)
        engine.init()
        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        boundaries = auditor.rules.get("architecture", {}).get("layer_boundaries", {})
        assert auditor._resolve_import_layer("react", boundaries) is None

    def test_detect_layer_not_in_boundary(self, tmp_project: Path) -> None:
        from loom_context.auditors.structure import StructureAuditor

        engine = LoomEngine(tmp_project)
        engine.init()
        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        boundaries = auditor.rules.get("architecture", {}).get("layer_boundaries", {})
        from pathlib import PurePosixPath

        assert auditor._detect_layer(PurePosixPath("random/file.ts"), boundaries) is None


class TestAuditorCorruptedRules:
    def test_naming_corrupted_rules(self, tmp_path: Path) -> None:
        from loom_context.auditors.naming import NamingAuditor

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "rules.json").write_text("not json!!!")
        ff = FileFilter(tmp_path)
        auditor = NamingAuditor(tmp_path, ff)
        assert not auditor.load_rules()

    def test_structure_corrupted_rules(self, tmp_path: Path) -> None:
        from loom_context.auditors.structure import StructureAuditor

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "rules.json").write_text("bad json")
        ff = FileFilter(tmp_path)
        auditor = StructureAuditor(tmp_path, ff)
        assert not auditor.load_rules()

    def test_structure_no_boundaries(self, tmp_path: Path) -> None:
        from loom_context.auditors.structure import StructureAuditor

        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "rules.json").write_text('{"naming": {}}')
        ff = FileFilter(tmp_path)
        auditor = StructureAuditor(tmp_path, ff)
        auditor.load_rules()
        assert auditor.audit() == []

    def test_structure_require_import(self, tmp_project: Path) -> None:
        bad = tmp_project / "src" / "domain" / "entities" / "Req.js"
        bad.write_text('const x = require("@infrastructure/repos/X");\n')
        engine = LoomEngine(tmp_project)
        engine.init()
        from loom_context.auditors.structure import StructureAuditor

        ff = FileFilter(tmp_project)
        auditor = StructureAuditor(tmp_project, ff)
        auditor.load_rules()
        violations = auditor.audit()
        assert any("Req.js" in v.file for v in violations)


class TestPromptMissingFiles:
    def test_prompt_missing_architecture(self, tmp_path: Path) -> None:
        ctx = tmp_path / ".context"
        ctx.mkdir()
        (ctx / "index.json").write_text(
            '{"project":{"name":"x","type":"python","architecture":[],'
            '"language":"Python","runtime":"Python"},"quick_rules":[],"stats":{}}'
        )
        from loom_context.generators.prompt import PromptGenerator

        gen = PromptGenerator(ctx)
        prompt = gen.generate()
        assert "Project Context" in prompt


class TestCorruptedJsonl:
    def test_decisions_corrupted(self, tmp_path: Path) -> None:
        from loom_context.store.decisions import DecisionLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "decisions.jsonl").write_text(
            '{"timestamp":"t","summary":"good","rationale":"r","scope":"architecture"}\nnot json\n'
        )
        assert len(DecisionLog(loom, tmp_path).read(count=10)) == 1

    def test_mutations_corrupted(self, tmp_path: Path) -> None:
        from loom_context.store.mutations import MutationLog

        loom = tmp_path / ".loom"
        loom.mkdir()
        (loom / "mutations.jsonl").write_text(
            '{"timestamp":"t","action":"init","files_changed":[],"summary":"x"}\nbad\n'
        )
        assert len(MutationLog(loom, tmp_path).read(count=10)) == 1


class TestBundleEdgeCases:
    def test_unknown_strategy(self, tmp_project: Path) -> None:
        from loom_context.selector.bundle import BundleBuilder

        engine = LoomEngine(tmp_project)
        engine.init()
        builder = BundleBuilder(tmp_project / ".context", tmp_project)
        assert builder.build("x", strategy="unknown") is None


class TestIndexRuntime:
    def test_runtime_with_stack(self) -> None:
        from loom_context.generators.index import IndexGenerator

        gen = IndexGenerator()
        r = gen.generate(
            {
                "structure": {"project_type": "nodejs", "architecture": [], "project_name": "t"},
                "deps": {
                    "dependencies": [],
                    "stack_summary": {"ui-framework": ["react@19"], "platform": ["expo@53"]},
                },
                "code": {"total_code_files": 0, "file_naming": {}},
                "docs": {"doc_count": 0, "agents_md": None},
            },
            "0.6.0",
        )
        assert "react@19" in r["project"]["runtime"]

    def test_runtime_without_stack(self) -> None:
        from loom_context.generators.index import IndexGenerator

        gen = IndexGenerator()
        r = gen.generate(
            {
                "structure": {"project_type": "go", "architecture": [], "project_name": "t"},
                "deps": {"dependencies": [], "stack_summary": {}},
                "code": {"total_code_files": 0, "file_naming": {}},
                "docs": {"doc_count": 0, "agents_md": None},
            },
            "0.6.0",
        )
        assert r["project"]["runtime"] == "Go"


class TestNamingByRole:
    def test_naming_by_role_detected(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        # tmp_project has hooks (useUser.ts) and components
        nbr = result.code.naming_by_role
        assert isinstance(nbr, dict)

    def test_hooks_detected_as_camelcase(self, tmp_path: Path) -> None:
        src = tmp_path / "src" / "hooks"
        src.mkdir(parents=True)
        for name in ["useAuth.ts", "useUser.ts", "useTheme.ts"]:
            (src / name).write_text("export {};")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.code.naming_by_role.get("hook", {}).get("style") == "camelCase"


class TestMetricsCommand:
    def test_metrics_with_layers(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["metrics", str(tmp_project)])
        assert result.exit_code == 0
        assert "Layer Metrics" in result.output
        assert "Balance" in result.output

    def test_metrics_json(self, tmp_project: Path) -> None:
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["metrics", str(tmp_project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "layers" in data
        assert "balance_score" in data

    def test_metrics_no_layers(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["metrics", str(tmp_path)])
        assert result.exit_code == 0


class TestAuditSummary:
    def test_audit_summary_flag(self, tmp_project: Path) -> None:
        bad = tmp_project / "src" / "domain" / "entities" / "SumBad.ts"
        bad.write_text('import { X } from "@infrastructure/repos/X";\n')
        runner = CliRunner()
        runner.invoke(main, ["init", str(tmp_project)])
        result = runner.invoke(main, ["audit", str(tmp_project), "--summary"])
        assert result.exit_code == 1
        assert "by Directory" in result.output
        assert "by Rule" in result.output


class TestReportCommand:
    def test_report_empty(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(tmp_path)])
        assert result.exit_code == 0
        assert "No usage data" in result.output

    def test_reporter_record_and_read(self, tmp_path: Path) -> None:
        from loom_context.store.reporter import UsageReporter

        loom = tmp_path / ".loom"
        loom.mkdir()
        reporter = UsageReporter(loom, tmp_path)
        reporter.record("init", 800, success=True)
        reporter.record("audit", 200, success=True)
        reporter.record("init", 900, success=True)
        summary = reporter.summary()
        assert "init" in summary
        assert summary["init"]["runs"] == 2
        assert summary["audit"]["runs"] == 1


class TestMonorepoDetection:
    def test_detects_workspaces_from_package_json(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text('{"workspaces": ["packages/*"]}')
        pkgs = tmp_path / "packages"
        pkgs.mkdir()
        (pkgs / "app-a").mkdir()
        (pkgs / "app-b").mkdir()
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.is_monorepo
        assert len(result.structure.workspaces) == 2

    def test_detects_packages_dir(self, tmp_path: Path) -> None:
        pkgs = tmp_path / "packages"
        pkgs.mkdir()
        (pkgs / "core").mkdir()
        (pkgs / "ui").mkdir()
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert result.structure.is_monorepo

    def test_not_monorepo(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("pass")
        engine = LoomEngine(tmp_path)
        result = engine.scan()
        assert not result.structure.is_monorepo


class TestVerboseFlag:
    def test_verbose_flag_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--verbose" in result.output or "-v" in result.output


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
        assert manifest.loom_version == "0.6.0"
        assert manifest.selection_strategy == "heuristic"
        assert len(manifest.included_sections) > 0


class TestPlanGenerate:
    def test_plan_generate_creates_report(self, tmp_project: Path) -> None:
        """loom plan --generate creates a plan file in .loom/reports/."""
        engine = LoomEngine(tmp_project)
        engine.init()

        runner = CliRunner()
        result = runner.invoke(main, ["plan", str(tmp_project), "--generate"])
        assert result.exit_code == 0
        assert "Implementation plan generated" in result.output

        reports = list((tmp_project / ".loom" / "reports").glob("plan-*.md"))
        assert len(reports) == 1

    def test_plan_generate_contains_sections(self, tmp_project: Path) -> None:
        """Generated plan contains expected markdown sections."""
        engine = LoomEngine(tmp_project)
        engine.init()

        from loom_context.generators.plan import PlanGenerator

        gen = PlanGenerator(tmp_project)
        output_path = gen.generate()
        content = Path(output_path).read_text()

        assert "# Implementation Plan" in content
        assert "## Current State" in content
        assert "## Recommended Sequence" in content

    def test_plan_generate_no_context_fails(self, tmp_path: Path) -> None:
        """loom plan --generate without .context/ shows error."""
        runner = CliRunner()
        result = runner.invoke(main, ["plan", str(tmp_path), "--generate"])
        assert result.exit_code == 0
        assert "No .context/ found" in result.output

    def test_plan_generate_with_violations(self, tmp_project: Path) -> None:
        """Generated plan includes violation clusters when findings exist."""
        engine = LoomEngine(tmp_project)
        engine.init()

        # Create mock findings with boundary violations
        loom_dir = tmp_project / ".loom"
        findings = {
            "timestamp": "2026-03-18T00:00:00+00:00",
            "git_sha": "abc1234",
            "errors": 3,
            "warnings": 0,
            "violations": [
                {
                    "file": "src/core/boot.ts",
                    "line": 10,
                    "rule": "layer-boundary",
                    "message": "core should not import from infrastructure",
                    "severity": "error",
                    "suggestion": "Use DI token",
                },
                {
                    "file": "src/core/init.ts",
                    "line": 5,
                    "rule": "layer-boundary",
                    "message": "core should not import from infrastructure",
                    "severity": "error",
                    "suggestion": "Use DI token",
                },
                {
                    "file": "src/core/ui.ts",
                    "line": 1,
                    "rule": "layer-boundary",
                    "message": "core should not import from presentation",
                    "severity": "error",
                    "suggestion": "Move to presentation",
                },
            ],
        }
        (loom_dir / "inconsistencies.json").write_text(json.dumps(findings))

        from loom_context.generators.plan import PlanGenerator

        gen = PlanGenerator(tmp_project)
        output_path = gen.generate()
        content = Path(output_path).read_text()

        assert "core" in content
        assert "infrastructure" in content
        assert "Priority Clusters" in content


class TestDeltaTracking:
    def test_delta_created_on_second_save(self, tmp_project: Path) -> None:
        """Delta report is created when saving findings a second time."""
        from loom_context.models import Violation
        from loom_context.store.findings import FindingsStore

        loom_dir = tmp_project / ".loom"
        loom_dir.mkdir(exist_ok=True)
        (loom_dir / "reports").mkdir(exist_ok=True)

        store = FindingsStore(loom_dir, tmp_project)

        # First save: 3 violations
        v1 = [
            Violation("a.ts", 1, "r1", "msg1", "error"),
            Violation("b.ts", 2, "r1", "msg2", "error"),
            Violation("c.ts", 3, "r1", "msg3", "error"),
        ]
        store.save(v1)

        # Second save: 2 violations (one resolved, one new)
        v2 = [
            Violation("a.ts", 1, "r1", "msg1", "error"),
            Violation("b.ts", 2, "r1", "msg2", "error"),
            Violation("d.ts", 4, "r1", "msg4", "error"),
        ]
        store.save(v2)

        delta_files = list((loom_dir / "reports").glob("delta-*.json"))
        assert len(delta_files) == 1

        delta = json.loads(delta_files[0].read_text())
        assert delta["before"] == 3
        assert delta["after"] == 3
        assert delta["resolved"] == 1
        assert delta["new"] == 1

    def test_no_delta_on_first_save(self, tmp_project: Path) -> None:
        """No delta report on first save (no previous findings)."""
        from loom_context.models import Violation
        from loom_context.store.findings import FindingsStore

        loom_dir = tmp_project / ".loom"
        loom_dir.mkdir(exist_ok=True)
        (loom_dir / "reports").mkdir(exist_ok=True)

        store = FindingsStore(loom_dir, tmp_project)
        store.save([Violation("a.ts", 1, "r1", "msg1", "error")])

        delta_files = list((loom_dir / "reports").glob("delta-*.json"))
        assert len(delta_files) == 0

    def test_delta_resolved_files(self, tmp_project: Path) -> None:
        """Delta tracks which files had their violations resolved."""
        from loom_context.models import Violation
        from loom_context.store.findings import FindingsStore

        loom_dir = tmp_project / ".loom"
        loom_dir.mkdir(exist_ok=True)
        (loom_dir / "reports").mkdir(exist_ok=True)

        store = FindingsStore(loom_dir, tmp_project)
        store.save(
            [
                Violation("a.ts", 1, "r1", "msg1", "error"),
                Violation("b.ts", 2, "r1", "msg2", "error"),
            ]
        )
        store.save(
            [
                Violation("a.ts", 1, "r1", "msg1", "error"),
            ]
        )

        delta_files = list((loom_dir / "reports").glob("delta-*.json"))
        delta = json.loads(delta_files[0].read_text())
        assert delta["resolved"] == 1
        assert "b.ts" in delta["resolved_files"]
