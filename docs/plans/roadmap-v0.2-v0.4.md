# Roadmap v0.2 - v0.4

> Objetivo: evolucionar Loom-Context desde generador global de `.context/` hacia compilador de contexto por tarea, sin perder su nucleo deterministic-first ni convertirlo en un editor de markdown.

## Resumen Ejecutivo

La siguiente etapa del producto no debe enfocarse en "mas comandos por si acaso", sino en resolver un problema concreto:

- hoy Loom genera buen contexto global
- falta entregar contexto minimo y util por tarea
- falta handoff entre sesiones/agentes
- falta una capa de integracion mas ergonomica para uso diario

La secuencia correcta es:

1. endurecer contratos y arquitectura interna
2. mejorar valor con heuristicas y manifests reproducibles
3. agregar retrieval local opcional
4. integrar export y workspace complementario
5. medir antes de introducir mas IA o complejidad

## Principios de Producto

- Loom sigue siendo analisis automatico del repo
- `.context/` sigue siendo el output canonico
- la IA es una capa opcional de seleccion y sintesis
- todos los outputs nuevos deben poder trazarse a un `git SHA`
- el sistema debe seguir funcionando offline
- el modo sin modelo debe ser util por si mismo

## Problemas Actuales

### 1. El prompt global es util, pero demasiado amplio

Impacto:

- consume mas tokens de los necesarios
- mezcla contexto importante con contexto accesorio
- obliga al usuario a filtrar mentalmente

### 2. No existe handoff estructurado

Impacto:

- retomar tareas requiere reexplicar estado
- cada agente o sesion recompone el contexto manualmente

### 3. Falta integracion operacional con agentes

Impacto:

- el repo genera contexto, pero el ultimo tramo hasta Codex/Cursor/u otros sigue siendo manual

### 4. `watch` todavia es polling completo

Impacto:

- trabajo innecesario
- peor experiencia para proyectos medianos o grandes

## Vision de Salida

Al final de v0.4, Loom deberia poder:

- generar bundles minimos por tarea
- producir handoffs reutilizables
- exportar contexto a agentes comunes
- mantener manifests reproducibles
- usar retrieval local opcional para mejorar seleccion
- seguir funcionando de manera determinista sin depender de un LLM

## Prerrequisito - Hardening arquitectonico

Antes de ampliar capacidades, Loom necesita una base mas explicita para escalar sin volver fragil el core.

Documento de referencia:

- [architecture-hardening-plan.md](./architecture-hardening-plan.md)

### Objetivos

- contratos tipados para resultados y manifests
- modularizacion del CLI
- separacion entre output canonico y estado efimero
- puertos y pipelines para agregar nuevas capabilities

### Entregables minimos

- [ ] modelos tipados para `ScanResult` y artefactos futuros
- [ ] extraccion de casos de uso fuera del CLI
- [ ] registry o factory para scanners/generators
- [ ] decision formal sobre `.context/`, `.loom/` y `context/`

### Criterio de salida

Las siguientes features deben poder entrar sin crecer por condicionantes ad hoc en `engine.py` o `cli.py`.

## v0.2 - Bundles, manifests y handoff

### Meta

Introducir el concepto de "unidad de contexto por tarea" sin incorporar todavia modelos locales.

### Entregables de CLI

- [ ] `loom bundle "<task>"`
- [ ] `loom handoff "<task>"`
- [ ] `loom doctor`

### Entregables de output

- [ ] `.context/bundles/<slug>/bundle.md`
- [ ] `.context/bundles/<slug>/manifest.json`
- [ ] `.context/bundles/<slug>/sources.json`
- [ ] `.context/handoffs/<slug>.md`

### Contenido minimo de `manifest.json`

- [ ] `task`
- [ ] `slug`
- [ ] `git_sha`
- [ ] `generated_at`
- [ ] `loom_version`
- [ ] `selection_strategy`
- [ ] `included_files`
- [ ] `included_docs`
- [ ] `included_rules`
- [ ] `warnings`

### Heuristicas iniciales

- coincidencia lexical con nombres de archivos
- coincidencia con nombres de directorios
- proximidad con reglas de arquitectura
- documentos clasificados como `plan`, `architecture`, `specification`
- archivos importados desde el area afectada
- boost a archivos bajo `src/` y docs cercanos al tema

### Alcance tecnico

- nuevo paquete `src/loom_context/selector/`
- `strategies/heuristic.py`
- `bundle.py`
- `manifest.py`
- `models.py` o contratos equivalentes
- tests especificos para seleccion y manifests
- tests de contrato para serializacion y trazabilidad

### Criterios de salida

