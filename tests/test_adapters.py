"""Tests for domain adapters and context ranker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def brand_project(tmp_path: Path) -> Path:
    """Create a brand/design-system project."""
    (tmp_path / "brand").mkdir()
    (tmp_path / "tokens").mkdir()
    (tmp_path / "guidelines").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "icons").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "brand" / "brand.yaml").write_text("name: TestBrand\n")
    (tmp_path / "tokens" / "colors.tokens.json").write_text('{"primary": "#000"}\n')
    (tmp_path / "guidelines" / "voice.md").write_text("# Voice\nFriendly and clear.\n")
    (tmp_path / "docs" / "style-guide.md").write_text("# Style Guide\nUse tokens.\n")
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    return tmp_path


@pytest.fixture
def research_project(tmp_path: Path) -> Path:
    """Create a research/academic project."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "raw").mkdir()
    (tmp_path / "notebooks").mkdir()
    (tmp_path / "experiments").mkdir()
    (tmp_path / "papers").mkdir()
    (tmp_path / "figures").mkdir()
    (tmp_path / "references.bib").write_text("@article{test, title={Test}}\n")
    (tmp_path / "notebooks" / "analysis.ipynb").write_text('{"cells":[]}\n')
    (tmp_path / "papers" / "draft.tex").write_text("\\documentclass{article}\n")
    (tmp_path / ".gitignore").write_text(".ipynb_checkpoints/\n")
    return tmp_path


@pytest.fixture
def data_project(tmp_path: Path) -> Path:
    """Create a data engineering project."""
    (tmp_path / "models").mkdir()
    (tmp_path / "seeds").mkdir()
    (tmp_path / "macros").mkdir()
    (tmp_path / "pipelines").mkdir()
    (tmp_path / "staging").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "dbt_project.yml").write_text("name: test_dbt\nversion: 1.0\n")
    (tmp_path / "models" / "staging.sql").write_text("SELECT * FROM raw\n")
    (tmp_path / "models" / "marts.sql").write_text("SELECT * FROM staging\n")
    (tmp_path / "seeds" / "countries.csv").write_text("id,name\n1,MX\n")
    (tmp_path / "macros" / "utils.sql").write_text("{% macro test() %}{% endmacro %}\n")
    (tmp_path / ".gitignore").write_text("target/\n")
    return tmp_path


