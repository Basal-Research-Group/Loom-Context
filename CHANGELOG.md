---
type: changelog
---

# Changelog

All notable changes to Loom-Context will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-03-20

### Added — Knowledge Registry: El Cerebro de Loom
- `knowledge/` module: centralized knowledge base with 13 JSON data files
- `KnowledgeRegistry`: singleton API with lazy loading, caching, 25+ typed queries
- `SignalScorer`: multi-signal architecture detection with weighted scoring and confidence levels
- `languages.json`: 22 programming languages across 3 tiers with extensions, markers, naming, code patterns, and frameworks
- `ecosystems.json`: 332 packages across 8 ecosystems (npm, pip, gem, cargo, hex, go, maven, nuget) + 18 inference rules
- `architectures.json`: 15 architecture patterns with scoring (adds DDD, event-driven, CQRS, microservices, serverless, monolith-modular)
- `directories.json`: 188 semantic directory annotations (was 129)
- `markers.json`: data-driven project type detection (replaces hardcoded marker lists)
- `security.json`: 45 dir exclusions + 33 secret patterns (extended per-language: Rust, Elixir, Ruby, Go)
- `infrastructure.json`: 13 services + 45 package mappings (adds Memcached, ClickHouse, Neo4j)
- `roles.json`: 47 architectural suffixes + 8 prefixes (adds Ruby, Go, Rust, DDD roles)
- `design_patterns.json`: 22 GoF + modern design patterns with per-language detection signals
- `domains/`: code.json, research.json, data.json domain definitions
- Local knowledge overrides via `.loom/knowledge/` (deep merge, not tracked in git)
- 7 new dependency parsers: Gemfile, Cargo.toml, go.mod, mix.exs, pom.xml, build.gradle(.kts), *.csproj
- 60 new tests for knowledge module + 24 new tests for dependency parsers (365 total, was 305)

### Changed
- All 11 scanners/auditors/generators migrated from hardcoded constants to KnowledgeRegistry
- Architecture detection uses weighted signals instead of exact directory-set matching (legacy compat preserved)
- `_detect_project_type` fully data-driven via `markers.json` (zero hardcoded markers in Python)
- `InfraScanner` fully migrated to registry (ServiceDefs from JSON, platform-aware commands)
- CODE_EXTENSIONS consolidated from 4 duplicated definitions to single source of truth (49 extensions)
- STOP_WORDS consolidated from 2 duplicated definitions to single source (141 words EN+ES)
- DependencyScanner supports 9 package formats (was 3)

### Removed
- 17 hardcoded knowledge databases scattered across 8 Python files (~650 entries)
- All inline ServiceDef instances in infra.py
- `_infer_category()` function (replaced by registry inference rules)

---

## [0.4.0] - 2026-03-19

### Added — Adoption: Measurable Savings & Zero Friction
- Token counting and savings metrics in CLI output
- Incremental scan caching (hash-based invalidation)
- Zero-friction agent integration setup wizard
- `loom setup` with presets (minimal, full, claude)
- Cross-platform demo script
- Database context generation (Prisma schema + migrations)

### Changed
- Improved performance with scan result caching
- README and quickstart rewritten for v0.4.0

---

## [0.3.0] - 2026-03-18

### Added — Analysis & Observability (v0.3.0)
- `loom metrics`: health metrics per layer (files, code, dirs, balance score)
- `loom report`: usage analytics from `.loom/reports/usage.jsonl`
- `loom audit --summary`: violations grouped by directory and rule
- `--verbose / -v`: global debug logging flag
- Naming by role analysis (hooks=camelCase, components=PascalCase vs 50% global)
- Monorepo detection (workspaces, packages/, apps/, pnpm-workspace.yaml)
- `.loom/reports/metrics.json` persistence
- 12 new tests (269 total, 95% coverage)

### Added — Context Engine (v0.2.0, included)

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
- License updated from MIT to Apache-2.0 with `NOTICE`, contributor credit, and trademark guidance

### Removed
- Duplicated git command logic across 4 files (replaced by GitHelper)
- Monolithic `cli.py`

### Tests
- 108 tests (was 25 in v0.1.0), all passing in ~3s
- Coverage: file filter, scanners, engine, CLI, auditors, edge cases, sessions, focus, status, findings, decisions, mutations, init+audit, enrich, decide, bundle, handoff, doctor, export, compact, pipeline detection, frontmatter, typed contracts

[0.2.0]: https://github.com/Basal-Research-Group/Loom-Context/releases/tag/v0.2.0

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

[0.1.0]: https://github.com/Basal-Research-Group/Loom-Context/releases/tag/v0.1.0
