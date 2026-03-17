---
type: changelog
---

# Changelog

All notable changes to Loom-Context will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## Branch Mapping

This changelog tracks released package versions, not every internal delivery plan.

Current branch interpretation:

- `develop`: active development line, keeps the current working package version
- `main`: stable integration line
- `release/0.2.0`: delta from `0.1.0` to `0.2.0`
- `release/0.2.1`: delta from `0.2.0` to `0.2.1`
- `release/0.2.2`: delta from `0.2.1` to `0.2.2`
- `release/0.3.0`: delta from `0.2.2` to `0.3.0`

See [`docs/guides/versioning.md`](docs/guides/versioning.md) for the branch/version policy.

## [0.2.0] - 2026-03-16

### Added — Commands (9 new, 15 total)
- `loom enrich`: re-audit, regenerate context, persist findings
- `loom decide`: record/show/clear architectural decisions
- `loom bundle`: task-specific context with heuristic selection (93% smaller than prompt)
- `loom handoff`: session continuity summary for resuming work
- `loom doctor`: 11-check health diagnostic
- `loom export --agent claude|cursor|codex|generic`: agent-specific output
- `--compact` flag on `prompt` and `bundle`: token-efficient format (71-89% reduction)
- `--top-k` and `--token-budget` flags on `bundle`: control output size
- `loom focus`: task-filtered prompt (existing, from v0.1.x)

### Added — Infrastructure
- `.loom/` directory for live operational state (separate from `.context/`)
- `store/` package: sessions, findings, decisions, mutations
- `selector/` package: heuristic strategy, bundle builder, handoff builder, compact formatter
- `exporters/` package: 4 agent adapters (Claude, Cursor, Codex, Generic) with Registry pattern
- `models.py`: typed contracts with frozen dataclasses
- `brand.py`: Loomy mascot with 8 expressions
- `GitHelper`: shared git utility (DRY)
- Frontmatter YAML parsing in DocsScanner (no PyYAML dependency)
- Pipeline architecture detection (scanners + generators)
- Audit integrated in `loom init` (non-blocking)
- Session migration from `.context/` to `.loom/`

### Added — Documentation
- Complete rewrite of README, quickstart, CLI reference, context output, security, best practices
- Philosophy guide with 8 scientific references (Miller, Hebb, Gibson, Ausubel, etc.)
- Loomy mascot guide with expressions and design philosophy
- Standard document format with frontmatter (docs/plans/format.md)
- Per-version delivery plans with lifecycle (planned → released → archived)
- Product scope definition (docs/plans/scope.md)

### Changed
- CLI modularized: `cli.py` (566 lines) → `cli/` package (15 command files, each <90 lines)
- `engine.scan()` returns `ScanResult` (typed) instead of `dict[str, Any]`
- `Violation.severity` now `Literal["error", "warning", "info"]`
- Session log moved from `.context/` to `.loom/`
- Exports write to `.context/exports/` (never overwrite user files)
- StructureScanner detects Python packages one level deep

### Removed
- Duplicated git command logic across 4 files (replaced by GitHelper)
- Monolithic `cli.py`

### Tests
- 108 tests (was 25 in v0.1.0), all passing in ~3s
- Coverage: file filter, scanners, engine, CLI, auditors, edge cases, sessions, focus, status, findings, decisions, mutations, init+audit, enrich, decide, bundle, handoff, doctor, export, compact, pipeline detection, frontmatter, typed contracts

[0.2.0]: https://github.com/jadruiz/Loom-Context/releases/tag/v0.2.0

## [0.1.0] - 2026-03-14

### Added
- Initial release of Loom-Context
- **CLI** with 6 commands: `init`, `scan`, `prompt`, `audit`, `plan`, `watch`
- **StructureScanner**: detects project type (15+ types), architecture patterns (Clean Architecture, Hexagonal, MVC, MVVM, Feature-based, Layered), directory tree with 80+ semantic annotations
- **DependencyScanner**: parses package.json, pyproject.toml, requirements.txt; categorizes 130+ known packages into functional groups
- **CodeScanner**: infers naming conventions from code (PascalCase, camelCase, kebab-case, snake_case), detects suffix/prefix patterns (Service, Repository, Adapter, I-prefix, use-prefix), reads tsconfig.json import aliases
- **DocsScanner**: indexes markdown documentation, classifies by type (architecture, plan, feature, setup), extracts plan status items
- **ContextGenerator**: generates 7 structured files in `.context/` (index.json, architecture.md, naming.md, directory-map.md, stack.json, rules.json, plans-summary.md)
- **PromptGenerator**: compiles all `.context/` files into a single master AI system prompt
- **NamingAuditor**: validates interface prefix conventions
- **StructureAuditor**: validates layer boundary rules (forbidden imports between architectural layers)
- **Security**: 3-layer file filtering (`.gitignore` + `.contextignore` + hardcoded secrets patterns)
- **25 unit tests** covering all components
- **Documentation**: 13 docs covering philosophy, architecture, patterns, quickstart, CLI reference, security, best practices, diagrams, and scientific references
- Rich terminal output with tables and panels

### Known Limitations
- `.context/loom.json` overrides are read but `extra_rules` and `audit_exceptions` are not yet processed
- Incremental scan (`loom scan`) re-scans everything (true incremental planned for 0.2)
- Auditors only check TypeScript/JavaScript files for naming and imports
- No plugin system yet (scanners/auditors are hardcoded)

[0.1.0]: https://github.com/jadruiz/Loom-Context/releases/tag/v0.1.0
