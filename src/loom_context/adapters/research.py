"""Research domain adapter: for academic, thesis, and experiment projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loom_context.adapters.base import DomainAdapter
from loom_context.scanners.base import BaseScanner


class ResearchAdapter(DomainAdapter):
    """Adapter for research/academic projects. Core scanners + research-specific output."""

    name = "research"

    def get_scanners(self) -> list[BaseScanner]:
        # Research projects may have code (Python, R, Julia)
        from loom_context.scanners.code import CodeScanner
        from loom_context.scanners.deps import DependencyScanner

        return [
            *self._core_scanners(),
            DependencyScanner(self.root, self.file_filter),
            CodeScanner(self.root, self.file_filter),
        ]

    def post_generate(self, scan_result: dict[str, Any], context_dir: Path) -> list[str]:
        """Generate research-specific .context/ files."""
        generated: list[str] = []

        content = self._generate_research_md(scan_result)
        if content:
            (context_dir / "research.md").write_text(content, encoding="utf-8")
            generated.append("research.md")

        return generated

    def _generate_research_md(self, scan_result: dict[str, Any]) -> str:
        """Generate research.md summarizing research project structure."""
        structure = scan_result.get("structure", {})
        docs = scan_result.get("docs", {})

        lines = ["# Research Context", ""]
        lines.append(f"Project: {structure.get('project_name', 'unknown')}")
        lines.append(f"Domain: research (confidence: {scan_result.get('domain_confidence', 0):.2f})")
        lines.append("")

        # Research directories
        tree = structure.get("directory_tree", {})
        research_keywords = {
            "data", "raw", "processed", "notebooks", "experiments",
            "papers", "thesis", "chapters", "figures", "results", "models",
        }
        research_dirs = [d for d in tree if d.lower() in research_keywords]
        if research_dirs:
            lines.append("## Research Directories")
            lines.append("")
            for d in sorted(research_dirs):
                lines.append(f"- `{d}/`")
            lines.append("")

        # Research documents
        doc_list = docs.get("docs", [])
        research_docs = [d for d in doc_list if any(
            kw in d.get("path", "").lower()
            for kw in ("paper", "thesis", "experiment", "hypothesis", "method", "result", "abstract")
        )]
        if research_docs:
            lines.append("## Research Documents")
            lines.append("")
            for d in research_docs[:10]:
                lines.append(f"- `{d['path']}` — {d.get('title', 'untitled')}")
            if len(research_docs) > 10:
                lines.append(f"- ... +{len(research_docs) - 10} more")
            lines.append("")

        return "\n".join(lines) if len(lines) > 4 else ""
