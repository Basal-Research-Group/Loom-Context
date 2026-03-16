# Roadmap v0.2 - v0.4

> Objetivo: evolucionar Loom-Context desde generador global de `.context/` hacia compilador de contexto por tarea, sin perder su nucleo deterministic-first ni convertirlo en un editor de markdown.

## Estado Actual (2026-03-16)

| Version | Estado | Entregables |
|---------|--------|-------------|
| v0.1.0 | Publicado en PyPI | init, scan, prompt, audit, plan, watch, focus, log, status |
| v0.2.0 | En develop, pendiente release | .loom/, audit en init, enrich, decide, GitHelper |
| v0.2.1 | Planificado | Contratos tipados + modularizacion CLI |
| v0.2.2 | Planificado | Bundles + manifests + handoff |
| v0.3.0 | Planificado | Retrieval local opcional (embeddings) |
| v0.4.0 | Planificado | Export a agentes + watch incremental |

---

## Principios de Producto

- Loom sigue siendo analisis automatico del repo
- `.context/` sigue siendo el output canonico
- `.loom/` es estado operativo, no fuente de verdad
- la IA es una capa opcional de seleccion y sintesis
- todos los outputs deben poder trazarse a un `git SHA`
- el sistema debe seguir funcionando offline
- el modo sin modelo debe ser util por si mismo

---

## v0.2.0 - Contexto vivo y audit integrado (EN DEVELOP)

### Meta

Separar contexto canonico de estado operativo. Detectar inconsistencias desde el primer init.

### Entregables completados

- [x] `.loom/` como directorio de estado vivo
- [x] `FindingsStore` → `.loom/inconsistencies.json`
- [x] `DecisionLog` → `.loom/decisions.jsonl`
- [x] `MutationLog` → `.loom/mutations.jsonl`
- [x] `SessionLogger` migrado a `.loom/`
- [x] `GitHelper` compartido (DRY)
- [x] `engine.audit()` integrado en `init()`
- [x] `engine.enrich()` pipeline determinista
- [x] `loom enrich` comando CLI
- [x] `loom decide` comando CLI
- [x] `status` muestra findings, decisions, sessions desde `.loom/`
- [x] 22 tests nuevos (78 total)

### Pendiente para release

- [ ] pruebas locales en proyecto real
- [ ] version bump a 0.2.0
- [ ] CHANGELOG actualizado
- [ ] merge a main → deploy a PyPI

---

## v0.2.1 - Contratos tipados y CLI modular

### Meta

Eliminar `dict[str, Any]` como contrato entre capas. Preparar la base para bundles.

### Entregables

- [ ] `ScanResult`, `StructureFacts`, `DependencyInfo`, `CodeAnalysis`, `DocsInventory` (dataclasses)
- [ ] scanners devuelven objetos tipados
- [ ] `ScanResult.to_dict()` para compatibilidad
- [ ] modularizacion CLI: un archivo por comando
- [ ] `mypy --strict` pasa en modelos

### Por que antes de bundles

Los bundles necesitan filtrar y seleccionar desde `ScanResult`. Si el contrato es `dict[str, Any]`, cada nuevo selector va a inventar sus propias llaves. Con contratos tipados, los bundles se construyen sobre una base estable.

### Criterios de salida

- scanners devuelven dataclasses, no dicts
- cli.py < 50 lineas
- 0 regresiones en tests
- mypy pasa sin errores en domain/

---

## v0.2.2 - Bundles, manifests y handoff

### Meta

Introducir "unidad de contexto por tarea" sin modelos locales.

### Entregables de CLI

- [ ] `loom bundle "<task>"`
- [ ] `loom handoff "<task>"`
- [ ] `loom doctor`

### Entregables de output

- [ ] `.context/bundles/<slug>/bundle.md`
- [ ] `.context/bundles/<slug>/manifest.json`
- [ ] `.context/bundles/<slug>/sources.json`
- [ ] `.context/handoffs/<slug>.md`

