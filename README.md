# Loom-Context

**The Architecture Context Engine for AI-First Engineering.**

> *"Code is what we write. Context is how we survive it."*

Loom-Context is the **nervous system** for your project. Just as the human brain doesn't reprocess all of reality every instant — it uses working memory, learned patterns, and cognitive shortcuts — Loom builds an **architectural context layer** that AI agents read as their long-term memory about your project.

Without Loom, every AI session starts from zero. With Loom, the AI **remembers** your architecture, your rules, and your intent.

```
pip install loom-context
cd your-project/
loom init .
```

~1 second. 7 files. Complete architectural context for any LLM.

---

## How It Works

```
Your Project          Loom Engine              AI Agent
─────────────    ──────────────────    ──────────────────
src/             → StructureScanner   → architecture.md
package.json     → DependencyScanner  → stack.json
*.ts, *.py       → CodeScanner        → naming.md
docs/            → DocsScanner        → plans-summary.md
                                      → index.json (entry point)
                                      → rules.json (auditable)
                                      → directory-map.md
```

1. **Scans** your project: structure, dependencies, code patterns, documentation
2. **Detects** architecture (Clean Architecture, Hexagonal, MVC, feature-based), naming conventions (PascalCase, I-prefix, use-prefix, suffixes), and full technology stack
3. **Generates** `.context/` — 7 structured files that any AI agent can consume in seconds
4. **Audits** code against detected rules: naming violations, layer boundary violations

## The Brain Analogy

Loom operates like the layers of the human brain:

| Brain Layer | Loom Component | Function |
|-------------|---------------|----------|
| Sensory System | Scanners | Perceives the project as-is |
| Working Memory | `.context/` (7 files) | What the AI holds "active" |
| Prefrontal Cortex | PromptGenerator | Compiles context into decisions |
| Immune System | Auditors | Detects anomalies proactively |
| Blood-Brain Barrier | Security Filter | Blocks secrets and noise |

Read the full analogy: [docs/guides/philosophy.md](docs/guides/philosophy.md)

## Commands

```bash
loom init .                    # Full scan + generate .context/
loom scan .                    # Re-scan and update
loom prompt . --stdout         # Generate master AI prompt
loom audit .                   # Validate against rules
loom plan .                    # Summarize project docs/plans
loom watch . --interval 60     # Continuous mode
```

## What It Generates

```
.context/
├── index.json          ← AI reads this FIRST (entry point)
├── architecture.md     ← Patterns, layers, boundaries
├── naming.md           ← Naming conventions with real examples
├── directory-map.md    ← Annotated directory tree
├── stack.json          ← Dependencies categorized by purpose
├── rules.json          ← Machine-readable rules for auditing
└── plans-summary.md    ← Summary of existing project plans
```

**Progressive consumption:**
- `index.json` quick_rules → 30 seconds of context
- `+ architecture.md + naming.md` → 2 minutes
- `+ directory-map.md + stack.json` → complete picture

## Detected Patterns

| What | How |
|------|-----|
| **Project type** | Marker files: `app.config.js` → Expo, `next.config.js` → Next.js, `pyproject.toml` → Python, etc. |
| **Architecture** | Directory analysis: `domain/ + infrastructure/ + presentation/` → Clean Architecture |
| **Naming** | Samples ~100 files: PascalCase, camelCase, I-prefix interfaces, use-prefix hooks |
| **Stack** | Parses package.json/pyproject.toml, categorizes 130+ known packages |
| **Docs** | Indexes all .md files, extracts titles, sections, plan status |
| **Boundaries** | Infers layer rules: "domain MUST NOT import from infrastructure" |

## Supported Project Types

React Native / Expo, React / Next.js, Angular, Vue / Nuxt, Svelte, Node.js, Python, Rust, Go, Java, and more.

## Security

Three layers of protection:

1. **`.gitignore` respect** — if Git ignores it, Loom ignores it
2. **`.contextignore`** — additional exclusions (same format as .gitignore)
3. **Hardcoded secrets** — `.env`, `*.pem`, `*.key`, `credentials*` are ALWAYS excluded

**Output is metadata only.** Zero source code in `.context/`. Never.

## Documentation

### Conceptual
| Document | Description |
|----------|-------------|
| [Philosophy & Brain Analogy](docs/guides/philosophy.md) | Why Loom exists, the nervous system metaphor |
| [Architecture](docs/architecture/overview.md) | Internal design: pipeline, components, patterns |
| [Design Patterns](docs/architecture/patterns.md) | Clean Arch, Hexagonal, MVC — detection algorithms |
| [References](docs/REFERENCES.md) | Scientific foundations, academic sources, citations |

### Technical
| Document | Description |
|----------|-------------|
| [Quick Start](docs/guides/quickstart.md) | Install, first scan, use with AI |
| [Directory Structure](docs/architecture/directory-structure.md) | Full annotated project anatomy |
| [CLI Reference](docs/guides/cli-reference.md) | All 6 commands with examples |
| [Context Output](docs/guides/context-output.md) | The 7 .context/ files explained |
| [Security](docs/guides/security.md) | Three-layer protection model |
| [Best Practices](docs/guides/best-practices.md) | Workflows for individuals, teams, and AI |

### Diagrams
| Document | Description |
|----------|-------------|
| [Data Flow](docs/diagrams/data-flow.md) | Information flow from code to AI prompt |
| [Component Map](docs/diagrams/component-map.md) | Component relationships and extensibility |

Full index: [docs/INDEX.md](docs/INDEX.md)

## Theoretical Foundations

Loom's design is grounded in:

- **Cognitive Science:** Baddeley's Working Memory model (1974), Miller's "Magical Number Seven" (1956), Sweller's Cognitive Load Theory (1988) — justifying progressive context compression
- **Software Architecture:** Martin's Clean Architecture (2017), Cockburn's Hexagonal Architecture (2005), Evans' Domain-Driven Design (2003) — the patterns Loom detects and enforces
- **AI-Assisted Engineering:** Fan et al. (2023) on LLMs for SE, Vaithilingam et al. (2022) on context as the #1 factor for code generation quality

Full references with citations: [docs/REFERENCES.md](docs/REFERENCES.md)

## Development

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Test
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/loom_context/

# Build for PyPI
python3 -m build
twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guide, git conventions, and publishing instructions.

## Requirements

- Python >= 3.9
- 4 runtime dependencies: `click`, `rich`, `pathspec`, `jinja2`
- Zero configuration needed — just `loom init .`

## License

MIT — J. Adrian Ruiz C.
