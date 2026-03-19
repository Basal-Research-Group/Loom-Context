"""loom scan: re-scan project and update .context/ files."""

from __future__ import annotations

import time
from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--force", "-f", is_flag=True, help="Force full re-scan, ignore cache")
def scan(path: str, force: bool) -> None:
    """Re-scan project and update .context/ files."""
    from loom_context.brand import LOOMY_HAPPY, LOOMY_THINKING, LOOMY_WINK
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    console.print(f"  {LOOMY_THINKING} Scanning [cyan]{root}[/cyan]...")

    start = time.time()
    engine = LoomEngine(root)
    scan_result = engine.scan(force=force)
    elapsed = time.time() - start

    if engine.was_cached:
        console.print(f"  {LOOMY_WINK} No changes detected — skipped (cached)")
        console.print(f"  Done in [bold]{elapsed:.2f}s[/bold]")
        return

    generated = engine.generate_context(scan_result)

    console.print(f"  {LOOMY_HAPPY} Updated {len(generated)} files in .context/")
    console.print(f"  Done in [bold]{elapsed:.1f}s[/bold]")
