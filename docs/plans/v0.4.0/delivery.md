---
type: delivery
version: "0.4.0"
status: planned
prerequisite: "0.3.0"
scope: cli, generator, infra
languages: [python]
patterns: [decorator, cache, adapter]
progress: 0/6
---

# v0.4.0 — Adopcion: Ahorro Medible y Cero Friccion

## TL;DR

Loom demuestra su valor con numeros. Cada comando muestra tokens ahorrados, tiempo reducido, y contexto comprimido. Integracion sin friccion con agentes. Demo en 60 segundos. Si no puedes medir el ahorro, no puedes vender la herramienta.

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Tareas](#tareas)
- [Mapa de independencia](#mapa-de-independencia)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

Loom funciona, pero no demuestra cuanto ahorra. Un dev que lo prueba no sabe si ahorro 50% o 90% de tokens. Sin numeros, no hay adopcion. Sin adopcion, no hay comunidad. Sin comunidad, el proyecto muere.

## Analogia

Hoy Loom es como un filtro de agua que funciona pero no tiene medidor. Sabes que el agua sale limpia, pero no sabes cuantos litros de basura filtro. v0.4.0 agrega el medidor: "filtre 93% de ruido, te ahorre 32,000 tokens, te evite releer 668 archivos".

---

## Tareas

### Tarea 1: Metricas de Ahorro en CLI

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** `cli/commands/bundle.py`, `cli/commands/prompt.py`, `cli/commands/init.py`
- **No tocar:** scanners/, generators/, store/

**Problema:** Bundle dice "2.6KB" pero no dice "vs 35KB sin bundle, ahorraste 93%". Prompt compact no muestra comparacion.

**Entregables:**
- [ ] Mostrar tokens estimados (chars/4) en bundle, prompt, compact
- [ ] Mostrar porcentaje de ahorro vs prompt completo
- [ ] `loom stats .` — resumen de ahorro acumulado
- [ ] Formato: "~(^ ^)~ 2.6KB bundle (93% saved, ~650 tokens vs ~8,700)"
- [ ] Tests

**Criterio de salida:** Cada bundle/prompt muestra ahorro real en CLI output.

---

### Tarea 2: Output Incremental (Cache)

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** `engine.py`, nuevo `store/cache.py`
- **No tocar:** scanners/, cli/, generators/

**Problema:** `loom scan` re-escanea todo aunque nada cambio. En proyectos grandes, es desperdicio.

**Entregables:**
- [ ] Hash de archivos en `.loom/cache/hashes.json`
- [ ] Skip scanner si archivos no cambiaron desde ultimo scan
- [ ] Mostrar "skipped (no changes)" vs "updated"
- [ ] `--force` flag para forzar re-scan completo
- [ ] Tests

**Criterio de salida:** Segundo `loom scan` en proyecto sin cambios termina en <0.1s.

---

### Tarea 3: Presupuesto de Tokens por Comando

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** `selector/compact.py`, `selector/bundle.py`
- **No tocar:** scanners/, store/, engine.py

**Problema:** `--token-budget` usa ~4 chars/token como estimacion. Necesita ser mas preciso y mostrar cuanto del budget uso.

**Entregables:**
- [ ] Estimacion de tokens mas precisa (basada en whitespace + words)
- [ ] Mostrar "budget: 2,000/4,000 tokens used (50%)"
- [ ] Warning si output excede budget
- [ ] Tests

**Criterio de salida:** Token estimation dentro de 20% del real para modelos comunes.

---

### Tarea 4: Integracion Zero-Friction

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** `exporters/`, `cli/commands/export.py`
- **No tocar:** scanners/, engine.py, store/

**Problema:** `loom export --install` funciona pero el usuario tiene que saber que flag usar para cada agente. Deberia auto-detectar.

**Entregables:**
- [ ] `loom setup .` — auto-detecta agentes y configura todo
- [ ] Detecta .cursorrules, CLAUDE.md, AGENTS.md existentes
- [ ] Pregunta antes de sobreescribir (o usa --force)
- [ ] Genera .gitignore entries automaticamente
- [ ] Tests

**Criterio de salida:** `loom setup .` configura Claude + Codex + Cursor en un solo comando.

---

### Tarea 5: Compresion Estructural Avanzada

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** `selector/compact.py`
- **No tocar:** scanners/, store/, engine.py

**Problema:** Compact format reduce 71-89% pero puede ir mas lejos. Hay redundancia entre rules, architecture y naming que se puede eliminar.

**Entregables:**
- [ ] Deduplicar reglas que aparecen en multiples secciones
- [ ] Comprimir boundaries a formato ultra-corto (d!->i,p)
- [ ] Eliminar secciones vacias automaticamente
- [ ] Formato `--ultra-compact` para contextos de <1KB
- [ ] Tests

**Criterio de salida:** Ultra-compact produce contexto util en <1KB para proyectos medianos.

---

### Tarea 6: Demo y Documentacion de Adopcion

- **Status:** `- [ ]` pendiente
- **Agente:** cualquiera
- **Archivos:** docs/, README.md
- **No tocar:** src/

**Problema:** No hay demo rapida, no hay caso de uso concreto documentado, no hay comparacion antes/despues visible.

**Entregables:**
- [ ] Demo script de 60 segundos (loom init → bundle → export)
- [ ] Pagina "Why Loom" con metricas reales
- [ ] Casos de uso concretos: "antes de refactor", "handoff entre agentes", "code review"
- [ ] Tabla comparativa: sin Loom vs con Loom (tokens, tiempo, precision)
- [ ] Repo de ejemplo minimo

**Criterio de salida:** Un dev nuevo puede entender y probar Loom en <5 minutos leyendo el README.

---

## Mapa de Independencia

```
Tarea    Archivos exclusivos              Conflicto
─────    ──────────────────────────────   ─────────
  1      cli/commands/ (output format)    Ninguno
  2      engine.py, store/cache.py NEW    Ninguno
  3      selector/compact.py, bundle.py   Ninguno
  4      exporters/, export.py            Ninguno
  5      selector/compact.py              Tarea 3 (merge trivial)
  6      docs/, README.md                 Ninguno
```

---

## Criterios de Salida (version completa)

- [ ] Tarea 1: ahorro medible en CLI
- [ ] Tarea 2: cache incremental
- [ ] Tarea 3: presupuesto de tokens preciso
- [ ] Tarea 4: setup zero-friction
- [ ] Tarea 5: compresion ultra-compact
- [ ] Tarea 6: demo y docs de adopcion
- [ ] Tests nuevos (meta: mantener 95%+ cobertura)
- [ ] Probado en 2+ proyectos reales
- [ ] Un dev nuevo puede probar Loom en <5 minutos

---

## Dependencias nuevas

Ninguna.

---

## Mejoras pendientes de feedback real

Observaciones de uso en proyectos reales que alimentan esta version:

### Monorepo: scan por workspace

Hoy el monorepo se detecta (`is_monorepo=True`, lista workspaces) pero la arquitectura
dice "flat" porque analiza la raiz, no cada workspace. Cada workspace puede tener su
propia arquitectura (clean, hexagonal, etc.).

**Mejora:** escanear cada workspace como sub-proyecto con su propio tipo y arquitectura.

### Deep audit gaps

Un audit manual en un proyecto real encontro 20 problemas que Loom no detecta:
- Race conditions en hooks
- Memory leaks por subscripciones no canceladas
- Keys basadas en indice en listas dinamicas
- Async sin cancelacion
- Accesibilidad

**Mejora:** ampliar auditors mas alla de naming + boundaries. Posible en v0.5.0.

### .loom/reports/ como input de planes

Los reportes de `.loom/reports/` (metrics.json, delta, deep-audit) ya se generan
pero `loom plan --generate` todavia no los consume todos. El plan generado deberia
incluir findings de deep audits y deltas acumulados.

---

## Metricas de exito

| Metrica | Target |
|---------|--------|
| Tiempo de demo | <60 segundos |
| Tiempo de setup | <5 minutos |
| Ahorro de tokens por bundle | >90% vs prompt completo |
| Segundo scan (cache hit) | <0.1s |
| Ultra-compact size | <1KB para proyectos medianos |
| README → primer bundle | <3 comandos |
