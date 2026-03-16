"""Loom Engine: central orchestrator that runs scanners and generators."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context import __version__
from loom_context.auditors.naming import NamingAuditor, Violation
from loom_context.auditors.structure import StructureAuditor
from loom_context.config import LoomConfig
from loom_context.findings import FindingsStore
from loom_context.generators.context import ContextGenerator
from loom_context.generators.index import IndexGenerator
from loom_context.generators.prompt import PromptGenerator
from loom_context.mutations import MutationLog
from loom_context.scanners.code import CodeScanner
from loom_context.scanners.deps import DependencyScanner
from loom_context.scanners.docs import DocsScanner
from loom_context.scanners.structure import StructureScanner
from loom_context.security.filter import FileFilter
from loom_context.session import SessionLogger


class LoomEngine:
    """Central orchestrator for Loom-Context."""

    def __init__(self, root: str | Path) -> None:
        self.config = LoomConfig(Path(root))
        self.file_filter = FileFilter(self.config.root)

    def scan(self) -> dict[str, Any]:
        """Run all scanners and return merged results."""
        structure_scanner = StructureScanner(self.config.root, self.file_filter)
        deps_scanner = DependencyScanner(self.config.root, self.file_filter)
        code_scanner = CodeScanner(self.config.root, self.file_filter)
        docs_scanner = DocsScanner(self.config.root, self.file_filter)

        result: dict[str, Any] = {
            "structure": structure_scanner.scan(),
            "deps": deps_scanner.scan(),
            "code": code_scanner.scan(),
            "docs": docs_scanner.scan(),
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add project name from root dir
        result["structure"]["project_name"] = self.config.root.name

        return result

    def generate_context(self, scan_result: Optional[dict[str, Any]] = None) -> list[str]:
        """Generate all .context/ files from scan results."""
        if scan_result is None:
            scan_result = self.scan()

        self.config.ensure_context_dir()

        # Generate index
        index_gen = IndexGenerator()
        index_data = index_gen.generate(scan_result, __version__)
        index_data["generated_at"] = datetime.now(timezone.utc).isoformat()

        # Generate all context files
        ctx_gen = ContextGenerator(self.config.context_dir)
        return ctx_gen.generate_all(scan_result, index_data)

    def generate_prompt(self) -> str:
        """Generate master AI prompt from existing .context/ files."""
        prompt_gen = PromptGenerator(self.config.context_dir)
        return prompt_gen.generate()

    def audit(self) -> list[Violation]:
        """Run all auditors and return violations."""
        file_filter = FileFilter(self.config.root)

        naming = NamingAuditor(self.config.root, file_filter)
        naming.load_rules()
        naming_v = naming.audit()

        structure = StructureAuditor(self.config.root, file_filter)
        structure.load_rules()
        structure_v = structure.audit()

        return naming_v + structure_v

    def enrich(self) -> dict[str, Any]:
        """Deterministic enrichment: audit + refine rules + persist."""
        # 1. Run audit
        violations = self.audit()

        # 2. Persist findings
        self.config.ensure_loom_dir()
        findings_store = FindingsStore(self.config.loom_dir, self.config.root)
        findings = findings_store.save(violations)

        # 3. Re-scan and regenerate context
        scan_result = self.scan()
        generated = self.generate_context(scan_result)

        # 4. Record mutation
        mutation_log = MutationLog(self.config.loom_dir, self.config.root)
        mutation_log.record(
            "enrich",
            generated,
            f"enriched after {findings.errors} errors, {findings.warnings} warnings",
        )

        return {
            "generated_files": generated,
            "audit": {"errors": findings.errors, "warnings": findings.warnings},
        }

    def init(self) -> dict[str, Any]:
        """Full initialization: scan + generate + audit + persist."""
        scan_result = self.scan()
        generated = self.generate_context(scan_result)

        # Ensure .loom/ exists
        self.config.ensure_loom_dir()

        # Migrate sessions from .context/ to .loom/ if needed
        self._migrate_sessions()

        # Non-blocking audit
        audit_result = self._safe_audit()

        # Persist findings
        findings_store = FindingsStore(self.config.loom_dir, self.config.root)
        findings = findings_store.save(audit_result)

        # Record mutation
        mutation_log = MutationLog(self.config.loom_dir, self.config.root)
        mutation_log.record("init", generated, f"initialized with {len(generated)} files")

        return {
            "scan_result": scan_result,
            "generated_files": generated,
            "context_dir": str(self.config.context_dir),
            "audit": {"errors": findings.errors, "warnings": findings.warnings},
        }

    def _safe_audit(self) -> list[Violation]:
        """Run audit without failing on errors."""
        try:
            return self.audit()
        except Exception:
            return []

    def _migrate_sessions(self) -> None:
        """Migrate sessions.jsonl from .context/ to .loom/ if it exists."""
        logger = SessionLogger(self.config.loom_dir, self.config.root)
        logger.migrate_from_context(self.config.context_dir)
