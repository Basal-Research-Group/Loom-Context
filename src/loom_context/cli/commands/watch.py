"""loom watch: continuous mode, re-scan on interval."""

from __future__ import annotations

import time
from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--interval", default=30, help="Seconds between scans")
def watch(path: str, interval: int) -> None:
    """Continuous mode: re-scan on interval."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    console.print(f"  Watching [cyan]{root}[/cyan] every {interval}s. Press Ctrl+C to stop.\n")

    engine = LoomEngine(root)

    try:
        while True:
            start = time.time()
            scan_result = engine.scan()
            engine.generate_context(scan_result)
            elapsed = time.time() - start
            console.print(f"  [{time.strftime('%H:%M:%S')}] Updated .context/ in {elapsed:.1f}s")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n  Stopped.")
