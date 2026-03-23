"""Governance auditor: enforces domain-specific rules from knowledge/domains/*.json."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry
from loom_context.models import Violation
from loom_context.security.filter import FileFilter


class GovernanceAuditor:
    """Audits domain governance rules (brand i18n, token consistency, etc.)."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter

    def audit(self, domain: str) -> list[Violation]:
        """Run governance rules for the given domain."""
        if domain in ("unknown", "mixed"):
            return []

        registry = get_registry()
        domain_data = registry.get_domain(domain)
        if not domain_data:
            return []

        gov_rules = domain_data.get("governance_rules", {})
        if not gov_rules:
            return []

        violations: list[Violation] = []

        for rule_name, rule_def in gov_rules.items():
            if not isinstance(rule_def, dict):
                continue

            handler = self._get_handler(rule_name)
            if handler:
                violations.extend(handler(rule_def))

        return violations

    def _get_handler(self, rule_name: str) -> Any:
        """Get handler function for a governance rule."""
        handlers = {
            "i18n_sync": self._check_i18n_sync,
            "token_consistency": self._check_token_consistency,
            "asset_naming": self._check_asset_naming,
        }
        return handlers.get(rule_name)

    def _check_i18n_sync(self, rule_def: dict[str, Any]) -> list[Violation]:
        """Check if multi-language docs are in sync."""
        violations: list[Violation] = []

        # Look for locale directories
        locale_dirs = {"en", "es", "fr", "de", "pt", "ja", "zh", "ko", "i18n", "locales"}
        found_locales: dict[str, Path] = {}

        for f in self.file_filter.walk():
            try:
                rel = f.relative_to(self.root)
                parts = rel.parts
                for part in parts:
                    if part.lower() in locale_dirs:
                        found_locales[part.lower()] = f.parent
                        break
            except ValueError:
                continue

        # If multiple locale dirs found, check for stale translations
        if len(found_locales) >= 2:
            # Compare file counts between locale dirs
            locale_counts: dict[str, int] = {}
            for name, path in found_locales.items():
                if path.exists():
                    count = sum(1 for _ in path.rglob("*.md"))
                    locale_counts[name] = count

            if locale_counts:
                max_count = max(locale_counts.values())
                for name, count in locale_counts.items():
                    if count < max_count * 0.5:  # Less than half the files
                        violations.append(Violation(
                            file=str(name) + "/",
                            line=None,
                            rule="governance:i18n_sync",
                            message=f"Locale '{name}' has {count} files, "
                                    f"expected ~{max_count} (stale translation)",
                            severity="warning",
                            suggestion=rule_def.get("action", "Flag stale translations"),
                        ))

        return violations

    def _check_token_consistency(self, rule_def: dict[str, Any]) -> list[Violation]:
        """Check if design tokens are the source of truth (no hardcoded brand values)."""
        violations: list[Violation] = []

        # Check if tokens/ directory exists
        tokens_dir = self.root / "tokens"
        if not tokens_dir.exists():
            tokens_dir = self.root / "foundations"

        if not tokens_dir.exists():
            return []  # No tokens to validate against

        # Look for CSS/SCSS files that might hardcode brand values
        for f in self.file_filter.walk():
            if f.suffix in (".css", ".scss", ".less"):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    # Simple heuristic: hardcoded hex colors that look like brand colors
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if "#" in line and "var(--" not in line and "token" not in line.lower():
                            # Has hex color but doesn't use CSS variables or tokens
                            stripped = line.strip()
                            if stripped.startswith("//") or stripped.startswith("/*"):
                                continue
                            if any(c in stripped for c in ["#fff", "#000", "#FFF", "#000"]):
                                continue  # Skip black/white
                            import re

                            if re.search(r"#[0-9a-fA-F]{3,8}", stripped):
                                try:
                                    rel_path = str(f.relative_to(self.root))
                                except ValueError:
                                    rel_path = str(f)
                                violations.append(Violation(
                                    file=rel_path,
                                    line=i,
                                    rule="governance:token_consistency",
                                    message="Hardcoded color value — should use design tokens",
                                    severity="warning",
                                    suggestion=rule_def.get("action", "Use token variables"),
                                ))
                                break  # One per file is enough
                except Exception:  # noqa: S110
                    continue

        return violations

    def _check_asset_naming(self, rule_def: dict[str, Any]) -> list[Violation]:
        """Check if brand assets follow naming conventions."""
        violations: list[Violation] = []
        asset_dirs = {"icons", "logos", "assets", "images"}

        for f in self.file_filter.walk():
            try:
                rel = f.relative_to(self.root)
                parts = {p.lower() for p in rel.parts}
            except ValueError:
                continue

            if not parts & asset_dirs:
                continue

            if f.suffix.lower() in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"):
                name = f.stem
                # Check naming: should be kebab-case or snake_case, not mixed
                has_upper = any(c.isupper() for c in name)
                has_space = " " in name
                if has_upper or has_space:
                    try:
                        rel_path = str(f.relative_to(self.root))
                    except ValueError:
                        rel_path = str(f)
                    violations.append(Violation(
                        file=rel_path,
                        line=None,
                        rule="governance:asset_naming",
                        message=f"Asset '{name}' uses inconsistent naming "
                                f"(should be kebab-case or snake_case)",
                        severity="warning",
                        suggestion=rule_def.get("action", "Rename to kebab-case"),
                    ))

        return violations
