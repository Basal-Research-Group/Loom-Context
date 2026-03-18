# Plan de Release 0.1.1

> Recomendacion: liberar `0.1.1` como primera version de adopcion temprana para validacion en proyectos reales.

## Decision

La recomendacion es liberar `0.1.1`, no `0.2.0-beta.1`.

### Por que `0.1.1`

- comunica estabilidad incremental sin sobreprometer
- permite probar Loom ya en un proyecto real
- encaja con el estado actual del producto: util, pero todavia no ampliado con bundles, retrieval ni workspace
- simplifica el mensaje para PyPI y GitHub Releases

### Por que no `0.2.0-beta.1`

- todavia no existe un salto funcional que justifique cambiar de fase publica
- puede introducir confusion sobre que parte ya esta implementada y que sigue siendo roadmap
- conviene primero obtener feedback real de `init`, `audit`, `prompt`, `plan` y `watch`

## Objetivo del Release

Poner Loom-Context en manos de 1 a 3 proyectos reales para validar:

- calidad de deteccion
- utilidad de auditoria
- utilidad del prompt generado
- friccion de instalacion
- problemas reales de DX y falso positivo

## Mensaje del Release

### Posicionamiento

`0.1.1` es la primera version lista para adopcion temprana en proyectos reales.

### Promesa

Loom-Context ya puede:

- escanear un repo real
- generar contexto util para agentes
- auditar reglas basicas de arquitectura y naming
- resumir documentacion y planes existentes

### Limites que deben decirse explicitamente

- no hay bundles por tarea todavia
- no hay retrieval local todavia
- `watch` sigue siendo simple
- la cobertura real debe validarse en repos mas variados

## Alcance del Release

### Incluir

- fixes recientes de CI, typing y compatibilidad Windows
- limpieza de `.gitignore` y remocion de artefactos locales de IA
- documentacion de adopcion temprana
- plan de piloto y roadmap actualizado

### No incluir

- features nuevas grandes
- cambios de arquitectura
- extras de IA local
- rediseno de CLI

## Archivos a Actualizar Antes del Tag

- [pyproject.toml](/Users/joseruiz/Documents/Code/Python/Loom-Context/pyproject.toml)
- [src/loom_context/__init__.py](/Users/joseruiz/Documents/Code/Python/Loom-Context/src/loom_context/__init__.py)
- [CHANGELOG.md](/Users/joseruiz/Documents/Code/Python/Loom-Context/CHANGELOG.md)
- [README.md](/Users/joseruiz/Documents/Code/Python/Loom-Context/README.md) si cambia wording o guidance

## Checklist Tecnico Pre-Release

### Codigo y calidad

- [ ] working tree limpio
- [ ] tests verdes
- [ ] lint verde
- [ ] format check verde
- [ ] mypy verde
- [ ] build verde
- [ ] `twine check` verde

### Empaque

- [ ] instalacion desde wheel
- [ ] instalacion desde repo
- [ ] `loom --version` correcto
- [ ] entrypoint CLI funcionando

### Docs

- [ ] quickstart verificado
- [ ] README consistente con version
- [ ] changelog actualizado
- [ ] planes enlazados desde `docs/INDEX.md`

## Smoke Test en Proyecto Real

### Perfil del proyecto piloto ideal

- repositorio activo
- estructura no trivial
- docs existentes
- uso real de arquitectura por capas o modulos
- tecnologia conocida por Loom

### Flujo

1. instalar `0.1.1` en entorno limpio
2. correr `loom init .`
3. revisar `.context/index.json`
4. revisar `.context/architecture.md`
5. correr `loom audit .`
6. usar `loom prompt . --stdout` en una tarea real con IA
7. correr `loom plan .`
8. registrar problemas y friccion

### Señales a observar

- deteccion correcta de tipo de proyecto
- arquitectura inferida razonable
- reglas accionables
- falsos positivos de auditoria
- tamano y utilidad del prompt
- claridad de los mensajes CLI

## Criterios de Go / No-Go

### Go

- CI verde
- build y packaging validados
- smoke test real completo
- sin errores bloqueantes de instalacion o CLI

### No-Go

- fallos de build o publicacion
- errores en Windows/macOS/Linux no documentados
- auditoria inutil por ruido extremo
- quickstart que no funcione en repo limpio

## Procedimiento de Release

### 1. Freeze corto

- no meter features nuevas
- solo fixes, docs y release prep

### 2. Version bump

- cambiar `0.1.0` -> `0.1.1` en version source y metadata

### 3. Changelog

Agregar seccion `0.1.1` con:

- fixes de CI
- mejoras de compatibilidad
- limpieza de tracking/config local
- docs de adopcion temprana

### 4. Verificacion local

Ejecutar:

```bash
python3 -m pytest -v --tb=short
python3 -m ruff check src/ tests/
python3 -m ruff format --check src/ tests/
python3 -m build
python3 -m twine check dist/*
```

### 5. Commit de release

Mensaje sugerido:

```text
chore(release): prepare v0.1.1
```

### 6. Tag

```bash
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

### 7. GitHub Release

Titulo sugerido:

```text
v0.1.1 - Early adoption release
```

Resumen sugerido:

- first real-world adoption release
- improved CI and packaging confidence
- ready for pilot use in real repositories
- roadmap and pilot guidance included

### 8. PyPI Publish

Usar workflow existente de publicacion o flujo manual controlado.

## Notas de Release Sugeridas

### Highlights

- primera release pensada para probar Loom en repos reales
- mejoras de estabilidad y CI
- mejor compatibilidad de output y packaging
- documentacion y planes mas claros para adopcion

### What to test

- `loom init .`
- `loom audit .`
- `loom prompt .`
- `loom plan .`
- experiencia completa en un repo real

### Feedback wanted

- falsos positivos
- proyectos mal clasificados
- prompt demasiado grande o irrelevante
- mejoras de DX

## Plan Post-Release (7 dias)

### Dia 0

- publicar release
- instalar en proyecto piloto

### Dia 1-2

- registrar bugs de instalacion y CLI
- registrar falsos positivos de `audit`

### Dia 3-4

- revisar utilidad del prompt en tareas reales
- detectar huecos de contexto

### Dia 5-7

- consolidar hallazgos
- decidir backlog de `0.2`
- priorizar `bundle`, `handoff` y retrieval local

## Output Esperado del Piloto

- [ ] 1 caso de exito documentado
- [ ] 1 lista priorizada de bugs
- [ ] 1 lista priorizada de mejoras DX
- [ ] decision clara sobre alcance de `0.2`

## Recomendacion Final

Libera `0.1.1`, no esperes a nuevas features grandes, y usalo esta misma semana en un proyecto real.

La mejor manera de acertar con `0.2` no es especular mas, sino observar:

- donde falla `audit`
- que sobra en `prompt`
- que friccion aparece en instalacion y uso diario

