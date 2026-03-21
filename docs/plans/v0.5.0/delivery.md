---
type: delivery
version: "0.5.0"
title: "Knowledge Registry: El Cerebro de Loom"
status: in-progress
created: 2026-03-20
---

# v0.5.0 Delivery Plan — Knowledge Registry

## Objetivo

Centralizar las 17 bases de conocimiento hardcodeadas en un Knowledge Registry
extensible basado en JSON. Expandir cobertura de 13 a 20+ lenguajes, de 9 a 15+
patrones de arquitectura, y de 138 a 300+ paquetes conocidos.

---

## Task 1: Infraestructura del modulo knowledge/

**Archivos a crear:**

| Archivo | Responsabilidad |
|---------|----------------|
| `knowledge/__init__.py` | API publica: `get_registry()` singleton |
| `knowledge/models.py` | Dataclasses: LanguageInfo, PackageInfo, ArchitecturePattern, etc. |
| `knowledge/registry.py` | KnowledgeRegistry: carga lazy, cache, queries tipadas |
| `knowledge/scorer.py` | SignalScorer: evaluacion multicapa de patrones de arquitectura |

**Checklist:**

- [x] `knowledge/__init__.py` con `get_registry()` que retorna singleton
- [x] `knowledge/models.py` con todos los dataclasses
  - [x] `LanguageInfo` — extensiones, markers, naming, code patterns, frameworks
  - [x] `PackageInfo` — nombre, categoria, descripcion, ecosystem
  - [x] `ArchitectureSignal` — tipo, patron, peso
  - [x] `ArchitecturePattern` — senales, threshold, boundary rules
  - [x] `ArchitectureMatch` — nombre, score, senales matched
  - [x] `DirectoryAnnotation` — nombre, descripcion
  - [x] `SecurityPatterns` — dir exclusions, secret patterns
  - [x] `InfraServiceDef` — nombre, categoria, puerto, comandos
  - [x] `RolePattern` — tipo (suffix/prefix), valor, descripcion
  - [x] `DocClassificationRule` — patron, tipo, source (filename/path/content)
  - [x] `DomainDef` — nombre, markers, scanners
- [x] `knowledge/registry.py` — KnowledgeRegistry
  - [x] `_load_json(filename)` — carga lazy con cache
  - [x] `get_language(ext_or_name)` → Optional[LanguageInfo]
  - [x] `get_all_extensions()` → set[str] (code extensions unificado)
  - [x] `get_project_markers()` → list[tuple[str, str]] (marker → project_type)
  - [x] `get_package(name, ecosystem)` → Optional[PackageInfo]
  - [x] `infer_package_category(name)` → str
  - [x] `get_architecture_patterns()` → dict[str, ArchitecturePattern]
  - [x] `get_directory_annotation(name)` → Optional[str]
  - [x] `get_boundary_rules(architecture)` → dict
  - [x] `get_dir_exclusions()` → set[str]
  - [x] `get_secret_patterns()` → list[str]
  - [x] `get_infra_service(package_name)` → Optional[InfraServiceDef]
  - [x] `get_role_suffixes()` → list[RolePattern]
  - [x] `get_role_prefixes()` → list[RolePattern]
  - [x] `get_doc_rules()` → tuple[list[DocRule], list[DocRule]]
  - [x] `get_stop_words()` → set[str]
- [x] `knowledge/scorer.py` — SignalScorer
  - [x] `score(pattern, evidence)` → ArchitectureMatch
  - [x] `score_all(evidence)` → list[ArchitectureMatch] (sorted by score)
  - [x] Evidence dataclass: directories, files, packages, config_keys

**Criterios de salida:**

- [x] `from loom_context.knowledge import get_registry` funciona
- [x] `registry.get_all_extensions()` retorna set con 49 extensiones
- [x] `registry.get_language(".rb")` retorna LanguageInfo completo
- [ ] mypy pasa sin errores
- [ ] ruff pasa sin errores

---

## Task 2: Base de datos de lenguajes (languages.json)

**Cobertura target:**

| Tier | Lenguajes | Detalle |
|------|-----------|---------|
| 1 | Python, TypeScript, JavaScript, Ruby, Go, Rust, Java | Full support: extensions, markers, package managers, naming, code patterns, frameworks |
| 2 | C#, PHP, Swift, Kotlin, Scala, Elixir, Dart | Extensions, markers, package managers, naming |
| 3 | Lua, Zig, Haskell, OCaml, R, Julia, C, C++ | Extensions, markers basicos |

**Checklist por lenguaje Tier 1:**

