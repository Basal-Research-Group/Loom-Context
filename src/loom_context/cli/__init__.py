"""Loom CLI: command-line interface for Loom-Context."""

from __future__ import annotations

import logging

import click
from rich.console import Console

from loom_context import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="loom")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(verbose: bool) -> None:
    """Loom - Architecture Context Engine for AI-First Engineering."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(name)s %(levelname)s: %(message)s",
            stream=__import__("sys").stderr,
        )


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
    init,
    log,
    metrics,
    plan,
    prompt,
    report,
    scan,
    status,
    watch,
)

main.add_command(init.init)
main.add_command(scan.scan)
main.add_command(prompt.prompt)
main.add_command(audit.audit)
main.add_command(plan.plan)
main.add_command(watch.watch)
main.add_command(focus.focus)
main.add_command(log.log_cmd, name="log")
main.add_command(status.status)
main.add_command(enrich.enrich)
main.add_command(decide.decide)
main.add_command(bundle.bundle)
main.add_command(handoff.handoff)
main.add_command(doctor.doctor)
main.add_command(export.export_cmd, name="export")
main.add_command(metrics.metrics)
main.add_command(report.report)
