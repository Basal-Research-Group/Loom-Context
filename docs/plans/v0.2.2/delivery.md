---
type: delivery
version: "0.2.2"
status: planned
prerequisite: "0.2.1"
scope: generator, cli
languages: [python]
---

# v0.2.2 — Bundles, Manifests y Handoff

> Estado: PLANIFICADO
> Prerequisito: v0.2.1 (contratos tipados)
> Referencia: [roadmap-v0.2-v0.4.md](../roadmap-v0.2-v0.4.md)

## Problema que resuelve

El prompt global es util pero demasiado amplio:

- consume mas tokens de los necesarios
- mezcla contexto importante con accesorio
- no hay handoff estructurado entre sesiones

## Que cambia

### Contexto por tarea

```bash
loom bundle "refactorizar auth" .
```

Genera un paquete minimo con solo el contexto relevante para esa tarea.

### Comandos nuevos

| Comando | Proposito |
|---------|-----------|
| `loom bundle "<task>"` | Contexto minimo por tarea |
| `loom handoff "<task>"` | Resumen para retomar trabajo |
| `loom doctor` | Verificacion de salud del setup |

### Output

```text
.context/bundles/<slug>/
  bundle.md          # contexto compilado para la tarea
  manifest.json      # metadata trazable
  sources.json       # archivos incluidos y razon

.context/handoffs/
  <slug>.md          # resumen para retomar
```

### manifest.json

```json
{
  "task": "refactorizar auth",
  "slug": "refactorizar-auth",
  "git_sha": "abc1234",
  "generated_at": "2026-03-20T...",
  "loom_version": "0.2.2",
  "selection_strategy": "heuristic",
  "included_files": [...],
  "included_docs": [...],
  "included_rules": [...],
  "warnings": [...]
}
```

### Heuristicas de seleccion (sin IA)

- coincidencia lexical con nombres de archivos
- coincidencia con directorios
- proximidad con reglas de arquitectura
- documentos tipo plan, architecture, specification
- archivos importados desde el area afectada
- boost a archivos bajo src/ y docs cercanos al tema

## Entregables

- [ ] `selector/strategies/heuristic.py`
- [ ] `selector/bundle.py`
- [ ] `selector/manifest.py`
- [ ] `selector/models.py` (sobre contratos de v0.2.1)
- [ ] CLI: `loom bundle`, `loom handoff`, `loom doctor`
- [ ] tests de seleccion y manifests
- [ ] tests de contrato para serializacion

## Criterios de salida

- bundle menor que el prompt global
- reproducible con mismo git SHA
- sin regresiones
- tests cubriendo proyectos vacios y con docs

## Dependencias nuevas

Ninguna.
