# Filosofía de Loom-Context: La Analogía del Cerebro

> *Loom no es una herramienta de documentación. Es un sistema nervioso para tu proyecto.*

## El Problema

Cuando un agente de IA (Cursor, Copilot, Claude, ChatGPT) trabaja en tu proyecto, empieza **amnésico**. No sabe que usas Clean Architecture. No sabe que las interfaces llevan prefijo `I`. No sabe que `core/` no puede importar de `infrastructure/`. Cada sesión es un paciente nuevo entrando a consulta sin historial médico.

El resultado: la IA alucina. Sugiere código que rompe tus patrones. Crea archivos en el lugar equivocado. Ignora convenciones que tu equipo lleva meses refinando.

**Loom resuelve esto construyendo la memoria que la IA necesita.**

---

## La Analogía: El Cerebro como Arquitectura

Loom-Context opera como las capas del cerebro humano. Cada componente cumple una función análoga:

```
┌─────────────────────────────────────────────────┐
│              CÓRTEX PREFRONTAL                   │
│         (PromptGenerator + CLI)                  │
│   Decisiones conscientes: genera el prompt       │
│   que la IA usa para razonar.                    │
├─────────────────────────────────────────────────┤
│              MEMORIA DE TRABAJO                  │
│           (.context/ folder)                     │
│   index.json, architecture.md, naming.md...      │
│   Lo que la IA tiene "activo" mientras trabaja.  │
├─────────────────────────────────────────────────┤
│            MEMORIA DE LARGO PLAZO                │
│        (Scanners + Project Source)               │
│   El código fuente real: 700 archivos, 50 docs.  │
│   Loom lo comprime en patrones consumibles.      │
├─────────────────────────────────────────────────┤
│             SISTEMA SENSORIAL                    │
│               (Scanners)                         │
│   Percibe: estructura, deps, naming, docs.       │
│   No inventa — observa y reporta.                │
├─────────────────────────────────────────────────┤
│             SISTEMA INMUNE                       │
│              (Auditors)                          │
│   Detecta anomalías: "este import viola una      │
│   boundary", "esta interface no tiene prefijo I" │
├─────────────────────────────────────────────────┤
│        BARRERA HEMATOENCEFÁLICA                  │
│           (Security/Filter)                      │
│   Protege: nunca expone .env, secrets, keys.     │
│   Filtra noise: node_modules, dist, .git.        │
└─────────────────────────────────────────────────┘
```

### Cada capa explicada

#### 1. Sistema Sensorial → Scanners

Como los sentidos perciben el mundo exterior, los **scanners** perciben tu proyecto:

| Scanner | Sentido análogo | Qué percibe |
|---------|----------------|-------------|
| `StructureScanner` | **Vista** | Forma del proyecto: directorios, tipo, arquitectura |
| `DependencyScanner` | **Tacto** | Dependencias: qué herramientas usa el proyecto |
| `CodeScanner` | **Oído** | Patrones del código: naming, convenciones, estilo |
| `DocsScanner` | **Lectura** | Documentación existente: planes, guías, reglas |

**Principio clave:** Los scanners **nunca inventan** — solo observan. Si tu código usa PascalCase en el 50% de archivos, Loom reporta eso. No opina si está bien o mal.

#### 2. Memoria de Trabajo → `.context/`

La memoria de trabajo del cerebro retiene ~7 elementos simultáneos. De forma análoga, `.context/` tiene **7 archivos** que representan lo que la IA necesita "tener presente":

| Archivo | Función en la memoria |
|---------|----------------------|
| `index.json` | **Atención selectiva** — lo primero que se lee, filtra lo esencial |
| `architecture.md` | **Modelo mental** — cómo se organiza el sistema |
| `naming.md` | **Vocabulario** — cómo se nombran las cosas |
| `directory-map.md` | **Mapa espacial** — dónde vive cada cosa |
| `stack.json` | **Conocimiento del entorno** — herramientas disponibles |
| `rules.json` | **Reglas internalizadas** — qué se puede y qué no |
| `plans-summary.md` | **Intenciones** — hacia dónde va el proyecto |

