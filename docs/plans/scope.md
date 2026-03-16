---
type: scope
---

# Scope de Loom-Context

## TL;DR

Loom es un compilador de contexto para proyectos de software. Escanea un repo, extrae metadata arquitectonica y genera `.context/` para que agentes de IA entiendan el proyecto sin leer todo el codigo. No es para tareas generales — funciona porque los repos codifican mucha informacion en su estructura.

---

## Indice

- [Que es Loom](#que-es-loom)
- [Analogia](#analogia)
- [Para que sirve bien](#para-que-sirve-bien)
- [Para que NO sirve](#para-que-no-sirve)
- [Limites del analisis determinista](#limites-del-analisis-determinista)
- [Flujo de actualizacion de contexto](#flujo-de-actualizacion-de-contexto)
- [Direccion futura](#direccion-futura)

---

## Que es Loom

Loom escanea un repositorio de forma determinista y genera un paquete compacto de contexto (`.context/`) que cualquier agente de IA puede consumir.

No usa IA para analizar. Usa reglas, heuristicas y la estructura del propio repo.

## Analogia

**Loom es como un inspector de obra que hace inventario tecnico.**

No diseña la casa, no decide los materiales, no la habita. Pero recorre cada habitacion, anota que hay, mide, detecta si algo no cuadra con los planos, y entrega un informe estructurado.

El arquitecto (tu) o el contratista (el agente de IA) usan ese informe para tomar decisiones informadas.

- El inspector no necesita "entender" el proposito de cada habitacion
- Pero sabe leer planos, detectar patrones y reportar hallazgos
- Si la casa cambia, hay que volver a pasar al inspector

---

## Para que sirve bien

### Software engineering (core)

| Capacidad | Como lo hace |
|-----------|-------------|
| Entender estructura de un repo | StructureScanner: detecta tipo, arquitectura, capas |
| Detectar convenciones | CodeScanner: naming, prefijos, sufijos, aliases |
| Clasificar stack | DependencyScanner: 130+ paquetes categorizados |
| Resumir docs | DocsScanner: titulo, secciones, checklists |
| Auditar reglas | NamingAuditor + StructureAuditor: boundaries, prefijos |
| Dar contexto a agentes | PromptGenerator + FocusGenerator: contexto completo o por tarea |

### Contexto operativo de producto (extension natural)

- Decisiones tecnicas registradas (`loom decide`)
- Hallazgos del audit persistidos (`.loom/inconsistencies.json`)
- Historial de sesiones (`.loom/sessions.jsonl`)
- Planes y roadmap versionados (si estan en `docs/`)
- Reglas de negocio documentadas en el repo

---

## Para que NO sirve

| Caso | Por que no |
|------|-----------|
| Investigacion general | No hay repo que escanear |
| Writing sin estructura | Loom lee estructura de proyecto, no texto libre |
| Gestion personal | No hay artefactos versionados |
| PDFs/carpetas arbitrarias | Loom depende de convenciones de software |
| Operaciones de negocio sin repo | Sin estructura versionada, no hay de donde extraer |

**Principio:** si no hay repositorio con estructura versionada, Loom no tiene de donde extraer contexto.

---

## Limites del analisis determinista

### Resuelve bien (sin IA)

| Problema | Metodo |
|----------|--------|
| Tipo de proyecto y stack | Archivos marcador (pyproject.toml, package.json, etc.) |
| Arquitectura | Nombres de carpetas y patrones conocidos |
| Convenciones de naming | Analisis estadistico de nombres reales |
| Dependencias | Parsing de manifiestos + base de 130+ paquetes |
| Documentacion | Indexacion por path, titulo, secciones, checklists |
| Exclusiones y secretos | 3 capas: hardcoded + .gitignore + .contextignore |
| Reglas de boundaries | Analisis de imports vs capas detectadas |

**Analogia:** es como un lector de codigos de barras. No "entiende" el producto, pero sabe leer la etiqueta y clasificar con precision.

### Resuelve regular (heuristicas)

- Relevancia de docs para una tarea especifica
- Prioridad entre archivos para un bundle
- Deteccion de arquitecturas mixtas o ambiguas

### Requiere IA auxiliar (futuro, v0.3.0+)

- Ranking semantico de contexto por tarea
- Resumen de decisiones implicitas
- Interpretacion de specs o mocks pobres
- Handoff narrativo entre sesiones

---

## Flujo de actualizacion de contexto

### Analogia

**`.context/` es como una fotografia del estado del proyecto.** Si el proyecto cambia, la foto queda vieja. Hay que tomar una nueva.

### Manual (recomendado para inicio)

```bash
loom init .          # primera foto: genera .context/ + .loom/
# agente trabaja...
loom scan .          # foto nueva: refresca .context/
loom enrich .        # foto + analisis: re-audita y persiste hallazgos
```

### Watch (util mientras un agente trabaja)

```bash
loom watch . --interval 60   # foto automatica cada N segundos
```

### Agent-triggered (avanzado)

El agente ejecuta Loom como parte de su flujo:
- "despues de cambiar estructura, corre `loom scan .`"
- "al terminar la tarea, corre `loom enrich .`"

---

## Direccion futura

### Context-first scaffolding (v0.5.0+, no confirmado)

**Analogia:** hoy el inspector solo revisa casas existentes. En el futuro, podria entregar los planos base para que el constructor arranque desde una estructura ya validada.

```bash
loom seed --type backend-clean --stack python
```

Generaria estructura, docs minimos, decisiones iniciales y `.context/` base. Asi un agente arrancaria desde contexto estructurado en vez de una carpeta vacia.

**No es prioridad ahora.** Primero consolidar el flujo repo-existente → contexto.
