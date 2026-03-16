# Loom-Context

**Architecture context for AI-assisted engineering.**

Loom-Context scans your repository, infers architecture and conventions, and generates a compact `.context/` directory that AI agents can use as project memory.

It is designed for one specific job:

- understand repo structure
- detect architecture and naming rules
- summarize docs and plans
- generate AI-ready context
- audit basic architectural boundaries

It does **not** send source code anywhere by default, and it does **not** require a hosted AI service to work.

## Install

```bash
pip install loom-context
```

Verify:

```bash
loom --version
```

## Quick Start

```bash
cd your-project/
loom init .
loom prompt . --stdout
```

What happens:

1. Loom scans your project structure, dependencies, code patterns, and docs.
2. Loom generates `.context/` with architecture, naming, stack, rules, and plans summary.
3. You can feed that context to an AI agent or audit the repo against detected rules.

## Core Commands

```bash
loom init .                    # Full scan + generate .context/
loom scan .                    # Re-scan and update .context/
loom prompt . --stdout         # Print master AI prompt
loom prompt . -o prompt.md     # Write prompt to file
loom audit .                   # Validate naming and layer rules
loom plan .                    # Summarize project docs/plans
loom watch . --interval 60     # Refresh context continuously
```

## What Loom Generates

```text
.context/
├── index.json
├── architecture.md
├── naming.md
├── directory-map.md
├── stack.json
├── rules.json
└── plans-summary.md
```

Recommended consumption order:

- `index.json`: fast orientation and quick rules
- `architecture.md` + `naming.md`: coding constraints
- `directory-map.md` + `stack.json`: implementation context
- `plans-summary.md`: docs and roadmap context

## Example Workflow

```bash
pip install loom-context
cd your-project/
loom init .
loom audit .
loom prompt . -o .context/PROMPT.md
```

Then use the generated prompt with your preferred AI tool.

## What It Detects

| Area | Detection |
|------|-----------|
| Project type | Marker files such as `pyproject.toml`, `next.config.js`, `app.config.js` |
| Architecture | Clean Architecture, Hexagonal, MVC, MVVM, feature-based, layered |
| Naming | PascalCase, camelCase, kebab-case, snake_case, prefixes, suffixes |
| Stack | Packages from `package.json`, `pyproject.toml`, `requirements.txt` |
| Docs | Markdown files, headings, plan status, doc categories |
| Rules | Layer boundaries and naming conventions inferred from the repo |

## Supported Project Types

Loom currently recognizes many common project shapes, including:

- React Native / Expo
- React / Next.js
- Angular
- Vue / Nuxt
- Svelte
- Node.js
- Python
- Rust
- Go
- Java

## Security Model

Loom uses three layers of filtering:

1. respects `.gitignore`
2. respects `.contextignore`
3. always excludes common secret patterns such as `.env`, `*.pem`, `*.key`, and credential files

The generated output is metadata-focused. Loom is designed to avoid copying source code into `.context/`.

## Why Use It

Without Loom:

- each AI session starts from zero
- architecture has to be rediscovered manually
- naming and boundary rules are easy to miss
- project docs stay disconnected from code assistance

With Loom:

- the repo becomes queryable context
- AI gets a stable architecture snapshot
- rule violations can be caught earlier
- docs and plans become part of the working context

## Current Scope

Loom is already useful for early adoption, but it is not pretending to be finished.

Current strengths:

- repository scanning
- architecture and naming inference
- prompt generation
- basic audits
- docs and plan summarization

Current limitations:

- no task-specific bundles yet
- no local retrieval/reranking yet
- `watch` is interval-based, not event-driven
- validation still needs more real-world repositories

## Documentation

### Guides

- [Quick Start](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/quickstart.md)
- [CLI Reference](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/cli-reference.md)
- [Context Output](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/context-output.md)
- [Security](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/security.md)
- [Best Practices](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/best-practices.md)

### Architecture

- [Philosophy and Brain Analogy](https://github.com/jadruiz/Loom-Context/blob/main/docs/guides/philosophy.md)
- [Architecture Overview](https://github.com/jadruiz/Loom-Context/blob/main/docs/architecture/overview.md)
- [Design Patterns](https://github.com/jadruiz/Loom-Context/blob/main/docs/architecture/patterns.md)
- [Directory Structure](https://github.com/jadruiz/Loom-Context/blob/main/docs/architecture/directory-structure.md)

### Planning

- [Documentation Index](https://github.com/jadruiz/Loom-Context/blob/main/docs/INDEX.md)
- [Roadmap v0.2 - v0.4](https://github.com/jadruiz/Loom-Context/blob/main/docs/plans/roadmap-v0.2-v0.4.md)
- [Local AI Integration Strategy](https://github.com/jadruiz/Loom-Context/blob/main/docs/plans/ai-integration-strategy.md)
- [Release Pilot Plan](https://github.com/jadruiz/Loom-Context/blob/main/docs/plans/release-pilot-plan.md)
- [Release 0.1.1 Plan](https://github.com/jadruiz/Loom-Context/blob/main/docs/plans/release-0.1.1-plan.md)

### References and Diagrams

- [Scientific References](https://github.com/jadruiz/Loom-Context/blob/main/docs/REFERENCES.md)
- [Data Flow](https://github.com/jadruiz/Loom-Context/blob/main/docs/diagrams/data-flow.md)
- [Component Map](https://github.com/jadruiz/Loom-Context/blob/main/docs/diagrams/component-map.md)

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest -v --tb=short
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/loom_context/
python3 -m build
python3 -m twine check dist/*
```

Contributor guide:

- [CONTRIBUTING.md](https://github.com/jadruiz/Loom-Context/blob/main/CONTRIBUTING.md)
- [SECURITY.md](https://github.com/jadruiz/Loom-Context/blob/main/SECURITY.md)
- [CODE_OF_CONDUCT.md](https://github.com/jadruiz/Loom-Context/blob/main/CODE_OF_CONDUCT.md)

Community workflow:

- bug reports and feature requests use the GitHub issue templates
- pull requests use the repository PR template
- security reports should be sent privately as described in `SECURITY.md`

## Requirements

- Python 3.9+
- runtime dependencies: `click`, `rich`, `pathspec`, `jinja2`

## License

MIT
