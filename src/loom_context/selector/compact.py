"""Compact formatter: token-efficient output for AI consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CompactFormatter:
    """Generates token-efficient context output.

    Instead of verbose markdown, produces a dense format that
    preserves all information in fewer tokens.

    Analogia: if markdown is a novel, compact is a telegram.
    Same message, 1/3 the words.
    """

    def __init__(self, context_dir: Path) -> None:
        self.context_dir = context_dir

    def format_all(self) -> str:
        """Generate complete compact context."""
        lines: list[str] = []

        index = self._read_json("index.json")
        if not index:
            return ""

        project = index.get("project", {})
        stats = index.get("stats", {})

        # Header: one line
        lines.append(
            f"CTX:{project.get('name', '?')}|"
            f"{project.get('type', '?')}|"
            f"{','.join(project.get('architecture', []))}|"
            f"{project.get('language', '?')}|"
            f"{project.get('runtime', '?')}"
        )

        # Stats: one line
        lines.append(
            f"STATS:files={stats.get('total_files', 0)}|"
            f"code={stats.get('total_code_files', 0)}|"
            f"docs={stats.get('total_docs', 0)}|"
            f"deps={stats.get('total_dependencies', 0)}"
        )

        # Rules: one line each
        rules = index.get("quick_rules", [])
        if rules:
            lines.append("RULES:")
            for rule in rules:
                lines.append(f"  {self._compress_rule(rule)}")

        # Architecture boundaries
        rules_json = self._read_json("rules.json")
        boundaries = rules_json.get("architecture", {}).get("layer_boundaries", {})
        if boundaries:
            lines.append("BOUNDS:")
            for layer, config in boundaries.items():
                forbidden = config.get("forbidden_imports", [])
                if forbidden:
                    lines.append(f"  {layer}!->{','.join(forbidden)}")

        naming = rules_json.get("naming", {})
        file_style = naming.get("files", {}).get("dominant_style", "")
        if file_style:
            lines.append(f"NAMING:files={file_style}")

        code_naming = naming.get("code", {})
        if code_naming:
            parts = []
            for kind, info in code_naming.items():
                if isinstance(info, dict):
                    fmt = info.get("format", "?")
                    prefix = info.get("prefix", "")
                    count = info.get("count", 0)
                    entry = f"{kind}={fmt}"
                    if prefix and prefix != "none":
                        entry += f"({prefix})"
                    if count:
                        entry += f"x{count}"
                    parts.append(entry)
            if parts:
                lines.append(f"NAMING:code={';'.join(parts)}")

        # Suffix patterns: dense
        suffix_patterns = naming.get("files", {}).get("suffix_patterns", [])
        if suffix_patterns:
            patterns = [f"{s['suffix']}={s['pattern']}" for s in suffix_patterns[:8]]
            lines.append(f"SUFFIXES:{';'.join(patterns)}")

        # Stack: one line per category
        stack = self._read_json("stack.json")
        summary = stack.get("stack_summary", {})
        if summary:
            lines.append("STACK:")
            for cat, deps in summary.items():
                short_deps = ",".join(d.split("@")[0] for d in deps[:4])
                lines.append(f"  {cat}:{short_deps}")

        # Directory structure: indented tree, no annotations
        dir_map = self._read_file("directory-map.md")
        if dir_map:
            lines.append("DIRS:")
            for line in dir_map.split("\n"):
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("#")
                    and not stripped.startswith("**")
                    and ("/" in stripped or "files" in stripped)
                ):
                    lines.append(f"  {stripped[:80]}")

        # Import aliases
        aliases = rules_json.get("imports", {}).get("aliases", {})
        if aliases:
            alias_parts = [f"{k}={v}" for k, v in aliases.items()]
            lines.append(f"ALIASES:{';'.join(alias_parts)}")

        return "\n".join(lines)

    def format_ultra(self) -> str:
        """Generate ultra-compact context (<1KB target).

        Strips everything non-essential: no dirs, no stack details,
        only rules and core architecture identity.
        """
        lines: list[str] = []

        index = self._read_json("index.json")
        if not index:
            return ""

        project = index.get("project", {})
        stats = index.get("stats", {})

        # Single-line identity
        lines.append(
            f"{project.get('name', '?')}|"
            f"{project.get('type', '?')}|"
            f"{','.join(project.get('architecture', []))}|"
            f"f={stats.get('total_files', 0)}"
        )

        # Rules: deduplicated, compressed
        rules = index.get("quick_rules", [])
        seen: set[str] = set()
        if rules:
            for rule in rules:
                compressed = self._compress_rule(rule)
                # Deduplicate similar rules
                key = compressed.split("!->")[0] if "!->" in compressed else compressed
                if key not in seen:
                    seen.add(key)
                    lines.append(compressed)

        rules_json = self._read_json("rules.json")
        boundaries = rules_json.get("architecture", {}).get("layer_boundaries", {})
        if boundaries:
            bound_parts = []
            for layer, config in boundaries.items():
                forbidden = config.get("forbidden_imports", [])
                if forbidden:
                    short = ",".join(f[0] for f in forbidden)  # first letter only
                    bound_parts.append(f"{layer[0]}!{short}")
            if bound_parts:
                lines.append(" ".join(bound_parts))

        # Code naming: one line
        naming = rules_json.get("naming", {})
        code_naming = naming.get("code", {})
        if code_naming:
            parts = []
            for kind, info in code_naming.items():
                if isinstance(info, dict) and info.get("format"):
                    parts.append(f"{kind[0]}={info['format']}")
            if parts:
                lines.append(" ".join(parts))

        return "\n".join(lines)

    def format_for_task(self, task: str, candidates: list) -> str:
        """Generate compact format for a bundle."""
        lines: list[str] = []

        index = self._read_json("index.json")
        project = index.get("project", {})

        lines.append(
            f"BUNDLE:{task}|{project.get('name', '?')}|"
            f"{project.get('type', '?')}|"
            f"{','.join(project.get('architecture', []))}"
        )

        for candidate in candidates:
            # Source tag + compressed content
            source = candidate.source.upper()[:4]
            content = candidate.content
            # Compress: remove markdown headers, empty lines, redundant whitespace
            compressed = self._compress_content(content)
            if compressed:
                lines.append(f"[{source}] {compressed}")

        return "\n".join(lines)

    def _compress_rule(self, rule: str) -> str:
        """Compress a rule to minimal form."""
        rule = rule.replace("Layer boundary: ", "")
        rule = rule.replace(" MUST NOT import from ", "!->")
        rule = rule.replace("files follow pattern: ", "=")
        rule = rule.replace(" MUST have ", "=")
        rule = rule.replace("Files use ", "files=")
        return rule.replace(" naming ", "")

    def _compress_content(self, content: str) -> str:
        """Strip markdown formatting, compress whitespace."""
        lines = []
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove markdown headers
            if line.startswith("#"):
                continue
            # Remove table separators
            if line.startswith("|--") or line.startswith("|-"):
                continue
            # Compress table rows
            if line.startswith("|"):
                cells = [c.strip() for c in line.split("|") if c.strip()]
                lines.append(" | ".join(cells))
                continue
            # Remove markdown bold/italic
            line = line.replace("**", "").replace("*", "")
            lines.append(line)

        return " ".join(lines)[:500]

    def _read_json(self, filename: str) -> dict[str, Any]:
        """Read a .context/ JSON file."""
        path = self.context_dir / filename
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _read_file(self, filename: str) -> str:
        """Read a .context/ file."""
        path = self.context_dir / filename
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""
