"""Metrics: quantitative health analysis per architectural layer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LayerMetrics:
    """Metrics for a single architectural layer."""

    name: str
    file_count: int = 0
    code_files: int = 0
    directories: int = 0


@dataclass
class ProjectMetrics:
    """Quantitative project health metrics."""

    layers: list[LayerMetrics] = field(default_factory=list)
    total_files: int = 0
    total_layers: int = 0
    largest_layer: str = ""
    smallest_layer: str = ""
    balance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)


CODE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go", ".java", ".kt", ".swift"}


class MetricsCollector:
    """Collects quantitative metrics from project structure."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def collect(self) -> ProjectMetrics:
        """Collect metrics per layer."""
        index = self._read_index()
        boundaries = index.get("architecture", {}).get("layer_boundaries", {})
        src_root = self._find_src_root()

        if not boundaries:
            return ProjectMetrics()

        layers: list[LayerMetrics] = []
        for layer_name in sorted(boundaries.keys()):
            layer_dir = src_root / layer_name
            if not layer_dir.exists():
                layer_dir = self.root / layer_name
            if not layer_dir.exists():
                layers.append(LayerMetrics(name=layer_name))
                continue

            file_count = 0
            code_count = 0
            dir_count = 0
            for entry in layer_dir.rglob("*"):
                if entry.is_file():
                    file_count += 1
                    if entry.suffix in CODE_EXTENSIONS:
                        code_count += 1
                elif entry.is_dir():
                    dir_count += 1

            layers.append(
                LayerMetrics(
                    name=layer_name,
                    file_count=file_count,
                    code_files=code_count,
                    directories=dir_count,
                )
            )

        if not layers:
            return ProjectMetrics()

        total = sum(ly.file_count for ly in layers)
        active = [ly for ly in layers if ly.file_count > 0]

        largest = max(active, key=lambda ly: ly.file_count) if active else layers[0]
        smallest = min(active, key=lambda ly: ly.file_count) if active else layers[0]

        # Balance: 1.0 = perfectly balanced, 0.0 = all in one layer
        if len(active) > 1 and total > 0:
            avg = total / len(active)
            deviation = sum(abs(ly.file_count - avg) for ly in active) / len(active)
            balance = max(0.0, 1.0 - (deviation / avg)) if avg > 0 else 0.0
        else:
            balance = 1.0

        return ProjectMetrics(
            layers=layers,
            total_files=total,
            total_layers=len(active),
            largest_layer=largest.name,
            smallest_layer=smallest.name,
            balance_score=round(balance, 2),
        )

    def save(self, metrics: ProjectMetrics) -> Path:
        """Save metrics to .loom/reports/metrics.json."""
        reports_dir = self.root / ".loom" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        path = reports_dir / "metrics.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)
        return path

    def _read_index(self) -> dict[str, Any]:
        """Read rules.json for boundaries."""
        path = self.root / ".context" / "rules.json"
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _find_src_root(self) -> Path:
        """Find src root directory."""
        for name in ["src", "lib", "app"]:
            candidate = self.root / name
            if candidate.is_dir():
                return candidate
        return self.root
