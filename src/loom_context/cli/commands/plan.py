"""loom plan: read and summarize existing docs/plans."""

from __future__ import annotations

from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def plan(path: str) -> None:
    """Read and summarize existing docs/plans for AI consumption."""
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

    for doc_type, docs_in_type in sorted(by_type.items()):
        console.print(f"\n  [bold]{doc_type.upper()}[/bold] ({len(docs_in_type)} files)")
        for doc in docs_in_type:
            title = doc.title or doc.path
            console.print(f"    [cyan]{doc.path}[/cyan]  {title}  ({doc.size_kb}KB)")

            if doc.status_items:
                done = sum(1 for s in doc.status_items if s["status"] == "done")
                total = len(doc.status_items)
                console.print(f"      Status: {done}/{total} done")
