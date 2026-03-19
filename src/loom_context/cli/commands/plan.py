"""loom plan: read and summarize existing docs/plans, or generate implementation plan."""

from __future__ import annotations

from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--generate", is_flag=True, help="Generate implementation plan from Loom data")
@click.option("--stdout", "to_stdout", is_flag=True, help="Print generated plan to stdout")
def plan(path: str, generate: bool, to_stdout: bool) -> None:
    """Read and summarize existing docs/plans for AI consumption."""
    if generate:
        _generate_plan(path, to_stdout=to_stdout)
    else:
        _list_plans(path)


def _generate_plan(path: str, to_stdout: bool = False) -> None:
    """Generate an implementation plan from .context/ and .loom/ data."""
    from loom_context.brand import LOOMY_HAPPY
    from loom_context.generators.plan import PlanGenerator

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print("  [red]No .context/ found.[/red] Run [cyan]loom init .[/cyan] first.")
        return

    generator = PlanGenerator(root)
    output_path = generator.generate()

    if to_stdout:
        content = Path(output_path).read_text(encoding="utf-8")
        click.echo(content)
        return

    rel_path = Path(output_path).relative_to(root)
    console.print(f"\n  {LOOMY_HAPPY} Implementation plan generated")
    console.print(f"  [green]+[/green] {rel_path}\n")


def _list_plans(path: str) -> None:
    """List and summarize existing documentation plans."""
    from loom_context.brand import LOOMY_HAPPY
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    engine = LoomEngine(root)
    scan_result = engine.scan()

    doc_list = scan_result.docs.docs

    if not doc_list:
        console.print("  No documentation files found.")
        return

    by_type: dict[str, list] = {}
    for doc in doc_list:
        by_type.setdefault(doc.type, []).append(doc)

    total_docs = 0
    for doc_type, docs_in_type in sorted(by_type.items()):
        console.print(f"\n  [bold]{doc_type.upper()}[/bold] ({len(docs_in_type)} files)")
        for doc in docs_in_type:
            total_docs += 1
            title = doc.title or doc.path

            # Frontmatter badges
            badges = ""
            if doc.version:
                badges += f" [blue]v{doc.version}[/blue]"
            if doc.doc_status:
                status_colors = {
                    "planned": "dim",
                    "in-progress": "yellow",
                    "released": "green",
                    "archived": "dim",
                    "deferred": "red",
                }
                color = status_colors.get(doc.doc_status, "dim")
                badges += f" [{color}]{doc.doc_status}[/{color}]"
            if doc.progress:
                badges += f" [cyan]{doc.progress}[/cyan]"

            console.print(f"    [cyan]{doc.path}[/cyan]  {title}  ({doc.size_kb}KB){badges}")

            if doc.status_items:
                done = sum(1 for s in doc.status_items if s["status"] == "done")
                total = len(doc.status_items)
                if total > 0:
                    pct = int(done / total * 100)
                    bar = "=" * (pct // 5) + "-" * (20 - pct // 5)
                    console.print(f"      [{bar}] {done}/{total} ({pct}%)")

    console.print(f"\n  {LOOMY_HAPPY} {total_docs} docs indexed\n")
