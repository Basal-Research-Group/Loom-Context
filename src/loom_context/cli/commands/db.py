"""loom db: database schema and migration inspection."""

from __future__ import annotations

import json as json_mod
from pathlib import Path

import click
from rich.table import Table

from loom_context.cli import console


@click.group()
def db() -> None:
    """Database schema and migration inspection."""
    pass


@db.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def schema(path: str, as_json: bool) -> None:
    """Parse and display Prisma schema summary."""
    from loom_context.brand import LOOMY_CURIOUS, LOOMY_HAPPY
    from loom_context.scanners.database import DatabaseScanner

    root = Path(path).resolve()
    scanner = DatabaseScanner(root)
    result = scanner.scan()

    if not result.models:
        console.print(f"  {LOOMY_CURIOUS} No Prisma schema found.")
        return

    if as_json:
        click.echo(json_mod.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    # Summary
    console.print(f"\n  {LOOMY_HAPPY} Schema: [bold]{result.provider}[/bold]")
    console.print(
        f"  Models: [cyan]{result.model_count}[/cyan] | "
        f"Enums: [cyan]{result.enum_count}[/cyan] | "
        f"Relations: [cyan]{result.relation_count}[/cyan]"
    )

    if result.extensions:
        console.print(f"  Extensions: {', '.join(result.extensions)}")

    # Models table
    table = Table(title=f"\nModels ({result.model_count})")
    table.add_column("Model", style="cyan")
    table.add_column("Table", style="dim")
    table.add_column("Fields", justify="right")
    table.add_column("Relations", justify="right")
    table.add_column("Tenant", justify="center")
    table.add_column("Timestamps", justify="center")

    for m in result.models:
        table.add_row(
            m.name,
            m.table_name,
            str(len(m.fields)),
            str(len(m.relations)),
            "✓" if m.has_tenant_id else "—",
            "✓" if m.has_created_at and m.has_updated_at else "—",
        )

    console.print(table)

    # Enums
    if result.enums:
        console.print(f"\n  [bold]Enums ({result.enum_count})[/bold]")
        for e in result.enums:
            values_str = ", ".join(e.values[:5])
            if len(e.values) > 5:
                values_str += f" ... (+{len(e.values) - 5})"
            console.print(f"    [cyan]{e.name}[/cyan]: {values_str}")

    console.print()


@db.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def migrations(path: str, as_json: bool) -> None:
    """Show migration history."""
    from loom_context.brand import LOOMY_CURIOUS, LOOMY_HAPPY
    from loom_context.scanners.migrations import MigrationScanner

    root = Path(path).resolve()
    scanner = MigrationScanner(root)
    result = scanner.scan()

    if not result.migrations:
        console.print(f"  {LOOMY_CURIOUS} No migrations found.")
        return

    if as_json:
        click.echo(json_mod.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    console.print(
        f"\n  {LOOMY_HAPPY} Migrations: [bold]{len(result.migrations)}[/bold] | "
        f"Total SQL: [cyan]{result.total_sql_lines}[/cyan] lines"
    )

    table = Table(title=f"\nMigrations ({len(result.migrations)})")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("SQL", justify="right")
    table.add_column("Tables", justify="right")
    table.add_column("Functions", justify="right")
    table.add_column("Triggers", justify="right")
    table.add_column("Policies", justify="right")

    for i, m in enumerate(result.migrations, 1):
        table.add_row(
            str(i),
            m.name,
            str(m.sql_lines),
            str(len(m.tables_created)) if m.tables_created else "—",
            str(len(m.functions_created)) if m.functions_created else "—",
            str(len(m.triggers_created)) if m.triggers_created else "—",
            str(len(m.policies_created)) if m.policies_created else "—",
        )

    console.print(table)

    # Totals
    console.print(
        f"\n  Totals: "
        f"Tables [cyan]{result.total_tables}[/cyan] | "
        f"Functions [cyan]{result.total_functions}[/cyan] | "
        f"Triggers [cyan]{result.total_triggers}[/cyan] | "
        f"Policies [cyan]{result.total_policies}[/cyan] | "
        f"Indices [cyan]{result.total_indices}[/cyan]\n"
    )


@db.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def domains(path: str) -> None:
    """Show tables grouped by domain (from loom.json)."""
    from loom_context.brand import LOOMY_CURIOUS, LOOMY_HAPPY

    root = Path(path).resolve()
    loom_json_path = root / ".context" / "loom.json"

    if not loom_json_path.exists():
        console.print(f"  {LOOMY_CURIOUS} No .context/loom.json found.")
        return

    try:
        data = json_mod.loads(loom_json_path.read_text(encoding="utf-8"))
    except (json_mod.JSONDecodeError, OSError):
        console.print(f"  {LOOMY_CURIOUS} Could not read loom.json.")
        return

    db_domains = data.get("database", {}).get("domains", {})
    if not db_domains:
        console.print(f"  {LOOMY_CURIOUS} No database.domains configured in loom.json.")
        return

    total_tables = sum(len(d.get("tables", [])) for d in db_domains.values())
    console.print(
        f"\n  {LOOMY_HAPPY} Database domains: [bold]{len(db_domains)}[/bold] | "
        f"Total tables: [cyan]{total_tables}[/cyan]"
    )

    table = Table(title=f"\nDomains ({len(db_domains)})")
    table.add_column("Domain", style="cyan")
    table.add_column("Tables", justify="right")
    table.add_column("Description")

    for name, domain in db_domains.items():
        tables = domain.get("tables", [])
        desc = domain.get("description", "")
        table.add_row(name, str(len(tables)), desc)

    console.print(table)
    console.print()
