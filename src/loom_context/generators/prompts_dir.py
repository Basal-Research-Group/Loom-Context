"""Prompts directory generator: creates .prompts/ with ready-to-use AI prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loom_context.knowledge import get_registry

_registry = get_registry()


def generate_prompts_dir(root: Path, scan_result: dict[str, Any]) -> list[str]:
    """Generate .prompts/ with copy-paste-ready prompts."""
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
    summary = deps.get("stack_summary", {})
    domain = scan_result.get("domain", "unknown")
    domain_details = scan_result.get("domain_details", {})

    # Build context block (reused across prompts)
    ctx = _build_context(
        project_name, language, project_type, architectures,
        ecosystem, pkg_mgr, is_monorepo, workspaces, summary,
        domain, domain_details,
    )

    # Build rules block
    rules = _build_rules(architectures, ecosystem, pkg_mgr, is_monorepo, domain)

    # Generate prompts
    _write(prompts_dir / "onboarding.md", _prompt_onboarding(ctx, rules))
    generated.append("onboarding.md")

    _write(prompts_dir / "implement-feature.md", _prompt_implement(ctx, rules))
    generated.append("implement-feature.md")

    _write(prompts_dir / "review-code.md", _prompt_review(ctx, rules))
    generated.append("review-code.md")

    _write(prompts_dir / "fix-bug.md", _prompt_fix_bug(ctx, rules))
    generated.append("fix-bug.md")

    _write(prompts_dir / "refactor.md", _prompt_refactor(ctx, rules))
    generated.append("refactor.md")

    return generated


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _build_context(
    name: str, language: str, ptype: str, archs: list[str],
    ecosystem: str, pkg_mgr: str, is_mono: bool,
    workspaces: list[str], summary: dict[str, Any],
    domain: str = "unknown", domain_details: dict[str, Any] | None = None,
) -> str:
    """Build the project context block for injection into prompts."""
    lines = []
    lines.append(f"Project: {name}")
    if language:
        lines.append(f"Language: {language}")
    lines.append(f"Type: {ptype}")
    if domain != "unknown":
        active = (domain_details or {}).get("active", [domain])
        lines.append(f"Domain: {domain} ({', '.join(active)})")
    if archs and archs != ["flat"]:
        lines.append(f"Architecture: {', '.join(archs)}")
    if ecosystem != "unknown":
        lines.append(f"Ecosystem: {ecosystem} ({pkg_mgr})")
    if is_mono:
        lines.append(f"Monorepo: {len(workspaces)} workspaces")
        for ws in workspaces:
            lines.append(f"  - {ws}")
    if summary:
        lines.append("Stack:")
        for cat, pkgs in sorted(summary.items()):
            pkg_list = ", ".join(p.split("@")[0] for p in pkgs[:5])
            lines.append(f"  {cat}: {pkg_list}")
    return "\n".join(lines)


def _build_rules(
    archs: list[str], ecosystem: str, pkg_mgr: str, is_mono: bool,
    domain: str = "unknown",
) -> str:
    """Build the rules block from architecture + ecosystem + domain."""
    lines: list[str] = []

    for arch in archs:
        tmpl = _registry.get_prompt_rules_for_architecture(arch)
        for r in tmpl.get("rules", []):
            lines.append(f"- {r}")
        for w in tmpl.get("warnings", []):
            lines.append(f"- {w}")

    if ecosystem:
        for h in _registry.get_prompt_hints_for_ecosystem(ecosystem):
            lines.append(f"- {h.replace('{package_manager}', pkg_mgr)}")

    if is_mono:
        mono = _registry.get_prompt_monorepo_rules()
        for r in mono.get("rules", []):
            lines.append(f"- {r}")

    # Domain-specific rules
    if domain != "unknown":
        domain_data = _registry.get_domain(domain)
        if domain_data:
            gov_rules = domain_data.get("governance_rules", {})
            for rule_name, rule_def in gov_rules.items():
                desc = rule_def if isinstance(rule_def, str) else rule_def.get("description", "")
                if desc:
                    lines.append(f"- [{domain}] {desc}")

    # Loom coordination rules (always present)
    lines.append("- This project uses Loom-Context for AI coordination")
    lines.append("- Loom detects, selects, compacts, exports, traces, and audits")
    lines.append("- Do NOT bypass Loom rules — they are the source of truth")
    lines.append("- If you propose changes, respect domain boundaries and layer rules")
    lines.append("- Register decisions with 'loom decide' for traceability")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def _prompt_onboarding(ctx: str, rules: str) -> str:
    return f"""# Onboarding

## When
First time working on this project. Copy the prompt below.

## Prompt

```
I'm starting to work on this project. Here is the context:

{ctx}

Rules:
{rules}

Read the project structure and give me:
1. A summary of how the codebase is organized
2. The main entry points
3. How to run it locally
4. The 3 most important files to understand first
5. Anything that looks unusual or risky

Don't modify anything. Just explain.
```
"""


def _prompt_implement(ctx: str, rules: str) -> str:
    return f"""# Implement Feature

## When
Before writing a new feature. Replace [FEATURE] with your task.

## Prompt

```
Context:
{ctx}

Rules:
{rules}

Task: implement [FEATURE]

Before writing code:
1. List the files you will create or modify
2. Explain how this fits the existing architecture
3. Flag if any rule above would be violated
4. Write the implementation

After writing code:
- Verify imports respect layer boundaries
- Add tests
- Update docs if the feature is user-facing
```
"""


def _prompt_review(ctx: str, rules: str) -> str:
    return f"""# Review Code

## When
Before merging a PR or after finishing a task. Replace [FILES] with the changed files.

## Prompt

```
Context:
{ctx}

Rules:
{rules}

Review these changes: [FILES]

Check:
1. Do imports respect layer boundaries?
2. Are naming conventions followed?
3. Is there any hardcoded secret, magic number, or debug output?
4. Are there tests for the new behavior?
5. Does the change affect other workspaces? If so, are they tested?
6. Any code smell (god class, deep nesting, long params)?

For each issue: file, line, problem, fix.
```
"""


def _prompt_fix_bug(ctx: str, rules: str) -> str:
    return f"""# Fix Bug

## When
Debugging an issue. Replace [BUG] with the description.

## Prompt

```
Context:
{ctx}

Rules:
{rules}

Bug: [BUG]

1. Identify the most likely files involved
2. Trace the data flow from input to where the bug manifests
3. Propose a fix that respects the architecture rules above
4. If the fix touches multiple workspaces, list all affected
5. Write the fix with tests that prove the bug is resolved
```
"""


def _prompt_refactor(ctx: str, rules: str) -> str:
    return f"""# Refactor

## When
Improving code without changing behavior. Replace [AREA] with the target.

## Prompt

```
Context:
{ctx}

Rules:
{rules}

Refactor: [AREA]

1. Analyze the current state — what smells or issues exist?
2. Propose the refactoring plan (before writing code)
3. For each change, explain why it improves the codebase
4. Ensure no behavior changes — tests must pass before and after
5. If splitting a god class, preserve the public API
6. If extracting a module, define its boundary and exports
```
"""
