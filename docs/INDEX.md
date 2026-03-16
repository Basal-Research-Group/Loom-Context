---
type: guide
audience: developer
---

# Loom-Context — Documentacion

## TL;DR

Loom escanea un repo de software y genera `.context/` con metadata arquitectonica para agentes de IA. Sin IA, sin cloud, sin deps pesadas. 78 tests, 4 dependencias runtime, <2 segundos para 700 archivos.

```bash
pip install loom-context
cd tu-proyecto/
loom init .
```

---

## Indice

- [Mapa de documentos](#mapa-de-documentos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Convenciones](#convenciones)
- [Orden de lectura recomendado](#orden-de-lectura-recomendado)

---

## Mapa de documentos

### Producto y scope

| Documento | Que responde |
|-----------|-------------|
| [Scope](plans/scope.md) | Que es Loom, para que sirve, para que no |
| [Filosofia](guides/philosophy.md) | Por que existe Loom, como opera |
| [Formato de docs](plans/format.md) | Estandar de escritura, frontmatter, analogias |

### Guias de uso

| Documento | Que responde |
|-----------|-------------|
| [Quickstart](guides/quickstart.md) | Como instalar y usar por primera vez |
| [CLI Reference](guides/cli-reference.md) | Todos los comandos con ejemplos |
| [Output .context/](guides/context-output.md) | Que genera Loom y como lo consume la IA |
| [Seguridad](guides/security.md) | Como Loom protege tu codigo |
| [Buenas practicas](guides/best-practices.md) | Patrones recomendados para equipos |
| [Loomy](guides/loomy.md) | La mascota spider-neuron y sus expresiones |

### Planes de entrega (por version)

| Version | Estado | Que entrega | Plan |
|---------|--------|-------------|------|
| v0.1.0 | Publicado | init, scan, prompt, audit, plan, watch | — |
| v0.2.0 | Completado | .loom/, audit en init, enrich, decide | [archive](plans/archive/v0.2.0/delivery.md) |
| v0.2.1 | Completado | Contratos, CLI modular, pipeline, Loomy | [archive](plans/archive/v0.2.1/delivery.md) |
| v0.2.2 | En desarrollo | Bundles + handoff + doctor | [delivery](plans/v0.2.2/delivery.md) |
| v0.3.0 | Planificado | Retrieval local opcional | [delivery](plans/v0.3.0/delivery.md) |
| v0.4.0 | Planificado | Export a agentes + watch incremental | [delivery](plans/v0.4.0/delivery.md) |

### Estrategias transversales

| Documento | Que cubre |
|-----------|-----------|
| [Roadmap v0.2-v0.4](plans/roadmap-v0.2-v0.4.md) | Vision completa con secuencia |
| [Architecture Hardening](plans/architecture-hardening-plan.md) | Refactor: contratos, pipelines, CLI |
| [AI Integration](plans/ai-integration-strategy.md) | Embeddings, ranking, postergado a v0.3.0 |

### Contribucion y comunidad

| Documento | Que cubre |
|-----------|-----------|
| [CONTRIBUTING](../CONTRIBUTING.md) | Setup, convenciones, PR process |
| [CHANGELOG](../CHANGELOG.md) | Historial de cambios por version |
| [SECURITY](../SECURITY.md) | Reporte de vulnerabilidades |
| [CODE_OF_CONDUCT](../CODE_OF_CONDUCT.md) | Reglas de colaboracion |
| [CLAUDE.md](../CLAUDE.md) | Reglas para agentes de IA |

---

## Estructura del proyecto

```
Loom-Context/
  src/loom_context/
    cli.py                 # Comandos Click (init, scan, audit, enrich, decide...)
    engine.py              # Orquestador: scan + generate + audit + enrich
    config.py              # Configuracion (.context/ + .loom/)
    git.py                 # GitHelper: metadata git compartida
    session.py             # .loom/sessions.jsonl
    status.py              # Dashboard de salud del proyecto
    findings.py            # .loom/inconsistencies.json
    decisions.py           # .loom/decisions.jsonl
    mutations.py           # .loom/mutations.jsonl
    security/filter.py     # 3 capas de filtrado (gitignore, contextignore, secrets)
    scanners/
      structure.py         # Tipo de proyecto, arquitectura, arbol de dirs
      deps.py              # Dependencias y categorias
      code.py              # Convenciones de naming
      docs.py              # Indexacion de documentacion
    generators/
      index.py             # index.json (master metadata)
      context.py           # Archivos .context/ via Jinja2
      prompt.py            # Prompt maestro para IA
      focus.py             # Contexto filtrado por tarea
    auditors/
      naming.py            # Convenciones de interfaces
      structure.py         # Boundaries entre capas
    templates/             # Jinja2 templates para .context/ output
  tests/
    conftest.py            # Fixture tmp_project
    test_cli.py            # 78 tests
  docs/
    guides/                # Guias de uso
    plans/                 # Planes de entrega y estrategias
      scope.md             # Que es y que no es Loom
      format.md            # Estandar de escritura
      roadmap-v0.2-v0.4.md
      v0.X.Y/delivery.md  # Un delivery por version
      archive/             # Planes obsoletos
```

### Dos carpetas de output

| Carpeta | Proposito | Quien la genera | En git |
|---------|-----------|----------------|--------|
| `.context/` | Contexto canonico del repo | `loom init/scan` | Opcional |
| `.loom/` | Estado operativo vivo | `loom init/enrich/decide/log` | No (gitignored) |

---

## Convenciones

### Emojis

No usar emojis decorativos. Solo estos funcionales en tablas de status:

| Uso permitido | Ejemplo |
|--------------|---------|
| Checkbox done | `- [x]` |
| Checkbox pending | `- [ ]` |
| En tablas de estado | Texto: "Publicado", "En develop", "Planificado" |

No usar: decorativos, en titulos, en commits, en codigo, en output CLI.

### Nomenclatura en docs

| Concepto | Nombre correcto | No usar |
|----------|----------------|---------|
| Carpeta canonica | `.context/` | "context folder", "output" |
| Carpeta operativa | `.loom/` | "state folder", "cache" |
| Analizar repo | scan | "parse", "read" |
| Generar contexto | generate | "build", "create" |
| Verificar reglas | audit | "check", "validate" |
| Re-analizar + persistir | enrich | "refresh", "update" |
| Seleccionar por tarea | bundle | "filter", "subset" |
| Resumir para retomar | handoff | "summary", "report" |
| Registrar decision | decision record | "ADR", "note" |

### Templates Jinja2

Los templates en `src/loom_context/templates/` son para generar archivos de `.context/` (architecture.md, naming.md, directory-map.md). NO son para documentos de planes ni docs del proyecto. Los docs del proyecto son escritos por humanos siguiendo el formato de [format.md](plans/format.md).

---

## Orden de lectura recomendado

### Si quieres entender Loom

1. Este archivo (INDEX.md)
2. [Scope](plans/scope.md) — que es y que no es
3. [Quickstart](guides/quickstart.md) — como usarlo
4. [CLI Reference](guides/cli-reference.md) — comandos

### Si quieres contribuir

1. [CONTRIBUTING](../CONTRIBUTING.md) — setup y convenciones
2. [Format](plans/format.md) — como escribir docs
3. [CLAUDE.md](../CLAUDE.md) — reglas de codigo
4. [Architecture Hardening](plans/architecture-hardening-plan.md) — hacia donde va el refactor

### Si quieres entender el roadmap

1. [Scope](plans/scope.md)
2. [Roadmap](plans/roadmap-v0.2-v0.4.md) — vision completa
3. Delivery de la version que te interese (`plans/vX.Y.Z/delivery.md`)
