"""Plan generator: synthesizes implementation plans from .context/ and .loom/ data."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from loom_context import __version__
from loom_context.git import GitHelper

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class ViolationCluster:
    """A group of violations sharing the same boundary crossing."""

    source: str
    target: str
    rule: str
    count: int
    files: list[str] = field(default_factory=list)


@dataclass
class PlanPhase:
    """A recommended phase in the implementation plan."""

    name: str
    tasks: list[str] = field(default_factory=list)
    validation: str = ""


class PlanGenerator:
    """Generates implementation plans from Loom context and operational state."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / ".context"
        self.loom_dir = root / ".loom"
        self.reports_dir = self.loom_dir / "reports"
        self._git = GitHelper(root)
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,  # noqa: S701 — generating .md, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self) -> str:
        """Generate an implementation plan and save to .loom/reports/. Returns file path."""
        template = self.env.get_template("implementation.md.j2")

        # Gather all data sources
        findings = self._load_findings()
        metrics = self._load_metrics()
        rules = self._load_json("rules.json")
        delta = self._load_delta()
        docs = self._load_plan_docs()
        decisions = self._load_decisions()

        # Analyze violations
        violations = findings.get("violations", [])
        clusters = self._cluster_violations(violations)
        phases = self._generate_phases(clusters, rules)

        # Collect pending items from existing plans
        pending_items = self._extract_pending_items(docs)

        # Build template data
        data = {
            "project_name": self.root.name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "loom_version": __version__,
            "git_sha": self._git.sha(),
            "branch": self._git.branch(),
            # Architecture state
            "project_type": self._detect_project_type(rules),
            "architecture": rules.get("architecture", {}).get("patterns", []),
            "total_layers": metrics.get("total_layers", 0),
            "total_files": metrics.get("total_files", 0),
            "balance_score": metrics.get("balance_score", 0.0),
            # Violations
            "violations_total": len(violations),
            "violations_by_severity": self._count_by_severity(violations),
            "clusters": [
                {
                    "source": c.source,
                    "target": c.target,
                    "rule": c.rule,
                    "count": c.count,
                    "files": c.files,
                }
                for c in clusters
            ],
            # Delta
            "delta": delta,
            # Phases
            "phases": [
                {"name": p.name, "tasks": p.tasks, "validation": p.validation} for p in phases
            ],
            # Existing plans
            "existing_plans": docs,
            "pending_items": pending_items,
            # Decisions
            "open_decisions": decisions,
        }

        content = template.render(**data)

        # Save to .loom/reports/
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"plan-{date_str}.md"
        path = self.reports_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(path)

    def _load_findings(self) -> dict[str, Any]:
        """Load .loom/inconsistencies.json."""
        return self._load_loom_json("inconsistencies.json")

    def _load_metrics(self) -> dict[str, Any]:
        """Load .loom/reports/metrics.json."""
        path = self.reports_dir / "metrics.json"
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_delta(self) -> Optional[dict[str, Any]]:
        """Load the most recent delta report."""
        if not self.reports_dir.exists():
            return None
        delta_files = sorted(self.reports_dir.glob("delta-*.json"), reverse=True)
        if not delta_files:
            return None
        try:
            with open(delta_files[0], encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return None

    def _load_plan_docs(self) -> list[dict[str, Any]]:
        """Load plan docs from .context/plans-summary.md."""
        docs = []
        # Parse plan doc paths from plans-summary
        plans_path = self.context_dir / "plans-summary.md"
        if plans_path.exists():
            # Parse minimal info from plans-summary
            content = plans_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("Path: `") and line.endswith("`)"):
                    path_str = line[7 : line.index("`", 7)]
                    docs.append({"path": path_str, "doc_status": None, "progress": None})
        return docs

    def _load_decisions(self) -> list[dict[str, Any]]:
        """Load recent decisions from .loom/decisions.jsonl."""
        path = self.loom_dir / "decisions.jsonl"
        if not path.exists():
            return []
        entries: list[dict[str, Any]] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass
        return entries[-10:]

    def _load_json(self, filename: str) -> dict[str, Any]:
        """Load a .context/ JSON file."""
        path = self.context_dir / filename
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_loom_json(self, filename: str) -> dict[str, Any]:
        """Load a .loom/ JSON file."""
        path = self.loom_dir / filename
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _detect_project_type(self, rules: dict[str, Any]) -> str:
        """Detect project type from index or rules."""
        index = self._load_json("index.json")
        project_type: str = index.get("project", {}).get("type", "unknown")
        return project_type

    def _count_by_severity(self, violations: list[dict[str, Any]]) -> dict[str, int]:
        """Count violations by severity."""
        counts: dict[str, int] = Counter()
        for v in violations:
            counts[v.get("severity", "unknown")] += 1
        return dict(counts)

    def _cluster_violations(self, violations: list[dict[str, Any]]) -> list[ViolationCluster]:
        """Group violations into clusters by boundary crossing pattern."""
        clusters_map: dict[str, ViolationCluster] = {}

        for v in violations:
            msg = v.get("message", "")
            rule = v.get("rule", "")
            file_path = v.get("file", "")

            # Extract source→target from boundary violation messages
            source, target = self._parse_boundary(msg, file_path)
            key = f"{source}→{target}:{rule}"

            if key not in clusters_map:
                clusters_map[key] = ViolationCluster(
                    source=source,
                    target=target,
                    rule=rule,
                    count=0,
                )
            cluster = clusters_map[key]
            cluster.count += 1
            if file_path and file_path not in cluster.files:
                cluster.files.append(file_path)

        # Sort by count descending
        return sorted(clusters_map.values(), key=lambda c: c.count, reverse=True)

    def _parse_boundary(self, message: str, file_path: str) -> tuple[str, str]:
        """Extract source and target layers from a violation message."""
        # Common patterns: "core imports from infrastructure", "forbidden import from X to Y"
        msg_lower = message.lower()

        # Try "X should not import from Y" pattern
        if "should not import from" in msg_lower:
            parts = msg_lower.split("should not import from")
            source = parts[0].strip().strip("'\"` ")
            target = parts[1].strip().strip("'\"` ").split()[0] if len(parts) > 1 else "unknown"
            return source, target

        # Try "imports from" pattern
        if "imports from" in msg_lower:
            parts = msg_lower.split("imports from")
            source = parts[0].strip().split()[-1] if parts[0].strip() else "unknown"
            target = parts[1].strip().split()[0] if len(parts) > 1 else "unknown"
            return source, target

        # Fallback: extract layer from file path
        source = self._layer_from_path(file_path)
        return source, "unknown"

    def _layer_from_path(self, file_path: str) -> str:
        """Extract layer name from file path."""
        parts = Path(file_path).parts
        for part in parts:
            if part in {"core", "domain", "infrastructure", "presentation", "ports", "adapters"}:
                return part
        return parts[0] if parts else "unknown"

    def _generate_phases(
        self, clusters: list[ViolationCluster], rules: dict[str, Any]
    ) -> list[PlanPhase]:
        """Generate recommended implementation phases from violation clusters."""
        if not clusters:
            return [PlanPhase(name="No violations", tasks=["Project is clean"])]

        phases: list[PlanPhase] = []

        # Phase 1: highest-count cluster
        if len(clusters) >= 1:
            top = clusters[0]
            phases.append(
                PlanPhase(
                    name=f"Fix {top.source} → {top.target} ({top.count} violations)",
                    tasks=[
                        f"Review imports in {top.source}/ that reference {top.target}/",
                        f"Extract interfaces or use DI tokens to break {top.count} direct imports",
                        f"Move concrete implementations to {top.target}/ if needed",
                        "Run loom enrich to verify reduction",
                    ],
                    validation="loom enrich . && loom metrics .",
                )
            )

        # Phase 2: second cluster
        if len(clusters) >= 2:
            second = clusters[1]
            phases.append(
                PlanPhase(
                    name=f"Fix {second.source} → {second.target} ({second.count} violations)",
                    tasks=[
                        f"Review imports in {second.source}/ that reference {second.target}/",
                        f"Resolve {second.count} boundary crossings",
                        "Run loom enrich to verify reduction",
                    ],
                    validation="loom enrich .",
                )
            )

        # Phase 3: remaining clusters
        remaining = clusters[2:]
        if remaining:
            total_remaining = sum(c.count for c in remaining)
            phases.append(
                PlanPhase(
                    name=(
                        f"Resolve {len(remaining)} remaining clusters"
                        f" ({total_remaining} violations)"
                    ),
                    tasks=[
                        f"Fix {c.source} → {c.target} ({c.count} violations)" for c in remaining[:5]
                    ],
                    validation="loom enrich . && loom metrics .",
                )
            )

        # Final phase: validate
        phases.append(
            PlanPhase(
                name="Validate and baseline",
                tasks=[
                    "Run full test suite",
                    "Run loom init to regenerate context",
                    "Run loom metrics to capture new baseline",
                    "Compare with previous metrics.json in git",
                ],
                validation="pytest && loom init . && loom metrics .",
            )
        )

        return phases

    def _extract_pending_items(self, docs: list[dict[str, Any]]) -> list[str]:
        """Extract pending items from plans-summary.md."""
        plans_path = self.context_dir / "plans-summary.md"
        if not plans_path.exists():
            return []

        pending: list[str] = []
        try:
            content = plans_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("- [ ]"):
                    pending.append(stripped[6:].strip())
                elif stripped.startswith("- [-]"):
                    pending.append(stripped[6:].strip() + " (in progress)")
        except OSError:
            pass
        return pending
