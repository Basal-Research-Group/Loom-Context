"""File filter that respects .gitignore, .contextignore, and hardcoded security patterns."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pathspec

from loom_context.knowledge import get_registry

# Backward-compatible aliases (read from Knowledge Registry)
_registry = get_registry()
HARDCODED_DIR_EXCLUSIONS = _registry.get_dir_exclusions()
SECRETS_PATTERNS = _registry.get_secret_patterns()


class FileFilter:
    """Walks a project tree respecting ignore files and security patterns."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self._specs: list[pathspec.PathSpec] = []
        self._secrets_spec: Optional[pathspec.PathSpec] = None
        self._load_gitignore()
        self._load_contextignore()
        self._build_secrets_spec()

    def _load_gitignore(self) -> None:
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            with open(gitignore, encoding="utf-8") as f:
                spec = pathspec.PathSpec.from_lines("gitignore", f)
                self._specs.append(spec)

    def _load_contextignore(self) -> None:
        contextignore = self.root / ".contextignore"
        if contextignore.exists():
            with open(contextignore, encoding="utf-8") as f:
                spec = pathspec.PathSpec.from_lines("gitignore", f)
                self._specs.append(spec)

    def _build_secrets_spec(self) -> None:
        self._secrets_spec = pathspec.PathSpec.from_lines("gitignore", SECRETS_PATTERNS)

    def is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        rel = path.relative_to(self.root)
        rel_str = str(rel)

        # Check hardcoded directory exclusions
        for part in rel.parts:
            if part in HARDCODED_DIR_EXCLUSIONS:
                return True

        # Check .gitignore and .contextignore
        return any(spec.match_file(rel_str) for spec in self._specs)

    def is_secret(self, path: Path) -> bool:
        """Check if a file matches secret patterns."""
        if self._secrets_spec is None:
            return False
        rel = str(path.relative_to(self.root))
        return bool(self._secrets_spec.match_file(rel))

    def walk(self) -> Iterator[Path]:
        """Yield every file path that passes all filters."""
        yield from self._walk_recursive(self.root)

    def _walk_recursive(self, directory: Path) -> Iterator[Path]:
        """Recursively walk directory, skipping excluded dirs early."""
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                # Skip hardcoded exclusions immediately (no need to check full path)
                if entry.name in HARDCODED_DIR_EXCLUSIONS:
                    continue
                if entry.name == ".context":
                    continue
                if not self.is_excluded(entry):
                    yield from self._walk_recursive(entry)
            elif entry.is_file():
                if not self.is_excluded(entry) and not self.is_secret(entry):
                    yield entry

    def walk_dirs(self) -> Iterator[Path]:
        """Yield only directories that pass filters."""
        yield from self._walk_dirs_recursive(self.root)

    def _walk_dirs_recursive(self, directory: Path) -> Iterator[Path]:
        """Recursively yield directories."""
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                if entry.name in HARDCODED_DIR_EXCLUSIONS:
                    continue
                if entry.name == ".context":
                    continue
                if not self.is_excluded(entry):
                    yield entry
                    yield from self._walk_dirs_recursive(entry)
