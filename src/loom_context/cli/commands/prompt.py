"""loom prompt: generate master AI system prompt."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout instead of file")
@click.option("--output", "-o", "output_file", help="Write prompt to file")
@click.option("--compact", is_flag=True, help="Token-efficient compact format")
@click.option("--ultra-compact", "ultra", is_flag=True, help="Ultra-compact format (<1KB)")
def prompt(
    path: str, to_stdout: bool, output_file: Optional[str], compact: bool, ultra: bool
) -> None:
    """Generate master AI system prompt from .context/ files."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        from loom_context.brand import LOOMY_FAIL

        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    if ultra:
        from loom_context.selector.compact import CompactFormatter

        formatter = CompactFormatter(context_dir)
        prompt_text = formatter.format_ultra()
    elif compact:
        from loom_context.selector.compact import CompactFormatter

        formatter = CompactFormatter(context_dir)
        prompt_text = formatter.format_all()
    else:
        engine = LoomEngine(root)
        prompt_text = engine.generate_prompt()

    tokens = _estimate_tokens(prompt_text)
    token_info = f"~{tokens:,} tokens"

    # If compact/ultra, show savings vs full
    savings_info = ""
    if compact or ultra:
        engine = LoomEngine(root)
        full_text = engine.generate_prompt()
        full_tokens = _estimate_tokens(full_text)
        if full_tokens > 0:
            saved_pct = int((1 - tokens / full_tokens) * 100)
            if saved_pct > 0:
                savings_info = f" ([green]{saved_pct}% saved[/green] vs full)"

    if output_file:
        out = Path(output_file).resolve()
        out.write_text(prompt_text, encoding="utf-8")
        console.print(
            f"  Prompt written to [green]{output_file}[/green] "
            f"({len(prompt_text)} chars, {token_info})"
        )
    elif to_stdout:
        click.echo(prompt_text)
    else:
        console.print(
            Panel(
                f"Master prompt: [bold]{len(prompt_text)}[/bold] chars, "
                f"[bold]{token_info}[/bold], "
                f"[bold]{len(prompt_text.splitlines())}[/bold] lines"
                + (f"\n  [dim]{savings_info}[/dim]" if savings_info else ""),
                title="Loom Prompt",
            )
        )
        console.print("\nUse [cyan]loom prompt --stdout[/cyan] to pipe to clipboard or file.")
        console.print("Use [cyan]loom prompt -o prompt.md[/cyan] to save to file.")


def _estimate_tokens(text: str) -> int:
    """Estimate token count. Uses word-based heuristic (~1.3 tokens per word)."""
    words = len(text.split())
    return int(words * 1.3)
