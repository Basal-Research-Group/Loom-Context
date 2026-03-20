---
type: guide
audience: user
---

# Quick Start Guide

## TL;DR

Install Loom, run `loom setup .` in your project, and in <2 seconds you have
architectural context ready for any AI agent.

---

## Install

```bash
# Recommended — installs in isolated environment, no venv needed
pipx install loom-context
```

> Don't have pipx? `brew install pipx` (macOS) or `sudo apt install pipx` (Linux).

Or try it first without installing:

```bash
pipx run loom-context init .
```

<details>
<summary>Alternative: pip with virtual environment</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows
pip install loom-context
```

</details>

Verify:

```bash
loom --version
# loom, version 0.4.0
```

---

## First Setup (the easy way)

```bash
cd your-project/
loom setup .
```

Loom will:
1. Scan your project structure, dependencies, naming, and documentation
2. Generate `.context/` with all metadata files
3. Check if your project needs infrastructure (Redis, PostgreSQL, etc.)
4. Detect existing agent files and ask which agents to install
5. Backup any existing files before overwriting

```
  ~(. .)~ Scanning /path/to/your-project...

  Project Type       react-native-expo
  Architecture       clean-architecture, hexagonal
  Files Scanned      683
  Dependencies       95
  Package Manager    pnpm

  Generated .context/

  Your project requires these services:
    PostgreSQL (database) — running
    Redis (cache) — not running (port 6379)
    > Start: brew services start redis

  Checking existing agent files...
    + CLAUDE.md exists (hand-crafted, 2.4 KB)
    ~ .cursorrules not found

  Install for Claude? (CLAUDE.md exists, will backup) [Y/n]: y
  Install for Cursor? [Y/n]: y

  Setup complete: 2 agents installed, 1 backups in .loom/backups/
```

### Non-interactive mode (for CI/scripts):

```bash
loom setup . --preset full --force      # all 5 agents, no prompts
loom setup . --preset claude --force    # just Claude
loom setup . --agent codex --force      # just Codex
```

---

## First Setup (step by step)

If you prefer individual commands:

```bash
# 1. Scan and generate context
loom init .

# 2. Check health
loom doctor .

# 3. Export for your agent
loom export . --agent claude --install

# 4. Check infrastructure
loom infra .
```

---

## Get Task-Specific Context

Instead of the full prompt (~1,300 tokens), generate only what's relevant:

```bash
loom bundle "refactor auth boundaries" . --stdout
```

```
  Bundle for "refactor auth boundaries"
  656 chars | 7 sections | strategy: heuristic
  ~118 tokens vs ~1,359 full prompt (91% saved)
```

Copy to clipboard:
```bash
loom bundle "my task" . --stdout | pbcopy    # macOS
loom bundle "my task" . --stdout | clip      # Windows
```

Save to file:
```bash
loom bundle "my task" . --save
# → .context/bundles/my-task/bundle.md + manifest.json
```

---

## Export for Your Agent

```bash
loom export . --agent claude --install    # → CLAUDE.md
loom export . --agent cursor --install    # → .cursorrules
loom export . --agent codex --install     # → AGENTS.md
loom export . --agent copilot --install   # → .github/copilot-instructions.md
loom export . --agent generic --install   # → .loom-export.md
```

> Loom automatically backs up existing files before overwriting.
> Use `--no-backup` to skip, `--force` to skip confirmation.

---

## Check Infrastructure

See what services your project needs and if they're running:

```bash
loom infra .
```

Start stopped services:
```bash
loom infra . --start              # native (brew/systemctl)
loom infra . --start --docker     # Docker containers
```

---

## Audit Rules

```bash
loom audit .
```

If violations are found:
```
  Summary: 48 errors, 0 warnings
  Run loom audit --summary for grouped view
```

---

## Daily Workflow

```bash
# 1. Start of day — check state
loom status .
loom scan .                               # instant if no changes (cached)

# 2. Before a task — get focused context
loom bundle "implement payment flow" . --stdout | pbcopy

# 3. During work — record decisions
loom decide "use Stripe adapter" -r "team standard" -s architecture

# 4. End of day — persist and handoff
loom enrich .
loom handoff "payment flow" . --save
```

---

## What Goes in Git

| Path | Track in git | Why |
|------|:---:|-----|
| `.context/*.md, *.json` | Yes | Reproducible project context |
| `.context/exports/` | No | Regenerated with `loom export` |
| `.context/bundles/` | No | Regenerated with `loom bundle` |
| `.loom/reports/` | Yes | Metrics, deltas, plans |
| `.loom/*` (rest) | No | Local state per user |

Loom configures `.gitignore` automatically on `loom init`.

---

*Next: [CLI Reference](./cli-reference.md)*
