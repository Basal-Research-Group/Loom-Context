---
type: delivery
version: "0.3.0"
status: planned
prerequisite: "0.2.0"
scope: scanner, generator, cli, infra
languages: [python]
patterns: [strategy, decorator, observer]
---

# v0.3.0 — Analisis Profundo y Observabilidad

## TL;DR

Loom pasa de "detectar arquitectura" a "medir salud". Naming por rol (no global), violaciones agrupadas con prioridad, metricas cuantitativas por capa, soporte monorepo, y `.loom/reports/` para analytics de uso.

---

## Tareas Independientes por Agente

Cada tarea es autocontenida. Un agente puede tomar cualquiera sin depender de las demas. No se pisan entre si porque tocan archivos distintos.

### Tarea 1: Naming por Rol

> Agente: puede trabajar solo en `scanners/code.py`

**Problema:** Loom detecta naming global (50% PascalCase, 48% camelCase en Akana). Pero no es "mixto" — componentes usan PascalCase, hooks/utils usan camelCase. Son dominios distintos.

**Que hacer:**
- [ ] Agrupar archivos por rol (componente, hook, service, repository, etc.)
- [ ] Calcular naming dominante POR ROL, no global
- [ ] Agregar `naming_by_role` al output de CodeScanner
- [ ] Actualizar `naming.md` template para mostrar por rol
- [ ] Tests: proyecto con naming mixto por rol

**Archivos a tocar:**
- `src/loom_context/scanners/code.py` — logica de agrupacion
- `src/loom_context/models.py` — agregar campo `naming_by_role` a CodeAnalysis
- `src/loom_context/templates/naming.md.j2` — mostrar por rol
- `tests/test_cli.py` — tests nuevos

**NO tocar:** engine.py, cli/, generators/, auditors/, store/

**Criterio de salida:**
- En Akana: componentes = PascalCase, hooks = camelCase, services = PascalCase
- Confianza por rol > 80% (vs 50% global actual)

---

### Tarea 2: Violaciones Agrupadas con Prioridad

> Agente: puede trabajar solo en `auditors/` y `cli/commands/audit.py`

**Problema:** 109 violaciones en Akana, todas "layer-boundary ERROR". No dice por donde empezar ni agrupa por modulo.

**Que hacer:**
- [ ] Agrupar violaciones por modulo/directorio
- [ ] Agregar severidad por frecuencia (modulo con mas violaciones = prioridad)
- [ ] Mostrar resumen agrupado en `loom audit`
- [ ] Agregar `--summary` flag a audit para vista compacta
- [ ] Persistir violaciones agrupadas en `.loom/inconsistencies.json`
- [ ] Tests: proyecto con violaciones en multiples modulos

**Archivos a tocar:**
- `src/loom_context/cli/commands/audit.py` — renderizado agrupado
- `src/loom_context/store/findings.py` — agregar agrupacion
- `tests/test_cli.py` — tests nuevos

**NO tocar:** scanners/, generators/, engine.py, selector/

**Criterio de salida:**
- `loom audit .` muestra: "core/ — 107 violations, domain/ — 2 violations"
- `loom audit . --summary` muestra solo totales por modulo

---

### Tarea 3: Metricas por Capa

> Agente: puede trabajar solo en `status.py` y un nuevo `metrics.py`

**Problema:** Loom detecta que hay Clean Architecture pero no mide si esta balanceada. No hay metricas cuantitativas.

**Que hacer:**
- [ ] Crear `src/loom_context/metrics.py` con calculo de metricas
- [ ] Metricas: archivos por capa, lineas por capa, balance ratio
- [ ] Agregar `loom metrics` comando
- [ ] Output: tabla con metricas por capa + score de salud
- [ ] Persistir en `.loom/reports/metrics.json`
- [ ] Tests: proyecto con capas desbalanceadas

**Archivos a tocar:**
- `src/loom_context/metrics.py` — NUEVO
- `src/loom_context/cli/commands/metrics.py` — NUEVO
- `src/loom_context/cli/__init__.py` — registrar comando
- `tests/test_cli.py` — tests nuevos

**NO tocar:** scanners/, generators/, auditors/, store/, selector/

**Criterio de salida:**
- `loom metrics .` muestra tabla con archivos/lineas por capa
- En Akana: muestra que core/ tiene mas archivos que domain/

---

### Tarea 4: Soporte Monorepo

> Agente: puede trabajar solo en `scanners/structure.py`

