"""loom knowledge: inspect and manage the Knowledge Registry."""

from __future__ import annotations

import click
from rich.table import Table

from loom_context.cli import console

_ACTIONS = click.Choice(["list", "langs", "patterns", "packages"])


@click.command()
@click.argument("action", default="list", type=_ACTIONS)
def knowledge(action: str) -> None:
    """Inspect what Loom knows: languages, patterns, packages.

    \b
    Actions:
      list      Summary of all knowledge (default)
      langs     List all supported languages
      patterns  List architecture + design patterns
      packages  List package ecosystems and counts
    """
    from loom_context.knowledge import get_registry

    registry = get_registry()

    if action == "list":
        _show_summary(registry)
    elif action == "langs":
        _show_languages(registry)
    elif action == "patterns":
        _show_patterns(registry)
    elif action == "packages":
        _show_packages(registry)


def _show_summary(registry: object) -> None:
    """Show knowledge summary."""
    from loom_context.brand import LOOMY_HAPPY

    r = registry  # type: ignore[assignment]
    langs = r._load_json("languages.json")
    eco = r._load_json("ecosystems.json")
    total_pkgs = sum(
        len(e.get("packages", {}))
        for e in eco.get("ecosystems", {}).values()
    )
    arch = r.get_architecture_patterns()
    dp = r.get_design_patterns()
    dirs = r.get_all_directory_annotations()

    console.print(f"\n  {LOOMY_HAPPY} Knowledge Registry\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    table.add_row("Languages", f"{len(langs)}")
    table.add_row("Extensions", f"{len(r.get_all_extensions())}")
    table.add_row("Ecosystems", f"{len(eco.get('ecosystems', {}))}")
    table.add_row("Known packages", f"{total_pkgs}")
    table.add_row("Architecture patterns", f"{len(arch)}")
    table.add_row("Design patterns", f"{len(dp)}")
    table.add_row("Directory annotations", f"{len(dirs)}")
    table.add_row("Dir exclusions", f"{len(r.get_dir_exclusions())}")
    table.add_row("Secret patterns", f"{len(r.get_secret_patterns())}")
    table.add_row("Role suffixes", f"{len(r.get_role_suffixes())}")
    table.add_row("Domains", ", ".join(r.get_available_domains()))
    console.print(table)
    console.print()


def _show_languages(registry: object) -> None:
    """Show all languages."""
    r = registry  # type: ignore[assignment]
    langs = r._load_json("languages.json")

    table = Table(title="Supported Languages")
    table.add_column("Language", style="cyan")
    table.add_column("Extensions")
    table.add_column("Markers")
    table.add_column("Code Patterns")
    table.add_column("Frameworks")

    for lid, ldata in sorted(langs.items()):
        exts = ", ".join(ldata.get("extensions", [])[:4])
        markers = ", ".join(ldata.get("markers", [])[:2])
        has_patterns = "yes" if ldata.get("class_pattern") else "-"
        fw = ", ".join(ldata.get("frameworks", {}).keys()) or "-"
        table.add_row(ldata.get("name", lid), exts, markers, has_patterns, fw)

    console.print()
    console.print(table)
    console.print()


def _show_patterns(registry: object) -> None:
    """Show architecture and design patterns."""
    r = registry  # type: ignore[assignment]

    # Architecture
    arch = r.get_architecture_patterns()
    table = Table(title="Architecture Patterns")
    table.add_column("Pattern", style="cyan")
    table.add_column("Signals", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Boundaries")

    for name, p in sorted(arch.items()):
        boundaries = ", ".join(p.boundary_rules.keys()) if p.boundary_rules else "-"
        table.add_row(
            p.display_name or name,
            str(len(p.signals)),
            f"{p.confidence_threshold:.0%}",
            boundaries,
        )

    console.print()
    console.print(table)

    # Design patterns
    dp = r.get_design_patterns()
    cats = r.get_design_pattern_categories()

    table2 = Table(title="Design Patterns")
    table2.add_column("Category", style="cyan")
    table2.add_column("Count", justify="right")
    table2.add_column("Patterns")

    for cat_id, cat in sorted(cats.items()):
        cat_patterns = [
            dp[p]["name"] for p in sorted(dp) if dp[p]["category"] == cat_id
        ]
        if cat_patterns:
            # Show first 5, then "..."
            shown = ", ".join(cat_patterns[:5])
            if len(cat_patterns) > 5:
                shown += f", +{len(cat_patterns) - 5} more"
            table2.add_row(cat["name"], str(len(cat_patterns)), shown)

    console.print()
    console.print(table2)
    console.print()


def _show_packages(registry: object) -> None:
    """Show package ecosystems."""
    r = registry  # type: ignore[assignment]
    eco = r._load_json("ecosystems.json")

    table = Table(title="Package Ecosystems")
    table.add_column("Ecosystem", style="cyan")
    table.add_column("Packages", justify="right")
    table.add_column("Sample categories")

    for ename, edata in sorted(eco.get("ecosystems", {}).items()):
        pkgs = edata.get("packages", {})
        cats = set()
        for p in pkgs.values():
            cats.add(p.get("category", ""))
        cat_str = ", ".join(sorted(cats)[:6])
        if len(cats) > 6:
            cat_str += f", +{len(cats) - 6}"
        table.add_row(ename, str(len(pkgs)), cat_str)

    total = sum(
        len(e.get("packages", {}))
        for e in eco.get("ecosystems", {}).values()
    )
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")

    console.print()
    console.print(table)
    console.print()
