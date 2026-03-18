---
type: delivery
version: "0.3.0"
status: in-progress
prerequisite: "0.2.0"
scope: scanner, cli, infra
languages: [python]
patterns: [strategy, decorator, observer]
progress: 6/6
---

# v0.3.0 — Analisis Profundo y Observabilidad

## TL;DR

Loom pasa de "detectar arquitectura" a "medir salud". Naming por rol, violaciones agrupadas con prioridad, metricas por capa, soporte monorepo, y observabilidad de uso.

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Tareas](#tareas)
- [Mapa de independencia](#mapa-de-independencia)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

Loom v0.2.0 detecta arquitectura y naming pero no mide salud. Un proyecto real tiene 109 violaciones sin prioridad, naming al 50% de confianza porque mezcla roles, y no hay metricas cuantitativas. El monorepo se detecta como "flat".

## Analogia

v0.2.0 es como un medico que te dice "tienes fiebre". v0.3.0 es el medico que te dice "tienes fiebre de 39.2, probablemente por infeccion en la garganta, toma primero antibiotico y luego analgesico".

---

## Tareas

Cada tarea es independiente. Ningun agente toca los mismos archivos que otro. Se pueden ejecutar en paralelo sin conflictos.

---

### Tarea 1: Naming por Rol

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `scanners/code.py`, `models.py`, `templates/naming.md.j2`
- **No tocar:** engine.py, cli/, generators/, auditors/, store/, selector/

**Problema:** Naming global dice 50% PascalCase + 48% camelCase = "mixto". Pero componentes son PascalCase y hooks son camelCase — son roles distintos, no inconsistencia.

**Entregables:**
- [ ] Agrupar archivos por rol (componente, hook, service, repository, etc.)
- [ ] Calcular naming dominante por rol, no global
- [ ] Agregar `naming_by_role` a CodeAnalysis en models.py
- [ ] Actualizar naming.md.j2 para mostrar tabla por rol
- [ ] Tests con proyecto que tiene naming mixto por rol

**Criterio de salida:** En un proyecto real, componentes = PascalCase (95%+), hooks = camelCase (95%+).

---

### Tarea 2: Violaciones Agrupadas con Prioridad

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `cli/commands/audit.py`, `store/findings.py`
- **No tocar:** scanners/, generators/, engine.py, selector/

**Problema:** 109 violaciones en un proyecto real, todas "layer-boundary ERROR". No agrupa por modulo ni indica por donde empezar.

**Entregables:**
- [ ] Agrupar violaciones por directorio
- [ ] Ordenar por frecuencia (modulo con mas violaciones = prioridad alta)
- [ ] Mostrar resumen agrupado en `loom audit`
- [ ] Agregar `--summary` flag para vista compacta
- [ ] Persistir agrupacion en `.loom/inconsistencies.json`
- [ ] Tests con violaciones en multiples modulos

**Criterio de salida:** `loom audit` muestra "core/ — 107 violations | domain/ — 2 violations".

---

### Tarea 3: Metricas por Capa

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `metrics.py` NUEVO, `cli/commands/metrics.py` NUEVO, `cli/__init__.py`
- **No tocar:** scanners/, generators/, auditors/, store/, selector/

**Problema:** Loom detecta Clean Architecture pero no mide si esta balanceada. No hay numeros.

**Entregables:**
- [ ] Crear `src/loom_context/metrics.py` con metricas por capa
- [ ] Metricas: archivos por capa, balance ratio, capa mas grande/chica
- [ ] Comando `loom metrics` con tabla Rich
- [ ] Persistir en `.loom/reports/metrics.json`
- [ ] Tests con capas desbalanceadas

**Criterio de salida:** `loom metrics` muestra tabla con archivos/capa y score de balance.

---

### Tarea 4: Soporte Monorepo

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `scanners/structure.py`, `models.py`
- **No tocar:** generators/, auditors/, cli/, store/, selector/

**Problema:** Un monorepo project se detecta como "flat". Loom no lee `workspaces` de package.json ni entra a `packages/`.

**Entregables:**
- [ ] Detectar monorepo: `workspaces` en package.json, `packages/`, `apps/`
- [ ] Agregar `is_monorepo` y `workspaces` a StructureFacts
- [ ] Escanear cada workspace como sub-proyecto
- [ ] Tests con monorepo de 2+ packages

**Criterio de salida:** Un monorepo project se detecta como monorepo con N workspaces listados.

---

### Tarea 5: Observabilidad (.loom/reports/)

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `store/reporter.py` NUEVO, `cli/commands/report.py` NUEVO, `cli/__init__.py`
- **No tocar:** scanners/, generators/, auditors/, selector/

**Problema:** No hay registro de como se usa Loom. Sin datos de uso, no se puede decidir que mejorar.

**Entregables:**
- [ ] Crear `.loom/reports/usage.jsonl` con registro por comando
- [ ] Registrar: comando, duracion, resultado, timestamp, SHA
- [ ] Comando `loom report` para ver analytics de uso
- [ ] Tests de registro y lectura

**Criterio de salida:** `loom report` muestra "init: 5 runs, avg 0.8s | audit: 3 runs".

---

### Tarea 6: Python Logging

- **Status:** `- [x]` completada
- **Agente:** cualquiera (no depende de otras tareas)
- **Archivos:** `engine.py`, `git.py`, `cli/__init__.py`
- **No tocar:** generators/, auditors/, store/, selector/, scanners/

**Problema:** Cuando Loom no detecta algo, no hay forma de saber por que. Debugging es ciego.

**Entregables:**
- [ ] Agregar `logging.getLogger("loom")` a engine y git
- [ ] Flag global `--verbose` para activar DEBUG
- [ ] Logging a stderr (no romper output Rich en stdout)
- [ ] Tests de logging

**Criterio de salida:** `loom init . --verbose` muestra log de cada scanner. Sin flag, output identico.

---

## Mapa de Independencia

```
Tarea    Archivos exclusivos                  Conflicto
─────    ─────────────────────────────────    ─────────
  1      scanners/code.py, naming.md.j2       Ninguno
  2      auditors/, audit.py, findings.py     Ninguno
  3      metrics.py NUEVO, metrics cmd        Ninguno
  4      scanners/structure.py                Ninguno
  5      store/reporter.py NUEVO, report cmd  Ninguno
  6      engine.py, git.py                    Ninguno
```

Solo `cli/__init__.py` se toca en tareas 3, 5 y 6 (para registrar comandos nuevos). Ese merge es trivial — una linea de import + una de add_command.

---

## Criterios de Salida (version completa)

- [x] Tarea 1: naming por rol completada
- [x] Tarea 2: audit agrupado completada
- [x] Tarea 3: metricas por capa completada
- [x] Tarea 4: monorepo support completada
- [x] Tarea 5: observabilidad completada
- [x] Tarea 6: logging completada
- [x] 269 tests pasan (95% cobertura mantenida)
- [x] Probado en a real-world project + a monorepo project + Loom-Context
- [x] Lint + format limpios

---

## Dependencias nuevas

Ninguna.
