"""Knowledge registry models: typed contracts for the knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PackageManagerInfo:
    """Package manager detection info for a language."""

    file: str
    lock: Optional[str] = None
    tool: str = ""


@dataclass(frozen=True)
class NamingConventions:
    """Expected naming conventions for a language."""

    files: str = ""
    classes: str = ""
    functions: str = ""
    methods: str = ""
    constants: str = ""
    modules: str = ""


@dataclass(frozen=True)
class FrameworkInfo:
    """Framework detection info within a language."""

    name: str
    markers: list[str] = field(default_factory=list)
    src_roots: list[str] = field(default_factory=list)
    dir_exclusions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LanguageInfo:
    """Complete language definition."""

    name: str
    extensions: list[str] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    project_type: str = ""
    package_managers: list[PackageManagerInfo] = field(default_factory=list)
    naming: Optional[NamingConventions] = None
    comment_style: str = ""
    import_pattern: str = ""
    class_pattern: str = ""
    function_pattern: str = ""
    constant_pattern: str = ""
    frameworks: dict[str, FrameworkInfo] = field(default_factory=dict)


@dataclass(frozen=True)
class PackageInfo:
    """A known package in an ecosystem."""

    name: str
    category: str
    description: str = ""


@dataclass(frozen=True)
class CategoryInferenceRule:
    """Rule for inferring package category from name patterns."""

    pattern: str
    category: str
    match_type: str = "contains"  # "contains", "startswith", "endswith"


@dataclass(frozen=True)
class ArchitectureSignal:
    """A single detection signal for an architecture pattern."""

    type: str  # "directory", "file_suffix", "file_content", "package", "config_key"
    pattern: str = ""
    patterns: list[str] = field(default_factory=list)
    weight: float = 0.0
    depth: str = "any"  # "top", "any" — where to look for directories
    ecosystem: str = ""  # for package signals


@dataclass(frozen=True)
class ArchitecturePattern:
    """Architecture pattern with scoring signals."""

    name: str
    display_name: str = ""
    signals: list[ArchitectureSignal] = field(default_factory=list)
    confidence_threshold: float = 0.5
    boundary_rules: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    # Legacy exact-match sets for backward compat
    legacy_dir_sets: list[list[str]] = field(default_factory=list)


@dataclass
class ArchitectureMatch:
    """Result of architecture scoring."""

    name: str
    score: float = 0.0
    confidence: str = "low"  # "low", "medium", "high"
    signals_matched: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RolePattern:
    """Architectural role suffix or prefix."""

    value: str
    description: str = ""
    type: str = "suffix"  # "suffix" or "prefix"
    languages: list[str] = field(default_factory=list)  # empty = all languages


@dataclass(frozen=True)
class DocClassificationRule:
    """Rule for classifying documentation files."""

    pattern: str
    doc_type: str
    source: str = "filename"  # "filename", "path", "content"


@dataclass(frozen=True)
class InfraServiceDef:
    """Infrastructure service definition."""

    name: str
    category: str
    default_port: int = 0
    install_cmd_mac: str = ""
    install_cmd_linux: str = ""
    start_cmd_mac: str = ""
    start_cmd_linux: str = ""
    stop_cmd_mac: str = ""
    stop_cmd_linux: str = ""
    status_cmd: str = ""
    docker_cmd: str = ""
    config_env: str = ""
    config_hint: str = ""
    binaries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DomainDef:
    """Domain definition (code, research, data, etc.)."""

    name: str
    display_name: str = ""
    markers: list[str] = field(default_factory=list)
    file_extensions: list[str] = field(default_factory=list)
    directory_patterns: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ScoringEvidence:
    """Evidence collected from a project for architecture scoring."""

    directories: set[str] = field(default_factory=set)
    all_directories: set[str] = field(default_factory=set)  # includes nested
    file_suffixes: set[str] = field(default_factory=set)
    file_names: list[str] = field(default_factory=list)
    packages: dict[str, set[str]] = field(default_factory=dict)  # ecosystem -> names
    config_keys: set[str] = field(default_factory=set)
