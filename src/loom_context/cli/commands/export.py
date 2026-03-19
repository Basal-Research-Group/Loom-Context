"""loom export: generate agent-specific context files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

from loom_context.cli import console

if TYPE_CHECKING:
    from loom_context.exporters.base import BaseExporter


@click.command(name="export")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--agent",
    "-a",
    required=True,
    type=click.Choice(["claude", "cursor", "codex", "copilot", "generic"]),
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
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation when overwriting existing files",
)
@click.option(
    "--no-backup",
    "no_backup",
    is_flag=True,
    help="Don't backup existing file before overwriting",
)
def export_cmd(
    path: str,
    agent: str,
    to_stdout: bool,
    output_file: Optional[str],
    do_install: bool,
    force: bool,
    no_backup: bool,
) -> None:
    """Export context formatted for a specific AI agent."""
    from loom_context.brand import LOOMY_FAIL, LOOMY_HAPPY
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
        _install_with_safety(exporter, agent, force, no_backup)
        return

    out_path = Path(output_file).resolve() if output_file else None
    saved = exporter.export_to_file(out_path)
    content = saved.read_text(encoding="utf-8")
    chars = len(content)
    tokens = int(len(content.split()) * 1.3)
    console.print(
        f"  {LOOMY_HAPPY} Exported for [bold]{agent}[/bold] ({chars} chars, ~{tokens:,} tokens)"
    )
    console.print(f"    [green]+[/green] {saved}")


def _install_with_safety(
    exporter: BaseExporter,
    agent: str,
    force: bool,
    no_backup: bool,
) -> None:
    """Install agent file with optional backup and confirmation."""
    from loom_context.brand import LOOMY_ALERT, LOOMY_WINK

    target = exporter.install_path()
    exists = exporter.existing_install_exists()

    if exists and not force:
        size = target.stat().st_size
        size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
        console.print(f"  {LOOMY_ALERT} [yellow]{target.name}[/yellow] already exists ({size_str})")
        if not click.confirm("  Overwrite?", default=True):
            console.print("  Skipped.")
            return

    installed, backup = exporter.install_with_backup(skip_backup=no_backup)
    content = installed.read_text(encoding="utf-8")
    chars = len(content)
    tokens = int(len(content.split()) * 1.3)

    console.print(
        f"  {LOOMY_WINK} Installed for [bold]{agent}[/bold] ({chars} chars, ~{tokens:,} tokens)"
    )
    console.print(f"    [green]+[/green] {installed.name}")

    if backup:
        console.print(f"    [dim]backup → .loom/backups/{backup.name}[/dim]")
