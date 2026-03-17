"""loom export: generate agent-specific context files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from loom_context.cli import console


@click.command(name="export")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--agent",
    "-a",
    required=True,
    type=click.Choice(["claude", "cursor", "codex", "generic"]),
    help="Target agent format",
)
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout")
@click.option("--output", "-o", "output_file", help="Write to specific file")
@click.option(
    "--install",
    "do_install",
    is_flag=True,
    help="Install to project root where the agent expects it",
)
def export_cmd(
    path: str,
    agent: str,
    to_stdout: bool,
    output_file: Optional[str],
    do_install: bool,
) -> None:
    """Export context formatted for a specific AI agent."""
    from loom_context.brand import LOOMY_FAIL, LOOMY_HAPPY, LOOMY_WINK
    from loom_context.exporters import get_exporter

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    exporter_cls = get_exporter(agent)
    if exporter_cls is None:
        console.print(f"  {LOOMY_FAIL} [red]Unknown agent: {agent}[/red]")
        sys.exit(1)

    exporter = exporter_cls(context_dir, root)

    if to_stdout:
        click.echo(exporter.export())
        return

    if do_install:
        # Install to where the agent expects it (project root)
        install = exporter.install_path()
        saved = exporter.export_to_file(install)
        chars = len(saved.read_text(encoding="utf-8"))
        console.print(f"  {LOOMY_WINK} Installed for [bold]{agent}[/bold] ({chars} chars)")
        console.print(f"    [green]+[/green] {saved.name}")
        return

    out_path = Path(output_file) if output_file else None
    saved = exporter.export_to_file(out_path)
    chars = len(saved.read_text(encoding="utf-8"))
    console.print(f"  {LOOMY_HAPPY} Exported for [bold]{agent}[/bold] ({chars} chars)")
    console.print(f"    [green]+[/green] {saved.relative_to(root)}")
