---
type: release
version: "0.5.0"
title: "Knowledge Registry: El Cerebro de Loom"
date: 2026-03-20
status: ready-for-release
---

# v0.5.0 Release Notes — Knowledge Registry

## TL;DR

Loom pasa de tener conocimiento hardcodeado disperso en 8 archivos Python a
un **Knowledge Registry centralizado** basado en JSON. Soporta 22 lenguajes,
332 paquetes en 8 ecosistemas, 15 patrones de arquitectura con scoring
multicapa, y permite extensiones locales sin tocar el codigo fuente.

---

## Que incluye esta version

### 1. Knowledge Registry (`knowledge/`)

Nuevo modulo con 4 archivos Python + 14 JSON + 3 dominios:

| Archivo | Contenido |
|---------|-----------|
| `__init__.py` | `get_registry()` singleton + `get_scorer()` |
| `models.py` | 14 dataclasses tipados (LanguageInfo, PackageInfo, ArchitecturePattern, etc.) |
| `registry.py` | KnowledgeRegistry: lazy load, cache en memoria, 25+ queries tipadas, override seguro |
| `scorer.py` | SignalScorer: deteccion de arquitectura con senales ponderadas |

### 2. Bases de datos JSON

| Archivo | Entradas | Que contiene |
|---------|----------|-------------|
| `languages.json` | 22 lenguajes | Extensiones, markers, package managers, naming, code patterns, frameworks |
| `ecosystems.json` | 332 paquetes | 8 ecosistemas (npm, pip, gem, cargo, hex, go, maven, nuget) + 18 reglas de inferencia |
| `architectures.json` | 15 patrones | Senales ponderadas, thresholds, boundary rules, legacy compat |
| `directories.json` | 188 anotaciones | Semantica de directorios (domain, models, cmd, benches, dags, etc.) |
| `security.json` | 45 + 33 | Exclusiones de directorio + patrones de secrets |
| `infrastructure.json` | 13 servicios | Redis, PostgreSQL, MySQL, MongoDB, ES, RabbitMQ, Meilisearch, Kafka, MinIO, SQLite, Memcached, ClickHouse, Neo4j + 41 package mappings |
| `roles.json` | 47 + 8 | Sufijos y prefijos arquitectonicos (Service, Repository, Controller, Concern, Aggregate, etc.) |
| `docs.json` | 15 + 20 | Reglas de clasificacion de documentacion (filename + path) |
| `stop_words.json` | 141 | Stop words EN + ES combinados |
| `markers.json` | 33 markers | Deteccion de tipo de proyecto ordenada por prioridad |
| `design_patterns.json` | 22 patrones | GoF + modernos con senales de deteccion por lenguaje |
| `domains/code.json` | - | Definicion del dominio de codigo |
| `domains/research.json` | - | Definicion del dominio de investigacion (placeholder) |
| `domains/data.json` | - | Definicion del dominio de data science (placeholder) |

### 3. Lenguajes soportados (22)

**Tier 1** — soporte completo (extensiones, markers, package managers, naming, code patterns, frameworks):
- Python, TypeScript, JavaScript, Ruby, Go, Rust, Java

**Tier 2** — extensiones, markers, package managers, naming:
- C#, PHP, Swift, Kotlin, Scala, Elixir, Dart

**Tier 3** — extensiones, markers basicos:
- Lua, Zig, Haskell, OCaml, R, Julia, C, C++

### 4. Design patterns (22)

Base de conocimiento para detectar patrones de diseno GoF y modernos:

| Categoria | Patrones | Ejemplos |
|-----------|----------|----------|
| Creational (5) | Singleton, Factory Method, Abstract Factory, Builder, Prototype | `_instance = None`, `create_*()`, `.build()` |
| Structural (6) | Adapter, Decorator, Facade, Proxy, Composite, Bridge | `*Adapter`, `*Decorator`, `*Proxy` |
| Behavioral (11) | Observer, Strategy, Command, Chain of Responsibility, Iterator, State, Repository, Mediator, Event Sourcing, Specification, Unit of Work | `*Observer`, `*Strategy`, `execute()`, `subscribe()` |

Cada patron tiene:
- Nombre estandar, categoria, intent
- Senales de deteccion con pesos (file_suffix, code_pattern, directory)
- Senales por lenguaje cuando aplica (Python vs Java vs TypeScript)
- Threshold de confianza

### 5. Patrones de arquitectura (15, con scoring)

