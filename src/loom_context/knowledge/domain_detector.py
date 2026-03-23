"""Domain detection: infer project domain from file tree evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loom_context.knowledge import get_registry
from loom_context.security.filter import FileFilter


@dataclass
class DomainMatch:
    """Result of domain detection for a single domain."""

    name: str
    display_name: str = ""
    score: float = 0.0
    confidence: str = "low"  # "low", "medium", "high"
    matched_markers: list[str] = field(default_factory=list)
    matched_extensions: list[str] = field(default_factory=list)
    matched_directories: list[str] = field(default_factory=list)


@dataclass
class DomainDetectionResult:
    """Complete domain detection result."""

    primary: str = "unknown"  # best domain or "mixed"
    primary_confidence: float = 0.0
    domains: list[DomainMatch] = field(default_factory=list)

    @property
    def is_mixed(self) -> bool:
        """True if multiple domains scored above threshold."""
        return self.primary == "mixed"

    @property
    def active_domains(self) -> list[str]:
        """Domain names that scored above threshold."""
        return [d.name for d in self.domains if d.score >= 0.3]

    def to_dict(self) -> dict[str, Any]:
        """Serialize for inclusion in ScanResult."""
        return {
            "primary": self.primary,
            "confidence": round(self.primary_confidence, 3),
            "active": self.active_domains,
            "scores": {d.name: round(d.score, 3) for d in self.domains if d.score > 0},
        }


class DomainDetector:
    """Detects project domain(s) by matching file tree against domain definitions."""

    THRESHOLD = 0.3

    def __init__(self, root: Path, file_filter: Optional[FileFilter] = None) -> None:
        self.root = root
        self.file_filter = file_filter or FileFilter(root)

    def detect(self) -> DomainDetectionResult:
        """Detect domains by scoring markers, extensions, and directory patterns."""
        registry = get_registry()
        available = registry.get_available_domains()

        # Collect evidence from file tree
        files = list(self.file_filter.walk())
        file_names = {f.name for f in files}
        file_extensions = {f.suffix.lower() for f in files if f.suffix}
        all_dirs = self._collect_directories(files)
        top_dirs = {d for d in all_dirs if "/" not in d}

        matches: list[DomainMatch] = []

        for domain_name in available:
            domain_data = registry.get_domain(domain_name)
            if not domain_data:
                continue

            match = self._score_domain(
                domain_name, domain_data, file_names, file_extensions, top_dirs, all_dirs
            )
            matches.append(match)

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        # Determine primary domain
        above_threshold = [m for m in matches if m.score >= self.THRESHOLD]

        if not above_threshold:
            return DomainDetectionResult(primary="unknown", domains=matches)

        if len(above_threshold) == 1:
            best = above_threshold[0]
            return DomainDetectionResult(
                primary=best.name,
                primary_confidence=best.score,
                domains=matches,
            )

        # Multiple domains above threshold — resolve ambiguity
        # Code projects often have brand-like dirs (assets/, icons/, i18n/).
        # If code is above threshold, it wins unless another domain is much stronger.
        code_match = next((m for m in above_threshold if m.name == "code"), None)
        if code_match and code_match.score >= self.THRESHOLD:
            top = above_threshold[0]
            # Code wins if it's within 0.2 of the top score
            if top.name != "code" and (top.score - code_match.score) < 0.2:
                return DomainDetectionResult(
                    primary="code",
                    primary_confidence=code_match.score,
                    domains=matches,
                )

        # Otherwise, top scorer wins if it's clearly ahead (>0.15 gap)
        if len(above_threshold) >= 2:
            gap = above_threshold[0].score - above_threshold[1].score
            if gap >= 0.15:
                best = above_threshold[0]
                return DomainDetectionResult(
                    primary=best.name,
                    primary_confidence=best.score,
                    domains=matches,
                )

        # True mixed: multiple domains close in score, none is code
        return DomainDetectionResult(
            primary="mixed",
            primary_confidence=above_threshold[0].score,
            domains=matches,
        )

    def _score_domain(
        self,
        name: str,
        data: dict[str, Any],
        file_names: set[str],
        file_extensions: set[str],
        top_dirs: set[str],
        all_dirs: set[str],
    ) -> DomainMatch:
        """Score a single domain against evidence."""
        markers = data.get("markers", [])
        extensions = data.get("file_extensions", [])
        dir_patterns = data.get("directory_patterns", [])

        score = 0.0
        matched_markers: list[str] = []
        matched_extensions: list[str] = []
        matched_directories: list[str] = []

        # Markers: files or directories that signal this domain
        # Each matched marker adds weight, capped at 0.5 total
        if markers:
            marker_hits = 0
            for marker in markers:
                marker_clean = marker.rstrip("/")
                if marker_clean in file_names or marker_clean in all_dirs:
                    marker_hits += 1
                    matched_markers.append(marker_clean)
            if marker_hits > 0:
                # More markers matched = stronger signal, diminishing returns
                marker_ratio = min(marker_hits / 3.0, 1.0)
                score += marker_ratio * 0.5

        # File extensions: what file types exist
        if extensions:
            ext_matches = file_extensions & {e.lower() for e in extensions}
            if ext_matches:
                ext_ratio = len(ext_matches) / max(len(extensions), 1)
                score += ext_ratio * 0.3
                matched_extensions = list(ext_matches)

        # Directory patterns: semantic directory names
        if dir_patterns:
            dir_lower = {d.lower() for d in all_dirs}
            pattern_matches = dir_lower & {p.lower() for p in dir_patterns}
            if pattern_matches:
                dir_ratio = len(pattern_matches) / max(len(dir_patterns), 1)
                score += dir_ratio * 0.3
                matched_directories = list(pattern_matches)

        # Boost: if this is 'code' domain and strong code markers exist, boost
        # A project with package.json or pyproject.toml is primarily code,
        # even if it has brand/ or assets/ directories
        if name == "code" and matched_markers:
            strong_code_markers = {
                "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
                "Gemfile", "pom.xml", "build.gradle", "composer.json",
                "mix.exs", "pubspec.yaml",
            }
            if matched_markers and set(matched_markers) & strong_code_markers:
                score += 0.15  # code projects with package managers get a boost

        # Cap at 1.0
        score = min(score, 1.0)

        # Confidence level
        confidence = "low"
        if score >= 0.6:
            confidence = "high"
        elif score >= self.THRESHOLD:
            confidence = "medium"

        return DomainMatch(
            name=name,
            display_name=data.get("display_name", name),
            score=round(score, 3),
            confidence=confidence,
            matched_markers=matched_markers,
            matched_extensions=matched_extensions,
            matched_directories=matched_directories,
        )

    def _collect_directories(self, files: list[Path]) -> set[str]:
        """Collect all directory names relative to root."""
        dirs: set[str] = set()
        for f in files:
            try:
                rel = f.relative_to(self.root)
                for parent in rel.parents:
                    if parent != Path("."):
                        dirs.add(str(parent).replace("\\", "/"))
                        dirs.add(parent.name)
            except ValueError:
                continue
        return dirs
