"""Global project registry: tracks all projects that use Loom on this machine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loom_context import __version__

_LOOM_HOME = Path.home() / ".loom"
_REGISTRY_FILE = _LOOM_HOME / "registry.json"

# SECURITY: registry.json is LOCAL-ONLY machine state.
# - Never include in .context/ output
# - Never send to agents or external services
# - Never commit to any git repository
# - Project names/paths are private to the user's machine


def _load_registry() -> dict[str, Any]:
    """Load the global registry."""
    if not _REGISTRY_FILE.exists():
        return {"projects": []}
    try:
        with open(_REGISTRY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"projects": []}


def _save_registry(data: dict[str, Any]) -> None:
    """Save the global registry."""
    _LOOM_HOME.mkdir(parents=True, exist_ok=True)
    with open(_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register_project(
    root: Path,
    project_type: str = "",
    language: str = "",
    architecture: Optional[list[str]] = None,
    ecosystem: str = "",
    is_monorepo: bool = False,
    description: str = "",
) -> None:
    """Register or update a project in the global registry."""
    registry = _load_registry()
    root_str = str(root.resolve())
    now = datetime.now(timezone.utc).isoformat()

    # Find existing entry
    existing = None
    for project in registry["projects"]:
        if project.get("path") == root_str:
            existing = project
            break

    if existing:
        existing["type"] = project_type or existing.get("type", "")
        existing["language"] = language or existing.get("language", "")
        existing["architecture"] = architecture or existing.get("architecture", [])
        existing["ecosystem"] = ecosystem or existing.get("ecosystem", "")
        existing["is_monorepo"] = is_monorepo
        existing["last_scan"] = now
        existing["loom_version"] = __version__
        if description:
            existing["description"] = description
    else:
        registry["projects"].append({
            "path": root_str,
            "name": root.resolve().name,
            "type": project_type,
            "language": language,
            "architecture": architecture or [],
            "ecosystem": ecosystem,
            "is_monorepo": is_monorepo,
            "description": description,
            "registered_at": now,
            "last_scan": now,
            "loom_version": __version__,
        })

    _save_registry(registry)


def unregister_project(root: Path) -> bool:
    """Remove a project from the registry."""
    registry = _load_registry()
    root_str = str(root.resolve())
    original_count = len(registry["projects"])
    registry["projects"] = [
        p for p in registry["projects"] if p.get("path") != root_str
    ]
    if len(registry["projects"]) < original_count:
        _save_registry(registry)
        return True
    return False


def get_all_projects() -> list[dict[str, Any]]:
    """Get all registered projects."""
    registry = _load_registry()
    return registry.get("projects", [])


def get_project(root: Path) -> Optional[dict[str, Any]]:
    """Get a specific project entry."""
    root_str = str(root.resolve())
    for project in get_all_projects():
        if project.get("path") == root_str:
            return project
    return None