**Problema:** `core_monorepo_enn` se detecta como "flat" porque Loom no entra a packages/workspaces. No lee `workspaces` de package.json ni `packages/` dirs.

**Que hacer:**
- [ ] Detectar monorepo por: `workspaces` en package.json, `packages/` dir, `apps/` dir
- [ ] Escanear cada workspace como sub-proyecto
- [ ] Agregar `is_monorepo` y `workspaces` a StructureFacts
- [ ] Mostrar info de workspaces en status y init
- [ ] Tests: proyecto monorepo con 2+ packages

**Archivos a tocar:**
- `src/loom_context/scanners/structure.py` — deteccion de workspaces
- `src/loom_context/models.py` — agregar campos a StructureFacts
- `tests/test_cli.py` — tests nuevos

**NO tocar:** generators/, auditors/, cli/, store/, selector/

**Criterio de salida:**
- `core_monorepo_enn` se detecta como monorepo con N workspaces
- Cada workspace tiene su propio project_type

---

### Tarea 5: Observabilidad (.loom/reports/)

> Agente: puede trabajar solo en `store/` y un nuevo `reporter.py`

**Problema:** No hay registro de como se usa Loom. No se sabe que comandos se corren, cuanto tardan, que sale. Sin esto no hay datos para decidir que mejorar.

**Que hacer:**
- [ ] Crear `.loom/reports/` para analytics de uso
- [ ] Registrar cada comando: nombre, duracion, resultado, timestamp
- [ ] `loom report` comando para ver analytics
- [ ] Metricas: comandos mas usados, tiempo promedio, errores frecuentes
- [ ] Tests: verificar que reports se crean y leen

**Archivos a tocar:**
- `src/loom_context/store/reporter.py` — NUEVO
- `src/loom_context/cli/commands/report.py` — NUEVO
- `src/loom_context/cli/__init__.py` — registrar comando
- `tests/test_cli.py` — tests nuevos

**NO tocar:** scanners/, generators/, auditors/, selector/

**Criterio de salida:**
- Cada `loom <cmd>` registra uso en `.loom/reports/usage.jsonl`
- `loom report` muestra: "init: 5 runs, avg 0.8s | audit: 3 runs, avg 0.2s"

---

### Tarea 6: Python Logging

> Agente: puede trabajar solo en `git.py`, `engine.py`

**Problema:** Cuando Loom no detecta algo, no hay forma de saber por que. Sin logging, debuggear es ciego.

**Que hacer:**
- [ ] Agregar `logging.getLogger("loom")` al engine y scanners
- [ ] Log level: DEBUG para detalles, INFO para resumen, WARNING para problemas
- [ ] `--verbose` flag global para activar DEBUG en CLI
- [ ] No romper output Rich (logging a stderr, Rich a stdout)
- [ ] Tests: verificar que logs se emiten correctamente

**Archivos a tocar:**
- `src/loom_context/engine.py` — agregar logger
- `src/loom_context/cli/__init__.py` — flag --verbose
- `src/loom_context/git.py` — log de errores git
- `tests/test_cli.py` — tests nuevos

**NO tocar:** generators/, auditors/, store/, selector/, scanners/ (solo engine)

**Criterio de salida:**
- `loom init . --verbose` muestra logs de cada scanner
- Sin --verbose, output identico al actual

---

## Mapa de Independencia

```
Tarea 1 (naming)     → scanners/code.py        ← INDEPENDIENTE
Tarea 2 (audit)      → auditors/ + audit.py     ← INDEPENDIENTE
Tarea 3 (metricas)   → metrics.py NUEVO         ← INDEPENDIENTE
Tarea 4 (monorepo)   → scanners/structure.py    ← INDEPENDIENTE
Tarea 5 (reports)    → store/reporter.py NUEVO  ← INDEPENDIENTE
Tarea 6 (logging)    → engine.py + git.py       ← INDEPENDIENTE
```

Ningun agente toca los mismos archivos que otro. Pueden ejecutarse en paralelo sin conflictos de merge.

---

## Orden sugerido (si se hacen secuenciales)

1. Tarea 2 (audit agrupado) — mayor impacto inmediato en Akana
2. Tarea 1 (naming por rol) — resuelve el 50% de confianza
3. Tarea 3 (metricas) — nuevo comando con valor propio
4. Tarea 4 (monorepo) — desbloquea core_monorepo_enn
5. Tarea 5 (reports) — observabilidad de uso
6. Tarea 6 (logging) — infraestructura para debugging
