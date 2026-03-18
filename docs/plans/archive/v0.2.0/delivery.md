---
type: delivery
version: "0.2.0"
status: archived
prerequisite: "0.1.0"
scope: engine, cli, scanner, generator, auditor, infra
languages: [python]
patterns: [template-method, value-object, facade, strategy, adapter, registry, builder, append-only-log]
progress: 35/35
---

# v0.2.0 — Release Unificado

> Incluye las fases internas v0.2.0, v0.2.1, v0.2.2 y v0.4.0.
> v0.3.0 (embeddings) postergado por falta de evidencia.

## TL;DR

De 6 comandos y 25 tests a 15 comandos y 257 tests. Agrega .loom/ live state, contratos tipados, CLI modular, bundles por tarea (93% menos tokens), export a 4 agentes, compact format, y Loomy mascot. Todo determinista, 0 dependencias nuevas, 95% cobertura.

---

## Entregables completados

### Fase 1: Contexto vivo (.loom/)

- [x] `.loom/` como directorio de estado operativo
- [x] `FindingsStore` → `.loom/inconsistencies.json`
- [x] `DecisionLog` → `.loom/decisions.jsonl`
- [x] `MutationLog` → `.loom/mutations.jsonl`
- [x] `SessionLogger` migrado de `.context/` a `.loom/`
- [x] `GitHelper` compartido (Facade pattern)
- [x] Audit integrado en `loom init` (no bloqueante)

### Fase 2: Contratos tipados y CLI modular

- [x] `models.py` con 7 frozen dataclasses (ScanResult, StructureFacts, etc.)
- [x] `Violation.severity` → `Literal["error", "warning", "info"]`
- [x] CLI modularizado: 15 archivos en `cli/commands/`
- [x] `store/` package para persistencia .loom/
- [x] Pipeline architecture detection
- [x] Frontmatter YAML parsing en docs scanner

### Fase 3: Bundles, handoff y doctor

- [x] `loom bundle` con seleccion heuristica (93% menor que prompt)
- [x] `loom handoff` para continuidad entre sesiones
- [x] `loom doctor` con 11 checks de salud
- [x] `--compact` format (71-89% menos tokens)
- [x] `--top-k` y `--token-budget` en bundle
- [x] Manifest trazable con git SHA y strategy

### Fase 4: Export a agentes

- [x] `loom export --agent claude|cursor|codex|generic`
- [x] `--install` flag para escribir donde el agente lo espera
- [x] Exports a `.context/exports/` por defecto
- [x] Adapter + Registry pattern

### Fase 5: DX y documentacion

- [x] Loomy mascot con 8 expresiones emocionales
- [x] README reescrito con metricas reales
- [x] 8 guias reescritas con emojis, analogias, referencias cientificas
- [x] Quality guide con 7 capas de calidad documentadas
- [x] Makefile para qa, coverage, smoke, build

### Postergado (v0.3.0 — embeddings)

No implementado. Razon: heuristicas producen 93% de reduccion sin IA.

---

## Metricas

| Metrica | v0.1.0 | v0.2.0 |
|---------|--------|--------|
| Comandos | 6 | 15 |
| Tests | 25 | 257 |
| Cobertura | ~60% | 95% |
| Archivos Python | ~20 | 58 |
| Deps runtime | 4 | 4 |
| Scan 674 archivos | — | 0.8s |

## Probado en

- Loom-Context (pipeline, 62 archivos, audit clean)
- A 674-file React Native project (react-native-expo, 675 archivos, 109 violations, 0.8s)
