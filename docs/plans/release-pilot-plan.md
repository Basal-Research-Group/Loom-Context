# Plan de Release Piloto

> Objetivo: decidir que liberar ahora, probarlo en un proyecto real y usar esa experiencia para corregir bugs antes de ampliar el alcance.

## Recomendacion

Si el objetivo es aprender rapido en un proyecto real, no esperaria a v0.2.

La recomendacion es liberar una version de estabilizacion corta sobre el estado actual:

- `0.1.1` si quieres comunicar "release de mantenimiento"
- `0.2.0-beta.1` si quieres comunicar "ya empieza la siguiente etapa pero todavia es piloto"

Mi recomendacion practica:

- si el publico es pequeno y controlado: `0.2.0-beta.1`
- si quieres algo mas conservador para PyPI y adopcion inicial: `0.1.1`

## Mi Juicio Sobre el Estado Actual

### Si, ya puedes probar Loom en un proyecto real

Porque ya tiene:

- `init`
- `scan`
- `prompt`
- `audit`
- `plan`
- `watch`
- tests pasando
- CI razonablemente completa
- docs suficientes para primera adopcion

### Pero todavia no lo venderia como estable

Porque aun faltan:

- experiencia de bundles por tarea
- watch incremental real
- mejor integracion con agentes
- validacion real sobre repositorios mas diversos

## Objetivo del Piloto

Validar si Loom aporta valor real en un proyecto activo sin necesidad de features futuras.

### Preguntas que el piloto debe responder

- [ ] `loom init .` detecta correctamente la arquitectura real
- [ ] `loom audit .` encuentra violaciones utiles y no solo ruido
- [ ] `loom prompt .` produce contexto que mejora una sesion real con IA
- [ ] `loom plan .` resume docs reales de forma util
- [ ] el tiempo de ejecucion es aceptable
- [ ] la documentacion alcanza para instalarlo sin adivinar

## Candidato de Release

### Opcion A: liberar `0.1.1`

#### Que incluir

- fixes de CI y type-check recientes
- limpieza de docs y release notes
- correcciones menores detectadas en smoke test real

#### Mensaje

"primera version util para adopcion temprana"

#### Ventaja

- mas conservadora
- menos confusion semantica

### Opcion B: liberar `0.2.0-beta.1`

#### Que incluir

- estado actual estable
- etiqueta beta explicita
- nota clara de que bundles y retrieval vienen despues

#### Mensaje

"inicio de la fase de validacion en proyectos reales"

#### Ventaja

- te da mas libertad para ajustar UX despues del piloto

## Alcance Minimo Antes de Liberar

- [ ] tests verdes
- [ ] lint verde
- [ ] type-check verde
- [ ] build y `twine check` verdes
- [ ] quickstart verificado en repo limpio
- [ ] smoke test en proyecto real

## Smoke Test Recomendado

Usar un proyecto real con:

- estructura no trivial
- docs existentes
- varios modulos o capas
- package manager y/o Python config reales

### Flujo

1. instalar desde wheel o desde git
2. correr `loom init .`
3. revisar `.context/index.json`
4. correr `loom audit .`
5. usar `loom prompt . --stdout` en una tarea real con IA
6. documentar falsos positivos, omisiones y friccion

## Bugs a Buscar en el Piloto

### Deteccion

- proyecto mal clasificado
- arquitectura inferida incorrectamente
- stack incompleto
- docs mal clasificadas

### Auditoria

- falsos positivos de boundaries
- falsos negativos en naming
- errores por aliases o rutas reales del proyecto

### UX

- comandos poco claros
- output excesivo o poco accionable
- mensajes de error ambiguos

### Packaging

- instalacion en entornos limpios
- problemas de PATH
- diferencias Windows/macOS/Linux

## Entregables del Piloto

- [ ] lista de bugs
- [ ] lista de falsos positivos
- [ ] lista de carencias de DX
- [ ] decision de alcance para `0.2`
- [ ] un caso de exito documentado

## Criterios para Pasar de Piloto a Siguiente Release

- falsos positivos reducidos a un nivel aceptable
- instalacion repetible en entorno limpio
- un proyecto real usando Loom de principio a fin
- feedback suficiente para priorizar bundles y handoff

## Recomendacion Final

Si quieres aprender rapido, libera ya una version piloto y usala en un proyecto real esta semana.

No esperes a tener bundles, embeddings o workspace. Esas mejoras van a salir mejor si primero observas:

- donde falla `audit`
- que partes del prompt sobran
- donde el usuario pierde tiempo

Eso te dira que construir en v0.2 con mucha mas precision.

