"""loom audit: validate code against rules defined in .context/."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--summary", "show_summary", is_flag=True, help="Show grouped summary only")
def audit(path: str, show_summary: bool) -> None:
    """Validate code against rules defined in .context/."""
    from loom_context.auditors.naming import NamingAuditor
    from loom_context.auditors.structure import StructureAuditor
    from loom_context.security.filter import FileFilter

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        from loom_context.brand import LOOMY_FAIL

        console.print(f"  {LOOMY_FAIL} [red]No .context/ found.[/red] Run 'loom init' first.")
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

    errors = sum(1 for v in all_violations if v.severity == "error")
    warnings = sum(1 for v in all_violations if v.severity == "warning")

    if show_summary:
        _show_summary(all_violations, errors, warnings)
    else:
        _show_full(all_violations, errors, warnings)

    if errors > 0:
        sys.exit(1)


def _show_summary(violations: list, errors: int, warnings: int) -> None:
    """Show grouped summary by directory and rule."""
    from loom_context.brand import LOOMY_ALERT

    # Group by directory
    by_dir: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    for v in violations:
        parts = v.file.split("/")
        dir_key = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        by_dir[dir_key] = by_dir.get(dir_key, 0) + 1
        by_rule[v.rule] = by_rule.get(v.rule, 0) + 1

    # By directory
    table = Table(title="Violations by Directory")
    table.add_column("Directory", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Priority", width=20)

    for dir_name, count in sorted(by_dir.items(), key=lambda x: -x[1]):
        pct = count / len(violations) * 100
        bar = "=" * int(pct / 5) + "-" * (20 - int(pct / 5))
        table.add_row(dir_name, str(count), f"[{bar}]")

    console.print(table)

    # By rule
    console.print("")
    rule_table = Table(title="Violations by Rule")
    rule_table.add_column("Rule", style="yellow")
    rule_table.add_column("Count", justify="right")

    for rule, count in sorted(by_rule.items(), key=lambda x: -x[1]):
        rule_table.add_row(rule, str(count))

    console.print(rule_table)

    console.print(
        f"\n  {LOOMY_ALERT} [red]{errors} errors[/red], "
        f"[yellow]{warnings} warnings[/yellow], "
        f"{len(violations)} total"
    )


def _show_full(violations: list, errors: int, warnings: int) -> None:
    """Show full violation table."""
    table = Table(title="Audit Results")
    table.add_column("Severity", width=8)
    table.add_column("File", style="cyan")
    table.add_column("Line", width=5)
    table.add_column("Rule", style="yellow")
    table.add_column("Message")
    table.add_column("Suggestion", style="dim")

    for v in sorted(violations, key=lambda x: (x.severity != "error", x.file)):
        severity_style = {
            "error": "[red]ERROR[/red]",
            "warning": "[yellow]WARN[/yellow]",
            "info": "[blue]INFO[/blue]",
        }.get(v.severity, v.severity)

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
        f"{len(violations)} total"
    )
