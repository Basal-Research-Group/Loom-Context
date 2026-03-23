"""loom trace: view and record resolution traces."""

from __future__ import annotations

import json as json_mod
from pathlib import Path

import click

from loom_context.cli import console


@click.group()
def trace() -> None:
    """View and manage resolution traces."""


@trace.command("list")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--count", "-n", default=10, help="Number of traces to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def trace_list(path: str, count: int, as_json: bool) -> None:
    """List recent resolution traces."""
    from loom_context.store.traces import TraceStore

    root = Path(path).resolve()
    loom_dir = root / ".loom"
    store = TraceStore(loom_dir, root)
    traces = store.read(count=count)

    if as_json:
        click.echo(json_mod.dumps([t.to_dict() for t in traces], indent=2, ensure_ascii=False))
        return

    if not traces:
        console.print("  No traces recorded. Use 'loom trace record' to add one.")
        return

    for t in traces:
        ts = t.timestamp[:16].replace("T", " ")
        outcome_color = {"success": "green", "partial": "yellow", "failed": "red"}.get(
            t.outcome, "dim"
        )
        console.print(
            f"  [dim]{ts}[/dim] [{outcome_color}]{t.outcome}[/{outcome_color}] "
            f"[bold]{t.agent}[/bold] {t.query[:60]}"
        )
        if t.selected_files:
            console.print(f"    files: {len(t.selected_files)} selected, {len(t.changed_files)} changed")
        if t.confidence > 0:
            console.print(f"    confidence: {t.confidence:.2f} ({t.selection_strategy})")
    console.print("")


@trace.command("record")
@click.argument("query")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--agent", "-a", default="generic", help="Agent name (claude, codex, cursor, copilot)")
@click.option("--outcome", "-o", default="pending", type=click.Choice(["success", "partial", "failed", "pending"]))
@click.option("--domain", "-d", default="unknown", help="Project domain")
@click.option("--confidence", "-c", default=0.0, type=float, help="Confidence score (0.0-1.0)")
@click.option("--notes", "-n", default="", help="Additional notes")
def trace_record(
    query: str, path: str, agent: str, outcome: str, domain: str, confidence: float, notes: str
) -> None:
    """Record a resolution trace."""
    from loom_context.brand import LOOMY_HAPPY
    from loom_context.store.traces import TraceStore

    root = Path(path).resolve()
    loom_dir = root / ".loom"
    loom_dir.mkdir(exist_ok=True)
    store = TraceStore(loom_dir, root)

    trace = store.record(
        query=query,
        domain=domain,
        agent=agent,
        outcome=outcome,
        confidence=confidence,
        notes=notes,
    )
    console.print(f"  {LOOMY_HAPPY} Trace recorded: {trace.task_id}")


@trace.command("stats")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def trace_stats(path: str, as_json: bool) -> None:
    """Show trace statistics."""
    from loom_context.store.traces import TraceStore

    root = Path(path).resolve()
    loom_dir = root / ".loom"
    store = TraceStore(loom_dir, root)
    stats = store.stats()

    if as_json:
        click.echo(json_mod.dumps(stats, indent=2, ensure_ascii=False))
        return

    if stats["total"] == 0:
        console.print("  No traces recorded yet.")
        return

    console.print(f"  Traces: {stats['total']}")
    outcomes = stats.get("outcomes", {})
    console.print(
        f"  Outcomes: [green]{outcomes.get('success', 0)} success[/green], "
        f"[yellow]{outcomes.get('partial', 0)} partial[/yellow], "
        f"[red]{outcomes.get('failed', 0)} failed[/red], "
        f"{outcomes.get('pending', 0)} pending"
    )
    if stats.get("agents"):
        agents_str = ", ".join(f"{k}: {v}" for k, v in stats["agents"].items())
        console.print(f"  Agents: {agents_str}")
    if stats.get("avg_confidence", 0) > 0:
        console.print(f"  Avg confidence: {stats['avg_confidence']:.2f}")
    if stats.get("total_tokens", 0) > 0:
        console.print(f"  Total tokens: {stats['total_tokens']:,}")
    console.print("")
