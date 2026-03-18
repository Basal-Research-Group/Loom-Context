.PHONY: test lint format type-check security audit build clean install qa smoke

# Full quality check (run before every commit)
qa: lint format type-check security test
	@echo "\n  ~(^ ^)~ all quality checks passed"

# Individual checks
test:
	python3 -m pytest tests/ -v --tb=short

lint:
	python3 -m ruff check src/ tests/

format:
	python3 -m ruff format --check src/ tests/

type-check:
	python3 -m mypy src/loom_context/ --ignore-missing-imports --disable-error-code=no-any-return --disable-error-code=has-type

# Security scan (bandit + pip-audit)
security:
	python3 -m bandit -c pyproject.toml --recursive src/

# Coverage report
coverage:
	python3 -m pytest tests/ --cov=loom_context --cov-report=term-missing --tb=short

# Dependency audit
audit:
	pip-audit

# Loom self-scan smoke test
smoke:
	loom init .
	loom doctor .
	loom metrics .
	loom bundle "architecture" . --stdout | head -20
	@echo "\n  ~(^ ^)~ smoke test passed"

# Build package
build: qa
	rm -rf dist/ build/
	python3 -m build
	python3 -m twine check dist/*

# Install in dev mode
install:
	pip install -e ".[dev]"

# Clean build artifacts
clean:
	rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
