---
type: guide
audience: contributor
---

# Formato Estandar de Documentos para Loom

## TL;DR

Todos los documentos del proyecto siguen un formato consistente con frontmatter YAML, seccion TL;DR, indice, analogias y patrones de diseno explicitos. Esto permite que Loom extraiga metadata estructurada y que cualquier persona (o agente) entienda el proyecto rapido.

---

## Indice

- [Reglas generales](#reglas-generales)
- [Secciones obligatorias por tipo](#secciones-obligatorias-por-tipo)
- [Frontmatter YAML](#frontmatter-yaml)
- [Reglas de escritura](#reglas-de-escritura)
- [Templates por tipo](#templates-por-tipo)

---

## Reglas generales

### Todo documento debe tener

1. **Frontmatter YAML** — metadata parseable por Loom
2. **TL;DR** — 2-3 lineas que resuman todo. Si alguien solo lee esto, debe entender de que va
3. **Indice** — enlaces a secciones principales (si tiene mas de 3 secciones)
4. **Analogia** — donde aplique, una comparacion con algo cotidiano que aclare el concepto
5. **Patrones de diseno** — si el documento describe arquitectura o implementacion, nombrar patrones explicitos
6. **Nombres claros** — sin ambiguedades, usar los mismos terminos que el codigo

### Reglas de escritura

- **Usa analogias**: "El engine es como un director de orquesta: no toca instrumentos, coordina a los que tocan"
- **Nombra patrones**: no digas "una cosa que selecciona", di "Strategy pattern para seleccion"
- **Se directo**: primera oracion = conclusion. Despues justifica
- **Sin jerga innecesaria**: si un termino tiene equivalente comun, usa el comun primero
- **Checklists sobre parrafos**: para entregables y criterios, siempre usar `- [ ]` o `- [x]`
- **Tablas sobre listas largas**: si comparas 3+ cosas, usa tabla
- **Codigo sobre descripcion**: si puedes mostrar un comando o estructura, hazlo

---

## Frontmatter YAML

```yaml
---
type: delivery | architecture | roadmap | scope | guide | decision | contributing | security | changelog | code-of-conduct
version: "0.2.0"           # solo para delivery
status: planned | in-progress | released | deferred
prerequisite: "0.1.0"      # solo para delivery
scope: engine, cli, scanner, generator, auditor, infra
languages: [python]
patterns: [clean-architecture, strategy, registry]
audience: developer | user | contributor
---
```

Campos opcionales segun tipo. Solo `type` es obligatorio.

---

## Secciones obligatorias por tipo

### Delivery (plan por version)

| Seccion | Obligatoria | Descripcion |
|---------|-------------|-------------|
| TL;DR | Si | 2-3 lineas: que, por que, impacto |
| Indice | Si (si > 3 secciones) | Links a secciones |
| Problema que resuelve | Si | Que dolor o gap existe hoy |
| Analogia | Si | "Es como..." para explicar el cambio |
| Que cambia | Si | Descripcion tecnica con subsecciones |
| Patrones de diseno | Si (si aplica) | Que patrones se usan y por que |
| Estructura de archivos | Si | Que archivos se crean/modifican |
| Entregables | Si | Checklist con `- [ ]` |
| Criterios de salida | Si | Como saber que esta lista |
| Dependencias nuevas | Si | Ninguna, o listado explicito |
| Riesgos | Opcional | Que puede salir mal |

### Architecture

| Seccion | Obligatoria |
|---------|-------------|
| TL;DR | Si |
| Indice | Si |
| Analogia | Si |
| Estado actual | Si |
| Arquitectura objetivo | Si |
| Principios de diseno | Si |
| Patrones de diseno | Si (nombrados: Strategy, Registry, etc.) |
| Anti-patrones | Si |
| Secuencia de implementacion | Si |
| Criterio de exito | Si |

### Scope

| Seccion | Obligatoria |
|---------|-------------|
| TL;DR | Si |
| Que es (con analogia) | Si |
| Para que sirve bien | Si |
| Para que NO sirve | Si |
| Limites del analisis | Si |
| Direccion futura | Opcional |

### Contributing

| Seccion | Obligatoria |
|---------|-------------|
| TL;DR | Si |
| Setup | Si |
| Estructura del proyecto | Si |
| Convenciones de codigo | Si |
| Testing | Si |
| Git conventions | Si |
| PR process | Si |

### Guide / How-to

| Seccion | Obligatoria |
|---------|-------------|
| TL;DR | Si |
| Prerequisitos | Si |
| Pasos | Si |
| Verificacion | Si |
| Troubleshooting | Opcional |

### Decision Record

| Seccion | Obligatoria |
|---------|-------------|
| TL;DR | Si |
| Contexto | Si |
| Decision | Si |
| Consecuencias | Si |
| Alternativas | Opcional |

### Changelog

| Seccion | Obligatoria |
|---------|-------------|
| Keep a Changelog format | Si |
| Unreleased al inicio | Si |
| Added/Changed/Removed/Fixed | Si |

### Security / Code of Conduct

Formato estandar de la industria. Solo agregar frontmatter y TL;DR.

---

## Templates por tipo

### Template: Delivery

```markdown
---
type: delivery
version: "X.Y.Z"
status: planned
prerequisite: "X.Y.Z"
scope: engine, cli
languages: [python]
patterns: [strategy, registry]
---

# vX.Y.Z — Titulo corto

## TL;DR

[2-3 lineas: que entrega, que problema resuelve, impacto principal]

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Que cambia](#que-cambia)
- [Patrones de diseno](#patrones-de-diseno)
- [Entregables](#entregables)
- [Criterios de salida](#criterios-de-salida)

## Problema que resuelve

[Que dolor existe hoy]

## Analogia

[Comparacion cotidiana que aclare el concepto]

## Que cambia

[Descripcion tecnica]

## Patrones de diseno

[Que patrones se usan: Strategy, Registry, Adapter, etc. y por que]

## Estructura de archivos

[Que se crea/modifica]

## Entregables

- [ ] entregable 1
- [ ] entregable 2

## Criterios de salida

[Como saber que esta listo]

## Dependencias nuevas

Ninguna.

## Riesgos

[Opcional]
```

### Template: Architecture

```markdown
---
type: architecture
languages: [python]
patterns: [clean-architecture, strategy]
---

# [Titulo]

## TL;DR

[2-3 lineas]

## Indice

## Analogia

## Estado actual

## Arquitectura objetivo

## Principios de diseno

## Patrones de diseno

[Strategy, Registry, Factory, Adapter, etc. — nombrados y explicados]

## Anti-patrones a evitar

## Secuencia de implementacion

## Criterio de exito
```

---

## Convenciones de nombres en documentos

| Concepto | Nombre correcto | No usar |
|----------|----------------|---------|
| Carpeta canonico | `.context/` | "context folder", "output" |
| Carpeta operativa | `.loom/` | "state folder", "cache" |
| Analisis del repo | scan | "parse", "read" |
| Generacion de contexto | generate | "build", "create" |
| Verificacion de reglas | audit | "check", "validate" |
| Re-analisis + persistencia | enrich | "refresh", "update" |
| Seleccion por tarea | bundle | "filter", "subset" |
| Resumen para retomar | handoff | "summary", "report" |
| Registro de decision | decision record | "ADR", "note" |
| Hallazgo del audit | finding | "violation", "issue" |
| Cambio al contexto | mutation | "update", "change" |

---

## Como lo usa Loom

### Hoy (v0.2.0)

El docs scanner extrae:
- titulo (primer H1)
- secciones (H2, H3)
- status items (checkboxes `[x]`/`[ ]`, tablas con done/pending)
- tipo (por path y contenido)

### Futuro (v0.2.1+)

Con frontmatter parsing:
- `type` → clasificacion precisa
- `version` → dependency graph entre deliveries
- `status` → dashboard de progreso
- `scope` → mejor seleccion en focus/bundle
- `languages` → contexto por lenguaje
- `patterns` → matching con arquitectura detectada
- `prerequisite` → orden de implementacion

### Regla

El frontmatter es opcional. Docs sin frontmatter siguen funcionando con heuristicas. Pero docs con frontmatter dan mejor contexto.

---

## Ciclo de vida de un delivery

| Fase | status en frontmatter | Entregables | Accion |
|------|----------------------|-------------|--------|
| Creacion | `planned` | Todos `- [ ]` | Escribir plan |
| Implementacion | `in-progress` | Se van marcando `- [x]` | Desarrollar |
| Release | `released` | Todos `- [x]` | Merge + tag + PyPI |
| Archivo | `archived` | No se modifica | Mover a `docs/plans/archive/vX.Y.Z/` |

### Reglas de archivado

- Un delivery se archiva cuando la **siguiente** version se publica
- Un delivery archivado es un registro historico — no se modifica
- El frontmatter cambia a `status: archived`
- Se mueve a `docs/plans/archive/vX.Y.Z/delivery.md`

### Progress en frontmatter

Agregar campo `progress` para tracking rapido:

```yaml
---
type: delivery
version: "0.2.0"
status: in-progress
progress: 12/12
---
```

Actualizar manualmente al marcar entregables.

---

## Template: Plan Multiagente

Cuando un delivery tiene tareas que pueden ejecutarse en paralelo por diferentes agentes, usar este formato. Es distinto al delivery simple porque cada tarea debe ser autocontenida.

```markdown
---
type: delivery
version: "X.Y.Z"
status: planned
prerequisite: "X.Y.Z"
scope: scanner, cli, infra
languages: [python]
progress: 0/N
---

# vX.Y.Z — Titulo

## TL;DR

[2-3 lineas]

## Indice

## Problema que resuelve

## Analogia

## Tareas

### Tarea N: Nombre

- **Status:** `- [ ]` pendiente | `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** [lista de archivos que PUEDE tocar]
- **No tocar:** [lista de archivos que NO debe tocar]

**Problema:** [que resuelve esta tarea especificamente]

**Entregables:**
- [ ] entregable 1
- [ ] entregable 2

**Criterio de salida:** [como saber que esta tarea esta lista]

## Mapa de Independencia

[Tabla mostrando que ninguna tarea comparte archivos con otra]

## Criterios de Salida (version completa)

- [ ] Tarea 1 completada
- [ ] Tarea 2 completada
- [ ] Tests pasan (meta: mantener cobertura)
- [ ] Probado en proyectos reales
```

### Reglas del template multiagente

- Cada tarea lista archivos a tocar Y archivos a NO tocar
- Ninguna tarea comparte archivos con otra (excepto triviales como cli/__init__.py)
- Cada tarea tiene su propio criterio de salida independiente
- Un agente puede tomar una tarea sin leer las demas
- El mapa de independencia es obligatorio — si hay conflictos, redisenar las tareas
