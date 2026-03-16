"""loom prompt: generate master AI system prompt."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout instead of file")
@click.option("--output", "-o", "output_file", help="Write prompt to file")
def prompt(path: str, to_stdout: bool, output_file: Optional[str]) -> None:
    """Generate master AI system prompt from .context/ files."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print("[red]Error:[/red] No .context/ found. Run 'loom init' first.")
        sys.exit(1)

    engine = LoomEngine(root)
    prompt_text = engine.generate_prompt()

    if output_file:
        Path(output_file).write_text(prompt_text, encoding="utf-8")
        console.print(
            f"  Prompt written to [green]{output_file}[/green] ({len(prompt_text)} chars)"
        )
    elif to_stdout:
        click.echo(prompt_text)
    else:
        console.print(
            Panel(
                f"Master prompt generated: [bold]{len(prompt_text)}[/bold] characters, "
                f"[bold]{len(prompt_text.splitlines())}[/bold] lines",
                title="Loom Prompt",
            )
        )
        console.print("\nUse [cyan]loom prompt --stdout[/cyan] to pipe to clipboard or file.")
        console.print("Use [cyan]loom prompt -o prompt.md[/cyan] to save to file.")