Python:
- [ ] Extensions: .py, .pyi, .pyw
- [ ] Markers: pyproject.toml, setup.py, setup.cfg, requirements.txt, Pipfile
- [ ] Package managers: poetry, uv, pip, pipenv
- [ ] Naming: files=snake_case, classes=PascalCase, functions=snake_case, constants=UPPER_SNAKE
- [ ] Code patterns: class, def, constants regex
- [ ] Frameworks: Django, Flask, FastAPI

TypeScript:
- [ ] Extensions: .ts, .tsx, .mts, .cts
- [ ] Markers: tsconfig.json
- [ ] Naming: varies by framework
- [ ] Code patterns: interface, class, function, const, enum, type

JavaScript:
- [ ] Extensions: .js, .jsx, .mjs, .cjs
- [ ] Markers: package.json
- [ ] Package managers: npm, yarn, pnpm, bun
- [ ] Code patterns: class, function, const

Ruby:
- [ ] Extensions: .rb, .erb, .rake, .gemspec, .ru
- [ ] Markers: Gemfile, Rakefile, .ruby-version
- [ ] Package managers: bundler
- [ ] Naming: files=snake_case, classes=PascalCase, methods=snake_case
- [ ] Frameworks: Rails (markers, src_roots, exclusions)

Go:
- [ ] Extensions: .go
- [ ] Markers: go.mod, go.sum
- [ ] Naming: files=snake_case, types/funcs=PascalCase (exported) / camelCase (unexported)
- [ ] Code patterns: func, type struct, type interface

Rust:
- [ ] Extensions: .rs
- [ ] Markers: Cargo.toml, Cargo.lock
- [ ] Naming: files=snake_case, types=PascalCase, functions=snake_case
- [ ] Code patterns: fn, struct, enum, trait, impl

Java:
- [ ] Extensions: .java
- [ ] Markers: pom.xml, build.gradle, build.gradle.kts
- [ ] Package managers: maven, gradle
- [ ] Naming: files=PascalCase, classes=PascalCase, methods=camelCase

**Criterios de salida:**

- [ ] 20+ lenguajes en languages.json
- [ ] JSON valido (parseable sin errores)
- [ ] Tier 1: 100% campos completos
- [ ] Tier 2: extensiones + markers + naming
- [ ] Tier 3: extensiones + markers minimos

---

## Task 3: Base de datos de ecosistemas (ecosystems.json)

**Target: 300+ paquetes en 8 ecosistemas**

| Ecosistema | Actual | Target | Categorias |
|-----------|--------|--------|------------|
| npm | 110 | 150+ | ui, state, db, http, testing, build, auth, logging |
| pip | 12 | 60+ | web, db, validation, testing, cli, async, ml, data |
| gem | 0 | 40+ | web, db, testing, auth, background, api, serialization |
| cargo | 0 | 30+ | web, async, db, serialization, cli, crypto |
| hex | 0 | 20+ | web, db, testing, auth, pubsub |
| go | 0 | 20+ | web, db, testing, cli, logging |
| maven | 0 | 20+ | web, db, testing, di, logging |
| nuget | 0 | 15+ | web, db, testing, di, auth |

**Checklist por ecosistema nuevo:**

gem (Ruby):
- [ ] rails, sinatra, hanami (web-framework)
- [ ] activerecord, sequel, rom-rb (database)
- [ ] rspec, minitest, factory_bot, faker (testing)
- [ ] devise, omniauth, doorkeeper (auth)
- [ ] sidekiq, delayed_job, resque (background)
- [ ] grape, jsonapi-serializer, dry-rb gems (api, validation)
- [ ] rubocop, standard (linting)
- [ ] puma, unicorn (http-server)

cargo (Rust):
- [ ] actix-web, axum, rocket, warp (web-framework)
- [ ] tokio, async-std (async-runtime)
- [ ] diesel, sqlx, sea-orm (database)
- [ ] serde, serde_json (serialization)
- [ ] clap, structopt (cli)
- [ ] tracing, log, env_logger (logging)

pip (Python, expandir):
- [ ] uvicorn, gunicorn, hypercorn (http-server)
- [ ] numpy, pandas, polars (data)
- [ ] scikit-learn, torch, tensorflow (ml)
- [ ] boto3, google-cloud-storage (cloud)
- [ ] aiohttp, starlette (async-web)
- [ ] black, isort, mypy (code-quality)
- [ ] structlog, loguru (logging)
- [ ] typer (cli)
- [ ] dbt-core (data-pipeline)

**Criterios de salida:**

