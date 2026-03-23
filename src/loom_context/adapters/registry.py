"""Adapter registry: resolves domain → adapter."""

from __future__ import annotations

from pathlib import Path

from loom_context.adapters.base import DomainAdapter
from loom_context.adapters.brand import BrandAdapter
from loom_context.adapters.code import CodeAdapter
from loom_context.adapters.data import DataAdapter
from loom_context.adapters.research import ResearchAdapter
from loom_context.security.filter import FileFilter

_ADAPTERS: dict[str, type[DomainAdapter]] = {
    "code": CodeAdapter,
    "brand": BrandAdapter,
    "research": ResearchAdapter,
    "data": DataAdapter,
}


def get_adapter(domain: str, root: Path, file_filter: FileFilter) -> DomainAdapter:
    """Get the appropriate adapter for a detected domain.

    Falls back to CodeAdapter for unknown or mixed domains.
    """
    adapter_cls = _ADAPTERS.get(domain, CodeAdapter)
    return adapter_cls(root, file_filter)


def get_available_adapters() -> list[str]:
    """List registered adapter names."""
    return list(_ADAPTERS.keys())
