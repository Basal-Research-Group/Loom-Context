"""Documentation scanner: indexes existing markdown and doc files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from loom_context.knowledge import get_registry
from loom_context.scanners.base import BaseScanner

_registry = get_registry()

# Doc classification rules from Knowledge Registry
DOC_TYPE_RULES: list[tuple[str, str]] = [
    (r.pattern, r.doc_type) for r in _registry.get_doc_filename_rules()
]

PATH_TYPE_RULES: list[tuple[str, str]] = [
    (r.pattern, r.doc_type) for r in _registry.get_doc_path_rules()
]

# Status markers in docs
STATUS_PATTERNS = [
    re.compile(r"[-*]\s*\[x\]\s*(.+)", re.IGNORECASE),
    re.compile(r"[-*]\s*\[\s*\]\s*(.+)", re.IGNORECASE),
    re.compile(r"\|\s*(.+?)\s*\|\s*(done|complete|completado|hecho|✅)\s*\|", re.IGNORECASE),
    re.compile(r"\|\s*(.+?)\s*\|\s*(pending|pendiente|todo|⏳)\s*\|", re.IGNORECASE),
    re.compile(r"\|\s*(.+?)\s*\|\s*(partial|parcial|in.?progress|🔄)\s*\|", re.IGNORECASE),
    re.compile(r"\b(CRITICA|ALTA|MEDIA|BAJA)\b", re.IGNORECASE),
]


class DocsScanner(BaseScanner):
    """Scans and indexes documentation files."""

    def scan(self) -> dict[str, Any]:
        docs = self._find_docs()
        indexed = [self._index_doc(doc) for doc in docs]
        agents_md = self._find_agents_md()

        return {
            "docs": indexed,
            "agents_md": str(agents_md.relative_to(self.root)) if agents_md else None,
            "doc_count": len(indexed),
            "by_type": self._group_by_type(indexed),
        }

    def _find_docs(self) -> list[Path]:
        """Find all documentation files."""
        docs: list[Path] = []

        # Root-level docs
        for f in self.root.iterdir():
            if (
                f.is_file()
                and f.suffix.lower() in {".md", ".mdx", ".rst", ".txt"}
                and f.name.lower() not in {"license", "license.md"}
            ):
                docs.append(f)

        # docs/ directory
        docs_dir = self.root / "docs"
        if docs_dir.is_dir():
            for f in docs_dir.rglob("*.md"):
                docs.append(f)
            for f in docs_dir.rglob("*.mdx"):
                docs.append(f)

        return sorted(docs)

    def _index_doc(self, path: Path) -> dict[str, Any]:
        """Index a single documentation file."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""

        frontmatter = self._extract_frontmatter(content)
        body = self._strip_frontmatter(content)

        title = self._extract_title(body)
        sections = self._extract_sections(body)
        status_items = self._extract_status(body)
        size_kb = round(len(content.encode("utf-8")) / 1024, 1)

        # Frontmatter type takes priority over heuristic
        doc_type = frontmatter.get("type") or self._classify_doc(path, body)

        result: dict[str, Any] = {
            "path": str(path.relative_to(self.root)),
            "title": title,
            "type": doc_type,
            "sections": sections,
            "status_items": status_items,
            "size_kb": size_kb,
        }

        # Add frontmatter fields if present
        if "version" in frontmatter:
            result["version"] = frontmatter["version"]
        if "status" in frontmatter:
            result["doc_status"] = frontmatter["status"]
        if "scope" in frontmatter:
            result["scope"] = frontmatter["scope"]
        if "prerequisite" in frontmatter:
            result["prerequisite"] = frontmatter["prerequisite"]
        if "patterns" in frontmatter:
            result["patterns"] = frontmatter["patterns"]
        if "progress" in frontmatter:
            result["progress"] = frontmatter["progress"]

        return result

    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from markdown (between --- delimiters)."""
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        fm_text = parts[1].strip()
        if not fm_text:
            return {}

        # Simple YAML parsing without PyYAML dependency
        result: dict[str, Any] = {}
        for line in fm_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Parse lists: [item1, item2]
            if value.startswith("[") and value.endswith("]"):
                items = value[1:-1].split(",")
                result[key] = [item.strip().strip('"').strip("'") for item in items if item.strip()]
            else:
                result[key] = value

        return result

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content."""
        if not content.startswith("---"):
            return content
        parts = content.split("---", 2)
        if len(parts) < 3:
            return content
        return parts[2]

    def _extract_title(self, content: str) -> str:
        """Extract the main title from markdown."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("##"):
                return line[2:].strip()
        return ""

    def _extract_sections(self, content: str) -> list[str]:
        """Extract section headings."""
        sections = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## ") or line.startswith("### "):
                heading = re.sub(r"^#+\s*", "", line).strip()
                if heading:
                    sections.append(heading)
        return sections

    def _classify_doc(self, path: Path, content: str) -> str:
        """Classify documentation type."""
        name = path.stem.lower()
        rel_path = str(path.relative_to(self.root)).lower()

        # Check filename rules first
        for pattern, doc_type in DOC_TYPE_RULES:
            if pattern.lower() in name:
                return doc_type

        # Check path rules
        for pattern, doc_type in PATH_TYPE_RULES:
            if pattern in rel_path:
                return doc_type

        # Check content patterns
        if re.search(r"##?\s*(plan|roadmap|milestone)", content, re.IGNORECASE):
            return "plan"
        if re.search(r"##?\s*(architecture|layers|capas)", content, re.IGNORECASE):
            return "architecture"

        return "general"

    def _extract_status(self, content: str) -> list[dict[str, str]]:
        """Extract status items from docs (plans, checklists)."""
        items: list[dict[str, str]] = []

        # Checkbox items
        for match in re.finditer(r"[-*]\s*\[x\]\s*(.+)", content, re.IGNORECASE):
            items.append({"name": match.group(1).strip(), "status": "done"})
        for match in re.finditer(r"[-*]\s*\[\s*\]\s*(.+)", content, re.IGNORECASE):
            items.append({"name": match.group(1).strip(), "status": "pending"})

        # Table status items
        for match in re.finditer(
            r"\|\s*(.+?)\s*\|\s*(done|complete|completado|hecho|✅)\s*\|",
            content,
            re.IGNORECASE,
        ):
            items.append({"name": match.group(1).strip(), "status": "done"})
        for match in re.finditer(
            r"\|\s*(.+?)\s*\|\s*(pending|pendiente|todo|⏳)\s*\|",
            content,
            re.IGNORECASE,
        ):
            items.append({"name": match.group(1).strip(), "status": "pending"})
        for match in re.finditer(
            r"\|\s*(.+?)\s*\|\s*(partial|parcial|in.?progress|🔄)\s*\|",
            content,
            re.IGNORECASE,
        ):
            items.append({"name": match.group(1).strip(), "status": "partial"})

        return items

    def _find_agents_md(self) -> Optional[Path]:
        """Find AGENTS.md file."""
        for name in ["AGENTS.md", "agents.md", ".cursorrules", "CLAUDE.md"]:
            path = self.root / name
            if path.exists():
                return path
        return None

    def _group_by_type(self, docs: list[dict[str, Any]]) -> dict[str, int]:
        """Group doc count by type."""
        groups: dict[str, int] = {}
        for doc in docs:
            t = doc["type"]
            groups[t] = groups.get(t, 0) + 1
        return groups
