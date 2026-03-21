"""Focus generator: produces task-specific context prompts from .context/ data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from loom_context.knowledge import get_registry

STOP_WORDS = get_registry().get_stop_words()


def _tokenize(query: str) -> list[str]:
    """Split query into meaningful tokens."""
    raw = re.split(r"[\s,;:./\\()\[\]{}'\"]+", query.lower())
    return [t for t in raw if t and t not in STOP_WORDS and len(t) > 1]


def _score_text(tokens: list[str], text: str) -> int:
    """Score how many tokens match in the text (substring match)."""
    text_lower = text.lower()
    return sum(1 for t in tokens if t in text_lower)


class FocusGenerator:
    """Generates a focused context prompt filtered by a task query."""

    def __init__(self, context_dir: Path) -> None:
        self.context_dir = context_dir

    def generate(self, query: str, max_chars: int = 8000) -> Optional[str]:
        """Generate focused prompt for the given query."""
        tokens = _tokenize(query)
        if not tokens:
            return None

        index = self._read_json("index.json")
        if not index:
            return None

        sections: list[str] = []
        project = index.get("project", {})

        # Header (always included)
        sections.append(f'# Focused Context: "{query}"')
        sections.append(
            f"**Project:** {project.get('name', '')} "
            f"({project.get('type', '')}, "
            f"{', '.join(project.get('architecture', []))})"
        )
        sections.append("")

        # Matched quick rules
        matched_rules = self._match_rules(tokens, index.get("quick_rules", []))
        if matched_rules:
            sections.append("## Relevant Rules")
            for rule in matched_rules:
                sections.append(f"- {rule}")
            sections.append("")

        # Matched architecture boundaries
        arch_section = self._match_architecture(tokens)
        if arch_section:
            sections.append(arch_section)

        # Matched directory structure
        dir_section = self._match_directories(tokens)
        if dir_section:
            sections.append(dir_section)

        # Matched naming patterns
        naming_section = self._match_naming(tokens)
        if naming_section:
            sections.append(naming_section)

        # Matched documentation
        docs_section = self._match_docs(tokens)
        if docs_section:
            sections.append(docs_section)

        # Matched stack
        stack_section = self._match_stack(tokens)
        if stack_section:
            sections.append(stack_section)

        # Footer
        full = "\n".join(sections)
        if len(full) > max_chars:
            full = full[:max_chars] + "\n\n[... truncated to budget]"

        char_count = len(full)
        full += f"\n\n---\nFocused context by Loom ({char_count} chars)."

        return full

    def _match_rules(self, tokens: list[str], rules: list[str]) -> list[str]:
        """Filter quick_rules by relevance to query."""
        return [r for r in rules if _score_text(tokens, r) > 0]

    def _match_architecture(self, tokens: list[str]) -> Optional[str]:
        """Extract relevant architecture sections."""
        content = self._read_md("architecture.md")
        if not content:
            return None

        lines = content.split("\n")
        matched_lines: list[str] = []
        in_relevant_section = False

        for line in lines:
            score = _score_text(tokens, line)
            if line.startswith("#"):
                in_relevant_section = score > 0
            if in_relevant_section or score > 0:
                matched_lines.append(line)

        if not matched_lines:
            return None

        return "\n".join(matched_lines) + "\n"

    def _match_directories(self, tokens: list[str]) -> Optional[str]:
        """Extract relevant directory entries."""
        content = self._read_md("directory-map.md")
        if not content:
            return None

        lines = content.split("\n")
        matched: list[str] = []

        for line in lines:
            if _score_text(tokens, line) > 0:
                matched.append(line)

        if not matched:
            return None

        result = "## Relevant Directories\n\n"
        result += "\n".join(matched) + "\n"
        return result

    def _match_naming(self, tokens: list[str]) -> Optional[str]:
        """Extract relevant naming patterns."""
        content = self._read_md("naming.md")
        if not content:
            return None

        lines = content.split("\n")
        matched: list[str] = []
        in_relevant = False

        for line in lines:
            score = _score_text(tokens, line)
            if line.startswith("#"):
                in_relevant = score > 0
                if in_relevant:
                    matched.append(line)
            elif in_relevant or (score > 0 and line.strip()):
                matched.append(line)

        if not matched:
            return None
        return "\n".join(matched) + "\n"

    def _match_docs(self, tokens: list[str]) -> Optional[str]:
        """Extract relevant documentation references."""
        content = self._read_md("plans-summary.md")
        if not content:
            return None

        lines = content.split("\n")
        matched: list[str] = []
        in_relevant = False

        for line in lines:
            score = _score_text(tokens, line)
            if line.startswith("#"):
                in_relevant = score > 0
                if in_relevant:
                    matched.append(line)
            elif in_relevant or score > 0:
                matched.append(line)

        if not matched:
            return None

        result = "## Related Documentation\n\n"
        result += "\n".join(matched) + "\n"
        return result

    def _match_stack(self, tokens: list[str]) -> Optional[str]:
        """Extract relevant stack info."""
        data = self._read_json("stack.json")
        if not data:
            return None

        summary = data.get("stack_summary", {})
        matched: list[str] = []

        for category, packages in summary.items():
            cat_text = f"{category}: {', '.join(packages)}"
            if _score_text(tokens, cat_text) > 0:
                matched.append(f"- **{category}:** {', '.join(packages)}")

        if not matched:
            return None

        result = "## Relevant Stack\n\n"
        result += "\n".join(matched) + "\n"
        return result

    def _read_md(self, filename: str) -> Optional[str]:
        path = self.context_dir / filename
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                return None
        return None

    def _read_json(self, filename: str) -> Optional[dict[str, Any]]:
        path = self.context_dir / filename
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else None
            except (json.JSONDecodeError, OSError):
                return None
        return None
