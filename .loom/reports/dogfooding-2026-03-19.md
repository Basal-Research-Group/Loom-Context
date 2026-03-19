# Loom-Context Dogfooding Report — 2026-03-19

## Context

Applied Loom v0.3.1 across 3 real projects to validate developer experience
and collect improvement feedback for v0.4.0 release.

| Project | Type | Files | Architecture | Loom Version |
|---------|------|-------|-------------|-------------|
| **Loom-Context** (self) | Python CLI | 72 | pipeline | v0.3.1 |
| **Akana** | React Native (Expo) | 683 | clean-arch, hexagonal, feature-based | v0.3.1 |
| **core_monorepo_enn** | Node.js monorepo | 1419 | layered monorepo (NestJS) | v0.3.1 |

---

## Hallazgos por Proyecto

### Loom-Context (self)

| Command | Result | Notes |
|---------|--------|-------|
| `loom init .` | OK (0.1s) | 68 files, pipeline arch, clean audit |
| `loom doctor .` | OK | 10/10 checks passed |
| `loom export --install` | **BUG** | Overwrote hand-crafted CLAUDE.md without warning |
| `loom metrics .` | WARN | "No layers detected" — Python layers not recognized |
| `loom bundle .` | WARN | "No relevant context" — error message unclear |

### Akana (React Native, 683 files)

| Command | Result | Notes |
|---------|--------|-------|
| `loom init .` | OK | clean-arch detected, 4 layers, 109 violations |
| `loom enrich .` | OK | Delta tracking works, mutations logged |
| `loom audit .` | OK | Violations detected but no clustering/ownership |
| `loom plan --generate` | OK | Generated plan but doesn't consume deep-audit or delta reports |
| `loom export --install` | **BUG** | Same overwrite problem |
| `loom metrics .` | OK | Balance score 0.73, layers detected for TS projects |

**Key feedback from Akana reports:**
- Violations need `cluster`, `owner`, and `status` fields
- Need violation classification: `intentional-mix` vs `accidental-mix` vs `temporary-mix`
- `plans-summary.md` mixes closed items with active backlog
- No multi-agent loop tracking (Loom → Codex → Claude → Loom)
- Deep audit found 20 problems Loom doesn't detect (race conditions, memory leaks, accessibility)
- Decisions too macro — need granularity per refactor block

### core_monorepo_enn (Node.js monorepo, 1419 files)

| Command | Result | Notes |
|---------|--------|-------|
| `loom init .` | OK | Detects "flat" — wrong, it's layered monorepo |
| `loom scan .` | OK | 7 files updated |
| `loom enrich .` | OK | 0 errors, 0 warnings (too permissive?) |
| `loom bundle` (x9) | OK | Specific task bundles work well |
| `loom metrics .` | **FAIL** | "No layers detected" — loom.json layers not read |
| `loom report .` | **FAIL** | "No usage data" — needs accumulated history |
| `loom export --format` | **FAIL** | Wrong flag; correct is `-a claude` |

**Key feedback from monorepo reports:**
- Architecture detected as "flat" — should be "layered-monorepo"
- `loom.json` layers are defined but `metrics` and `audit` don't read them
- Bundle relevance scoring doesn't use configured layer boundaries
- `loom export -o` requires absolute paths — relative paths fail with ValueError
- Need README template in `.loom/reports/` for report organization
- Useful session: 33+ loom commands in one session, all productive

---

## Hallazgos Consolidados — Mejoras para v0.4.0

### P0 — Críticos (ya implementados en esta sesión)

| # | Mejora | Estado |
|---|--------|--------|
| 1 | `loom export --install` backup automático antes de sobreescribir | **DONE** |
| 2 | `--force` y `--no-backup` flags en export | **DONE** |
| 3 | `loom setup` wizard con detección de agentes + presets | **DONE** |
| 4 | BackupStore en `.loom/backups/` | **DONE** |
| 5 | Confirmación interactiva al sobreescribir archivos existentes | **DONE** |

### P1 — Altos (v0.4.0 scope)

