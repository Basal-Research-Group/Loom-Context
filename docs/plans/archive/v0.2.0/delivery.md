---
type: delivery
version: "0.2.0"
status: archived
prerequisite: "0.1.0"
scope: engine, cli, infra
languages: [python]
patterns: [template-method, append-only-log, snapshot, facade]
progress: 12/12
---

# v0.2.0 — Contexto Vivo y Audit Integrado

## TL;DR

Separa contexto canonico (`.context/`) de estado operativo (`.loom/`). Integra audit en init para detectar inconsistencias desde el primer contacto. Agrega `enrich` y `decide` para que el contexto evolucione con el proyecto.

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Que cambia](#que-cambia)
- [Patrones de diseno](#patrones-de-diseno)
- [Estructura de archivos](#estructura-de-archivos)
- [Entregables](#entregables)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

`.context/` era una foto estatica que no evolucionaba. No habia donde persistir hallazgos ni decisiones. El audit se corria manualmente, separado del init. Las sessions vivian en `.context/`, mezclando estado operativo con contexto canonico.

## Analogia

**Antes:** Loom era como un fotografo que toma una foto y se va. Si quieres otra foto, tienes que llamarlo de nuevo.

**Ahora:** Loom es como un fotografo que ademas tiene un cuaderno de notas. Toma la foto (`.context/`), pero tambien anota observaciones, decisiones y cambios (`.loom/`). La proxima vez que vuelve, sabe que cambio.

- `.context/` = la foto (reproducible, derivada del repo)
- `.loom/` = el cuaderno de notas (vivo, evoluciona con uso)

---

## Que cambia

### Separacion canonico vs operativo

| Carpeta | Proposito | Reproducible | Analogia |
|---------|-----------|-------------|----------|
| `.context/` | Contexto derivado del repo | Si, desde git SHA | La foto |
| `.loom/` | Estado operativo vivo | No, evoluciona con uso | El cuaderno |

### Archivos nuevos en `.loom/`

| Archivo | Contenido | Formato |
|---------|-----------|---------|
| `sessions.jsonl` | Historial de sesiones (migrado) | JSONL append-only |
| `inconsistencies.json` | Hallazgos del audit | JSON snapshot |
| `decisions.jsonl` | Decision records explicitos | JSONL append-only |
| `mutations.jsonl` | Log de cambios al contexto | JSONL append-only |

### Comandos nuevos

| Comando | Proposito | Analogia |
|---------|-----------|----------|
| `loom enrich .` | Re-audita + refresca + persiste | "Tomar nueva foto y anotar cambios" |
| `loom decide "..." -r "..."` | Registrar decision | "Anotar en el cuaderno por que se tomo esta decision" |
| `loom decide --show` | Ver decisions recientes | "Revisar el cuaderno" |

### Cambios a comandos existentes

- `loom init` corre audit (no bloqueante) y muestra findings
- `loom log` escribe en `.loom/` en vez de `.context/`
- `loom status` muestra findings, decisions, sessions desde `.loom/`

---

## Patrones de diseno

| Patron | Donde se usa | Por que |
|--------|-------------|---------|
| **Template Method** | `engine.init()`: scan → generate → audit → persist | La secuencia es fija, los pasos pueden cambiar |
| **Append-only log** | sessions, decisions, mutations (JSONL) | Trazabilidad completa sin conflictos de escritura |
| **Snapshot** | `inconsistencies.json` | El ultimo audit sobreescribe el anterior — solo importa el estado actual |
| **Facade** | `GitHelper` | Un punto de acceso para toda la logica git, sin duplicar en cada modulo |

---

## Estructura de archivos

### Nuevos (4)

```
src/loom_context/
  git.py                  # GitHelper: facade para comandos git
  findings.py             # FindingsStore: snapshot de audit
  decisions.py            # DecisionLog: append-only JSONL
  mutations.py            # MutationLog: append-only JSONL
```

### Modificados (7)

```
src/loom_context/
  config.py               # + loom_dir, ensure_loom_dir()
  engine.py               # + audit(), enrich(), init con audit
  session.py              # migrado a .loom/, usa GitHelper
  status.py               # lee desde .loom/
  cli.py                  # init con audit, + enrich, + decide
tests/
  test_cli.py             # + 22 tests (78 total)
pyproject.toml            # lint exceptions para git.py
```

---

## Entregables

- [x] `.loom/` como directorio de estado vivo
- [x] `FindingsStore` → `.loom/inconsistencies.json`
- [x] `DecisionLog` → `.loom/decisions.jsonl`
- [x] `MutationLog` → `.loom/mutations.jsonl`
- [x] `SessionLogger` migrado a `.loom/`
- [x] `GitHelper` compartido (Facade pattern)
- [x] `engine.audit()` integrado en `init()`
- [x] `engine.enrich()` pipeline determinista
- [x] `loom enrich` comando CLI
- [x] `loom decide` comando CLI
- [x] `status` muestra findings, decisions, sessions desde `.loom/`
- [x] 22 tests nuevos (78 total, 2s)

## Criterios de salida

- [ ] probar en proyecto real: `loom init .`, `loom enrich .`, `loom decide`, `loom status .`
- [ ] verificar `.loom/` se genera correctamente
- [ ] verificar migracion de sessions si existia `.context/sessions.jsonl`
- [ ] version bump a 0.2.0
- [ ] actualizar CHANGELOG
- [ ] merge develop → main
- [ ] tag + push → PyPI deploy

## Dependencias nuevas

Ninguna. Sigue con 4 runtime deps: click, rich, pathspec, jinja2.