#### 3. Córtex Prefrontal → PromptGenerator

El córtex prefrontal toma toda la información sensorial y la memoria, y genera **una decisión coherente**. El `PromptGenerator` hace exactamente eso: toma los 7 archivos de `.context/` y los compila en un **master prompt** — un solo documento que la IA puede consumir de principio a fin.

#### 4. Sistema Inmune → Auditors

El sistema inmune no espera a que estés enfermo — detecta amenazas proactivamente. Los **auditors** hacen lo mismo:

- `NamingAuditor`: "Esta interface no tiene prefijo I — ¿es intencional?"
- `StructureAuditor`: "core/ está importando de infrastructure/ — violación de boundary"

#### 5. Barrera Hematoencefálica → Security Filter

La barrera hematoencefálica protege al cerebro de toxinas en la sangre. El `FileFilter` protege al contexto de información que **nunca debe exponerse**:

- Archivos `.env`, claves privadas, credentials
- Ruido: `node_modules/`, `dist/`, `.git/`
- Código que el `.gitignore` ya excluye

---

## Principios de Diseño

### 1. Escanear mucho, preguntar poco

Loom NO te pregunta "¿qué arquitectura usas?" — lo **detecta**. Si tienes `domain/`, `infrastructure/` y `presentation/`, Loom deduce Clean Architecture. Si hay `ports/` dentro de `domain/`, agrega Hexagonal. La filosofía es: **la mejor herramienta es la que no necesitas configurar**.

### 2. Resolver automáticamente, parar solo en catástrofe

En una red neuronal, millones de decisiones se toman sin llegar a la consciencia. Solo los eventos importantes "suben" al córtex. Loom opera igual:

- **Auto-resuelve:** naming, estructura, stack, boundaries
- **Reporta silencioso:** violaciones menores (warnings)
- **Para y alerta:** violaciones de seguridad, boundaries rotas (errors)

### 3. Metadata, nunca contenido

Loom **nunca** incluye tu código fuente en el output. Solo metadata: nombres de archivos, conteos, patrones, reglas. Esto es como la diferencia entre saber que "hay una casa roja en la esquina" vs. tener los planos completos de la casa. La IA necesita el mapa, no el territorio.

### 4. Progresivo: de lo general a lo específico

```
index.json (30 seg)  →  architecture.md + naming.md (2 min)  →  directory-map.md (5 min)
     ↑                          ↑                                      ↑
  Quick rules               Reglas detalladas                   Contexto completo
```

Un agente de IA puede detenerse en cualquier nivel. Para una pregunta simple, `quick_rules` basta. Para refactorizar una capa entera, necesita el mapa completo.

---

## El Ciclo Loom

```
         ┌──────────┐
         │  loom     │
         │  init     │◄─── Primera vez: scan completo
         └────┬─────┘
              │
              ▼
    ┌─────────────────┐
    │   .context/     │◄─── Memoria de trabajo generada
    │   (7 archivos)  │
    └────────┬────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐    ┌──────────┐
│  IA lee │    │  loom    │
│ context │    │  audit   │◄─── Validación continua
│ y opera │    └──────────┘
└────┬────┘
     │
     ▼ (cambios en el código)
┌─────────┐
│  loom   │
│  scan   │◄─── Re-scan incremental
└─────────┘
```

Este ciclo se repite. Con `loom watch`, es automático. El proyecto evoluciona, Loom actualiza la memoria, la IA siempre tiene contexto fresco.

---

## Loom como Gadget del Proyecto

Piensa en Loom como el **HUD de un piloto de caza**. El piloto (la IA) no necesita abrir el manual de vuelo en pleno combate. El HUD le muestra:

- Altitud (arquitectura)
- Velocidad (stack)
- Amenazas (violaciones)
- Ruta (planes)

Loom es ese HUD. Se instala en 1 segundo, se actualiza en 1 segundo, y la IA lo lee antes de cada acción.

---

*Siguiente: [Arquitectura de Loom →](../architecture/overview.md)*