| Patron | Nuevo | Senales | Threshold |
|--------|-------|---------|-----------|
| clean-architecture | Migrado | directory, file_suffix | 0.45 |
| hexagonal | Migrado | directory, file_suffix | 0.40 |
| mvc | Migrado | directory, file_suffix | 0.45 |
| mvvm | Migrado | directory, file_suffix | 0.50 |
| feature-based | Migrado | directory, file_suffix | 0.40 |
| layered | Migrado | directory, file_suffix | 0.45 |
| nestjs-modular | Migrado | directory, file_suffix | 0.40 |
| pipeline | Migrado | directory | 0.35 |
| terraform | Migrado | directory, file | 0.40 |
| **ddd** | **Nuevo** | directory, file_suffix, package | 0.40 |
| **event-driven** | **Nuevo** | directory, file_suffix, package | 0.35 |
| **cqrs** | **Nuevo** | directory, file_suffix | 0.40 |
| **microservices** | **Nuevo** | directory, file_suffix, package | 0.40 |
| **serverless** | **Nuevo** | directory, file_suffix | 0.35 |
| **monolith-modular** | **Nuevo** | directory, file_suffix | 0.40 |

La deteccion paso de match exacto de directorios a **scoring multicapa** con 5 tipos de senal:
directory, file_suffix, file_content, package, config_key. Cada senal tiene un peso.
Backward compat preservado via legacy_dir_sets.

### 5. Parsers de dependencias (9, eran 3)

| Parser | Archivo | Ecosistema | Estado |
|--------|---------|-----------|--------|
| `_scan_package_json` | package.json | npm | Existente |
| `_scan_pyproject_toml` | pyproject.toml | pip | Existente |
| `_scan_requirements_txt` | requirements.txt | pip | Existente |
| **`_scan_gemfile`** | Gemfile | gem | **Nuevo** |
| **`_scan_cargo_toml`** | Cargo.toml | cargo | **Nuevo** |
| **`_scan_go_mod`** | go.mod | go | **Nuevo** |
| **`_scan_mix_exs`** | mix.exs | hex | **Nuevo** |
| **`_scan_pom_xml`** | pom.xml | maven | **Nuevo** |
| **`_scan_gradle`** | build.gradle(.kts) | gradle | **Nuevo** |
| **`_scan_csproj`** | *.csproj | nuget | **Nuevo** |

Cada parser extrae nombre + version + dev/prod y categoriza via Knowledge Registry.

### 6. Deteccion de proyecto data-driven

`_detect_project_type` paso de ~90 lineas hardcodeadas a ~40 lineas que leen de `markers.json`.
Para agregar un nuevo tipo de proyecto: editar el JSON, no Python.

### 7. Overrides locales

Usuarios pueden extender la base de conocimiento sin modificar el paquete:

```
.loom/knowledge/
├── languages.json       ← agrega lenguajes custom
├── ecosystems.json      ← agrega paquetes
├── directories.json     ← agrega anotaciones
└── roles.json           ← agrega roles
```

Los overrides hacen **deep merge seguro** (append-only, type-safe).
No se trackean en git.

### 8. Hardening de seguridad

| Vulnerabilidad cerrada | Severidad | Mecanismo |
|----------------------|-----------|-----------|
| Command injection via infrastructure.json override | Critico | Archivo protegido |
| Path traversal en get_domain/load_json | Alto | Validacion + resolve check |
| markers.json override manipula deteccion | Medio | Archivo protegido |
| Type confusion (list a string) | Medio | _safe_merge rechaza cambio de tipo |
| Empty list override borra entries | Medio | Lists append-only |
| JSON bomb (DoS) | Bajo | Max 1MB por override |
| Stack overflow en merge | Bajo | Max depth 20 |

Archivos protegidos (nunca overrideables): `security.json`, `infrastructure.json`, `markers.json`

### 9. Migracion completa

11 archivos migrados de constantes hardcodeadas a Knowledge Registry:

| Archivo | Que se migro |
|---------|-------------|
| `security/filter.py` | HARDCODED_DIR_EXCLUSIONS, SECRETS_PATTERNS |
| `scanners/structure.py` | PROJECT_MARKERS, ARCHITECTURE_PATTERNS, DIR_ANNOTATIONS, BOUNDARY_RULES |
| `scanners/deps.py` | KNOWN_PACKAGES, _infer_category |
| `scanners/code.py` | CODE_EXTENSIONS, ROLE_SUFFIXES, ROLE_PREFIXES |
| `scanners/docs.py` | DOC_TYPE_RULES, PATH_TYPE_RULES |
| `scanners/infra.py` | ServiceDef instances, INFRA_SERVICES |
| `auditors/naming.py` | CODE_EXTENSIONS |
| `auditors/structure.py` | CODE_EXTENSIONS |
| `metrics.py` | CODE_EXTENSIONS |
| `generators/focus.py` | STOP_WORDS |
| `selector/strategies/heuristic.py` | STOP_WORDS |

