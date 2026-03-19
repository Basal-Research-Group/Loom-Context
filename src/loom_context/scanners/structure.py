"""Structure scanner: project type, architecture, directory tree with semantic annotations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from loom_context.scanners.base import BaseScanner
from loom_context.security.filter import FileFilter

# Project type detection: (marker_file, json_key_reserved, project_type)
PROJECT_MARKERS: list[tuple[str, Optional[str], str]] = [
    # Terraform (check early — often combined with other stacks)
    ("main.tf", None, "terraform"),
    # Monorepo tools (check before framework-specific markers)
    ("turbo.json", None, "turborepo"),
    ("nx.json", None, "nx-monorepo"),
    ("lerna.json", None, "lerna-monorepo"),
    # Mobile
    ("app.config.js", None, "react-native-expo"),
    ("app.config.ts", None, "react-native-expo"),
    ("expo-env.d.ts", None, "react-native-expo"),
    ("react-native.config.js", None, "react-native"),
    # Web frameworks
    ("next.config.js", None, "nextjs"),
    ("next.config.ts", None, "nextjs"),
    ("next.config.mjs", None, "nextjs"),
    ("nuxt.config.ts", None, "nuxt"),
    ("angular.json", None, "angular"),
    ("svelte.config.js", None, "svelte"),
    ("astro.config.mjs", None, "astro"),
    # Build tools
    ("vite.config.ts", None, "vite"),
    ("vite.config.js", None, "vite"),
    ("webpack.config.js", None, "webpack"),
    # Backend languages
    ("Cargo.toml", None, "rust"),
    ("go.mod", None, "go"),
    ("pom.xml", None, "java-maven"),
    ("build.gradle", None, "java-gradle"),
    ("Gemfile", None, "ruby"),
    ("composer.json", None, "php"),
    ("Package.swift", None, "swift"),
    # Infrastructure
    ("Dockerfile", None, "docker"),
    ("serverless.yml", None, "serverless"),
    ("serverless.ts", None, "serverless"),
    ("cdk.json", None, "aws-cdk"),
    ("pulumi.yaml", None, "pulumi"),
]

# Architecture pattern detection based on top-level src directories
ARCHITECTURE_PATTERNS: dict[str, list[set[str]]] = {
    "clean-architecture": [
        {"domain", "infrastructure", "presentation"},
        {"domain", "infra", "presentation"},
        {"domain", "infrastructure", "ui"},
        {"domain", "data", "presentation"},
    ],
    "hexagonal": [
        {"ports", "adapters"},
        {"domain", "ports", "adapters"},
    ],
    "mvc": [
        {"models", "views", "controllers"},
        {"model", "view", "controller"},
    ],
    "mvvm": [
        {"models", "views", "viewmodels"},
        {"model", "view", "viewmodel"},
    ],
    "feature-based": [
        {"features"},
        {"modules"},
    ],
    "layered": [
        {"controllers", "services", "repositories"},
        {"api", "services", "data"},
    ],
    "nestjs-modular": [
        {"modules", "common"},
        {"modules", "config"},
        {"health", "modules"},
    ],
    "pipeline": [
        {"scanners", "generators"},
        {"scanners", "generators", "auditors"},
        {"parsers", "transformers", "emitters"},
        {"extractors", "processors", "loaders"},
        {"collectors", "analyzers", "reporters"},
    ],
    "terraform": [
        {"modules", "environments"},
        {"modules", "providers"},
    ],
}

# Semantic annotations for directory names
DIR_ANNOTATIONS: dict[str, str] = {
    "domain": "Domain layer - entities, ports, use cases (pure business logic)",
    "core": "Core layer - orchestration, DI, services, state management",
    "infrastructure": "Infrastructure layer - DB, external services, concrete implementations",
    "infra": "Infrastructure layer - DB, external services, concrete implementations",
    "presentation": "Presentation layer - UI, screens, components, navigation",
    "ui": "UI layer - components, screens, views",
    "entities": "Domain entities/models",
    "models": "Data models",
    "ports": "Port interfaces (dependency contracts)",
    "adapters": "Adapter implementations (Ports & Adapters pattern)",
    "repositories": "Data access layer (repository interfaces or implementations)",
    "services": "Service layer",
    "useCases": "Application use cases",
    "use-cases": "Application use cases",
    "use_cases": "Application use cases",
    "controllers": "Request controllers",
    "middleware": "Middleware handlers",
    "hooks": "Custom hooks",
    "components": "UI components",
    "features": "Feature modules",
    "screens": "App screens/pages",
    "views": "View layer",
    "viewModels": "View models (MVVM pattern)",
    "viewmodels": "View models (MVVM pattern)",
    "navigation": "App navigation/routing",
    "routing": "App routing configuration",
    "routes": "Route definitions",
    "state": "State management",
    "store": "State store / persistence layer",
    "slices": "State slices",
    "actions": "State actions/thunks",
    "selectors": "State selectors/queries",
    "di": "Dependency injection configuration",
    "bootstrap": "Application initialization/bootstrap",
    "config": "Configuration files",
    "constants": "Constants and static values",
    "types": "Type definitions",
    "interfaces": "Interface definitions",
    "dtos": "Data Transfer Objects",
    "mappers": "Data transformation mappers",
    "schemas": "Database/validation schemas",
    "definitions": "Schema/table definitions",
    "migrations": "Database migrations",
    "seeds": "Database seed data",
    "scanners": "Input scanners (pipeline pattern)",
    "generators": "Output generators (pipeline pattern)",
    "auditors": "Rule validators (pipeline pattern)",
    "parsers": "Input parsers (pipeline pattern)",
    "transformers": "Data transformers (pipeline pattern)",
    "emitters": "Output emitters (pipeline pattern)",
    "extractors": "Data extractors (ETL pattern)",
    "processors": "Data processors (ETL pattern)",
    "loaders": "Data loaders (ETL pattern)",
    "utils": "Utility functions",
    "helpers": "Helper functions",
    "lib": "Shared library code",
    "common": "Shared/common code",
    "shared": "Shared modules",
    "tests": "Test files",
    "__tests__": "Test files",
    "test": "Test files",
    "spec": "Test specifications",
    "fixtures": "Test fixtures",
    "mocks": "Mock implementations",
    "docs": "Documentation",
    "scripts": "Build/utility scripts",
    "assets": "Static assets (images, fonts, etc.)",
    "images": "Image assets",
    "fonts": "Font files",
    "animations": "Animation files",
    "styles": "Style definitions",
    "theme": "Theme/design tokens",
    "tokens": "Design tokens",
    "i18n": "Internationalization",
    "locales": "Locale/translation files",
    "providers": "Context/service providers",
    "contexts": "React contexts or similar",
    "guards": "Auth/validation guards",
    "pipes": "Data transformation pipes",
    "decorators": "Decorators/annotations",
    "events": "Event system",
    "bus": "Message/event bus",
    "monitoring": "Observability, logging, telemetry",
    "logging": "Logging system",
    "telemetry": "Telemetry/analytics",
    "tracking": "Event tracking",
    "error": "Error handling",
    "devtools": "Development tools/debug utilities",
    "strategies": "Strategy pattern implementations",
    "filters": "Data filters",
    "rules": "Business/validation rules",
    "registries": "Service/component registries",
    "runners": "Execution runners",
    "engine": "Processing engine",
    "orchestration": "Flow orchestration",
    "scenario": "Scenario/flow processing",
    "tts": "Text-to-speech",
    "voice": "Voice system",
    "tutor": "Tutor/assistant system",
    "auth": "Authentication",
    "onboarding": "User onboarding flow",
    "profile": "User profile",
    "layouts": "Layout components",
    "containers": "Container components",
    "compound": "Compound/composite components",
    "environments": "Terraform environments (dev/staging/prod)",
    "tfmodules": "Terraform modules",
    "stacks": "Infrastructure stacks",
    "lambdas": "AWS Lambda functions",
    "functions": "Cloud functions",
    "policies": "IAM/security policies",
    "e2e": "End-to-end tests",
    "health": "Health check endpoints",
    "interceptors": "Request interceptors",
    "dto": "Data transfer objects",
    "renderers": "UI renderers (Strategy pattern)",
    "data": "Data layer",
    "sources": "Data sources",
    "db": "Database",
    "sql": "SQL files",
    "api": "API layer",
    "graphql": "GraphQL schema/resolvers",
    "rest": "REST API",
    "plugins": "Plugin system",
    "modules": "Application modules",
    "background": "Background task processing",
    "normalized": "Normalized data structures",
}

# Layer boundary rules for known architectures
BOUNDARY_RULES: dict[str, dict[str, dict[str, list[str]]]] = {
    "clean-architecture": {
        "domain": {"forbidden_imports": ["core", "infrastructure", "infra", "presentation", "ui"]},
        "core": {"forbidden_imports": ["infrastructure", "infra", "presentation", "ui"]},
        "infrastructure": {"forbidden_imports": ["presentation", "ui"]},
        "presentation": {"forbidden_imports": ["infrastructure", "infra"]},
    },
    "hexagonal": {
        "domain": {"forbidden_imports": ["adapters", "infrastructure", "infra"]},
        "ports": {"forbidden_imports": ["adapters", "infrastructure", "infra"]},
    },
    "mvc": {
        "models": {"forbidden_imports": ["views", "controllers"]},
    },
    "layered": {
        "controllers": {"forbidden_imports": ["repositories"]},
        "repositories": {"forbidden_imports": ["controllers", "services"]},
    },
}


class StructureScanner(BaseScanner):
    """Scans project structure to detect type, architecture, and annotate directories."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        super().__init__(root, file_filter)
        self._file_count: dict[str, int] = {}

    def scan(self) -> dict[str, Any]:
        project_type = self._detect_project_type()
        src_root = self._find_src_root()
        top_dirs = self._get_top_dirs(src_root)
        architecture = self._detect_architecture(top_dirs)
        directory_tree = self._build_annotated_tree(src_root, max_depth=4)
        boundaries = self._get_boundary_rules(architecture)

        # Monorepo detection
        is_monorepo, workspaces = self._detect_monorepo()

        return {
            "project_type": project_type,
            "architecture": architecture,
            "src_root": str(src_root.relative_to(self.root)) if src_root != self.root else ".",
            "directory_tree": directory_tree,
            "layer_boundaries": boundaries,
            "total_files": sum(self._file_count.values()),
            "file_counts_by_dir": self._file_count,
            "is_monorepo": is_monorepo,
            "workspaces": workspaces,
        }

    def _detect_project_type(self) -> str:
        """Detect project type from marker files."""
        for marker, _json_key, ptype in PROJECT_MARKERS:
            if (self.root / marker).exists():
                return ptype

        # Check for Terraform in subdirs (e.g., infra/main.tf)
        if list(self.root.glob("**/*.tf"))[:1]:
            return "terraform"

        # Check package.json for framework detection
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json, encoding="utf-8") as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react-native" in deps:
                    return "react-native"
                if "@nestjs/core" in deps:
                    return "nestjs"
                if "react" in deps:
                    return "react"
                if "@angular/core" in deps:
                    return "angular"
                return "nodejs"
            except (json.JSONDecodeError, KeyError):
                return "nodejs"

        # Check app.json for expo
        app_json = self.root / "app.json"
        if app_json.exists():
            try:
                with open(app_json, encoding="utf-8") as f:
                    data = json.load(f)
                if "expo" in data:
                    return "react-native-expo"
            except (json.JSONDecodeError, KeyError):
                pass

        # Python
        if (self.root / "pyproject.toml").exists() or (self.root / "setup.py").exists():
            return "python"

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

    def _detect_architecture(self, top_dirs: set[str]) -> list[str]:
        """Detect architecture patterns from directory names."""
        detected = []
        normalized = {d.lower() for d in top_dirs}

        for pattern_name, dir_sets in ARCHITECTURE_PATTERNS.items():
            for required_dirs in dir_sets:
                if required_dirs.issubset(normalized):
                    detected.append(pattern_name)
                    break

        # Check for hexagonal within clean-arch (ports inside domain)
        if "clean-architecture" in detected:
            for d in top_dirs:
                ports_dir = self.root / "src" / d / "ports"
                if not ports_dir.exists():
                    ports_dir = self.root / d / "ports"
                if ports_dir.exists() and "hexagonal" not in detected:
                    detected.append("hexagonal")
                    break

        # Check for feature-based within presentation
        for d in top_dirs:
            features_path = self.root / "src" / d / "features"
            if not features_path.exists():
                features_path = self.root / d / "features"
            if features_path.exists() and "feature-based" not in detected:
                detected.append("feature-based")
                break

        return detected if detected else ["flat"]

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
            if arch in BOUNDARY_RULES:
                boundaries.update(BOUNDARY_RULES[arch])
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
