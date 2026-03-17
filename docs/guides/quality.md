---
type: guide
audience: contributor
---

# 🛡️ Calidad, Seguridad y Herramientas

## TL;DR

Loom usa 7 capas de calidad que se ejecutan automaticamente antes de cada commit. Si algo falla, el codigo no entra. Cobertura minima: 80%. Vulnerabilidades: 0 en dependencias directas.

---

## 🔧 Herramientas Instaladas

| Herramienta | Que hace | Cuando se ejecuta |
|-------------|----------|-------------------|
| `pytest` | Tests unitarios e integracion | Pre-push, CI |
| `pytest-cov` | Cobertura de codigo | CI, manual |
| `ruff check` | Lint (50+ reglas) | Pre-commit |
| `ruff format` | Formato consistente | Pre-commit |
| `mypy` | Type checking estatico | Pre-commit |
| `pre-commit` | Hooks automaticos | Cada commit |
| `pip-audit` | Vulnerabilidades en deps | CI, manual |
| `twine check` | Validacion de paquete | Pre-release |
| `loom doctor` | Salud del setup de Loom | Manual |
| `loom audit` | Reglas de arquitectura | Manual, CI |

---

## 🔄 Flujo de Calidad

### Automatico (pre-commit hooks)

Cada commit pasa por estos checks:

```
1. trailing-whitespace     ← limpieza basica
2. end-of-file-fixer       ← newline al final
3. check-yaml/json/toml    ← syntax valida
4. check-added-large-files ← max 500KB
5. check-merge-conflict    ← sin marcadores de conflicto
6. detect-private-key      ← bloquea keys privadas
7. check-ast               ← Python syntax valida
8. ruff check --fix        ← lint + auto-fix
9. ruff format             ← formato consistente
10. mypy                   ← type safety
11. conventional-pre-commit ← formato de commit message
```

### Manual (antes de release)

```bash
# Tests completos
pytest -v --tb=short

# Cobertura
pytest --cov=loom_context --cov-report=term-missing

# Seguridad de dependencias
pip-audit

# Build + verificacion
python3 -m build && twine check dist/*

# Install en venv limpio
python3 -m venv /tmp/loom-qa
source /tmp/loom-qa/bin/activate
pip install dist/loom_context-*.whl
loom --version && loom doctor .
deactivate && rm -rf /tmp/loom-qa
```

---

## 📊 Metricas Actuales

| Metrica | Valor | Minimo |
|---------|-------|--------|
| Tests | 118 | — |
| Cobertura total | 88% | 80% |
| Lint errors | 0 | 0 |
| Format diffs | 0 | 0 |
| mypy errors | 0 | 0 |
| Vulnerabilidades (deps directas) | 0 | 0 |
| Build (wheel+sdist) | PASSED | PASSED |
| Doctor checks | 10/10 | — |

### Cobertura por modulo

| Modulo | Cobertura | Notas |
|--------|-----------|-------|
| models.py | 100% | Contratos tipados |
| store/* | 82-95% | Sessions, findings, decisions, mutations |
| scanners/* | 83-100% | deps.py mejorado de 48% a 83% |
| generators/* | 84-100% | focus.py tiene branches de matching |
| selector/* | 86-94% | Heuristic strategy, bundle, compact |
| exporters/* | 89-100% | 4 adapters |
| cli/commands/* | 72-100% | Rendering con Rich |
| security/* | 76% | Edge cases de .contextignore |

---

## 🔒 Seguridad

### Dependencias

Solo 4 dependencias runtime, todas auditadas:

| Paquete | Version | Vulnerabilidades |
|---------|---------|-----------------|
| click | 8.1.x | 0 |
| rich | 14.x | 0 |
| pathspec | 1.0.x | 0 |
| jinja2 | 3.1.x | 0 |

### Codigo

| Proteccion | Como se verifica |
|-----------|-----------------|
| No secrets en output | `FileFilter` con 3 capas, tests `TestEdgeCases` |
| No source code en .context/ | Scanners solo extraen metadata |
| Private keys bloqueadas | Pre-commit hook `detect-private-key` |
| No large files accidentales | Pre-commit hook `check-added-large-files` |
| .loom/ en .gitignore | `loom doctor` verifica |

---

## 🧪 Como Agregar Tests

### Convencion

```python
class TestNuevoModulo:
    def test_caso_basico(self, tmp_project: Path) -> None:
        """Descripcion clara de que se prueba."""
        engine = LoomEngine(tmp_project)
        result = engine.scan()
        assert result.structure.project_type in {"react-native", "react"}
```

### Fixture disponible

`tmp_project` en `conftest.py` crea un proyecto mock con:
- Clean Architecture (domain/, infrastructure/, presentation/, core/)
- package.json (React, Zustand, Jest, TypeScript)
- tsconfig.json con path aliases
- AGENTS.md, docs/, .gitignore

### Ejecutar tests especificos

```bash
pytest tests/test_cli.py::TestScanResult              # una clase
pytest tests/test_cli.py::TestScanResult::test_frozen  # un test
pytest -k "bundle"                                      # por nombre
pytest --cov=loom_context.scanners.deps                # cobertura de un modulo
```

---

## ⚙️ Configuracion de Ruff

Reglas activas (en `pyproject.toml`):

| Grupo | Que verifica |
|-------|-------------|
| E, W | Errores y warnings PEP 8 |
| F | PyFlakes (imports no usados, variables) |
| I | Isort (orden de imports) |
| N | Naming conventions PEP 8 |
| UP | Pyupgrade (syntax moderna) |
| B | Bugbear (bugs comunes) |
| SIM | Simplificacion de codigo |
| S | Bandit (seguridad) |
| C4 | Comprehensions |
| DTZ | Datetime timezone-aware |
| RET | Return statements |
| PTH | Pathlib vs os.path |
| ERA | Commented-out code |
| RUF | Ruff-specific rules |

---

## 🚀 Setup para Nuevos Contribuidores

```bash
# 1. Clonar y setup
git clone https://github.com/jadruiz/Loom-Context.git
cd Loom-Context
pip install -e ".[dev]"

# 2. Instalar pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg

# 3. Verificar todo
pytest
ruff check src/ tests/
mypy src/loom_context/ --ignore-missing-imports
loom doctor .

# 4. Listo para desarrollar
```

---

*Siguiente: [🚀 Quickstart →](./quickstart.md)*
