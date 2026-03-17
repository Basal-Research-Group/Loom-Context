---
type: delivery
version: "0.4.0"
status: archived
prerequisite: "0.2.2"
scope: cli, infra
languages: [python]
patterns: [adapter, registry, facade]
progress: 5/5
---

# v0.4.0 — Export a Agentes

## TL;DR

Export genera contexto listo para cada agente en su formato. 4 adapters: Claude, Cursor, Codex, Generic. Flag `--install` escribe donde el agente lo espera.

## Entregables

- [x] `loom export --agent claude|cursor|codex|generic`
- [x] `--install` flag para escribir en raiz del proyecto
- [x] Exports a `.context/exports/` por defecto (no sobreescribe)
- [x] Adapter + Registry pattern para extensibilidad
- [x] 5 tests de export

## Que se postergo

- `loom watch --events` (requiere `watchfiles` dependency)
- `loom workspace init` (opcional, baja prioridad)
