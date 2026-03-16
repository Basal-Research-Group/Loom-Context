# v0.3.0 — Retrieval Local Opcional

> Estado: PLANIFICADO
> Prerequisito: v0.2.2 (bundles heuristicos funcionando)
> Referencia: [ai-integration-strategy.md](../ai-integration-strategy.md)
> Condicion: solo si hay evidencia medible de que heuristicas no alcanzan

## Problema que resuelve

Las heuristicas lexicales tienen limite en proyectos grandes o con nomenclatura ambigua. Embeddings locales mejoran precision sin depender de servicios cloud.

## Que cambia

### Seleccion hibrida

```bash
loom bundle "refactorizar auth" --ai off    # solo heuristicas (default)
loom bundle "refactorizar auth" --ai local  # heuristicas + embeddings
loom bundle "refactorizar auth" --top-k 10
loom bundle "refactorizar auth" --token-budget 4000
```

### Pipeline

1. heuristicas producen candidatos
2. embeddings ordenan semanticamente
3. se corta por top-k o token-budget
4. se genera bundle con razones de inclusion

### Modelos candidatos

- `sentence-transformers/all-MiniLM-L6-v2` (MVP ligero)
- `BAAI/bge-m3` (mejor retrieval, multilingue)

### Packaging

```toml
[project.optional-dependencies]
ai = ["sentence-transformers>=2.0"]
```

```bash
pip install loom-context[ai]
```

El paquete base sigue con 4 dependencias.

## Entregables

- [ ] `selector/strategies/hybrid.py`
- [ ] `infrastructure/ai/embeddings.py`
- [ ] cache local en `.loom/cache/embeddings/`
- [ ] invalidacion incremental (si archivo cambia, recalcular embedding)
- [ ] mediciones baseline vs embeddings
- [ ] CLI flags: `--ai`, `--top-k`, `--token-budget`
- [ ] fallback a heuristicas si no hay modelo

## Prerequisitos de evidencia

Antes de implementar:

- [ ] 10 tareas reales documentadas
- [ ] archivos esperados por tarea
- [ ] precision@k baseline heuristico medido
- [ ] evidencia de que el problema es del ranking, no del pipeline

## Criterios de salida

- mejora medible de precision@k vs heuristico
- `--ai off` sigue funcionando sin extras instalados
- tiempo aceptable para proyectos medianos
- manifest.json registra strategy usada y scores

## Dependencias nuevas

Solo en extra `[ai]`: sentence-transformers (trae torch, transformers, etc.)
