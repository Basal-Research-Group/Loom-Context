---
type: delivery
version: "0.3.0"
status: archived
progress: 5/7
prerequisite: "0.2.2"
scope: cli, infra
languages: [python]
patterns: [adapter, observer, facade]
---

# v0.3.0 — Export a Agentes y Watch Incremental

## TL;DR

Reduce la friccion entre Loom y agentes externos (Claude, Codex, Cursor). Export genera contexto listo para cada agente en su formato. Watch deja de re-escanear todo y solo actualiza lo que cambio.

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Que cambia](#que-cambia)
- [Patrones de diseno](#patrones-de-diseno)
- [Entregables](#entregables)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

El ultimo tramo entre Loom y el agente es manual: copiar/pegar prompt, configurar archivos, re-escanear todo cada vez. Watch hace polling completo, desperdiciando trabajo en proyectos que apenas cambian.

## Analogia

**Export:** hoy Loom genera un informe generico. Pero cada agente "habla" diferente — Claude quiere system prompt, Cursor quiere .cursorrules, Codex quiere archivos especificos. Export es como un traductor que adapta el mismo informe al idioma de cada agente.

**Watch incremental:** hoy Loom re-escanea toda la casa cada vez. Watch incremental es como tener sensores en las puertas — solo revisa las habitaciones donde algo se movio.

---

## Que cambia

### Export directo a agentes

```bash
loom export --agent claude .     # genera system prompt optimizado
loom export --agent cursor .     # genera .cursorrules
loom export --agent codex .      # genera archivos para Codex
loom export --agent generic .    # formato universal
```

### Watch incremental

```bash
loom watch --events .            # detecta cambios de archivo, no polling
```

### Workspace humano opcional

```bash
loom workspace init .
```

```
context/                         # material humano, NO generado por Loom
  specs/
  architecture/
  decisions/
  knowledge/
```

---

## Patrones de diseno

| Patron | Donde | Por que |
|--------|-------|---------|
| **Adapter** | `exporters/claude.py`, `exporters/cursor.py` | Cada agente tiene su formato; el adapter traduce sin cambiar el core |
| **Observer** | Watch con file system events | Reaccionar a cambios en vez de preguntar periodicamente |
| **Facade** | `loom export` | Un comando, multiples adapters detras |
| **Registry** | Registro de exporters disponibles | Agregar nuevo agente = agregar modulo + registrar |

---

## Entregables

- [x] `loom export --agent claude|cursor|codex|generic` (4 adapters)
- [x] exports write to `.context/exports/` (no overwrite user files)
- [x] Adapter + Registry pattern for extensibility
- [x] 5 tests de export
- [ ] `loom watch --events` (requiere `watchfiles` dep — postergado)
- [ ] `loom workspace init` (opcional — postergado)

## Criterios de salida

- Export claro a 2+ agentes
- Watch mas eficiente que polling
- Workspace util pero no requerido para usar Loom

## Dependencias nuevas

Posiblemente `watchfiles` para watch incremental (ligero, sin deps pesadas).

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Imitar herramientas de workspace | `.context/` sigue siendo generado; `context/` es humano |
| Confundir `.context/` con `context/` | Documentar claramente; Loom nunca toca `context/` |
| Formatos de agente cambian | Adapters aislados; cambiar uno no afecta otros |
