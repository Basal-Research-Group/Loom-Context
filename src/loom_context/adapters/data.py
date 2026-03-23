"""Data domain adapter: for data engineering, pipelines, and ML projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loom_context.adapters.base import DomainAdapter
from loom_context.scanners.base import BaseScanner


class DataAdapter(DomainAdapter):
    """Adapter for data/ML projects. Core + deps + code scanners."""

    name = "data"

    def get_scanners(self) -> list[BaseScanner]:
        from loom_context.scanners.code import CodeScanner
        from loom_context.scanners.deps import DependencyScanner

        return [
            *self._core_scanners(),
            DependencyScanner(self.root, self.file_filter),
            CodeScanner(self.root, self.file_filter),
        ]

    def post_generate(self, scan_result: dict[str, Any], context_dir: Path) -> list[str]:
        """Generate data-specific .context/ files."""
        generated: list[str] = []

        content = self._generate_data_md(scan_result)
        if content:
            (context_dir / "data-pipelines.md").write_text(content, encoding="utf-8")
            generated.append("data-pipelines.md")

        return generated

    def _generate_data_md(self, scan_result: dict[str, Any]) -> str:
        """Generate data-pipelines.md summarizing data project structure."""
        structure = scan_result.get("structure", {})

        lines = ["# Data Pipeline Context", ""]
        lines.append(f"Project: {structure.get('project_name', 'unknown')}")
        lines.append(f"Domain: data (confidence: {scan_result.get('domain_confidence', 0):.2f})")
        lines.append("")

        tree = structure.get("directory_tree", {})
        data_keywords = {
            "models", "sources", "seeds", "snapshots", "macros",
            "pipelines", "dags", "operators", "warehouses", "staging",
            "marts", "raw", "transformations", "ingestion", "features",
        }
        data_dirs = [d for d in tree if d.lower() in data_keywords]
        if data_dirs:
            lines.append("## Data Directories")
            lines.append("")
            for d in sorted(data_dirs):
                lines.append(f"- `{d}/`")
            lines.append("")

        return "\n".join(lines) if len(lines) > 4 else ""
