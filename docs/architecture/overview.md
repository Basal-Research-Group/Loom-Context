# Arquitectura de Loom-Context

> *Loom usa Clean Architecture internamente para detectar Clean Architecture en otros proyectos.*

## Visión General

Loom-Context sigue una arquitectura de **pipeline unidireccional**: los datos fluyen desde el código fuente, pasan por scanners, se transforman en generators, y terminan como archivos `.context/` consumibles por IA.

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLI (cli.py)                              │
│  Punto de entrada: loom init | scan | prompt | audit | plan     │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     ENGINE (engine.py)                            │
│  Orquestador central — coordina scanners y generators            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              SECURITY LAYER (filter.py)                     │  │
│  │  .gitignore + .contextignore + hardcoded secrets           │  │
│  │  TODO file I/O pasa por aquí primero                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │Structure│ │  Deps   │ │  Code   │ │  Docs   │  ◄─ Scanners │
│  │ Scanner │ │ Scanner │ │ Scanner │ │ Scanner │              │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘              │
│       │           │           │           │                     │
│       └───────────┴─────┬─────┴───────────┘                     │
│                         │                                        │
│                         ▼                                        │
│                  ┌─────────────┐                                 │
│                  │ ScanResult  │  ◄─ Datos unificados           │
│                  └──────┬──────┘                                 │
│                         │                                        │
│       ┌─────────────────┼─────────────────┐                     │
│       ▼                 ▼                 ▼                     │
│  ┌─────────┐     ┌──────────┐     ┌──────────┐                │
│  │  Index  │     │ Context  │     │  Prompt  │  ◄─ Generators │
│  │Generator│     │Generator │     │Generator │                │
│  └─────────┘     └──────────┘     └──────────┘                │
│                         │                                        │
│                         ▼                                        │
│              ┌─────────────────┐                                │
│              │   .context/     │  ◄─ Output final               │
│              │  (7 archivos)   │                                │
│              └─────────────────┘                                │
│                                                                  │
│  ┌─────────┐  ┌──────────┐                                     │
│  │ Naming  │  │Structure │  ◄─ Auditors (usan rules.json)     │
│  │ Auditor │  │ Auditor  │                                     │
│  └─────────┘  └──────────┘                                     │
└──────────────────────────────────────────────────────────────────┘
```

## Componentes en Detalle

### 1. CLI (`cli.py`)

**Patrón:** Command Pattern via [Click](https://click.palletsprojects.com/)

El CLI es la interfaz pública. Cada comando es un `@click.command()` que instancia el `LoomEngine` y delega:

| Comando | Llama a | Resultado |
|---------|---------|-----------|
| `loom init` | `engine.init()` | `.context/` completo |
| `loom scan` | `engine.scan()` + `engine.generate_context()` | `.context/` actualizado |
| `loom prompt` | `engine.generate_prompt()` | Master prompt en stdout/archivo |
| `loom audit` | `NamingAuditor` + `StructureAuditor` | Tabla de violaciones |
| `loom plan` | `DocsScanner.scan()` | Resumen de planes |
| `loom watch` | Loop de `scan` + `generate_context` | Actualización continua |

**Output visual:** Usa [Rich](https://rich.readthedocs.io/) para tablas, paneles y colores en terminal.

### 2. Engine (`engine.py`)

**Patrón:** Facade + Mediator

El engine es el punto central que:
1. Instancia `LoomConfig` y `FileFilter`
2. Crea los 4 scanners, cada uno recibe el `FileFilter`
3. Ejecuta todos los scanners y merge resultados en un `ScanResult` (dict)
4. Pasa el `ScanResult` a los generators
5. Los generators escriben `.context/`

```python
class LoomEngine:
    def __init__(self, root):
        self.config = LoomConfig(root)       # Configuración
        self.file_filter = FileFilter(root)   # Capa de seguridad

    def scan(self) -> dict:
        # 4 scanners ejecutan en secuencia
        # Retorna dict con keys: structure, deps, code, docs

    def generate_context(self, scan_result) -> list[str]:
        # IndexGenerator + ContextGenerator
        # Escribe 7 archivos en .context/

    def generate_prompt(self) -> str:
        # PromptGenerator lee .context/ y compila

    def init(self) -> dict:
        # scan() + generate_context() en un solo paso
```

### 3. Security Layer (`security/filter.py`)

**Patrón:** Chain of Responsibility (3 filtros en cascada)

```
Archivo → ¿Está en .gitignore? ──yes──→ EXCLUIDO
           │ no
           ▼
         ¿Está en .contextignore? ──yes──→ EXCLUIDO
           │ no
           ▼
         ¿Es un secreto? ──yes──→ EXCLUIDO
         (.env, .pem, credentials...)
           │ no
           ▼
         INCLUIDO ✓
