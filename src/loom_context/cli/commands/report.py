"""loom report: show usage analytics."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def report(path: str) -> None:
    """Show usage analytics from .loom/reports/."""
    from loom_context.brand import LOOMY, LOOMY_CURIOUS
    from loom_context.store.reporter import UsageReporter

    root = Path(path).resolve()
    loom_dir = root / ".loom"

    reporter = UsageReporter(loom_dir, root)
    summary = reporter.summary()

    if not summary:
        console.print(f"  {LOOMY_CURIOUS} No usage data yet. Use Loom commands first.")
        return

    table = Table(title="Usage Analytics")
    table.add_column("Command", style="cyan")
    table.add_column("Runs", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Total", justify="right")

    for cmd, stats in summary.items():
        avg = f"{stats['avg_ms']}ms"
        total = f"{stats['total_ms']}ms"
        table.add_row(cmd, str(stats["runs"]), avg, total)

    console.print(table)
    console.print(f"\n  {LOOMY} data from [green].loom/reports/usage.jsonl[/green]\n")
