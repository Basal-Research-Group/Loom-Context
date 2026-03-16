"""loom enrich: re-audit, refine rules, persist findings."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def enrich(path: str) -> None:
    """Enrich context: re-audit, refine rules, persist findings."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print("[red]Error:[/red] No .context/ found. Run 'loom init' first.")
        sys.exit(1)

    console.print(f"  Enriching [cyan]{root}[/cyan]...\n")

    start = time.time()
    engine = LoomEngine(root)
    result = engine.enrich()
    elapsed = time.time() - start

    audit = result.get("audit", {})
    errors = audit.get("errors", 0)
    warnings = audit.get("warnings", 0)

    console.print(f"  Updated {len(result['generated_files'])} files in .context/")

    if errors or warnings:
        console.print(f"  Audit  [red]{errors} errors[/red], [yellow]{warnings} warnings[/yellow]")
    else:
        console.print("  Audit  [green]clean[/green]")

    console.print("  Findings persisted to [green].loom/inconsistencies.json[/green]")
    console.print(f"\n  Done in [bold]{elapsed:.1f}s[/bold]")
