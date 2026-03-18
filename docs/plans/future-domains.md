---
type: architecture
status: exploration
scope: scanner, engine
---

# Loom para Dominios mas alla del Codigo

## TL;DR

Loom esta disenado para codigo, pero su pipeline (scanners → engine → generators) es agnostico al tipo de artefacto. Extender Loom a otros dominios (investigacion, ciencia, datos) requiere scanners nuevos, no cambios al core. Este plan explora como y cuando hacerlo.

---

## Indice

- [Por que es posible](#por-que-es-posible)
- [Analogia](#analogia)
- [Dominio: Research](#dominio-research)
- [Otros dominios posibles](#otros-dominios-posibles)
- [Como se implementaria](#como-se-implementaria)
- [Que NO cambia](#que-no-cambia)

---

## Por que es posible

El pipeline de Loom no sabe que esta leyendo codigo. Sabe leer archivos, extraer metadata, y compilar contexto. Los scanners actuales buscan patrones especificos (imports, package.json, naming), pero el engine y los generators son agnosticos.

```
Scanner de codigo:   lee .ts → extrae imports, naming, architecture
Scanner de research: lee .bib, .csv, .md → extrae hipotesis, datasets, metodos
Scanner de datos:    lee schemas, pipelines → extrae transformaciones, linaje

El engine no cambia. Solo conecta scanners con generators.
```

## Analogia

Loom es como un microscopio. Hoy tiene un lente para codigo (scanners). Pero el cuerpo del microscopio (engine, generators, .context/) sirve para cualquier lente. Agregar un dominio nuevo = fabricar un lente nuevo, no un microscopio nuevo.

---

## Dominio: Research

El caso mas inmediato. Un proyecto de investigacion tiene estructura que Loom puede escanear:

```
mi-tesis/
  docs/
    hipotesis.md
    metodologia.md
    marco-teorico.md
    resultados.md
  data/
    raw/
    processed/
    analysis/
  notebooks/
    01-exploracion.ipynb
    02-modelo.ipynb
  references/
    bibliography.bib
    papers/
  experiments/
    config.yaml
    results.json
```

### Que escanearia un ResearchScanner

| Artefacto | Que extrae |
|-----------|-----------|
| `*.md` en docs/ | Hipotesis, preguntas de investigacion, secciones del marco teorico |
| `*.bib` | Referencias, autores, anos, journals |
| `*.ipynb` | Celdas de codigo, visualizaciones, conclusiones |
| `*.csv` / `*.json` en data/ | Schema de datasets, columnas, tipos, tamano |
| `config.yaml` | Parametros de experimentos, hiperparametros |
| `results.json` | Metricas, comparaciones, conclusiones |

### Que generaria en .context/

```
.context/
  index.json              ← metadata del proyecto de investigacion
  methodology.md          ← metodo detectado, variables, instrumentos
  literature-map.md       ← mapa de referencias por tema
  data-inventory.md       ← datasets, schemas, tamanos
  experiment-summary.md   ← resultados, metricas, conclusiones
  rules.json              ← convenciones del proyecto (formato de citas, naming de datos)
```

### Que le daria a un agente

Un agente con este contexto podria:
- Revisar consistencia entre hipotesis y resultados
- Sugerir referencias faltantes basandose en el tema
- Detectar gaps en la metodologia
- Resumir el estado de la tesis para un advisor
- Generar borradores de secciones con contexto correcto

### Auto-deteccion

```python
# En StructureScanner._detect_project_type():
if (root / "bibliography.bib").exists() or (root / "references").is_dir():
    return "research"
if any((root / "notebooks").glob("*.ipynb")):
    return "research-notebook"
if (root / "experiments").is_dir():
    return "experiment"
```

### CLI

```bash
loom init .                        # auto-detecta "research"
loom init . --domain research      # forzar dominio
loom bundle "marco teorico" .      # contexto para esa seccion
loom focus "metodologia" .         # filtrar por tema
loom plan . --generate             # plan de la investigacion
```

---

## Otros dominios posibles

### Ciencia de datos

```
Scanner: DataScanner
Lee: .csv, .parquet, schemas, pipelines, dbt models
Extrae: linaje de datos, transformaciones, calidad, schemas
Util para: equipos de data que usan agentes para analisis
```

### Genomica

```
Scanner: GenomicsScanner
Lee: .fasta, .vcf, config de pipelines bioinformaticos
Extrae: secuencias, variantes, parametros de analisis
Util para: validar que el analisis sigue protocolos
```

### Documentacion tecnica

```
Scanner: DocsProjectScanner
Lee: estructuras de docs (Docusaurus, MkDocs, Sphinx)
Extrae: mapa de navegacion, secciones, cross-references
Util para: mantener consistencia en docs grandes
```

---

## Como se implementaria

### Patron: Scanner por dominio

```python
# Cada dominio tiene su scanner
class ResearchScanner(BaseScanner):
    def scan(self) -> dict[str, Any]:
        bibliography = self._scan_bib()
        methodology = self._scan_methodology()
        datasets = self._scan_data()
        experiments = self._scan_experiments()
        return {
            "bibliography": bibliography,
            "methodology": methodology,
            "datasets": datasets,
            "experiments": experiments,
        }
```

### Patron: Template por dominio

```
templates/
  architecture.md.j2          ← codigo (ya existe)
  naming.md.j2                ← codigo (ya existe)
  methodology.md.j2           ← research (nuevo)
  literature-map.md.j2        ← research (nuevo)
  data-inventory.md.j2        ← data science (nuevo)
```

### Patron: Auto-deteccion + flag

```python
# Auto-deteccion en StructureScanner
def _detect_domain(self) -> str:
    if self._has_bib_files():
        return "research"
    if self._has_data_pipelines():
        return "data"
    return "code"  # default

# Override via CLI
# loom init . --domain research
```

---

## Que NO cambia

- `engine.py` — sigue orquestando scanners → generators
- `.context/` — sigue siendo el output canonico
- `.loom/` — sigue siendo estado operativo
- `models.py` — se extiende con nuevos dataclasses, no se modifica
- `selector/` — bundle y handoff funcionan con cualquier .context/
- `exporters/` — export a agentes funciona igual
- `cli/` — mismos comandos, nuevo flag `--domain`

El core es agnostico al dominio. Los scanners son especificos.

---

## Estado

Exploracion. No hay fecha ni version asignada. Se implementara cuando:

- El dominio de research se valide con un proyecto real (tesis doctoral)
- Se confirme que el patron scanner-por-dominio funciona sin modificar el core
- Se defina el set minimo de artefactos que un ResearchScanner debe leer
