# Loom-Context — AI Agent Guidelines

## Project Overview

Loom-Context is a Python CLI tool that scans software projects and generates
a `.context/` folder with architectural metadata for AI agents.
Deterministic core — no AI required. 17 commands, 365 tests, Apache-2.0.

## Architecture

- **Pattern**: Clean pipeline — scanners → engine → generators
- **Language**: Python 3.9+ (use `from __future__ import annotations`, `Optional[X]` not `X | None`)
- **Entry point**: `loom` CLI via Click (`src/loom_context/cli/__init__.py`)

## Layer Rules

```
knowledge/            ← centralized knowledge base (JSON + registry), no internal deps
security/filter.py    ← foundation, depends on knowledge only
scanners/*            ← depend on knowledge + security + base
generators/*          ← depend on scan results, no scanner imports
auditors/*            ← depend on knowledge + security + rules.json
store/*               ← .loom/ persistence (sessions, findings, decisions, mutations)
selector/*            ← bundle, handoff, compact, heuristic strategy
exporters/*           ← agent-specific output (claude, cursor, codex, generic)
models.py             ← typed contracts (frozen dataclasses)
metrics.py            ← per-layer health metrics
engine.py             ← orchestrates scanners + generators + audit
cli/commands/*.py     ← one file per command, no business logic
```

## Knowledge Registry

All detection patterns live in `knowledge/*.json` — never hardcode patterns in scanners.

```
knowledge/
├── __init__.py         ← get_registry() singleton API
├── registry.py         ← KnowledgeRegistry: lazy load + query
├── scorer.py           ← SignalScorer: multi-signal architecture detection
├── models.py           ← Typed dataclasses for knowledge entities
├── languages.json      ← 22 languages (extensions, markers, naming, frameworks)
├── ecosystems.json     ← 332 packages across 8 ecosystems
├── architectures.json  ← 15 architecture patterns with weighted scoring
├── directories.json    ← 170+ semantic directory annotations
├── security.json       ← dir exclusions + secret patterns
├── infrastructure.json ← service definitions + package mapping
├── roles.json          ← 47 suffixes + 8 prefixes (architectural roles)
├── docs.json           ← documentation classification rules
├── design_patterns.json ← 22 GoF + modern patterns with detection signals
├── stop_words.json     ← EN + ES stop words for query tokenization
└── domains/            ← domain definitions (code, research, data)
```

To add a new language or pattern: edit the JSON, never modify scanner Python code.

### Local Overrides

Users can extend the knowledge base locally without modifying the package:

```
.loom/knowledge/           ← not tracked in git
├── languages.json         ← adds/overrides languages
├── ecosystems.json        ← adds packages to ecosystems
├── architectures.json     ← adds custom architecture patterns
├── directories.json       ← adds directory annotations
└── ...                    ← any knowledge/*.json can be extended
```

Local overrides are **deep-merged** with built-in data:
- Dicts: local keys extend/override built-in keys
- Lists: local items are appended (no duplicates)
- Scalars: local value wins

## Naming Conventions

- **Files**: snake_case (`code.py`, `structure.py`)
- **Classes**: PascalCase (`LoomEngine`, `FileFilter`, `StructureScanner`)
- **Functions**: snake_case (`generate_quick_rules`, `_detect_project_type`)
- **Constants**: UPPER_SNAKE (`HARDCODED_DIR_EXCLUSIONS`, `CODE_EXTENSIONS`)
- **Private methods**: underscore prefix (`_load_gitignore`, `_scan_package_json`)
- **Scanner naming**: `{What}Scanner` (`StructureScanner`, `DependencyScanner`)
- **Generator naming**: `{What}Generator` (`IndexGenerator`, `PlanGenerator`)
- **Auditor naming**: `{What}Auditor` (`NamingAuditor`, `StructureAuditor`)
- **Store naming**: `{What}Store` or `{What}Log` (`FindingsStore`, `DecisionLog`)
- **Exporter naming**: `{What}Exporter` (`ClaudeExporter`, `CursorExporter`)

## Code Standards

- **Lint**: `ruff check src/ tests/` must pass
- **Format**: `ruff format src/ tests/` — double quotes, 100 char line length
- **Types**: all public functions must have type annotations
- **Security**: `bandit -c pyproject.toml --recursive src/` must pass
- **Docstrings**: one-line for simple functions, required on public classes
- **No print()**: use `console.print()` (Rich) in CLI, or `click.echo()` for stdout piping
- **No project-specific references**: keep docs generic, no named projects

## Git Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`)
- **Scopes**: `scanner`, `generator`, `auditor`, `cli`, `security`, `engine`, `docs`
- **Branches**: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`
- **Flow**: develop → release/vX.Y.Z → PR to main → tag → PyPI via CI
- **Never commit directly to main**

## Testing

- Run: `pytest` (365+ tests, 95% coverage)
- Fixture `tmp_project` in `conftest.py` provides a complete mock project
- Quality: `make qa` runs lint + format + types + security + tests

## Key Design Principles

1. **Deterministic core** — no AI required, reproducible output
2. **Scan much, ask nothing** — auto-detect, don't prompt the user
3. **Metadata only** — never include source code in `.context/` output
4. **Security first** — 3-layer file filtering, secrets always excluded
5. **Progressive consumption** — quick_rules (30s) → bundle (2min) → full (5min)
6. **Stay fast** — scanning 700 files must complete in < 2 seconds
7. **Stay light** — 4 runtime dependencies only
8. **Axiomatic context** — rules as invariants, not probability
