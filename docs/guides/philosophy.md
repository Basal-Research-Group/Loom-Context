---
type: guide
audience: developer
---

# 🧠 Filosofia de Loom-Context

> *"La mente no es una hoja en blanco — es un telar. Y cada hilo de contexto que conectas cambia el patron completo."*

---

## El problema que nadie quiere admitir

Cada vez que abres una nueva sesion con un agente de IA, le estas pidiendo a un cirujano que opere sin historial medico. No sabe que arquitectura usas. No sabe que `core/` no puede importar de `infrastructure/`. No sabe que las interfaces llevan prefijo `I`. No sabe que tu equipo estuvo 3 meses refinando esas convenciones.

Y entonces pasa lo inevitable: la IA **alucina**. No porque sea tonta — porque **no tiene contexto**.

Esto no es un bug de la IA. Es un problema de ingenieria de contexto.

> 📚 *"The most powerful factor in learning is what the learner already knows. Ascertain this, and teach accordingly."*
> — David Ausubel, *Educational Psychology: A Cognitive View* (1968)

Ausubel lo dijo para estudiantes humanos, pero aplica identico para agentes de IA: **sin contexto previo, el aprendizaje (y la generacion de codigo) es fragil, impredecible y propenso a errores**.

Loom resuelve esto construyendo la memoria que la IA necesita.

---

## 🕸️ La analogia del telar

¿Por que "Loom"? Un telar (**loom** en ingles) toma hilos individuales y los teje en un patron coherente. Loom-Context hace exactamente eso:

- Cada archivo de tu repo es un **hilo**
- Las reglas de arquitectura son la **trama**
- Las convenciones de naming son la **urdimbre**
- El `.context/` resultante es el **tejido** — un patron que cualquier agente puede leer

Y Loomy, nuestra neurona-araña, es la tejedora:

```
        .  *  .  *  .
         \  |  /
      ── (O O) ──
         /  |  \
        *  .  *  .  *
```

Sus dendritas se extienden hacia cada rincon de tu codebase. Su soma `(O O)` procesa todo y produce contexto compacto.

> 📚 *"The strength of a neural network lies not in individual neurons, but in the patterns of connections between them."*
> — Hebb, D.O., *The Organization of Behavior* (1949)

Tu proyecto es una red. Los archivos son nodos. Los imports son sinapsis. Loom mapea esa red para que la IA la entienda sin recorrerla archivo por archivo.

---

## 🧬 El cerebro como arquitectura

Esto no es solo una metafora bonita — es un patron de diseno real. Cada componente de Loom cumple una funcion analoga a una estructura cerebral:

```
┌─────────────────────────────────────────────────┐
│  🧠 CORTEX PREFRONTAL                           │
│  PromptGenerator + BundleBuilder                │
│  Decisiones: que contexto necesita la IA        │
├─────────────────────────────────────────────────┤
│  💾 MEMORIA DE TRABAJO                           │
│  .context/ (7 archivos canonicos)               │
│  Lo que la IA tiene "activo" mientras trabaja   │
├─────────────────────────────────────────────────┤
│  📓 MEMORIA EPISODICA                            │
│  .loom/ (sessions, decisions, mutations)        │
│  Lo que paso antes — trazabilidad               │
├─────────────────────────────────────────────────┤
│  👁️ SISTEMA SENSORIAL                            │
│  Scanners (structure, deps, code, docs)         │
│  Percibe el proyecto sin inventar nada          │
├─────────────────────────────────────────────────┤
│  🛡️ SISTEMA INMUNE                               │
│  Auditors (naming, structure)                   │
│  Detecta amenazas: boundaries rotas, naming mal │
├─────────────────────────────────────────────────┤
│  🔒 BARRERA HEMATOENCEFALICA                     │
│  Security Filter (3 capas)                      │
│  Protege: nunca expone secretos ni codigo       │
└─────────────────────────────────────────────────┘
```

### 👁️ Sistema Sensorial → Scanners

Los scanners **perciben** tu proyecto como los sentidos perciben el mundo. No opinan, no inventan — reportan lo que ven.

