# Scope de Loom-Context

## Que es Loom

Loom es un compilador de contexto para proyectos de software.

Escanea un repositorio, extrae metadata arquitectonica y genera `.context/` — un paquete compacto que cualquier agente de IA puede consumir para entender el proyecto sin leer todo el codigo.

## Para que sirve bien

### Software engineering (core)

- entender estructura de un repo
- detectar arquitectura y convenciones
- clasificar dependencias y stack
- resumir docs y planes existentes
- auditar naming y boundaries
- dar contexto preciso a agentes para programar, refactorizar, auditar

### Contexto operativo de producto (extension natural)

- decisiones de producto tecnicas
- reglas de negocio documentadas en el repo
- handoffs entre agentes y sesiones
- planes y roadmap versionados
- mockups resumidos (metadata, no contenido)

## Para que NO sirve

- investigacion general fuera de un repo
- writing puro sin estructura de proyecto
- gestion personal sin artefactos versionados
- analisis de PDFs/carpetas arbitrarias sin relacion con software
- operaciones de negocio sin repo

## Principio

Loom funciona porque los proyectos de software codifican mucha informacion en su estructura: carpetas, nombres, dependencias, docs, configuraciones. Eso es lo que Loom lee.

Si no hay estructura versionada, Loom no tiene de donde extraer contexto.

## Limites del analisis determinista

### Resuelve bien (sin IA)

- tipo de proyecto y stack
- arquitectura por carpetas y patrones
- convenciones de naming
- dependencias y categorias
- documentacion existente
- exclusiones y secretos
- reglas de boundaries

### Resuelve regular (heuristicas)

- relevancia de docs para una tarea especifica
- prioridad entre archivos para un bundle
- deteccion de arquitecturas mixtas o ambiguas

### Requiere IA auxiliar (futuro, v0.3.0+)

- ranking semantico de contexto por tarea
- resumen de decisiones implicitas
- interpretacion de specs o mocks pobres
- handoff narrativo entre sesiones

## Flujo de actualizacion de contexto

### Manual (recomendado para inicio)

```bash
loom init .          # genera .context/ + .loom/
# agente trabaja...
loom scan .          # refresca .context/ con el estado nuevo
loom enrich .        # re-audita y persiste hallazgos
```

### Watch (util mientras un agente trabaja)

```bash
loom watch . --interval 60
```

### Agent-triggered (avanzado)

El agente puede ejecutar Loom como parte de su flujo:
- "despues de cambiar estructura, corre `loom scan .`"
- "al terminar la tarea, corre `loom enrich .`"

### Regla

`.context/` es una foto del repo en un momento. Si el repo cambia, hay que volver a correr Loom.

## Direccion futura

### Context-first scaffolding (v0.5.0+, no confirmado)

```bash
loom seed --type backend-clean --stack python
```

Generaria:
- estructura de carpetas
- docs minimos
- decisiones iniciales
- `.context/` base

Esto permitiria que un agente arranque desde contexto estructurado en vez de una carpeta vacia.

**No es prioridad ahora.** Primero hay que consolidar el flujo repo-existente → contexto.