### Contenido de manifest.json

- [ ] task, slug, git_sha, generated_at, loom_version
- [ ] selection_strategy, included_files, included_docs, included_rules
- [ ] warnings

### Heuristicas iniciales

- coincidencia lexical con nombres de archivos
- coincidencia con nombres de directorios
- proximidad con reglas de arquitectura
- documentos clasificados como plan, architecture, specification
- archivos importados desde el area afectada
- boost a archivos bajo src/ y docs cercanos al tema

### Alcance tecnico

- nuevo paquete `selector/`
- `strategies/heuristic.py`
- `bundle.py`
- `manifest.py`
- tests especificos para seleccion y manifests

### Criterios de salida

- bundle menor que el prompt global
- reproducible con el mismo git SHA
- sin regresiones
- tests cubriendo proyectos vacios y con docs

---

## v0.3.0 - Retrieval local opcional

### Meta

Mejorar precision de seleccion con embeddings locales. Fallback a heuristicas si no hay modelo.

### Prerequisitos

- contratos tipados (v0.2.1)
- bundles heuristicos funcionando (v0.2.2)
- evidencia de que heuristicas no alcanzan

### Entregables

- [ ] `loom bundle "<task>" --ai off|local`
- [ ] `loom bundle "<task>" --top-k N`
- [ ] `loom bundle "<task>" --token-budget N`
- [ ] `selector/strategies/hybrid.py`
- [ ] `infrastructure/ai/embeddings.py`
- [ ] cache local de embeddings en `.loom/cache/`
- [ ] invalidacion incremental

### Modelos candidatos

- `sentence-transformers/all-MiniLM-L6-v2` (MVP ligero)
- `BAAI/bge-m3` (mejor retrieval, multilingue)

### Packaging

- extra opcional: `pip install loom-context[ai]`
- paquete base sigue con 4 deps

### Criterios de salida

- mejora medible de precision@k vs heuristico
- `--ai off` sigue funcionando
- tiempo aceptable para proyectos medianos

---

## v0.4.0 - Export a agentes y watch incremental

### Meta

Reducir friccion de adopcion diaria.

### Entregables

- [ ] `loom export --agent codex|cursor|generic`
- [ ] `loom workspace init`
- [ ] `loom watch --events`
- [ ] invalidacion de bundles stale
- [ ] snippets listos para agentes comunes

### Criterios de salida

- export a por lo menos 2 agentes
- watch mas eficiente que polling
- workspace util pero no requerido

---

## Evals y Telemetria Local (pre v0.3.0)

### Dataset minimo

- [ ] 10 tareas reales
- [ ] archivos esperados por tarea
- [ ] docs esperados por tarea
- [ ] reglas esperadas por tarea

### Metricas

- [ ] precision@k
- [ ] recall@k
- [ ] tamano del bundle
- [ ] tiempo de generacion

### Regla

No introducir fine-tuning antes de tener baseline medido.

---

## Dependencias y Packaging

### Core (siempre)

- click, rich, pathspec, jinja2

### Extra `ai` (v0.3.0+)

- sentence-transformers + dependencias

### Regla

El usuario no debe instalar stack pesado si solo quiere init, scan, audit o prompt.

---

## Orden de Implementacion (actualizado)

```
HECHO:
  1. separacion .context/ vs .loom/
  2. GitHelper compartido
  3. audit en init + enrich + decide
  4. 78 tests

SIGUIENTE:
  5. pruebas locales v0.2.0 → release
  6. contratos tipados (v0.2.1)
  7. modularizacion CLI (v0.2.1)
  8. bundles + manifests (v0.2.2)
  9. evals baseline
  10. embeddings locales (v0.3.0)
  11. export + watch (v0.4.0)
```

## Definicion de Exito

El roadmap sera correcto si Loom termina haciendo esto mejor que hoy:

- menos contexto, mas relevante
- menor friccion para retomar trabajo
- mejor handoff entre agentes
- sin perder trazabilidad ni depender de servicios externos
