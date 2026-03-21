"""Structure scanner: project type, architecture, directory tree with semantic annotations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry, get_scorer
from loom_context.knowledge.models import ScoringEvidence
from loom_context.scanners.base import BaseScanner
from loom_context.security.filter import FileFilter

_registry = get_registry()

# Backward-compatible aliases (now served from Knowledge Registry)
DIR_ANNOTATIONS = _registry.get_all_directory_annotations()


class StructureScanner(BaseScanner):
    """Scans project structure to detect type, architecture, and annotate directories."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        super().__init__(root, file_filter)
        self._file_count: dict[str, int] = {}

    def scan(self) -> dict[str, Any]:
        project_type = self._detect_project_type()
        src_root = self._find_src_root()
        top_dirs = self._get_top_dirs(src_root)
        architecture, arch_confidence = self._detect_architecture(top_dirs)
        directory_tree = self._build_annotated_tree(src_root, max_depth=4)
        boundaries = self._get_boundary_rules(architecture)

        # Detect language from project type
        lang_info = _registry.get_language_for_project_type(project_type)
        language = lang_info.name if lang_info else ""

        # Monorepo detection
        is_monorepo, workspaces = self._detect_monorepo()

        return {
            "project_type": project_type,
            "language": language,
            "architecture": architecture,
            "architecture_confidence": arch_confidence,
            "src_root": str(src_root.relative_to(self.root)) if src_root != self.root else ".",
            "directory_tree": directory_tree,
            "layer_boundaries": boundaries,
            "total_files": sum(self._file_count.values()),
            "file_counts_by_dir": self._file_count,
            "is_monorepo": is_monorepo,
            "workspaces": workspaces,
        }

    def _detect_project_type(self) -> str:
        """Detect project type from marker files (fully data-driven)."""
        # Phase 1: Priority markers from markers.json (ordered, first match wins)
        for marker, ptype in _registry.get_priority_markers():
            if (self.root / marker).exists():
                return ptype

        # Phase 2: package.json dependency inspection
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json, encoding="utf-8") as f:
                    pkg = json.load(f)
                deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }
                for dep_name, ptype in _registry.get_package_json_dep_rules():
                    if dep_name in deps:
                        return ptype
                return "nodejs"
            except (json.JSONDecodeError, KeyError):
                return "nodejs"

        # Phase 3: app.json (Expo)
        app_json = self.root / "app.json"
        if app_json.exists():
            try:
                with open(app_json, encoding="utf-8") as f:
                    data = json.load(f)
                if "expo" in data:
                    return "react-native-expo"
            except (json.JSONDecodeError, KeyError):
                pass

        # Phase 4: Python fallback
        if (self.root / "pyproject.toml").exists() or (self.root / "setup.py").exists():
            return "python"

        # Phase 5: Terraform in subdirs
        if list(self.root.glob("**/*.tf"))[:1]:
            return "terraform"

        return "unknown"

    def _find_src_root(self) -> Path:
        """Find the main source directory."""
        for name in ["src", "lib", "app", "source"]:
            candidate = self.root / name
            if candidate.is_dir():
                return candidate
        return self.root

    def _get_top_dirs(self, src_root: Path) -> set[str]:
        """Get top-level directory names under src root."""
        dirs = set()
        if src_root.is_dir():
            for entry in src_root.iterdir():
                if entry.is_dir() and entry.name not in {".git", "node_modules", "__pycache__"}:
                    dirs.add(entry.name)

        # If only one dir exists and it looks like a Python package, look inside it
        if len(dirs) == 1:
            pkg_name = next(iter(dirs))
            pkg_dir = src_root / pkg_name
            init_file = pkg_dir / "__init__.py"
            if init_file.exists():
                for entry in pkg_dir.iterdir():
                    if entry.is_dir() and entry.name not in {"__pycache__"}:
                        dirs.add(entry.name)

        return dirs

    def _detect_architecture(
        self, top_dirs: set[str]
    ) -> tuple[list[str], dict[str, Any]]:
        """Detect architecture patterns using signal scoring."""
        scorer = get_scorer()
        patterns = _registry.get_architecture_patterns()

        # Collect all nested directories for deep scanning
        all_dirs = set(top_dirs)
        src_root = self._find_src_root()
        for d in top_dirs:
            dir_path = src_root / d if src_root != self.root else self.root / d
            if dir_path.is_dir():
                try:
                    for entry in dir_path.iterdir():
                        if entry.is_dir() and not entry.name.startswith("."):
                            all_dirs.add(entry.name)
                except PermissionError:
                    pass

        # Collect file suffixes from a sample of files
        file_suffixes: set[str] = set()
        suffix_patterns = [r.value for r in _registry.get_role_suffixes()]
        for f in list(self.file_filter.walk())[:500]:
            stem = f.stem
            for suffix in suffix_patterns:
                if stem.endswith(suffix):
                    file_suffixes.add(suffix)

        evidence = ScoringEvidence(
            directories=top_dirs,
            all_directories=all_dirs,
            file_suffixes=file_suffixes,
        )

        matches = scorer.score_all(patterns, evidence)
        detected = [m.name for m in matches]
        confidence = {
            m.name: {"score": m.score, "confidence": m.confidence}
            for m in matches
        }

        # Check for hexagonal within clean-arch (ports inside domain)
        if "clean-architecture" in detected:
            for d in top_dirs:
                ports_dir = self.root / "src" / d / "ports"
                if not ports_dir.exists():
                    ports_dir = self.root / d / "ports"
                if ports_dir.exists() and "hexagonal" not in detected:
                    detected.append("hexagonal")
                    confidence["hexagonal"] = {
                        "score": 0.5, "confidence": "medium",
                    }
                    break

        # Check for feature-based within presentation
        if "feature-based" not in detected:
            for d in top_dirs:
                features_path = self.root / "src" / d / "features"
                if not features_path.exists():
                    features_path = self.root / d / "features"
                if features_path.exists():
                    detected.append("feature-based")
                    confidence["feature-based"] = {
                        "score": 0.5, "confidence": "medium",
                    }
                    break

        if not detected:
            return ["flat"], {}
        return detected, confidence

    def _build_annotated_tree(
        self, root: Path, max_depth: int = 4, current_depth: int = 0
    ) -> dict[str, Any]:
        """Build annotated directory tree."""
        tree: dict[str, Any] = {}

        if current_depth >= max_depth or not root.is_dir():
            return tree

        try:
            entries = sorted(root.iterdir())
        except PermissionError:
            return tree

        for entry in entries:
            if entry.is_dir():
                if entry.name.startswith(".") or entry.name in {
                    "node_modules",
                    "__pycache__",
                    ".git",
                }:
                    continue
                if self.file_filter.is_excluded(entry):
                    continue

                rel = str(entry.relative_to(self.root))
                file_count = self._count_files(entry)
                self._file_count[rel] = file_count

                annotation = DIR_ANNOTATIONS.get(entry.name, "")
                subtree = self._build_annotated_tree(entry, max_depth, current_depth + 1)

                tree[entry.name] = {
                    "_annotation": annotation,
                    "_file_count": file_count,
                    **subtree,
                }

        return tree

    def _count_files(self, directory: Path) -> int:
        """Count files in a directory (non-recursive, fast)."""
        count = 0
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    count += 1
        except PermissionError:
            pass
        return count

    def _get_boundary_rules(self, architecture: list[str]) -> dict[str, Any]:
        """Get layer boundary rules for detected architecture."""
        boundaries: dict[str, Any] = {}
        for arch in architecture:
            rules = _registry.get_boundary_rules(arch)
            boundaries.update(rules)
        return boundaries

    def _detect_monorepo(self) -> tuple[bool, list[str]]:
        """Detect monorepo structure and list workspaces."""
        workspaces: list[str] = []

        # Check package.json workspaces
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json, encoding="utf-8") as f:
                    pkg = json.load(f)
                ws = pkg.get("workspaces", [])
                if isinstance(ws, list) and ws:
                    # Resolve glob patterns
                    for pattern in ws:
                        clean = pattern.rstrip("/*").rstrip("*")
                        ws_dir = self.root / clean
                        if ws_dir.is_dir():
                            for entry in sorted(ws_dir.iterdir()):
                                if entry.is_dir() and not entry.name.startswith("."):
                                    workspaces.append(str(entry.relative_to(self.root)))
                elif isinstance(ws, dict) and ws.get("packages"):
                    for pattern in ws["packages"]:
                        clean = pattern.rstrip("/*").rstrip("*")
                        ws_dir = self.root / clean
                        if ws_dir.is_dir():
                            for entry in sorted(ws_dir.iterdir()):
                                if entry.is_dir() and not entry.name.startswith("."):
                                    workspaces.append(str(entry.relative_to(self.root)))
            except (json.JSONDecodeError, OSError):
                pass

        # Check common monorepo dirs
        if not workspaces:
            for mono_dir in ["packages", "apps", "libs", "modules"]:
                candidate = self.root / mono_dir
                if candidate.is_dir():
                    for entry in sorted(candidate.iterdir()):
                        if entry.is_dir() and not entry.name.startswith("."):
                            workspaces.append(str(entry.relative_to(self.root)))

        # Check pnpm-workspace.yaml
        pnpm_ws = self.root / "pnpm-workspace.yaml"
        if not workspaces and pnpm_ws.exists():
            try:
                content = pnpm_ws.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip().lstrip("- ").strip("'\"").rstrip("/*")
                    if line and not line.startswith("#") and not line.startswith("packages"):
                        ws_dir = self.root / line
                        if ws_dir.is_dir():
                            for entry in sorted(ws_dir.iterdir()):
                                if entry.is_dir() and not entry.name.startswith("."):
                                    workspaces.append(str(entry.relative_to(self.root)))
            except OSError:
                pass

        return bool(workspaces), workspaces
