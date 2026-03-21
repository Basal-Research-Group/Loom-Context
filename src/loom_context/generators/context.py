"""Context generator: writes all .context/ files using Jinja2 templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ContextGenerator:
    """Generates all .context/ files from scan results."""

    def __init__(self, context_dir: Path) -> None:
        self.context_dir = context_dir
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,  # noqa: S701 — generating .md, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_all(self, scan_result: dict[str, Any], index_data: dict[str, Any]) -> list[str]:
        """Generate all context files. Returns list of generated file names."""
        self.context_dir.mkdir(exist_ok=True)
        generated: list[str] = []

        # index.json
        self._write_json("index.json", index_data)
        generated.append("index.json")

        # architecture.md
        self._generate_architecture(scan_result)
        generated.append("architecture.md")

        # naming.md
        self._generate_naming(scan_result)
        generated.append("naming.md")

        # directory-map.md
        self._generate_directory_map(scan_result)
        generated.append("directory-map.md")

        # stack.json
        self._generate_stack(scan_result)
        generated.append("stack.json")

        # rules.json
        self._generate_rules(scan_result)
        generated.append("rules.json")

        # plans-summary.md
        self._generate_plans_summary(scan_result)
        generated.append("plans-summary.md")

        # database.md (if database config exists in loom.json)
        if self._has_database_config():
            self._generate_database()
            generated.append("database.md")

        return generated

    def _write_json(self, filename: str, data: Any) -> None:
        path = self.context_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _write_md(self, filename: str, content: str) -> None:
        path = self.context_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _read_loom_json(self) -> dict[str, Any]:
        """Read .context/loom.json if it exists."""
        loom_path = self.context_dir / "loom.json"
        if not loom_path.exists():
            return {}
        try:
            with open(loom_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _has_database_config(self) -> bool:
        """Check if loom.json has a database section."""
        loom_json = self._read_loom_json()
        return bool(loom_json.get("database", {}).get("schema_path"))

    def _generate_database(self) -> None:
        """Generate database.md from Prisma schema and migrations."""
        from loom_context.scanners.database import DatabaseScanner
        from loom_context.scanners.migrations import MigrationScanner

        loom_json = self._read_loom_json()
        db_config = loom_json.get("database", {})

        # Resolve root from context_dir (context_dir = root/.context)
        root = self.context_dir.parent

        # Scan schema
        db_scanner = DatabaseScanner(root)
        db_result = db_scanner.scan(db_config.get("schema_path"))

        # Scan migrations
        mig_scanner = MigrationScanner(root)
        mig_result = mig_scanner.scan(db_config.get("migrations_path"))

        # Get domains from loom.json
        domains = db_config.get("domains", {})

        template = self.env.get_template("database.md.j2")
        content = template.render(
            provider=db_result.provider,
            model_count=db_result.model_count,
            enum_count=db_result.enum_count,
            relation_count=db_result.relation_count,
            extensions=db_result.extensions,
            models=db_result.models,
            enums=db_result.enums,
            migrations=mig_result.migrations,
            total_sql_lines=mig_result.total_sql_lines,
            total_functions=mig_result.total_functions,
            total_triggers=mig_result.total_triggers,
            total_policies=mig_result.total_policies,
            total_indices=mig_result.total_indices,
            domains=domains,
        )
        self._write_md("database.md", content)

    def _generate_architecture(self, scan_result: dict[str, Any]) -> None:
        template = self.env.get_template("architecture.md.j2")
        structure = scan_result.get("structure", {})

        # Read loom.json for manual layer definitions (monorepo support)
        loom_json = self._read_loom_json()
        loom_arch = loom_json.get("architecture", {})
        loom_layers = loom_arch.get("layers", [])

        # Use loom.json layers if auto-detection found nothing
        boundaries = structure.get("layer_boundaries", {})
        if not boundaries and loom_layers:
            for layer in loom_layers:
                name = layer.get("name", "")
                cannot = layer.get("cannot_import", [])
                boundaries[name] = {"forbidden_imports": cannot, "path": layer.get("path", "")}

        content = template.render(
            project_type=structure.get("project_type", "unknown"),
            architecture=structure.get("architecture", []),
            boundaries=boundaries,
            src_root=structure.get("src_root", "."),
            loom_layers=loom_layers,
            loom_boundary_rules=loom_arch.get("boundary_rules", []),
            loom_import_aliases=loom_arch.get("import_aliases", {}),
        )
        self._write_md("architecture.md", content)

    def _generate_naming(self, scan_result: dict[str, Any]) -> None:
        template = self.env.get_template("naming.md.j2")
        code = scan_result.get("code", {})
        content = template.render(
            file_naming=code.get("file_naming", {}),
            code_naming=code.get("code_naming", {}),
            suffix_patterns=code.get("suffix_patterns", []),
            prefix_patterns=code.get("prefix_patterns", []),
            import_aliases=code.get("import_aliases", {}),
        )
        self._write_md("naming.md", content)

    def _generate_directory_map(self, scan_result: dict[str, Any]) -> None:
        template = self.env.get_template("directory_map.md.j2")
        structure = scan_result.get("structure", {})
        content = template.render(
            tree=structure.get("directory_tree", {}),
            src_root=structure.get("src_root", "."),
            project_type=structure.get("project_type", "unknown"),
        )
        self._write_md("directory-map.md", content)

    def _generate_stack(self, scan_result: dict[str, Any]) -> None:
        deps = scan_result.get("deps", {})
        stack_data = {
            "ecosystem": deps.get("ecosystem", "unknown"),
            "package_manager": deps.get("package_manager", "unknown"),
            "dependency_files": deps.get("dependency_files", []),
            "stack_summary": deps.get("stack_summary", {}),
            "total_dependencies": len(deps.get("dependencies", [])),
        }
        self._write_json("stack.json", stack_data)

    def _generate_rules(self, scan_result: dict[str, Any]) -> None:
        structure = scan_result.get("structure", {})
        code = scan_result.get("code", {})

        rules: dict[str, Any] = {
            "naming": {
                "files": {},
                "code": {},
            },
            "architecture": {
                "layer_boundaries": structure.get("layer_boundaries", {}),
                "patterns": structure.get("architecture", []),
            },
        }

        # File naming rules
        file_naming = code.get("file_naming", {})
        if file_naming.get("dominant_style"):
            rules["naming"]["files"]["dominant_style"] = file_naming["dominant_style"]

        # Suffix patterns as rules
        suffix_patterns = code.get("suffix_patterns", [])
        if suffix_patterns:
            rules["naming"]["files"]["suffix_patterns"] = [
                {"suffix": sp["suffix"], "pattern": sp["pattern"]} for sp in suffix_patterns
            ]

        # Prefix patterns as rules
        prefix_patterns = code.get("prefix_patterns", [])
        if prefix_patterns:
            rules["naming"]["files"]["prefix_patterns"] = [
                {"prefix": pp["prefix"], "pattern": pp["pattern"], "description": pp["description"]}
                for pp in prefix_patterns
            ]

        # Code naming rules
        code_naming = code.get("code_naming", {})
        rules["naming"]["code"] = code_naming

        # Import aliases
        aliases = code.get("import_aliases", {})
        if aliases:
            rules["imports"] = {"aliases": aliases}

        self._write_json("rules.json", rules)

    def _generate_plans_summary(self, scan_result: dict[str, Any]) -> None:
        docs = scan_result.get("docs", {})
        doc_list = docs.get("docs", [])
        plans = [d for d in doc_list if d["type"] == "plan"]
        arch_docs = [d for d in doc_list if d["type"] == "architecture"]

        lines: list[str] = ["# Project Plans & Documentation Summary\n"]

        if arch_docs:
            lines.append("## Architecture Documentation\n")
            for doc in arch_docs:
                title = doc["title"] or doc["path"]
                lines.append(f"- **{title}** (`{doc['path']}`, {doc['size_kb']}KB)")
                if doc["sections"]:
                    for section in doc["sections"][:5]:
                        lines.append(f"  - {section}")
            lines.append("")

        if plans:
            # Separate active from completed plans
            active_plans = []
            completed_plans = []
            for plan in plans:
                items = plan.get("status_items", [])
                if items:
                    pending = sum(1 for s in items if s["status"] in ("pending", "partial"))
                    if pending == 0:
                        completed_plans.append(plan)
                    else:
                        active_plans.append(plan)
                else:
                    active_plans.append(plan)

            if active_plans:
                lines.append("## Active Plans\n")
                for plan in active_plans:
                    self._render_plan(plan, lines)

            if completed_plans:
                lines.append("## Completed Plans\n")
                for plan in completed_plans:
                    self._render_plan(plan, lines)

        # Other doc types summary
        by_type = docs.get("by_type", {})
        other_types = {k: v for k, v in by_type.items() if k not in {"plan", "architecture"}}
        if other_types:
            lines.append("## Other Documentation\n")
            for doc_type, count in sorted(other_types.items()):
                lines.append(f"- **{doc_type}**: {count} file(s)")
            lines.append("")

        self._write_md("plans-summary.md", "\n".join(lines))

    def _render_plan(self, plan: dict[str, Any], lines: list[str]) -> None:
        """Render a single plan entry into lines."""
        lines.append(f"### {plan['title'] or plan['path']}")
        lines.append(f"Path: `{plan['path']}` ({plan['size_kb']}KB)\n")

        if plan["status_items"]:
            done = sum(1 for s in plan["status_items"] if s["status"] == "done")
            pending = sum(1 for s in plan["status_items"] if s["status"] == "pending")
            partial = sum(1 for s in plan["status_items"] if s["status"] == "partial")
            lines.append(f"Status: {done} done, {partial} in-progress, {pending} pending\n")

            for item in plan["status_items"]:
                icon = {"done": "[x]", "pending": "[ ]", "partial": "[-]"}.get(
                    item["status"], "[ ]"
                )
                lines.append(f"- {icon} {item['name']}")
            lines.append("")

        if plan["sections"]:
            lines.append("Sections:")
            for section in plan["sections"][:8]:
                lines.append(f"  - {section}")
            lines.append("")
