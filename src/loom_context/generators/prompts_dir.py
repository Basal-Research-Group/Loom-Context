"""Prompts directory generator: creates .prompts/ with context-aware AI prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry

_registry = get_registry()


def generate_prompts_dir(root: Path, scan_result: dict[str, Any]) -> list[str]:
    """Generate .prompts/ directory with context-aware prompts."""
    prompts_dir = root / ".prompts"
    prompts_dir.mkdir(exist_ok=True)
    generated: list[str] = []

    structure = scan_result.get("structure", {})
    deps = scan_result.get("deps", {})

    project_name = structure.get("project_name", root.name)
    project_type = structure.get("project_type", "unknown")
    language = structure.get("language", "")
    architectures = structure.get("architecture", [])
    ecosystem = deps.get("ecosystem", "")
    pkg_mgr = deps.get("package_manager", "")
    is_monorepo = structure.get("is_monorepo", False)
    workspaces = structure.get("workspaces", [])

    # 01 — Onboarding
    _write(prompts_dir / "01-onboarding.md", _gen_onboarding(
        project_name, project_type, language, architectures,
        ecosystem, pkg_mgr, is_monorepo, workspaces, deps,
    ))
    generated.append("01-onboarding.md")

    # 02 — Before coding
    _write(prompts_dir / "02-before-coding.md", _gen_rules(
        architectures, ecosystem, pkg_mgr, is_monorepo,
    ))
    generated.append("02-before-coding.md")

    # 03 — Workspace guide (monorepo only)
    if is_monorepo and workspaces:
        _write(prompts_dir / "03-workspace-guide.md", _gen_workspace_guide(
            workspaces, pkg_mgr,
        ))
        generated.append("03-workspace-guide.md")

    return generated


def _write(path: Path, content: str) -> None:
    """Write content to file."""
    path.write_text(content, encoding="utf-8")


def _gen_onboarding(
    name: str, ptype: str, language: str, archs: list[str],
    ecosystem: str, pkg_mgr: str, is_mono: bool,
    workspaces: list[str], deps: dict[str, Any],
) -> str:
    """Generate project onboarding prompt."""
    lines = [f"# Project: {name}\n"]

    if language:
        lines.append(f"**Language:** {language}")
    lines.append(f"**Type:** {ptype}")
    if archs and archs != ["flat"]:
        lines.append(f"**Architecture:** {', '.join(archs)}")
    if ecosystem != "unknown":
        lines.append(f"**Ecosystem:** {ecosystem} ({pkg_mgr})")
    lines.append("")

    if is_mono:
        lines.append(f"## Monorepo ({len(workspaces)} workspaces)\n")
        for ws in workspaces:
            lines.append(f"- `{ws}`")
        lines.append("")

    # Stack summary
    summary = deps.get("stack_summary", {})
    if summary:
        lines.append("## Technology Stack\n")
        for cat, pkgs in sorted(summary.items()):
            pkg_list = ", ".join(p.split("@")[0] for p in pkgs[:5])
            if len(pkgs) > 5:
                pkg_list += f", +{len(pkgs) - 5} more"
            lines.append(f"- **{cat}:** {pkg_list}")
        lines.append("")

    return "\n".join(lines)


def _gen_rules(
    archs: list[str], ecosystem: str, pkg_mgr: str, is_mono: bool,
) -> str:
    """Generate coding rules prompt from architecture and ecosystem."""
    lines = ["# Rules Before Coding\n"]

    # Architecture rules
    for arch in archs:
        tmpl = _registry.get_prompt_rules_for_architecture(arch)
        rules = tmpl.get("rules", [])
        warnings = tmpl.get("warnings", [])
        if rules:
            lines.append(f"## {arch}\n")
            for r in rules:
                lines.append(f"- {r}")
            for w in warnings:
                lines.append(f"- _{w}_")
            lines.append("")

    # Ecosystem hints
    if ecosystem:
        hints = _registry.get_prompt_hints_for_ecosystem(ecosystem)
        if hints:
            lines.append("## Ecosystem\n")
            for h in hints:
                h = h.replace("{package_manager}", pkg_mgr)
                lines.append(f"- {h}")
            lines.append("")

    # Monorepo rules
    if is_mono:
        mono = _registry.get_prompt_monorepo_rules()
        if mono.get("rules"):
            lines.append("## Monorepo\n")
            for r in mono["rules"]:
                lines.append(f"- {r}")
            lines.append("")

    return "\n".join(lines)


def _gen_workspace_guide(workspaces: list[str], pkg_mgr: str) -> str:
    """Generate workspace navigation guide."""
    lines = ["# Workspace Guide\n"]

    lines.append("## Workspaces\n")
    for ws in workspaces:
        lines.append(f"- `{ws}`")
    lines.append("")

    lines.append("## Commands\n")
    lines.append("```bash")
    if pkg_mgr == "pnpm":
        lines.append("pnpm --filter <workspace> dev    # run one")
        lines.append("pnpm --filter <workspace> test   # test one")
        lines.append("pnpm -r test                     # test all")
        lines.append("pnpm -r build                    # build all")
    elif pkg_mgr in ("yarn", "npm"):
        lines.append(f"{pkg_mgr} workspace <name> dev")
        lines.append(f"{pkg_mgr} workspace <name> test")
    lines.append("```\n")

    lines.append("## Change Order (bottom-up)\n")
    lines.append("1. Shared packages first (types, contracts)")
    lines.append("2. Core/library packages")
    lines.append("3. UI components")
    lines.append("4. Apps last (consumers)")
    lines.append("")

    return "\n".join(lines)
