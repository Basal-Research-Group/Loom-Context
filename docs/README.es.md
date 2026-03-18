# 🕸️ Loom-Context

[![CI](https://github.com/jadruiz/Loom-Context/actions/workflows/ci.yml/badge.svg)](https://github.com/jadruiz/Loom-Context/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/loom-context)](https://pypi.org/project/loom-context/)
[![Python](https://img.shields.io/pypi/pyversions/loom-context)](https://pypi.org/project/loom-context/)
[![License](https://img.shields.io/github/license/jadruiz/Loom-Context)](../LICENSE)

**Contexto determinista y axiomatico para ingenieria AI-first.**

[English](../README.md) · Español

```
        .  *  .  *  .
         \  |  /
      ── (O O) ──
         /  |  \
        *  .  *  .  *

  menos tokens, mas senal
```

Loom no usa IA. Loom evita desperdiciar IA.

Escanea tu repo, infiere arquitectura y convenciones, y compila contexto compacto que cualquier agente (Claude, Codex, Cursor) puede consumir — para que dejen de releer 700 archivos y trabajen con los 7 que importan.

```
Sin Loom:   35KB de prompt  →  agente lee todo         →  deriva, desperdicio, alucinaciones
Con Loom:   2.6KB de bundle →  agente lee lo relevante →  precision, consistencia, ahorro
```

Sin cloud. Sin LLM. Sin deps pesadas. Analisis determinista en <2 segundos. 93% menos tokens.

```bash
pip install loom-context
cd tu-proyecto/
loom init .
```

> 📉 Probado en un proyecto React Native de 674 archivos: scan en 0.9s, 107 violaciones de boundary, bundles 93% mas pequenos que el prompt completo.

---

## ⚡ Inicio Rapido

```bash
loom init .                                  # scan + genera .context/ + .loom/
loom bundle "refactorizar auth" . --stdout   # contexto por tarea (93% mas chico)
loom export . --agent claude                 # exportar para tu agente
```

Listo. Tu agente tiene arquitectura, reglas, naming y boundaries — sin leer 700 archivos.

---

## 🎯 17 Comandos

### 🔍 Escaneo y Generacion

```bash
loom init .                    # Scan completo + .context/ + .loom/ + audit
loom scan .                    # Re-escanear y actualizar .context/
```

### 📝 Contexto para IA

```bash
loom prompt . --stdout         # Prompt maestro completo
loom focus "auth" . --stdout   # Prompt filtrado por tema
loom bundle "tarea" . --stdout # Bundle por tarea con manifest
loom handoff "tarea" . --save  # Resumen para retomar trabajo
loom export . --agent claude   # Formato para agente especifico
```

### ✅ Calidad y Auditoria

```bash
loom audit .                   # Validar reglas de naming + boundaries
loom audit . --summary         # Vista agrupada por directorio
loom enrich .                  # Re-auditar + refrescar + persistir
loom doctor .                  # Diagnostico de salud (11 checks)
loom metrics .                 # Metricas por capa arquitectonica
```

### 📊 Estado y Memoria

```bash
loom status .                  # Dashboard de salud del proyecto
loom decide "..." -r "..." -s architecture  # Registrar decision
loom log "nota" -p .           # Memoria de sesion
loom plan .                    # Resumir docs/planes
loom plan . --generate         # Generar plan de implementacion
loom report .                  # Analytics de uso
loom watch . --interval 60     # Re-scan continuo
```

---

## 📁 Que Genera Loom

```
.context/                      ← canonico, reproducible, compartible
  index.json                   ← entry point + quick_rules
  architecture.md              ← patrones + layer boundaries
  naming.md                    ← convenciones + suffix/prefix
  directory-map.md             ← arbol de directorios anotado
  stack.json                   ← dependencias categorizadas
  rules.json                   ← reglas machine-readable para audit
  plans-summary.md             ← progreso de docs y planes
  exports/                     ← formatos por agente
  bundles/                     ← contexto por tarea + manifests

.loom/                         ← estado vivo, local por usuario
  inconsistencies.json         ← hallazgos del ultimo audit
  decisions.jsonl              ← decision records
  sessions.jsonl               ← log de sesiones con git metadata
  mutations.jsonl              ← historial de cambios al contexto
  reports/                     ← metricas, deltas, planes generados
```

---

## 🤖 Exportar para tu Agente

```bash
loom export . --agent claude   # → .context/exports/CLAUDE.md
loom export . --agent cursor   # → .context/exports/.cursorrules
loom export . --agent codex    # → .context/exports/AGENTS.md
loom export . --agent generic  # → .context/exports/.loom-export.md
loom export . --agent claude --install  # → CLAUDE.md en raiz del proyecto
```

---

## 🔍 Que Detecta

| Area | Deteccion |
|------|-----------|
| 🏗️ Arquitectura | Clean Architecture, Hexagonal, MVC, MVVM, Pipeline, Feature-based, Layered, Monorepo |
| 📦 Tipo de proyecto | React Native/Expo, Next.js, Angular, Vue, Python, Rust, Go, Java, y mas |
| 🏷️ Naming | PascalCase, camelCase, kebab-case, snake_case, prefijo I-, prefijo use-, sufijos por rol |
| 📦 Stack | 130+ paquetes conocidos categorizados (ui, state, db, testing, DI, etc.) |
| 📄 Docs | Markdown con frontmatter, status de planes, secciones |
| ⚙️ Reglas | Layer boundaries, convenciones de naming, import aliases |
| 📊 Metricas | Archivos por capa, balance, naming por rol |

---

## 🔒 Seguridad

Tres capas de filtrado — tu codigo fuente nunca aparece en el output:

1. ✅ Respeta `.gitignore`
2. ✅ Respeta `.contextignore`
3. ✅ Siempre excluye `.env`, `*.pem`, `*.key`, credenciales

Output es solo metadata: nombres de archivos, patrones, reglas, estructura. Nunca codigo fuente.

---

## 🔁 Flujo Diario

```bash
# Manana: ver estado
loom status .
loom scan .

# Antes de una tarea: contexto enfocado
loom bundle "implementar flujo de pago" . --stdout | pbcopy

# Durante el trabajo: registrar decisiones
loom decide "usar adapter de Stripe" -r "estandar del equipo" -s architecture

# Al terminar: persistir y handoff
loom enrich .
loom handoff "flujo de pago" . --save
```

---

## 📊 Resultados Reales

Probado en un proyecto React Native de 674 archivos:

| Metrica | Resultado |
|---------|-----------|
| Tiempo de scan | 0.9s |
| Archivos analizados | 674 archivos, 95 dependencias, 59 docs |
| Arquitectura detectada | Clean Architecture + Hexagonal + Feature-based |
| Patrones de naming | 67 Repositories, 28 Mappers, 17 Services, 14 ViewModels |
| Violaciones de boundary | 107 (todas en `core/` importando de `infrastructure/`) |
| Bundle vs prompt | 2.6KB vs 35KB (93% reduccion) |
| Naming por rol | hooks=camelCase 100%, components=PascalCase 92% |
| Balance de capas | 73% (core 33%, infra 29%, presentation 25%, domain 11%) |
| Formatos de export | Claude, Cursor, Codex, Generic |

---

## 📚 Documentacion

| Guia | Que cubre |
|------|-----------|
| [🚀 Inicio Rapido](guides/quickstart.md) | Instalacion, primer scan, flujo diario |
| [📖 Referencia CLI](guides/cli-reference.md) | Los 17 comandos con ejemplos |
| [📁 Output .context/](guides/context-output.md) | Estructura de .context/ y .loom/ |
| [🔒 Seguridad](guides/security.md) | Modelo de filtrado de 3 capas |
| [📐 Buenas Practicas](guides/best-practices.md) | Patrones individuales, equipo e IA |
| [🧠 Filosofia](guides/philosophy.md) | Analogia del cerebro + referencias cientificas |
| [🕸️ Loomy](guides/loomy.md) | La mascota neurona-arana |
| [🛡️ Calidad](guides/quality.md) | 7 capas de calidad, herramientas, cobertura |
| [📋 Roadmap](plans/roadmap-v0.2-v0.4.md) | Plan de versiones con deliveries |

---

## 🛠️ Desarrollo

```bash
git clone https://github.com/jadruiz/Loom-Context.git
cd Loom-Context
pip install -e ".[dev]"

pytest                         # 281 tests, ~8s
ruff check src/ tests/         # lint
ruff format --check src/ tests/  # format
```

- [CONTRIBUTING.md](../CONTRIBUTING.md) — setup, convenciones, proceso de PR
- [CHANGELOG.md](../CHANGELOG.md) — historial de releases
- [SECURITY.md](../SECURITY.md) — reporte de vulnerabilidades

---

## Requisitos

- Python 3.9+
- 4 dependencias runtime: `click`, `rich`, `pathspec`, `jinja2`
- Cero dependencias de IA/ML en la instalacion base

## Licencia

Apache License 2.0.
