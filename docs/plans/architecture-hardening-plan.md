---
type: architecture
languages: [python]
patterns: [clean-pipeline, clean-architecture]
---

# Plan de Hardening Arquitectonico

> Objetivo: preparar Loom-Context para crecer hacia bundles, handoff, retrieval local y export a agentes sin degradar mantenibilidad, testeabilidad ni claridad del dominio.

## Estado (actualizado 2026-03-16)

- v0.1.0 publicado en PyPI
- v0.2.0 en develop: .loom/ live state, audit en init, enrich, decide
- 78 tests pasando en 2s
- 4 dependencias runtime (click, rich, pathspec, jinja2)
- GitHelper extraido (DRY)

### Ya completado

- [x] separacion `.context/` (canonico) vs `.loom/` (operativo)
- [x] GitHelper compartido para metadata git
- [x] audit integrado en init (no bloqueante)
- [x] findings, decisions, mutations persistidos
- [x] session migrado de `.context/` a `.loom/`

### Pendiente

- [ ] contratos tipados (Fase A)
- [ ] modularizacion del CLI (Fase C)
- [ ] pipelines y puertos (Fase B)
- [ ] seleccion y AI opcional (Fase E)

---

## Principios de Diseno

### 1. Contratos antes que diccionarios

Los datos que cruzan boundaries deben tener forma explicita:

- `ScanResult`
- `StructureFacts`
- `DependencyInfo`
- `DocsInventory`
- `CodeAnalysis`
- `AuditFindings` (ya existe)
- `BundleManifest` (futuro)
- `SelectionCandidate` (futuro)

Usar:

- `dataclass(frozen=True)` para entidades y value objects
- `TypedDict` solo en bordes de serializacion

### 2. Composicion por capacidades

El sistema debe crecer agregando capacidades, no editando un archivo central para todo.

Patrones recomendados:

- Registry para scanners, generators y exporters
- Strategy para seleccion, ranking y budget
- Factory para construir pipelines segun comando y flags
- Template Method solo donde la secuencia sea estable

### 3. Separacion de outputs (COMPLETADO)

- `.context/` = output canonico y reproducible
- `.loom/` = estado operativo (sessions, findings, decisions, mutations)
- `context/` = workspace humano opcional (futuro)

### 4. Casos de uso explicitos

La logica de aplicacion debe vivir en servicios, no en el CLI:

- `scan_project`
- `generate_context`
- `run_audit` (parcialmente en engine.py)
- `enrich_context` (parcialmente en engine.py)
- `build_bundle` (futuro)
- `build_handoff` (futuro)
- `export_agent_payload` (futuro)

### 5. Testeabilidad por seams

Cada componente debe poder probarse sin CLI, sin FS real complejo y sin dependencias opcionales instaladas.

---

## Arquitectura Actual (v0.2.0)

```text
src/loom_context/
  git.py                 # utilidad compartida (NEW v0.2)
  config.py              # configuracion + loom_dir (UPDATED v0.2)
  engine.py              # orquestador: scan + generate + audit + enrich
  session.py             # .loom/sessions.jsonl (MIGRATED v0.2)
  status.py              # dashboard desde .context/ + .loom/
  findings.py            # .loom/inconsistencies.json (NEW v0.2)
  decisions.py           # .loom/decisions.jsonl (NEW v0.2)
  mutations.py           # .loom/mutations.jsonl (NEW v0.2)
  cli.py                 # Click commands (550+ lines)
  security/
    filter.py            # 3-layer file filtering
  scanners/
    base.py              # ABC
    structure.py          # project type, architecture, tree
    deps.py              # dependencies + categorization
    code.py              # naming conventions
    docs.py              # documentation index
  generators/
    index.py             # index.json
    context.py           # .context/ files via Jinja2
    prompt.py            # master AI prompt
    focus.py             # task-specific context
  auditors/
    naming.py            # naming conventions
    structure.py         # layer boundaries
  templates/
    *.md.j2              # Jinja2 templates
```

## Arquitectura Objetivo (post-hardening)

