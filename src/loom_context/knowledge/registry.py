"""Knowledge Registry: central knowledge base for Loom detection."""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any, ClassVar, Optional

from loom_context.knowledge.models import (
    ArchitecturePattern,
    ArchitectureSignal,
    DocClassificationRule,
    FrameworkInfo,
    InfraServiceDef,
    LanguageInfo,
    NamingConventions,
    PackageInfo,
    PackageManagerInfo,
    RolePattern,
)

_DATA_DIR = Path(__file__).parent
_IS_MAC = platform.system() == "Darwin"


class KnowledgeRegistry:
    """Central knowledge base for Loom detection.

    Loads JSON data files lazily and caches them in memory.
    Supports local overrides from .loom/knowledge/ that extend the built-in data.
    """

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self._cache: dict[str, Any] = {}
        self._project_root = project_root

    def set_project_root(self, root: Path) -> None:
        """Set the project root for local overrides. Clears cache."""
        self._project_root = root
        self._cache.clear()

    # Files that CANNOT be overridden locally (security-critical)
    # - security.json: dir exclusions + secret patterns (weakening = data leak)
    # - infrastructure.json: contains shell commands (override = command injection)
    # - markers.json: project detection order (override = analysis confusion)
    _PROTECTED_FILES: ClassVar[set[str]] = {
        "security.json",
        "infrastructure.json",
        "markers.json",
    }

    # Max size for local override files (prevents JSON bomb DoS)
    _MAX_OVERRIDE_SIZE: ClassVar[int] = 1_048_576  # 1 MB

    # Max merge recursion depth (prevents stack overflow)
    _MAX_MERGE_DEPTH: ClassVar[int] = 20

    # --- JSON loading ---

    def _load_json(self, filename: str) -> Any:
        """Load a JSON file, merging local overrides if present.

        Priority: built-in data + local overrides (.loom/knowledge/).
        Local overrides EXTEND built-in data, they don't replace it.
        Security-critical files (security.json) cannot be overridden.
        """
        if filename in self._cache:
            return self._cache[filename]

        # Guard: prevent path traversal in filename
        if ".." in filename:
            msg = f"Invalid knowledge filename: {filename}"
            raise ValueError(msg)

        # Load built-in data
        path = _DATA_DIR / filename
        # Verify resolved path is within _DATA_DIR
        resolved = path.resolve()
        if not str(resolved).startswith(str(_DATA_DIR.resolve())):
            msg = f"Path traversal detected: {filename}"
            raise ValueError(msg)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Merge local overrides if project root is set
        # Security-critical files are NEVER overridable
        if self._project_root and filename not in self._PROTECTED_FILES:
            local_path = self._project_root / ".loom" / "knowledge" / filename
            if local_path.exists():
                try:
                    # Guard: file size limit (prevents JSON bomb DoS)
                    if local_path.stat().st_size > self._MAX_OVERRIDE_SIZE:
                        pass  # Silently ignore oversized files
                    else:
                        with open(local_path, encoding="utf-8") as f:
                            local_data = json.load(f)
                        data = self._safe_merge(data, local_data, depth=0)
                except (json.JSONDecodeError, OSError):
                    pass  # Ignore invalid local overrides

        self._cache[filename] = data
        return data

    @staticmethod
    def _safe_merge(base: Any, override: Any, depth: int = 0) -> Any:
        """Safe merge: override can only ADD, never change types or remove.

        Rules:
        - dict + dict → merge keys (new keys added, existing keys recurse)
        - list + list → append unique items from override
        - type mismatch → base wins (prevents type-confusion attacks)
        - scalar + scalar → override wins ONLY for new keys
        - max depth enforced (prevents stack overflow from deep nesting)
        """
        if depth >= KnowledgeRegistry._MAX_MERGE_DEPTH:
            return base  # Too deep — refuse to merge
        if isinstance(base, dict) and isinstance(override, dict):
            merged = dict(base)
            for key, value in override.items():
                if key in merged:
                    merged[key] = KnowledgeRegistry._safe_merge(
                        merged[key], value, depth + 1
                    )
                else:
                    merged[key] = value
            return merged
        if isinstance(base, list) and isinstance(override, list):
            # Append unique items — never shrink
            seen = {
                json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                for item in base
            }
            merged = list(base)
            for item in override:
                key = (
                    json.dumps(item, sort_keys=True)
                    if isinstance(item, dict)
                    else str(item)
                )
                if key not in seen:
                    merged.append(item)
                    seen.add(key)
            return merged
        # Type mismatch → base wins (prevents list→scalar or dict→scalar attacks)
        if type(base) is not type(override):
            return base
        # Same scalar type: override wins (for new keys added above)
        return override

    # --- Languages ---

    def get_language(self, ext_or_name: str) -> Optional[LanguageInfo]:
        """Get language info by extension (.py) or name (python)."""
        data = self._load_json("languages.json")
        # By name
        if ext_or_name in data:
            return self._build_language_info(ext_or_name, data[ext_or_name])
        # By extension
        for lang_id, lang_data in data.items():
            if ext_or_name in lang_data.get("extensions", []):
                return self._build_language_info(lang_id, lang_data)
        return None

    def get_all_extensions(self) -> set[str]:
        """Get all known code file extensions."""
        data = self._load_json("languages.json")
        extensions: set[str] = set()
        for lang_data in data.values():
            extensions.update(lang_data.get("extensions", []))
        return extensions

    def get_project_markers(self) -> list[tuple[str, str]]:
        """Get all project type markers: (marker_file, project_type)."""
        data = self._load_json("languages.json")
        markers: list[tuple[str, str]] = []
        for lang_data in data.values():
            ptype = lang_data.get("project_type", "")
            for marker in lang_data.get("markers", []):
                markers.append((marker, ptype))
            # Framework markers
            for fw_data in lang_data.get("frameworks", {}).values():
                for marker in fw_data.get("markers", []):
                    markers.append((marker, ptype))
        return markers

    def get_language_for_project_type(self, project_type: str) -> Optional[LanguageInfo]:
        """Get language info by project type identifier."""
        data = self._load_json("languages.json")
        for lang_id, lang_data in data.items():
            if lang_data.get("project_type", "") == project_type:
                return self._build_language_info(lang_id, lang_data)
        return None

    def _build_language_info(self, lang_id: str, data: dict[str, Any]) -> LanguageInfo:
        """Build a LanguageInfo from raw JSON data."""
        naming = None
        if "naming" in data:
            n = data["naming"]
            naming = NamingConventions(
                files=n.get("files", ""),
                classes=n.get("classes", ""),
                functions=n.get("functions", ""),
                methods=n.get("methods", ""),
                constants=n.get("constants", ""),
                modules=n.get("modules", ""),
            )

        pm_list = []
        for pm in data.get("package_managers", []):
            pm_list.append(
                PackageManagerInfo(
                    file=pm.get("file", ""),
                    lock=pm.get("lock"),
                    tool=pm.get("tool", ""),
                )
            )

        frameworks: dict[str, FrameworkInfo] = {}
        for fw_name, fw_data in data.get("frameworks", {}).items():
            frameworks[fw_name] = FrameworkInfo(
                name=fw_name,
                markers=fw_data.get("markers", []),
                src_roots=fw_data.get("src_roots", []),
                dir_exclusions=fw_data.get("dir_exclusions", []),
            )

        return LanguageInfo(
            name=data.get("name", lang_id),
            extensions=data.get("extensions", []),
            markers=data.get("markers", []),
            project_type=data.get("project_type", ""),
            package_managers=pm_list,
            naming=naming,
            comment_style=data.get("comment_style", ""),
            import_pattern=data.get("import_pattern", ""),
            class_pattern=data.get("class_pattern", ""),
            function_pattern=data.get("function_pattern", ""),
            constant_pattern=data.get("constant_pattern", ""),
            frameworks=frameworks,
        )

    # --- Packages / Ecosystems ---

    def get_package(self, name: str, ecosystem: str = "") -> Optional[PackageInfo]:
        """Get package info by name, optionally filtered by ecosystem."""
        data = self._load_json("ecosystems.json")
        ecosystems = data.get("ecosystems", {})

        if ecosystem:
            pkgs = ecosystems.get(ecosystem, {}).get("packages", {})
            if name in pkgs:
                p = pkgs[name]
                return PackageInfo(
                    name=name, category=p["category"], description=p.get("description", "")
                )
            return None

        # Search all ecosystems
        for eco_data in ecosystems.values():
            pkgs = eco_data.get("packages", {})
            if name in pkgs:
                p = pkgs[name]
                return PackageInfo(
                    name=name, category=p["category"], description=p.get("description", "")
                )
        return None

    def infer_package_category(self, name: str) -> str:
        """Infer category from package name using inference rules."""
        data = self._load_json("ecosystems.json")
        for rule in data.get("inference_rules", []):
            pattern = rule["pattern"]
            match_type = rule.get("match_type", "contains")
            lower_name = name.lower()
            pat_lower = pattern.lower()
            if (match_type == "startswith" and lower_name.startswith(pat_lower)) or (
                match_type == "endswith" and lower_name.endswith(pat_lower)
            ):
                return rule["category"]
            if match_type == "contains" and pat_lower in lower_name:
                return rule["category"]
        return "other"

    def categorize_package(self, name: str, ecosystem: str = "") -> tuple[str, str]:
        """Categorize a package: returns (category, description)."""
        info = self.get_package(name, ecosystem)
        if info:
            return info.category, info.description
        return self.infer_package_category(name), ""

    # --- Architectures ---

    def get_architecture_patterns(self) -> dict[str, ArchitecturePattern]:
        """Get all architecture patterns."""
        data = self._load_json("architectures.json")
        patterns: dict[str, ArchitecturePattern] = {}
        for pid, pdata in data.get("patterns", {}).items():
            signals = []
            for s in pdata.get("signals", []):
                signals.append(
                    ArchitectureSignal(
                        type=s.get("type", ""),
                        pattern=s.get("pattern", ""),
                        patterns=s.get("patterns", []),
                        weight=s.get("weight", 0.0),
                        depth=s.get("depth", "any"),
                        ecosystem=s.get("ecosystem", ""),
                    )
                )
            boundary_rules: dict[str, dict[str, list[str]]] = {}
            for layer, rules in pdata.get("boundary_rules", {}).items():
                boundary_rules[layer] = {"forbidden_imports": rules.get("forbidden_imports", [])}

            patterns[pid] = ArchitecturePattern(
                name=pid,
                display_name=pdata.get("name", pid),
                signals=signals,
                confidence_threshold=pdata.get("confidence_threshold", 0.5),
                boundary_rules=boundary_rules,
                legacy_dir_sets=pdata.get("legacy_dir_sets", []),
            )
        return patterns

    def get_boundary_rules(self, architecture: str) -> dict[str, dict[str, list[str]]]:
        """Get boundary rules for a specific architecture."""
        patterns = self.get_architecture_patterns()
        pattern = patterns.get(architecture)
        if pattern:
            return pattern.boundary_rules
        return {}

    # --- Directories ---

    def get_directory_annotation(self, name: str) -> Optional[str]:
        """Get semantic annotation for a directory name."""
        data = self._load_json("directories.json")
        return data.get("annotations", {}).get(name)

    def get_all_directory_annotations(self) -> dict[str, str]:
        """Get all directory annotations."""
        data = self._load_json("directories.json")
        return dict(data.get("annotations", {}))

    # --- Security ---

    def get_dir_exclusions(self) -> set[str]:
        """Get hardcoded directory exclusions."""
        data = self._load_json("security.json")
        return set(data.get("dir_exclusions", []))

    def get_secret_patterns(self) -> list[str]:
        """Get secret file patterns."""
        data = self._load_json("security.json")
        return list(data.get("secret_patterns", []))

    # --- Infrastructure ---

    def get_infra_service(self, package_name: str) -> Optional[InfraServiceDef]:
        """Get infrastructure service for a package dependency."""
        data = self._load_json("infrastructure.json")
        mapping = data.get("package_mapping", {})
        service_id = mapping.get(package_name)
        if not service_id:
            return None
        services = data.get("services", {})
        svc = services.get(service_id)
        if not svc:
            return None
        return InfraServiceDef(
            name=svc.get("name", ""),
            category=svc.get("category", ""),
            default_port=svc.get("default_port", 0),
            install_cmd_mac=svc.get("install_cmd_mac", ""),
            install_cmd_linux=svc.get("install_cmd_linux", ""),
            start_cmd_mac=svc.get("start_cmd_mac", ""),
            start_cmd_linux=svc.get("start_cmd_linux", ""),
            stop_cmd_mac=svc.get("stop_cmd_mac", ""),
            stop_cmd_linux=svc.get("stop_cmd_linux", ""),
            status_cmd=svc.get("status_cmd", ""),
            docker_cmd=svc.get("docker_cmd", ""),
            config_env=svc.get("config_env", ""),
            config_hint=svc.get("config_hint", ""),
            binaries=svc.get("binaries", []),
        )

    def get_all_infra_services(self) -> dict[str, InfraServiceDef]:
        """Get all infrastructure service definitions."""
        data = self._load_json("infrastructure.json")
        result: dict[str, InfraServiceDef] = {}
        for svc_id, svc in data.get("services", {}).items():
            result[svc_id] = InfraServiceDef(
                name=svc.get("name", ""),
                category=svc.get("category", ""),
                default_port=svc.get("default_port", 0),
                install_cmd_mac=svc.get("install_cmd_mac", ""),
                install_cmd_linux=svc.get("install_cmd_linux", ""),
                start_cmd_mac=svc.get("start_cmd_mac", ""),
                start_cmd_linux=svc.get("start_cmd_linux", ""),
                stop_cmd_mac=svc.get("stop_cmd_mac", ""),
                stop_cmd_linux=svc.get("stop_cmd_linux", ""),
                status_cmd=svc.get("status_cmd", ""),
                docker_cmd=svc.get("docker_cmd", ""),
                config_env=svc.get("config_env", ""),
                config_hint=svc.get("config_hint", ""),
                binaries=svc.get("binaries", []),
            )
        return result

    def get_infra_install_cmd(self, svc: InfraServiceDef) -> str:
        """Get install command for current platform."""
        return svc.install_cmd_mac if _IS_MAC else svc.install_cmd_linux

    def get_infra_start_cmd(self, svc: InfraServiceDef) -> str:
        """Get start command for current platform."""
        return svc.start_cmd_mac if _IS_MAC else svc.start_cmd_linux

    def get_infra_stop_cmd(self, svc: InfraServiceDef) -> str:
        """Get stop command for current platform."""
        return svc.stop_cmd_mac if _IS_MAC else svc.stop_cmd_linux

    # --- Roles ---

    def get_role_suffixes(self) -> list[RolePattern]:
        """Get architectural role suffixes."""
        data = self._load_json("roles.json")
        return [
            RolePattern(
                value=r["value"],
                description=r.get("description", ""),
                type="suffix",
                languages=r.get("languages", []),
            )
            for r in data.get("suffixes", [])
        ]

    def get_role_prefixes(self) -> list[RolePattern]:
        """Get architectural role prefixes."""
        data = self._load_json("roles.json")
        return [
            RolePattern(
                value=r["value"],
                description=r.get("description", ""),
                type="prefix",
                languages=r.get("languages", []),
            )
            for r in data.get("prefixes", [])
        ]

    # --- Documentation ---

    def get_doc_filename_rules(self) -> list[DocClassificationRule]:
        """Get documentation filename classification rules."""
        data = self._load_json("docs.json")
        return [
            DocClassificationRule(
                pattern=r["pattern"],
                doc_type=r["doc_type"],
                source="filename",
            )
            for r in data.get("filename_rules", [])
        ]

    def get_doc_path_rules(self) -> list[DocClassificationRule]:
        """Get documentation path classification rules."""
        data = self._load_json("docs.json")
        return [
            DocClassificationRule(
                pattern=r["pattern"],
                doc_type=r["doc_type"],
                source="path",
            )
            for r in data.get("path_rules", [])
        ]

    # --- Design Patterns ---

    def get_design_patterns(self) -> dict[str, Any]:
        """Get all design pattern definitions with signals."""
        data = self._load_json("design_patterns.json")
        return dict(data.get("patterns", {}))

    def get_design_pattern_categories(self) -> dict[str, Any]:
        """Get design pattern category definitions."""
        data = self._load_json("design_patterns.json")
        return dict(data.get("categories", {}))

    def get_design_pattern(self, name: str) -> Optional[dict[str, Any]]:
        """Get a specific design pattern definition."""
        patterns = self.get_design_patterns()
        return patterns.get(name)

    # --- Code Smells ---

    def get_code_smells(self) -> dict[str, Any]:
        """Get all code smell definitions."""
        data = self._load_json("code_smells.json")
        return dict(data.get("smells", {}))

    def get_code_smell(self, name: str) -> Optional[dict[str, Any]]:
        """Get a specific code smell definition."""
        return self.get_code_smells().get(name)

    def get_code_smell_categories(self) -> dict[str, str]:
        """Get code smell categories."""
        data = self._load_json("code_smells.json")
        return dict(data.get("categories", {}))

    # --- Stop Words ---

    def get_stop_words(self) -> set[str]:
        """Get combined stop words (EN + ES)."""
        data = self._load_json("stop_words.json")
        words: set[str] = set()
        words.update(data.get("en", []))
        words.update(data.get("es", []))
        return words

    # --- Project Markers ---

    def get_priority_markers(self) -> list[tuple[str, str]]:
        """Get ordered project markers: (marker_file, project_type)."""
        data = self._load_json("markers.json")
        return [(m["marker"], m["project_type"]) for m in data.get("priority_markers", [])]

    def get_package_json_dep_rules(self) -> list[tuple[str, str]]:
        """Get package.json dependency → project_type rules."""
        data = self._load_json("markers.json")
        return [(r["dep"], r["project_type"]) for r in data.get("package_json_deps", [])]

    # --- Domains ---

    def get_domain(self, name: str) -> Optional[dict[str, Any]]:
        """Get domain definition by name."""
        # Guard: prevent path traversal (e.g., "../../etc/passwd")
        if not name.isalnum() and not all(c.isalnum() or c in "-_" for c in name):
            return None
        if ".." in name or "/" in name or "\\" in name:
            return None
        try:
            return self._load_json(f"domains/{name}.json")
        except FileNotFoundError:
            return None

    def get_available_domains(self) -> list[str]:
        """List available domain names."""
        domains_dir = _DATA_DIR / "domains"
        if not domains_dir.is_dir():
            return []
        return [f.stem for f in sorted(domains_dir.glob("*.json"))]
