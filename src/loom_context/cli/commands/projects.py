"""loom projects: list all projects using Loom on this machine."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.command()
@click.option("--add", "add_desc", default="", help="Add description to current project")
@click.option("--remove", "do_remove", is_flag=True, help="Remove current project")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def projects(add_desc: str, do_remove: bool, as_json: bool) -> None:
    """List all projects using Loom on this machine.

    \b
    Run from any directory to see all registered projects.
    Projects are auto-registered when you run loom init or loom scan.
    """
    from loom_context.store.registry import (
        get_all_projects,
        register_project,
        unregister_project,
    )

    if do_remove:
        root = Path.cwd().resolve()
        if unregister_project(root):
            console.print(f"  Removed [cyan]{root.name}[/cyan] from registry")
        else:
            console.print("  Project not found in registry")
        return

    if add_desc:
        root = Path.cwd().resolve()
        register_project(root, description=add_desc)
        console.print(f"  Updated [cyan]{root.name}[/cyan]: {add_desc}")
        return

    all_projects = get_all_projects()

    if not all_projects:
        console.print("  No projects registered yet.")
        console.print("  Run [cyan]loom init .[/cyan] in a project to register it.")
        return

    if as_json:
        import json

        click.echo(json.dumps(all_projects, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Loom Projects ({len(all_projects)})")
    table.add_column("Project", style="cyan")
    table.add_column("Type")
    table.add_column("Language")
    table.add_column("Architecture")
    table.add_column("Ecosystem")
    table.add_column("Description", style="dim")

    for p in sorted(all_projects, key=lambda x: x.get("name", "")):
        arch = ", ".join(p.get("architecture", [])[:2])
        if len(p.get("architecture", [])) > 2:
            arch += "..."
        mono = " [mono]" if p.get("is_monorepo") else ""
        path_exists = Path(p["path"]).exists()
        name = p.get("name", "?")
        if not path_exists:
            name = f"[dim strikethrough]{name}[/dim strikethrough]"

        table.add_row(
            name,
            p.get("type", ""),
            p.get("language", ""),
            arch + mono,
            p.get("ecosystem", ""),
            p.get("description", ""),
        )

    console.print()
    console.print(table)
    console.print()
