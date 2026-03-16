---
type: delivery
version: "0.2.1"
status: planned
prerequisite: "0.2.0"
scope: engine, scanner, cli
languages: [python]
---

# v0.2.1 — Contratos Tipados y CLI Modular

> Estado: PLANIFICADO
> Prerequisito: v0.2.0 publicado
> Referencia: [architecture-hardening-plan.md](../architecture-hardening-plan.md) Fases A y B

## Problema que resuelve

Todo el pipeline pasa `dict[str, Any]` entre capas. Esto significa:

- errores de tipado solo se descubren en runtime
- cada nuevo modulo inventa sus propias llaves
- mypy no puede validar nada entre scanner y generator
- cli.py tiene 550+ lineas y crece con cada comando

Sin contratos tipados, los bundles (v0.2.2) heredarian la misma fragilidad.

## Que cambia

### Contratos tipados

Dataclasses que reemplazan dicts anonimos:

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
class DependencyInfo:
    package_manager: str
    dependencies: list[Dependency]
    stack_summary: dict[str, list[str]]

@dataclass(frozen=True)
class CodeAnalysis:
    file_naming: dict[str, Any]
    code_naming: dict[str, Any]
    suffix_patterns: list[dict[str, Any]]
    prefix_patterns: list[dict[str, Any]]
    import_aliases: dict[str, str]
    total_code_files: int

@dataclass(frozen=True)
class DocsInventory:
    docs: list[DocEntry]
    doc_count: int
    agents_md: Optional[str]
    by_type: dict[str, int]

@dataclass(frozen=True)
class ScanResult:
    structure: StructureFacts
    deps: DependencyInfo
    code: CodeAnalysis
    docs: DocsInventory
    scanned_at: str
```

### Transicion gradual

- scanners devuelven dataclasses
- `ScanResult.to_dict()` para compatibilidad con generators
- generators pueden migrar gradualmente a recibir objetos tipados
- tests existentes no deben romperse

### CLI modular

```text
src/loom_context/
  cli/
    __init__.py          # main group + version (~30 lines)
    commands/
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

Cada comando:
- parsea input
- invoca engine o servicio
- renderiza salida con Rich
- no contiene logica de negocio

## Entregables

- [ ] `domain/models/scan.py` con todos los dataclasses
- [ ] scanners actualizados para devolver objetos tipados
- [ ] `ScanResult.to_dict()` para compatibilidad
- [ ] CLI modularizado: un archivo por comando
- [ ] `mypy --strict` pasa en domain/models/
- [ ] cli.py principal < 50 lineas

## Tests

- [ ] tests existentes siguen pasando sin cambios
- [ ] tests de contrato para serializacion (ScanResult → dict → JSON)
- [ ] mypy pasa sin errores en domain/

## Dependencias nuevas

Ninguna.

## Riesgos

- romper compatibilidad de salida en `.context/`
- migracion parcial que deja dicts y dataclasses mezclados

## Mitigacion

- `to_dict()` mantiene formato de salida identico
- migrar scanner por scanner, test por test
- verificar que `.context/` output no cambia bit a bit
