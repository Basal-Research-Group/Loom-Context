"""Naming convention auditor."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry
from loom_context.models import Violation
from loom_context.security.filter import FileFilter

CODE_EXTENSIONS = get_registry().get_all_extensions()


class NamingAuditor:
    """Validates naming conventions against rules.json."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter
        self.rules: dict[str, Any] = {}

    def load_rules(self) -> bool:
        """Load rules from .context/rules.json."""
        rules_path = self.root / ".context" / "rules.json"
        if not rules_path.exists():
            return False
        try:
            with open(rules_path, encoding="utf-8") as f:
                self.rules = json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def audit(self) -> list[Violation]:
        """Run naming audit and return violations."""
        if not self.rules and not self.load_rules():
            return [
                Violation(
                    file=".context/rules.json",
                    line=None,
                    rule="rules-missing",
                    message="No rules.json found. Run 'loom init' first.",
                    severity="error",
                )
            ]

        violations: list[Violation] = []
        naming_rules = self.rules.get("naming", {})

        # Audit code-level naming
        code_rules = naming_rules.get("code", {})

        for filepath in self.file_filter.walk():
            if filepath.suffix not in CODE_EXTENSIONS:
                continue

            rel = str(filepath.relative_to(self.root))

            # Check interface prefix rule
            if code_rules.get("interfaces", {}).get("prefix") == "I":
                violations.extend(self._check_interface_prefix(filepath, rel))

        return violations

    def _check_interface_prefix(self, filepath: Path, rel: str) -> list[Violation]:
        """Check that interfaces have the I prefix."""
        violations: list[Violation] = []

        if filepath.suffix not in {".ts", ".tsx"}:
            return violations

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")[:150]
        except OSError:
            return violations

        interface_pattern = re.compile(r"(?:export\s+)?interface\s+(\w+)")
        for i, line in enumerate(lines, 1):
            match = interface_pattern.search(line)
            if match:
                name = match.group(1)
                if (
                    (not name.startswith("I") or (len(name) > 1 and not name[1].isupper()))
                    and not name.endswith("Props")
                    and not name.endswith("State")
                ):
                    violations.append(
                        Violation(
                            file=rel,
                            line=i,
                            rule="interface-prefix",
                            message=f"Interface '{name}' missing 'I' prefix",
                            severity="warning",
                            suggestion=f"Rename to 'I{name}'",
                        )
                    )

        return violations
