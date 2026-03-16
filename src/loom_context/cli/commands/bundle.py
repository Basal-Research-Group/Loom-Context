"""loom bundle: generate task-specific context bundle."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from loom_context.cli import console


@click.command()
@click.argument("task")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout")
@click.option("--output", "-o", "output_file", help="Write to file")
@click.option("--max-chars", default=12000, help="Target max characters")
@click.option("--save", "do_save", is_flag=True, help="Save to .context/bundles/")
def bundle(
    task: str,
    path: str,
    to_stdout: bool,
    output_file: Optional[str],
    max_chars: int,
    do_save: bool,
) -> None:
    """Generate a task-specific context bundle."""
    from loom_context.brand import LOOMY_CURIOUS, LOOMY_FAIL, LOOMY_HAPPY, LOOMY_THINKING
    from loom_context.selector.bundle import BundleBuilder

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    console.print(f'  {LOOMY_THINKING} Weaving bundle for [cyan]"{task}"[/cyan]...')

    builder = BundleBuilder(context_dir, root)

    if do_save:
        result = builder.save(task, max_chars=max_chars)
        if result is None:
            msg = "No relevant context found for this task."
            console.print(f"  {LOOMY_CURIOUS} [yellow]{msg}[/yellow]")
            sys.exit(1)
        bundle_path, manifest_path = result
        content = bundle_path.read_text(encoding="utf-8")
        console.print(f"  {LOOMY_HAPPY} Bundle saved ({len(content)} chars)")
        console.print(f"    [green]+[/green] {bundle_path.relative_to(root)}")
        console.print(f"    [green]+[/green] {manifest_path.relative_to(root)}")
        return

    build_result = builder.build(task, max_chars=max_chars)
    if build_result is None:
        msg = "No relevant context found for this task."
        console.print(f"  {LOOMY_CURIOUS} [yellow]{msg}[/yellow]")
        sys.exit(1)

    content, manifest = build_result

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        chars = len(content)
        console.print(
            f"  {LOOMY_HAPPY} Bundle written to [green]{output_file}[/green] ({chars} chars)"
        )
    elif to_stdout:
        click.echo(content)
    else:
        console.print(
            Panel(
                f'  {LOOMY_HAPPY} Bundle for [bold]"{task}"[/bold]\n'
                f"  [bold]{len(content)}[/bold] chars | "
                f"[bold]{manifest.included_count}[/bold] sections | "
                f"strategy: {manifest.selection_strategy}",
                title="Loom Bundle",
            )
        )
        console.print(f'\n  Use [cyan]loom bundle "{task}" --stdout[/cyan] to pipe output.')
        console.print(f'  Use [cyan]loom bundle "{task}" --save[/cyan] to persist.')