- [ ] 300+ paquetes totales
- [ ] 8 ecosistemas representados
- [ ] Cada paquete tiene: category + description
- [ ] Reglas de inferencia migradas y expandidas

---

## Task 4: Base de datos de arquitecturas (architectures.json)

**Target: 15+ patrones con scoring multicapa**

| Patron | Status | Senales clave |
|--------|--------|--------------|
| clean-architecture | Migrar + scoring | domain/, infrastructure/, presentation/, use_cases/ |
| hexagonal | Migrar + scoring | ports/, adapters/, application/ |
| mvc | Migrar + scoring | models/, views/, controllers/ |
| mvvm | Migrar + scoring | models/, views/, viewmodels/ |
| feature-based | Migrar + scoring | features/, modules/ |
| layered | Migrar + scoring | controllers/, services/, repositories/ |
| nestjs-modular | Migrar + scoring | modules/, common/ |
| pipeline | Migrar + scoring | scanners/, generators/, auditors/ |
| terraform | Migrar + scoring | modules/, environments/ |
| **ddd** | **Nuevo** | domains/, aggregates/, value_objects/, bounded_contexts/ |
| **event-driven** | **Nuevo** | events/, listeners/, handlers/, subscribers/ |
| **cqrs** | **Nuevo** | commands/, queries/, read_models/ |
| **microservices** | **Nuevo** | services/, gateway/, proto/, api-gateway/ |
| **serverless** | **Nuevo** | functions/, handlers/, stacks/, serverless.yml |
| **monolith-modular** | **Nuevo** | modules/ con alta cohesion interna |

**Checklist por patron nuevo:**

DDD:
- [ ] 8+ senales con pesos calibrados
- [ ] Threshold: 0.40
- [ ] Boundary rules para domain, application, infrastructure
- [ ] Detecta DDD dentro de Rails (app/domains/)

Event-Driven:
- [ ] Senales: events/, listeners/, handlers/, subscribers/, _event suffix, _listener suffix
- [ ] Package signals: wisper (gem), eventmachine (gem), celery (pip)
- [ ] Threshold: 0.35

CQRS:
- [ ] Senales: commands/, queries/, read_models/, _command suffix, _query suffix
- [ ] Frecuentemente combinado con event-driven y DDD
- [ ] Threshold: 0.40

**Criterios de salida:**

- [ ] 15+ patrones en architectures.json
- [ ] Cada patron tiene 5+ senales con pesos
- [ ] Cada patron tiene threshold definido
- [ ] Boundary rules para patrones que los necesitan
- [ ] Backward compat: match exacto sigue funcionando como senal peso 1.0

---

## Task 5: Bases de datos secundarias

### directories.json (150+ anotaciones)

- [ ] Migrar 129 existentes de DIR_ANNOTATIONS
- [ ] Agregar Ruby: app/mailers, app/jobs, app/channels, app/concerns, app/serializers
- [ ] Agregar Go: cmd/, internal/, pkg/, api/, configs/
- [ ] Agregar Rust: benches/, examples/, src/bin/
- [ ] Agregar Java: src/main/java, src/main/resources, src/test/
- [ ] Agregar Research: data/, notebooks/, experiments/, references/, figures/
- [ ] Agregar Data: pipelines/, warehouses/, dbt/, airflow/, models/

### security.json

- [ ] Migrar HARDCODED_DIR_EXCLUSIONS (21)
- [ ] Migrar SECRETS_PATTERNS (22)
- [ ] Agregar per-language: target/ (Rust), _build/ (Elixir), deps/ (Elixir), .bundle/ (Ruby), bin/ (Go built)
- [ ] Agregar: *.sqlite, *.db (database files)

### infrastructure.json

- [ ] Migrar 9 servicios + 20 package mappings
- [ ] Agregar: Memcached, ClickHouse, Neo4j
- [ ] Mapeo por ecosistema (no solo npm)

### roles.json

- [ ] Migrar 25 sufijos + 5 prefijos
- [ ] Agregar Ruby: Concern, Decorator, Serializer, Job, Mailer, Channel
- [ ] Agregar Go: Handler, Server, Client, Store
- [ ] Agregar Rust: Handler, Builder, Error

### docs.json

- [ ] Migrar DOC_TYPE_RULES (6) + PATH_TYPE_RULES (14)
- [ ] Agregar: ADR (Architecture Decision Record), RFC, SECURITY.md

### stop_words.json

- [ ] Merge focus.py (55) + heuristic.py (59), deduplicar
- [ ] ~70 palabras unicas (EN + ES)

