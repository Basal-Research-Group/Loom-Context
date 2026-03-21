"""Heuristic selection strategy: lexical + structural matching without AI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry
from loom_context.selector.models import SelectionCandidate, SelectionReason

STOP_WORDS = get_registry().get_stop_words()


class HeuristicStrategy:
    """Select context candidates using lexical and structural heuristics."""

    def __init__(self, context_dir: Path) -> None:
        self.context_dir = context_dir

    def select(self, query: str, max_chars: int = 12000) -> list[SelectionCandidate]:
        """Select candidates matching the query, scored and sorted by relevance."""
        tokens = self._tokenize(query)
        if not tokens:
            return []

        candidates: list[SelectionCandidate] = []

        # 1. Quick rules — always high priority
        candidates.extend(self._match_rules(tokens))

        # 2. Architecture — boundaries and patterns
        candidates.extend(self._match_architecture(tokens))

        # 3. Directory map — structural context
        candidates.extend(self._match_directories(tokens))

        # 4. Naming conventions
        candidates.extend(self._match_naming(tokens))

        # 5. Stack/dependencies
        candidates.extend(self._match_stack(tokens))

        # 6. Plans and docs
        candidates.extend(self._match_plans(tokens))

        # Sort by total score descending
        candidates.sort(key=lambda c: c.total_score, reverse=True)

        # Cut by character budget
        selected: list[SelectionCandidate] = []
        char_count = 0
        for candidate in candidates:
            if char_count + len(candidate.content) > max_chars:
                # Always include rules even if over budget
                if candidate.source == "rules" and char_count < max_chars * 0.9:
                    selected.append(candidate)
                    char_count += len(candidate.content)
                continue
            selected.append(candidate)
            char_count += len(candidate.content)

        return selected

    def _tokenize(self, query: str) -> list[str]:
        """Extract meaningful tokens from query."""
        words = re.findall(r"[a-zA-Z\u00C0-\u024F]+", query.lower())
        return [w for w in words if w not in STOP_WORDS and len(w) > 2]

    def _read_file(self, filename: str) -> str:
        """Read a .context/ file, return empty string if missing."""
        path = self.context_dir / filename
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _read_json(self, filename: str) -> dict[str, Any]:
        """Read a .context/ JSON file."""
        import json

        content = self._read_file(filename)
        if not content:
            return {}
        try:
            data: dict[str, Any] = json.loads(content)
            return data
        except (json.JSONDecodeError, ValueError):
            return {}

    def _score_line(self, line: str, tokens: list[str]) -> float:
        """Score a line based on token matches."""
        line_lower = line.lower()
        matches = sum(1 for t in tokens if t in line_lower)
        if not matches:
            return 0.0
        return min(1.0, matches / len(tokens))

    def _match_rules(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match quick rules from index.json."""
        index = self._read_json("index.json")
        rules = index.get("quick_rules", [])
        if not rules:
            return []

        candidates = []
        matched_rules = []
        unmatched_rules = []

        for rule in rules:
            score = self._score_line(rule, tokens)
            if score > 0:
                matched_rules.append((rule, score))
            else:
                unmatched_rules.append(rule)

        # Always include matched rules
        if matched_rules:
            content_lines = ["## Relevant Rules\n"]
            for rule, _ in sorted(matched_rules, key=lambda x: -x[1]):
                content_lines.append(f"- {rule}")
            candidates.append(
                SelectionCandidate(
                    source="rules",
                    content="\n".join(content_lines),
                    reasons=[
                        SelectionReason(
                            strategy="rule",
                            detail=f"{len(matched_rules)} rules match query tokens",
                            score=0.9,
                        )
                    ],
                )
            )

        # Include remaining rules at lower priority (they're short, always useful)
        if unmatched_rules:
            content_lines = ["## Other Rules\n"]
            for rule in unmatched_rules:
                content_lines.append(f"- {rule}")
            candidates.append(
                SelectionCandidate(
                    source="rules",
                    content="\n".join(content_lines),
                    reasons=[
                        SelectionReason(
                            strategy="rule",
                            detail="remaining rules for completeness",
                            score=0.3,
                        )
                    ],
                )
            )

        return candidates

    def _match_architecture(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match architecture sections."""
        content = self._read_file("architecture.md")
        if not content:
            return []

        sections = self._split_sections(content)
        candidates = []

        for heading, body in sections:
            score = max(
                self._score_line(heading, tokens),
                self._score_line(body[:200], tokens) * 0.7,
            )
            # Architecture is always somewhat relevant
            score = max(score, 0.2)

            candidates.append(
                SelectionCandidate(
                    source="architecture",
                    content=f"## {heading}\n{body}",
                    reasons=[
                        SelectionReason(
                            strategy="architecture",
                            detail=f"section '{heading}' matches",
                            score=score,
                        )
                    ],
                )
            )

        return candidates

    def _match_directories(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match directory map lines."""
        content = self._read_file("directory-map.md")
        if not content:
            return []

        matched_lines = []
        for line in content.split("\n"):
            score = self._score_line(line, tokens)
            if score > 0:
                matched_lines.append((line.strip(), score))

        if not matched_lines:
            return []

        matched_lines.sort(key=lambda x: -x[1])
        content_lines = ["## Relevant Directories\n"]
        for line, _ in matched_lines[:20]:
            if line:
                content_lines.append(line)

        return [
            SelectionCandidate(
                source="directory",
                content="\n".join(content_lines),
                reasons=[
                    SelectionReason(
                        strategy="directory",
                        detail=f"{len(matched_lines)} directory entries match",
                        score=min(1.0, len(matched_lines) / 5),
                    )
                ],
            )
        ]

    def _match_naming(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match naming convention sections."""
        content = self._read_file("naming.md")
        if not content:
            return []

        sections = self._split_sections(content)
        candidates = []

        for heading, body in sections:
            score = max(
                self._score_line(heading, tokens),
                self._score_line(body[:300], tokens) * 0.6,
            )
            if score > 0.1:
                candidates.append(
                    SelectionCandidate(
                        source="naming",
                        content=f"## {heading}\n{body}",
                        reasons=[
                            SelectionReason(
                                strategy="lexical",
                                detail=f"naming section '{heading}' matches",
                                score=score,
                            )
                        ],
                    )
                )

        return candidates

    def _match_stack(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match stack/dependency categories."""
        stack = self._read_json("stack.json")
        summary = stack.get("stack_summary", {})
        if not summary:
            return []

        matched = []
        for category, deps in summary.items():
            cat_score = self._score_line(category.replace("-", " "), tokens)
            deps_text = ", ".join(deps)
            dep_score = self._score_line(deps_text, tokens) * 0.5
            score = max(cat_score, dep_score)
            if score > 0:
                matched.append((category, deps, score))

        if not matched:
            return []

        matched.sort(key=lambda x: -x[2])
        content_lines = ["## Relevant Stack\n"]
        for cat, deps, _ in matched:
            content_lines.append(f"- **{cat}**: {', '.join(deps)}")

        return [
            SelectionCandidate(
                source="stack",
                content="\n".join(content_lines),
                reasons=[
                    SelectionReason(
                        strategy="lexical",
                        detail=f"{len(matched)} stack categories match",
                        score=max(s for _, _, s in matched),
                    )
                ],
            )
        ]

    def _match_plans(self, tokens: list[str]) -> list[SelectionCandidate]:
        """Match plan summaries."""
        content = self._read_file("plans-summary.md")
        if not content:
            return []

        sections = self._split_sections(content)
        candidates = []

        for heading, body in sections:
            score = max(
                self._score_line(heading, tokens),
                self._score_line(body[:300], tokens) * 0.5,
            )
            if score > 0.15:
                candidates.append(
                    SelectionCandidate(
                        source="plan",
                        content=f"## {heading}\n{body}",
                        reasons=[
                            SelectionReason(
                                strategy="doc",
                                detail=f"plan '{heading}' matches",
                                score=score,
                            )
                        ],
                    )
                )

        return candidates

    def _split_sections(self, content: str) -> list[tuple[str, str]]:
        """Split markdown into (heading, body) tuples."""
        sections: list[tuple[str, str]] = []
        current_heading = ""
        current_body: list[str] = []

        for line in content.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                if current_heading:
                    sections.append((current_heading, "\n".join(current_body)))
                current_heading = re.sub(r"^#+\s*", "", line).strip()
                current_body = []
            else:
                current_body.append(line)

        if current_heading:
            sections.append((current_heading, "\n".join(current_body)))

        return sections
