---
type: guide
audience: contributor
---

# Formato Estandar de Documentos para Loom

> Este formato permite que Loom extraiga metadata estructurada de planes, decisiones y documentacion del proyecto.

## Por que un formato

Loom escanea docs y extrae: titulo, secciones, status items. Pero sin estructura consistente, la calidad del contexto depende de como cada autor escriba su markdown.

Con un formato estandar:
- el docs scanner extrae metadata rica
- focus y bundle seleccionan mejor
- el contexto para agentes es mas preciso
- la trazabilidad entre versiones es automatica

## Formato de Delivery (plan por version)

```markdown
---
type: delivery
version: "0.2.0"
status: in-progress | planned | released
prerequisite: "0.1.0"
scope: engine | cli | scanner | generator | auditor | infra
languages: [python]
---

# vX.Y.Z — Titulo corto

> Estado: EN DEVELOP | PLANIFICADO | PUBLICADO

## Problema que resuelve

[1-3 parrafos: que dolor resuelve esta entrega]

## Que cambia

[Descripcion de cambios con subsecciones si es necesario]

## Entregables

- [ ] entregable pendiente
- [x] entregable completado

## Criterios de salida

[Como saber que esta version esta lista]

## Dependencias nuevas

[Ninguna, o listado explicito]

## Riesgos

[Opcional: que puede salir mal y como mitigarlo]
```

## Formato de Decision Record

```markdown
---
type: decision
scope: architecture | naming | deps | security | product
status: accepted | superseded | deprecated
date: 2026-03-16
---

# DR-NNN: Titulo de la decision

## Contexto

[Que situacion motiva la decision]

## Decision

[Que se decidio]

## Consecuencias

[Que implica esta decision para el futuro]

## Alternativas consideradas

[Opcional: que otras opciones habia]
```

## Formato de Scope / Definicion de Producto

```markdown
---
type: scope
---

# Scope de [Producto]

## Que es

## Para que sirve bien

## Para que NO sirve

## Principio

## Direccion futura
```

## Formato de Arquitectura

```markdown
---
type: architecture
languages: [python, typescript]
patterns: [clean-architecture, hexagonal]
---

# Arquitectura de [Proyecto]

## Estado actual

## Arquitectura objetivo

## Principios de diseno

## Capas / Modulos

## Anti-patrones a evitar
```

## Formato de Roadmap

```markdown
---
type: roadmap
versions: ["0.2.0", "0.2.1", "0.2.2", "0.3.0", "0.4.0"]
---

# Roadmap [Rango]

## Estado actual

[Tabla con versiones y estados]

## Principios de producto

## [Version] — [Titulo]

[Para cada version, resumen breve con link a delivery.md]
```

## Formato de Guia / How-to

```markdown
---
type: guide
audience: developer | user | contributor
languages: [python]
---

# [Titulo de la guia]

## Prerequisitos

## Pasos

## Verificacion
```

## Como lo usa Loom

### Hoy (v0.2.0)

El docs scanner extrae:
- titulo (primer H1)
- secciones (H2, H3)
- status items (checkboxes, tablas con done/pending)
- tipo (por path y contenido)

### Futuro (v0.2.1+)

Con frontmatter parsing, el scanner extraera:
- `type` → clasificacion mas precisa
- `version` → dependency graph entre deliveries
- `status` → dashboard de progreso real
- `scope` → mejor seleccion en focus/bundle
- `languages` → contexto por lenguaje
- `patterns` → matching con arquitectura detectada
- `prerequisite` → orden de implementacion

### Que no cambia

- el frontmatter es opcional
- docs sin frontmatter siguen funcionando con heuristicas
- Loom nunca modifica los docs del usuario
- el formato no es obligatorio, es recomendado

## Lenguajes de programacion

Loom detecta lenguajes por archivos marcador:

| Lenguaje | Marcadores |
|----------|-----------|
| Python | pyproject.toml, setup.py, requirements.txt |
| TypeScript | tsconfig.json, package.json + ts deps |
| JavaScript | package.json |
| Rust | Cargo.toml |
| Go | go.mod |
| Java | pom.xml, build.gradle |
| Kotlin | build.gradle.kts |
| Swift | Package.swift |
| Ruby | Gemfile |
| PHP | composer.json |
| C# | *.csproj, *.sln |

Los templates de `.context/` se adaptan al lenguaje detectado. En el futuro, los delivery docs podran especificar `languages` en frontmatter para dar contexto adicional al scanner.

## Estructura de directorios recomendada

```text
docs/
  plans/
    scope.md                    # que es y que no es el producto
    format.md                   # este documento
    roadmap-vX-vY.md            # overview con links
    architecture-*.md           # planes transversales
    ai-integration-*.md         # estrategias especificas
    vX.Y.Z/
      delivery.md               # plan de entrega por version
  guides/
    quickstart.md
    cli-reference.md
    best-practices.md
    security.md
  architecture/
    overview.md                 # si es necesario separar de plans
```

## Regla general

Los docs son para humanos y agentes. El formato debe ser:

- legible sin herramientas
- parseable por Loom
- util para focus y bundle
- trazable a una version o decision
