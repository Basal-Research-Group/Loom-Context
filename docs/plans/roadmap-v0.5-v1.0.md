---
type: roadmap
versions: ["0.5.0", "0.6.0", "0.7.0", "0.8.0", "1.0.0"]
status: active
created: 2026-03-20
---

# Roadmap v0.5 - v1.0: Knowledge Registry, IA y Dominios Multiples

> Objetivo: transformar Loom de un scanner hardcodeado para JS/TS/Python en una plataforma de contexto universal — con base de conocimiento extensible, capa de IA opcional, y soporte para multiples dominios (codigo, investigacion, datos).

## Vision

```
v0.1-v0.4  → Prueba de concepto: pipeline funcional, 4 lenguajes, 9 arquitecturas
v0.5       → Cerebro: Knowledge Registry centralizada, 20+ lenguajes, scoring multicapa [DONE]
v0.6       → Deteccion: DomainDetector, domain-aware prompts, security rules [DONE]
v0.7       → Adapters: DomainAdapter base, ContextRanker, engine dinamico [DONE]
v0.8       → Trazas: ResolutionTrace, GovernanceAuditor, loom trace CLI [DONE]
v0.9       → IA: OllamaRanker, HybridRanker, --ai local, benchmark
v1.0       → Estabilidad: API publica, plugins, backward compat, 500+ tests
```

---

## Estado Actual (v0.4.0, 2026-03-20)

| Aspecto | Estado | Problema |
|---------|--------|----------|
| Lenguajes | 13 extensiones, pesado en JS/TS | Ruby, Elixir, Dart, R sin soporte real |
| Paquetes conocidos | 138 (mayoria npm) | Gem, Cargo, Hex, Go modules vacios |
| Arquitecturas | 9 patrones, match exacto por directorio | No detecta DDD en Rails, ni CQRS, ni event-driven |
| Datos dispersos | 17 bases hardcodeadas en 8 archivos | Duplicacion (CODE_EXTENSIONS x4), dificil de mantener |
| Dominios | Solo codigo | Research, data science sin soporte |
| IA | Ninguna | Sin embeddings, sin ranking semantico |

### Inventario de conocimiento hardcodeado (a migrar)

| Base de datos | Archivo actual | Entradas | Destino |
|--------------|----------------|----------|---------|
| `PROJECT_MARKERS` | `scanners/structure.py:13` | 28 | `languages.json` |
| `ARCHITECTURE_PATTERNS` | `scanners/structure.py:54` | 9 | `architectures.json` |
| `DIR_ANNOTATIONS` | `scanners/structure.py:100` | 129 | `directories.json` |
| `BOUNDARY_RULES` | `scanners/structure.py:231` | 4 | `architectures.json` |
| `KNOWN_PACKAGES` | `scanners/deps.py:12` | 138 | `ecosystems.json` |
| `CODE_EXTENSIONS` | `scanners/code.py:15` | 18 | `languages.json` |
| `CODE_EXTENSIONS` | `metrics.py:37` | 10 | `languages.json` (dedup) |
| `CODE_EXTENSIONS` | `auditors/naming.py:13` | 7 | `languages.json` (dedup) |
| `CODE_EXTENSIONS` | `auditors/structure.py:18` | 7 | `languages.json` (dedup) |
| `ROLE_SUFFIXES` | `scanners/code.py:45` | 25 | `roles.json` |
| `ROLE_PREFIXES` | `scanners/code.py:78` | 5 | `roles.json` |
| `HARDCODED_DIR_EXCLUSIONS` | `security/filter.py:12` | 21 | `security.json` |
| `SECRETS_PATTERNS` | `security/filter.py:36` | 22 | `security.json` |
| `INFRA_SERVICES` | `scanners/infra.py:158` | 20 | `infrastructure.json` |
| `DOC_TYPE_RULES` | `scanners/docs.py:12` | 6 | `docs.json` |
| `PATH_TYPE_RULES` | `scanners/docs.py:21` | 14 | `docs.json` |
| `STOP_WORDS` (x2) | `generators/focus.py:11`, `selector/strategies/heuristic.py:12` | 55+59 | `stop_words.json` (merge) |

**Total: ~650+ entradas en 17 bases → 10 archivos JSON centralizados**

---

## Principios de Producto (extendidos)

Los 7 principios originales se mantienen. Se agregan 3 nuevos:

