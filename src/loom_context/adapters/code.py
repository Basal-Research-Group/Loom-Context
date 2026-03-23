"""Code domain adapter: the default pipeline for software projects."""

from __future__ import annotations

from loom_context.adapters.base import DomainAdapter
from loom_context.scanners.base import BaseScanner


class CodeAdapter(DomainAdapter):
    """Adapter for code/software projects. Runs all 4 original scanners."""

    name = "code"

    def get_scanners(self) -> list[BaseScanner]:
        from loom_context.scanners.code import CodeScanner
        from loom_context.scanners.deps import DependencyScanner

        return [
            *self._core_scanners(),
            DependencyScanner(self.root, self.file_filter),
            CodeScanner(self.root, self.file_filter),
        ]
