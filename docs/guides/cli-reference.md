# Referencia del CLI

## Comandos

### `loom --help`
```
Usage: loom [OPTIONS] COMMAND [ARGS]...

  Loom - Architecture Context Engine for AI-First Engineering.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  audit   Validate code against rules defined in .context/.
  init    Scan project and create .context/ folder with all context files.
  plan    Read and summarize existing docs/plans for AI consumption.
  prompt  Generate master AI system prompt from .context/ files.
  scan    Re-scan project and update .context/ files.
  watch   Continuous mode: re-scan on interval.
```

---

### `loom init [PATH]`

Escaneo completo del proyecto + generacion de `.context/`.

```bash
loom init .                    # Proyecto actual
loom init /path/to/project     # Proyecto especifico
```

**Que hace:**
1. Crea `FileFilter` respetando `.gitignore` y secretos
2. Ejecuta los 4 scanners (structure, deps, code, docs)
3. Genera `IndexGenerator` con metadata y quick_rules
4. Escribe 7 archivos en `.context/` via `ContextGenerator`
5. Muestra resumen con Rich

**Output:** Directorio `.context/` con 7 archivos.

---

### `loom scan [PATH]`

Re-escanea y actualiza `.context/`.

```bash
loom scan .
```

**Diferencia con init:** Funcionalmente identico en v0.1. En versiones futuras, `scan` sera incremental (solo re-escanea archivos modificados).

---

### `loom prompt [PATH] [OPTIONS]`

Genera el master prompt compilando todo `.context/`.

```bash
loom prompt .                    # Info sobre el prompt
loom prompt . --stdout           # Imprime a stdout
loom prompt . -o prompt.md       # Guarda en archivo
loom prompt . --stdout | pbcopy  # Al portapapeles (macOS)
```

**Opciones:**
| Flag | Descripcion |
|------|-------------|
| `--stdout` | Imprime el prompt a stdout (para piping) |
| `-o FILE` / `--output FILE` | Guarda el prompt en un archivo |

**Requiere:** `.context/` existente. Ejecuta `loom init` primero.

---

### `loom audit [PATH]`

Valida codigo contra reglas en `.context/rules.json`.

```bash
loom audit .
```

**Auditors ejecutados:**
1. `NamingAuditor` — verifica naming conventions (prefijos, sufijos)
2. `StructureAuditor` — verifica layer boundaries (imports prohibidos)

**Exit codes:**
- `0` — sin errores
- `1` — errores encontrados

**Severidades:**
- `ERROR` — violacion que debe corregirse
- `WARNING` — posible problema, revisar manualmente
- `INFO` — sugerencia de mejora

**Requiere:** `.context/` existente.

---

### `loom plan [PATH]`

Lee y muestra documentacion y planes del proyecto.

```bash
loom plan .
```

**Que muestra:**
- Documentos agrupados por tipo (architecture, plan, feature, etc.)
- Path, titulo, tamano de cada documento
- Status de items en planes (done/pending/partial)

**No requiere** `.context/` — escanea docs directamente.

---

### `loom watch [PATH] [OPTIONS]`

Modo continuo: re-escanea a intervalos regulares.

```bash
loom watch .                     # Cada 30 segundos
loom watch . --interval 60       # Cada 60 segundos
loom watch . --interval 10       # Cada 10 segundos
```

**Opciones:**
| Flag | Default | Descripcion |
|------|---------|-------------|
| `--interval N` | 30 | Segundos entre scans |

**Para detener:** `Ctrl+C`

---

## Argumentos Globales

Todos los comandos aceptan `PATH` como primer argumento:

```bash
loom <command> [PATH]
```

- Si se omite, usa `.` (directorio actual)
- Debe ser un directorio existente
- Puede ser absoluto o relativo

---

*Siguiente: [El Output .context/ →](./context-output.md)*