**Criterios de salida:**

- [ ] Todos los JSON parseables sin error
- [ ] 0 datos hardcodeados fuera de knowledge/

---

## Task 6: Migracion de scanners

Cada scanner pasa de constantes inline a `registry.method()`.

**Orden de migracion (por dependencias):**

1. [ ] `security/filter.py` — HARDCODED_DIR_EXCLUSIONS, SECRETS_PATTERNS → registry
2. [ ] `scanners/structure.py` — PROJECT_MARKERS, ARCHITECTURE_PATTERNS, DIR_ANNOTATIONS, BOUNDARY_RULES → registry
3. [ ] `scanners/deps.py` — KNOWN_PACKAGES, _infer_category → registry
4. [ ] `scanners/code.py` — CODE_EXTENSIONS, ROLE_SUFFIXES, ROLE_PREFIXES → registry
5. [ ] `scanners/docs.py` — DOC_TYPE_RULES, PATH_TYPE_RULES → registry
6. [ ] `scanners/infra.py` — INFRA_SERVICES → registry
7. [ ] `auditors/naming.py` — CODE_EXTENSIONS → registry
8. [ ] `auditors/structure.py` — CODE_EXTENSIONS → registry
9. [ ] `metrics.py` — CODE_EXTENSIONS → registry
10. [ ] `generators/focus.py` — STOP_WORDS → registry
11. [ ] `selector/strategies/heuristic.py` — STOP_WORDS → registry

**Patron de migracion:**

```python
# ANTES
from loom_context.scanners.structure import DIR_ANNOTATIONS

annotation = DIR_ANNOTATIONS.get(name, "")

# DESPUES
from loom_context.knowledge import get_registry

registry = get_registry()
annotation = registry.get_directory_annotation(name) or ""
```

**Regla:** el registry se inyecta en el constructor de cada scanner cuando es posible. Si no, se accede via `get_registry()`.

**Criterios de salida:**

- [ ] 0 constantes hardcodeadas fuera de knowledge/
- [ ] Todos los imports apuntan a knowledge
- [ ] 0 regresiones en 281+ tests
- [ ] `make qa` pasa

---

## Task 7: Tests

- [ ] `tests/test_knowledge_registry.py`
  - [ ] Test carga de cada JSON
  - [ ] Test queries: get_language, get_package, get_extensions, etc.
  - [ ] Test singleton behavior
  - [ ] Test cache (segunda carga es instantanea)
- [ ] `tests/test_signal_scorer.py`
  - [ ] Test scoring con fixture de proyecto clean-architecture
  - [ ] Test scoring con fixture de proyecto DDD
  - [ ] Test scoring con fixture de proyecto plano (→ "flat")
  - [ ] Test threshold: score bajo → no detectado
  - [ ] Test multiples patrones detectados
- [ ] `tests/test_knowledge_data.py`
  - [ ] Validacion de schema de cada JSON
  - [ ] Todos los lenguajes tienen extensiones
  - [ ] Todos los paquetes tienen categoria
  - [ ] Todos los patrones tienen senales y threshold
- [ ] Tests de regresion
  - [ ] `pytest` completo pasa (281+ tests)
  - [ ] `make qa` pasa (ruff + mypy + bandit + pytest)
- [ ] Tests de integracion
  - [ ] tmp_project fixture: loom init genera mismos archivos que antes
  - [ ] Benchmark: scan < 2s en proyecto de 700 archivos

**Target total: 320+ tests (281 existentes + 40 nuevos)**

---

## Orden de implementacion recomendado

```
1. knowledge/models.py          ← tipos primero
2. JSON data files              ← datos puros, sin logica
3. knowledge/registry.py        ← carga + queries
4. knowledge/scorer.py          ← scoring de arquitectura
5. knowledge/__init__.py        ← API publica
6. Tests de knowledge           ← validar antes de migrar
7. Migracion de scanners        ← uno a uno, tests entre cada uno
8. Tests de regresion           ← todo sigue pasando
9. Cleanup: remover constantes  ← cuando todo esta verde
```

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| JSON parsing lento en startup | Lazy loading + cache en memoria |
| Regresion en tests por cambio de API | Migracion gradual, test entre cada scanner |
| JSON invalido causa crash | Schema validation en CI + test que parsea todos los JSON |
| Scoring retorna diferentes arquitecturas que match exacto | Mantener match exacto como fallback con peso 1.0 |
| Performance degradada por escaneo recursivo de dirs | Limitar profundidad a 4 niveles, benchmark en CI |