```text
src/loom_context/
  cli/
    commands/             # un archivo por comando
  domain/
    models/               # dataclasses tipados (ScanResult, etc.)
    ports/                # interfaces (scanner, generator, store)
  application/
    use_cases/            # scan_project, generate_context, etc.
  infrastructure/
    scanners/             # implementaciones concretas
    generators/           # implementaciones concretas
    auditors/             # implementaciones concretas
    storage/              # .loom/ stores
    ai/                   # embeddings, ranking (futuro)
  shared/
    git.py                # GitHelper
    config.py             # LoomConfig
    security/             # FileFilter
```

---

## Fase A - Contratos tipados (PRIORIDAD ACTUAL)

### Objetivo

Eliminar `dict[str, Any]` como contrato entre capas. Hacer que mypy detecte errores antes de runtime.

### Entregables

1. `domain/models/scan.py`:

```python
@dataclass(frozen=True)
class StructureFacts:
    project_type: str
    architecture: list[str]
    src_root: str
    directory_tree: dict[str, Any]
    layer_boundaries: dict[str, Any]
    total_files: int
    project_name: str = ""

@dataclass(frozen=True)
class DependencyInfo:
    package_manager: str
    dependencies: list[Dependency]
    stack_summary: dict[str, list[str]]

@dataclass(frozen=True)
class CodeAnalysis:
    file_naming: dict[str, Any]
    code_naming: dict[str, Any]
    suffix_patterns: list[dict[str, Any]]
    prefix_patterns: list[dict[str, Any]]
    import_aliases: dict[str, str]
    total_code_files: int

@dataclass(frozen=True)
class DocsInventory:
    docs: list[DocEntry]
    doc_count: int
    agents_md: Optional[str]
    by_type: dict[str, int]

@dataclass(frozen=True)
class ScanResult:
    structure: StructureFacts
    deps: DependencyInfo
    code: CodeAnalysis
    docs: DocsInventory
    scanned_at: str
```

2. Mappers de serializacion en cada scanner:
   - `StructureScanner.scan() -> StructureFacts`
   - `DependencyScanner.scan() -> DependencyInfo`
   - `CodeScanner.scan() -> CodeAnalysis`
   - `DocsScanner.scan() -> DocsInventory`

3. `ScanResult.to_dict()` para compatibilidad con generators existentes.

### Reglas

- el dominio no importa Click, Rich ni Jinja2
- los scanners devuelven objetos tipados, no dicts
- los generators pueden recibir `ScanResult` o `dict` (transicion gradual)
- los tests existentes no deben romperse

### Criterios de salida

- `mypy --strict` pasa en domain/models/
- menos llaves string "magicas" cruzando capas
- serializacion estable para outputs existentes

### Complejidad estimada

- Baja-Media: los datos ya existen como dicts, solo se formalizan
- 0 dependencias nuevas
- Puede hacerse modulo por modulo sin romper nada

---

## Fase B - Modularizacion del CLI

### Objetivo

cli.py tiene 550+ lineas y crece con cada comando. Separar en un archivo por comando.

### Entregables

```text
cli/
  __init__.py            # main group + version
  commands/
    init.py
    scan.py
    prompt.py
    audit.py
    plan.py
    watch.py
    focus.py
    log.py
    status.py
    enrich.py
    decide.py
```

### Regla

Cada comando:

- parsea input
- invoca engine o servicio
- renderiza salida con Rich

No debe contener logica de negocio.

### Criterios de salida

- cli.py < 50 lineas (solo group + imports)
- cada comando < 80 lineas
- tests CLI siguen pasando sin cambios

---

## Fase C - Pipelines y puertos

### Objetivo

Sustituir imports directos en engine.py por composicion.

### Patrones

- Port (ABC) para Scanner, Generator
- Registry de componentes
- Pipeline Builder por comando

### Entregables

- `domain/ports/scanner.py` (ABC)
- `domain/ports/generator.py` (ABC)
- `application/services/pipeline_builder.py`

### Resultado esperado

Agregar un nuevo scanner o generator no debe requerir tocar engine.py.

---

## Fase D - Estado, cache e incrementalidad (PARCIALMENTE COMPLETADA)

### Completado

