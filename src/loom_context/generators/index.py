"""Index generator: creates the master index.json for AI agents."""

from __future__ import annotations

from typing import Any


def generate_quick_rules(scan_result: dict[str, Any]) -> list[str]:
    """Generate quick rules from scan results for immediate AI context."""
    rules: list[str] = []

    # Architecture boundaries
    boundaries = scan_result.get("structure", {}).get("layer_boundaries", {})
    for layer, config in boundaries.items():
        forbidden = config.get("forbidden_imports", [])
        if forbidden:
            rules.append(f"Layer boundary: {layer} MUST NOT import from {', '.join(forbidden)}")

    # Naming conventions
    code_naming = scan_result.get("code", {}).get("code_naming", {})
    if "interfaces" in code_naming:
        prefix = code_naming["interfaces"].get("prefix", "none")
        if prefix != "none":
            rules.append(f"Interfaces MUST have '{prefix}' prefix (e.g., {prefix}UserRepository)")

    prefix_patterns = scan_result.get("code", {}).get("prefix_patterns", [])
    for p in prefix_patterns:
        if p["prefix"] == "use" and p["count"] >= 3:
            rules.append("React hooks MUST have 'use' prefix (e.g., useLogoutApp)")

    # File naming
    file_naming = scan_result.get("code", {}).get("file_naming", {})
    if file_naming.get("dominant_style") and file_naming.get("confidence", 0) > 0.5:
        rules.append(
            f"Files use {file_naming['dominant_style']} naming "
            f"({int(file_naming['confidence'] * 100)}% of codebase)"
        )

    # Suffix patterns
    suffix_patterns = scan_result.get("code", {}).get("suffix_patterns", [])
    for sp in suffix_patterns[:5]:
        rules.append(f"{sp['suffix']} files follow pattern: {sp['pattern']}")

    return rules


class IndexGenerator:
    """Generates the master index.json."""

    def generate(self, scan_result: dict[str, Any], version: str) -> dict[str, Any]:
        structure = scan_result.get("structure", {})
        deps = scan_result.get("deps", {})
        code = scan_result.get("code", {})
        docs = scan_result.get("docs", {})

        # Language: prefer structure.language (from registry), fallback to heuristic
        language = structure.get("language", "") or self._detect_language(
            structure.get("project_type", "unknown"), code
        )

        # Build runtime string
        runtime = self._build_runtime(structure.get("project_type", ""), deps)

        project: dict[str, Any] = {
            "name": structure.get("project_name", ""),
            "type": structure.get("project_type", "unknown"),
            "architecture": structure.get("architecture", []),
            "language": language,
            "runtime": runtime,
        }

        # Monorepo info
        if structure.get("is_monorepo"):
            project["is_monorepo"] = True
            project["workspaces"] = structure.get("workspaces", [])

        # Architecture confidence
        arch_conf = structure.get("architecture_confidence", {})
        if arch_conf:
            project["architecture_confidence"] = arch_conf

        # Ecosystem
        ecosystem = deps.get("ecosystem", "unknown")
        if ecosystem != "unknown":
            project["ecosystem"] = ecosystem

        # Domain
        domain = scan_result.get("domain", "unknown")
        if domain != "unknown":
            project["domain"] = domain
            project["domain_confidence"] = scan_result.get("domain_confidence", 0.0)
            domain_details = scan_result.get("domain_details", {})
            if domain_details.get("active"):
                project["domain_active"] = domain_details["active"]

        return {
            "loom_version": version,
            "project": project,
            "context_files": {
                "architecture": ".context/architecture.md",
                "naming": ".context/naming.md",
                "directory_map": ".context/directory-map.md",
                "stack": ".context/stack.json",
                "rules": ".context/rules.json",
                "plans_summary": ".context/plans-summary.md",
            },
            "agents_md": docs.get("agents_md"),
            "quick_rules": generate_quick_rules(scan_result),
            "stats": {
                "total_files": structure.get("total_files", 0),
                "total_code_files": code.get("total_code_files", 0),
                "total_docs": docs.get("doc_count", 0),
                "total_dependencies": len(deps.get("dependencies", [])),
            },
        }

    def _detect_language(self, project_type: str, code: dict[str, Any]) -> str:
        ts_types = {"react-native-expo", "react-native", "nextjs", "angular"}
        if project_type in ts_types:
            return "TypeScript"
        if project_type in {"react", "nodejs", "vite", "webpack"}:
            return "TypeScript/JavaScript"
        if project_type == "python":
            return "Python"
        if project_type == "rust":
            return "Rust"
        if project_type == "go":
            return "Go"
        return "Unknown"

    def _build_runtime(self, project_type: str, deps: dict[str, Any]) -> str:
        parts: list[str] = []
        stack = deps.get("stack_summary", {})

        if "ui-framework" in stack:
            parts.extend(stack["ui-framework"][:3])
        if "platform" in stack:
            parts.extend(stack["platform"][:2])

        if parts:
            return " + ".join(parts)

        type_runtimes = {
            "python": "Python",
            "rust": "Rust (Cargo)",
            "go": "Go",
            "nodejs": "Node.js",
        }
        return type_runtimes.get(project_type, project_type)