**0 bases de conocimiento hardcodeadas fuera de knowledge/.**

---

## Numeros

| Metrica | v0.4.0 | v0.5.0 | Delta |
|---------|--------|--------|-------|
| Tests | 281 | 373 | +92 |
| Lenguajes | ~4 | 22 | +18 |
| Extensiones | 13 (x4 dup) | 49 (0 dup) | +36 |
| Paquetes conocidos | 138 | 332 | +194 |
| Ecosistemas | 2 | 8 | +6 |
| Arquitecturas | 9 | 15 | +6 |
| Dir annotations | 129 | 188 | +59 |
| Dir exclusions | 21 | 45 | +24 |
| Secret patterns | 22 | 33 | +11 |
| Role suffixes | 25 | 47 | +22 |
| Dependency parsers | 3 | 9 | +6 |
| Infra services | 9 | 13 | +4 |
| Security tests | 0 | 8 | +8 |
| Bases hardcodeadas | 17 | 0 | -17 |

---

## Que falta para liberar

### Obligatorio

- [ ] Merge de archivos no-v0.5.0 pendientes (db.py, database.py, migrations.py, database.md.j2 de v0.4.0)
- [ ] `ruff format src/ tests/` completo (7 line-length issues preexistentes en database.py/migrations.py)
- [ ] Branch release/v0.5.0 desde develop
- [ ] PR a main
- [ ] Tag v0.5.0
- [ ] Publicar en PyPI via CI

### Recomendado (puede ir en v0.5.1)

- [ ] `loom knowledge list` — CLI para ver que conoce Loom
- [ ] `loom knowledge validate` — validar JSON locales
- [ ] mypy strict en knowledge/
- [ ] README actualizado con badges de v0.5.0
- [ ] Quickstart actualizado mencionando multi-lenguaje

### Fuera de scope (v0.6.0+)

- Embeddings / ranking semantico
- Research scanner / Data scanner
- Multi-agente / gobernanza
- Plugin system

---

## Archivos modificados en esta version

### Nuevos (22 archivos)

```
src/loom_context/knowledge/__init__.py
src/loom_context/knowledge/models.py
src/loom_context/knowledge/registry.py
src/loom_context/knowledge/scorer.py
src/loom_context/knowledge/languages.json
src/loom_context/knowledge/ecosystems.json
src/loom_context/knowledge/architectures.json
src/loom_context/knowledge/directories.json
src/loom_context/knowledge/security.json
src/loom_context/knowledge/infrastructure.json
src/loom_context/knowledge/roles.json
src/loom_context/knowledge/docs.json
src/loom_context/knowledge/stop_words.json
src/loom_context/knowledge/markers.json
src/loom_context/knowledge/design_patterns.json
src/loom_context/knowledge/domains/code.json
src/loom_context/knowledge/domains/research.json
src/loom_context/knowledge/domains/data.json
tests/test_knowledge.py
docs/plans/roadmap-v0.5-v1.0.md
docs/plans/v0.5.0/delivery.md
docs/plans/v0.5.0/release-notes.md
```

### Modificados (16 archivos)

```
pyproject.toml (version bump)
src/loom_context/__init__.py (version bump)
src/loom_context/engine.py (registry project root)
src/loom_context/security/filter.py (migrado a registry)
src/loom_context/scanners/structure.py (migrado a registry + scorer)
src/loom_context/scanners/deps.py (migrado + 7 parsers nuevos)
src/loom_context/scanners/code.py (migrado a registry)
src/loom_context/scanners/docs.py (migrado a registry)
src/loom_context/scanners/infra.py (migrado a registry)
src/loom_context/auditors/naming.py (migrado a registry)
src/loom_context/auditors/structure.py (migrado a registry)
src/loom_context/metrics.py (migrado a registry)
src/loom_context/generators/focus.py (migrado a registry)
src/loom_context/selector/strategies/heuristic.py (migrado a registry)
tests/test_cli.py (version bump + test actualizado)
CHANGELOG.md
CLAUDE.md
docs/INDEX.md
```

---

## Calidad

| Check | Estado |
|-------|--------|
| pytest (373 tests) | Pass |
| ruff check (knowledge/, tests/) | Pass |
| ruff format (knowledge/, tests/) | Pass |
| bandit (0 issues, 7447 LOC) | Pass |
| Security tests (8 attack vectors) | Pass |
| Regression (0 tests rotos) | Pass |
