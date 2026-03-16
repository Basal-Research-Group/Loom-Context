"""Exporters: format context for specific AI agents."""

from __future__ import annotations

from typing import Optional

from loom_context.exporters.base import BaseExporter
from loom_context.exporters.claude import ClaudeExporter
from loom_context.exporters.codex import CodexExporter
from loom_context.exporters.cursor import CursorExporter
from loom_context.exporters.generic import GenericExporter

EXPORTERS: dict[str, type[BaseExporter]] = {
    "claude": ClaudeExporter,
    "cursor": CursorExporter,
    "codex": CodexExporter,
    "generic": GenericExporter,
}

AGENT_NAMES = list(EXPORTERS.keys())


def get_exporter(agent: str) -> Optional[type[BaseExporter]]:
    """Get exporter class by agent name."""
    return EXPORTERS.get(agent.lower())
