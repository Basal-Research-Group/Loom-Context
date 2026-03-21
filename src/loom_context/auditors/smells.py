"""Code smell auditor: detects common anti-patterns using knowledge registry."""

from __future__ import annotations

import re
from pathlib import Path

from loom_context.knowledge import get_registry
from loom_context.models import Violation
from loom_context.security.filter import FileFilter

_registry = get_registry()
CODE_EXTENSIONS = _registry.get_all_extensions()


class SmellAuditor:
    """Detects code smells from code_smells.json definitions."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter
        self._smells = _registry.get_code_smells()

    def audit(self) -> list[Violation]:
        """Run smell detection and return violations."""
        violations: list[Violation] = []

        violations.extend(self._check_god_classes())
        violations.extend(self._check_hardcoded_secrets())
        violations.extend(self._check_empty_catches())
        violations.extend(self._check_config_smells())

        return violations

    def _check_god_classes(self) -> list[Violation]:
        """Detect files with too many lines (>500)."""
        violations: list[Violation] = []
        threshold = 500

        for filepath in self.file_filter.walk():
            if filepath.suffix not in CODE_EXTENSIONS:
                continue
            try:
                line_count = len(filepath.read_bytes().split(b"\n"))
            except OSError:
                continue

            if line_count > threshold:
                rel = str(filepath.relative_to(self.root))
                violations.append(
                    Violation(
                        file=rel,
                        line=None,
                        rule="god-class",
                        message=f"File has {line_count} lines (>{threshold})",
                        severity="warning",
                        suggestion="Split into smaller modules",
                    )
                )

        return violations

    def _check_hardcoded_secrets(self) -> list[Violation]:
        """Detect hardcoded passwords, tokens, API keys in code."""
        violations: list[Violation] = []
        smell = self._smells.get("hardcoded-secret", {})
        patterns_raw = (
            smell.get("detection", {}).get("patterns", {}).get("_all", [])
        )
        if not patterns_raw:
            return violations

        compiled = []
        for p in patterns_raw:
            try:
                compiled.append(re.compile(p, re.IGNORECASE))
            except re.error:
                continue

        for filepath in self.file_filter.walk():
            if filepath.suffix not in CODE_EXTENSIONS:
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")[:300]
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            for i, line in enumerate(lines, 1):
                for pat in compiled:
                    if pat.search(line):
                        violations.append(
                            Violation(
                                file=rel,
                                line=i,
                                rule="hardcoded-secret",
                                message="Possible hardcoded secret",
                                severity="error",
                                suggestion="Move to environment variable",
                            )
                        )
                        break  # One per line max

        return violations

    def _check_empty_catches(self) -> list[Violation]:
        """Detect empty exception handlers."""
        violations: list[Violation] = []
        smell = self._smells.get("empty-catch", {})
        lang_patterns = smell.get("detection", {}).get("patterns", {})

        for filepath in self.file_filter.walk():
            if filepath.suffix not in CODE_EXTENSIONS:
                continue

            lang = _registry.get_language(filepath.suffix)
            if not lang:
                continue

            # Find matching pattern for this language
            lang_name = lang.name.lower()
            pat_str = lang_patterns.get(lang_name, "")
            if not pat_str:
                continue

            try:
                pat = re.compile(pat_str, re.MULTILINE)
            except re.error:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            for match in pat.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                violations.append(
                    Violation(
                        file=rel,
                        line=line_num,
                        rule="empty-catch",
                        message="Empty exception handler",
                        severity="warning",
                        suggestion="Log the error or handle it",
                    )
                )

        return violations

    def _check_config_smells(self) -> list[Violation]:
        """Check project configuration smells."""
        violations: list[Violation] = []

        # No .gitignore
        if not (self.root / ".gitignore").exists():
            violations.append(
                Violation(
                    file=".",
                    line=None,
                    rule="no-gitignore",
                    message="No .gitignore file found",
                    severity="warning",
                    suggestion="Add a .gitignore for your language",
                )
            )

        # No lockfile
        smell = self._smells.get("no-lockfile", {})
        pairs = smell.get("detection", {}).get("pairs", [])
        for pair in pairs:
            manifest = pair.get("manifest", "")
            locks = pair.get("locks", [])
            if (self.root / manifest).exists():
                has_lock = any((self.root / lf).exists() for lf in locks)
                if not has_lock:
                    violations.append(
                        Violation(
                            file=manifest,
                            line=None,
                            rule="no-lockfile",
                            message=f"No lockfile for {manifest}",
                            severity="warning",
                            suggestion=f"Expected one of: {', '.join(locks)}",
                        )
                    )

        return violations
