"""Tests for ResolutionTrace store, GovernanceAuditor, and trace CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# TraceStore tests
# ---------------------------------------------------------------------------


class TestTraceStore:
    """Tests for the resolution trace store."""

    def test_record_creates_file(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        trace = store.record(query="fix bug", domain="code", agent="claude")
        assert (tmp_path / "traces.jsonl").exists()
        assert trace.task_id
        assert trace.query == "fix bug"
        assert trace.domain == "code"
        assert trace.agent == "claude"

    def test_record_fields(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        trace = store.record(
            query="implement feature",
            domain="code",
            agent="codex",
            selected_files=["a.py", "b.py"],
            changed_files=["a.py"],
            outcome="success",
            duration_ms=1500,
            tokens_used=3000,
            confidence=0.85,
            selection_strategy="heuristic",
            why_selected=["matched:auth"],
            fallback_used=False,
            validation_result="pass",
            notes="test trace",
        )
        assert trace.outcome == "success"
        assert trace.duration_ms == 1500
        assert trace.tokens_used == 3000
        assert trace.confidence == 0.85
        assert trace.why_selected == ["matched:auth"]
        assert trace.validation_result == "pass"

    def test_read_returns_newest_first(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        store.record(query="first", domain="code")
        store.record(query="second", domain="code")
        store.record(query="third", domain="code")

        traces = store.read(count=10)
        assert len(traces) == 3
        assert traces[0].query == "third"
        assert traces[2].query == "first"

    def test_read_respects_count(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        for i in range(10):
            store.record(query=f"task {i}", domain="code")

        traces = store.read(count=3)
        assert len(traces) == 3

    def test_read_empty_returns_empty(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        assert store.read() == []

    def test_stats_empty(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        stats = store.stats()
        assert stats["total"] == 0

    def test_stats_with_data(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        store.record(query="task1", domain="code", agent="claude", outcome="success", confidence=0.8)
        store.record(query="task2", domain="code", agent="codex", outcome="failed", confidence=0.3)
        store.record(query="task3", domain="brand", agent="claude", outcome="success", confidence=0.9)

        stats = store.stats()
        assert stats["total"] == 3
        assert stats["outcomes"]["success"] == 2
        assert stats["outcomes"]["failed"] == 1
        assert stats["agents"]["claude"] == 2
        assert stats["agents"]["codex"] == 1
        assert stats["avg_confidence"] > 0

    def test_to_dict_serializable(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        trace = store.record(query="test", domain="code")
        d = trace.to_dict()
        assert isinstance(d, dict)
        json.dumps(d)  # Must not raise

    def test_multiple_records_append(self, tmp_path: Path) -> None:
        from loom_context.store.traces import TraceStore

        store = TraceStore(tmp_path, tmp_path)
        store.record(query="a", domain="code")
        store.record(query="b", domain="brand")

        lines = (tmp_path / "traces.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# GovernanceAuditor tests
# ---------------------------------------------------------------------------


class TestGovernanceAuditor:
    """Tests for domain governance auditing."""

    def test_code_domain_returns_empty(self, tmp_path: Path) -> None:
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        violations = auditor.audit("code")
        assert violations == []

    def test_unknown_domain_returns_empty(self, tmp_path: Path) -> None:
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        assert auditor.audit("unknown") == []
        assert auditor.audit("mixed") == []

    def test_brand_governance_runs(self, tmp_path: Path) -> None:
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        (tmp_path / "tokens").mkdir()
        (tmp_path / "brand").mkdir()
        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        # Should not crash, may return empty if no violations found
        violations = auditor.audit("brand")
        assert isinstance(violations, list)

    def test_asset_naming_violation(self, tmp_path: Path) -> None:
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        icons = tmp_path / "icons"
        icons.mkdir()
        (icons / "MyIcon.svg").write_text("<svg/>")
        (icons / "good-icon.svg").write_text("<svg/>")

        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        violations = auditor.audit("brand")
        asset_violations = [v for v in violations if v.rule == "governance:asset_naming"]
        assert len(asset_violations) >= 1
        assert "MyIcon" in asset_violations[0].message

    def test_token_consistency_violation(self, tmp_path: Path) -> None:
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        tokens = tmp_path / "tokens"
        tokens.mkdir()
        (tokens / "colors.json").write_text('{"primary": "#ff6600"}')

        (tmp_path / "styles.css").write_text("body { color: #ff6600; }\n")

        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        violations = auditor.audit("brand")
        token_violations = [v for v in violations if v.rule == "governance:token_consistency"]
        assert len(token_violations) >= 1


# ---------------------------------------------------------------------------
# Engine integration with governance
# ---------------------------------------------------------------------------


class TestEngineGovernance:
    """Tests that engine audit includes governance violations."""

    def test_audit_includes_governance_for_brand(self, tmp_path: Path) -> None:
        """GovernanceAuditor runs directly for brand domain."""
        from loom_context.auditors.governance import GovernanceAuditor
        from loom_context.security.filter import FileFilter

        (tmp_path / ".gitignore").write_text("")
        (tmp_path / "brand").mkdir()
        (tmp_path / "tokens").mkdir()
        icons = tmp_path / "icons"
        icons.mkdir()
        (icons / "BadName.svg").write_text("<svg/>")

        auditor = GovernanceAuditor(tmp_path, FileFilter(tmp_path))
        violations = auditor.audit("brand")
        governance = [v for v in violations if v.rule.startswith("governance:")]
        assert len(governance) >= 1

    def test_audit_no_governance_for_code(self, tmp_project: Path) -> None:
        from loom_context.engine import LoomEngine

        engine = LoomEngine(tmp_project)
        engine.scan(force=True)
        violations = engine.audit()
        governance = [v for v in violations if v.rule.startswith("governance:")]
        assert governance == []


# ---------------------------------------------------------------------------
# Trace CLI tests
# ---------------------------------------------------------------------------


class TestTraceCLI:
    """Tests for the loom trace CLI commands."""

    def test_trace_help(self) -> None:
        from click.testing import CliRunner

        from loom_context.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["trace", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "record" in result.output
        assert "stats" in result.output

    def test_trace_record_and_list(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from loom_context.cli import main

        runner = CliRunner()

        # Record
        result = runner.invoke(main, [
            "trace", "record", "test task", str(tmp_path),
            "--agent", "claude", "--outcome", "success",
        ])
        assert result.exit_code == 0
        assert "Trace recorded" in result.output

        # List
        result = runner.invoke(main, ["trace", "list", str(tmp_path)])
        assert result.exit_code == 0
        assert "test task" in result.output

    def test_trace_stats_empty(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from loom_context.cli import main

        (tmp_path / ".loom").mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["trace", "stats", str(tmp_path)])
        assert result.exit_code == 0
        assert "No traces" in result.output

    def test_trace_list_json(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from loom_context.cli import main

        runner = CliRunner()
        runner.invoke(main, ["trace", "record", "task1", str(tmp_path), "--agent", "claude"])
        result = runner.invoke(main, ["trace", "list", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
