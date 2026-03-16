# Plan de Hardening Arquitectonico

> Objetivo: preparar Loom-Context para crecer hacia bundles, handoff, retrieval local y export a agentes sin degradar mantenibilidad, testeabilidad ni claridad del dominio.

## Diagnostico

La arquitectura actual es suficiente para `0.1.x`, pero tiene limites claros para la siguiente etapa:

- el orquestador central conoce demasiados detalles de construccion
- el contrato de datos entre componentes es demasiado implicito
- el CLI va camino a concentrar demasiada logica de aplicacion
- `.context/` corre el riesgo de mezclar output canonico con estado operativo
- la futura capa de seleccion todavia no tiene boundaries tecnicos explicitos

## Principios de Diseno

### 1. Contratos antes que diccionarios

Los datos que cruzan boundaries deben tener forma explicita:

- `ScanResult`
- `StructureFacts`
- `DocsInventory`
- `BundleManifest`
- `SelectionCandidate`
- `SelectionReason`

Usar:

- `dataclass(frozen=True)` para entidades y value objects
- `TypedDict` solo en bordes de serializacion

### 2. Composicion por capacidades

El sistema debe crecer agregando capacidades, no editando un archivo central para todo.

Patrones recomendados:

- Registry para scanners, generators y exporters
- Strategy para seleccion, ranking y budget
- Factory para construir pipelines segun comando y flags
- Template Method solo donde la secuencia sea estable y el algoritmo cambie poco

### 3. Separacion de outputs

No mezclar:

- `.context/` = output canonico y reproducible
- `.loom/` = cache, sesiones, estado incremental, artefactos efimeros
- `context/` = workspace humano opcional

### 4. Casos de uso explicitos

La logica de aplicacion debe vivir en servicios/casos de uso, no en el CLI:

- `scan_project`
- `generate_context`
- `build_bundle`
- `build_handoff`
- `export_agent_payload`
- `run_audit`

### 5. Testeabilidad por seams

Cada componente debe poder probarse sin CLI, sin FS real complejo y sin dependencias opcionales instaladas.

## Arquitectura Objetivo

```text
cli/
  commands/
application/
  use_cases/
  services/
domain/
  models/
  policies/
  ports/
infrastructure/
  scanners/
  generators/
  auditors/
  storage/
  ai/
```

## Fase A - Contratos y dominio minimo

### Objetivo

Eliminar dependencias fuertes de `dict[str, Any]` en el nucleo.

### Entregables

- `domain/models/scan_result.py`
- `domain/models/docs.py`
- `domain/models/bundle.py`
- mappers de serializacion hacia `index.json`, `rules.json`, `manifest.json`

### Reglas

- el dominio no importa Click, Rich ni Jinja2
- el dominio no conoce rutas absolutas salvo value objects controlados
- los scanners devuelven objetos del dominio o DTOs bien tipados

### Criterios de salida

- menos llaves string "magicas" cruzando capas
- errores de tipado detectados por mypy antes de runtime
- serializacion estable para outputs existentes

## Fase B - Orquestacion por pipelines

### Objetivo

Sustituir el orquestador monolitico por composicion de pipelines.

### Patrones

- Registry de componentes disponibles
- Pipeline Builder por capability
- Dependency Inversion sobre puertos simples

### Entregables

- `application/services/pipeline_builder.py`
- `domain/ports/scanner.py`
- `domain/ports/generator.py`
- `domain/ports/store.py`

### Resultado esperado

Agregar `bundle`, `handoff` o `export` no debe requerir tocar el mismo bloque central de wiring cada vez.

## Fase C - Modularizacion del CLI

### Objetivo

Mantener la interfaz publica estable mientras se reduce acoplamiento.

### Entregables

- `cli/commands/init.py`
- `cli/commands/scan.py`
- `cli/commands/prompt.py`
- `cli/commands/audit.py`
- `cli/commands/plan.py`
- `cli/commands/watch.py`

### Regla

Cada comando:

- parsea input
- invoca un caso de uso
- renderiza salida

No debe contener logica de negocio ni agregacion compleja.

## Fase D - Estado, cache e incrementalidad

### Objetivo

Preparar `watch --events`, bundles reproducibles y retrieval local sin contaminar `.context/`.

### Entregables

- `.loom/cache/`
- `.loom/sessions/`
- `.loom/index/`
- storage adapter para hashes, timestamps y embeddings

### Decisiones

- `.context/` permanece reproducible desde el repo y SHA
- `.loom/` puede regenerarse y no es fuente de verdad
- `context/` humano nunca reemplaza `.context/`

## Fase E - Seleccion y AI opcional

### Objetivo

Montar la capa de seleccion encima de contratos y caches ya estables.

### Patrones

- Strategy para heuristics vs hybrid ranking
- Policy objects para budget, cutoffs y inclusion minima
- Adapter para proveedores de embeddings

### Entregables

- `selector/strategies/heuristic.py`
- `selector/strategies/hybrid.py`
- `selector/policies/budget.py`
- `infrastructure/ai/embeddings.py`

## Estrategia de Testing

### Piramide recomendada

- tests unitarios para domain models, policies y selectors
- tests de integracion para scanners/generators con fixture de proyecto
- tests de contrato para serializacion de `.context/` y manifests
- tests CLI solo para humo y wiring

### Cobertura que hoy falta reforzar

- contratos de salida estables
- reasons de seleccion y reproducibilidad
- invalidacion de cache
- fallback cuando `local-ai` no esta instalado
- separacion entre `.context/`, `.loom/` y `context/`

### Dataset de regresion

Mantener fixtures para:

- repo Python simple
- repo TypeScript con aliases
- repo mixto con docs extensos
- repo vacio o casi vacio

## Anti-patrones a evitar

- crecer por `if command == ...` en el CLI o engine
- pasar mapas anonimos entre todas las capas
- dejar que `.context/` acumule estado no reproducible
- acoplar retrieval local al flujo base
- esconder reglas de inclusion en helpers sin trazabilidad

## Secuencia recomendada

1. contratos tipados
2. modularizacion del CLI
3. pipelines y puertos
4. separacion `.context/` vs `.loom/`
5. bundles y handoff heuristico
6. retrieval local opcional
7. export y watch incremental

## Criterio final de exito

La arquitectura estara lista cuando una nueva capability pueda agregarse:

- creando un modulo nuevo
- registrandolo en una fabrica o registry
- sin editar mas de un punto de composicion
- con pruebas de unidad y contrato claras