1. **Deterministic-first** — la IA es capa opcional, nunca requisito
2. **Scan much, ask nothing** — auto-detectar, no preguntar
3. **Metadata only** — nunca incluir codigo fuente en `.context/`
4. **Security first** — 3 capas de filtrado, secrets siempre excluidos
5. **Progressive consumption** — quick_rules → bundle → full
6. **Stay fast** — < 2s para 700 archivos
7. **Stay light** — 4 deps runtime core
8. **NEW: Data-driven detection** — patrones en JSON, no en Python
9. **NEW: Signal scoring** — multiples senales con pesos, no match exacto
10. **NEW: Domain-agnostic core** — engine y generators sirven para cualquier dominio

---

## v0.5.0 — Knowledge Registry

> **Titulo**: "El Cerebro de Loom"
> **Meta**: centralizar todo el conocimiento en una base de datos extensible, expandir cobertura de lenguajes y arquitecturas, eliminar duplicacion.

### Fase 1: Infraestructura del Knowledge Registry

- [x] Crear modulo `knowledge/` con estructura de directorios
- [x] Crear `knowledge/models.py` — dataclasses tipados para cada entidad
  - [x] `LanguageInfo`: extensiones, markers, naming, code patterns
  - [x] `PackageInfo`: categoria, descripcion, ecosystem
  - [x] `ArchitecturePattern`: senales, threshold, boundary rules
  - [x] `DirectoryAnnotation`: nombre, descripcion, roles
  - [x] `SecurityRule`: exclusiones, secrets
  - [x] `InfraService`: nombre, categoria, puertos, comandos
  - [x] `RolePattern`: sufijo/prefijo, descripcion
  - [x] `DocRule`: patron, tipo
  - [x] `DomainInfo`: marcadores, scanners, templates
- [x] Crear `knowledge/registry.py` — clase `KnowledgeRegistry`
  - [x] Carga lazy de JSON (solo cuando se necesita)
  - [x] Cache en memoria (singleton per process)
  - [x] API tipada: `get_language()`, `get_extensions()`, `detect_architecture()`, etc.
  - [x] Metodo `score_signals()` para arquitecturas
- [x] Crear `knowledge/__init__.py` — API publica

### Fase 2: Bases de datos JSON

- [x] `languages.json` — 22+ lenguajes Tier 1-3
  - [ ] Tier 1: Python, TypeScript, JavaScript, Ruby, Go, Rust, Java
  - [ ] Tier 2: C#, PHP, Swift, Kotlin, Scala, Elixir, Dart
  - [ ] Tier 3: Lua, Zig, Haskell, OCaml, R, Julia, C, C++
  - [ ] Cada lenguaje: extensiones, markers, package managers, naming, code patterns, comment style, import patterns