| # | Mejora | Fuente | Archivos |
|---|--------|--------|----------|
| 6 | `loom metrics` debe leer layers de `loom.json` | monorepo, self | `metrics.py`, `engine.py` |
| 7 | Arquitectura "layered-monorepo" — detectar workspaces como sub-proyectos | monorepo | `scanners/structure.py` |
| 8 | Naming scanner: single-word filenames no son "camelCase" | self | `scanners/code.py` |
| 9 | `loom bundle` mejor error message cuando falta task description | self, monorepo | `cli/commands/bundle.py` |
| 10 | `loom export -o` debe aceptar paths relativos | monorepo | `cli/commands/export.py` |
| 11 | Violation classification: `intentional`/`accidental`/`temporary` | akana | `models.py`, `auditors/` |
| 12 | `plans-summary.md` separar planes activos vs cerrados | akana, monorepo | `generators/plans.py` |

### P2 — Medios (v0.4.0 o v0.5.0)

| # | Mejora | Fuente | Detalle |
|---|--------|--------|---------|
| 13 | Violations con campos `cluster` y `owner` | akana | Agrupar por ownership, no solo por regla |
| 14 | `loom plan --generate` consumir deep-audit y delta reports | akana | Plan generado incluya hallazgos de `.loom/reports/` |
| 15 | Multi-agent loop tracking (Loom→Codex→Claude→Loom) | akana | Registrar ciclo de detección-fix-review-baseline |
| 16 | Decisions enriquecidas: `cluster`, `files`, `validation`, `expected_delta` | akana | `store/decisions.py` |
| 17 | `loom report` template en `.loom/reports/README.md` | monorepo | Auto-generar con estructura de reportes |
| 18 | `loom setup --dry-run` para preview sin instalar | self | `cli/commands/setup.py` |
| 19 | `loom restore` comando para recuperar desde backups | self | `cli/commands/restore.py` |
| 20 | Ahorro de tokens medible en bundle/prompt/export | delivery v0.4.0 | Tarea 1 del plan existente |
| 21 | Cache incremental (segundo scan en <0.1s) | delivery v0.4.0 | Tarea 2 del plan existente |

### P3 — Bajos (v0.5.0+)

| # | Mejora | Fuente |
|---|--------|--------|
| 22 | Deep audit: race conditions, memory leaks, accessibility | akana |
| 23 | Duplicate-capability detection (dos targets, dos adapters) | akana |
| 24 | Naming drift detection (archivo cuyo nombre no coincide con su rol) | akana |
| 25 | Warning classification: `architecture-warning` vs `test-infra-warning` | akana |
| 26 | `next-actions.md` auto-generado con top 10 inconsistencias | akana |

---

## Métricas de la Sesión (implementación loom setup)

| Métrica | Valor |
|---------|-------|
| Archivos nuevos | 7 (4 src + 3 tests) |
| Archivos modificados | 5 |
| Tests nuevos | 24 |
| Tests totales | 305 (antes: 281) |
| Comandos Loom | 19 (antes: 18) |
| Lint | clean (ruff) |

## Uso Real de Loom en 3 Proyectos

| Métrica | Loom-Context | Akana | Monorepo |
|---------|-------------|-------|----------|
| Comandos ejecutados | 6 | ~15 | 33+ |
| Violaciones detectadas | 0 | 109→48 | 0 |
| Decisiones registradas | 0 | 10 | 2 |
| Exports generados | 2 | 2 | 1 |
| Bundles generados | 1 | 0 | 9 |
| Delta reports | 2 | 3 | 2 |
| Reportes manuales | 1 | 5 | 4 |

### Conclusión

Loom funciona bien como **detector y snapshot**. Los 3 proyectos producen reportes útiles
que guían refactors. Las fricciones principales son:

1. **Sobreescritura destructiva** — resuelto con `loom setup` + backup
2. **Métricas rotas en monorepos/Python** — necesita leer `loom.json`
3. **Violaciones sin clasificación** — necesita `intentional`/`accidental`
4. **Plans-summary desalineado** — necesita separar activos vs cerrados

Los bundles task-specific (9 en monorepo) son el feature más productivo del día a día.
El loop multiagente existe en Akana pero no está modelado en Loom todavía.
