"""Selection models: candidates, reasons, and manifest for bundles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class SelectionReason:
    """Why a piece of context was included in the bundle."""

    strategy: str  # "lexical" | "directory" | "architecture" | "doc" | "rule" | "import"
    detail: str  # human-readable explanation
    score: float  # 0.0 to 1.0


@dataclass
class SelectionCandidate:
    """A candidate piece of context for inclusion in a bundle."""

    source: str  # "rules" | "architecture" | "naming" | "directory" | "stack" | "doc" | "plan"
    content: str
    reasons: list[SelectionReason] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        """Sum of all reason scores."""
        return sum(r.score for r in self.reasons)


@dataclass
class BundleManifest:
    """Metadata for a generated bundle — trazability record."""

    task: str
    slug: str
    git_sha: Optional[str]
    generated_at: str
    loom_version: str
    selection_strategy: str
    total_candidates: int
    included_count: int
    total_chars: int
    included_rules: list[str] = field(default_factory=list)
    included_docs: list[str] = field(default_factory=list)
    included_sections: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        return asdict(self)
