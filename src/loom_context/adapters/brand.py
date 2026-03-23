"""Brand domain adapter: for brand, design system, and product projects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loom_context.adapters.base import DomainAdapter
from loom_context.scanners.base import BaseScanner


class BrandAdapter(DomainAdapter):
    """Adapter for brand/design-system projects. Core scanners + brand-specific output."""

    name = "brand"

    def get_scanners(self) -> list[BaseScanner]:
        # Brand projects typically don't have code or deps to scan
        return self._core_scanners()

    def post_generate(self, scan_result: dict[str, Any], context_dir: Path) -> list[str]:
        """Generate brand-specific .context/ files."""
        generated: list[str] = []

        # brand.md — brand identity summary
        brand_content = self._generate_brand_md(scan_result)
        if brand_content:
            (context_dir / "brand.md").write_text(brand_content, encoding="utf-8")
            generated.append("brand.md")

        # governance.md — brand governance rules
        governance_content = self._generate_governance_md(scan_result)
        if governance_content:
            (context_dir / "governance.md").write_text(governance_content, encoding="utf-8")
            generated.append("governance.md")

        return generated

    def _generate_brand_md(self, scan_result: dict[str, Any]) -> str:
        """Generate brand.md from scan results."""
        structure = scan_result.get("structure", {})
        docs = scan_result.get("docs", {})
        domain_details = scan_result.get("domain_details", {})

        lines = ["# Brand Context", ""]
        lines.append(f"Project: {structure.get('project_name', 'unknown')}")
        lines.append(f"Domain: brand (confidence: {scan_result.get('domain_confidence', 0):.2f})")
        lines.append("")

        # Brand directories found
        brand_dirs = []
        tree = structure.get("directory_tree", {})
        brand_keywords = {"brand", "tokens", "guidelines", "assets", "icons", "logos", "typography"}
        for d in tree:
            if d.lower() in brand_keywords:
                brand_dirs.append(d)

        if brand_dirs:
            lines.append("## Brand Directories")
            lines.append("")
            for d in sorted(brand_dirs):
                lines.append(f"- `{d}/`")
            lines.append("")

        # Documentation summary
        doc_list = docs.get("docs", [])
        brand_docs = [d for d in doc_list if any(
            kw in d.get("path", "").lower()
            for kw in ("brand", "guide", "token", "style", "design")
        )]
        if brand_docs:
            lines.append("## Brand Documentation")
            lines.append("")
            for d in brand_docs[:10]:
                lines.append(f"- `{d['path']}` — {d.get('title', 'untitled')}")
            if len(brand_docs) > 10:
                lines.append(f"- ... +{len(brand_docs) - 10} more")
            lines.append("")

        return "\n".join(lines) if len(lines) > 4 else ""

    def _generate_governance_md(self, scan_result: dict[str, Any]) -> str:
        """Generate governance.md from domain governance rules."""
        from loom_context.knowledge import get_registry

        registry = get_registry()
        domain_data = registry.get_domain("brand")
        if not domain_data:
            return ""

        gov_rules = domain_data.get("governance_rules", {})
        if not gov_rules:
            return ""

        lines = ["# Brand Governance Rules", ""]
        lines.append("These rules are enforced by Loom for brand-domain projects.")
        lines.append("")

        for rule_name, rule_def in gov_rules.items():
            if isinstance(rule_def, dict):
                desc = rule_def.get("description", "")
                detection = rule_def.get("detection", "")
                action = rule_def.get("action", "")
                lines.append(f"## {rule_name.replace('_', ' ').title()}")
                lines.append("")
                if desc:
                    lines.append(f"**Rule**: {desc}")
                if detection:
                    lines.append(f"**Detection**: {detection}")
                if action:
                    lines.append(f"**Action**: {action}")
                lines.append("")
            else:
                lines.append(f"- **{rule_name}**: {rule_def}")
                lines.append("")

        return "\n".join(lines)
