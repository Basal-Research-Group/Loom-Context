"""Dependency scanner: parses package managers and categorizes dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry
from loom_context.scanners.base import BaseScanner

_registry = get_registry()


class DependencyScanner(BaseScanner):
    """Scans dependency files and categorizes packages."""

    def scan(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "package_manager": "unknown",
            "ecosystem": "unknown",
            "dependency_files": [],
            "dependencies": [],
            "stack_summary": {},
        }

        # JS/TS — package.json
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            self._scan_package_json(pkg_json, result)

        # Python — pyproject.toml
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            self._scan_pyproject_toml(pyproject, result)

        # Python — requirements.txt
        req_txt = self.root / "requirements.txt"
        if req_txt.exists():
            self._scan_requirements_txt(req_txt, result)

        # Ruby — Gemfile
        gemfile = self.root / "Gemfile"
        if gemfile.exists():
            self._scan_gemfile(gemfile, result)

        # Rust — Cargo.toml
        cargo = self.root / "Cargo.toml"
        if cargo.exists():
            self._scan_cargo_toml(cargo, result)

        # Go — go.mod
        gomod = self.root / "go.mod"
        if gomod.exists():
            self._scan_go_mod(gomod, result)

        # Elixir — mix.exs
        mix_exs = self.root / "mix.exs"
        if mix_exs.exists():
            self._scan_mix_exs(mix_exs, result)

        # Java — pom.xml
        pom = self.root / "pom.xml"
        if pom.exists():
            self._scan_pom_xml(pom, result)

        # Java/Kotlin — build.gradle / build.gradle.kts
        for gradle_name in ["build.gradle", "build.gradle.kts"]:
            gradle = self.root / gradle_name
            if gradle.exists():
                self._scan_gradle(gradle, result)
                break

        # C# — *.csproj
        csproj_files = list(self.root.glob("*.csproj"))
        if csproj_files:
            self._scan_csproj(csproj_files[0], result)

        # Resolve ecosystem from package manager
        _pm_to_ecosystem = {
            "npm": "npm", "yarn": "npm", "pnpm": "npm", "bun": "npm",
            "pip": "pip", "poetry": "pip", "uv": "pip", "pipenv": "pip",
            "bundler": "gem",
            "cargo": "cargo",
            "go": "go",
            "hex": "hex",
            "maven": "maven", "gradle": "maven",
            "nuget": "nuget",
        }
        result["ecosystem"] = _pm_to_ecosystem.get(
            result["package_manager"], "unknown"
        )

        # Build stack summary
        summary: dict[str, list[str]] = {}
        for dep in result["dependencies"]:
            cat = dep["category"]
            version_str = (
                f"{dep['name']}@{dep['version']}" if dep["version"] else dep["name"]
            )
            summary.setdefault(cat, []).append(version_str)
        result["stack_summary"] = summary

        return result

    # --- JS/TS ---

    def _scan_package_json(self, path: Path, result: dict[str, Any]) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                pkg = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        result["dependency_files"].append("package.json")

        # Detect package manager
        if (self.root / "pnpm-lock.yaml").exists():
            result["package_manager"] = "pnpm"
        elif (self.root / "yarn.lock").exists():
            result["package_manager"] = "yarn"
        elif (self.root / "bun.lockb").exists():
            result["package_manager"] = "bun"
        elif (self.root / "package-lock.json").exists():
            result["package_manager"] = "npm"

        for name, version in pkg.get("dependencies", {}).items():
            result["dependencies"].append(self._categorize(name, version, dev=False))

        for name, version in pkg.get("devDependencies", {}).items():
            result["dependencies"].append(self._categorize(name, version, dev=True))

    # --- Python ---

    def _scan_pyproject_toml(self, path: Path, result: dict[str, Any]) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("pyproject.toml")
        if result["package_manager"] == "unknown":
            if (self.root / "poetry.lock").exists():
                result["package_manager"] = "poetry"
            elif (self.root / "uv.lock").exists():
                result["package_manager"] = "uv"
            else:
                result["package_manager"] = "pip"

        # Extract inline lists like: dependencies = ["click>=8.0", "rich"]
        self._parse_toml_inline_list(content, "dependencies", result, dev=False)

        # Parse line-by-line for sections like [tool.poetry.dependencies]
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                continue
            if stripped.startswith("["):
                in_deps = "dependencies" in stripped and "=" not in stripped
                continue
            if in_deps and stripped and not stripped.startswith("#"):
                # Skip TOML key assignments like 'dev = [' or 'key = value'
                if re.match(r"^\w+\s*=\s*[\[\"{]", stripped):
                    continue
                # Skip closing brackets
                if stripped in ("]", "},"):
                    continue
                self._parse_dep_line(stripped, result, dev=False)

    def _scan_requirements_txt(self, path: Path, result: dict[str, Any]) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("requirements.txt")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "pip"

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            for sep in ["==", ">=", "~=", "<=", "!="]:
                if sep in line:
                    name, version = line.split(sep, 1)
                    result["dependencies"].append(
                        self._categorize(name.strip(), version.strip(), dev=False)
                    )
                    break
            else:
                result["dependencies"].append(self._categorize(line, "", dev=False))

    # --- Ruby ---

    def _scan_gemfile(self, path: Path, result: dict[str, Any]) -> None:
        """Parse Gemfile for gem dependencies."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("Gemfile")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "bundler"

        # Match: gem 'name', '~> 1.0'  or  gem "name", ">= 2.0", "< 3.0"
        # Also: gem 'name' (no version)
        gem_pattern = re.compile(
            r"""^\s*gem\s+['"]([^'"]+)['"]"""
            r"""(?:\s*,\s*['"]([^'"]*)['"]\s*)?""",
        )

        in_test_group = False
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Track group blocks for dev detection
            if re.match(r"group\s+:(?:development|test)", stripped):
                in_test_group = True
            elif stripped == "end":
                in_test_group = False

            match = gem_pattern.match(stripped)
            if match:
                name = match.group(1)
                version = match.group(2) or ""
                # Clean version specifier
                version = version.lstrip("~> ").lstrip(">= ").lstrip("= ")
                result["dependencies"].append(
                    self._categorize(name, version, dev=in_test_group)
                )

    # --- Rust ---

    def _scan_cargo_toml(self, path: Path, result: dict[str, Any]) -> None:
        """Parse Cargo.toml for crate dependencies."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("Cargo.toml")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "cargo"

        # Parse [dependencies] and [dev-dependencies] sections
        section = ""
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("["):
                section = stripped.strip("[]").strip()
                continue

            if section in ("dependencies", "dev-dependencies"):
                dev = section == "dev-dependencies"
                # name = "version" or name = { version = "x" }
                m = re.match(r'(\w[\w-]*)\s*=\s*"([^"]*)"', stripped)
                if m:
                    result["dependencies"].append(
                        self._categorize(m.group(1), m.group(2), dev=dev)
                    )
                    continue
                # name = { version = "x", features = [...] }
                m = re.match(r'(\w[\w-]*)\s*=\s*\{', stripped)
                if m:
                    name = m.group(1)
                    ver_match = re.search(r'version\s*=\s*"([^"]*)"', stripped)
                    version = ver_match.group(1) if ver_match else ""
                    result["dependencies"].append(
                        self._categorize(name, version, dev=dev)
                    )

    # --- Go ---

    def _scan_go_mod(self, path: Path, result: dict[str, Any]) -> None:
        """Parse go.mod for module dependencies."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("go.mod")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "go"

        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            if stripped.startswith("require ("):
                in_require = True
                continue
            if stripped == ")" and in_require:
                in_require = False
                continue

            # Single-line: require github.com/gin-gonic/gin v1.9.0
            if stripped.startswith("require ") and "(" not in stripped:
                parts = stripped[8:].strip().split()
                if len(parts) >= 2:
                    mod_path, version = parts[0], parts[1]
                    name = self._go_module_short_name(mod_path)
                    result["dependencies"].append(
                        self._categorize(name, version.lstrip("v"), dev=False)
                    )
                continue

            # Inside require block
            if in_require:
                parts = stripped.split()
                if len(parts) >= 2 and not parts[0].startswith("//"):
                    mod_path, version = parts[0], parts[1]
                    name = self._go_module_short_name(mod_path)
                    result["dependencies"].append(
                        self._categorize(name, version.lstrip("v"), dev=False)
                    )

    @staticmethod
    def _go_module_short_name(mod_path: str) -> str:
        """Extract short name from Go module path (last segment)."""
        # github.com/gin-gonic/gin → gin
        parts = mod_path.rstrip("/").split("/")
        return parts[-1] if parts else mod_path

    # --- Elixir ---

    def _scan_mix_exs(self, path: Path, result: dict[str, Any]) -> None:
        """Parse mix.exs for Hex dependencies."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("mix.exs")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "hex"

        # Match: {:phoenix, "~> 1.7"} or {:plug, ">= 0.0.0"}
        dep_pattern = re.compile(
            r"""\{:(\w+)\s*,\s*"([^"]*)"[^}]*\}"""
        )
        for match in dep_pattern.finditer(content):
            name = match.group(1)
            version = match.group(2).lstrip("~> ").lstrip(">= ")
            # Check if it's a test-only dep
            dev = "only: :test" in match.group(0) or "only: [:test" in match.group(0)
            result["dependencies"].append(
                self._categorize(name, version, dev=dev)
            )

    # --- Java (Maven) ---

    def _scan_pom_xml(self, path: Path, result: dict[str, Any]) -> None:
        """Parse pom.xml for Maven dependencies (simple regex, no XML parser)."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append("pom.xml")
        if result["package_manager"] == "unknown":
            result["package_manager"] = "maven"

        # Match <dependency> blocks with <artifactId> and optional <version>
        dep_blocks = re.findall(
            r"<dependency>(.*?)</dependency>", content, re.DOTALL
        )
        for block in dep_blocks:
            artifact = re.search(r"<artifactId>(.*?)</artifactId>", block)
            version = re.search(r"<version>(.*?)</version>", block)
            scope = re.search(r"<scope>(.*?)</scope>", block)
            if artifact:
                name = artifact.group(1).strip()
                ver = version.group(1).strip() if version else ""
                dev = scope is not None and scope.group(1).strip() == "test"
                result["dependencies"].append(
                    self._categorize(name, ver, dev=dev)
                )

    # --- Java/Kotlin (Gradle) ---

    def _scan_gradle(self, path: Path, result: dict[str, Any]) -> None:
        """Parse build.gradle for dependencies (simple regex)."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append(path.name)
        if result["package_manager"] == "unknown":
            result["package_manager"] = "gradle"

        # Match: implementation 'group:artifact:version'
        # Also: testImplementation "group:artifact:version"
        dep_pattern = re.compile(
            r"""(?:implementation|api|compileOnly|runtimeOnly"""
            r"""|testImplementation|testRuntimeOnly"""
            r"""|kapt|annotationProcessor)"""
            r"""\s*[\(]?\s*['"]([^'"]+)['"]\s*[\)]?""",
        )
        for match in dep_pattern.finditer(content):
            coord = match.group(1)
            dev = "test" in match.group(0).lower()
            parts = coord.split(":")
            if len(parts) >= 2:
                name = parts[1]  # artifactId
                version = parts[2] if len(parts) >= 3 else ""
                result["dependencies"].append(
                    self._categorize(name, version, dev=dev)
                )

    # --- C# ---

    def _scan_csproj(self, path: Path, result: dict[str, Any]) -> None:
        """Parse .csproj for NuGet package references."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        result["dependency_files"].append(path.name)
        if result["package_manager"] == "unknown":
            result["package_manager"] = "nuget"

        # Match: <PackageReference Include="Name" Version="1.0" />
        pkg_pattern = re.compile(
            r'<PackageReference\s+Include="([^"]+)"'
            r'(?:\s+Version="([^"]*)")?',
        )
        for match in pkg_pattern.finditer(content):
            name = match.group(1)
            version = match.group(2) or ""
            result["dependencies"].append(
                self._categorize(name, version, dev=False)
            )

    # --- Shared helpers ---

    def _parse_toml_inline_list(
        self, content: str, key: str, result: dict[str, Any], dev: bool
    ) -> None:
        """Extract deps from TOML inline list: key = ["pkg>=ver", ...]."""
        pattern = rf"{key}\s*=\s*\[(.*?)\]"
        for match in re.finditer(pattern, content, re.DOTALL):
            items_str = match.group(1)
            for item in re.findall(r'"([^"]+)"', items_str):
                self._parse_dep_line(item, result, dev=dev)

    def _parse_dep_line(self, line: str, result: dict[str, Any], dev: bool) -> None:
        """Parse a single dependency string like 'click>=8.0'."""
        line = line.strip().strip('"').strip("'").strip(",").strip('"').strip("'")
        if not line or line.startswith("#") or line.startswith("["):
            return
        for sep in [">=", "==", "~=", "<=", "!=", "<", ">"]:
            if sep in line:
                name, version = line.split(sep, 1)
                result["dependencies"].append(
                    self._categorize(name.strip(), version.strip(), dev=dev)
                )
                return
        result["dependencies"].append(self._categorize(line.strip(), "", dev=dev))

    def _categorize(self, name: str, version: str, dev: bool) -> dict[str, Any]:
        """Categorize a dependency."""
        category, description = _registry.categorize_package(name)

        return {
            "name": name,
            "version": version,
            "dev": dev,
            "category": category,
            "description": description,
        }