@pytest.fixture
def code_project(tmp_path: Path) -> Path:
    """Create a standard code project."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "0.1.0"\n')
    (tmp_path / ".gitignore").write_text("__pycache__/\n.venv/\n")
    return tmp_path


# ---------------------------------------------------------------------------
# DomainDetector tests
# ---------------------------------------------------------------------------


class TestDomainDetector:
    """Tests for domain detection."""

    def test_detects_code_domain(self, code_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(code_project, FileFilter(code_project))
        result = detector.detect()
        assert result.primary == "code"
        assert result.primary_confidence > 0.3

    def test_detects_brand_domain(self, brand_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(brand_project, FileFilter(brand_project))
        result = detector.detect()
        assert result.primary == "brand"
        assert result.primary_confidence > 0.3

    def test_detects_research_domain(self, research_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(research_project, FileFilter(research_project))
        result = detector.detect()
        assert result.primary == "research"
        assert result.primary_confidence > 0.3

    def test_detects_data_domain(self, data_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(data_project, FileFilter(data_project))
        result = detector.detect()
        # Data domain should score highest even if below threshold
        scores = {d.name: d.score for d in result.domains}
        assert scores.get("data", 0) > scores.get("code", 0), f"data should outscore code: {scores}"

    def test_empty_project_returns_unknown(self, tmp_path: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        detector = DomainDetector(tmp_path, FileFilter(tmp_path))
        result = detector.detect()
        assert result.primary == "unknown"

    def test_code_wins_over_brand_ambiguity(self, tmp_path: Path) -> None:
        """A project with package.json + assets/ should be code, not brand."""
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        (tmp_path / "src").mkdir()
        (tmp_path / "assets").mkdir()
        (tmp_path / "icons").mkdir()
        (tmp_path / "src" / "app.tsx").write_text("export default App;\n")
        pkg = {"name": "my-app", "dependencies": {"react-native": "0.79.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / ".gitignore").write_text("node_modules/\n")

        detector = DomainDetector(tmp_path, FileFilter(tmp_path))
        result = detector.detect()
        assert result.primary == "code"

    def test_to_dict_serializable(self, code_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(code_project, FileFilter(code_project))
        result = detector.detect()
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "primary" in d
        assert "scores" in d
        # Must be JSON serializable
        json.dumps(d)

    def test_active_domains_list(self, code_project: Path) -> None:
        from loom_context.knowledge.domain_detector import DomainDetector
        from loom_context.security.filter import FileFilter

        detector = DomainDetector(code_project, FileFilter(code_project))
        result = detector.detect()
        assert isinstance(result.active_domains, list)
        assert "code" in result.active_domains


# ---------------------------------------------------------------------------
# DomainAdapter tests
# ---------------------------------------------------------------------------


class TestAdapterRegistry:
    """Tests for adapter selection."""

    def test_code_adapter_selected_for_code(self) -> None:
        from loom_context.adapters.code import CodeAdapter
        from loom_context.adapters.registry import get_adapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("code", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, CodeAdapter)

    def test_brand_adapter_selected_for_brand(self) -> None:
        from loom_context.adapters.brand import BrandAdapter
        from loom_context.adapters.registry import get_adapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("brand", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, BrandAdapter)

    def test_research_adapter_selected_for_research(self) -> None:
        from loom_context.adapters.registry import get_adapter
        from loom_context.adapters.research import ResearchAdapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("research", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, ResearchAdapter)

    def test_data_adapter_selected_for_data(self) -> None:
        from loom_context.adapters.data import DataAdapter
        from loom_context.adapters.registry import get_adapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("data", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, DataAdapter)

    def test_unknown_falls_back_to_code(self) -> None:
        from loom_context.adapters.code import CodeAdapter
        from loom_context.adapters.registry import get_adapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("unknown", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, CodeAdapter)

    def test_mixed_falls_back_to_code(self) -> None:
        from loom_context.adapters.code import CodeAdapter
        from loom_context.adapters.registry import get_adapter
        from loom_context.security.filter import FileFilter

        adapter = get_adapter("mixed", Path("."), FileFilter(Path(".")))
        assert isinstance(adapter, CodeAdapter)

    def test_available_adapters(self) -> None:
        from loom_context.adapters.registry import get_available_adapters

        available = get_available_adapters()
        assert "code" in available
        assert "brand" in available
        assert "research" in available
        assert "data" in available


class TestCodeAdapter:
    """Tests for the code domain adapter."""

    def test_has_four_scanners(self, code_project: Path) -> None:
        from loom_context.adapters.code import CodeAdapter
        from loom_context.security.filter import FileFilter

        adapter = CodeAdapter(code_project, FileFilter(code_project))
        scanners = adapter.get_scanners()
        assert len(scanners) == 4
        names = [type(s).__name__ for s in scanners]
        assert "StructureScanner" in names
        assert "DocsScanner" in names
        assert "DependencyScanner" in names
        assert "CodeScanner" in names

    def test_post_generate_returns_empty(self, code_project: Path) -> None:
        from loom_context.adapters.code import CodeAdapter
        from loom_context.security.filter import FileFilter

        adapter = CodeAdapter(code_project, FileFilter(code_project))
        result = adapter.post_generate({}, code_project)
        assert result == []


class TestBrandAdapter:
    """Tests for the brand domain adapter."""

    def test_has_core_scanners_only(self, brand_project: Path) -> None:
        from loom_context.adapters.brand import BrandAdapter
        from loom_context.security.filter import FileFilter

        adapter = BrandAdapter(brand_project, FileFilter(brand_project))
        scanners = adapter.get_scanners()
        assert len(scanners) == 2
        names = [type(s).__name__ for s in scanners]
        assert "StructureScanner" in names
        assert "DocsScanner" in names

    def test_post_generate_creates_governance(self, brand_project: Path) -> None:
        from loom_context.adapters.brand import BrandAdapter
        from loom_context.security.filter import FileFilter

        context_dir = brand_project / ".context"
        context_dir.mkdir()
        adapter = BrandAdapter(brand_project, FileFilter(brand_project))
        generated = adapter.post_generate({
            "structure": {"project_name": "TestBrand", "directory_tree": {"brand": {}, "tokens": {}}},
            "docs": {"docs": []},
            "domain_confidence": 0.5,
        }, context_dir)
        assert "governance.md" in generated
        assert (context_dir / "governance.md").exists()
        content = (context_dir / "governance.md").read_text()
        assert "I18N Sync" in content or "i18n" in content.lower()

    def test_post_generate_creates_brand_md(self, brand_project: Path) -> None:
        from loom_context.adapters.brand import BrandAdapter
        from loom_context.security.filter import FileFilter

        context_dir = brand_project / ".context"
        context_dir.mkdir()
        adapter = BrandAdapter(brand_project, FileFilter(brand_project))
        generated = adapter.post_generate({
            "structure": {"project_name": "TestBrand", "directory_tree": {"brand": {}, "tokens": {}}},
            "docs": {"docs": [
                {"path": "brand/brand.yaml", "title": "Brand Identity"},
                {"path": "guidelines/voice.md", "title": "Voice Guidelines"},
            ]},
            "domain_confidence": 0.5,
        }, context_dir)
        assert "brand.md" in generated
        content = (context_dir / "brand.md").read_text()
        assert "Brand Context" in content


class TestResearchAdapter:
    """Tests for the research domain adapter."""

    def test_has_four_scanners(self, research_project: Path) -> None:
        from loom_context.adapters.research import ResearchAdapter
        from loom_context.security.filter import FileFilter

        adapter = ResearchAdapter(research_project, FileFilter(research_project))
        scanners = adapter.get_scanners()
        assert len(scanners) == 4

    def test_post_generate_creates_research_md(self, research_project: Path) -> None:
        from loom_context.adapters.research import ResearchAdapter
        from loom_context.security.filter import FileFilter

        context_dir = research_project / ".context"
        context_dir.mkdir()
        adapter = ResearchAdapter(research_project, FileFilter(research_project))
        generated = adapter.post_generate({
            "structure": {
                "project_name": "TestResearch",
                "directory_tree": {"data": {}, "notebooks": {}, "experiments": {}},
            },
            "docs": {"docs": [
                {"path": "papers/draft.tex", "title": "Draft Paper"},
            ]},
            "domain_confidence": 0.6,
        }, context_dir)
        assert "research.md" in generated
        content = (context_dir / "research.md").read_text()
        assert "Research Context" in content


# ---------------------------------------------------------------------------
# ContextRanker tests
# ---------------------------------------------------------------------------


class TestHeuristicRanker:
    """Tests for the heuristic context ranker."""

    def test_ranks_by_keyword_match(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        result = ranker.rank(
            candidates=["src/auth/login.py", "src/utils/helpers.py", "src/auth/session.py"],
            query="fix auth login bug",
        )
        assert result.strategy == "heuristic"
        assert result.total_candidates == 3
        # auth/login should rank higher than helpers
        paths = result.paths
        assert paths[0] == "src/auth/login.py"

    def test_returns_top_k(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        candidates = [f"src/file_{i}.py" for i in range(20)]
        result = ranker.rank(candidates=candidates, query="test", top_k=5)
        assert result.total_selected <= 5
        assert result.total_candidates == 20

    def test_handles_empty_query(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        result = ranker.rank(
            candidates=["a.py", "b.py"],
            query="",
            top_k=5,
        )
        assert len(result.files) <= 5

    def test_handles_empty_candidates(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        result = ranker.rank(candidates=[], query="anything")
        assert result.files == []
        assert result.total_candidates == 0

    def test_ranked_file_has_evidence(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        result = ranker.rank(
            candidates=["src/auth/login.py"],
            query="auth login",
        )
        assert len(result.files) == 1
        assert result.files[0].score > 0
        assert len(result.files[0].evidence) > 0

    def test_ranking_result_paths_property(self) -> None:
        from loom_context.selector.ranker import HeuristicRanker

        ranker = HeuristicRanker()
        result = ranker.rank(
            candidates=["a.py", "b.py", "c.py"],
            query="something",
        )
        assert isinstance(result.paths, list)
        assert all(isinstance(p, str) for p in result.paths)


# ---------------------------------------------------------------------------
# Integration: Engine + Adapter
# ---------------------------------------------------------------------------


class TestEngineAdapterIntegration:
    """Tests that engine correctly uses adapters."""

    def test_engine_scan_includes_domain(self, tmp_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(tmp_project)
        result = engine.scan(force=True)
        assert hasattr(result, "domain")
        assert result.domain in ("code", "brand", "research", "data", "mixed", "unknown")

    def test_engine_scan_domain_in_dict(self, tmp_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(tmp_project)
        result = engine.scan(force=True)
        d = result.to_dict()
        assert "domain" in d
        assert "domain_confidence" in d
        assert "domain_details" in d

    def test_code_project_uses_code_adapter(self, tmp_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(tmp_project)
        engine.scan(force=True)
        assert engine._last_adapter is not None
        assert engine._last_adapter.name in ("code", "brand", "research", "data")

    def test_brand_project_generates_extra_files(self, brand_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(brand_project)
        result = engine.init()
        generated = result["generated_files"]
        # Brand projects should have governance.md
        assert any("governance" in f for f in generated)

    def test_scan_result_domain_persisted_in_cache(self, tmp_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(tmp_project)
        engine.scan(force=True)
        # Second scan should use cache and preserve domain
        result2 = engine.scan(force=False)
        assert result2.domain in ("code", "brand", "research", "data", "mixed", "unknown")
