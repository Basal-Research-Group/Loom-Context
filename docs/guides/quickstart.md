# Guia de Inicio Rapido

## Instalacion

```bash
# Desde el repositorio local
pip install .

# Desde GitHub directamente
pip install git+https://github.com/jadruiz/Loom-Context.git

# Verificar
loom --version
# loom, version 0.1.0
```

> **Nota:** Si `loom` no esta en tu PATH, usa `python3 -m loom_context.cli` o agrega `~/.local/bin` o `~/Library/Python/3.x/bin` a tu PATH.

## Primer Scan

```bash
cd tu-proyecto/
loom init .
```

Output esperado:
```
╭──────────────────────────────────────────────╮
│ Loom Context Engine v0.1.0                   │
╰──── Architecture Context for AI Agents ──────╯

  Scanning /path/to/tu-proyecto...

  Project Type       react-native-expo
  Architecture       clean-architecture, hexagonal, feature-based
  Files Scanned      663
  Code Files         702
  Docs Found         52
  Dependencies       95
  Package Manager    pnpm

  Generated .context/
    + index.json
    + architecture.md
    + naming.md
    + directory-map.md
    + stack.json
    + rules.json
    + plans-summary.md

  Quick Rules (11):
    > Layer boundary: domain MUST NOT import from infrastructure
    > Layer boundary: core MUST NOT import from presentation
    > React hooks MUST have 'use' prefix
    > Repository files follow pattern: {Name}Repository.ts
    > Service files follow pattern: {Name}Service.ts
    ... and 6 more

  Done in 1.1s
```

## Usar el Prompt con IA

### Opcion 1: Copiar al portapapeles (macOS)
```bash
loom prompt . --stdout | pbcopy
```
Luego pega en ChatGPT, Claude, o cualquier LLM.

### Opcion 2: Guardar a archivo
```bash
loom prompt . -o .context/PROMPT.md
```

### Opcion 3: Usar como system prompt en Cursor/Copilot
Copia `.context/` a tu proyecto y configura tu IDE para leer `index.json` como contexto.

### Opcion 4: Integrar con CLAUDE.md o .cursorrules
```bash
# Genera el prompt y anexalo a tu archivo de reglas de IA
loom prompt . --stdout >> CLAUDE.md
```

## Auditar tu Codigo

```bash
loom audit .
```

Output si hay violaciones:
```
  Auditing /path/to/project...

┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Severity ┃ File          ┃ Line  ┃ Rule          ┃ Message       ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ ERROR    │ src/core/di…  │ 8     │ layer-bound…  │ 'core' imports│
│          │               │       │               │ from          │
│          │               │       │               │ 'infrastructure│
│ WARNING  │ src/domain/…  │ 12    │ interface-pr… │ Interface     │
│          │               │       │               │ 'UserRepo'    │
│          │               │       │               │ missing 'I'   │
│          │               │       │               │ prefix        │
└──────────┴───────────────┴───────┴───────────────┴───────────────┘

  Summary: 1 errors, 1 warnings, 2 total
```

## Ver Planes del Proyecto

```bash
loom plan .
```

```
  ARCHITECTURE (2 files)
    docs/architecture/capas.md  Capas y Modulos  (12.0KB)
    docs/architecture/di.md     Bootstrap y DI   (13.0KB)

  PLAN (8 files)
    docs/plans/00-indice.md  Plan Maestro  (5.2KB)
      Status: 5/8 done
    docs/plans/01-setup.md   Setup inicial (3.1KB)
      Status: 3/3 done
```

## Modo Watch (Desarrollo Continuo)

```bash
loom watch . --interval 60
```

```
  Watching /path/to/project every 60s. Press Ctrl+C to stop.

  [14:30:00] Updated .context/ in 1.1s
  [14:31:00] Updated .context/ in 0.9s
  [14:32:00] Updated .context/ in 1.0s
  ^C
  Stopped.
```

## Que Sigue

1. **Lee** `.context/index.json` para entender que detecto Loom
2. **Revisa** `.context/architecture.md` para confirmar que las reglas son correctas
3. **Personaliza** creando `.context/loom.json` si necesitas overrides
4. **Decide** si `.context/` va en tu `.gitignore` (privado) o se commitea (equipo)
5. **Integra** el prompt en tu flujo con tu IA favorita

---

*Siguiente: [Referencia del CLI →](./cli-reference.md)*
