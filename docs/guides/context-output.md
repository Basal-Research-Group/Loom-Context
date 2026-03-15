# El Output: .context/

> *Lo que genera Loom es lo que la IA consume. Cada archivo tiene un proposito especifico.*

## Los 7 Archivos

### 1. `index.json` — El Entry Point

**Analogia:** La corteza prefrontal — atencion selectiva, lo primero que se procesa.

La IA debe leer este archivo **primero**. Contiene:

```json
{
  "loom_version": "0.1.0",
  "project": {
    "name": "mi-proyecto",
    "type": "react-native-expo",
    "architecture": ["clean-architecture", "hexagonal", "feature-based"],
    "language": "TypeScript",
    "runtime": "react@19.0.0 + react-native@0.79.2 + expo@^53.0.9"
  },
  "context_files": {
    "architecture": ".context/architecture.md",
    "naming": ".context/naming.md",
    "directory_map": ".context/directory-map.md",
    "stack": ".context/stack.json",
    "rules": ".context/rules.json",
    "plans_summary": ".context/plans-summary.md"
  },
  "agents_md": "AGENTS.md",
  "quick_rules": [
    "Layer boundary: domain MUST NOT import from infrastructure",
    "Layer boundary: core MUST NOT import from presentation",
    "Interfaces MUST have 'I' prefix (e.g., IUserRepository)",
    "React hooks MUST have 'use' prefix (e.g., useLogoutApp)",
    "Repository files follow pattern: {Name}Repository.ts",
    "Service files follow pattern: {Name}Service.ts"
  ],
  "stats": {
    "total_files": 663,
    "total_code_files": 702,
    "total_docs": 52,
    "total_dependencies": 95
  },
  "generated_at": "2026-03-14T21:28:24.171346+00:00"
}
```

**`quick_rules`** es la clave: son las reglas mas importantes en texto plano. Un agente que solo lea esto ya tiene suficiente contexto para no romper tu proyecto.

---

### 2. `architecture.md` — Patrones y Boundaries

**Analogia:** Modelo mental — como se organiza el sistema.

Contiene:
- Tipo de proyecto detectado
- Patrones arquitectonicos identificados
- Tabla de layer boundaries (que capa puede importar de cual)
- Diagrama de direccion de dependencias

```markdown
## Layer Boundaries
| Layer | MUST NOT import from |
|-------|---------------------|
| domain | infrastructure, presentation |
| core | infrastructure, presentation |
| infrastructure | presentation |
| presentation | infrastructure |

## Dependency Direction
presentation -> core -> domain <- infrastructure
```

---

### 3. `naming.md` — Convenciones de Nombres

**Analogia:** Vocabulario — como se nombran las cosas en este proyecto.

Contiene:
- Estilo dominante de archivos (PascalCase, camelCase, etc.)
- Patrones de sufijo con ejemplos reales (Service, Repository, Mapper...)
- Patrones de prefijo con ejemplos (I, use, Base...)
- Naming a nivel de codigo (interfaces, clases, funciones)
- Import aliases de tsconfig.json

---

### 4. `directory-map.md` — Arbol Anotado

**Analogia:** Mapa espacial — donde vive cada cosa.

```
core/                    # Core layer - orchestration, DI, services
  bootstrap/             # Application initialization (11 files)
  di/                    # Dependency injection configuration (7 files)
  orchestration/         # Flow orchestration
  state/                 # State management
domain/                  # Domain layer - entities, ports, use cases
  entities/              # Domain entities/models (28 files)
  ports/                 # Port interfaces (6 files)
  repositories/          # Data access layer (20 files)
```

Cada directorio tiene una **anotacion semantica** y un conteo de archivos. La IA sabe exactamente donde crear un nuevo archivo.

---

### 5. `stack.json` — Stack Tecnologico

**Analogia:** Conocimiento del entorno — que herramientas hay disponibles.

```json
{
  "package_manager": "pnpm",
  "stack_summary": {
    "ui-framework": ["react@19.0.0", "react-native@0.79.2"],
    "state-management": ["zustand@^5.0.3"],
    "database": ["drizzle-orm@^0.40.0", "expo-sqlite@~15.2.14"],
    "dependency-injection": ["tsyringe@^4.8.0"],
    "validation": ["zod@^3.25.17"],
    "testing": ["jest@^29.7.0", "@playwright/test@^1.52.0"],
    "tts": ["expo-speech@~13.1.11", "react-native-tts@^4.1.0"]
  }
}
```

Esto evita que la IA sugiera `npm install redux` cuando ya usas `zustand`, o `sequelize` cuando ya usas `drizzle-orm`.

---

### 6. `rules.json` — Reglas Machine-Readable

**Analogia:** Reglas internalizadas — que se puede y que no.

```json
{
  "naming": {
    "files": {
      "dominant_style": "PascalCase",
      "suffix_patterns": [
        {"suffix": "Repository", "pattern": "{Name}Repository.ts"},
        {"suffix": "Service", "pattern": "{Name}Service.ts"}
      ],
      "prefix_patterns": [
        {"prefix": "I", "pattern": "I{Name}.ts", "description": "Interface prefix"},
        {"prefix": "use", "pattern": "use{Name}.ts", "description": "React hook prefix"}
      ]
    },
    "code": {
      "interfaces": {"format": "PascalCase", "prefix": "I", "count": 89},
      "classes": {"format": "PascalCase", "count": 45}
    }
  },
  "architecture": {
    "layer_boundaries": {
      "domain": {"forbidden_imports": ["infrastructure", "presentation"]},
      "core": {"forbidden_imports": ["infrastructure", "presentation"]}
    }
  },
  "imports": {
    "aliases": {
      "@domain/*": "src/domain/*",
      "@core/*": "src/core/*"
    }
  }
}
```

Este archivo es el input para `loom audit`. Tambien puede ser consumido programaticamente por CI/CD o git hooks.

---

### 7. `plans-summary.md` — Estado de Planes

**Analogia:** Intenciones — hacia donde va el proyecto.

```markdown
# Project Plans & Documentation Summary

## Architecture Documentation
- **Capas y Modulos** (`docs/architecture/capas.md`, 12.0KB)
  - Principios de arquitectura
  - Regla de dependencia
  - Modulos del sistema

## Implementation Plans

### Plan Maestro
Path: `docs/plans/00-indice.md` (5.2KB)
Status: 5 done, 1 in-progress, 2 pending

- [x] Documentacion base
- [x] Setup de proyecto
- [-] Motor de escenarios
- [ ] Generacion adaptativa
```

---

## Seguridad del Output

**Lo que `.context/` NUNCA contiene:**
- Codigo fuente real
- Contenido de archivos
- Valores de variables
- Secretos o credenciales
- Datos personales

**Lo que SI contiene:**
- Nombres de archivos y directorios
- Nombres de dependencias y versiones
- Patrones de naming inferidos
- Titulos de documentos
- Estructura de directorios
- Reglas de boundaries

---

## Commitear o No `.context/`

| Escenario | Recomendacion |
|-----------|--------------|
| Proyecto personal | Commitear — sirve como documentacion viva |
| Equipo pequeno (confianza) | Commitear — todos se benefician |
| Open source | `.gitignore` — no exponer estructura interna |
| Empresa con compliance | `.gitignore` + generar localmente |

Para excluir:
```bash
echo ".context/" >> .gitignore
```

---

*Siguiente: [Seguridad →](./security.md)*
