---
type: guide
audience: researcher
---

# Loom para mejora e investigacion

## TL;DR

Loom no solo sirve para productividad. Tambien puede funcionar como motor de observacion de un sistema socio-tecnico: repo, reglas, agentes, decisiones y deriva entre arquitectura esperada y arquitectura producida.

Para explotarlo con fines de mejora e investigacion, el foco no debe estar solo en el codigo generado, sino en los artefactos, mutaciones y hallazgos que deja el sistema.

---

## Que datos interesan

### 1. Deriva axiomatica

Distancia entre la constitucion del proyecto y el comportamiento real del codigo o del agente.

Artefactos base:

- `.context/rules.json`
- `.context/architecture.md`
- `.loom/inconsistencies.json`
- `.loom/mutations.jsonl`
- `.loom/decisions.jsonl`

Lo que interesa medir:

- cantidad de violaciones por tipo
- violaciones antes y despues de usar Loom
- reglas que se rompen de forma recurrente
- reglas que cambian tras nuevas decisiones

### 2. Entropia del contexto

Relacion entre tamano de contexto entregado y capacidad del agente para seguir reglas utiles.

Artefactos base:

- `.context/index.json`
- salida de `loom prompt`
- salida de `loom focus`
- bundles futuros si existen

Lo que interesa medir:

- tamano del contexto
- cobertura de reglas incluidas
- tasa de cumplimiento arquitectonico
- tasa de omisiones o contradicciones

### 3. Negociacion humano-agente

Como evoluciona el contexto despues de uso repetido por humanos y agentes.

Artefactos base:

- `.loom/decisions.jsonl`
- `.loom/mutations.jsonl`
- `.loom/sessions.jsonl`
- diffs historicos de `.context/`

Lo que interesa medir:

- que reglas sobreviven en el tiempo
- que reglas cambian con frecuencia
- que decisiones estabilizan el sistema
- donde el agente necesita correccion humana constante

### 4. Stack vs sugerencia incorrecta

Relacion entre stack real del repo y propuestas externas que no respetan el sistema.

Artefactos base:

- `.context/stack.json`
- `.context/rules.json`
- `.loom/inconsistencies.json`
- registros de sugerencias o diffs evaluados

Lo que interesa medir:

- sugerencias fuera del stack detectado
- sugerencias incompatibles con la arquitectura
- dependencia de sugerencias genericas
- mejora de precision al usar contexto estructurado

---

## Que necesita Loom para explotar estos datos

No hace falta convertir Loom en un laboratorio complejo. Hace falta preservar mejor el rastro del sistema.

### Artefactos minimos recomendados

- `.loom/inconsistencies.json`
- `.loom/decisions.jsonl`
- `.loom/mutations.jsonl`
- `.loom/sessions.jsonl`
- manifests por tarea o por corrida

### Campos minimos por evento

- `timestamp`
- `git_sha`
- `branch`
- `agent`
- `task`
- `source_artifacts`
- `rule_ids`
- `decision`
- `violation_type`
- `severity`
- `files_affected`

### Fuentes que conviene versionar o conservar

- `.context/index.json`
- `.context/rules.json`
- `.context/stack.json`
- `.context/architecture.md`
- resultados de `loom audit`
- salida resumida de `loom focus` o bundles futuros

---

## Que preguntas de mejora e investigacion habilita

Sin detallar aun el protocolo, Loom deberia permitir responder preguntas como:

- cuando disminuyen las violaciones arquitectonicas
- que reglas son demasiado fragiles o ambiguas
- cuanto contexto adicional deja de aportar valor
- que decisiones humanas estabilizan mejor el sistema
- cuando el agente contradice el stack o la arquitectura real

---

## Como leer a Loom cientificamente

Loom no observa inteligencia de forma abstracta. Observa:

- estructura real del repo
- reglas declaradas o inferidas
- diferencias entre expectativa y ejecucion
- huella de decisiones y correcciones

Eso lo vuelve util para estudiar gobernanza, deriva, consistencia y soberania contextual sin depender por completo del discurso del agente.

---

## Limites

Loom no ve por si solo:

- intencion profunda del negocio si no esta documentada
- calidad semantica total de una solucion
- motivaciones humanas no registradas

Por eso, si el objetivo es investigacion seria, conviene complementar con:

- glosario de dominio
- reglas de negocio explicitas
- decision records
- tareas o prompts conservados
- evaluaciones humanas o rubricas simples

---

## Posicion recomendada

Para fines de mejora e investigacion, Loom debe tratarse como:

- compilador de contexto
- registrador de inconsistencias
- historial de decisiones
- base de evidencia para comparar agentes, tareas y versiones

No como una caja magica que entiende el proyecto sin trazabilidad.
