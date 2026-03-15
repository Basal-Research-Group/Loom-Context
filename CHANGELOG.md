# Changelog

All notable changes to Loom-Context will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
