"""Loom CLI: command-line interface for Loom-Context."""

from __future__ import annotations

import logging
import time

import click
from rich.console import Console

from loom_context import __version__

console = Console()

# Global state for usage tracking
_cli_start_time: float = 0.0


def _record_usage() -> None:
    """Record command usage after execution completes."""
    global _cli_start_time
    if _cli_start_time == 0.0:
        return

    duration_ms = int((time.monotonic() - _cli_start_time) * 1000)
    _cli_start_time = 0.0

    # Get the invoked subcommand name
    ctx = click.get_current_context(silent=True)
    if ctx is None or ctx.invoked_subcommand is None:
        # Try to get from info_name of the child context
        if ctx and ctx.info_name:
            cmd_name = ctx.info_name
        else:
            return
    else:
        cmd_name = ctx.invoked_subcommand

    # Find project root (.loom/ directory)
    from pathlib import Path

    root = Path.cwd()
    loom_dir = root / ".loom"
    if not loom_dir.exists():
        return

    try:
        from loom_context.store.reporter import UsageReporter

        reporter = UsageReporter(loom_dir, root)
        reporter.record(cmd_name, duration_ms, success=True)
    except Exception:  # noqa: S110 — intentional: never fail CLI for tracking
        pass


@click.group()
@click.version_option(version=__version__, prog_name="loom")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Loom - Architecture Context Engine for AI-First Engineering."""
    global _cli_start_time
    _cli_start_time = time.monotonic()

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(name)s %(levelname)s: %(message)s",
            stream=__import__("sys").stderr,
        )

    ctx.call_on_close(_record_usage)


# Register all commands
from loom_context.cli.commands import (  # noqa: E402
    audit,
    bundle,
    decide,
    doctor,
    enrich,
    export,
    focus,
    handoff,
    infra,
    init,
    log,
    metrics,
    plan,
    prompt,
    report,
    scan,
    setup,
    status,
    watch,
)

main.add_command(init.init)  # type: ignore[has-type]
main.add_command(scan.scan)  # type: ignore[has-type]
main.add_command(prompt.prompt)  # type: ignore[has-type]
main.add_command(audit.audit)  # type: ignore[has-type]
main.add_command(plan.plan)  # type: ignore[has-type]
main.add_command(watch.watch)  # type: ignore[has-type]
main.add_command(focus.focus)  # type: ignore[has-type]
main.add_command(log.log_cmd, name="log")  # type: ignore[has-type]
main.add_command(status.status)  # type: ignore[has-type]
main.add_command(enrich.enrich)  # type: ignore[has-type]
main.add_command(decide.decide)  # type: ignore[has-type]
main.add_command(bundle.bundle)  # type: ignore[has-type]
main.add_command(handoff.handoff)  # type: ignore[has-type]
main.add_command(doctor.doctor)  # type: ignore[has-type]
main.add_command(export.export_cmd, name="export")  # type: ignore[has-type]
main.add_command(metrics.metrics)  # type: ignore[has-type]
main.add_command(report.report)  # type: ignore[has-type]
main.add_command(setup.setup)  # type: ignore[has-type]
main.add_command(infra.infra)  # type: ignore[has-type]
