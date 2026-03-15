"""Loom Engine: central orchestrator that runs scanners and generators."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context import __version__
from loom_context.config import LoomConfig
from loom_context.generators.context import ContextGenerator
from loom_context.generators.index import IndexGenerator
from loom_context.generators.prompt import PromptGenerator
from loom_context.scanners.code import CodeScanner
from loom_context.scanners.deps import DependencyScanner
from loom_context.scanners.docs import DocsScanner
from loom_context.scanners.structure import StructureScanner
from loom_context.security.filter import FileFilter


class LoomEngine:
    """Central orchestrator for Loom-Context."""

    def __init__(self, root: str | Path) -> None:
        self.config = LoomConfig(root)
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
        generated = ctx_gen.generate_all(scan_result, index_data)

        return generated

    def generate_prompt(self) -> str:
        """Generate master AI prompt from existing .context/ files."""
        prompt_gen = PromptGenerator(self.config.context_dir)
        return prompt_gen.generate()

    def init(self) -> dict[str, Any]:
        """Full initialization: scan + generate context."""
        scan_result = self.scan()
        generated = self.generate_context(scan_result)

        return {
            "scan_result": scan_result,
            "generated_files": generated,
            "context_dir": str(self.config.context_dir),
        }
