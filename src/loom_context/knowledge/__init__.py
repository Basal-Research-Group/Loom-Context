"""Knowledge Registry: centralized knowledge base for Loom detection.

Usage:
    from loom_context.knowledge import get_registry

    registry = get_registry()
    lang = registry.get_language(".rb")
    extensions = registry.get_all_extensions()
"""

from __future__ import annotations

from typing import Optional

from loom_context.knowledge.registry import KnowledgeRegistry
from loom_context.knowledge.scorer import SignalScorer

_registry: Optional[KnowledgeRegistry] = None
_scorer: Optional[SignalScorer] = None


def get_registry() -> KnowledgeRegistry:
    """Get the singleton KnowledgeRegistry instance."""
    global _registry
    if _registry is None:
        _registry = KnowledgeRegistry()
    return _registry


def get_scorer() -> SignalScorer:
    """Get the singleton SignalScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = SignalScorer()
    return _scorer
