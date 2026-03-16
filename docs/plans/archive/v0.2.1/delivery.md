---
type: delivery
version: "0.2.1"
status: archived
prerequisite: "0.2.0"
scope: engine, scanner, cli
languages: [python]
patterns: [value-object, facade, composition]
progress: 9/9
---

# v0.2.1 — Contratos Tipados y CLI Modular

## TL;DR

Reemplaza `dict[str, Any]` por dataclasses tipados en todo el pipeline. Separa cli.py (550+ lineas) en un archivo por comando. Esto prepara la base estable para bundles (v0.2.2) y elimina errores de tipado que hoy solo se descubren en runtime.

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Que cambia](#que-cambia)
- [Patrones de diseno](#patrones-de-diseno)
- [Estructura de archivos](#estructura-de-archivos)
- [Entregables](#entregables)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

Hoy todo el pipeline pasa `dict[str, Any]` entre capas. Eso significa:

- errores de tipado solo se descubren en runtime
- cada modulo nuevo inventa sus propias llaves string
- mypy no puede validar nada entre scanner y generator
- cli.py crece sin limite y mezcla rendering con logica

Sin contratos tipados, los bundles (v0.2.2) heredarian la misma fragilidad.

## Analogia

**Hoy:** los scanners entregan cajas sin etiqueta. El generator abre cada caja, mete la mano y espera encontrar lo que necesita. Si alguien cambio el contenido, solo se entera cuando algo falla.

**Despues:** cada scanner entrega un formulario con campos definidos. El generator sabe exactamente que esperar, y si falta algo, el error se detecta antes de ejecutar.

- `dict[str, Any]` = caja sin etiqueta
- `dataclass(frozen=True)` = formulario con campos obligatorios

---

## Que cambia

### Contratos tipados

```python
@dataclass(frozen=True)
class StructureFacts:
    project_type: str
    architecture: list[str]
    src_root: str
    directory_tree: dict[str, Any]
    layer_boundaries: dict[str, Any]
    total_files: int
    project_name: str = ""

@dataclass(frozen=True)
class ScanResult:
    structure: StructureFacts
    deps: DependencyInfo
    code: CodeAnalysis
    docs: DocsInventory
    scanned_at: str
```

### Transicion gradual

- Scanners devuelven dataclasses en vez de dicts
- `ScanResult.to_dict()` mantiene compatibilidad con generators
- Generators migran gradualmente a recibir objetos tipados
- Tests existentes no se rompen

### CLI modular

```
cli/
  __init__.py            # main group (~30 lineas)
  commands/
    init.py              # cada comando < 80 lineas
    scan.py
    prompt.py
    audit.py
    ...
```

---

## Patrones de diseno

| Patron | Donde | Por que |
|--------|-------|---------|
| **Value Object** | `StructureFacts`, `DependencyInfo`, etc. (`frozen=True`) | Inmutables, sin identidad, comparables por valor |
| **Facade** | `ScanResult.to_dict()` | Un punto de acceso para serializar todo el resultado |
| **Composition** | CLI group + commands | Cada comando es un modulo independiente, compuesto en el group |
| **Adapter** | mappers `dict → dataclass` en cada scanner | Transicion gradual sin romper generators |

---

## Estructura de archivos

### Nuevos

```
src/loom_context/
  domain/
    models/
      __init__.py
      scan.py             # ScanResult, StructureFacts, DependencyInfo, etc.
  cli/
    __init__.py           # main group + version
    commands/
      __init__.py
      init.py
      scan.py
      prompt.py
      audit.py
      plan.py
      watch.py
      focus.py
      log.py
      status.py
      enrich.py
      decide.py
```

### Modificados

```
src/loom_context/
  scanners/structure.py   # devuelve StructureFacts
  scanners/deps.py        # devuelve DependencyInfo
  scanners/code.py        # devuelve CodeAnalysis
  scanners/docs.py        # devuelve DocsInventory
  engine.py               # usa ScanResult
```

### Eliminados

```
src/loom_context/
  cli.py                  # reemplazado por cli/__init__.py + commands/
```

---

## Entregables

- [x] `models.py` con todos los dataclasses (ScanResult, StructureFacts, etc.)
- [x] scanners actualizados para devolver objetos tipados (via engine wrapping)
- [x] `ScanResult.to_dict()` para compatibilidad
- [x] CLI modularizado: 12 archivos en `cli/commands/`
- [x] `Violation.severity` migrado a `Literal["error", "warning", "info"]`
- [x] cli/__init__.py < 50 lineas (45)
- [x] cada comando < 90 lineas
- [x] 87 tests existentes pasan sin cambios
- [x] 4 tests de contrato + 2 tests pipeline detection

## Criterios de salida

- Scanners devuelven dataclasses, no dicts
- `mypy --strict` pasa en domain/
- cli.py eliminado, reemplazado por cli/
- `.context/` output identico al de v0.2.0 (no breaking changes)
- 0 regresiones en tests

## Dependencias nuevas

Ninguna.

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Romper formato de `.context/` | `to_dict()` mantiene output identico; comparar bit a bit |
| Mezcla de dicts y dataclasses | Migrar scanner por scanner, test por test |
| CLI commands con imports circulares | Lazy imports en cada comando (patron ya usado) |
