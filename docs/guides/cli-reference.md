---
type: guide
audience: user
---

# 📖 Referencia del CLI

## TL;DR

15 comandos organizados por flujo: escanear → generar → auditar → enriquecer → exportar.

---

## 📋 Todos los Comandos

| Comando | Que hace | Requiere .context/ |
|---------|----------|-------------------|
| `loom init` | 🔍 Scan completo + genera .context/ + .loom/ | No |
| `loom scan` | 🔄 Re-escanea y actualiza .context/ | No |
| `loom prompt` | 📝 Genera prompt maestro para IA | Si |
| `loom focus` | 🎯 Prompt filtrado por tarea | Si |
| `loom bundle` | 📦 Contexto minimo por tarea con manifest | Si |
| `loom handoff` | 🤝 Resumen para retomar trabajo | Si |
| `loom export` | 🤖 Formatea para un agente especifico | Si |
| `loom audit` | ✅ Valida reglas de arquitectura y naming | Si |
| `loom enrich` | 🔄 Re-audita + refresca + persiste | Si |
| `loom status` | 📊 Dashboard de salud del proyecto | Si |
| `loom doctor` | 🩺 Verifica salud del setup de Loom | No |
| `loom plan` | 📋 Resume docs y planes existentes | No |
| `loom decide` | 💡 Registra decisiones arquitectonicas | No |
| `loom log` | 📓 Memoria de sesion entre sessiones | No |
| `loom watch` | 👁️ Modo continuo con re-scan periodico | No |

---

## 🔍 Escaneo y Generacion

### `loom init [PATH]`

Escaneo completo + generacion de `.context/` + `.loom/` + audit integrado.

```bash
loom init .
loom init /path/to/project
```

**Pipeline:** scan → generate .context/ → create .loom/ → audit → persist findings

**Output:**
- `.context/` con 7 archivos canonicos
- `.loom/` con inconsistencies.json + mutations.jsonl
- Loomy `~(^ ^)~` si audit limpio, `~(! !)~` si hay errores

---

### `loom scan [PATH]`

Re-escanea y actualiza `.context/`. Mas rapido que init (no crea .loom/).

```bash
loom scan .
```

---

## 📝 Generacion de Contexto

### `loom prompt [PATH] [OPTIONS]`

Genera el prompt maestro compilando todo `.context/`.

```bash
loom prompt .                    # Info sobre el prompt
loom prompt . --stdout           # Imprime a stdout
loom prompt . -o prompt.md       # Guarda en archivo
loom prompt . --stdout | pbcopy  # Al portapapeles (macOS)
```

| Flag | Descripcion |
|------|-------------|
| `--stdout` | Imprime a stdout para piping |
| `-o FILE` | Guarda en archivo |

---

### `loom focus QUERY [PATH] [OPTIONS]`

Prompt filtrado por tarea — version ligera de bundle.

```bash
loom focus "autenticacion" .
loom focus "domain layer" . --stdout
loom focus "testing" . --max-chars 4000
```

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--stdout` | — | Imprime a stdout |
| `-o FILE` | — | Guarda en archivo |
| `--max-chars N` | 8000 | Limite de caracteres |

---

### `loom bundle TASK [PATH] [OPTIONS]`

📦 Contexto minimo por tarea con manifest trazable. Seleccion heuristica por relevancia.

```bash
loom bundle "refactorizar auth" .
loom bundle "implementar TTS" . --stdout
loom bundle "domain layer" . --save
loom bundle "testing" . --max-chars 4000
```

| Flag | Descripcion |
|------|-------------|
| `--stdout` | Imprime a stdout |
| `-o FILE` | Guarda en archivo |
| `--save` | Guarda en `.context/bundles/<slug>/` con manifest.json |
| `--max-chars N` | Limite de caracteres (default: 12000) |

**Output con --save:**
```
.context/bundles/<slug>/
  bundle.md       # contexto compilado
  manifest.json   # metadata: task, SHA, strategy, sections
