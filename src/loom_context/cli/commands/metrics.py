"""loom metrics: quantitative health metrics per layer."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def metrics(path: str, as_json: bool) -> None:
    """Show quantitative health metrics per architectural layer."""
    import json as json_mod

    from loom_context.brand import LOOMY, LOOMY_CURIOUS
    from loom_context.metrics import MetricsCollector

    root = Path(path).resolve()
    collector = MetricsCollector(root)
    result = collector.collect()

    if as_json:
        click.echo(json_mod.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    if not result.layers:
        console.print(f"  {LOOMY_CURIOUS} No layers detected. Run 'loom init' first.")
        return

    table = Table(title="Layer Metrics")
    table.add_column("Layer", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Code", justify="right")
    table.add_column("Dirs", justify="right")
    table.add_column("Share", width=15)

    total = result.total_files or 1
    for layer in result.layers:
        pct = int(layer.file_count / total * 100) if total > 0 else 0
        bar = "=" * (pct // 5) + "-" * (20 - pct // 5) if pct > 0 else "-" * 20
        table.add_row(
            layer.name,
            str(layer.file_count),
            str(layer.code_files),
            str(layer.directories),
            f"[{bar[:15]}] {pct}%",
        )

    console.print(table)
    console.print(
        f"\n  {LOOMY} Balance: [bold]{result.balance_score:.0%}[/bold] | "
        f"Largest: [cyan]{result.largest_layer}[/cyan] | "
        f"Smallest: [cyan]{result.smallest_layer}[/cyan]"
    )

    # Save
    collector.save(result)
    console.print("  Saved to [green].loom/reports/metrics.json[/green]\n")
