# 🕸️ Loom-Context

[![CI](https://github.com/jadruiz/Loom-Context/actions/workflows/ci.yml/badge.svg)](https://github.com/jadruiz/Loom-Context/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/loom-context)](https://pypi.org/project/loom-context/)
[![Python](https://img.shields.io/pypi/pyversions/loom-context)](https://pypi.org/project/loom-context/)
[![License](https://img.shields.io/github/license/jadruiz/Loom-Context)](LICENSE)

**Architecture context engine for AI-first engineering.**

```
        .  *  .  *  .
         \  |  /
      ── (O O) ──
         /  |  \
        *  .  *  .  *

  weaving context, one thread at a time
```

Loom scans your repository, infers architecture and conventions, and generates compact `.context/` that any AI agent can consume as project memory. No cloud, no LLM, no heavy deps — just deterministic analysis in <2 seconds.

```bash
pip install loom-context
cd your-project/
loom init .
```

> 📉 Tested on a 674-file React Native project: full scan in 0.9s, 107 boundary violations detected, bundles 93% smaller than full prompt.

---

## ⚡ Quick Start

```bash
loom init .                                  # scan + generate .context/ + .loom/
loom bundle "refactor auth" . --stdout       # task-specific context (93% smaller)
loom export . --agent claude                 # export for your AI agent
```

That's it. Your agent now has architecture, rules, naming, and boundaries — without reading 700 files.

---

## 🎯 15 Commands

### 🔍 Scan & Generate

```bash
loom init .                    # Full scan + .context/ + .loom/ + audit
loom scan .                    # Re-scan and update .context/
```

### 📝 Context for AI

```bash
loom prompt . --stdout         # Full master prompt (all context)
loom focus "auth" . --stdout   # Filtered prompt by topic
loom bundle "task" . --stdout  # Task-specific bundle with manifest
loom handoff "task" . --save   # Session continuity summary
loom export . --agent claude   # Format for specific agent
```

### ✅ Quality & Audit

```bash
loom audit .                   # Validate naming + boundary rules
loom enrich .                  # Re-audit + refresh + persist findings
loom doctor .                  # Health check (11 diagnostics)
```

### 📊 State & Memory

```bash
loom status .                  # Project health dashboard
loom decide "..." -r "..." -s architecture  # Record decision
loom log "note" -p .           # Session memory
loom plan .                    # Summarize docs/plans
loom watch . --interval 60     # Continuous re-scan
```

---

## 📁 What Loom Generates

```
.context/                      ← canonical, reproducible, shareable
  index.json                   ← entry point + quick_rules
  architecture.md              ← patterns + layer boundaries
  naming.md                    ← conventions + suffix/prefix patterns
  directory-map.md             ← annotated directory tree
  stack.json                   ← categorized dependencies
  rules.json                   ← machine-readable rules for audit
  plans-summary.md             ← docs and plan progress
  exports/                     ← agent-specific formats
  bundles/                     ← task-specific context + manifests

.loom/                         ← live state, local per user
  inconsistencies.json         ← last audit findings
  decisions.jsonl              ← architectural decision records
  sessions.jsonl               ← session log with git metadata
  mutations.jsonl              ← context change history
```

---

## 🤖 Export for Your Agent

```bash
loom export . --agent claude   # → .context/exports/CLAUDE.md
loom export . --agent cursor   # → .context/exports/.cursorrules
loom export . --agent codex    # → .context/exports/AGENTS.md
loom export . --agent generic  # → .context/exports/.loom-export.md
```

---

## 🔍 What It Detects

| Area | Detection |
|------|-----------|
| 🏗️ Architecture | Clean Architecture, Hexagonal, MVC, MVVM, Pipeline, Feature-based, Layered |
| 📦 Project Type | React Native/Expo, Next.js, Angular, Vue, Python, Rust, Go, Java, and more |
| 🏷️ Naming | PascalCase, camelCase, kebab-case, snake_case, I-prefix, use-prefix, suffixes |
| 📦 Stack | 130+ known packages categorized (ui, state, db, testing, DI, etc.) |
| 📄 Docs | Markdown with frontmatter, plan status, section headings |
| ⚙️ Rules | Layer boundaries, naming conventions, import aliases |

---

## 🔒 Security

Three layers of filtering — your source code never appears in output:

1. ✅ Respects `.gitignore`
2. ✅ Respects `.contextignore`
3. ✅ Always excludes `.env`, `*.pem`, `*.key`, credentials

Output is metadata only: file names, patterns, rules, structure. Never source code.

---

## 🔁 Daily Workflow

```bash
# Morning: check state
loom status .
loom scan .

# Before a task: get focused context
loom bundle "implement payment flow" . --stdout | pbcopy

# During work: record decisions
loom decide "use Stripe adapter" -r "team standard" -s architecture

# End of day: persist and handoff
loom enrich .
loom handoff "payment flow" . --save
```

---

## 📊 Real-World Results

Tested on [Akana](https://github.com/jadruiz) — a 674-file React Native literacy app:

| Metric | Result |
|--------|--------|
| Scan time | 0.9s |
| Files analyzed | 674 files, 95 dependencies, 59 docs |
| Architecture detected | Clean Architecture + Hexagonal + Feature-based |
| Naming patterns | 67 Repositories, 28 Mappers, 17 Services, 14 ViewModels |
| Boundary violations | 107 (all in `core/` importing from `infrastructure/`) |
| Bundle vs prompt | 2.6KB vs 35KB (93% reduction) |
| Export formats | Claude, Cursor, Codex, Generic |

---

## 📚 Documentation

| Guide | What it covers |
|-------|---------------|
| [🚀 Quick Start](docs/guides/quickstart.md) | Install, first scan, daily workflow |
| [📖 CLI Reference](docs/guides/cli-reference.md) | All 15 commands with examples |
| [📁 Context Output](docs/guides/context-output.md) | .context/ and .loom/ structure |
| [🔒 Security](docs/guides/security.md) | 3-layer filtering model |
| [📐 Best Practices](docs/guides/best-practices.md) | Individual, team, and AI patterns |
| [🧠 Philosophy](docs/guides/philosophy.md) | The brain analogy + scientific references |
| [🕸️ Loomy](docs/guides/loomy.md) | The spider-neuron mascot |
| [📋 Roadmap](docs/plans/roadmap-v0.2-v0.4.md) | Version plan with delivery docs |

---

## 🛠️ Development

```bash
git clone https://github.com/jadruiz/Loom-Context.git
cd Loom-Context
pip install -e ".[dev]"

pytest                         # 104 tests, ~3s
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
- Zero AI/ML dependencies in base install

## License

MIT