```

**Directorio hardcoded excluidos (siempre):**
`node_modules`, `.git`, `__pycache__`, `.expo`, `.next`, `dist`, `build`, `vendor`, `.venv`, `.cache`

**Patrones de secretos (siempre):**
`*.pem`, `*.key`, `.env*`, `credentials*`, `secrets*`, `*_rsa`, `service-account*.json`

### 4. Scanners (`scanners/`)

**Patrón:** Strategy Pattern — cada scanner implementa `BaseScanner.scan() → dict`

#### StructureScanner (`structure.py`)

El más complejo. Tres algoritmos principales:

**a) Detección de tipo de proyecto:**
```
¿Existe app.config.js?        → react-native-expo
¿Existe next.config.js?       → nextjs
¿Existe angular.json?         → angular
¿package.json tiene react-native? → react-native
¿package.json tiene react?    → react
¿Existe pyproject.toml?       → python
¿Existe Cargo.toml?           → rust
¿Existe go.mod?               → go
```

**b) Detección de arquitectura:**
```
{domain, infrastructure, presentation} ⊂ dirs  → clean-architecture
{ports, adapters} ⊂ dirs                       → hexagonal
{models, views, controllers} ⊂ dirs            → mvc
{features} ⊂ dirs                              → feature-based
```

**c) Anotación semántica:** 80+ mappings nombre→propósito:
```
"entities"    → "Domain entities/models"
"hooks"       → "Custom hooks"
"di"          → "Dependency injection configuration"
"orchestration" → "Flow orchestration"
"renderers"   → "UI renderers (Strategy pattern)"
```

#### DependencyScanner (`deps.py`)

Parsea archivos de dependencias y categoriza usando una **base de conocimiento interna de 130+ paquetes**:

```
zustand     → state-management
drizzle-orm → database
jest        → testing
tsyringe    → dependency-injection
expo-speech → tts
```

Para paquetes desconocidos, infiere categoría por nombre:
```
@types/*       → type-definitions
*eslint*       → linting
*-plugin       → plugin
expo-*         → expo-module
react-native-* → react-native-module
```

#### CodeScanner (`code.py`)

**Algoritmo de inferencia de naming:**

1. Recolecta todos los archivos de código
2. Samplea ~100 archivos (80% de `src/`, 20% resto)
3. Para cada archivo, clasifica el nombre: PascalCase, camelCase, kebab-case, snake_case
4. Lee las primeras 100 líneas de cada sample para extraer interfaces, clases, funciones
5. Detecta patrones de sufijo (Service, Repository, Mapper) y prefijo (I, use, Base)
6. Lee `tsconfig.json` para import aliases

**Principio:** Solo metadata. Lee contenido para inferir patrones, pero **nunca persiste** el contenido.

#### DocsScanner (`docs.py`)

1. Busca todos los `.md` en root y `docs/`
2. Extrae título (primer `#`), secciones (`##`, `###`)
3. Clasifica tipo: architecture, plan, feature, agent-guidelines, setup
4. Extrae items de status: `[x]` done, `[ ]` pending, tablas con estados

### 5. Generators (`generators/`)

**Patrón:** Template Method + Builder

#### IndexGenerator (`index.py`)

Genera `index.json` — el **entry point** para cualquier agente de IA. Incluye:
- Metadata del proyecto (nombre, tipo, arquitectura, lenguaje, runtime)
- Punteros a los otros 6 archivos
- `quick_rules`: las reglas más importantes en una lista plana
- Estadísticas (archivos, deps, docs)

#### ContextGenerator (`context.py`)

Usa **Jinja2 templates** para generar los archivos markdown y JSON:

```
templates/architecture.md.j2  →  .context/architecture.md
templates/naming.md.j2        →  .context/naming.md
templates/directory_map.md.j2 →  .context/directory-map.md
(datos directos)              →  .context/stack.json
(datos directos)              →  .context/rules.json
(generación directa)          →  .context/plans-summary.md
```

#### PromptGenerator (`prompt.py`)

Lee todos los archivos de `.context/` y los ensambla en un solo **master prompt**:

```
# Project Context: {name}
## Quick Rules (MUST follow)
{rules de index.json}
## Architecture
{architecture.md completo}
## Naming Conventions
{naming.md completo}
## Directory Map
{directory-map.md}
## Technology Stack
{stack.json formateado}
## Plans
{plans-summary.md}
## Agent Guidelines
{AGENTS.md si existe}
---
This context was generated by Loom-Context.
All suggestions MUST comply with the rules above.
```

### 6. Auditors (`auditors/`)

**Patrón:** Rule Engine

Los auditors leen `rules.json` y validan el código contra esas reglas:

#### NamingAuditor

- Carga reglas de naming de `.context/rules.json`
- Para cada archivo `.ts`/`.tsx`, busca interfaces sin prefijo `I`
- Genera `Violation` objects con: archivo, línea, regla, mensaje, severidad, sugerencia

#### StructureAuditor

- Carga boundaries de `.context/rules.json`
- Para cada archivo de código, extrae imports (regex)
- Resuelve cada import a su capa arquitectónica
- Si la capa violada está en `forbidden_imports`, genera `Violation`

```
Ejemplo de detección:
  Archivo:  src/core/bootstrap/initDb.ts
  Import:   @infrastructure/data/db/connection
  Capa:     core → importa de → infrastructure
  Regla:    core.forbidden_imports = [infrastructure]
  Resultado: ERROR — Layer violation
```

---

## Dependencias Externas

| Paquete | Versión | Para qué |
|---------|---------|----------|
| `click` | >= 8.1 | CLI framework |
| `rich` | >= 13.0 | Output bonito en terminal |
| `pathspec` | >= 0.12 | Parsing de .gitignore |
| `jinja2` | >= 3.1 | Templates para markdown |

**4 dependencias.** Loom es ligero por diseño.

---

*Siguiente: [Patrones de Diseño →](./patterns.md)*