| Scanner | Sentido | Que percibe |
|---------|---------|-------------|
| `StructureScanner` | 👁️ Vista | Forma: directorios, tipo, arquitectura |
| `DependencyScanner` | ✋ Tacto | Herramientas: que stack usa el proyecto |
| `CodeScanner` | 👂 Oido | Patrones: naming, convenciones, estilo |
| `DocsScanner` | 📖 Lectura | Documentacion: planes, guias, estado |

> 📚 *"Perception is not the passive reception of signals but the active construction of representations."*
> — James J. Gibson, *The Ecological Approach to Visual Perception* (1979)

Los scanners de Loom construyen **representaciones** de tu proyecto — no copian archivos.

### 💾 Memoria de Trabajo → `.context/`

George Miller descubrio en 1956 que la memoria de trabajo humana retiene ~7±2 elementos simultaneos. ¿Casualidad que `.context/` tiene exactamente **7 archivos**? No del todo.

| Archivo | Funcion cognitiva |
|---------|------------------|
| `index.json` | 🎯 Atencion selectiva — lo primero que procesar |
| `architecture.md` | 🏗️ Modelo mental — como se organiza el sistema |
| `naming.md` | 🏷️ Vocabulario — como se nombran las cosas |
| `directory-map.md` | 🗺️ Mapa espacial — donde vive cada cosa |
| `stack.json` | 📦 Conocimiento del entorno — herramientas disponibles |
| `rules.json` | ⚙️ Reglas internalizadas — que se puede y que no |
| `plans-summary.md` | 📋 Intenciones — hacia donde va el proyecto |

> 📚 Miller, G.A. (1956). *"The Magical Number Seven, Plus or Minus Two."* Psychological Review, 63(2), 81-97.

### 📓 Memoria Episodica → `.loom/`

La memoria de trabajo es lo que tienes "activo". Pero el cerebro tambien tiene **memoria episodica** — recuerdos de lo que paso antes. `.loom/` es exactamente eso:

| Archivo | Que recuerda |
|---------|-------------|
| `sessions.jsonl` | "Que hice ayer" |
| `decisions.jsonl` | "Por que tome esa decision" |
| `mutations.jsonl` | "Que cambio y cuando" |
| `inconsistencies.json` | "Que problemas detecte la ultima vez" |

Sin memoria episodica, cada sesion con la IA empieza desde cero. Con `.loom/`, el handoff entre sesiones es natural:

```bash
loom handoff "mi tarea" . --stdout
# → resume decisiones, estado, problemas, para quien retome
```

### 🛡️ Sistema Inmune → Auditors

Tu sistema inmune no espera a que estes enfermo — detecta amenazas proactivamente. Los auditors hacen lo mismo:

```bash
loom audit .
# ~(^ ^)~ No violations found.    ← sistema sano
# ~(! !)~ 107 errors              ← infeccion detectada
```

Cada error es una sinapsis que se conecto donde no debia: un import que cruza una frontera arquitectonica, un nombre que rompe la convencion.

### 🔒 Barrera Hematoencefalica → Security Filter

La barrera hematoencefalica protege al cerebro de toxinas en la sangre. El `FileFilter` protege al contexto de informacion que **nunca debe exponerse**: `.env`, claves privadas, `node_modules/`.

3 capas. Sin excepciones. Incluso si te equivocas, Loom no.

---

## ⚡ Principios de diseno

### 1. Escanear mucho, preguntar poco

Loom no te pregunta "¿que arquitectura usas?" — lo **detecta**. Ve `domain/`, `infrastructure/`, `presentation/` y deduce Clean Architecture. Ve `ports/` y agrega Hexagonal. Ve `scanners/` + `generators/` y detecta Pipeline.

> 📚 *"Don't make me think."* — Steve Krug, titulo del libro mas influyente de UX (2000)

La mejor herramienta es la que no necesitas configurar.

### 2. Metadata, nunca contenido

Loom **nunca** incluye tu codigo fuente. Solo metadata: nombres, conteos, patrones, reglas.

> La diferencia entre saber que "hay una casa roja en la esquina" y tener los planos completos de la casa. La IA necesita el **mapa**, no el **territorio**.

