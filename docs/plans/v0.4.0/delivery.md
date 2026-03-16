# v0.4.0 — Export a Agentes y Watch Incremental

> Estado: PLANIFICADO
> Prerequisito: v0.3.0 o al menos v0.2.2 funcional

## Problema que resuelve

El ultimo tramo entre Loom y el agente (Claude, Codex, Cursor) sigue siendo manual. Watch es polling completo, no incremental.

## Que cambia

### Export directo a agentes

```bash
loom export --agent codex .
loom export --agent cursor .
loom export --agent claude .
loom export --agent generic .
```

Genera snippets o archivos listos para cada agente en su formato preferido.

### Watch incremental

```bash
loom watch --events .
```

En vez de re-escanear todo cada N segundos, detecta cambios de archivo y actualiza solo lo necesario.

### Workspace humano opcional

```bash
loom workspace init .
```

```text
context/
  specs/
  architecture/
  decisions/
  knowledge/
  prompts/
  agents/
```

Material humano opcional que Loom puede indexar pero no genera.

## Entregables

- [ ] `loom export --agent codex|cursor|claude|generic`
- [ ] `loom watch --events` (file system events, no polling)
- [ ] `loom workspace init` (opcional)
- [ ] invalidacion de bundles stale
- [ ] snippets listos para al menos 2 agentes

## Criterios de salida

- export claro a 2+ agentes
- watch mas eficiente que polling
- workspace util pero no requerido

## Reglas

- `.context/` sigue siendo generado por Loom
- `.loom/` absorbe cache, sesiones y estado incremental
- `context/` es material humano opcional
- manifests enlazan ambos mundos, no los mezclan

## Dependencias nuevas

Posiblemente `watchfiles` para watch incremental (ligero, sin deps pesadas).
