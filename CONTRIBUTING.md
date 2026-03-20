---
type: contributing
---

# Contributing to Loom-Context

Thanks for your interest in contributing! This guide covers everything you need to set up your development environment, follow our conventions, and submit quality contributions.

Before contributing, also review:

- `CODE_OF_CONDUCT.md` for collaboration expectations
- `SECURITY.md` for private vulnerability reporting

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style & Linting](#code-style--linting)
- [Testing](#testing)
- [Git Conventions](#git-conventions)
- [Pull Request Process](#pull-request-process)
- [Publishing to PyPI](#publishing-to-pypi)
- [Architecture Decisions](#architecture-decisions)

---

## Development Setup

### Prerequisites

- Python >= 3.9
- pip (any version) or [uv](https://docs.astral.sh/uv/) (recommended for speed)
- Git

### Clone and Install

```bash
# Clone
git clone https://github.com/Basal-Research-Group/Loom-Context.git
cd Loom-Context

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"

# Verify
loom --version
# loom, version 0.1.0

pytest
# 78 passed
```

### Alternative: Install Without Virtual Environment

```bash
pip install -e ".[dev]"
```

> **Note:** If `loom` is not on your PATH after install, the binary is likely in `~/.local/bin/` (Linux) or `~/Library/Python/3.x/bin/` (macOS). Add it to your PATH.

---

## Project Structure

```
Loom-Context/
├── src/loom_context/           # Main package
│   ├── __init__.py             # Version
│   ├── cli.py                  # Click CLI (commands)
│   ├── engine.py               # Central orchestrator
│   ├── config.py               # Configuration (.context/ + .loom/)
│   ├── git.py                  # Shared git utilities
│   ├── session.py              # Session logger (.loom/sessions.jsonl)
│   ├── status.py               # Project health dashboard
│   ├── findings.py             # Audit persistence (.loom/inconsistencies.json)
│   ├── decisions.py            # Decision records (.loom/decisions.jsonl)
│   ├── mutations.py            # Context change log (.loom/mutations.jsonl)
│   ├── scanners/               # Project analysis
│   ├── generators/             # .context/ output
│   ├── auditors/               # Rule validation
│   ├── security/               # File filtering
│   └── templates/              # Jinja2 templates
├── tests/                      # Pytest tests (78+)
│   ├── conftest.py             # Fixtures (tmp_project)
│   └── test_cli.py             # All tests
├── docs/
│   ├── guides/                 # User-facing guides
│   └── plans/                  # Delivery plans by version
│       ├── scope.md
│       ├── format.md
│       ├── roadmap-v0.2-v0.4.md
│       └── v0.X.Y/delivery.md
├── pyproject.toml              # Package config
├── CONTRIBUTING.md             # This file
├── CHANGELOG.md                # Release history
├── README.md                   # Project readme
└── LICENSE                     # Apache-2.0
```

See [docs/architecture/directory-structure.md](docs/architecture/directory-structure.md) for full annotated structure.

## License and Attribution

By contributing to Loom-Context, you agree that your contributions are submitted
under the Apache License 2.0 used by this repository.

Contributors are credited through Git history, release notes, and
`CONTRIBUTORS.md`. Please use your preferred public Git identity in commits so
that attribution remains accurate.

---

## Code Style & Linting

### Style Rules

- **Python version:** Write code compatible with Python 3.9+
  - Use `from __future__ import annotations` in every module
  - Use `Optional[X]` instead of `X | None` (3.10+ syntax)
  - Use `list[X]` and `dict[X, Y]` with `from __future__ import annotations`
- **Formatting:** Follow PEP 8
  - Line length: 100 characters max
  - Indentation: 4 spaces
  - Imports: grouped (stdlib → third-party → local), alphabetically sorted within groups
- **Type hints:** All public functions must have type annotations
- **Docstrings:** One-line for simple functions, multi-line for complex ones
- **No emojis** in code or output strings (Rich handles visual formatting)

### Recommended Tools

```bash
# Install development tools
pip install ruff mypy

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/loom_context/
```

### Ruff Configuration (add to pyproject.toml if contributing linter setup)

```toml
[tool.ruff]
target-version = "py39"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
```

---

## Testing

### Run Tests

```bash
# All tests
pytest

# Verbose
pytest -v

# Specific test class
pytest tests/test_cli.py::TestEngine

# Specific test
pytest tests/test_cli.py::TestEngine::test_full_init

# With coverage (install pytest-cov first)
pip install pytest-cov
pytest --cov=loom_context --cov-report=term-missing
```

### Test Structure

Tests are in `tests/test_cli.py` organized by component:

| Class | Tests | What it validates |
|-------|-------|-------------------|
| `TestFileFilter` | 5 | Security: excludes node_modules, .git, .env, respects .gitignore |
| `TestStructureScanner` | 3 | Detects architecture, project type, annotations |
| `TestDependencyScanner` | 2 | Parses package.json, categorizes deps |
| `TestCodeScanner` | 2 | Naming detection, import aliases |
| `TestDocsScanner` | 3 | Finds docs, classifies, extracts status |
| `TestEngine` | 3 | Full init, index.json structure, prompt generation |
| `TestCLI` | 10 | All CLI commands work |
| `TestNamingAuditor` | 2 | Interface prefix detection |
| `TestStructureAuditor` | 2 | Layer boundary violations |
| `TestEdgeCases` | 5 | Empty projects, Python, secrets, contextignore |
| `TestSessionLogger` | 6 | Append, read, clear, migration to .loom/ |
| `TestFocusGenerator` | 6 | Task-specific context matching |
| `TestStatusCommand` | 4 | Dashboard, JSON output, sessions |
| `TestLogCommand` | 4 | Session logging via CLI |
| `TestFindingsStore` | 4 | Audit persistence |
| `TestDecisionLog` | 4 | Decision records |
| `TestMutationLog` | 2 | Context change tracking |
| `TestInitWithAudit` | 4 | Audit in init, .loom/ creation |
| `TestEnrichCommand` | 3 | Enrichment pipeline |
| `TestDecideCommand` | 4 | Decision recording via CLI |

### Writing New Tests

Use the `tmp_project` fixture from `conftest.py` — it creates a complete mock project with Clean Architecture structure, package.json, tsconfig.json, AGENTS.md, and docs.

```python
class TestMyFeature:
    def test_something(self, tmp_project: Path) -> None:
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert result["structure"]["project_type"] == "react-native"
```

### Integration Test (Manual)

```bash
# Test against a real complex project
cd /path/to/real-project
loom init .
# Verify .context/ is correct
loom audit .
# Verify violations make sense
loom prompt . --stdout | wc -l
# Verify prompt is reasonable size
```

---

## Git Conventions

### Branch Naming

```
feat/description       # New feature
fix/description        # Bug fix
docs/description       # Documentation only
refactor/description   # Code refactoring
test/description       # Adding tests
chore/description      # Build, CI, tooling
```

Examples:
```
feat/add-git-scanner
fix/false-positive-boundary-check
docs/add-references
refactor/simplify-code-scanner
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `chore` | Build, CI, tooling, dependencies |
| `perf` | Performance improvement |

**Scope** (optional): the component affected (`scanner`, `generator`, `auditor`, `cli`, `security`, `docs`).

**Examples:**
```
feat(scanner): add git history analysis
fix(auditor): false positive on DI wiring imports
docs: add scientific references
refactor(engine): simplify scan result merging
test: add integration tests for Python projects
chore: add ruff linter configuration
```

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **PATCH** (0.1.x): Bug fixes, documentation
- **MINOR** (0.x.0): New features, backward compatible
- **MAJOR** (x.0.0): Breaking changes

Current: `0.1.0` (pre-1.0, API may change between minor versions).

---

## Pull Request Process

Open pull requests with the repository template and keep the validation checklist accurate. If your change is user-facing, update `README.md`, `docs/`, or `CHANGELOG.md` as appropriate.

1. **Fork** the repo and create a branch from `develop` (main triggers PyPI deploy)
2. **Write code** following the style guide above
3. **Add tests** for new functionality
4. **Run tests** locally: `pytest`
5. **Update docs** if your change affects user-facing behavior
6. **Commit** following Conventional Commits
7. **Open PR** against `develop` with:
   - Clear title (Conventional Commits format)
   - Description of what and why
   - Link to related issue if applicable

### PR Checklist

```markdown
- [ ] Tests pass (`pytest`)
- [ ] New functionality has tests
- [ ] Code follows style guide (Python 3.9+ compatible)
- [ ] Documentation updated if needed
- [ ] Commit messages follow Conventional Commits
```

### Review Criteria

- Does it solve the stated problem?
- Is it the simplest solution?
- Are there tests?
- Does it maintain backward compatibility?
- Does it follow existing patterns in the codebase?

---

## Publishing to PyPI

### Option A: Automated via GitHub Actions (Recommended)

The repo includes two workflows in `.github/workflows/`:

**`ci.yml`** — Runs on every push/PR:
- Tests on Python 3.9, 3.10, 3.11, 3.12 across Linux, macOS, Windows
- Ruff lint + format check
- Mypy type checking
- pip-audit security scan
- Build verification

**`pypi-publish.yml`** — Publishes to PyPI:
- Triggered automatically on GitHub Release creation
- Can also be triggered manually via Actions tab

#### Release Workflow

```
1. Update version
   → src/loom_context/__init__.py: __version__ = "0.2.0"

2. Update CHANGELOG.md

3. Commit and push
   → git add -A && git commit -m "chore: bump version to 0.2.0"
   → git push origin main

4. Create GitHub Release
   → gh release create v0.2.0 --title "v0.2.0" --notes "See CHANGELOG.md"

5. Workflow runs automatically:
   build → test-install (6 matrix combos) → publish to PyPI
```

#### GitHub Setup Required

1. Go to repo Settings → Environments
2. Create environment `pypi`:
   - No protection rules needed for now
3. Create environment `testpypi`:
   - For test publishes
4. Go to Settings → Actions → General:
   - Ensure "Allow GitHub Actions to create and approve pull requests" is enabled
5. **Trusted Publisher** (recommended, no API token needed):
   - Go to [pypi.org/manage/project/loom-context/settings/publishing/](https://pypi.org/manage/project/loom-context/settings/publishing/)
   - Add new publisher: GitHub, owner `Basal-Research-Group`, repo `Loom-Context`, workflow `pypi-publish.yml`, environment `pypi`
   - Same for TestPyPI at [test.pypi.org](https://test.pypi.org)

#### Manual Test Publish

```bash
# Via GitHub Actions UI:
# Go to Actions → "Publish to PyPI" → Run workflow → target: testpypi

# Then verify:
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ loom-context
loom --version
```

### Option B: Manual Publish (Local)

```bash
# Install build tools
pip install build twine

# 1. Update version in src/loom_context/__init__.py

# 2. Clean and build
rm -rf dist/ build/ *.egg-info src/*.egg-info
python3 -m build
twine check dist/*

# 3. Test on TestPyPI first
twine upload --repository testpypi dist/*
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ loom-context
loom --version

# 4. Publish to real PyPI
twine upload dist/*
```

### Verify Published Package

```bash
pip install loom-context
loom --version
```

---

## Architecture Decisions

When making significant changes, consider:

1. **Loom must stay fast.** Scanning 700 files should take < 2 seconds.
2. **Loom must stay light.** Minimize dependencies (currently 4).
3. **Security first.** Never expose source code or secrets in output.
4. **Metadata only.** Scanners read file contents to infer patterns, but never persist content.
5. **Auto-resolve.** Don't ask the user questions. Detect patterns and report.
6. **Progressive consumption.** AI can stop at any depth level (quick_rules → full context).

See [docs/architecture/overview.md](docs/architecture/overview.md) for full architecture documentation.

---

## Questions?

Open an issue on [GitHub](https://github.com/Basal-Research-Group/Loom-Context/issues).
