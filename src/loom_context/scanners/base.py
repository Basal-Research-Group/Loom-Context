"""Base scanner interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loom_context.security.filter import FileFilter


class BaseScanner(ABC):
    """Abstract base class for all project scanners."""

    def __init__(self, root: Path, file_filter: FileFilter) -> None:
        self.root = root
        self.file_filter = file_filter

    @abstractmethod
    def scan(self) -> dict[str, Any]:
        """Execute the scan and return structured results."""
        ...