- bundle de tamano menor al prompt global por defecto
- reproducibilidad con el mismo `git SHA`
- sin regresiones en CLI existente
- tests de bundle y handoff cubriendo proyectos vacios y proyectos con docs

### Riesgos

- heuristicas demasiado simples que no reduzcan ruido
- bundles demasiado pequenos que omitan reglas criticas
- crecimiento desordenado del CLI

### Mitigacion

- nunca excluir `quick_rules` relevantes
- incluir trazabilidad de por que cada archivo entro al bundle
- limitar el MVP a texto + manifest, sin interfaz adicional
- construir la feature sobre contratos tipados, no sobre nuevos `dict` anonimos

## v0.3 - Retrieval local opcional

### Meta

Mejorar la precision de seleccion con modelos abiertos ejecutados localmente, manteniendo fallback al modo heuristico.

### Entregables de CLI

- [ ] `loom bundle "<task>" --ai off|local`
- [ ] `loom bundle "<task>" --top-k N`
- [ ] `loom bundle "<task>" --token-budget N`

### Entregables tecnicos

- [ ] `selector/strategies/hybrid.py`
- [ ] `infrastructure/ai/embeddings.py`
- [ ] cache local de embeddings
- [ ] ranking hibrido heuristico + semantico
- [ ] invalidacion incremental del cache
- [ ] mediciones baseline vs embeddings

### Flujo esperado

1. heuristicas producen candidatos
2. embeddings ordenan semanticamente
3. se corta por `top-k` o `token-budget`
4. se genera bundle con razones de inclusion

### Modelos candidatos

- `sentence-transformers/all-MiniLM-L6-v2`
- `BAAI/bge-m3`

### Criterios de salida

- mejora medible de precision@k frente al baseline heuristico
- tiempo aceptable para proyectos medianos
- modo `--ai off` sigue funcionando sin instalar extras

### Riesgos

- dependencia excesiva de librerias pesadas
- tiempos altos de indexado
- bundles aparentemente mas "inteligentes" pero menos reproducibles

### Mitigacion

- extras opcionales en `pyproject.toml`
- cache persistente
- registrar score y estrategia usada en `manifest.json`
- adapter aislado para proveedores de embeddings

## v0.4 - Export a agentes, workspace y watch incremental

### Meta

Reducir friccion de adopcion diaria sin desplazar el centro del producto.

### Entregables de CLI

- [ ] `loom export --agent codex|cursor|generic`
- [ ] `loom workspace init`
- [ ] `loom watch --events`

### Entregables funcionales

- [ ] snippets o archivos listos para agentes comunes
- [ ] workspace opcional `context/`
- [ ] actualizacion incremental por eventos de archivo
- [ ] invalidacion de bundles stale
- [ ] mantener `.context/` como salida canonica reproducible
- [ ] mantener `.loom/` como estado no canonico

### Estructura inicial del workspace

- `context/specs/`
- `context/architecture/`
- `context/decisions/`
- `context/knowledge/`
- `context/prompts/`
- `context/agents/`

### Criterios de salida

- export claro a por lo menos 2 agentes
- `watch` mas eficiente que polling
- workspace util pero no requerido para usar Loom

### Riesgos

- imitar demasiado a herramientas de markdown-centric workspace
- confundir `.context/` con `context/`
- introducir dos fuentes de verdad

### Mitigacion

- `.context/` sigue siendo generado por Loom
- `.loom/` absorbe cache, sesiones y estado incremental
- `context/` es material humano opcional
- manifests enlazan ambos mundos, no los mezclan

## Evals y Telemetria Local

### Dataset minimo

- [ ] 10 tareas reales
- [ ] archivos esperados por tarea
- [ ] docs esperados por tarea
- [ ] reglas esperadas por tarea

### Metricas

- [ ] precision@k
- [ ] recall@k
- [ ] tamano del bundle
- [ ] tiempo de generacion
- [ ] utilidad del handoff

### Regla

No introducir fine-tuning ni LoRA antes de tener este baseline.

## Dependencias y Packaging

### Core

- el paquete base no debe requerir modelos ni torch

### Extras propuestos

- `loom-context[local-ai]`
- `loom-context[dev]`

### Objetivo

Mantener instalacion base ligera para adopcion simple.

## Orden de Implementacion Recomendado

1. `bundle`
2. `manifest.json`
3. `handoff`
4. `doctor`
5. evals baseline
6. embeddings locales opcionales
7. export a agentes
8. workspace opcional
9. watch incremental

## Definicion de Exito

El roadmap sera correcto si Loom termina haciendo esto mejor que hoy:

- menos contexto, mas relevante
- menor friccion para retomar trabajo
- mejor handoff entre agentes
- sin perder trazabilidad ni depender de servicios externos
