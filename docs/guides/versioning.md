---
type: guide
audience: contributor
---

# Versiones y ramas

## TL;DR

Loom usa SemVer para releases y Git branches para separar trabajo activo de lineas congeladas. `develop` conserva la version actual de trabajo. Las ramas de release documentan el delta frente a la version anterior.

---

## Estado actual

### Version del paquete

- `pyproject.toml` mantiene la version actual de trabajo
- hoy esa version es `0.2.0`

### Ramas visibles

| Rama | Rol |
|------|-----|
| `develop` | linea activa de desarrollo |
| `main` | integracion estable visible del proyecto |
| `release/0.2.0` | corte de release para la version `0.2.0` |

---

## Regla operativa

### develop

`develop` conserva la version actual del paquete mientras no se corte una nueva release.

Eso significa:

- no se fuerza a reflejar cada delivery historico en el numero de version
- puede contener trabajo acumulado de varias entregas internas
- el numero de version solo cambia cuando se decide una release real

### main

`main` representa la linea estable que integra trabajo ya consolidado.

### release/x.y.z

Cada rama `release/x.y.z` debe responder una pregunta simple:

> Que cambia en esta version respecto de la anterior

Por eso, cada release debe tener:

- version congelada
- changelog resumido
- delta claro frente a la version anterior

---

## Delta por version

### `0.1.0`

Primera release funcional:

- `init`, `scan`, `prompt`, `audit`, `plan`, `watch`
- scanners, generators, auditors y seguridad base

### `0.2.0`

Delta frente a `0.1.0`:

- `.loom/` como estado operativo
- `enrich`, `decide`, `bundle`, `handoff`, `doctor`, `export`
- contratos tipados
- CLI modular
- bundles y handoff deterministas
- export a agentes

La rama asociada hoy es:

- `release/0.2.0`

---

## Politica recomendada hacia adelante

Para evitar confusion entre deliveries internos y releases reales:

- `docs/plans/` puede describir entregas internas por version o fase
- `CHANGELOG.md` debe reflejar solo releases reales del paquete
- `develop` mantiene la version actual de trabajo
- una rama `release/x.y.z` se crea solo cuando el numero en `pyproject.toml` va a publicarse

---

## Que no hacer

- no asumir que cada delivery interno obliga a bump de version
- no usar `main` y `develop` como si fueran changelog
- no mezclar roadmap historico con version real publicada

---

## Posicion actual recomendada

Con el estado actual del repo:

- dejar `develop` con la version actual del paquete
- usar `release/0.2.0` como referencia del salto respecto a `0.1.0`
- tratar futuros saltos como releases reales solo cuando se alineen codigo, changelog y packaging
