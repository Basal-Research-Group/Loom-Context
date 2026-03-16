"""Loom CLI: command-line interface for Loom-Context."""

from __future__ import annotations

import click
from rich.console import Console

from loom_context import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="loom")
def main() -> None:
    """Loom - Architecture Context Engine for AI-First Engineering."""


# Register all commands
from loom_context.cli.commands import (  # noqa: E402
    audit,
    bundle,
    decide,
    doctor,
    enrich,
    focus,
    handoff,
    init,
    log,
    plan,
    prompt,
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
