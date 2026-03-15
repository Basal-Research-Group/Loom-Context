"""Loom CLI: command-line interface for Loom-Context."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from loom_context import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="loom")
def main() -> None:
    """Loom - Architecture Context Engine for AI-First Engineering."""


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path: str) -> None:
    """Scan project and create .context/ folder with all context files."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    console.print(Panel(
        f"[bold blue]Loom Context Engine[/bold blue] v{__version__}",
        subtitle="Architecture Context for AI Agents",
    ))
    console.print(f"\n  Scanning [cyan]{root}[/cyan]...\n")

    start = time.time()
    engine = LoomEngine(root)
    result = engine.init()
    elapsed = time.time() - start

    scan = result["scan_result"]
    structure = scan.get("structure", {})
    deps = scan.get("deps", {})
    code = scan.get("code", {})
    docs = scan.get("docs", {})

    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Project Type", structure.get("project_type", "unknown"))
    table.add_row("Architecture", ", ".join(structure.get("architecture", [])))
    table.add_row("Files Scanned", str(structure.get("total_files", 0)))
    table.add_row("Code Files", str(code.get("total_code_files", 0)))
    table.add_row("Docs Found", str(docs.get("doc_count", 0)))
    table.add_row("Dependencies", str(len(deps.get("dependencies", []))))
    table.add_row("Package Manager", deps.get("package_manager", "unknown"))

    console.print(table)

    # Generated files
    console.print("\n  Generated [green].context/[/green]")
    for fname in result["generated_files"]:
        console.print(f"    [green]+[/green] {fname}")

    # Quick rules preview
    from loom_context.generators.index import generate_quick_rules
    quick_rules = generate_quick_rules(scan)
    if quick_rules:
        console.print(f"\n  Quick Rules ({len(quick_rules)}):")
        for rule in quick_rules[:5]:
            console.print(f"    [yellow]>[/yellow] {rule}")
        if len(quick_rules) > 5:
            console.print(f"    ... and {len(quick_rules) - 5} more")

    console.print(f"\n  Done in [bold]{elapsed:.1f}s[/bold]\n")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def scan(path: str) -> None:
    """Re-scan project and update .context/ files."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    console.print(f"  Scanning [cyan]{root}[/cyan]...")

    start = time.time()
    engine = LoomEngine(root)
    scan_result = engine.scan()
    generated = engine.generate_context(scan_result)
    elapsed = time.time() - start

    console.print(f"  Updated {len(generated)} files in .context/")
    console.print(f"  Done in [bold]{elapsed:.1f}s[/bold]")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", "to_stdout", is_flag=True, help="Print to stdout instead of file")
@click.option("--output", "-o", "output_file", help="Write prompt to file")
def prompt(path: str, to_stdout: bool, output_file: Optional[str]) -> None:
    """Generate master AI system prompt from .context/ files."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print("[red]Error:[/red] No .context/ found. Run 'loom init' first.")
        sys.exit(1)

    engine = LoomEngine(root)
    prompt_text = engine.generate_prompt()

    if output_file:
        Path(output_file).write_text(prompt_text, encoding="utf-8")
        console.print(
            f"  Prompt written to [green]{output_file}[/green] ({len(prompt_text)} chars)"
        )
    elif to_stdout:
        click.echo(prompt_text)
    else:
        # Print to terminal with formatting
        console.print(Panel(
            f"Master prompt generated: [bold]{len(prompt_text)}[/bold] characters, "
            f"[bold]{len(prompt_text.splitlines())}[/bold] lines",
            title="Loom Prompt",
        ))
        console.print("\nUse [cyan]loom prompt --stdout[/cyan] to pipe to clipboard or file.")
        console.print("Use [cyan]loom prompt -o prompt.md[/cyan] to save to file.")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def audit(path: str) -> None:
    """Validate code against rules defined in .context/."""
    from loom_context.auditors.naming import NamingAuditor
    from loom_context.auditors.structure import StructureAuditor
    from loom_context.security.filter import FileFilter

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print("[red]Error:[/red] No .context/ found. Run 'loom init' first.")
        sys.exit(1)

    file_filter = FileFilter(root)

    console.print(f"  Auditing [cyan]{root}[/cyan]...\n")

    # Run auditors
    naming_auditor = NamingAuditor(root, file_filter)
    naming_auditor.load_rules()
    naming_violations = naming_auditor.audit()

    structure_auditor = StructureAuditor(root, file_filter)
    structure_auditor.load_rules()
    structure_violations = structure_auditor.audit()

    all_violations = naming_violations + structure_violations

    if not all_violations:
        console.print("  [green]No violations found.[/green]")
        return

    # Display violations
    table = Table(title="Audit Results")
    table.add_column("Severity", width=8)
    table.add_column("File", style="cyan")
    table.add_column("Line", width=5)
    table.add_column("Rule", style="yellow")
    table.add_column("Message")
    table.add_column("Suggestion", style="dim")

    errors = 0
    warnings = 0

    for v in sorted(all_violations, key=lambda x: (x.severity != "error", x.file)):
        severity_style = {
            "error": "[red]ERROR[/red]",
            "warning": "[yellow]WARN[/yellow]",
            "info": "[blue]INFO[/blue]",
        }.get(v.severity, v.severity)

        if v.severity == "error":
            errors += 1
        elif v.severity == "warning":
            warnings += 1

        table.add_row(
            severity_style,
            v.file,
            str(v.line) if v.line else "-",
            v.rule,
            v.message,
            v.suggestion,
        )

    console.print(table)
    console.print(
        f"\n  Summary: [red]{errors} errors[/red], "
        f"[yellow]{warnings} warnings[/yellow], "
        f"{len(all_violations)} total"
    )

    if errors > 0:
        sys.exit(1)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def plan(path: str) -> None:
    """Read and summarize existing docs/plans for AI consumption."""
    from loom_context.engine import LoomEngine

    root = Path(path).resolve()
    engine = LoomEngine(root)
    scan_result = engine.scan()

    docs = scan_result.get("docs", {})
    doc_list = docs.get("docs", [])

    if not doc_list:
        console.print("  No documentation files found.")
        return

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for doc in doc_list:
        by_type.setdefault(doc["type"], []).append(doc)

    for doc_type, docs_in_type in sorted(by_type.items()):
        console.print(f"\n  [bold]{doc_type.upper()}[/bold] ({len(docs_in_type)} files)")
        for doc in docs_in_type:
            title = doc["title"] or doc["path"]
            console.print(f"    [cyan]{doc['path']}[/cyan]  {title}  ({doc['size_kb']}KB)")

            if doc["status_items"]:
                done = sum(1 for s in doc["status_items"] if s["status"] == "done")
                total = len(doc["status_items"])
                console.print(f"      Status: {done}/{total} done")


@main.command()
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
