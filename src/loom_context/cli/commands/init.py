"""loom init: scan project and create .context/ folder."""

from __future__ import annotations

import time
from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from loom_context import __version__
from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path: str) -> None:
    """Scan project and create .context/ folder with all context files."""
    from loom_context.brand import (
        LOOMY_ALERT,
        LOOMY_CURIOUS,
        LOOMY_HAPPY,
        LOOMY_THINKING,
        loomy_banner,
    )
    from loom_context.engine import LoomEngine
    from loom_context.generators.index import generate_quick_rules

    root = Path(path).resolve()
    banner = loomy_banner(__version__)
    console.print(Panel(banner, subtitle="Architecture Context for AI Agents"))
    console.print(f"\n  {LOOMY_THINKING} Scanning [cyan]{root}[/cyan]...\n")

    start = time.time()
    engine = LoomEngine(root)
    result = engine.init()
    elapsed = time.time() - start

    scan = result["scan_result"]

    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Project Type", scan.structure.project_type)
    if scan.structure.language:
        table.add_row("Language", scan.structure.language)
    # Architecture with confidence
    arch_parts = []
    for a in scan.structure.architecture:
        conf = scan.structure.architecture_confidence.get(a, {})
        if conf:
            arch_parts.append(f"{a} ({conf.get('confidence', '')})")
        else:
            arch_parts.append(a)
    table.add_row("Architecture", ", ".join(arch_parts))
    table.add_row("Files Scanned", str(scan.structure.total_files))
    table.add_row("Code Files", str(scan.code.total_code_files))
    table.add_row("Docs Found", str(scan.docs.doc_count))
    table.add_row("Dependencies", str(len(scan.deps.dependencies)))
    table.add_row("Ecosystem", scan.deps.ecosystem)
    table.add_row("Package Manager", scan.deps.package_manager)

    console.print(table)

    # Generated files
    console.print("\n  Generated [green].context/[/green]")
    for fname in result["generated_files"]:
        console.print(f"    [green]+[/green] {fname}")

    # Quick rules preview
    quick_rules = generate_quick_rules(scan.to_dict())
    if quick_rules:
        console.print(f"\n  Quick Rules ({len(quick_rules)}):")
        for rule in quick_rules[:5]:
            console.print(f"    [yellow]>[/yellow] {rule}")
        if len(quick_rules) > 5:
            console.print(f"    ... and {len(quick_rules) - 5} more")

    # Audit findings
    audit = result.get("audit", {})
    errors = audit.get("errors", 0)
    warnings = audit.get("warnings", 0)
    if errors or warnings:
        console.print(
            f"\n  Audit  [red]{errors} errors[/red], [yellow]{warnings} warnings[/yellow]"
        )
        console.print("  Run [cyan]loom audit[/cyan] for details.")
    else:
        console.print("\n  Audit  [green]clean[/green]")

    # Farewell
    if scan.structure.total_files == 0:
        console.print(f"\n  {LOOMY_CURIOUS} [dim]empty project... nothing to weave yet[/dim]")
    elif errors:
        console.print(f"\n  {LOOMY_ALERT} [dim]some threads need attention[/dim]")
    else:
        console.print(f"\n  {LOOMY_HAPPY} [dim]all threads connected[/dim]")
    console.print(f"  Done in [bold]{elapsed:.1f}s[/bold]\n")
