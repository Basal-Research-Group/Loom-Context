"""Base domain adapter: defines which scanners and generators run per domain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loom_context.scanners.base import BaseScanner
from loom_context.security.filter import FileFilter


class DomainAdapter(ABC):
    """Base class for domain-specific scan/generate pipelines.

    Each adapter defines:
    - core_scanners: always run (structure, docs)
    - domain_scanners: domain-specific (deps, code, etc.)
    - post_generate: domain-specific .context/ files
    """

    name: str = "base"

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter

    @abstractmethod
    def get_scanners(self) -> list[BaseScanner]:
        """Return ordered list of scanners to run."""
        ...

    def post_generate(self, scan_result: dict[str, Any], context_dir: Path) -> list[str]:
        """Generate domain-specific .context/ files after core generation.

        Returns list of generated file names. Override in subclasses.
        """
        return []

    def _core_scanners(self) -> list[BaseScanner]:
        """Scanners that always run regardless of domain."""
        from loom_context.scanners.docs import DocsScanner
        from loom_context.scanners.structure import StructureScanner

        return [
            StructureScanner(self.root, self.file_filter),
            DocsScanner(self.root, self.file_filter),
        ]
