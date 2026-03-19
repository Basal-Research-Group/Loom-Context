"""Setup presets: predefined configurations for loom setup."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SetupPreset:
    """A predefined setup configuration."""

    name: str
    description: str
    scan: bool = True
    agents: list[str] = field(default_factory=list)
    install: bool = True
    export_only: bool = False


PRESETS: dict[str, SetupPreset] = {
    "minimal": SetupPreset(
        name="minimal",
        description="Scan only, no agent exports",
        scan=True,
        agents=[],
        install=False,
    ),
    "full": SetupPreset(
        name="full",
        description="Scan + export all agents + install to project root",
        scan=True,
        agents=["claude", "cursor", "codex", "copilot", "generic"],
        install=True,
    ),
    "claude": SetupPreset(
        name="claude",
        description="Scan + export + install Claude only",
        scan=True,
        agents=["claude"],
        install=True,
    ),
}


def get_preset(name: str) -> Optional[SetupPreset]:
    """Get a preset by name."""
    return PRESETS.get(name.lower())


def list_presets() -> list[SetupPreset]:
    """Return all available presets."""
    return list(PRESETS.values())
