---
type: delivery
version: "0.3.0"
status: deferred
prerequisite: "0.2.2"
scope: infra, generator
languages: [python]
patterns: [strategy, adapter, policy]
progress: 0/8
---

# v0.3.0 — Retrieval Local Opcional

> Estado: POSTERGADO — se implementara solo con evidencia de que heuristicas no alcanzan.

## TL;DR

Embeddings locales como capa opcional para mejorar precision de seleccion en bundles. Postergado porque las heuristicas de bundle ya producen 93% de reduccion y seleccionan contexto relevante sin IA.

## Por que se postergo

- Heuristicas de bundle funcionan bien en Akana (674 archivos, contexto relevante)
- `sentence-transformers` trae PyTorch (~2GB), rompe principio de ligereza
- No hay evidencia medible de que embeddings mejorarian el resultado

## Se activara cuando

- [ ] 10+ tareas reales documentadas con archivos esperados
- [ ] precision@k baseline heuristico medido
- [ ] evidencia concreta de que heuristicas fallan en proyectos grandes

## Entregables (NO implementados)

- [ ] `selector/strategies/hybrid.py`
- [ ] `infrastructure/ai/embeddings.py`
- [ ] `selector/policies/budget.py`
- [ ] cache local en `.loom/cache/embeddings/`
- [ ] invalidacion incremental
- [ ] CLI flags: `--ai off|local`
- [ ] fallback a heuristicas
- [ ] mediciones baseline vs embeddings
