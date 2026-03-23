"""loom status: project health dashboard."""

from __future__ import annotations

from pathlib import Path

import click
from rich.panel import Panel

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(path: str, as_json: bool) -> None:
    """Project health dashboard."""
    import json as json_mod

    from loom_context.status import StatusCollector

    root = Path(path).resolve()
    collector = StatusCollector(root)
    st = collector.collect()

    if as_json:
        click.echo(json_mod.dumps(st.to_dict(), indent=2, ensure_ascii=False, default=str))
        return

    from loom_context.brand import LOOMY, LOOMY_FAIL, LOOMY_SLEEPING

    if not st.context_exists:
        console.print(f"  {LOOMY_FAIL} [red]Not initialized.[/red] Run 'loom init .' first.")
        return

    arch = ", ".join(st.architecture) if st.architecture else "unknown"
    domain_display = st.domain if st.domain != "unknown" else ""
    header = f"  {LOOMY_SLEEPING if st.is_stale else LOOMY}  "
    header += f"[bold]{st.project_name}[/bold]  {st.project_type} · {arch}"
    if domain_display:
        header += f" · [cyan]{domain_display}[/cyan]"
    console.print(Panel(header, title="Loom Status"))

    if st.last_scan:
        scan_display = st.last_scan[:19].replace("T", " ")
        if st.is_stale:
            console.print(
                f"  [yellow]Stale[/yellow]  Last scan: {scan_display}  "
                f"({st.stale_file_count} files changed). Run 'loom scan'."
            )
        else:
            console.print(f"  [green]Fresh[/green]  Last scan: {scan_display}")
    else:
        console.print("  [yellow]No scan timestamp found.[/yellow]")

    if st.audit_errors > 0 or st.audit_warnings > 0:
        console.print(
            f"  Audit   [red]{st.audit_errors} errors[/red], "
            f"[yellow]{st.audit_warnings} warnings[/yellow]"
        )
    else:
        console.print("  Audit   [green]clean[/green]")

    if st.quick_rules:
        console.print(f"\n  Rules ({len(st.quick_rules)}):")
        for rule in st.quick_rules[:5]:
            console.print(f"    [yellow]>[/yellow] {rule}")
        if len(st.quick_rules) > 5:
            console.print(f"    ... +{len(st.quick_rules) - 5} more")

    if st.last_findings:
        fe = st.last_findings.get("errors", 0)
        fw = st.last_findings.get("warnings", 0)
        if fe or fw:
            console.print(f"  Findings  [red]{fe} errors[/red], [yellow]{fw} warnings[/yellow]")
        else:
            console.print("  Findings  [green]clean[/green]")

    if st.decisions_count > 0:
        console.print(f"  Decisions  {st.decisions_count} recorded")

    if st.recent_logs:
        console.print(f"\n  Session Log ({len(st.recent_logs)} recent):")
        for entry in st.recent_logs[:3]:
            ts = entry.timestamp[:16].replace("T", " ")
            console.print(f'    [dim]{ts}[/dim] "{entry.message}"')
    console.print("")
