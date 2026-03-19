"""Code scanner: infers naming conventions and patterns from actual code files."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from loom_context.scanners.base import BaseScanner
from loom_context.security.filter import FileFilter

# File extensions to analyze
CODE_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".py",
    ".pyi",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".scala",
    ".cs",
    ".rb",
    ".php",
    ".swift",
}

# Regex patterns for naming detection
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
# camelCase requires at least one uppercase transition (e.g., myFile, useState)
# Single lowercase words (engine, models, config) are NOT camelCase
CAMEL_CASE = re.compile(r"^[a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*$")
KEBAB_CASE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)+$")
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")

# Suffix patterns that indicate architectural role
ROLE_SUFFIXES = [
    "Service",
    "Repository",
    "Adapter",
    "Mapper",
    "Controller",
    "Provider",
    "Factory",
    "Builder",
    "Handler",
    "Middleware",
    "Guard",
    "Pipe",
    "Interceptor",
    "Resolver",
    "Validator",
    "Strategy",
    "Observer",
    "Command",
    "Query",
    "Event",
    "Renderer",
    "Generator",
    "Registry",
    "Manager",
    "Listener",
    "UseCase",
    "Interactor",
    "Presenter",
    "ViewModel",
]

# Prefix patterns
ROLE_PREFIXES = [
    ("I", "Interface prefix"),
    ("use", "React hook prefix"),
    ("Abstract", "Abstract class prefix"),
    ("Base", "Base class prefix"),
    ("Mock", "Mock/test double prefix"),
]

# Import alias detection patterns (tsconfig paths)
TS_ALIAS_PATTERN = re.compile(r'"(@[^"]+/\*?)"\s*:\s*\["([^"]+)"\]')

# Code-level naming extraction patterns
INTERFACE_PATTERN = re.compile(r"(?:export\s+)?interface\s+(\w+)")
CLASS_PATTERN = re.compile(r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)")
FUNCTION_PATTERN = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)")
CONST_FUNC_PATTERN = re.compile(r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(")
ENUM_PATTERN = re.compile(r"(?:export\s+)?enum\s+(\w+)")
TYPE_PATTERN = re.compile(r"(?:export\s+)?type\s+(\w+)\s*=")
PY_CLASS_PATTERN = re.compile(r"class\s+(\w+)")
PY_FUNC_PATTERN = re.compile(r"def\s+(\w+)")
PY_CONST_PATTERN = re.compile(r"^([A-Z][A-Z_0-9]+)\s*=", re.MULTILINE)


def _classify_case(name: str) -> str:
    """Classify the naming case of a string."""
    stem = name.rsplit(".", 1)[0] if "." in name else name
    if PASCAL_CASE.match(stem):
        return "PascalCase"
    if CAMEL_CASE.match(stem):
        return "camelCase"
    if KEBAB_CASE.match(stem):
        return "kebab-case"
    if SNAKE_CASE.match(stem):
        return "snake_case"
    if UPPER_SNAKE.match(stem):
        return "UPPER_CASE"
    return "mixed"


class CodeScanner(BaseScanner):
    """Scans code files to infer naming conventions and patterns."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        super().__init__(root, file_filter)
        self._sample_size = 100

    def scan(self) -> dict[str, Any]:
        files = self._collect_code_files()
        sample = self._sample_files(files)

        file_naming = self._analyze_file_naming(files)
        code_naming = self._analyze_code_naming(sample)
        suffix_patterns = self._detect_suffix_patterns(files)
        prefix_patterns = self._detect_prefix_patterns(files, sample)
        import_aliases = self._detect_import_aliases()

        naming_by_role = self._analyze_naming_by_role(files, suffix_patterns)

        return {
            "file_naming": file_naming,
            "code_naming": code_naming,
            "suffix_patterns": suffix_patterns,
            "prefix_patterns": prefix_patterns,
            "import_aliases": import_aliases,
            "total_code_files": len(files),
            "naming_by_role": naming_by_role,
        }

    def _collect_code_files(self) -> list[Path]:
        """Collect all code files."""
        return [f for f in self.file_filter.walk() if f.suffix in CODE_EXTENSIONS]

    def _sample_files(self, files: list[Path]) -> list[Path]:
        """Sample files for detailed analysis."""
        if len(files) <= self._sample_size:
            return files

        # Weight toward src/ files
        src_files = [f for f in files if "src" in f.parts]
        other_files = [f for f in files if "src" not in f.parts]

        src_count = min(len(src_files), int(self._sample_size * 0.8))
        other_count = min(len(other_files), self._sample_size - src_count)

        sample = random.sample(src_files, src_count)
        if other_count > 0:
            sample += random.sample(other_files, other_count)
        return sample

    def _analyze_naming_by_role(
        self, files: list[Path], suffix_patterns: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze naming style per architectural role."""
        # Build role map from detected suffixes
        role_files: dict[str, list[str]] = {}
        suffix_set = {sp["suffix"].lower() for sp in suffix_patterns}

        for f in files:
            stem = f.stem
            role = "other"

            # Detect role from suffix
            for suffix in suffix_set:
                if stem.lower().endswith(suffix.lower()):
                    role = suffix
                    break

            # Detect role from prefix
            if stem.startswith("use") and len(stem) > 3 and stem[3].isupper():
                role = "hook"
            elif stem.startswith("I") and len(stem) > 1 and stem[1].isupper():
                role = "interface"

            # Detect role from directory
            for part in f.parts:
                if part in {"components", "screens", "views", "pages"}:
                    if role == "other":
                        role = "component"
                    break
                if part in {"hooks"}:
                    role = "hook"
                    break

            role_files.setdefault(role, []).append(stem)

        # Calculate naming per role
        result: dict[str, Any] = {}
        for role, stems in sorted(role_files.items()):
            if len(stems) < 2:
                continue
            counts: dict[str, int] = {}
            for stem in stems:
                case = _classify_case(stem)
                counts[case] = counts.get(case, 0) + 1
            total = sum(counts.values())
            dominant = max(counts, key=counts.get) if counts else "unknown"  # type: ignore[arg-type]
            confidence = counts.get(dominant, 0) / total if total > 0 else 0
            if confidence > 0.5:
                result[role] = {
                    "style": dominant,
                    "confidence": round(confidence, 2),
                    "count": total,
                }

        return result

    def _analyze_file_naming(self, files: list[Path]) -> dict[str, Any]:
        """Analyze file naming patterns."""
        case_counts: dict[str, int] = {}
        for f in files:
            case = _classify_case(f.stem)
            case_counts[case] = case_counts.get(case, 0) + 1

        total = sum(case_counts.values())
        dominant = max(case_counts, key=case_counts.get) if case_counts else "unknown"  # type: ignore[arg-type]
        confidence = case_counts.get(dominant, 0) / total if total > 0 else 0

        return {
            "dominant_style": dominant,
            "confidence": round(confidence, 2),
            "distribution": (
                {k: round(v / total, 2) for k, v in case_counts.items()} if total > 0 else {}
            ),
        }

    def _analyze_code_naming(self, sample: list[Path]) -> dict[str, Any]:
        """Analyze naming inside code files."""
        interfaces: list[str] = []
        classes: list[str] = []
        functions: list[str] = []
        enums: list[str] = []
        constants: list[str] = []

        for filepath in sample:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                # Only read first 100 lines for performance
                lines = content.split("\n")[:100]
                content = "\n".join(lines)
            except OSError:
                continue

            ext = filepath.suffix
            if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                interfaces.extend(INTERFACE_PATTERN.findall(content))
                classes.extend(CLASS_PATTERN.findall(content))
                functions.extend(FUNCTION_PATTERN.findall(content))
                functions.extend(CONST_FUNC_PATTERN.findall(content))
                enums.extend(ENUM_PATTERN.findall(content))
            elif ext in {".py", ".pyi"}:
                classes.extend(PY_CLASS_PATTERN.findall(content))
                functions.extend(PY_FUNC_PATTERN.findall(content))
                constants.extend(PY_CONST_PATTERN.findall(content))

        result: dict[str, Any] = {}

        if interfaces:
            i_prefix_count = sum(
                1 for i in interfaces if i.startswith("I") and len(i) > 1 and i[1].isupper()
            )
            result["interfaces"] = {
                "format": self._dominant_case(interfaces),
                "prefix": "I" if i_prefix_count / len(interfaces) > 0.6 else "none",
                "count": len(interfaces),
            }

        if classes:
            result["classes"] = {
                "format": self._dominant_case(classes),
                "count": len(classes),
            }

        if functions:
            result["functions"] = {
                "format": self._dominant_case(functions),
                "count": len(functions),
            }

        if enums:
            result["enums"] = {
                "format": self._dominant_case(enums),
                "count": len(enums),
            }

        return result

    def _detect_suffix_patterns(self, files: list[Path]) -> list[dict[str, Any]]:
        """Detect role-based suffix patterns in filenames."""
        patterns: list[dict[str, Any]] = []

        for suffix in ROLE_SUFFIXES:
            matches = [f for f in files if f.stem.endswith(suffix)]
            if len(matches) >= 2:
                examples = [f.name for f in matches[:3]]
                patterns.append(
                    {
                        "suffix": suffix,
                        "pattern": f"{{Name}}{suffix}{matches[0].suffix}",
                        "count": len(matches),
                        "examples": examples,
                    }
                )

        return sorted(patterns, key=lambda p: p["count"], reverse=True)

    def _detect_prefix_patterns(
        self, files: list[Path], sample: list[Path]
    ) -> list[dict[str, Any]]:
        """Detect role-based prefix patterns."""
        patterns: list[dict[str, Any]] = []

        for prefix, description in ROLE_PREFIXES:
            if prefix == "I":
                # Check interfaces in code
                matches = [
                    f
                    for f in files
                    if f.stem.startswith("I") and len(f.stem) > 1 and f.stem[1].isupper()
                ]
            elif prefix == "use":
                matches = [
                    f
                    for f in files
                    if f.stem.startswith("use") and len(f.stem) > 3 and f.stem[3].isupper()
                ]
            else:
                matches = [f for f in files if f.stem.startswith(prefix)]

            if len(matches) >= 2:
                examples = [f.name for f in matches[:3]]
                patterns.append(
                    {
                        "prefix": prefix,
                        "description": description,
                        "pattern": f"{prefix}{{Name}}{matches[0].suffix}",
                        "count": len(matches),
                        "examples": examples,
                    }
                )

        return sorted(patterns, key=lambda p: p["count"], reverse=True)

    def _detect_import_aliases(self) -> dict[str, str]:
        """Detect import path aliases from tsconfig.json."""
        aliases: dict[str, str] = {}

        tsconfig = self.root / "tsconfig.json"
        if tsconfig.exists():
            try:
                content = tsconfig.read_text(encoding="utf-8")
                # Remove comments (simple single-line)
                cleaned = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
                # Remove trailing commas before } or ]
                cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
                data = json.loads(cleaned)
                paths = data.get("compilerOptions", {}).get("paths", {})
                for alias, targets in paths.items():
                    if targets:
                        aliases[alias] = targets[0]
            except (json.JSONDecodeError, OSError, KeyError):
                pass

        return aliases

    def _dominant_case(self, names: list[str]) -> str:
        """Find the dominant naming case in a list of names."""
        counts: dict[str, int] = {}
        for name in names:
            case = _classify_case(name)
            counts[case] = counts.get(case, 0) + 1
        return max(counts, key=counts.get) if counts else "unknown"  # type: ignore[arg-type]
