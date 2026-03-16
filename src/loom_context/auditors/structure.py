"""Structure auditor: validates architectural layer boundaries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from loom_context.models import Violation
from loom_context.security.filter import FileFilter

# Import patterns for different languages
TS_IMPORT = re.compile(r"""(?:import|from)\s+['"](@?[^'"]+)['"]""")
TS_REQUIRE = re.compile(r"""require\(['"]([^'"]+)['"]\)""")
PY_IMPORT = re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE)

CODE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}


class StructureAuditor:
    """Validates import boundaries between architectural layers."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter
        self.rules: dict[str, Any] = {}
        self.import_aliases: dict[str, str] = {}

    def load_rules(self) -> bool:
        """Load rules from .context/rules.json."""
        rules_path = self.root / ".context" / "rules.json"
        if not rules_path.exists():
            return False
        try:
            with open(rules_path, encoding="utf-8") as f:
                self.rules = json.load(f)
            self.import_aliases = self.rules.get("imports", {}).get("aliases", {})
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def audit(self) -> list[Violation]:
        """Run structural audit and return violations."""
        if not self.rules and not self.load_rules():
            return []

        boundaries = self.rules.get("architecture", {}).get("layer_boundaries", {})
        if not boundaries:
            return []

        violations: list[Violation] = []

        for filepath in self.file_filter.walk():
            if filepath.suffix not in CODE_EXTENSIONS:
                continue

            rel = filepath.relative_to(self.root)
            current_layer = self._detect_layer(rel, boundaries)
            if not current_layer:
                continue

            forbidden = boundaries.get(current_layer, {}).get("forbidden_imports", [])
            if not forbidden:
                continue

            imports = self._extract_imports(filepath)
            for imp, line_num in imports:
                target_layer = self._resolve_import_layer(imp, boundaries)
                if target_layer and target_layer in forbidden:
                    violations.append(
                        Violation(
                            file=str(rel),
                            line=line_num,
                            rule="layer-boundary",
                            message=(
                                f"Layer violation: '{current_layer}' imports from "
                                f"'{target_layer}' (import: {imp})"
                            ),
                            severity="error",
                            suggestion=f"Use a port/interface from '{current_layer}' layer instead",
                        )
                    )

        return violations

    def _detect_layer(self, rel: Path, boundaries: dict[str, Any]) -> Optional[str]:
        """Detect which architectural layer a file belongs to."""
        parts = rel.parts
        for part in parts:
            if part in boundaries:
                return part
        return None

    def _extract_imports(self, filepath: Path) -> list[tuple[str, int]]:
        """Extract import paths with line numbers."""
        imports: list[tuple[str, int]] = []

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return imports

        lines = content.split("\n")
        for i, line in enumerate(lines[:200], 1):  # Only check first 200 lines
            if filepath.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                for match in TS_IMPORT.finditer(line):
                    imports.append((match.group(1), i))
                for match in TS_REQUIRE.finditer(line):
                    imports.append((match.group(1), i))
            elif filepath.suffix == ".py":
                for match in PY_IMPORT.finditer(line):
                    imports.append((match.group(1), i))

        return imports

    def _resolve_import_layer(self, import_path: str, boundaries: dict[str, Any]) -> Optional[str]:
        """Resolve an import path to its architectural layer."""
        # Handle aliases first
        for alias, target in self.import_aliases.items():
            clean_alias = alias.rstrip("/*")
            if import_path.startswith(clean_alias):
                # Resolve the alias to actual path
                clean_target = target.rstrip("/*")
                import_path = import_path.replace(clean_alias, clean_target, 1)
                break

        # Check each part of the import path against known layers
        parts = import_path.replace("\\", "/").split("/")
        for part in parts:
            if part in boundaries:
                return part

        return None
