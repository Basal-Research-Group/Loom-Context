"""loom bundle: generate task-specific context bundle."""

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
@click.option("--max-chars", default=12000, help="Target max characters")
@click.option("--top-k", default=0, help="Max number of sections to include (0=unlimited)")
@click.option("--token-budget", default=0, help="Approx token budget (0=use max-chars)")
@click.option("--compact", is_flag=True, help="Token-efficient compact format")
@click.option("--save", "do_save", is_flag=True, help="Save to .context/bundles/")
def bundle(
    task: str,
    path: str,
    to_stdout: bool,
    output_file: Optional[str],
    max_chars: int,
    top_k: int,
    token_budget: int,
    compact: bool,
    do_save: bool,
) -> None:
    """Generate a task-specific context bundle."""
    from loom_context.brand import LOOMY_CURIOUS, LOOMY_FAIL, LOOMY_HAPPY, LOOMY_THINKING
    from loom_context.selector.bundle import BundleBuilder

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
        sys.exit(1)

    # Token budget conversion
    effective_chars = token_budget * 4 if token_budget > 0 else max_chars
    has_budget = token_budget > 0

    console.print(f'  {LOOMY_THINKING} Weaving bundle for [cyan]"{task}"[/cyan]...')

    builder = BundleBuilder(context_dir, root)

    if do_save:
        result = builder.save(task, max_chars=effective_chars, top_k=top_k)
        if result is None:
            msg = f'No relevant context found for "{task}". Try a more specific description.'
            console.print(f"  {LOOMY_CURIOUS} [yellow]{msg}[/yellow]")
            sys.exit(1)
        bundle_path, manifest_path = result
        content = bundle_path.read_text(encoding="utf-8")
        tokens = _estimate_tokens(content)
        console.print(f"  {LOOMY_HAPPY} Bundle saved ({len(content)} chars, ~{tokens:,} tokens)")
        console.print(f"    [green]+[/green] {bundle_path.relative_to(root)}")
        console.print(f"    [green]+[/green] {manifest_path.relative_to(root)}")
        if has_budget:
            _show_budget(tokens, token_budget)
        return

    build_result = builder.build(task, max_chars=effective_chars, top_k=top_k)
    if build_result is None:
        msg = f'No relevant context found for "{task}". Try a more specific description.'
        console.print(f"  {LOOMY_CURIOUS} [yellow]{msg}[/yellow]")
        sys.exit(1)

    content, manifest = build_result

    # Compact mode: reformat for token efficiency
    if compact:
        from loom_context.selector.compact import CompactFormatter

        formatter = CompactFormatter(context_dir)
        content = formatter.format_for_task(task, builder.last_candidates or [])

    # Calculate savings vs full prompt
    savings_line = _savings_line(content, root / ".context")

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        chars = len(content)
        console.print(
            f"  {LOOMY_HAPPY} Bundle written to [green]{output_file}[/green] ({chars} chars)"
        )
        if savings_line:
            console.print(f"  {savings_line}")
    elif to_stdout:
        click.echo(content)
    else:
        console.print(
            Panel(
                f'  {LOOMY_HAPPY} Bundle for [bold]"{task}"[/bold]\n'
                f"  [bold]{len(content)}[/bold] chars | "
                f"[bold]{manifest.included_count}[/bold] sections | "
                f"strategy: {manifest.selection_strategy}"
                + (f"\n  {savings_line}" if savings_line else ""),
                title="Loom Bundle",
            )
        )
        console.print(f'\n  Use [cyan]loom bundle "{task}" --stdout[/cyan] to pipe output.')
        console.print(f'  Use [cyan]loom bundle "{task}" --save[/cyan] to persist.')

    if has_budget and not to_stdout:
        _show_budget(_estimate_tokens(content), token_budget)


def _savings_line(content: str, context_dir: Path) -> str:
    """Calculate token savings vs full prompt."""
    from loom_context.generators.prompt import PromptGenerator

    try:
        gen = PromptGenerator(context_dir)
        full = gen.generate()
    except Exception:
        return ""

    full_tokens = _estimate_tokens(full)
    bundle_tokens = _estimate_tokens(content)

    if full_tokens <= 0:
        return ""

    saved_pct = int((1 - bundle_tokens / full_tokens) * 100)
    if saved_pct <= 0:
        return ""

    return (
        f"[dim]~{bundle_tokens:,} tokens vs ~{full_tokens:,} full prompt "
        f"([green]{saved_pct}% saved[/green])[/dim]"
    )


def _estimate_tokens(text: str) -> int:
    """Estimate token count. Uses word-based heuristic (~1.3 tokens per word)."""
    words = len(text.split())
    return int(words * 1.3)


def _show_budget(used_tokens: int, budget: int) -> None:
    """Show token budget usage."""
    pct = int(used_tokens / budget * 100) if budget > 0 else 0
    if used_tokens > budget:
        console.print(
            f"  [yellow]⚠ Budget: ~{used_tokens:,}/{budget:,} tokens ({pct}%) — exceeded[/yellow]"
        )
    else:
        console.print(f"  [dim]Budget: ~{used_tokens:,}/{budget:,} tokens ({pct}%)[/dim]")
