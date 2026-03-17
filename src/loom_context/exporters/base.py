"""Base exporter: abstract interface for agent-specific exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseExporter(ABC):
    """Base class for agent-specific context exporters."""

    agent_name: str = "generic"
    file_extension: str = ".md"

    def __init__(self, context_dir: Path, root: Path) -> None:
        self.context_dir = context_dir
        self.root = root

    @abstractmethod
    def export(self) -> str:
        """Generate agent-specific context output."""

    def export_to_file(self, output_path: Optional[Path] = None) -> Path:
        """Export to .context/exports/ or specified file."""
        content = self.export()
        if output_path is None:
            exports_dir = self.context_dir / "exports"
            exports_dir.mkdir(exist_ok=True)
            output_path = exports_dir / self.default_filename()
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def default_filename(self) -> str:
        """Default output filename for this agent."""
        return f"{self.agent_name}{self.file_extension}"

    def install_path(self) -> Path:
        """Where the agent expects the file in the project root."""
        return self.root / self.default_filename()

    def _read_file(self, filename: str) -> str:
        """Read a .context/ file."""
        path = self.context_dir / filename
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _read_prompt(self) -> str:
        """Generate master prompt using PromptGenerator."""
        from loom_context.generators.prompt import PromptGenerator

        gen = PromptGenerator(self.context_dir)
        return gen.generate()