```

---

### `loom handoff TASK [PATH] [OPTIONS]`

🤝 Resumen para retomar trabajo. Incluye estado actual, decisiones, sesiones, reglas.

```bash
loom handoff "mi tarea" .
loom handoff "refactor" . --stdout
loom handoff "sprint" . --save
```

| Flag | Descripcion |
|------|-------------|
| `--stdout` | Imprime a stdout |
| `-o FILE` | Guarda en archivo |
| `--save` | Guarda en `.context/handoffs/<slug>.md` |

---

### `loom export [PATH] --agent AGENT [OPTIONS]`

🤖 Formatea contexto para un agente especifico.

```bash
loom export . --agent claude    # → .context/exports/CLAUDE.md
loom export . --agent cursor    # → .context/exports/.cursorrules
loom export . --agent codex     # → .context/exports/AGENTS.md
loom export . --agent generic   # → .context/exports/.loom-export.md
loom export . --agent claude --stdout
loom export . --agent cursor -o .cursorrules
```

| Agente | Archivo generado | Formato |
|--------|-----------------|---------|
| `claude` | CLAUDE.md | System prompt completo |
| `cursor` | .cursorrules | Project type + rules + architecture |
| `codex` | AGENTS.md | Directives + architecture + directory map |
| `generic` | .loom-export.md | Prompt maestro universal |

> 🔒 Por defecto exporta a `.context/exports/`. Usa `-o` para escribir donde quieras.

---

## ✅ Auditoria y Enriquecimiento

### `loom audit [PATH]`

Valida codigo contra reglas en `.context/rules.json`.

```bash
loom audit .
```

**Auditors:**
- 📛 `NamingAuditor` — prefijos de interfaces (I), hooks (use)
- 🧱 `StructureAuditor` — boundaries entre capas (imports prohibidos)

**Exit codes:** `0` sin errores, `1` con errores.

---

### `loom enrich [PATH]`

🔄 Re-audita + refresca .context/ + persiste hallazgos en .loom/.

```bash
loom enrich .
```

**Pipeline:** audit → persist findings → re-scan → regenerate .context/ → record mutation

---

## 📊 Estado y Diagnostico

### `loom status [PATH] [OPTIONS]`

Dashboard de salud del proyecto.

```bash
loom status .
loom status . --json
```

| Flag | Descripcion |
|------|-------------|
| `--json` | Output en JSON |

**Muestra:** project type, architecture, freshness, audit results, findings, decisions, sessions.

**Loomy:** `~(O O)~` fresco, `~(- -)~` stale.

---

### `loom doctor [PATH]`

🩺 Verifica 11 checks de salud del setup de Loom.

```bash
loom doctor .
```

**Checks:** .context/ exists, index.json valid, context files present, .loom/ exists, findings, mutations, sessions, decisions, .gitignore, staleness.

---

## 📋 Planes y Documentacion

### `loom plan [PATH]`

Resume documentacion y planes del proyecto.

```bash
loom plan .
```

Muestra docs agrupados por tipo con status de checklists.

---

## 💡 Decisiones y Sesiones

### `loom decide [SUMMARY] [OPTIONS]`

Registra decisiones arquitectonicas en `.loom/decisions.jsonl`.

```bash
loom decide "usar repository pattern" -r "desacoplar persistencia" -s architecture
loom decide --show
loom decide --show --last 20
loom decide --clear
```

| Flag | Descripcion |
|------|-------------|
| `-r TEXT` | Rationale (por que) |
| `-s SCOPE` | architecture, naming, deps, security |
| `-p PATH` | Ruta del proyecto |
| `--show` | Ver decisiones recientes |
| `--last N` | Numero de entries (default: 10) |
| `--clear` | Borrar todas |

---

### `loom log [MESSAGE] [OPTIONS]`

📓 Memoria de sesion con metadata git automatica.

```bash
loom log "terminado refactor de auth" -p .
loom log --show -p .
loom log --show --last 20 -p .
loom log --clear -p .
```

| Flag | Descripcion |
|------|-------------|
| `-p PATH` | Ruta del proyecto |
| `--show` | Ver entries recientes |
| `--last N` | Numero de entries (default: 5) |
| `--clear` | Borrar log |

---

### `loom watch [PATH] [OPTIONS]`

👁️ Modo continuo: re-escanea a intervalos regulares.

```bash
loom watch .
loom watch . --interval 60
```

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--interval N` | 30 | Segundos entre scans |

**Detener:** `Ctrl+C`

---

## 🌐 Argumentos Globales

```bash
loom <command> [PATH]
```

- Si se omite PATH, usa `.` (directorio actual)
- Debe ser un directorio existente
- Puede ser absoluto o relativo

---

*Siguiente: [📁 El Output .context/ →](./context-output.md)*
