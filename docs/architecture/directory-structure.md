# Estructura de Directorios de Loom-Context

> *Anatomía completa del proyecto — cada archivo con su propósito.*

## Vista General

```
Loom-Context/
│
├── src/loom_context/                # Paquete Python principal
│   │
│   ├── __init__.py                  # Version: __version__ = "0.1.0"
│   ├── cli.py                       # [CÓRTEX] CLI con Click — 6 comandos
│   ├── engine.py                    # [CÓRTEX] Orquestador central
│   ├── config.py                    # Configuración y paths
│   │
│   ├── scanners/                    # [SENSORES] Percepción del proyecto
│   │   ├── __init__.py
│   │   ├── base.py                  # ABC: BaseScanner.scan() → dict
│   │   ├── structure.py             # Vista: tipo de proyecto, arquitectura, árbol
│   │   ├── deps.py                  # Tacto: dependencias, package managers
│   │   ├── code.py                  # Oído: naming, convenciones, import aliases
│   │   └── docs.py                  # Lectura: documentación, planes, status
│   │
│   ├── generators/                  # [OUTPUT] Producción de contexto
│   │   ├── __init__.py
│   │   ├── index.py                 # Genera index.json (entry point IA)
│   │   ├── context.py               # Genera los 7 archivos de .context/
│   │   └── prompt.py                # Compila master prompt para IA
│   │
│   ├── auditors/                    # [INMUNE] Detección de anomalías
│   │   ├── __init__.py
│   │   ├── naming.py                # Valida convenciones de nombres
│   │   └── structure.py             # Valida boundaries arquitectónicas
│   │
│   ├── security/                    # [BARRERA] Protección de información
│   │   ├── __init__.py
│   │   └── filter.py                # FileFilter: gitignore + secrets
│   │
│   └── templates/                   # Plantillas Jinja2 para output
│       ├── architecture.md.j2       # Template: reglas de arquitectura
│       ├── naming.md.j2             # Template: convenciones de naming
│       └── directory_map.md.j2      # Template: árbol anotado
│
├── tests/                           # Tests unitarios (25 tests)
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures: tmp_project simulado
│   └── test_cli.py                  # Tests de todas las capas
│
├── docs/                            # Documentación (este directorio)
│   ├── INDEX.md                     # Índice maestro
│   ├── guides/                      # Guías de uso
│   ├── architecture/                # Diseño interno
│   └── diagrams/                    # Diagramas
│
├── pyproject.toml                   # Config: hatchling, deps, CLI entry
├── README.md                        # Descripción del proyecto
└── LICENSE                          # MIT — J. Adrian Ruiz C.
```

## Métricas del Código

| Métrica | Valor |
|---------|-------|
| Archivos Python | 16 |
| Templates Jinja2 | 3 |
| Tests | 25 |
| Dependencias runtime | 4 |
| Líneas de código (aprox) | ~2,500 |
| Tiempo de scan (proyecto 700 archivos) | ~1 segundo |

## Output: `.context/` en el Proyecto Target

Cuando ejecutas `loom init` en un proyecto, genera esta estructura:

```
tu-proyecto/
├── .context/                        # Generado por Loom
│   ├── index.json                   # ENTRY POINT para IA
│   │                                # - project metadata
│   │                                # - quick_rules (lo más importante)
│   │                                # - punteros a otros archivos
│   │                                # - estadísticas
│   │
│   ├── architecture.md              # Arquitectura detectada
│   │                                # - tipo de proyecto
│   │                                # - patrones (clean-arch, hexagonal...)
│   │                                # - layer boundaries con tabla
│   │                                # - dirección de dependencias
│   │
│   ├── naming.md                    # Convenciones de naming
│   │                                # - estilo dominante de archivos
│   │                                # - patrones de sufijo (Service, Repo...)
│   │                                # - patrones de prefijo (I, use, Base...)
│   │                                # - naming en código (interfaces, clases...)
│   │                                # - import aliases
│   │
│   ├── directory-map.md             # Árbol anotado
│   │                                # - cada directorio con su propósito
│   │                                # - conteo de archivos por directorio
│   │                                # - profundidad hasta 4 niveles
│   │
│   ├── stack.json                   # Stack tecnológico
│   │                                # - package manager
│   │                                # - deps agrupadas por categoría
│   │                                # - total de dependencias
│   │
│   ├── rules.json                   # Reglas machine-readable
│   │                                # - naming rules (archivo + código)
│   │                                # - architecture boundaries
│   │                                # - import aliases
│   │
│   └── plans-summary.md            # Resumen de planes
│                                    # - docs de arquitectura indexados
│                                    # - planes con status (done/pending)
│                                    # - otros docs por tipo
│
├── src/                             # Tu código (no se modifica)
├── docs/                            # Tu documentación (no se modifica)
└── ...
```

## Cómo la IA Consume `.context/`

```
Nivel 1 — Contexto inmediato (30 seg):
  IA lee index.json → quick_rules
  "Ah, es clean-architecture, interfaces con I prefix,
   core no puede importar de infrastructure"

Nivel 2 — Contexto medio (2 min):
  IA lee architecture.md + naming.md
  "Entiendo las 4 capas, los boundaries, los
   11 patrones de suffix y prefix"

Nivel 3 — Contexto completo (5 min):
  IA lee directory-map.md + stack.json + plans-summary.md
  "Sé exactamente dónde vive cada cosa, qué
   tecnologías usan y hacia dónde va el proyecto"
```

---

*Siguiente: [Guía de Inicio Rápido →](../guides/quickstart.md)*
