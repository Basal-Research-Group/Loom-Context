---
type: delivery
version: "0.3.0"
status: planned
prerequisite: "0.2.0"
scope: TBD
languages: [python]
---

# v0.3.0 — Scope por definir

> Basado en feedback de uso real en Akana, Loom-Context y core_monorepo_enn.

## TL;DR

Esta version se define DESPUES de usar v0.2.0 en proyectos reales. No antes.

## Areas candidatas (de la sesion de desarrollo)

- Analisis profundo de arquitecturas mixtas (Akana tiene 3 mezcladas)
- Naming por dominio (50% confianza en Akana — PascalCase vs camelCase)
- Categorizacion de violaciones (109 todas genericas "layer-boundary")
- Metricas de salud por capa (archivos, balance, deuda)
- `.loom/reports/` para analytics de uso
- Observabilidad: Python logging, timing por scanner
- Templates editables para prompt/bundle/handoff
- Embeddings opcionales (si heuristicas no alcanzan)

## Como definir el scope

Usa Loom diario en tus proyectos. Cuando algo falle o falte:

```bash
loom log "el bundle no incluyo X que necesitaba" -p .
loom decide "necesito metricas por capa" -r "razon" -s architecture
```

Despues de 1-2 semanas, revisa:

```bash
loom log --show -p .
loom decide --show -p .
```

Esas notas son el scope real de v0.3.0.

## Entregables

Pendiente de definir.

## Proyectos de prueba

- Akana: /Users/joseruiz/Documents/Code/ReactNative/akana/
- Monorepo: /Users/joseruiz/Documents/Code/MONOREPOS/scripts_core/core_monorepo_enn/
- Loom-Context: este proyecto
