"""loom infra: infrastructure dependency manager."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click
from rich.table import Table

from loom_context.cli import console

if TYPE_CHECKING:
    from loom_context.scanners.infra import ServiceDef


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--start", "do_start", is_flag=True, help="Start stopped services")
@click.option("--check", "do_check", is_flag=True, help="Only check status")
@click.option("--docker", "prefer_docker", is_flag=True, help="Prefer Docker commands")
def infra(path: str, do_start: bool, do_check: bool, prefer_docker: bool) -> None:
    """Check your project's infrastructure services (Redis, PostgreSQL, etc.).

    Reads your project's dependencies (package.json, pyproject.toml, etc.)
    and checks if required services are installed and running locally.
    These are YOUR project's requirements, not Loom's.
    """
    from loom_context.brand import LOOMY_ALERT, LOOMY_HAPPY, LOOMY_THINKING
    from loom_context.engine import LoomEngine
    from loom_context.scanners.infra import scan_infrastructure

    root = Path(path).resolve()
    context_dir = root / ".context"

    if not context_dir.exists():
        console.print(f"  {LOOMY_THINKING} No .context/ found, scanning first...")
        engine = LoomEngine(root)
        engine.init()

    engine = LoomEngine(root)
    scan_result = engine.scan()
    dep_names = [dep.name for dep in scan_result.deps.dependencies]

    report = scan_infrastructure(dep_names, check_ports=True)

    if not report.services:
        console.print(f"  {LOOMY_HAPPY} No external services required by this project.")
        console.print("  Your dependencies are all libraries — no Redis, DB, etc. needed.")
        return

    # Status table
    pkg = scan_result.deps.package_manager
    table = Table(
        title=f"Project Infrastructure (from {pkg} dependencies)",
        show_lines=False,
    )
    table.add_column("Service", style="cyan")
    table.add_column("Category")
    table.add_column("Port", justify="right")
    table.add_column("Installed")
    table.add_column("Running")
    table.add_column("Config Env")

    all_running = True
    stopped: list = []

    for status in report.services:
        svc = status.service

        if status.installed is True:
            inst_str = "[green]yes[/green]"
        elif status.installed is False:
            inst_str = "[red]no[/red]"
        else:
            inst_str = "[dim]?[/dim]"

        if status.running is True:
            run_str = "[green]running[/green]"
        elif status.running is False:
            run_str = "[red]stopped[/red]"
            all_running = False
            stopped.append(status)
        else:
            run_str = "[dim]N/A[/dim]"

        table.add_row(
            svc.name,
            svc.category,
            str(svc.default_port) if svc.default_port > 0 else "-",
            inst_str,
            run_str,
            svc.config_env or "-",
        )

    console.print()
    console.print(table)
    console.print()

    if all_running:
        console.print(f"  {LOOMY_HAPPY} All services running.\n")
        return

    if do_check:
        for st in stopped:
            console.print(
                f"  {LOOMY_ALERT} {st.service.name} — port {st.service.default_port} not responding"
            )
        console.print()
        return

    # Show fix commands or auto-start
    for st in stopped:
        svc = st.service
        console.print(f"  {LOOMY_ALERT} [bold]{svc.name}[/bold] is not running")

        if do_start:
            _try_start(svc, st.installed, prefer_docker)
        else:
            if st.installed and svc.start_cmd:
                console.print(f"    Start:   [cyan]{svc.start_cmd}[/cyan]")
            elif svc.install_cmd:
                console.print(f"    Install: [cyan]{svc.install_cmd}[/cyan]")
            if svc.docker_cmd:
                console.print(f"    Docker:  [cyan]{svc.docker_cmd}[/cyan]")
            if svc.config_env:
                console.print(f"    Config:  [dim]{svc.config_env}={svc.config_hint}[/dim]")
            console.print()

    if not do_start:
        console.print(
            "  [dim]Run [cyan]loom infra --start[/cyan] to auto-start stopped services[/dim]"
        )
        console.print(
            "  [dim]Run [cyan]loom infra --start --docker[/cyan] for Docker containers[/dim]\n"
        )


def _try_start(
    svc: ServiceDef,
    installed: Optional[bool],
    prefer_docker: bool,
) -> None:
    """Attempt to start a service."""
    from loom_context.brand import LOOMY_FAIL, LOOMY_HAPPY, LOOMY_THINKING
    from loom_context.scanners.infra import _check_port

    if prefer_docker and svc.docker_cmd:
        cmd = svc.docker_cmd
        console.print(f"    {LOOMY_THINKING} Running: [cyan]{cmd}[/cyan]")
        ok = _run_cmd(cmd)
        if ok and _check_port(svc.default_port, timeout=3.0):
            console.print(f"    {LOOMY_HAPPY} [green]{svc.name} started (Docker)[/green]")
        elif ok:
            console.print(f"    {LOOMY_THINKING} Container created, port pending...")
        else:
            console.print(f"    {LOOMY_FAIL} Docker command failed")
        return

    if installed and svc.start_cmd:
        cmd = svc.start_cmd
        console.print(f"    {LOOMY_THINKING} Running: [cyan]{cmd}[/cyan]")
        ok = _run_cmd(cmd)
        if ok:
            import time

            time.sleep(1)
            if _check_port(svc.default_port, timeout=2.0):
                console.print(f"    {LOOMY_HAPPY} [green]{svc.name} started[/green]")
            else:
                console.print(f"    {LOOMY_FAIL} Port {svc.default_port} not responding")
        else:
            console.print(f"    {LOOMY_FAIL} Start command failed")
        return

    if svc.install_cmd:
        console.print(f"    Not installed. Run: [cyan]{svc.install_cmd}[/cyan]")
    elif svc.docker_cmd:
        console.print(f"    Docker: [cyan]{svc.docker_cmd}[/cyan]")
    else:
        console.print("    No install command available")


def _run_cmd(cmd: str) -> bool:
    """Run a shell command, return True if exit code 0."""
    try:
        result = subprocess.run(  # noqa: S602
            cmd,
            shell=True,
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False
