---
type: delivery
version: "0.2.0"
status: in-progress
prerequisite: "0.1.0"
scope: engine, cli, infra
languages: [python]
---

# v0.2.0 — Contexto Vivo y Audit Integrado

> Estado: EN DEVELOP, pendiente pruebas locales y release

## Problema que resuelve

`.context/` era estatico y no evolucionaba con el uso del proyecto. No habia forma de persistir hallazgos, decisiones ni mutaciones. El audit solo se corria manualmente, separado del init.

## Que cambia

### Separacion canonico vs operativo

| Carpeta | Proposito | Reproducible |
|---------|-----------|-------------|
| `.context/` | Contexto derivado del repo | Si, desde git SHA |
| `.loom/` | Estado operativo vivo | No, evoluciona con uso |

### Archivos nuevos en `.loom/`

- `sessions.jsonl` — migrado desde `.context/`
- `inconsistencies.json` — hallazgos del audit persistidos
- `decisions.jsonl` — decision records explicitos
- `mutations.jsonl` — log de cambios al contexto

### Comandos nuevos

| Comando | Proposito |
|---------|-----------|
| `loom enrich .` | Re-audita, refresca `.context/`, persiste findings |
| `loom decide "..." -r "..."` | Registra decision arquitectonica |
| `loom decide --show` | Muestra decisions recientes |

### Cambios a comandos existentes

- `loom init` ahora corre audit no-bloqueante y muestra findings
- `loom log` escribe en `.loom/` en vez de `.context/`
- `loom status` muestra findings, decisions, sessions desde `.loom/`

### Refactor

- `GitHelper` centralizado (antes duplicado en 4 archivos)

## Archivos tocados

### Nuevos (4)

- `src/loom_context/git.py`
- `src/loom_context/findings.py`
- `src/loom_context/decisions.py`
- `src/loom_context/mutations.py`

### Modificados (7)

- `src/loom_context/config.py` — loom_dir + ensure_loom_dir
- `src/loom_context/engine.py` — audit(), enrich(), init con audit
- `src/loom_context/session.py` — migrado a .loom/, usa GitHelper
- `src/loom_context/status.py` — lee desde .loom/
- `src/loom_context/cli.py` — init con audit, enrich, decide
- `tests/test_cli.py` — 22 tests nuevos (78 total)
- `pyproject.toml` — lint exceptions para git.py

## Tests

78 tests, 2.0s, todos pasando.

## Dependencias nuevas

Ninguna.

## Checklist para release

- [ ] probar en proyecto real: `loom init .`, `loom enrich .`, `loom decide`, `loom status .`
- [ ] verificar `.loom/` se genera correctamente
- [ ] verificar migracion de sessions si existia `.context/sessions.jsonl`
- [ ] version bump a 0.2.0
- [ ] actualizar CHANGELOG
- [ ] merge develop → main
- [ ] tag + push → PyPI deploy
