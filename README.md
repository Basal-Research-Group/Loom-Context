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

---

## Install

```bash
# Recommended — installs in isolated environment, no venv needed
pipx install loom-context
```

> Don't have pipx? `brew install pipx` (macOS) or `sudo apt install pipx` (Linux).

Or try it without installing:

```bash
pipx run loom-context init .
```

<details>
<summary>Alternative: pip with virtual environment</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows
pip install loom-context
```

</details>

Verify:

```bash
loom --version
# loom, version 0.4.0
```

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

## 20 Commands

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

Loom reads your project's dependencies and checks if required services are running:

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

  Redis is not running
    Install: brew install redis
    Docker:  docker run -d --name redis -p 6379:6379 redis:alpine

  Run loom infra --start to auto-start stopped services
```

> These are YOUR project's requirements, not Loom's.
> Loom itself only needs Python + 4 libraries.

Supports: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, RabbitMQ, Kafka, Meilisearch, MinIO.

---

## What It Detects

| Area | Detection |
|------|-----------|
| Architecture | Clean Architecture, Hexagonal, MVC, MVVM, Pipeline, Feature-based, NestJS, Layered |
| Project Type | React Native/Expo, Next.js, NestJS, Angular, Vue, Python, Rust, Go, Terraform, Turborepo, Nx, and more |
| Naming | PascalCase, camelCase, kebab-case, snake_case, I-prefix, use-prefix, suffixes |
| Stack | 130+ known packages categorized (ui, state, db, testing, DI, etc.) |
| Docs | Markdown with frontmatter, plan status tracking (active vs completed) |
| Rules | Layer boundaries, naming conventions, import aliases |
| Infrastructure | 18 services with port check, install hints, Docker commands |

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
| [CLI Reference](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/cli-reference.md) | All 20 commands with examples |
| [Context Output](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/context-output.md) | .context/ and .loom/ structure |
| [Security](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/security.md) | 3-layer filtering model |
| [Best Practices](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/best-practices.md) | Individual, team, and AI patterns |
| [Philosophy](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/guides/philosophy.md) | The brain analogy + scientific references |
| [Roadmap](https://github.com/Basal-Research-Group/Loom-Context/blob/main/docs/plans/roadmap-v0.2-v0.4.md) | Version plan with delivery docs |

---

## Development

```bash
git clone https://github.com/Basal-Research-Group/Loom-Context.git
cd Loom-Context
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                         # 305 tests, ~8s
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
