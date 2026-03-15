# Diagrama: Mapa de Componentes

> *Relacion entre todos los componentes de Loom-Context.*

## Diagrama de Dependencias

```
                          ┌──────────┐
                          │  cli.py  │
                          │  (Click) │
                          └────┬─────┘
                               │ usa
                               ▼
                         ┌───────────┐
                         │ engine.py │
                         │ (Facade)  │
                         └─────┬─────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────┐    ┌────────────┐   ┌──────────┐
       │ config.py│    │ security/  │   │ scanners/│
       │          │    │ filter.py  │   │          │
       └──────────┘    └──────┬─────┘   └────┬─────┘
                              │               │
                              │    ┌──────────┼──────────┬──────────┐
                              │    │          │          │          │
                              │    ▼          ▼          ▼          ▼
                              │ structure  deps.py   code.py   docs.py
                              │   .py
                              │    │          │          │          │
                              │    └──────────┴────┬─────┴──────────┘
                              │                    │
                              │                    ▼
                              │             ┌────────────┐
                              │             │ ScanResult │
                              │             │   (dict)   │
                              │             └──────┬─────┘
                              │                    │
                              │    ┌───────────────┼───────────────┐
                              │    │               │               │
                              │    ▼               ▼               ▼
                              │ generators/   generators/   generators/
                              │  index.py     context.py    prompt.py
                              │    │               │               │
                              │    │               │    ┌──────────┘
                              │    │               │    │
                              │    │               ▼    │
                              │    │        ┌──────────┐│
                              │    │        │templates/││
                              │    │        │  *.j2    ││
                              │    │        └──────────┘│
                              │    │               │    │
                              │    └───────┬───────┘    │
                              │            │            │
                              │            ▼            ▼
                              │     ┌────────────┐  ┌────────┐
                              │     │ .context/  │  │ prompt │
                              │     │ (7 files)  │  │ (text) │
                              │     └──────┬─────┘  └────────┘
                              │            │
                              │            ▼
                              │     ┌────────────┐
                              └────►│ auditors/  │
                                    │ naming.py  │
                                    │ structure  │
                                    │   .py      │
                                    └────────────┘
```

## Tabla de Componentes

| Componente | Tipo | Responsabilidad | Depende de |
|------------|------|----------------|------------|
| `cli.py` | Interface | Comandos CLI con Click + Rich | engine |
| `engine.py` | Facade | Orquesta scanners y generators | config, filter, scanners, generators |
| `config.py` | Value Object | Paths y configuracion | - |
| `filter.py` | Filter Chain | Exclusion de archivos | pathspec |
| `structure.py` | Scanner | Tipo, arquitectura, arbol | base, filter |
| `deps.py` | Scanner | Dependencias y stack | base, filter |
| `code.py` | Scanner | Naming y convenciones | base, filter |
| `docs.py` | Scanner | Documentacion y planes | base, filter |
| `index.py` | Generator | index.json | scan result |
| `context.py` | Generator | 7 archivos .context/ | scan result, templates, jinja2 |
| `prompt.py` | Generator | Master prompt | .context/ files |
| `naming.py` | Auditor | Validacion de naming | filter, rules.json |
| `structure.py` | Auditor | Validacion de boundaries | filter, rules.json |
| `*.j2` | Template | Estructura de output markdown | jinja2 |

## Ciclo de Vida de los Datos

```
1. ENTRADA
   Proyecto real: archivos, dirs, configs, docs
                    │
2. FILTRADO
   FileFilter excluye noise y secretos
                    │
3. PERCEPCION
   4 Scanners extraen metadata (nunca contenido)
                    │
4. FUSION
   Engine merge en ScanResult (dict unificado)
                    │
5. TRANSFORMACION
   Generators + Templates → archivos estructurados
                    │
6. OUTPUT
   .context/ con 7 archivos listos para IA
                    │
7. CONSUMO
   IA lee → genera codigo alineado con tu arquitectura
                    │
8. VALIDACION
   Auditors verifican que el codigo cumple las reglas
                    │
9. FEEDBACK
   Violaciones → correccion → nuevo scan → ciclo continua
```

## Extensibilidad

Para agregar un nuevo scanner:

```python
# src/loom_context/scanners/git_scanner.py
class GitScanner(BaseScanner):
    def scan(self) -> dict[str, Any]:
        # Analizar historial git, contributors, frecuencia de cambios
        return {"git": {...}}
```

Para agregar un nuevo auditor:

```python
# src/loom_context/auditors/imports_auditor.py
class ImportsAuditor:
    def audit(self) -> list[Violation]:
        # Verificar imports circulares, unused imports, etc.
        return [...]
```

Para agregar un nuevo template:

```jinja2
{# src/loom_context/templates/new_output.md.j2 #}
# {{ title }}
{% for item in items %}
- {{ item }}
{% endfor %}
```

La arquitectura de plugins esta pensada para que Loom crezca sin romper lo existente.

---

*[Volver al indice →](../INDEX.md)*
