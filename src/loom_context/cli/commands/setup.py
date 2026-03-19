"""loom setup: interactive wizard for zero-friction project configuration."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.table import Table

from loom_context.cli import console

# Infrastructure categories that warrant advisory warnings
INFRA_CATEGORIES = {"database", "task-queue", "message-queue", "cache"}


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--preset",
    "-p",
    type=click.Choice(["minimal", "full", "claude"]),
    help="Use a preset configuration",
)
@click.option(
    "--agent",
    "-a",
    "agents",
    multiple=True,
    type=click.Choice(["claude", "cursor", "codex", "copilot", "generic"]),
    help="Target agents (repeatable)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompts",
)
@click.option(
    "--no-backup",
    "no_backup",
    is_flag=True,
    help="Don't backup existing agent files",
)
@click.option(
    "--no-install",
    "no_install",
    is_flag=True,
    help="Export to .context/exports/ instead of project root",
)
def setup(
    path: str,
    preset: Optional[str],
    agents: tuple[str, ...],
    force: bool,
    no_backup: bool,
    no_install: bool,
) -> None:
    """Interactive setup wizard: scan, detect, configure, and install in one step."""
    from loom_context import __version__
    from loom_context.brand import (
        LOOMY_ALERT,
        LOOMY_CURIOUS,
        LOOMY_HAPPY,
        LOOMY_THINKING,
        LOOMY_WINK,
        loomy_banner,
    )
    from loom_context.engine import LoomEngine
    from loom_context.exporters import get_exporter
    from loom_context.exporters.detect import (
        AGENT_FILES,
        agent_file_info,
        detect_installed_agents,
    )
    from loom_context.generators.index import generate_quick_rules
    from loom_context.presets import get_preset

    root = Path(path).resolve()

    # --- Banner ---
    banner = loomy_banner(__version__)
    console.print(Panel(banner, subtitle="Zero-Friction Setup"))

    # --- Phase 1: Scan ---
    console.print(f"\n  {LOOMY_THINKING} Scanning [cyan]{root}[/cyan]...\n")

    start = time.time()
    engine = LoomEngine(root)
    result = engine.init()
    elapsed = time.time() - start

    scan = result["scan_result"]

    # Summary table (same as init)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Project Type", scan.structure.project_type)
    table.add_row("Architecture", ", ".join(scan.structure.architecture))
    table.add_row("Files Scanned", str(scan.structure.total_files))
    table.add_row("Code Files", str(scan.code.total_code_files))
    table.add_row("Docs Found", str(scan.docs.doc_count))
    table.add_row("Dependencies", str(len(scan.deps.dependencies)))
    table.add_row("Package Manager", scan.deps.package_manager)
    console.print(table)

    # Generated files
    console.print("\n  Generated [green].context/[/green]")
    for fname in result["generated_files"]:
        console.print(f"    [green]+[/green] {fname}")

    # Quick rules preview
    quick_rules = generate_quick_rules(scan.to_dict())
    if quick_rules:
        console.print(f"\n  Quick Rules ({len(quick_rules)}):")
        for rule in quick_rules[:5]:
            console.print(f"    [yellow]>[/yellow] {rule}")
        if len(quick_rules) > 5:
            console.print(f"    ... and {len(quick_rules) - 5} more")

    # Audit summary
    audit = result.get("audit", {})
    errors = audit.get("errors", 0)
    warnings = audit.get("warnings", 0)
    if errors or warnings:
        console.print(
            f"\n  Audit  [red]{errors} errors[/red], [yellow]{warnings} warnings[/yellow]"
        )
    else:
        console.print("\n  Audit  [green]clean[/green]")

    console.print(f"  Scanned in [bold]{elapsed:.1f}s[/bold]\n")

    # --- Phase 2: Infrastructure health check ---
    from loom_context.scanners.infra import scan_infrastructure

    dep_names = [dep.name for dep in scan.deps.dependencies]
    infra = scan_infrastructure(dep_names, check_ports=True)

    if infra.services:
        console.print(f"  {LOOMY_ALERT} Your project requires these services:")
        for st in infra.services:
            svc = st.service
            if st.running is True:
                run_str = "[green]running[/green]"
            elif st.running is False:
                run_str = f"[red]not running[/red] (port {svc.default_port})"
            else:
                run_str = "[dim]no port[/dim]"
            console.print(f"    {svc.name} ({svc.category}) — {run_str}")

        if infra.warnings:
            for warn in infra.warnings:
                console.print(f"    [yellow]![/yellow] {warn}")
        if infra.suggestions:
            console.print()
            for suggestion in infra.suggestions[:6]:
                console.print(f"    [dim]> {suggestion}[/dim]")

        has_stopped = any(st.running is False for st in infra.services)
        if has_stopped:
            console.print("    [dim]Run [cyan]loom infra --start[/cyan] to start services[/dim]")
        console.print()

    # --- Phase 3: Detect existing agent files ---
    console.print(f"  {LOOMY_CURIOUS} Checking existing agent files...")
    installed = detect_installed_agents(root)

    for agent_name, filename in AGENT_FILES.items():
        if agent_name in installed:
            info = agent_file_info(installed[agent_name])
            size_str = info["size"] if info else "?"
            origin = info["origin"] if info else "unknown"
            console.print(f"    [green]+[/green] {filename} exists ({origin}, {size_str})")
        else:
            console.print(f"    [dim]~[/dim] {filename} not found")
    console.print()

    # --- Phase 4: Resolve which agents to install ---
    if preset:
        preset_config = get_preset(preset)
        if preset_config is None:
            console.print(f"  [red]Unknown preset: {preset}[/red]")
            return
        selected_agents = list(preset_config.agents)
        no_install = no_install or not preset_config.install
    elif agents:
        selected_agents = list(agents)
    elif force:
        # --force without --agent or --preset: install all
        selected_agents = list(AGENT_FILES.keys())
    else:
        # Interactive: ask for each agent
        selected_agents = _interactive_agent_selection(installed)

    if not selected_agents:
        console.print(f"  {LOOMY_WINK} No agents selected. .context/ is ready.\n")
        return

    # --- Phase 5: Export and install ---
    context_dir = root / ".context"
    install_count = 0
    backup_count = 0

    for agent_name in selected_agents:
        exporter_cls = get_exporter(agent_name)
        if exporter_cls is None:
            continue

        exporter = exporter_cls(context_dir, root)

        if no_install:
            saved = exporter.export_to_file()
            chars = len(saved.read_text(encoding="utf-8"))
            console.print(f"  {LOOMY_WINK} Exported [bold]{agent_name}[/bold] ({chars} chars)")
            console.print(f"    [green]+[/green] {saved.relative_to(root)}")
            install_count += 1
        else:
            exists = exporter.existing_install_exists()

            if exists and not force:
                target = exporter.install_path()
                size = target.stat().st_size
                size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                if not click.confirm(f"  Overwrite {target.name} ({size_str})?", default=True):
                    console.print(f"    [dim]skipped {target.name}[/dim]")
                    continue

            target_path, backup_path = exporter.install_with_backup(skip_backup=no_backup)
            content = target_path.read_text(encoding="utf-8")
            chars = len(content)
            tokens = int(len(content.split()) * 1.3)
            console.print(
                f"  {LOOMY_WINK} Installed [bold]{agent_name}[/bold] "
                f"({chars} chars, ~{tokens:,} tokens)"
            )
            console.print(f"    [green]+[/green] {target_path.name}")

            if backup_path:
                console.print(f"    [dim]backup → .loom/backups/{backup_path.name}[/dim]")
                backup_count += 1

            install_count += 1

    # --- Summary ---
    action = "exported" if no_install else "installed"
    backup_msg = f", {backup_count} backups in .loom/backups/" if backup_count else ""
    console.print(f"\n  {LOOMY_HAPPY} Setup complete: {install_count} agents {action}{backup_msg}")
    console.print()


def _interactive_agent_selection(
    installed: dict[str, Path],
) -> list[str]:
    """Ask user which agents to install via click.confirm."""
    from loom_context.exporters.detect import AGENT_FILES

    selected: list[str] = []
    for agent_name, filename in AGENT_FILES.items():
        # Default is Y for all except generic
        default = agent_name != "generic"

        if agent_name in installed:
            prompt = f"  Install for {agent_name}? ({filename} exists, will backup)"
        else:
            prompt = f"  Install for {agent_name}? ({filename})"

        if click.confirm(prompt, default=default):
            selected.append(agent_name)

    return selected
