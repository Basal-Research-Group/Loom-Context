---
type: delivery
version: "0.3.0"
status: deferred
prerequisite: "0.2.2"
scope: infra, generator
languages: [python]
patterns: [strategy, adapter, policy]
---

# v0.3.0 — Retrieval Local Opcional

> Estado: POSTERGADO — se implementara solo con evidencia de que heuristicas no alcanzan.

## TL;DR

Agrega embeddings locales como capa opcional para mejorar la precision de seleccion en bundles. Fallback a heuristicas si no hay modelo. Se instala con `pip install loom-context[ai]`. Solo se implementa si hay evidencia de que las heuristicas no alcanzan.

## Por que se postergo

Las heuristicas de bundle (implementadas en v0.2.0) producen bundles 93% mas pequenos que el prompt completo y seleccionan contexto relevante en Akana (674 archivos). No hay evidencia de que embeddings mejorarian el resultado. Ademas, `sentence-transformers` trae PyTorch (~2GB), rompiendo el principio de ligereza.

Se activara cuando:
- se documenten 10+ tareas reales con archivos esperados
- precision@k baseline heuristico sea medido
- haya evidencia concreta de que heuristicas fallan en proyectos grandes

---

## Indice

- [Problema que resuelve](#problema-que-resuelve)
- [Analogia](#analogia)
- [Que cambia](#que-cambia)
- [Patrones de diseno](#patrones-de-diseno)
- [Entregables](#entregables)
- [Criterios de salida](#criterios-de-salida)

---

## Problema que resuelve

Las heuristicas lexicales tienen limite en proyectos grandes o con nomenclatura ambigua. Ejemplo: si buscas "autenticacion" pero los archivos se llaman `auth-gateway.ts`, la heuristica lo encuentra. Pero si se llaman `identity-provider.ts`, la heuristica falla.

Embeddings capturan similitud semantica, no solo lexical.

## Analogia

**Heuristicas:** es como buscar en un diccionario por la primera letra. Rapido, pero si la palabra esta escrita diferente, no la encuentras.

**Embeddings:** es como pedirle a alguien que entiende el idioma que te diga "que palabras significan algo parecido". Mas lento, pero encuentra relaciones que la busqueda por letra no puede.

- `--ai off` = busqueda por letra (rapido, determinista)
- `--ai local` = busqueda por significado (mas preciso, mas costo)

---

## Que cambia

### Pipeline hibrido

```
1. heuristicas producen candidatos (Strategy: heuristic)
2. embeddings ordenan semanticamente (Strategy: hybrid)
3. policy corta por top-k o token-budget
4. bundle se genera con razones de inclusion
```

### CLI

```bash
loom bundle "refactorizar auth" --ai off    # solo heuristicas (default)
loom bundle "refactorizar auth" --ai local  # heuristicas + embeddings
loom bundle "refactorizar auth" --top-k 10
loom bundle "refactorizar auth" --token-budget 4000
```

### Packaging

```bash
pip install loom-context        # base: 4 deps, sin IA
pip install loom-context[ai]    # + sentence-transformers
```

---

## Patrones de diseno

| Patron | Donde | Por que |
|--------|-------|---------|
| **Strategy** | `heuristic.py` vs `hybrid.py` | Intercambiar seleccion sin tocar el pipeline |
| **Adapter** | `infrastructure/ai/embeddings.py` | Encapsular modelo; mañana puedes cambiar de MiniLM a bge-m3 sin tocar nada mas |
| **Policy** | `budget.py` | Reglas de corte (top-k, token-budget, inclusion minima) separadas de la seleccion |
| **Cache** | `.loom/cache/embeddings/` | Evitar recalcular embeddings de archivos que no cambiaron |

---

## Entregables

- [ ] `selector/strategies/hybrid.py`
- [ ] `infrastructure/ai/embeddings.py` (Adapter)
- [ ] `selector/policies/budget.py` (Policy)
- [ ] cache local en `.loom/cache/embeddings/`
- [ ] invalidacion incremental (si archivo cambia, recalcular)
- [ ] CLI flags: `--ai`, `--top-k`, `--token-budget`
- [ ] fallback a heuristicas si no hay modelo
- [ ] mediciones baseline vs embeddings

## Prerequisitos de evidencia

Antes de implementar, se necesita:

- [ ] 10 tareas reales documentadas
- [ ] archivos esperados por tarea
- [ ] precision@k baseline heuristico medido
- [ ] evidencia de que el problema es del ranking, no del pipeline

## Criterios de salida

- Mejora medible de precision@k vs heuristico
- `--ai off` sigue funcionando sin extras
- Tiempo aceptable para proyectos medianos
- manifest.json registra strategy usada y scores

## Dependencias nuevas

Solo en extra `[ai]`: `sentence-transformers` (trae torch, transformers, etc.)

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Peso excesivo de dependencias | Extra opcional, no en base |
| Tiempos altos de indexado | Cache persistente en `.loom/` |
| Bundles menos reproducibles | Registrar score y strategy en manifest |
