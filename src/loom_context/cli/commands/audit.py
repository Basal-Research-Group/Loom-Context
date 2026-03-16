"""loom audit: validate code against rules defined in .context/."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.command()
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

    naming_auditor = NamingAuditor(root, file_filter)
    naming_auditor.load_rules()
    naming_violations = naming_auditor.audit()

    structure_auditor = StructureAuditor(root, file_filter)
    structure_auditor.load_rules()
    structure_violations = structure_auditor.audit()

    all_violations = naming_violations + structure_violations

    if not all_violations:
        from loom_context.brand import LOOMY_HAPPY

        console.print(f"  {LOOMY_HAPPY} [green]No violations found.[/green]")
        return

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
