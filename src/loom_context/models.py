"""Domain models: typed contracts for data crossing layer boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class StructureFacts:
    """Project structure analysis results."""

    project_type: str
    architecture: list[str]
    src_root: str
    directory_tree: dict[str, Any]
    layer_boundaries: dict[str, Any]
    total_files: int
    file_counts_by_dir: dict[str, int] = field(default_factory=dict)
    project_name: str = ""
    language: str = ""
    architecture_confidence: dict[str, Any] = field(default_factory=dict)
    is_monorepo: bool = False
    workspaces: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Dependency:
    """A single project dependency."""

    name: str
    version: str
    dev: bool
    category: str
    description: str = ""


@dataclass(frozen=True)
class DependencyInfo:
    """Dependency analysis results."""

    package_manager: str
    dependency_files: list[str]
    dependencies: list[Dependency]
    stack_summary: dict[str, list[str]]
    ecosystem: str = "unknown"


@dataclass(frozen=True)
class CodeAnalysis:
    """Code naming convention analysis results."""

    file_naming: dict[str, Any]
    code_naming: dict[str, Any]
    suffix_patterns: list[dict[str, Any]]
    prefix_patterns: list[dict[str, Any]]
    import_aliases: dict[str, str]
    total_code_files: int
    naming_by_role: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocEntry:
    """A single indexed documentation file."""

    path: str
    title: str
    type: str
    sections: list[str]
    status_items: list[dict[str, str]]
    size_kb: float
    version: Optional[str] = None
    doc_status: Optional[str] = None
    scope: Optional[str] = None
    prerequisite: Optional[str] = None
    patterns: Optional[list[str]] = None
    progress: Optional[str] = None


@dataclass(frozen=True)
class DocsInventory:
    """Documentation index results."""

    docs: list[DocEntry]
    agents_md: Optional[str]
    doc_count: int
    by_type: dict[str, int]


@dataclass(frozen=True)
class ScanResult:
    """Complete scan result from all scanners."""

    structure: StructureFacts
    deps: DependencyInfo
    code: CodeAnalysis
    docs: DocsInventory
    scanned_at: str
    domain: str = "unknown"
    domain_confidence: float = 0.0
    domain_details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for backward compatibility with generators."""
        return asdict(self)


@dataclass
class Violation:
    """A naming or structure violation."""

    file: str
    line: Optional[int]
    rule: str
    message: str
    severity: Literal["error", "warning", "info"]
    suggestion: str = ""
