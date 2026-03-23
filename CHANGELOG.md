---
type: changelog
---

# Changelog

All notable changes to Loom-Context will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.7.0] - 2026-03-23

### Added — Domain Adapters: Loom Adapts to What It Scans
- `DomainAdapter` base class: defines scanners + generators per domain
- `CodeAdapter`: default adapter, runs all 4 original scanners (backward compatible)
- `BrandAdapter`: structure + docs scanners, generates `brand.md` + `governance.md`
- `ResearchAdapter`: structure + docs + deps + code, generates `research.md`
- `DataAdapter`: structure + docs + deps + code, generates `data-pipelines.md`
- Adapter registry: `get_adapter(domain)` resolves domain → adapter automatically
- Engine now selects adapter dynamically by detected domain
- Brand projects (Kinsignia) get domain-specific `.context/` files (brand.md, governance.md)
- `ContextRanker` interface with strategy pattern for file ranking
- `HeuristicRanker`: keyword + path matching ranker (default, no AI deps)
- `RankedFile` and `RankingResult` typed models for ranking output

### Changed
- `engine.py`: refactored from 4 hardcoded scanners to adapter-driven pipeline
- Engine stores `_last_adapter` for domain-specific post-generation
- Adapters provide default empty dicts for missing scanner results (backward compat)
- Brand projects generate 14 files (vs 12 for code projects)

## [0.6.0] - 2026-03-23

### Added — Domain Detection: Loom Knows What It's Scanning
- `DomainDetector`: automatic domain inference from file tree (markers, extensions, directory patterns)
- 4 domain definitions: `code`, `research`, `brand`, `data` (in `knowledge/domains/*.json`)
- `ScanResult.domain`, `.domain_confidence`, `.domain_details` fields
- `DomainMatch` and `DomainDetectionResult` typed models
- Domain displayed in `loom status` output
- Domain persisted in `.context/index.json` (`project.domain`, `project.domain_confidence`, `project.domain_active`)
- `.prompts/` now include `Domain:` line with detected domain
- Domain-specific governance rules injected into prompts (brand: i18n sync, token consistency, asset naming)
- Loom coordination rules in all generated prompts ("Do NOT bypass Loom rules")
- Code domain boost: projects with package managers (package.json, pyproject.toml, etc.) get priority over ambiguous brand signals
- Smart disambiguation: React Native apps with assets/ and icons/ correctly detected as `code`, not `mixed`

### Changed
- `engine.py`: runs `DomainDetector` during scan, populates ScanResult domain fields
- `IndexGenerator`: persists domain to index.json for agent consumption
- `prompts_dir.py`: injects domain + governance rules + Loom coordination rules
- `status.py` + `cli/commands/status.py`: displays domain in status panel
- `.loom/cache/hashes.json`: now includes domain in cached scan results

### Architecture Decisions Documented
- Loom = coordination layer (detect/select/compact/export/trace/audit)
- Domain Adapter Protocol designed (v0.7.0)
- TaskIntent, ResolutionTrace, AgentHandoff contracts specified
- ContextRanker strategy pattern (Heuristic → Ollama → Embedding) designed
- Loom Core vs Loom Assist separation defined
- Migration strategy: shadow mode → gradual promotion → distillation
- 10 immutable principles documented

## [0.5.0] - 2026-03-22

### Added — Knowledge Registry: El Cerebro de Loom
- `knowledge/` module: centralized knowledge base with 16 JSON data files
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
- `design_patterns.json`: 47 design patterns (GoF complete + enterprise + resilience)
- `code_smells.json`: 17 code smell detectors (god class, secrets, SQL injection, etc.)
- `prompt_templates.json`: context-aware prompt rules for 12 architectures + 6 ecosystems
- `domains/brand.json`: brand & product domain definition
- `loom ask`: task prompts with injected context (implement, review, fix, refactor modes)
- `loom projects`: global project registry (~/.loom/registry.json)
- `.prompts/` auto-generated: 5 copy-paste-ready prompts per project
- `SmellAuditor`: god class, hardcoded secrets, empty catch, SQL injection, deep nesting, TODO/FIXME, console in production, missing lockfile, long parameters
- Multi-ecosystem monorepo: Cargo workspaces, Go workspaces, Maven multi-module, Gradle, Elixir umbrella
- Deep recursive scanning (4 levels) replaces 1-level shallow scan
- Architecture patterns: go-standard, rails-convention, design-system, atomic-design, onion, vertical-slice, plugin, space-based (+8 total)
- 105 new tests (386 total, was 281)

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
