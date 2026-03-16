"""loom focus: generate task-specific context prompt."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from loom_context.cli import console


@click.command()
@click.argument("query")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout")
@click.option("--output", "-o", "output_file", help="Write to file")
@click.option("--max-chars", default=8000, help="Target max characters")
def focus(
    query: str, path: str, to_stdout: bool, output_file: Optional[str], max_chars: int
) -> None:
    """Generate a focused context prompt for a specific task."""
    from loom_context.generators.focus import FocusGenerator

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        from loom_context.brand import LOOMY_FAIL

        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    gen = FocusGenerator(context_dir)
    result = gen.generate(query, max_chars=max_chars)

    if result is None:
        console.print("[red]Error:[/red] Could not generate focused context. Check your query.")
        sys.exit(1)

    if output_file:
        Path(output_file).write_text(result, encoding="utf-8")
        console.print(
            f"  Focused context written to [green]{output_file}[/green] ({len(result)} chars)"
        )
    elif to_stdout:
        click.echo(result)
    else:
        console.print(
            Panel(
                f'Focused context for [bold]"{query}"[/bold]: [bold]{len(result)}[/bold] chars',
                title="Loom Focus",
            )
        )
        console.print('\nUse [cyan]loom focus "query" --stdout[/cyan] to pipe output.')
