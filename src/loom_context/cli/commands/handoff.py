"""loom handoff: generate session continuity summary."""

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
@click.option("--save", "do_save", is_flag=True, help="Save to .context/handoffs/")
def handoff(
    task: str, path: str, to_stdout: bool, output_file: Optional[str], do_save: bool
) -> None:
    """Generate a handoff summary for resuming work on a task."""
    from loom_context.brand import LOOMY_FAIL, LOOMY_HAPPY
    from loom_context.selector.handoff import HandoffBuilder

    root = Path(path).resolve()
    context_dir = root / ".context"
    loom_dir = root / ".loom"

    if not context_dir.exists():
        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    builder = HandoffBuilder(context_dir, loom_dir, root)

    if do_save:
        saved = builder.save(task)
        if saved is None:
            console.print(f"  {LOOMY_FAIL} [red]Could not generate handoff.[/red]")
            sys.exit(1)
        console.print(f"  {LOOMY_HAPPY} Handoff saved")
        console.print(f"    [green]+[/green] {saved.relative_to(root)}")
        return

    content = builder.build(task)
    if content is None:
        console.print(f"  {LOOMY_FAIL} [red]Could not generate handoff.[/red]")
        sys.exit(1)

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        chars = len(content)
        console.print(
            f"  {LOOMY_HAPPY} Handoff written to [green]{output_file}[/green] ({chars} chars)"
        )
    elif to_stdout:
        click.echo(content)
    else:
        console.print(
            Panel(
                f'  {LOOMY_HAPPY} Handoff for [bold]"{task}"[/bold]\n'
                f"  [bold]{len(content)}[/bold] chars | "
                f"includes: state, decisions, sessions, rules",
                title="Loom Handoff",
            )
        )
        console.print(f'\n  Use [cyan]loom handoff "{task}" --stdout[/cyan] to pipe.')
        console.print(f'  Use [cyan]loom handoff "{task}" --save[/cyan] to persist.')
