"""loom decide: record architectural decisions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from loom_context.cli import console


@click.command()
@click.argument("summary", required=False)
@click.option("--rationale", "-r", default="", help="Why this decision was made")
@click.option(
    "--scope",
    "-s",
    default="architecture",
    type=click.Choice(["architecture", "naming", "deps", "security"]),
    help="Decision scope",
)
@click.option("--path", "-p", default=".", type=click.Path(exists=True), help="Project path")
@click.option("--show", "do_show", is_flag=True, help="Show recent decisions")
@click.option("--last", "last_n", type=int, default=10, help="Number of entries to show")
@click.option("--clear", "do_clear", is_flag=True, help="Clear all decisions")
def decide(
    summary: Optional[str],
    rationale: str,
    scope: str,
    path: str,
    do_show: bool,
    last_n: int,
    do_clear: bool,
) -> None:
    """Record an architectural decision."""
    from loom_context.decisions import DecisionLog

    root = Path(path).resolve()
    loom_dir = root / ".loom"
    loom_dir.mkdir(exist_ok=True)
    log = DecisionLog(loom_dir, root)

    if do_clear:
        count = log.clear()
        console.print(f"  Cleared {count} decisions.")
        return

    if do_show:
        entries = log.read(count=last_n)
        if not entries:
            console.print("  No decisions recorded.")
            return
        console.print(f"\n  Decisions (last {len(entries)})\n")
        for entry in entries:
            ts = entry.timestamp[:19].replace("T", " ")
            console.print(f"  [dim]{ts}[/dim]  [{entry.scope}]")
            console.print(f"    [bold]{entry.summary}[/bold]")
            if entry.rationale:
                console.print(f"    [dim]Why: {entry.rationale}[/dim]")
            branch_info = f" {entry.branch}" if entry.branch else ""
            sha_info = f" ({entry.sha})" if entry.sha else ""
            if branch_info or sha_info:
                console.print(f"    [dim]{branch_info}{sha_info}[/dim]")
            console.print("")
        return

    if not summary:
        console.print("[red]Error:[/red] Provide a summary or use --show / --clear.")
        console.print('  Usage: loom decide "decision summary" -r "rationale"')
        sys.exit(1)

    entry = log.append(summary, rationale, scope)
    branch_info = f" ({entry.branch})" if entry.branch else ""
    console.print(f"  [green]+[/green] Decision recorded{branch_info}  [{scope}]")
    console.print(f'    "{summary}"')
