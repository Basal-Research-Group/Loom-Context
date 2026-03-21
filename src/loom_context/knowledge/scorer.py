"""Signal-based architecture scorer for multi-pattern detection."""

from __future__ import annotations

from loom_context.knowledge.models import (
    ArchitectureMatch,
    ArchitecturePattern,
    ArchitectureSignal,
    ScoringEvidence,
)


class SignalScorer:
    """Scores architecture patterns against project evidence using weighted signals."""

    def score(self, pattern: ArchitecturePattern, evidence: ScoringEvidence) -> ArchitectureMatch:
        """Score a single architecture pattern against evidence."""
        total_score = 0.0
        matched_signals: list[str] = []

        for signal in pattern.signals:
            if self._match_signal(signal, evidence):
                total_score += signal.weight
                sig_desc = signal.pattern or ",".join(signal.patterns)
                matched_signals.append(f"{signal.type}:{sig_desc}")

        # Also check legacy exact-match sets (weight 1.0 if any matches)
        legacy_matched = self._check_legacy(pattern, evidence)
        if legacy_matched:
            # Legacy match guarantees detection at threshold
            total_score = max(total_score, pattern.confidence_threshold)
            if "legacy:exact-match" not in matched_signals:
                matched_signals.append("legacy:exact-match")

        confidence = "low"
        if total_score >= pattern.confidence_threshold + 0.2:
            confidence = "high"
        elif total_score >= pattern.confidence_threshold:
            confidence = "medium"

        return ArchitectureMatch(
            name=pattern.name,
            score=round(total_score, 3),
            confidence=confidence,
            signals_matched=matched_signals,
        )

    def score_all(
        self,
        patterns: dict[str, ArchitecturePattern],
        evidence: ScoringEvidence,
    ) -> list[ArchitectureMatch]:
        """Score all patterns and return those above threshold, sorted by score."""
        matches: list[ArchitectureMatch] = []
        for pattern in patterns.values():
            match = self.score(pattern, evidence)
            if match.score >= pattern.confidence_threshold:
                matches.append(match)
        return sorted(matches, key=lambda m: m.score, reverse=True)

    def _match_signal(self, signal: ArchitectureSignal, evidence: ScoringEvidence) -> bool:
        """Check if a single signal matches the evidence."""
        if signal.type == "directory":
            return self._match_directory(signal, evidence)
        if signal.type == "file_suffix":
            return self._match_file_suffix(signal, evidence)
        if signal.type == "file_content":
            # File content matching requires actual file reads — handled externally
            return False
        if signal.type == "package":
            return self._match_package(signal, evidence)
        if signal.type == "config_key":
            return signal.pattern in evidence.config_keys
        return False

    def _match_directory(self, signal: ArchitectureSignal, evidence: ScoringEvidence) -> bool:
        """Match a directory signal."""
        pattern = signal.pattern.lower()
        if signal.depth == "top":
            return pattern in {d.lower() for d in evidence.directories}
        # "any" depth — check all directories
        return pattern in {d.lower() for d in evidence.all_directories}

    def _match_file_suffix(self, signal: ArchitectureSignal, evidence: ScoringEvidence) -> bool:
        """Match a file suffix signal."""
        suffix = signal.pattern.lower()
        return any(s.lower() == suffix for s in evidence.file_suffixes)

    def _match_package(self, signal: ArchitectureSignal, evidence: ScoringEvidence) -> bool:
        """Match a package signal."""
        pkg_names = signal.patterns if signal.patterns else [signal.pattern]
        if signal.ecosystem:
            eco_pkgs = evidence.packages.get(signal.ecosystem, set())
            return any(p in eco_pkgs for p in pkg_names)
        # Check all ecosystems
        all_pkgs: set[str] = set()
        for pkgs in evidence.packages.values():
            all_pkgs.update(pkgs)
        return any(p in all_pkgs for p in pkg_names)

    def _check_legacy(self, pattern: ArchitecturePattern, evidence: ScoringEvidence) -> bool:
        """Check legacy exact directory-set matching for backward compatibility."""
        if not pattern.legacy_dir_sets:
            return False
        normalized = {d.lower() for d in evidence.directories}
        for dir_set in pattern.legacy_dir_sets:
            required = {d.lower() for d in dir_set}
            if required.issubset(normalized):
                return True
        return False