> 📚 *"The map is not the territory."* — Alfred Korzybski, *Science and Sanity* (1933)

### 3. Consumo progresivo

```
index.json (30s)  →  architecture + naming (2min)  →  bundle completo (5min)
     ↑                      ↑                              ↑
  Quick rules          Reglas detalladas            Contexto por tarea
```

Un agente puede detenerse en cualquier nivel. Para una pregunta simple, `quick_rules` basta. Para refactorizar una capa, necesita un `bundle`.

> 📚 *"Elaboration is the process of adding meaningful connections."* — Craik & Lockhart, *Levels of Processing* (1972)

Cuanto mas profundo procesa el agente, mejor es su output.

### 4. Contexto vivo, no estatico

`.context/` no es un snapshot muerto. Con `enrich`, `decide`, `log`, y `handoff`, el contexto **evoluciona** con tu proyecto:

```bash
loom init .       # primera foto
# ... trabajo ...
loom enrich .     # re-audita y persiste hallazgos
loom decide "..." # registra por que tomaste esa decision
loom handoff ...  # resume para quien siga
```

> 📚 *"Knowledge is not a thing to be possessed, but a process of transformation."* — Jerome Bruner, *The Process of Education* (1960)

---

## 🎯 Por que funciona

Loom funciona porque los proyectos de software **ya codifican mucha informacion en su estructura**. No necesitas IA para saber que un proyecto es Clean Architecture — solo mira las carpetas. No necesitas IA para saber que usas React — mira el `package.json`.

Lo que Loom agrega es la **compilacion**: tomar esa informacion dispersa en 700 archivos y comprimirla en 7 archivos que un agente consume en 30 segundos.

> 📚 *"Simplicity is the ultimate sophistication."* — atribuido a Leonardo da Vinci, adoptado por toda la industria de software.

---

## 🔬 Referencias

| Referencia | Concepto | Como aplica en Loom |
|-----------|---------|-------------------|
| Miller (1956) | Magic number 7±2 | 7 archivos en .context/ |
| Hebb (1949) | Redes neuronales | Proyecto como red de nodos e imports |
| Gibson (1979) | Percepcion ecologica | Scanners construyen representaciones, no copian |
| Ausubel (1968) | Aprendizaje significativo | Sin contexto previo, el output es fragil |
| Korzybski (1933) | Map vs territory | Metadata, nunca codigo fuente |
| Craik & Lockhart (1972) | Niveles de procesamiento | Consumo progresivo de contexto |
| Bruner (1960) | Conocimiento como proceso | Contexto vivo que evoluciona |
| Krug (2000) | Don't make me think | Auto-deteccion, cero configuracion |

---

## 🔷 Contexto Axiomatico

Los LLMs son probabilisticos. Loom es axiomatico.

> 📚 *"An axiom is a statement that is taken to be true, to serve as a premise or starting point for further reasoning."* — Euclid, *Elements* (~300 BCE)

Las reglas de boundaries, naming, arquitectura de tu proyecto no son opiniones — son **invariantes**. No cambian segun el modelo, la sesion, ni el prompt. Son axiomas del proyecto.

Loom los extrae una vez, los persiste, y todos los agentes los respetan. No porque "crean" que son correctos (probabilidad), sino porque estan **definidos** como correctos (axioma).

### Por que importa

| Enfoque | Tipo | Riesgo |
|---------|------|--------|
| Agente lee el repo completo | Probabilistico | Re-interpreta reglas en cada sesion, deriva |
| Agente lee `.context/` de Loom | Axiomatico | Reglas fijas, consistentes, verificables |

### Implicaciones

- **Menos tokens** — no re-descubrir lo que ya se sabe
- **Menos deriva** — mismas reglas para todos los agentes
- **Menos costo** — contexto comprimido, no diluido
- **Menos impacto energetico** — menos computo por tarea

> La propuesta de valor no es "Loom usa IA". Es "Loom evita desperdiciar IA".

---

*Siguiente: [🏗️ Arquitectura de Loom →](../architecture/overview.md)*
