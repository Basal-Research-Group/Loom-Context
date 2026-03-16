"""loom log: session memory between development sessions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from loom_context.cli import console


@click.command(name="log")
@click.argument("message", required=False)
@click.option("--path", "-p", default=".", type=click.Path(exists=True), help="Project path")
@click.option("--show", "do_show", is_flag=True, help="Show recent entries")
@click.option("--last", "last_n", type=int, default=5, help="Number of entries to show")
@click.option("--clear", "do_clear", is_flag=True, help="Clear session log")
def log_cmd(message: Optional[str], path: str, do_show: bool, last_n: int, do_clear: bool) -> None:
    """Session memory: log progress between development sessions."""
    from loom_context.store.session import SessionLogger

    root = Path(path).resolve()
    loom_dir = root / ".loom"
    loom_dir.mkdir(exist_ok=True)
    logger = SessionLogger(loom_dir, root)

    if do_clear:
        count = logger.clear()
        console.print(f"  Cleared {count} session entries.")
        return

    if do_show:
        entries = logger.read(count=last_n)
        if not entries:
            console.print("  No session entries.")
            return
        console.print(f"\n  Session Log (last {len(entries)})\n")
        for entry in entries:
            ts = entry.timestamp[:19].replace("T", " ")
            branch_info = f" {entry.branch}" if entry.branch else ""
            sha_info = f" ({entry.sha})" if entry.sha else ""
            console.print(f"  [dim]{ts}[/dim]{branch_info}{sha_info}")
            console.print(f'    "{entry.message}"')
            if entry.modified_files:
                files = ", ".join(entry.modified_files[:5])
                overflow = len(entry.modified_files) - 5
                extra = f" +{overflow}" if overflow > 0 else ""
                console.print(f"    [dim]Modified: {files}{extra}[/dim]")
            console.print("")
        return

    if not message:
        console.print("[red]Error:[/red] Provide a message or use --show / --clear.")
        console.print('  Usage: loom log "your message here"')
        sys.exit(1)

    from loom_context.brand import LOOMY_HAPPY

    entry = logger.append(message)
    branch_info = f" ({entry.branch})" if entry.branch else ""
    console.print(f"  {LOOMY_HAPPY} Logged{branch_info}")
    if entry.modified_files:
        console.print(f"    Modified: {len(entry.modified_files)} files")
