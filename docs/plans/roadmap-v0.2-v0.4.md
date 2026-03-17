---
type: roadmap
versions: ["0.2.0", "0.2.1", "0.2.2", "0.3.0"]
---

# Roadmap v0.2 - v0.4

> Objetivo: evolucionar Loom-Context desde generador global de `.context/` hacia compilador de contexto por tarea, sin perder su nucleo deterministic-first ni convertirlo en un editor de markdown.

## Scope

Loom es un compilador de contexto para proyectos de software. Ver [scope.md](./scope.md) para limites y direccion.

## Estado Actual (2026-03-16)

| Version | Estado | Entregables | Detalle |
|---------|--------|-------------|---------|
| v0.1.0 | Publicado en PyPI | init, scan, prompt, audit, plan, watch, focus, log, status | — |
| v0.2.0 | Completado | .loom/, audit en init, enrich, decide, GitHelper | [archive](./archive/v0.2.0/delivery.md) |
| v0.2.1 | Completado | Contratos tipados, CLI modular, store/, pipeline, frontmatter, Loomy | [archive](./archive/v0.2.1/delivery.md) |
| v0.2.2 | Completado | Bundle, handoff, doctor, compact format | [archive](./archive/v0.2.2/delivery.md) |
| v0.3.0 | Postergado | Embeddings (sin evidencia de necesidad) | [archive](./archive/v0.3.0/delivery.md) |
| v0.4.0 | Completado | Export a 4 agentes + --install | [archive](./archive/v0.4.0/delivery.md) |

### Extras no planificados (implementados durante desarrollo)

- `--compact` format en prompt y bundle (71-89% menos tokens)
- `--top-k` y `--token-budget` en bundle
- `--install` en export (escribe donde el agente lo espera)
- `loom plan` con barras de progreso y badges de frontmatter
- Pipeline architecture detection
- Frontmatter YAML parsing en docs scanner
- Loomy mascot con 8 expresiones
- Compact formatter para output denso sin markdown

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

## v0.3.0 - Export a agentes y watch incremental

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

## Evals y Telemetria Local (post-v0.3.0, pre-AI)

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

### Extra `ai` (futuro, post-v0.3.0)

- sentence-transformers + dependencias

### Regla

El usuario no debe instalar stack pesado si solo quiere init, scan, audit o prompt.

---

## Orden de Implementacion (actualizado)

Alineado con [architecture-hardening-plan.md](./architecture-hardening-plan.md).

| Paso | Version | Que hacer | Estado |
|------|---------|-----------|--------|
| 1-3 | v0.2.0 | .loom/, GitHelper, audit en init, enrich, decide | Completado |
| 4-5 | v0.2.0 | Probado en Akana (674 archivos, 107 violaciones, 0.9s) | Completado |
| 6 | v0.2.1 | Contratos tipados (models.py, ScanResult) | Completado |
| 7 | v0.2.1 | CLI modular (12 comandos), store/ package | Completado |
| 8 | v0.2.1 | Pipeline detection, frontmatter parsing, Loomy | Completado |
| 9 | v0.2.2 | Bundle command con seleccion heuristica | Completado |
| 10 | v0.2.2 | Handoff + doctor | Completado |
| 11 | v0.3.0 | Export + watch incremental | Completado parcial |
| 12 | futuro | Embeddings opcionales (si se necesitan) | No iniciado |

Fase C (pipelines/puertos) postergada hasta que haya 6+ scanners o plugins.

## Definicion de Exito

El roadmap sera correcto si Loom termina haciendo esto mejor que hoy:

- menos contexto, mas relevante
- menor friccion para retomar trabajo
- mejor handoff entre agentes
- sin perder trazabilidad ni depender de servicios externos
