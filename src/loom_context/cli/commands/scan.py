"""loom scan: re-scan project and update .context/ files."""

from __future__ import annotations

import time
from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def scan(path: str) -> None:
    """Re-scan project and update .context/ files."""
    from loom_context.brand import LOOMY_HAPPY, LOOMY_THINKING
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    console.print(f"  {LOOMY_THINKING} Scanning [cyan]{root}[/cyan]...")

    start = time.time()
    engine = LoomEngine(root)
    scan_result = engine.scan()
    generated = engine.generate_context(scan_result)
    elapsed = time.time() - start

    console.print(f"  {LOOMY_HAPPY} Updated {len(generated)} files in .context/")
    console.print(f"  Done in [bold]{elapsed:.1f}s[/bold]")
