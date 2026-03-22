"""Code smell auditor: detects common anti-patterns using knowledge registry."""

from __future__ import annotations

import re
from pathlib import Path

from loom_context.knowledge import get_registry
from loom_context.models import Violation
from loom_context.security.filter import FileFilter

_registry = get_registry()
CODE_EXTENSIONS = _registry.get_all_extensions()

# Directories to exclude from console/print checks
_TEST_DIRS = {"tests", "test", "spec", "__tests__", "scripts", "e2e"}


class SmellAuditor:
    """Detects code smells from code_smells.json definitions."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter
        self._smells = _registry.get_code_smells()
        self._code_files: list[Path] = []

    def _get_code_files(self) -> list[Path]:
        """Lazily collect code files (cached)."""
        if not self._code_files:
            self._code_files = [
                f for f in self.file_filter.walk() if f.suffix in CODE_EXTENSIONS
            ]
        return self._code_files

    def audit(self) -> list[Violation]:
        """Run all smell detections."""
        violations: list[Violation] = []

        violations.extend(self._check_god_classes())
        violations.extend(self._check_hardcoded_secrets())
        violations.extend(self._check_empty_catches())
        violations.extend(self._check_sql_injection())
        violations.extend(self._check_console_in_production())
        violations.extend(self._check_todo_fixme())
        violations.extend(self._check_long_parameters())
        violations.extend(self._check_deep_nesting())
        violations.extend(self._check_config_smells())

        return violations

    # --- Size smells ---

    def _check_god_classes(self) -> list[Violation]:
        """Detect files with too many lines (>500)."""
        violations: list[Violation] = []
        threshold = 500

        for filepath in self._get_code_files():
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

    def _check_long_parameters(self) -> list[Violation]:
        """Detect functions with too many parameters (>5)."""
        violations: list[Violation] = []
        smell = self._smells.get("long-parameter-list", {})
        lang_patterns = smell.get("detection", {}).get("patterns", {})

        for filepath in self._get_code_files():
            lang = _registry.get_language(filepath.suffix)
            if not lang:
                continue
            pat_str = lang_patterns.get(lang.name.lower(), "")
            if not pat_str:
                continue
            try:
                pat = re.compile(pat_str)
            except re.error:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            for i, line in enumerate(content.split("\n")[:500], 1):
                if pat.search(line):
                    violations.append(
                        Violation(
                            file=rel,
                            line=i,
                            rule="long-parameter-list",
                            message="Function has many parameters",
                            severity="info",
                            suggestion="Use a parameter object or builder",
                        )
                    )

        return violations

    def _check_deep_nesting(self) -> list[Violation]:
        """Detect deeply nested code (>4 levels)."""
        violations: list[Violation] = []
        # 5 levels x 4 spaces = 20 spaces threshold
        threshold_spaces = 20
        pat = re.compile(r"^(\s+)\S")

        for filepath in self._get_code_files():
            try:
                lines = filepath.read_text(
                    encoding="utf-8", errors="ignore"
                ).split("\n")[:500]
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            deep_count = 0
            for i, line in enumerate(lines, 1):
                m = pat.match(line)
                if m:
                    indent = len(m.group(1).expandtabs(4))
                    if indent >= threshold_spaces:
                        deep_count += 1
                        if deep_count == 1:
                            violations.append(
                                Violation(
                                    file=rel,
                                    line=i,
                                    rule="deep-nesting",
                                    message="Deeply nested code (>4 levels)",
                                    severity="warning",
                                    suggestion="Use early returns or extract methods",
                                )
                            )
            # Max 1 violation per file for nesting

        return violations

    # --- Security smells ---

    def _check_hardcoded_secrets(self) -> list[Violation]:
        """Detect hardcoded passwords, tokens, API keys."""
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

        for filepath in self._get_code_files():
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")[:300]
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            for i, line in enumerate(lines, 1):
                for cpat in compiled:
                    if cpat.search(line):
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
                        break

        return violations

    def _check_sql_injection(self) -> list[Violation]:
        """Detect string interpolation in SQL queries."""
        violations: list[Violation] = []
        smell = self._smells.get("sql-injection-risk", {})
        lang_patterns = smell.get("detection", {}).get("patterns", {})

        for filepath in self._get_code_files():
            lang = _registry.get_language(filepath.suffix)
            if not lang:
                continue
            pat_str = lang_patterns.get(lang.name.lower(), "")
            if not pat_str:
                continue
            try:
                pat = re.compile(pat_str)
            except re.error:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            for i, line in enumerate(content.split("\n")[:500], 1):
                if pat.search(line):
                    violations.append(
                        Violation(
                            file=rel,
                            line=i,
                            rule="sql-injection-risk",
                            message="Possible SQL injection (string interpolation)",
                            severity="error",
                            suggestion="Use parameterized queries",
                        )
                    )

        return violations

    def _check_empty_catches(self) -> list[Violation]:
        """Detect empty exception handlers."""
        violations: list[Violation] = []
        smell = self._smells.get("empty-catch", {})
        lang_patterns = smell.get("detection", {}).get("patterns", {})

        for filepath in self._get_code_files():
            lang = _registry.get_language(filepath.suffix)
            if not lang:
                continue
            pat_str = lang_patterns.get(lang.name.lower(), "")
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

    # --- Structure smells ---

    def _check_console_in_production(self) -> list[Violation]:
        """Detect console.log/print in production code."""
        violations: list[Violation] = []
        smell = self._smells.get("console-in-production", {})
        lang_patterns = smell.get("detection", {}).get("patterns", {})

        for filepath in self._get_code_files():
            # Skip test directories
            if any(part in _TEST_DIRS for part in filepath.parts):
                continue

            lang = _registry.get_language(filepath.suffix)
            if not lang:
                continue
            pat_str = lang_patterns.get(lang.name.lower(), "")
            if not pat_str:
                continue
            try:
                pat = re.compile(pat_str)
            except re.error:
                continue

            try:
                lines = filepath.read_text(
                    encoding="utf-8", errors="ignore"
                ).split("\n")[:300]
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            count = 0
            for i, line in enumerate(lines, 1):
                if pat.search(line) and count < 3:
                    violations.append(
                        Violation(
                            file=rel,
                            line=i,
                            rule="console-in-production",
                            message="Debug output in production code",
                            severity="info",
                            suggestion="Use a logging framework",
                        )
                    )
                    count += 1

        return violations

    def _check_todo_fixme(self) -> list[Violation]:
        """Detect TODO/FIXME/HACK comments."""
        violations: list[Violation] = []
        smell = self._smells.get("todo-fixme", {})
        patterns_raw = (
            smell.get("detection", {}).get("patterns", {}).get("_all", [])
        )
        if not patterns_raw:
            return violations

        pat_str = patterns_raw[0] if patterns_raw else ""
        try:
            pat = re.compile(pat_str, re.IGNORECASE)
        except re.error:
            return violations

        for filepath in self._get_code_files():
            try:
                lines = filepath.read_text(
                    encoding="utf-8", errors="ignore"
                ).split("\n")[:500]
            except OSError:
                continue

            rel = str(filepath.relative_to(self.root))
            count = 0
            for i, line in enumerate(lines, 1):
                if pat.search(line) and count < 5:
                    violations.append(
                        Violation(
                            file=rel,
                            line=i,
                            rule="todo-fixme",
                            message="TODO/FIXME marker",
                            severity="info",
                            suggestion="Track in issue tracker",
                        )
                    )
                    count += 1

        return violations

    # --- Config smells ---

    def _check_config_smells(self) -> list[Violation]:
        """Check project configuration smells."""
        violations: list[Violation] = []

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
                            suggestion=f"Expected: {', '.join(locks)}",
                        )
                    )

        return violations
