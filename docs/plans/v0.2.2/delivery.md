---
type: delivery
version: "0.2.2"
status: in-progress
prerequisite: "0.2.1"
scope: generator, cli
languages: [python]
patterns: [strategy, builder, manifest]
---

# v0.2.2 — Bundles, Manifests y Handoff

## TL;DR

Introduce contexto minimo por tarea: `loom bundle "refactorizar auth"` genera solo el contexto relevante para esa tarea, con un manifest trazable. Agrega handoff para retomar trabajo entre sesiones. Todo determinista, sin IA.

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

El prompt global es util pero demasiado amplio:

- consume mas tokens de los necesarios
- mezcla contexto importante con accesorio
- no hay handoff estructurado entre sesiones
- retomar una tarea requiere reexplicar todo el estado

## Analogia

**Antes:** Loom te da el libro completo del proyecto. Aunque solo necesites el capitulo de autenticacion, tienes que leer (o pagar tokens por) todo.

**Despues:** Loom te da exactamente las paginas que necesitas para tu tarea, con un indice que dice de donde vino cada pagina y por que se incluyo.

- `prompt` = el libro completo
- `bundle` = las paginas relevantes para tu tarea
- `manifest` = el indice con trazabilidad
- `handoff` = un resumen para quien retome el trabajo

---

## Que cambia

### Comandos nuevos

| Comando | Proposito |
|---------|-----------|
| `loom bundle "refactorizar auth"` | Genera contexto minimo por tarea |
| `loom handoff "refactorizar auth"` | Resumen para retomar trabajo |
| `loom doctor` | Verificacion de salud del setup |

### Output

```
.context/bundles/<slug>/
  bundle.md          # contexto compilado para la tarea
  manifest.json      # metadata trazable (git SHA, strategy, sources)
  sources.json       # archivos incluidos y razon de inclusion

.context/handoffs/
  <slug>.md          # resumen para retomar
```

### Heuristicas de seleccion (sin IA)

| Estrategia | Que busca |
|-----------|-----------|
| Lexical match | Nombres de archivos/dirs que coincidan con la tarea |
| Architecture proximity | Capas y boundaries relacionados |
| Doc classification | Docs tipo plan, architecture, spec cercanos al tema |
| Import graph | Archivos importados desde el area afectada |
| Rule matching | Quick rules relevantes para la tarea |

---

## Patrones de diseno

| Patron | Donde | Por que |
|--------|-------|---------|
| **Strategy** | `selector/strategies/heuristic.py` | Intercambiar heuristicas sin cambiar el pipeline |
| **Builder** | Bundle assembly | Construir el bundle paso a paso (candidatos → filtro → ranking → cut) |
| **Manifest** | `manifest.json` | Registro inmutable de que se incluyo, por que y cuando |
| **Chain of Responsibility** | Heuristicas en cascada | Cada heuristica agrega score, la siguiente refina |

---

## Estructura de archivos

### Nuevos

```
src/loom_context/
  selector/
    __init__.py
    strategies/
      __init__.py
      heuristic.py      # Strategy: seleccion por heuristicas
    bundle.py            # Builder: genera bundle.md
    manifest.py          # Manifest: genera manifest.json
    models.py            # SelectionCandidate, SelectionReason
```

---

## Entregables

- [x] `selector/strategies/heuristic.py`
- [x] `selector/bundle.py`
- [x] `selector/models.py` (SelectionCandidate, SelectionReason, BundleManifest)
- [x] CLI: `loom bundle`
- [x] 5 tests de bundle (stdout, save, no context, smaller than prompt, manifest)
- [ ] CLI: `loom handoff`
- [ ] CLI: `loom doctor`
- [ ] `.context/handoffs/<slug>.md`
- [ ] tests de handoff

## Criterios de salida

- Bundle menor que el prompt global por defecto
- Reproducible con mismo git SHA y misma tarea
- Manifest incluye razon de inclusion por cada archivo
- Sin regresiones en CLI existente
- Tests cubriendo proyectos vacios, con docs, y con multiples capas

## Dependencias nuevas

Ninguna.

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Heuristicas demasiado simples | Nunca excluir `quick_rules` relevantes |
| Bundles demasiado pequenos | Inclusion minima de reglas + arquitectura |
| Crecimiento desordenado del CLI | Modularizado desde v0.2.1, un archivo por comando |
