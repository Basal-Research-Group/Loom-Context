# Diagrama: Flujo de Datos

> *Como fluye la informacion desde tu codigo hasta el cerebro de la IA.*

## Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TU PROYECTO                                  │
│                                                                     │
│  package.json    tsconfig.json    src/        docs/     AGENTS.md   │
│       │               │            │           │            │       │
└───────┼───────────────┼────────────┼───────────┼────────────┼───────┘
        │               │            │           │            │
        ▼               ▼            ▼           ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SECURITY FILTER                                   │
│         .gitignore + .contextignore + secrets                       │
│                                                                     │
│  Excluye: node_modules, .env, .pem, dist, .git, credentials        │
│  Pasa:    archivos seguros de codigo, config, docs                  │
└───────┬───────────────┬────────────┬───────────┬────────────────────┘
        │               │            │           │
        ▼               ▼            ▼           ▼
┌──────────────┐ ┌─────────────┐ ┌────────┐ ┌─────────┐
│   Deps       │ │   Code      │ │Structur│ │  Docs   │
│   Scanner    │ │   Scanner   │ │Scanner │ │ Scanner │
│              │ │             │ │        │ │         │
│ Parsea:      │ │ Infiere:    │ │Detecta:│ │ Indexa: │
│ package.json │ │ naming      │ │ tipo   │ │ titulos │
│ pyproject    │ │ convenciones│ │ arq    │ │ status  │
│ requirements │ │ prefijos    │ │ arbol  │ │ tipos   │
│              │ │ sufijos     │ │ layers │ │ plans   │
│ Categoriza:  │ │ aliases     │ │ annots │ │         │
│ 130+ pkgs    │ │             │ │        │ │         │
└──────┬───────┘ └──────┬──────┘ └───┬────┘ └────┬────┘
       │                │            │            │
       └────────────────┴──────┬─────┴────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     SCAN RESULT     │
                    │    (dict unificado) │
                    │                     │
                    │  structure: {...}    │
                    │  deps: {...}        │
                    │  code: {...}        │
                    │  docs: {...}        │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
          ┌───────────┐ ┌──────────┐ ┌───────────┐
          │  Index    │ │ Context  │ │  Prompt   │
          │ Generator │ │Generator │ │ Generator │
          │           │ │(Jinja2)  │ │           │
          │ quick_    │ │          │ │ Compila   │
          │ rules     │ │ 7 files  │ │ todo en   │
          │ metadata  │ │ .md+.json│ │ 1 prompt  │
          └─────┬─────┘ └────┬─────┘ └─────┬─────┘
                │            │              │
                ▼            ▼              ▼
          ┌──────────────────────────────────────┐
          │           .context/                   │
          │                                       │
          │  index.json ◄── IA lee esto primero   │
          │  architecture.md                      │
          │  naming.md                            │
          │  directory-map.md                     │
          │  stack.json                           │
          │  rules.json ──► loom audit lo usa     │
          │  plans-summary.md                     │
          └──────────────────┬───────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
             ┌───────────┐     ┌───────────┐
             │ AI Agent  │     │   loom    │
             │           │     │   audit   │
             │ Lee .ctx/ │     │           │
             │ genera    │     │ Lee rules │
             │ codigo    │     │ valida    │
             │ correcto  │     │ codigo    │
             └───────────┘     └───────────┘
```

## Flujo de Datos por Comando

### `loom init`
```
proyecto → FileFilter → 4 Scanners → ScanResult → IndexGen + ContextGen → .context/ (7 files)
```

### `loom scan`
```
proyecto → FileFilter → 4 Scanners → ScanResult → ContextGen → .context/ (actualizado)
```

### `loom prompt`
```
.context/ (7 files) → PromptGenerator → master prompt (stdout o archivo)
```

### `loom audit`
```
.context/rules.json → NamingAuditor + StructureAuditor → Violations → tabla Rich
```

### `loom plan`
```
proyecto → DocsScanner → docs indexados → tabla Rich
```

### `loom watch`
```
loop { proyecto → scan → .context/ → sleep(interval) }
```

---

*Siguiente: [Mapa de Componentes →](./component-map.md)*
