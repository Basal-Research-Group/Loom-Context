"""loom doctor: verify Loom setup health."""

from __future__ import annotations

import json
from pathlib import Path

import click

from loom_context.cli import console


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def doctor(path: str) -> None:
    """Verify Loom setup health and diagnose issues."""
    from loom_context.brand import LOOMY_ALERT, LOOMY_FAIL, LOOMY_HAPPY

    root = Path(path).resolve()
    context_dir = root / ".context"
    loom_dir = root / ".loom"

    console.print(f"\n  Checking [cyan]{root}[/cyan]...\n")

    checks_passed = 0
    checks_failed = 0
    checks_warned = 0

    def ok(msg: str) -> None:
        nonlocal checks_passed
        checks_passed += 1
        console.print(f"  [green]+[/green] {msg}")

    def fail(msg: str) -> None:
        nonlocal checks_failed
        checks_failed += 1
        console.print(f"  [red]x[/red] {msg}")

    def warn(msg: str) -> None:
        nonlocal checks_warned
        checks_warned += 1
        console.print(f"  [yellow]~[/yellow] {msg}")

    # 1. .context/ exists
    if context_dir.exists():
        ok(".context/ exists")
    else:
        fail(".context/ missing — run 'loom init .'")

    # 2. index.json exists and valid
    index_path = context_dir / "index.json"
    if index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
            if index.get("project", {}).get("type"):
                ok(f"index.json valid (project type: {index['project']['type']})")
            else:
                warn("index.json exists but project type unknown")
        except (json.JSONDecodeError, OSError):
            fail("index.json exists but is corrupted")
    elif context_dir.exists():
        fail("index.json missing — run 'loom scan .'")

    # 3. Core context files
    expected_files = [
        "architecture.md",
        "naming.md",
        "directory-map.md",
        "stack.json",
        "rules.json",
        "plans-summary.md",
    ]
    if context_dir.exists():
        missing = [f for f in expected_files if not (context_dir / f).exists()]
        if not missing:
            ok(f"all {len(expected_files)} context files present")
        else:
            fail(f"missing context files: {', '.join(missing)}")

    # 4. .loom/ exists
    if loom_dir.exists():
        ok(".loom/ exists")
    else:
        warn(".loom/ missing — run 'loom init .' to create")

    # 5. .loom/ files
    if loom_dir.exists():
        loom_files = list(loom_dir.iterdir())
        loom_names = {f.name for f in loom_files}
        if "inconsistencies.json" in loom_names:
            ok("findings persisted (inconsistencies.json)")
        else:
            warn("no findings yet — run 'loom enrich .'")

        if "mutations.jsonl" in loom_names:
            ok("mutation log active")
        else:
            warn("no mutations logged")

        if "sessions.jsonl" in loom_names:
            ok("session log active")
        else:
            warn("no sessions logged — use 'loom log'")

        if "decisions.jsonl" in loom_names:
            ok("decision log active")
        else:
            warn("no decisions recorded — use 'loom decide'")

    # 6. .gitignore includes .loom/ with reports exception
    gitignore = root / ".gitignore"
    if gitignore.exists():
        gi_content = gitignore.read_text(encoding="utf-8")
        has_loom_ignore = ".loom/*" in gi_content or ".loom/" in gi_content or ".loom" in gi_content
        has_reports_exception = "!.loom/reports/" in gi_content or "!.loom/reports" in gi_content
        if has_loom_ignore and has_reports_exception:
            ok(".loom/* ignored, .loom/reports/ tracked")
        elif has_loom_ignore:
            warn(".loom/ ignored but .loom/reports/ not tracked — run 'loom init .' to fix")
        else:
            warn(".loom/ not in .gitignore — run 'loom init .' to configure")
    else:
        warn("no .gitignore found")

    # 7. Staleness check
    if context_dir.exists() and index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                idx = json.load(f)
            generated_at = idx.get("generated_at", "")
            if generated_at:
                from datetime import datetime

                scan_dt = datetime.fromisoformat(generated_at)
                from loom_context.security.filter import FileFilter

                file_filter = FileFilter(root)
                stale = 0
                scan_ts = scan_dt.timestamp()
                for fp in file_filter.walk():
                    if fp.suffix in {".ts", ".tsx", ".js", ".jsx", ".py"}:
                        try:
                            if fp.stat().st_mtime > scan_ts:
                                stale += 1
                        except OSError:
                            pass
                        if stale > 10:
                            break

                if stale == 0:
                    ok("context is fresh")
                else:
                    warn(f"context is stale ({stale}+ files changed) — run 'loom scan .'")
        except (ValueError, OSError, json.JSONDecodeError):
            warn("could not check staleness")

    # Summary
    console.print("")
    if checks_failed:
        console.print(
            f"  {LOOMY_FAIL} {checks_passed} passed, "
            f"[red]{checks_failed} failed[/red], "
            f"[yellow]{checks_warned} warnings[/yellow]"
        )
    elif checks_warned:
        console.print(
            f"  {LOOMY_ALERT} {checks_passed} passed, [yellow]{checks_warned} warnings[/yellow]"
        )
    else:
        console.print(f"  {LOOMY_HAPPY} all {checks_passed} checks passed")
    console.print("")
