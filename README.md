# Loom-Context

[![CI](https://github.com/Basal-Research-Group/Loom-Context/actions/workflows/ci.yml/badge.svg)](https://github.com/Basal-Research-Group/Loom-Context/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/loom-context)](https://pypi.org/project/loom-context/)
[![Python](https://img.shields.io/pypi/pyversions/loom-context)](https://pypi.org/project/loom-context/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

**Deterministic, axiomatic context for AI-first engineering.**

[English](#-quick-start) · [Español](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/README.es.md)

```
        .  *  .  *  .
         \  |  /
      ── (O O) ──
         /  |  \
        *  .  *  .  *

  less tokens, more signal
```

Loom scans your project, infers architecture and conventions, and compiles compact context
that any AI agent (Claude, Codex, Cursor, Copilot) can consume — so they stop re-reading
700 files and start working with the right 7.

```
Without Loom:  35KB prompt  →  agent reads everything  →  drift, waste, hallucinations
With Loom:     2.6KB bundle →  agent reads what matters →  precision, consistency, savings
```

No cloud. No LLM. No heavy deps. Deterministic analysis in <2 seconds. 91% fewer tokens.

**v0.5.0**: 22 languages · 421 known packages · 23 architecture patterns · 47 design patterns · 9 dependency parsers

---

## Prerequisites

Loom requires **Python 3.9 or higher**. It has 4 lightweight dependencies (`click`, `rich`, `pathspec`, `jinja2`) — no AI/ML libraries.

<details>
<summary><strong>macOS</strong> — install Python if you don't have it</summary>

```bash
# Check if Python is installed
python3 --version

# If not installed, use Homebrew
brew install python@3.12

# Install pipx (recommended for CLI tools)
brew install pipx
pipx ensurepath
```

</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
# Python is usually pre-installed, verify version
python3 --version

# If needed
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Install pipx
sudo apt install pipx
pipx ensurepath
```

</details>

<details>
<summary><strong>Windows</strong></summary>

```powershell
# Option 1: Download from python.org
# https://www.python.org/downloads/ (check "Add to PATH" during install)

# Option 2: Via winget
winget install Python.Python.3.12

# Install pipx
pip install --user pipx
pipx ensurepath
```

> After installing, restart your terminal so PATH changes take effect.

</details>

---

## Install Loom

### Option A: pipx (recommended)

pipx installs Loom in its own isolated environment — no venv needed, no warnings, no conflicts:

```bash
pipx install loom-context
```

Or try it without installing:

```bash
pipx run loom-context --help
```

### Option B: pip with virtual environment

If you prefer pip, always use a virtual environment to avoid system conflicts:

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

pip install loom-context
```

> Without a virtual environment, `pip install` on modern macOS/Linux will
> show "externally-managed-environment" errors (PEP 668). Use pipx or venv.

### Verify

```bash
loom --version
# loom, version 0.5.0
```

> If `loom` is not found: with pipx, run `pipx ensurepath` and restart terminal.
> With venv, make sure it's activated (`source .venv/bin/activate`).

---

## Quick Start

The fastest way to get started — one command does everything:

```bash
cd your-project/
loom setup .
```

This will:
1. Scan your project (type, architecture, naming, dependencies)
2. Generate `.context/` with all metadata
3. Detect infrastructure services (Redis, PostgreSQL, etc.) and check if they're running
4. Detect existing agent files (CLAUDE.md, AGENTS.md, .cursorrules)
5. Ask which agents to install — with automatic backup of existing files

For non-interactive use (CI, scripts):

```bash
loom setup . --preset full --force     # all agents, no prompts
loom setup . --preset claude --force   # just Claude
```

### Or step by step:

```bash
loom init .                                  # scan + generate .context/
loom bundle "refactor auth" . --stdout       # task-specific context (91% smaller)
loom export . --agent claude --install       # install CLAUDE.md at project root
```

---

## 24 Commands

### Scan & Generate

```bash
loom init .                    # Full scan + .context/ + .loom/ + audit
loom scan .                    # Re-scan (uses cache, <0.1s if no changes)
loom scan . --force            # Force full re-scan
```

### Context for AI

```bash
loom prompt .                  # Full master prompt (~1,300 tokens)
loom prompt . --compact        # Compact format (92% saved)
loom prompt . --ultra-compact  # Ultra-compact (<100 chars, 99% saved)
loom bundle "task" . --stdout  # Task-specific bundle with manifest
loom focus "auth" . --stdout   # Filtered prompt by topic
loom handoff "task" . --save   # Session continuity summary
```

### Export & Setup

```bash
loom setup .                   # Interactive wizard (scan + install agents)
loom export . --agent claude   # Export for Claude (CLAUDE.md)
loom export . --agent cursor   # Export for Cursor (.cursorrules)
loom export . --agent codex    # Export for Codex (AGENTS.md)
loom export . --agent copilot  # Export for Copilot (.github/copilot-instructions.md)
loom export . --agent generic  # Universal format
loom export . --agent claude --install  # Install to project root (with backup)
```

### Infrastructure

```bash
loom infra .                   # Check project's required services
loom infra . --start           # Auto-start stopped services
loom infra . --start --docker  # Start via Docker
```

### Quality & Audit

```bash
loom audit .                   # Validate naming + boundary rules
loom enrich .                  # Re-audit + refresh + persist findings
loom doctor .                  # Health check (10 diagnostics)
loom metrics .                 # Layer balance metrics
```

### State & Memory

```bash
loom status .                  # Project health dashboard
loom decide "..." -r "..."     # Record architectural decision
loom log "note" -p .           # Session memory
loom plan .                    # Summarize docs/plans
loom report .                  # Usage analytics
loom watch . --interval 60     # Continuous re-scan
```

### Knowledge Registry

```bash
loom knowledge list            # What Loom knows (langs, patterns, packages)
loom knowledge langs           # All 22 supported languages
loom knowledge patterns        # 23 architecture + 47 design patterns
loom knowledge packages        # 421 packages across 8 ecosystems
```

### Task Prompts

```bash
loom ask "implement auth" .                    # Generate context-aware prompt
loom ask "fix login bug" . --mode fix --stdout # Pipe to clipboard
loom ask "review PR" . --mode review -o pr.md  # Save to file
```

### Global Project Registry

```bash
loom projects                  # List all projects using Loom on this machine
loom projects --add "My API"   # Add description to current project
loom projects --json           # JSON output
```

---

## What Loom Generates

```
.context/                      ← canonical, reproducible, shareable
  index.json                   ← entry point + quick_rules
  architecture.md              ← patterns + layer boundaries
  naming.md                    ← conventions + suffix/prefix patterns
  directory-map.md             ← annotated directory tree
  stack.json                   ← categorized dependencies
  rules.json                   ← machine-readable rules for audit
  plans-summary.md             ← active vs completed plan tracking
  exports/                     ← agent-specific formats
  bundles/                     ← task-specific context + manifests

.prompts/                      ← copy-paste-ready prompts with project context
  onboarding.md                ← understand the project
  implement-feature.md         ← implement with architecture rules
  review-code.md               ← code review checklist
  fix-bug.md                   ← debug with data flow
  refactor.md                  ← safe refactoring plan

.loom/                         ← live state, local per user
  inconsistencies.json         ← last audit findings
  decisions.jsonl              ← architectural decision records
  sessions.jsonl               ← session log with git metadata
  mutations.jsonl              ← context change history
  backups/                     ← automatic backups before file overwrites
  cache/                       ← scan cache for instant re-scans
  reports/                     ← metrics, deltas, plans (tracked in git)
```

---

## Export for Your Agent

```bash
loom setup . --preset full --force   # Install all 5 agents at once
```

Or individually:

```bash
loom export . --agent claude --install   # → CLAUDE.md (with backup if exists)
loom export . --agent cursor --install   # → .cursorrules
loom export . --agent codex --install    # → AGENTS.md
loom export . --agent copilot --install  # → .github/copilot-instructions.md
loom export . --agent generic --install  # → .loom-export.md
```

> When installing, Loom checks if the file already exists. If it does,
> it creates a backup in `.loom/backups/` before overwriting. Use `--force`
> to skip confirmation, `--no-backup` to skip the backup.

---

## Infrastructure Check

Loom reads your project's dependencies and checks if required services are running.
**These are your project's requirements, not Loom's** — Loom itself only needs Python.

```bash
loom infra .
```

```
       Project Infrastructure (from pnpm dependencies)
┏━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Service    ┃ Category ┃ Port ┃ Installed ┃ Running ┃ Config Env   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ PostgreSQL │ database │ 5432 │ yes       │ running │ DATABASE_URL │
│ Redis      │ cache    │ 6379 │ no        │ stopped │ REDIS_URL    │
└────────────┴──────────┴──────┴───────────┴─────────┴──────────────┘
```

Auto-start stopped services:

```bash
loom infra . --start              # native (brew/systemctl)
loom infra . --start --docker     # Docker containers
```

<details>
<summary><strong>Manual install guides per service</strong></summary>

#### Redis

| Platform | Install | Start |
|----------|---------|-------|
| macOS | `brew install redis` | `brew services start redis` |
| Linux | `sudo apt install redis-server` | `sudo systemctl start redis` |
| Docker | `docker run -d --name redis -p 6379:6379 redis:alpine` | — |
| Windows | [Download](https://github.com/microsoftarchive/redis/releases) or WSL | — |

Verify: `redis-cli ping` should return `PONG`. Default port: **6379**.
Config env: `REDIS_URL=redis://localhost:6379`

#### PostgreSQL

| Platform | Install | Start |
|----------|---------|-------|
| macOS | `brew install postgresql@16` | `brew services start postgresql@16` |
| Linux | `sudo apt install postgresql` | `sudo systemctl start postgresql` |
| Docker | `docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine` | — |
| Windows | [Download installer](https://www.postgresql.org/download/windows/) | — |

Verify: `pg_isready` should return `accepting connections`. Default port: **5432**.
Config env: `DATABASE_URL=postgresql://user:pass@localhost:5432/dbname`

#### MongoDB

| Platform | Install | Start |
|----------|---------|-------|
| macOS | `brew install mongodb-community` | `brew services start mongodb-community` |
| Linux | [Install guide](https://www.mongodb.com/docs/manual/administration/install-on-linux/) | `sudo systemctl start mongod` |
| Docker | `docker run -d --name mongo -p 27017:27017 mongo:7` | — |

Default port: **27017**. Config env: `MONGODB_URI=mongodb://localhost:27017/dbname`

#### MySQL

| Platform | Install | Start |
|----------|---------|-------|
| macOS | `brew install mysql` | `brew services start mysql` |
| Linux | `sudo apt install mysql-server` | `sudo systemctl start mysql` |
| Docker | `docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8` | — |

Default port: **3306**. Config env: `MYSQL_URL=mysql://user:pass@localhost:3306/dbname`

</details>

Supports: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, RabbitMQ, Kafka, Meilisearch, MinIO, Memcached, ClickHouse, Neo4j, SQLite.

---

## What It Detects

| Area | Detection |
|------|-----------|
| Languages | Python, TypeScript, JavaScript, Ruby, Go, Rust, Java, C#, PHP, Swift, Kotlin, Scala, Elixir, Dart, and 8 more |
| Architecture | 23 patterns with confidence scoring: Clean, Hexagonal, MVC, DDD, CQRS, Event-Driven, Microservices, Serverless, Design System, Atomic Design, Go Standard, Rails Convention, and more |
| Design Patterns | 47 patterns: GoF complete (Singleton, Factory, Observer, Strategy...) + enterprise (Circuit Breaker, Saga, CQRS, Event Sourcing...) |
| Code Smells | God class, hardcoded secrets, empty catch, SQL injection risk, missing lockfile |
| Stack | 421 packages across 8 ecosystems (npm, pip, gem, cargo, hex, go, maven, nuget) |
| Monorepo | pnpm, yarn, npm workspaces, Cargo workspaces, Go workspaces, Maven multi-module, Gradle multi-project, Elixir umbrella |
| Naming | PascalCase, camelCase, kebab-case, snake_case, 47 role suffixes, 8 prefixes |
| Docs | Markdown with frontmatter, plan status tracking (active vs completed) |
| Rules | Layer boundaries, naming conventions, import aliases |
| Infrastructure | 13 services with port check, install hints, Docker commands |

---

## Token Savings

Every output command shows how many tokens you're saving:

```
  Bundle for "refactor auth"
  656 chars | 7 sections | strategy: heuristic
  ~118 tokens vs ~1,359 full prompt (91% saved)
```

```
  Prompt: 766 chars, ~107 tokens (92% saved vs full)
```

Use `--token-budget` to cap output:

```bash
loom bundle "task" . --token-budget 500
# Budget: ~118/500 tokens (23%)
```

---

## Security

Three layers of filtering — your source code never appears in output:

1. Respects `.gitignore`
2. Respects `.contextignore`
3. Always excludes `.env`, `*.pem`, `*.key`, credentials

Output is metadata only: file names, patterns, rules, structure. Never source code.

---

## Daily Workflow

```bash
# Morning: check state
loom status .
loom scan .                                # cached if no changes

# Before a task: get focused context
loom bundle "implement payment flow" . --stdout | pbcopy

# During work: record decisions
loom decide "use Stripe adapter" -r "team standard" -s architecture

# End of day: persist and handoff
loom enrich .
loom handoff "payment flow" . --save
```

---

## Real-World Results

Tested on 3 projects:

| Project | Type | Files | Scan Time | Architecture |
|---------|------|-------|-----------|-------------|
| Python CLI | Python | 72 | 0.1s | Pipeline |
| React Native | Expo | 683 | 0.8s | Clean + Hexagonal + Feature |
| NestJS Monorepo | Node.js | 1,419 | 1.6s | Layered Monorepo |

| Metric | Value |
|--------|-------|
| Bundle vs full prompt | 91% reduction |
| Compact prompt | 92% saved |
| Ultra-compact | 99% saved (<100 chars) |
| Cached re-scan | 0.02s |
| Export formats | Claude, Cursor, Codex, Copilot, Generic |
| Infrastructure services | 18 detected with port check |

---

## Documentation

| Guide | What it covers |
|-------|---------------|
| [Quick Start](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/quickstart.md) | Install, first scan, daily workflow |
| [CLI Reference](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/cli-reference.md) | All 24 commands with examples |
| [Context Output](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/context-output.md) | .context/ and .loom/ structure |
| [Security](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/security.md) | 3-layer filtering model |
| [Best Practices](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/best-practices.md) | Individual, team, and AI patterns |
| [Philosophy](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/philosophy.md) | The brain analogy + scientific references |
| [Roadmap](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/plans/roadmap-v0.5-v1.0.md) | Version plan v0.5-v1.0 |

---

## Development

```bash
git clone https://github.com/Basal-Research-Group/Loom-Context.git
cd Loom-Context
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                         # 386 tests, ~15s
ruff check src/ tests/         # lint
ruff format --check src/ tests/  # format
```

- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, conventions, PR process
- [CHANGELOG.md](CHANGELOG.md) — release history
- [SECURITY.md](SECURITY.md) — vulnerability reporting

---

## Requirements

- Python 3.9+
- 4 runtime deps: `click`, `rich`, `pathspec`, `jinja2`
- Zero AI/ML dependencies

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
