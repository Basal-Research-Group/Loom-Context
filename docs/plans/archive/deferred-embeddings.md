---
type: delivery
status: deferred
scope: infra, generator
languages: [python]
patterns: [strategy, adapter, policy]
progress: 0/8
---

# IA Opcional — Embeddings y Ranking Semantico

> Estado: POSTERGADO — se implementara solo con evidencia de que heuristicas no alcanzan.

## TL;DR

Capa opcional de IA ligera para mejorar seleccion en bundles. No reemplaza el core determinista — opera encima de el. Se instala con `pip install loom-context[ai]`. El core sigue funcionando sin IA.

## Principio

El core de Loom es axiomatico: determinista, reproducible, sin dependencias de IA. La IA es una capa de mejora opcional que refina resultados, nunca los produce.

```
Capa 1: Determinista (siempre)     → heuristicas, reglas, patterns
Capa 2: IA opcional (futuro)       → embeddings para ranking semantico
Capa 3: IA de revision (futuro)    → reranker para refinar top-20
```

## Modelos Recomendados

### Embeddings: `sentence-transformers/all-MiniLM-L6-v2`

| Caracteristica | Valor |
|---------------|-------|
| Proposito | Semantic search basico |
| Peso | ~80MB |
| Costo | Gratuito, open source |
| Ventaja | Ligero, rapido, facil de integrar |
| Limitacion | Precision menor que modelos mas grandes |
| URL | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 |

Usar cuando: MVP de ranking semantico, proyectos en ingles, entorno modesto.

### Embeddings upgrade: `BAAI/bge-m3`

| Caracteristica | Valor |
|---------------|-------|
| Proposito | Retrieval multilingue (espanol/ingles) |
| Peso | ~1.5GB |
| Costo | Gratuito, open source |
| Ventaja | Mejor retrieval, buen soporte multilingue |
| Limitacion | Mas pesado que MiniLM |
| URL | https://huggingface.co/BAAI/bge-m3 |

Usar cuando: docs mezcladas es/en, reglas y planes extensos, calidad sobre velocidad.

### Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

| Caracteristica | Valor |
|---------------|-------|
| Proposito | Refinar top-20 candidatos por relevancia |
| Peso | ~80MB |
| Costo | Gratuito, open source |
| Ventaja | Mucho mas ligero que un LLM, mejora precision |
| Limitacion | Solo reordena, no genera |
| URL | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2 |

Usar cuando: heuristicas producen buenos candidatos pero el orden no es optimo.

### Generacion minima (NO recomendado aun): `Qwen/Qwen2.5-Coder-7B-Instruct`

| Caracteristica | Valor |
|---------------|-------|
| Proposito | Handoff narrativo, resumen tecnico |
| Peso | ~4GB |
| Costo | Gratuito, pesos abiertos |
| Ventaja | Orientado a codigo, buena relacion calidad/costo |
| Limitacion | Pesado, no debe estar en camino critico del CLI |
| URL | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |

NO meter hasta que embeddings + reranker esten validados.

## Packaging

```toml
# pyproject.toml
[project.optional-dependencies]
ai = ["sentence-transformers>=2.0"]
```

```bash
pip install loom-context        # base: 4 deps, sin IA, funciona completo
pip install loom-context[ai]    # + sentence-transformers para ranking
```

**Regla:** el paquete base nunca requiere modelos ni torch.

## Pipeline Propuesto

```
1. heuristicas producen candidatos        (Strategy: heuristic) ← YA EXISTE
2. embeddings ordenan semanticamente      (Strategy: hybrid)    ← FUTURO
3. reranker refina top-20                  (Policy: rerank)     ← FUTURO
4. policy corta por top-k/token-budget    (Policy: budget)     ← YA EXISTE
5. bundle se genera con razones           (Builder)             ← YA EXISTE
```

## CLI Propuesto

```bash
loom bundle "tarea" . --ai off      # solo heuristicas (default, siempre funciona)
loom bundle "tarea" . --ai local    # heuristicas + embeddings
loom bundle "tarea" . --ai rerank   # heuristicas + embeddings + reranker
```

## Por que se postergo

- Heuristicas producen 93% de reduccion sin IA
- `sentence-transformers` trae PyTorch (~2GB)
- No hay evidencia de que embeddings mejorarian el resultado
- El costo en complejidad y deps supera el beneficio demostrado

## Se activara cuando

- [ ] 10+ tareas reales documentadas con archivos esperados
- [ ] precision@k baseline heuristico medido
- [ ] evidencia concreta de que heuristicas fallan
- [ ] usuario solicite ranking semantico

## Entregables (NO implementados)

- [ ] `selector/strategies/hybrid.py` (Strategy pattern)
- [ ] `infrastructure/ai/embeddings.py` (Adapter pattern)
- [ ] `selector/policies/rerank.py` (Policy pattern)
- [ ] cache local en `.loom/cache/embeddings/`
- [ ] invalidacion incremental (si archivo cambia, recalcular)
- [ ] CLI flags: `--ai off|local|rerank`
- [ ] fallback a heuristicas si modelo no instalado
- [ ] mediciones precision@k: baseline vs embeddings vs rerank