- `.loom/sessions.jsonl`
- `.loom/inconsistencies.json`
- `.loom/decisions.jsonl`
- `.loom/mutations.jsonl`

### Pendiente

- `.loom/cache/` para hashes y embeddings futuros
- invalidacion incremental
- storage adapter generico

---

## Fase E - Seleccion y AI opcional (futuro, post-v0.3.0)

### Prerequisitos

- contratos tipados (Fase A)
- puertos claros (Fase C)
- bundles funcionando con heuristicas (v0.2.1)

### Patrones

- Strategy para heuristics vs hybrid ranking
- Policy objects para budget, cutoffs e inclusion minima
- Adapter para proveedores de embeddings

---

## Estrategia de Testing

### Piramide

- tests unitarios para domain models, policies y selectors
- tests de integracion para scanners/generators con fixture
- tests de contrato para serializacion de `.context/` y manifests
- tests CLI para humo y wiring

### Cobertura actual (78 tests)

- [x] FileFilter (5)
- [x] Scanners: structure, deps, code, docs (10)
- [x] Engine: init, index, prompt (3)
- [x] CLI: help, version, all commands (10)
- [x] Auditors: naming, structure (4)
- [x] Edge cases: empty, no deps, python, secrets, contextignore (5)
- [x] SessionLogger: append, read, clear, limit, create, migrate (6)
- [x] Focus: matching, empty, no context, max chars, CLI (6)
- [x] Status: not init, after init, json, session log (4)
- [x] Log command: append, show, clear, no args (4)
- [x] FindingsStore: save/load, empty, has_findings, empty violations (4)
- [x] DecisionLog: append/read, empty, clear, limit (4)
- [x] MutationLog: record/read, empty (2)
- [x] InitWithAudit: creates loom, persists findings, records mutation, CLI (4)
- [x] EnrichCommand: basic, no context, persists (3)
- [x] DecideCommand: basic, show, clear, no args (4)

### Pendiente

- [ ] contratos de salida estables (post Fase A)
- [ ] reproducibilidad por SHA
- [ ] invalidacion de cache

---

## Anti-patrones a evitar

- crecer por `if command == ...` en el CLI o engine
- pasar mapas anonimos entre todas las capas
- dejar que `.context/` acumule estado no reproducible
- acoplar retrieval local al flujo base
- esconder reglas de inclusion en helpers sin trazabilidad

## Secuencia de implementacion (actualizada)

### Completo

| Paso | Fase | Version | Estado |
|------|------|---------|--------|
| 1 | D parcial | v0.2.0 | Hecho: .loom/ separado de .context/ |
| 2 | — | v0.2.0 | Hecho: GitHelper compartido (Facade) |
| 3 | — | v0.2.0 | Hecho: audit en init + enrich + decide |

### Siguiente

| Paso | Fase | Version | Que hacer |
|------|------|---------|-----------|
| 4 | A | v0.2.1 | Contratos tipados (ScanResult, StructureFacts, etc.) |
| 5 | B | v0.2.1 | Modularizacion CLI (1 archivo por comando) |
| 6 | — | v0.2.2 | Bundles + manifests + handoff (sobre contratos estables) |

### Postergado (cuando se necesite)

| Paso | Fase | Condicion para implementar |
|------|------|---------------------------|
| 7 | C: Pipelines/puertos | Cuando haya 6+ scanners o plugins externos |
| 8 | D resto: Cache | Cuando haya embeddings (post-v0.3.0) |
| 9 | E: IA | Cuando heuristicas demuestren ser insuficientes |

### Por que Fase C se posterga

El engine tiene 155 lineas y 4 scanners fijos. Agregar bundles no requiere registry ni pipeline builder — el selector es un consumidor de ScanResult, no un nuevo scanner. Introducir puertos abstractos y registry ahora seria abstraccion prematura. Se implementara cuando:

- haya mas de 5 scanners
- haya plugins externos
- el engine supere 300 lineas

## Criterio final de exito

La arquitectura estara lista cuando una nueva capability pueda agregarse:

- creando un modulo nuevo
- sin editar mas de 2 archivos existentes
- con pruebas de unidad y contrato claras
- sin romper output de `.context/`
