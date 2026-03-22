"""loom ask: generate a task prompt with injected context for Claude or any agent."""

from __future__ import annotations

from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("task")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--stdout", is_flag=True, help="Print to stdout (for piping)")
@click.option("-o", "--output", "out_file", default="", help="Save to file")
@click.option(
    "--mode",
    type=click.Choice(["implement", "review", "fix", "refactor", "ask"]),
    default="ask",
    help="Prompt mode",
)
def ask(task: str, path: str, stdout: bool, out_file: str, mode: str) -> None:
    """Generate a task prompt with project context injected.

    \b
    Examples:
      loom ask "implement payment flow" .
      loom ask "fix auth bug" . --mode fix --stdout | pbcopy
      loom ask "review PR #42" . --mode review -o prompt.md

    The output complements CLAUDE.md — it adds task-specific context
    that the static file doesn't have.
    """
    from loom_context.engine import LoomEngine
    from loom_context.knowledge import get_registry

    root = Path(path).resolve()
    engine = LoomEngine(root)
    scan = engine.scan()
    registry = get_registry()

    # Build context (complementary to CLAUDE.md)
    prompt = _build_prompt(task, mode, scan, registry)

    if stdout:
        click.echo(prompt)
        return

    if out_file:
        Path(out_file).write_text(prompt, encoding="utf-8")
        console.print(f"  Saved to [cyan]{out_file}[/cyan]")
        return

    # Default: show with stats
    from loom_context.brand import LOOMY_HAPPY

    chars = len(prompt)
    tokens = chars // 4
    console.print(f"\n  {LOOMY_HAPPY} Prompt for: [bold]{task}[/bold]")
    console.print(f"  {chars} chars, ~{tokens} tokens, mode: {mode}\n")
    console.print(prompt)
    console.print(
        "\n  [dim]Use --stdout to pipe, -o file.md to save[/dim]\n"
    )


def _build_prompt(task: str, mode: str, scan: object, registry: object) -> str:
    """Build the task prompt with injected context."""
    s = scan  # type: ignore[assignment]
    r = registry  # type: ignore[assignment]

    lines: list[str] = []

    # Context block (what CLAUDE.md doesn't have: live state)
    lines.append("# Task Context\n")
    lines.append(f"Project: {s.structure.project_name}")
    if s.structure.language:
        lines.append(f"Language: {s.structure.language}")
    if s.structure.architecture != ["flat"]:
        lines.append(f"Architecture: {', '.join(s.structure.architecture)}")
    lines.append(f"Ecosystem: {s.deps.ecosystem} ({s.deps.package_manager})")

    if s.structure.is_monorepo:
        lines.append(f"Monorepo: {len(s.structure.workspaces)} workspaces")
        for ws in s.structure.workspaces[:5]:
            lines.append(f"  - {ws}")

    # Stack
    if s.deps.stack_summary:
        lines.append("\nStack:")
        for cat, pkgs in sorted(s.deps.stack_summary.items()):
            pkg_list = ", ".join(p.split("@")[0] for p in pkgs[:4])
            lines.append(f"  {cat}: {pkg_list}")

    lines.append("")

    # Architecture rules (what matters for this task)
    arch_rules: list[str] = []
    for arch in s.structure.architecture:
        tmpl = r.get_prompt_rules_for_architecture(arch)
        arch_rules.extend(tmpl.get("rules", []))

    if arch_rules:
        lines.append("# Rules\n")
        for rule in arch_rules:
            lines.append(f"- {rule}")
        lines.append("")

    # Monorepo rules
    if s.structure.is_monorepo:
        mono = r.get_prompt_monorepo_rules()
        for rule in mono.get("rules", []):
            lines.append(f"- {rule}")
        lines.append("")

    # Task
    lines.append("# Task\n")

    if mode == "implement":
        lines.append(f"Implement: {task}\n")
        lines.append("1. List files to create or modify")
        lines.append("2. Verify it fits the architecture above")
        lines.append("3. Flag any rule that would be violated")
        lines.append("4. Write the implementation with tests")
    elif mode == "review":
        lines.append(f"Review: {task}\n")
        lines.append("Check for:")
        lines.append("- Layer boundary violations")
        lines.append("- Naming convention breaks")
        lines.append("- Hardcoded secrets or debug output")
        lines.append("- Missing tests")
        lines.append("- Cross-workspace impact")
    elif mode == "fix":
        lines.append(f"Fix: {task}\n")
        lines.append("1. Identify the most likely files involved")
        lines.append("2. Trace the data flow to the bug")
        lines.append("3. Fix respecting architecture rules")
        lines.append("4. Add a test that proves the bug is fixed")
    elif mode == "refactor":
        lines.append(f"Refactor: {task}\n")
        lines.append("1. Analyze current state and smells")
        lines.append("2. Propose plan before writing code")
        lines.append("3. No behavior changes — tests pass before and after")
        lines.append("4. Preserve public APIs")
    else:
        lines.append(f"{task}")

    return "\n".join(lines)
