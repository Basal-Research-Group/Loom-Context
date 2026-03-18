"""Loomy: brand identity for Loom-Context CLI."""

from __future__ import annotations

from rich.text import Text


def loomy_art() -> Text:
    """Generate Loomy ASCII art as Rich Text (no markup escaping issues)."""
    art = Text()
    art.append("        .  *  .  *  .\n", style="dim")
    art.append("         \\  |  /\n", style="magenta")
    art.append("      ── ", style="magenta")
    art.append("(O O)", style="bold bright_magenta")
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


# --- Loomy expressions ---
# Each expression conveys a distinct emotional state.
# Format: ~( eyes )~ with dendrites on each side.

# Neutral — default, status dashboard, idle
LOOMY = "[magenta]~[bold bright_magenta](O O)[/bold bright_magenta]~[/magenta]"

# Happy — clean audit, successful operation
LOOMY_HAPPY = "[magenta]~[bold bright_magenta](^ ^)[/bold bright_magenta]~[/magenta]"

# Alert — violations found, issues detected
LOOMY_ALERT = "[magenta]~[bold yellow](! !)[/bold yellow]~[/magenta]"

# Thinking — scanning, processing
LOOMY_THINKING = "[magenta]~[bold bright_magenta](. .)[/bold bright_magenta]~[/magenta]"

# Fail — command error, critical failure
LOOMY_FAIL = "[magenta]~[bold red](x x)[/bold red]~[/magenta]"

# Curious — first init, empty project, discovery
LOOMY_CURIOUS = "[magenta]~[bold bright_magenta](? ?)[/bold bright_magenta]~[/magenta]"

# Sleeping — stale context, needs rescan
LOOMY_SLEEPING = "[magenta]~[bold dim](- -)[/bold dim]~[/magenta]"

# Wink — easter egg, fun moments
LOOMY_WINK = "[magenta]~[bold bright_magenta](^ o)[/bold bright_magenta]~[/magenta]"
