"""Generic exporter: universal format for any AI agent."""

from __future__ import annotations

from loom_context.exporters.base import BaseExporter


class GenericExporter(BaseExporter):
    """Export context in universal format usable by any agent."""

    agent_name = "generic"
    file_extension = ".md"

    def export(self) -> str:
        """Generate universal context export."""
        return self._read_prompt()

    def default_filename(self) -> str:
        return ".loom-export.md"
