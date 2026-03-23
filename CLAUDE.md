# Loom-Context — AI Agent Guidelines

## Project Overview

Loom-Context is a Python CLI tool that scans software projects and generates
a `.context/` folder with architectural metadata for AI agents.
Deterministic core — no AI required. 25 commands, 457 tests, Apache-2.0.
**v0.9.0**: AI rankers + traces + governance + domain adapters + 25 commands.

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
adapters/*            ← domain-specific pipelines (code, brand, research, data)
store/*               ← .loom/ persistence (sessions, findings, decisions, mutations)
selector/*            ← bundle, handoff, compact, heuristic strategy, ranker
exporters/*           ← agent-specific output (claude, cursor, codex, generic)
models.py             ← typed contracts (frozen dataclasses)
metrics.py            ← per-layer health metrics
engine.py             ← orchestrates adapters + generators + audit (domain-driven)
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
├── domain_detector.py  ← DomainDetector: auto-infers project domain
└── domains/            ← domain definitions (code, research, data, brand)
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

## Domain Detection (v0.6.0)

Loom auto-detects project domain by matching file tree against `knowledge/domains/*.json`.

- **Domains**: `code`, `research`, `brand`, `data`, `mixed`, `unknown`
- **Detection**: `DomainDetector` scores markers, extensions, and directory patterns
- **Result**: `ScanResult.domain` + `.domain_confidence` + `.domain_details`
- **Prompts**: `.prompts/` include domain + governance rules automatically
- **Override**: `.loom/config.json` → `"domain": "research"` (not yet implemented)

### Domain-specific governance rules

`brand.json` defines rules enforced in generated prompts:
- i18n sync: docs must be kept in sync across languages
- Token consistency: design tokens are source of truth
- Asset naming: icons/logos follow naming conventions

### Adding a domain

1. Create `knowledge/domains/yourdomain.json` with markers, extensions, patterns
2. Optionally add `governance_rules` for domain-specific validation
3. Run `loom scan .` — DomainDetector picks it up automatically

## Security Rules

**CRITICAL — these rules are non-negotiable:**

1. **Never expose secrets**: `.env`, API keys, credentials, tokens MUST never appear
   in `.context/`, `.prompts/`, bundles, handoffs, or any Loom output
2. **Metadata only**: Loom outputs architectural metadata, NEVER source code content
3. **No absolute paths**: outputs must not contain system paths (`/Users/`, `/home/`)
4. **Treat agents as untrusted**: AI agents receive context, rules, and boundaries —
   never secrets, credentials, or unrestricted access
5. **3-layer file filter**: gitignore + hardcoded exclusions + secret pattern detection
6. **No admin privileges**: Loom runs as normal user, reads/writes only `.context/` and `.loom/`
7. **Local-first**: no data leaves the machine, no cloud, no telemetry
8. **Protected knowledge files**: `security.json`, `infrastructure.json`, `markers.json`
   cannot be overridden via `.loom/knowledge/`

### What agents receive from Loom

| Allowed | Forbidden |
|---|---|
| Project type, architecture, domain | Source code content |
| Naming conventions, layer boundaries | API keys, tokens, passwords |
| Dependency names and categories | .env file contents |
| File structure (paths, not content) | Absolute system paths |
| Governance rules and violations | Credentials or secrets |
| Quick rules and prompt templates | Internal IPs or infrastructure details |

### SDLC Security — Supply Chain Protection

**Dependency analysis:**
- Never blindly trust `pip install` / `npm install` — audit dependencies
- Use tools like Snyk, OSV-Scanner, or `pip-audit` before production
- Loom's `security.json` detects 33 secret patterns in scanned files
- `bandit` runs as part of QA (`make qa`) to catch security issues in Python code

**Secret management:**
- Use secret managers (Doppler, HashiCorp Vault) instead of `.env` files
- `.env` files can be read by misconfigured AI tools or info-stealing malware
- Loom's FileFilter excludes `.env`, credentials, and key files at scan time
- Pre-commit hooks (Husky, pre-commit) should block secrets from entering git

**Security priority matrix:**

| Layer | Tool | Action |
|---|---|---|
| Network | LuLu / Little Snitch | Block unknown outbound connections |
| Code | Snyk / bandit / Husky | Block commits with secrets or vulnerabilities |
| Identity | SSH keys with passphrase | Never store unencrypted private keys |
| AI/LLMs | Ollama / Llama local | Use local models for confidential data |
| Dependencies | pip-audit / OSV-Scanner | Audit before deploy |

### Terminal Hardening

- Run AI tools (Copilot, Cursor, Ollama) **without admin privileges**
- Isolate local models to specific directories
- Use `zsh-autosuggestions` and shell plugins with caution — cloned repos
  can contain malicious `.zshrc` or `.bashrc` that execute on shell init
- Never paste API keys, secrets, or proprietary code into commercial AI chats
- Verify binary signatures before installing new CLI tools

### Zero Trust for Developers

Even trusted tools must be verified:
- **Verify binaries**: check digital signatures before installing CLI tools
- **Monitor network**: periodically review which processes consume network
- **Sandbox experiments**: test experimental AI tools inside Docker containers or VMs
- **Loom follows this**: deterministic core, no network, no cloud, local-only execution

## Git Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`)
- **Scopes**: `scanner`, `generator`, `auditor`, `cli`, `security`, `engine`, `docs`, `knowledge`
- **Branches**: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`
- **Flow**: develop → release/vX.Y.Z → PR to main → tag → PyPI via CI
- **Never commit directly to main**

## Extension Rules

**Loom is extensible through defined contracts, not ad-hoc expansion.**

### What Loom IS and IS NOT

| Loom IS | Loom IS NOT |
|---|---|
| Compiler/orchestrator of operational context | General planner or autonomous agent |
| Domain-aware adapter system | Universal knowledge graph |
| Trace/audit recorder | LLM wrapper or chatbot framework |
| Agent context exporter | Business logic engine |

### Official extension points (v0.7.0)

These are the only stable interfaces for extending Loom:

1. `DomainAdapter` — add scanners/generators per domain
2. `ContextRanker` — swap ranking strategy (heuristic, hybrid, AI)
3. `GovernanceRule` — domain-specific validation rules (in domains/*.json)
4. `Exporter` — agent-specific output format
5. `DomainDetector` — domain inference from file tree (via domains/*.json)

### Rules for extensions

1. An extension MUST NOT change the core contract (ScanResult, Violation, etc.)
2. An extension MUST NOT depend on another extension
3. The core MUST work without AI — AI is always optional enhancement
4. Every extension MUST declare: input, output, side effects, fallback
5. Every extension MUST be disableable without breaking the base flow
6. Extensions write through ports only: trace store, exporter, adapter registry
7. Governance rules execute outside the agent — agent proposes, Loom validates

### Layer responsibilities

| Layer | Owns | Does NOT own |
|---|---|---|
| **Core** | detect, select, compact, export, trace, audit | planning, execution, AI decisions |
| **Adapters** | domain-specific scanners + generators | core contracts, cross-adapter deps |
| **IA (optional)** | ranking improvement, semantic matching | domain rules, policy decisions |
| **Agents** | task execution, code generation | Loom rules, trace mutation, audit bypass |
| **Observability** | metrics, cost tracking | functional decisions |

## Testing

- Run: `pytest` (457+ tests, 95% coverage)
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
9. **Domain-aware** — detect domain, apply domain-specific rules and governance
10. **Loom coordinates, agents execute** — Loom provides context, agents do the work
