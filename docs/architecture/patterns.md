# Patrones de Diseño que Loom Detecta y Usa

> *Loom no solo detecta patrones — los practica.*

## Patrones que Loom Detecta en tu Proyecto

### Clean Architecture

```
                    ┌───────────────────┐
                    │     DOMAIN        │
                    │  (Entities, Ports)│
                    │  Cero dependencias│
                    └────────▲──────────┘
                             │ depende de
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴───────┐     │    ┌─────────┴────────┐
     │     CORE       │     │    │ INFRASTRUCTURE    │
     │ (Orchestration,│     │    │ (DB, APIs,        │
     │  State, DI)    │     │    │  Adapters)        │
     └────────▲───────┘     │    └──────────────────┘
              │              │
     ┌────────┴───────┐     │
     │  PRESENTATION  │─────┘
     │ (UI, Screens,  │
     │  Components)   │
     └────────────────┘
```

**Cómo Loom lo detecta:**
1. Busca directorios `domain`, `infrastructure`/`infra`, `presentation`/`ui` bajo `src/`
2. Si los 3 existen → `clean-architecture` confirmada
3. Genera reglas de boundary automáticas:
   - `domain` → no importa de nadie
   - `core` → solo importa de `domain`
   - `infrastructure` → importa de `domain` y `core`
   - `presentation` → importa de `core` y `domain`, **nunca** de `infrastructure`

**Analogía cerebral:** Es como la separación entre el tronco encefálico (domain — funciones vitales puras), el sistema límbico (core — coordinación), la corteza motora (infrastructure — ejecuta acciones) y la corteza visual (presentation — percepción).

### Hexagonal (Ports & Adapters)

```
          ┌─────────────┐
          │   DOMAIN    │
          │ ┌─────────┐ │
          │ │  PORTS  │ │ ◄── Interfaces/contratos
          │ └────▲────┘ │
          └──────┼──────┘
                 │ implementa
          ┌──────┴──────┐
          │  ADAPTERS   │
          │ (concreto)  │
          └─────────────┘
```

**Cómo Loom lo detecta:**
1. Si dentro de `domain/` existe `ports/` → hexagonal detectado
2. Si existen directorios `adapters/` en `infrastructure/` o `presentation/` → confirmado
3. Genera regla: `ports` no puede importar de `adapters`

**Analogía cerebral:** Los puertos son como los receptores neuronales — definen *qué* señal aceptan. Los adaptadores son los neurotransmisores específicos que encajan en esos receptores. Puedes cambiar el neurotransmisor (implementación) sin cambiar el receptor (contrato).

### MVC (Model-View-Controller)

```
    User ──→ Controller ──→ Model
                  │            │
                  └──→ View ◄──┘
```

**Cómo Loom lo detecta:**
- Directorios `models`, `views`, `controllers` bajo `src/`
- Regla: `models` no importa de `views` ni `controllers`

### Feature-Based

```
    src/
    ├── features/
    │   ├── auth/          # Auto-contenido
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   ├── services/
    │   │   └── screens/
    │   ├── payments/      # Auto-contenido
    │   └── profile/       # Auto-contenido
```

**Cómo Loom lo detecta:**
- Directorio `features/` o `modules/` con subdirectorios que contienen su propia estructura
- Compatible con Clean Architecture (feature-based dentro de `presentation/`)

### Combinaciones

Loom detecta **múltiples patrones simultáneos**. Un proyecto real frecuentemente combina:

```
clean-architecture + hexagonal + feature-based
```

Esto significa:
- 4 capas principales (domain, core, infrastructure, presentation)
- Ports & Adapters dentro de domain
- Features auto-contenidas dentro de presentation

---

## Patrones que Loom Usa Internamente

### Strategy Pattern → Scanners

Cada scanner es una estrategia intercambiable que implementa `BaseScanner.scan()`:

```python
class BaseScanner(ABC):
    @abstractmethod
    def scan(self) -> dict[str, Any]: ...

class StructureScanner(BaseScanner): ...
class DependencyScanner(BaseScanner): ...
class CodeScanner(BaseScanner): ...
class DocsScanner(BaseScanner): ...
```

Agregar un nuevo scanner (e.g., `GitScanner` para analizar historial) es crear una nueva clase y registrarla en el engine.

### Facade Pattern → Engine

`LoomEngine` simplifica la complejidad detrás de una interfaz limpia:

```python
engine = LoomEngine("/path/to/project")
engine.init()  # ← una línea, internamente ejecuta 4 scanners + 3 generators
```

### Chain of Responsibility → Security Filter

Tres filtros en cascada. Si cualquiera dice "excluir", el archivo se excluye:

```
.gitignore → .contextignore → Hardcoded Secrets
```

### Template Method → Generators

Los templates Jinja2 definen la *estructura*, los generators proveen los *datos*:

```
Template (estructura fija)  +  ScanResult (datos variables)  =  Output final
```

### Builder Pattern → PromptGenerator

El prompt se construye paso a paso, sección por sección:

```python
sections = []
sections.append(header)           # 1. Metadata
sections.append(quick_rules)      # 2. Reglas rápidas
sections.append(architecture)     # 3. Arquitectura
sections.append(naming)           # 4. Naming
sections.append(directory_map)    # 5. Mapa
sections.append(stack)            # 6. Stack
sections.append(plans)            # 7. Planes
return "\n".join(sections)
```

---

## Tabla de Patrones Detectables

| Patrón | Señales de detección | Reglas generadas |
|--------|---------------------|-----------------|
| Clean Architecture | `domain/` + `infrastructure/` + `presentation/` | Boundaries entre capas |
| Hexagonal | `ports/` + `adapters/` | Ports no importa de adapters |
| MVC | `models/` + `views/` + `controllers/` | Models no importa de views/controllers |
| MVVM | `models/` + `views/` + `viewmodels/` | - |
| Feature-Based | `features/` o `modules/` | - |
| Layered | `controllers/` + `services/` + `repositories/` | Controllers no importa de repositories |
| Repository | Archivos `*Repository.ts` | Suffix pattern |
| Strategy | Archivos `*Strategy.ts` | Suffix pattern |
| Adapter | Archivos `*Adapter.ts` | Suffix pattern |
| Factory | Archivos `*Factory.ts` | Suffix pattern |
| Observer/Event | Directorio `events/` o `bus/` | Annotation |

---

## Patrones de Naming Detectables

| Patrón | Ejemplo | Detección |
|--------|---------|-----------|
| Interface prefix | `IUserRepository` | >60% de interfaces usan `I` prefix |
| Hook prefix | `useAuth` | Archivos que empiezan con `use` + PascalCase |
| Abstract prefix | `AbstractGenerator` | Archivos con `Abstract` prefix |
| PascalCase files | `UserService.ts` | Clasificación de case por regex |
| camelCase files | `useAuth.ts` | Clasificación de case por regex |
| kebab-case files | `user-service.ts` | Clasificación de case por regex |
| snake_case files | `user_service.py` | Clasificación de case por regex |
| Role suffixes | `AuthService`, `UserMapper` | Conteo de archivos con suffix |

---

*Siguiente: [Estructura de Directorios →](./directory-structure.md)*