- [ ] `ecosystems.json` — 300+ paquetes en 6+ ecosistemas
  - [ ] npm (existente: 110+ → expandir a 150+)
  - [ ] pip (existente: 12 → expandir a 60+)
  - [ ] gem (nuevo: 40+ paquetes Ruby)
  - [ ] cargo (nuevo: 30+ crates Rust)
  - [ ] hex (nuevo: 20+ paquetes Elixir)
  - [ ] go (nuevo: 20+ modulos Go)
  - [ ] maven/gradle (nuevo: 20+ librerias Java/Kotlin)
  - [ ] nuget (nuevo: 15+ paquetes C#)
  - [ ] Reglas de inferencia por patron (existente, migrar `_infer_category`)
- [ ] `architectures.json` — 15+ patrones con scoring
  - [ ] Migrar 9 existentes (clean, hexagonal, mvc, mvvm, feature, layered, nestjs, pipeline, terraform)
  - [ ] Agregar: DDD, Event-Driven, CQRS, Microservices, Serverless, Monolith-Modular
  - [ ] Cada patron: senales con peso, threshold de confianza, boundary rules
  - [ ] Tipos de senal: directory, file_suffix, file_content, package, config_key
  - [ ] Soporte para escaneo recursivo (no solo top-level)
- [ ] `directories.json` — 150+ anotaciones semanticas
  - [ ] Migrar 129 existentes
  - [ ] Agregar: Ruby (app/mailers, app/jobs, app/channels), Go (cmd/, internal/, pkg/), Rust (benches/, examples/)
  - [ ] Agregar: research (data/, notebooks/, experiments/, references/)
  - [ ] Agregar: data science (pipelines/, warehouses/, dbt/, airflow/)
- [ ] `security.json` — exclusiones y secrets
  - [ ] Migrar HARDCODED_DIR_EXCLUSIONS (21 dirs)
  - [ ] Migrar SECRETS_PATTERNS (22 patrones)
  - [ ] Agregar exclusiones por lenguaje (target/, _build/, deps/, .bundle/)
- [ ] `infrastructure.json` — servicios detectables
  - [ ] Migrar 9 servicios existentes (Redis, Postgres, MySQL, MongoDB, ES, RabbitMQ, Meilisearch, Kafka, MinIO)
  - [ ] Agregar: Memcached, DynamoDB (local), Supabase, Neon, CockroachDB
  - [ ] Mapeo package→service por ecosistema
- [ ] `roles.json` — sufijos y prefijos arquitectonicos
  - [ ] Migrar 25 sufijos + 5 prefijos
  - [ ] Agregar roles por lenguaje (Ruby: `_concern`, `_decorator`, `_serializer`)
- [ ] `docs.json` — reglas de clasificacion de documentacion
  - [ ] Migrar DOC_TYPE_RULES (6) + PATH_TYPE_RULES (14)
  - [ ] Agregar patrones para README variants, ADRs, RFCs
- [ ] `stop_words.json` — merge de ambas listas
  - [ ] Combinar focus.py (55) + heuristic.py (59), deduplicar

### Fase 3: Migracion de scanners

- [ ] `StructureScanner` → usa registry para markers, architecture, dir annotations, boundaries
- [ ] `DependencyScanner` → usa registry para known packages e inferencia
- [ ] `CodeScanner` → usa registry para extensiones, roles, code patterns
- [ ] `DocsScanner` → usa registry para doc rules
- [ ] `FileFilter` → usa registry para security patterns
- [ ] `InfraScanner` → usa registry para service definitions
- [ ] `NamingAuditor` → usa registry para code extensions
- [ ] `StructureAuditor` → usa registry para code extensions
- [ ] `MetricsCollector` → usa registry para code extensions (elimina duplicado)
- [ ] `FocusGenerator` → usa registry para stop words
- [ ] `HeuristicStrategy` → usa registry para stop words

### Fase 4: Scoring de arquitectura (reemplaza match exacto)

- [ ] Implementar `SignalScorer` en registry
  - [ ] Senal tipo `directory`: busca directorio en cualquier profundidad
  - [ ] Senal tipo `file_suffix`: busca archivos con sufijo especifico
  - [ ] Senal tipo `file_content`: busca patron en contenido (regex, max 100 archivos)
  - [ ] Senal tipo `package`: busca dependencia en ecosistema
  - [ ] Senal tipo `config_key`: busca key en archivos de configuracion
- [ ] Cada senal tiene un `weight` (0.0-1.0)
- [ ] Score = sum(matched_signal.weight for signal in pattern.signals)
- [ ] Si score >= threshold → arquitectura detectada (con confianza)
- [ ] Mantener backward compat: match exacto como senal con peso 1.0
- [ ] Retornar lista de `ArchMatch(name, score, signals_matched)` ordenada por score

### Fase 5: Tests y QA

- [ ] Tests unitarios para `KnowledgeRegistry` (carga, queries, cache)
- [ ] Tests para `SignalScorer` con fixtures de proyectos reales
- [ ] Tests de regresion: todos los 281+ tests existentes pasan
- [ ] Tests de integracion: loom init en proyecto Ruby on Rails detecta correctamente
- [ ] Tests de integracion: loom init en proyecto Go detecta correctamente
- [ ] Validacion de JSON: schema validation en CI para todos los .json
- [ ] `make qa` pasa (ruff + mypy + bandit + pytest)
- [ ] Benchmark: scan performance sigue < 2s para 700 archivos

### Criterios de salida v0.5.0

- [ ] 0 bases de conocimiento hardcodeadas (todo en knowledge/)
- [ ] 20+ lenguajes soportados
- [ ] 15+ patrones de arquitectura con scoring
- [ ] 300+ paquetes categorizados
- [ ] 150+ anotaciones de directorio
- [ ] 0 regresiones en tests existentes
- [ ] Documentacion actualizada

---

## v0.6.0 — Capa de IA Opcional

> **Titulo**: "Inteligencia Local"
> **Meta**: agregar embeddings, ranking semantico y templates generativos sin romper el core determinista.

### Prerequisitos (deben existir de v0.5.0)

- [x] Knowledge Registry funcional
- [x] Contratos tipados (ya existe desde v0.2.1)
- [x] Scoring de arquitectura (v0.5.0)

### Entregables

- [ ] `knowledge/embeddings.py` — generacion y cache de embeddings
  - [ ] Interface `Embedder` (port)
  - [ ] Adapter `SentenceTransformerEmbedder` (all-MiniLM-L6-v2)
  - [ ] Adapter `BGEEmbedder` (BAAI/bge-m3 para multilingue)
  - [ ] Cache en `.loom/cache/embeddings/`
  - [ ] Invalidacion por hash de archivo
- [ ] `knowledge/ranker.py` — ranking semantico de contexto
  - [ ] Ranking por similitud coseno con embeddings
  - [ ] Fusion con score heuristico (weighted hybrid)
  - [ ] Policy de token budget
- [ ] `knowledge/templates.py` — templates generativos
  - [ ] Template de handoff enriquecido
  - [ ] Template de resumen ejecutivo
  - [ ] Template de risk assessment
  - [ ] Fallback a templates estaticos sin IA
- [ ] Integracion con selector/
  - [ ] `strategies/hybrid.py` — combina heuristic + embeddings
  - [ ] `strategies/semantic.py` — full semantic ranking
- [ ] CLI: `--ai local` flag
  - [ ] Auto-detecta modelo disponible
  - [ ] Fallback graceful si no hay modelo
  - [ ] `loom config ai.model <model>` para configurar
- [ ] Packaging: `pip install loom-context[ai]`
  - [ ] Extra dependency: `sentence-transformers`
  - [ ] No afecta instalacion base

### Pre-embeddings: Knowledge Embeddings

- [ ] Pre-calcular embeddings de las descripciones en knowledge/*.json
- [ ] Usar para similitud: "este directorio se parece a X patron"
- [ ] Permite matching fuzzy sin LLM externo
- [ ] Ejemplo: directorio `bounded_contexts/` → 0.87 similitud con DDD.description

### Criterios de salida v0.6.0

- [ ] `loom bundle "tarea" --ai local` produce bundles mas relevantes que heuristic-only
- [ ] Evals con 10 tareas reales: precision@5 > 0.7
- [ ] Sin IA instalada, todo sigue funcionando identico
- [ ] Benchmark: con IA, bundle < 5s (embeddings cacheados)

---

## v0.8.0 — Dominios Multiples

> **Titulo**: "Mas alla del Codigo"
> **Meta**: soporte para proyectos de investigacion, ciencia de datos y documentacion tecnica.

### Prerequisitos

- [x] Knowledge Registry (v0.5.0)
- [x] Domain patterns en `knowledge/domains/` (v0.5.0)
- [x] Embeddings opcionales (v0.6.0)

### Dominio: Research

- [ ] `scanners/research.py` — `ResearchScanner`
  - [ ] Escanea .bib → extrae referencias, autores, journals
  - [ ] Escanea .tex → extrae secciones, hipotesis, citations
  - [ ] Escanea .ipynb → extrae celdas, visualizaciones, conclusiones
  - [ ] Escanea data/ → schema de datasets (columnas, tipos, tamano)
  - [ ] Escanea experiments/ → config, resultados, metricas
- [ ] `templates/methodology.md.j2`
- [ ] `templates/literature-map.md.j2`
- [ ] `templates/data-inventory.md.j2`
- [ ] `templates/experiment-summary.md.j2`
- [ ] `knowledge/domains/research.json` — marcadores y patrones
- [ ] Auto-deteccion: .bib, references/, notebooks/, experiments/
- [ ] CLI: `loom init . --domain research`
- [ ] Packaging: `pip install loom-context[research]`

### Dominio: Data Science

- [ ] `scanners/data_science.py` — `DataScienceScanner`
  - [ ] Escanea dbt_project.yml → modelos, sources, tests
  - [ ] Escanea schemas → columnas, tipos, relaciones
  - [ ] Escanea pipelines (Airflow, Prefect, Dagster) → DAGs, dependencias
  - [ ] Escanea .parquet/.csv headers → schema de datos
- [ ] `templates/data-lineage.md.j2`
- [ ] `templates/pipeline-map.md.j2`
- [ ] `knowledge/domains/data.json` — marcadores y patrones
- [ ] Auto-deteccion: dbt_project.yml, pipeline/, airflow/
- [ ] CLI: `loom init . --domain data`
- [ ] Packaging: `pip install loom-context[data]`

### Dominio: Documentacion Tecnica

- [ ] `scanners/docs_project.py` — `DocsProjectScanner`
  - [ ] Escanea Docusaurus, MkDocs, Sphinx configs
  - [ ] Extrae navegacion, cross-references, versiones
  - [ ] Detecta docs rotas (links muertos, secciones vacias)
- [ ] `knowledge/domains/docs.json`
- [ ] Auto-deteccion: docusaurus.config.js, mkdocs.yml, conf.py

### Engine: soporte multi-dominio

- [ ] `engine.py` detecta dominio(s) y carga scanners apropiados
- [ ] Proyecto mixto (code + research) ejecuta ambos sets de scanners
- [ ] `.context/` genera archivos segun dominio detectado

### Criterios de salida v0.8.0

- [ ] loom init en proyecto de tesis genera contexto util
- [ ] loom init en proyecto dbt genera contexto util
- [ ] Dominio detectado automaticamente en 90%+ de casos
- [ ] Sin regresiones en dominio code

---

## v0.8.0 — Gobernanza y Multi-Agente

> **Titulo**: "Contexto Compartido"
> **Meta**: soporte para multiples agentes trabajando en el mismo repo, con boundaries explicitos y conflict detection.

### Entregables

- [ ] `loom.json` como fuente de verdad de configuracion
  - [ ] Layers explicitas con paths
  - [ ] Ownership por layer (equipo/agente)
  - [ ] Constraints personalizados
- [ ] Worktree locks para bundles
  - [ ] Un agente reclama un area → otros ven el lock
  - [ ] Deteccion de conflictos entre tareas activas
- [ ] Gobernanza de decisions
  - [ ] Approval workflow para cambios en boundaries
  - [ ] History de quien decidio que y cuando
- [ ] Export multi-agente
  - [ ] Contexto diferenciado por rol de agente
  - [ ] Agente de review vs agente de implementacion
- [ ] Metricas de multi-agente
  - [ ] Tokens consumidos por agente
  - [ ] Conflictos detectados
  - [ ] Cobertura de contexto

---

## v1.0.0 — Estabilidad

> **Titulo**: "Produccion"
> **Meta**: API publica estable, backward compat garantizada, documentacion completa, 500+ tests.

### Entregables

- [ ] API publica documentada (Python)
- [ ] Backward compatibility policy (semver estricto)
- [ ] 500+ tests, 95%+ coverage
- [ ] Documentacion completa en ingles y espanol
- [ ] Plugin system para scanners externos
- [ ] Performance: < 1s para 1000 archivos
- [ ] CI/CD: release automatico a PyPI en tag
- [ ] Security audit completo

---

## Dependencias y Packaging

### Core (siempre, 4 deps)

```
click>=8.1
rich>=13.0
pathspec>=0.12
jinja2>=3.1
```

### Extras opcionales

| Extra | Dependencias | Peso | Version |
|-------|-------------|------|---------|
| `[ai]` | sentence-transformers | ~2GB | v0.6.0 |
| `[research]` | bibtexparser | ~1MB | v0.8.0 |
| `[data]` | (stdlib) | 0 | v0.8.0 |

### Regla

El core NUNCA crece en dependencias. Cada dominio y capacidad es un extra opcional.

---

## Estructura del Knowledge Registry (v0.5.0)

```
src/loom_context/knowledge/
├── __init__.py              # API publica: get_registry()
├── registry.py              # KnowledgeRegistry (singleton, lazy load)
├── models.py                # Dataclasses tipados
├── scorer.py                # SignalScorer para arquitecturas
│
├── languages.json           # 20+ lenguajes con todo su metadata
├── ecosystems.json          # 300+ paquetes en 6+ ecosistemas
├── architectures.json       # 15+ patrones con scoring multicapa
├── directories.json         # 150+ anotaciones semanticas
├── security.json            # Exclusiones + secrets
├── infrastructure.json      # Servicios detectables
├── roles.json               # Sufijos/prefijos arquitectonicos
├── docs.json                # Clasificacion de documentacion
├── stop_words.json          # Stop words (EN + ES)
│
└── domains/                 # Dominios de contexto
    ├── code.json            # Default: patrones especificos de codigo
    ├── research.json        # Investigacion (v0.8.0)
    └── data.json            # Data science (v0.8.0)
```

### Esquema de arquitectura con scoring (ejemplo)

```json
{
  "ddd": {
    "name": "Domain-Driven Design",
    "signals": [
      {"type": "directory", "pattern": "domains", "weight": 0.20, "depth": "any"},
      {"type": "directory", "pattern": "aggregates", "weight": 0.15, "depth": "any"},
      {"type": "directory", "pattern": "value_objects", "weight": 0.15, "depth": "any"},
      {"type": "directory", "pattern": "bounded_contexts", "weight": 0.15, "depth": "any"},
      {"type": "file_suffix", "pattern": "_aggregate", "weight": 0.10},
      {"type": "file_suffix", "pattern": "_value_object", "weight": 0.10},
      {"type": "file_suffix", "pattern": "_repository", "weight": 0.05},
      {"type": "package", "names": ["dry-types", "dry-struct", "sequent"], "ecosystem": "gem", "weight": 0.10}
    ],
    "confidence_threshold": 0.40,
    "boundary_rules": {
      "domain": {"forbidden_imports": ["infrastructure", "presentation", "application"]},
      "application": {"forbidden_imports": ["infrastructure", "presentation"]}
    }
  }
}
```

### Esquema de lenguaje (ejemplo)

```json
{
  "ruby": {
    "name": "Ruby",
    "extensions": [".rb", ".erb", ".rake", ".gemspec", ".ru"],
    "markers": ["Gemfile", "Rakefile", ".ruby-version", ".ruby-gemset"],
    "project_type": "ruby",
    "package_managers": [
      {"file": "Gemfile", "lock": "Gemfile.lock", "tool": "bundler"}
    ],
    "naming": {
      "files": "snake_case",
      "classes": "PascalCase",
      "methods": "snake_case",
      "constants": "UPPER_SNAKE",
      "modules": "PascalCase"
    },
    "comment_style": "#",
    "import_pattern": "^(?:require|require_relative|include|extend)\\s+['\"]?([\\w/.]+)",
    "class_pattern": "(?:class|module)\\s+(\\w+)",
    "function_pattern": "def\\s+(\\w+)",
    "constant_pattern": "^\\s*([A-Z][A-Z_0-9]+)\\s*=",
    "frameworks": {
      "rails": {
        "markers": ["config/routes.rb", "app/controllers", "bin/rails"],
        "src_roots": ["app", "lib"],
        "dir_exclusions": [".bundle", "tmp", "log", "storage"]
      }
    }
  }
}
```

---

## Diagrama de Evolucion

```
v0.4.0 (HOY)                    v0.5.0                        v0.6.0
┌──────────────┐    ┌───────────────────────┐    ┌──────────────────────┐
│ Scanners     │    │ Knowledge Registry    │    │ Embeddings           │
│ (hardcoded)  │ →  │ (JSON + Registry API) │ →  │ (local, cached)      │
│              │    │                       │    │                      │
│ 9 archs      │    │ 15+ archs (scoring)   │    │ Semantic ranking     │
│ 13 extensions │    │ 20+ langs, 300+ pkgs  │    │ Hybrid strategies    │
│ 138 packages  │    │ Signal scorer         │    │ Templates generativos│
└──────────────┘    └───────────────────────┘    └──────────────────────┘
                              │
                    v0.8.0    │    v0.8.0              v1.0.0
              ┌──────────────┐│┌──────────────┐  ┌──────────────┐
              │ Multi-dominio│││ Multi-agente │  │ API estable  │
              │ Research     │││ Governance   │  │ 500+ tests   │
              │ Data Science │││ Locks        │  │ Plugin system│
              │ Docs         │││ Conflicts    │  │ Semver       │
              └──────────────┘│└──────────────┘  └──────────────┘
```

---

## Calendario Tentativo

| Version | Scope | Estimado |
|---------|-------|----------|
| v0.5.0 | Knowledge Registry | Siguiente release |
| v0.6.0 | IA opcional | Despues de v0.5.0 validado |
| v0.8.0 | Dominios multiples | Despues de primer proyecto research |
| v0.8.0 | Gobernanza | Despues de uso multi-agente real |
| v1.0.0 | Estabilidad | Cuando API se congele |

Sin fechas absolutas. Cada version se libera cuando los criterios de salida se cumplen.

---

## Definicion de Exito

El roadmap sera correcto si Loom termina haciendo esto:

- **v0.5.0**: `loom init` en un proyecto Ruby on Rails DDD detecta lenguaje, framework, y arquitectura correctamente
- **v0.6.0**: `loom bundle "auth" --ai local` produce un bundle 30% mas relevante que heuristic-only
- **v0.8.0**: `loom init` en una tesis doctoral genera contexto util para un agente de IA
- **v0.8.0**: dos agentes trabajan en el mismo repo sin pisarse
- **v1.0.0**: la API no rompe entre minor versions
