---
type: guide
audience: user
---

# 📁 El Output: .context/ y .loom/

## TL;DR

Loom genera dos carpetas: `.context/` (contexto canonico, compartible) y `.loom/` (estado vivo, local). La IA consume `.context/`. Tu flujo de trabajo vive en `.loom/`.

---

## 🗂️ Estructura Completa

```
.context/                          ← canonico, derivado del repo
  index.json                       ← entry point para la IA
  architecture.md                  ← patrones y boundaries
  naming.md                        ← convenciones de nombres
  directory-map.md                 ← arbol anotado
  stack.json                       ← dependencias categorizadas
  rules.json                       ← reglas machine-readable
  plans-summary.md                 ← estado de planes y docs
  exports/                         ← generados por loom export
    CLAUDE.md
    .cursorrules
    AGENTS.md
  bundles/                         ← generados por loom bundle
    <slug>/
      bundle.md
      manifest.json
  handoffs/                        ← generados por loom handoff
    <slug>.md

.loom/                             ← estado vivo, local por usuario
  inconsistencies.json             ← hallazgos del ultimo audit
  decisions.jsonl                  ← decision records
  sessions.jsonl                   ← log de sesiones
  mutations.jsonl                  ← log de cambios al contexto
```

---

## 📌 Los 7 Archivos Canonicos

### 1. `index.json` — 🧠 El Entry Point

La IA debe leer este archivo **primero**. Contiene metadata del proyecto y `quick_rules` — las reglas mas importantes en texto plano.

```json
{
  "loom_version": "0.2.0",
  "project": {
    "name": "akana",
    "type": "react-native-expo",
    "architecture": ["clean-architecture", "hexagonal", "feature-based"],
    "language": "TypeScript",
    "runtime": "react@19.0.0 + react-native@0.79.2"
  },
  "quick_rules": [
    "Layer boundary: domain MUST NOT import from infrastructure",
    "Interfaces MUST have 'I' prefix (e.g., IUserRepository)",
    "React hooks MUST have 'use' prefix (e.g., useLogoutApp)",
    "Repository files follow pattern: {Name}Repository.ts"
  ],
  "stats": {
    "total_files": 674,
    "total_code_files": 731,
    "total_docs": 59,
    "total_dependencies": 95
  }
}
```

> 💡 Un agente que solo lea `quick_rules` ya tiene suficiente contexto para no romper tu proyecto.

---

### 2. `architecture.md` — 🏗️ Patrones y Boundaries

Tipo de proyecto, patrones detectados, boundaries entre capas, direccion de dependencias.

```markdown
## Layer Boundaries
| Layer | MUST NOT import from |
|-------|---------------------|
| domain | infrastructure, presentation |
| core | infrastructure, presentation |

## Dependency Direction
presentation → core → domain ← infrastructure
```

---

### 3. `naming.md` — 🏷️ Convenciones de Nombres

Estilo dominante de archivos, patrones de sufijo/prefijo con ejemplos reales, naming a nivel de codigo.

```markdown
## Suffix Patterns
| Pattern | Count | Examples |
|---------|-------|---------|
| {Name}Repository.ts | 67 | IUserRepository.ts, ScenarioConfigRepository.ts |
| {Name}Service.ts | 17 | TelemetryService.ts, AdaptiveStaircaseService.ts |
| {Name}ViewModel.ts | 14 | useAvatarSelectionViewModel.ts |
```

---

### 4. `directory-map.md` — 🗺️ Arbol Anotado

Cada directorio con anotacion semantica y conteo de archivos.

```
core/                    # Core layer - orchestration, DI, services
  bootstrap/             # Application initialization (11 files)
  di/                    # Dependency injection (7 files)
domain/                  # Domain layer - entities, ports, use cases
  entities/              # Domain entities (28 files)
  ports/                 # Port interfaces (6 files)
```

> 🎯 La IA sabe exactamente donde crear un nuevo archivo.

---

### 5. `stack.json` — 📦 Stack Tecnologico

Dependencias categorizadas. Evita que la IA sugiera librerias que contradicen tu stack.

```json
{
  "stack_summary": {
    "ui-framework": ["react@19.0.0", "react-native@0.79.2"],
    "state-management": ["zustand@^5.0.3"],
    "database": ["drizzle-orm@^0.40.0"],
    "dependency-injection": ["tsyringe@^4.8.0"]
  }
}
```

---

### 6. `rules.json` — ⚙️ Reglas Machine-Readable

Input para `loom audit`. Consumible por CI/CD o git hooks.

```json
{
  "naming": {
    "files": { "dominant_style": "PascalCase" },
    "code": { "interfaces": { "prefix": "I", "count": 89 } }
  },
  "architecture": {
    "layer_boundaries": {
      "domain": { "forbidden_imports": ["infrastructure"] }
    }
  }
}
```

---

### 7. `plans-summary.md` — 📋 Estado de Planes

Resumen de documentacion y planes con progreso de checklists.

```markdown
## Implementation Plans
### Plan Maestro
Status: 5 done, 1 in-progress, 2 pending
- [x] Documentacion base
- [-] Motor de escenarios
- [ ] Generacion adaptativa
```

---

## 📂 Archivos Efimeros

### `.context/exports/`

Generados por `loom export --agent <name>`. Se regeneran bajo demanda.

| Archivo | Agente | Contenido |
|---------|--------|-----------|
| `CLAUDE.md` | Claude Code | System prompt completo |
| `.cursorrules` | Cursor IDE | Project type + rules |
| `AGENTS.md` | Codex / CLI agents | Directives + directory map |

### `.context/bundles/<slug>/`

Generados por `loom bundle "<task>" --save`.

- `bundle.md` — contexto compilado para la tarea
- `manifest.json` — trazabilidad: task, SHA, strategy, sections incluidas

### `.context/handoffs/<slug>.md`

Generados por `loom handoff "<task>" --save`. Resumen para retomar trabajo.

---

## 🔐 Estado Vivo: .loom/

`.loom/` es local por usuario. Nunca se commitea.

| Archivo | Que contiene | Formato |
|---------|-------------|---------|
| `inconsistencies.json` | Ultimo resultado de audit | JSON snapshot |
| `decisions.jsonl` | Decisiones arquitectonicas | JSONL append-only |
| `sessions.jsonl` | Log de sesiones con git metadata | JSONL append-only |
| `mutations.jsonl` | Cambios al contexto | JSONL append-only |

---

## 🔒 Seguridad

**Lo que `.context/` NUNCA contiene:**
- ❌ Codigo fuente real
- ❌ Contenido de archivos
- ❌ Valores de variables o secretos
- ❌ Datos personales

**Lo que SI contiene:**
- ✅ Nombres de archivos y directorios
- ✅ Nombres de dependencias y versiones
- ✅ Patrones de naming inferidos
- ✅ Titulos de documentos
- ✅ Reglas de boundaries

---

## 📋 Que va en Git

| Ruta | Git | Por que |
|------|-----|---------|
| `.context/*.md, *.json` | ✅ | Contexto canonico — el valor de Loom |
| `.context/exports/` | ❌ | Se regenera con `loom export` |
| `.context/bundles/` | ❌ | Se regenera con `loom bundle` |
| `.context/handoffs/` | 🟡 | Opcional — util para compartir estado |
| `.loom/` | ❌ | Estado local por usuario |

---

*Siguiente: [🔒 Seguridad →](./security.md)*
