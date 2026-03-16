"""Loomy: brand identity for Loom-Context CLI."""

from __future__ import annotations

from rich.text import Text


def loomy_art() -> Text:
    """Generate Loomy ASCII art as Rich Text (no markup escaping issues)."""
    art = Text()
    art.append("        .  *  .  *  .\n", style="dim")
    art.append("         \\  |  /\n", style="magenta")
    art.append("      ── ", style="magenta")
    art.append("(O)", style="bold bright_magenta")
    art.append(" ──\n", style="magenta")
    art.append("         /  |  \\\n", style="magenta")
    art.append("        *  .  *  .  *", style="dim")
    return art


def loomy_banner(version: str) -> Text:
    """Generate the full Loomy banner for init command."""
    banner = loomy_art()
    banner.append("\n\n")
    banner.append("  Loom Context Engine", style="bold blue")
    banner.append(f" v{version}\n")
    banner.append("  weaving context, one thread at a time", style="dim")
    return banner


LOOMY_SMALL = "[magenta]~[bold bright_magenta](O)[/bold bright_magenta]~[/magenta]"

LOOMY_HAPPY = "[magenta]~[bold bright_magenta](^)[/bold bright_magenta]~[/magenta]"

LOOMY_ALERT = "[magenta]~[bold yellow](!)[/bold yellow]~[/magenta]"
