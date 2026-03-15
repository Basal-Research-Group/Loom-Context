# Loom-Context Documentation

> *"El código es lo que escribimos. El contexto es cómo sobrevivimos."*

## TL;DR

Loom-Context es el **sistema nervioso** de tu proyecto. Así como el cerebro humano no reprocesa toda la realidad en cada instante — usa memoria de trabajo, patrones aprendidos y atajos cognitivos — Loom construye una **capa de contexto arquitectónico** que los agentes de IA leen como su "memoria de largo plazo" sobre tu proyecto. Sin Loom, cada sesión con IA empieza desde cero. Con Loom, la IA **recuerda** tu arquitectura, tus reglas y tu intención.

```
pip install loom-context
cd tu-proyecto/
loom init .
```

En ~1 segundo, genera `.context/` con 7 archivos que cualquier LLM puede consumir.

---

## Índice de Documentación

### Conceptual
| Documento | Descripción |
|-----------|-------------|
| [Filosofía y Analogía](./guides/philosophy.md) | La analogía del cerebro: por qué Loom existe y cómo opera |
| [Arquitectura de Loom](./architecture/overview.md) | Diseño interno de Loom-Context como herramienta |
| [Patrones de Diseño](./architecture/patterns.md) | Clean Architecture, Hexagonal, y cómo Loom los detecta |
| [Referencias Científicas](./REFERENCES.md) | Fundamentos académicos, fuentes primarias, citas |

### Técnico
| Documento | Descripción |
|-----------|-------------|
| [Guía de Inicio Rápido](./guides/quickstart.md) | Instalación, primer scan, uso básico |
| [Estructura de Directorios](./architecture/directory-structure.md) | Anatomía completa de Loom-Context |
| [Referencia del CLI](./guides/cli-reference.md) | Todos los comandos con ejemplos |
| [El Output .context/](./guides/context-output.md) | Qué genera Loom y cómo lo consume la IA |
| [Seguridad](./guides/security.md) | Cómo Loom protege tu código |
| [Buenas Prácticas](./guides/best-practices.md) | Patrones recomendados para equipos |

### Diagramas
| Diagrama | Descripción |
|----------|-------------|
| [Flujo de Datos](./diagrams/data-flow.md) | Cómo fluye la información desde tu código hasta el prompt |
| [Mapa de Componentes](./diagrams/component-map.md) | Relación entre scanners, generators y auditors |

---

## Estructura del Repositorio

```
Loom-Context/
├── src/loom_context/           # Motor principal
│   ├── cli.py                  # Interfaz de línea de comandos
│   ├── engine.py               # Orquestador central (el "córtex")
│   ├── config.py               # Configuración
│   ├── scanners/               # Sensores (input del mundo real)
│   │   ├── structure.py        # Detector de arquitectura
│   │   ├── deps.py             # Analizador de dependencias
│   │   ├── code.py             # Inferencia de naming
│   │   └── docs.py             # Indexador de documentación
│   ├── generators/             # Output (la respuesta del cerebro)
│   │   ├── index.py            # Genera el índice maestro
│   │   ├── context.py          # Genera todos los archivos .context/
│   │   └── prompt.py           # Compila el prompt para IA
│   ├── auditors/               # Validadores (sistema inmune)
│   │   ├── naming.py           # Auditoría de convenciones
│   │   └── structure.py        # Auditoría de boundaries
│   ├── security/               # Barrera hematoencefálica
│   │   └── filter.py           # Filtrado de secretos y exclusiones
│   └── templates/              # Plantillas Jinja2
├── tests/                      # Tests (25 passing)
├── docs/                       # Esta documentación
└── pyproject.toml              # Configuración del paquete
```

## Links Rápidos

- **GitHub:** [github.com/jadruiz/Loom-Context](https://github.com/jadruiz/Loom-Context)
- **Licencia:** MIT
- **Python:** >= 3.9
- **Versión actual:** 0.1.0
