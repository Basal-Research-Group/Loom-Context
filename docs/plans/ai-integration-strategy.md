# Estrategia de Integracion de IA Local

> Objetivo: usar modelos abiertos para mejorar seleccion, resumen y handoff, sin convertir a Loom en una herramienta dependiente de LLMs.

## Decision Principal

La IA no debe reemplazar scanners, generators ni auditors. Debe operar encima de ellos.

Eso significa:

- primero estructura
- luego retrieval
- despues sintesis opcional

No al reves.

## Donde Agrega Valor la IA

### Seleccion

Cuando el usuario pide:

- "quiero trabajar auth"
- "quiero refactorizar el scanner"
- "quiero revisar el flujo de release"

el problema principal ya no es detectar la arquitectura del repo, sino escoger que 8-15 piezas de contexto son realmente utiles.

### Sintesis

La IA puede resumir:

- bundle tecnico
- riesgos
- decisiones pendientes
- handoff de fin de sesion

### Export

La IA puede ayudar a producir:

- prompts por tarea
- handoffs compactos
- resumentes ejecutivos para otro agente

## Donde NO Debe Entrar

- no para decidir si existe Clean Architecture o no
- no para leer secretos o archivos ignorados
- no para ser requisito del flujo base
- no para introducir red obligatoria

## Arquitectura Objetivo

### Capa 1: analisis determinista

Responsabilidad:

- detectar estructura
- detectar naming
- clasificar dependencias
- indexar docs
- generar reglas
- generar `.context/`

Componentes actuales:

- scanners
- generators
- auditors
- security filter

### Capa 2: seleccion

Responsabilidad:

- construir candidatos
- rankear por relevancia
- cortar por presupuesto

Paquetes propuestos:

- `selector/heuristics.py`
- `selector/embeddings.py`
- `selector/rerank.py`
- `selector/budget.py`

### Capa 3: sintesis opcional

Responsabilidad:

- resumir
- redactar handoffs
- exportar para agentes

Paquetes propuestos:

- `assistants/export.py`
- `assistants/handoff.py`
- `assistants/summarize.py`

## Modelos Recomendados

### Embeddings

#### `sentence-transformers/all-MiniLM-L6-v2`

Usar cuando:

- quieras un MVP muy ligero
- el foco sea semantic search basico
- el entorno de ejecucion sea modesto

Pros:

- pequeno
- rapido
- facil de integrar

Contras:

- precision menor que opciones mas fuertes

#### `BAAI/bge-m3`

Usar cuando:

- quieras mejor retrieval
- tengas docs mezcladas en espanol/ingles
- priorices calidad de ranking

Pros:

- mas fuerte en retrieval
- buen soporte multilingue

Contras:

- mas costo operativo que MiniLM

### Generacion

#### `Qwen/Qwen2.5-Coder-7B-Instruct`

Usar para:

- handoff
- resumen tecnico
- pasos siguientes
- export para agentes

Pros:

- buena relacion calidad/costo
- orientado a codigo
- pesos abiertos

Contras:

- no debe meterse en el camino critico de CLI base

## Politica de Activacion

### Default

- `--ai off`

### Opcional

- `--ai local`

### Reglas

- si no hay modelo, fallback a heuristicas
- si la dependencia opcional no esta instalada, mensaje claro
- nunca fallar duro por ausencia de IA en comandos base

## Estrategia de Dependencias

### Paquete base

Debe incluir solo:

- click
- rich
- pathspec
- jinja2

### Extra `local-ai`

Debe incluir:

- sentence-transformers
- dependencias de embeddings/reranking elegidas

### Regla de producto

El usuario no debe instalar stack pesado si solo quiere `init`, `scan`, `audit` o `prompt`.

## Pipeline Propuesto para `loom bundle`

1. leer `.context/index.json`
2. leer reglas y docs disponibles
3. generar candidatos con heuristicas
4. si `--ai local`, rankear semanticamente
5. cortar por `top-k` y `token-budget`
6. generar `bundle.md`
7. generar `manifest.json`
8. opcionalmente sintetizar handoff

## Cache e Incrementalidad

### Cache minimo

- hash del archivo
- embedding
- timestamp
- tipo de artefacto

### Invalidacion

- si cambia archivo, recalcular embedding
- si cambia tarea, reusar embeddings pero recalcular ranking
- si cambia SHA, registrar bundle nuevo

## Evals Minimas Antes de Afinar Modelos

- [ ] 10 tareas reales
- [ ] expected files
- [ ] expected docs
- [ ] expected rules
- [ ] precision@k
- [ ] recall@k
- [ ] tiempo de generacion
- [ ] tamano del bundle

## Regla de Afinado

No hacer fine-tuning antes de cumplir estas condiciones:

- baseline heuristico medido
- baseline con embeddings medido
- tareas reales repetibles
- evidencia de que el problema es del modelo y no del pipeline

## Diferenciacion Frente a Otras Herramientas

Loom debe seguir defendiendo esta posicion:

- otras herramientas organizan contexto humano
- Loom compila contexto operacional desde el repo
- la IA en Loom sirve para reducir ruido, no para inventar estructura

## Decision Final

La estrategia correcta es:

- deterministic-first
- local-first
- optional-AI
- reproducible outputs
- small-core, heavy-extras

No:

- cloud-first
- prompt-first
- monolithic dependency tree
- dependencia total de un proveedor

