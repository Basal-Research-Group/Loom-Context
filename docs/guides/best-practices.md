---
type: guide
audience: user
---

# 📐 Buenas Practicas

## TL;DR

Loom es mas util cuando lo integras en tu flujo diario: scan al empezar, bundle antes de cada tarea, enrich al terminar, handoff para retomar.

---

## 👤 Para el Ingeniero Individual

### 1. 🔄 Flujo diario con Loom

```bash
# Al empezar
loom status .                              # ver estado
loom scan .                                # refrescar contexto

# Antes de una tarea
loom bundle "mi tarea" . --stdout          # contexto enfocado
loom export . --agent claude               # exportar para tu agente

# Durante el trabajo
loom decide "..." -r "..." -s architecture # registrar decisiones
loom log "progreso" -p .                   # anotar sesion

# Al terminar
loom enrich .                              # re-auditar y persistir
loom handoff "mi tarea" . --save           # handoff para manana
```

### 2. ✅ Audita antes de commit

```bash
loom audit .
git add .
git commit -m "feat: add payment flow"
```

> 💡 Detecta violaciones de boundaries y naming antes de que lleguen al PR.

### 3. 📦 Usa bundle en vez de prompt completo

```bash
# Mal: prompt completo (35KB de contexto)
loom prompt . --stdout | pbcopy

# Bien: bundle enfocado (2-4KB de contexto relevante)
loom bundle "refactorizar auth" . --stdout | pbcopy
```

> 📉 93% menos tokens, misma precision para la tarea.

### 4. 💡 Registra decisiones, no solo codigo

```bash
loom decide "migrar a repository pattern" -r "desacoplar persistencia de core" -s architecture
```

> Un agente que lea tu handoff sabe POR QUE se tomo una decision, no solo QUE se cambio.

---

## 👥 Para Equipos

### 1. 📂 Commitea `.context/` (en proyectos privados)

```bash
git add .context/
git commit -m "chore: update Loom context"
```

> Todo el equipo (y sus IAs) comparten el mismo entendimiento del proyecto.

### 2. 🤖 Agrega `loom audit` al CI

```yaml
# .github/workflows/lint.yml
- name: Audit architecture
  run: |
    pip install loom-context
    loom audit .
```

> PRs que violan boundaries se rechazan automaticamente.

### 3. 🤝 Usa handoff para rotaciones

```bash
# Dev A al terminar su turno
loom handoff "sprint task" . --save

# Dev B al empezar
cat .context/handoffs/sprint-task.md
```

### 4. 🩺 Doctor en CI

```bash
loom doctor .
```

> Detecta .loom/ faltante, contexto stale, archivos corruptos.

---

## 🤖 Para la IA

### Instrucciones recomendadas para tu system prompt

```
1. Lee .context/index.json primero. Respeta quick_rules sin excepcion.
2. Consulta .context/directory-map.md antes de crear archivos nuevos.
3. Verifica naming en .context/naming.md antes de nombrar clases o funciones.
4. Consulta .context/stack.json — no sugieras librerias que contradigan el stack.
5. Si mi peticion viola alguna regla, dimelo antes de escribir codigo.
```

O mejor: usa `loom export . --agent claude` y dale ese archivo directamente.

---

## ❌ Anti-Patrones

| Anti-patron | Por que es malo | Que hacer |
|-------------|----------------|-----------|
| Editar `.context/` manualmente | Se sobreescribe en cada scan | Usar `.context/loom.json` para overrides |
| Ignorar boundary errors | Son violaciones reales | Crear puerto/interfaz o documentar excepcion |
| Generar prompt una vez y olvidar | El contexto envejece | `loom scan` frecuente o `loom watch` |
| Usar Loom como unica documentacion | `.context/` es para IAs, no para humanos | Mantener `docs/` y `README.md` |
| Prompt completo para tareas puntuales | Desperdicio de tokens | Usar `loom bundle` o `loom focus` |

---

## ✅ Checklist de Integracion

- [ ] `pip install loom-context`
- [ ] `loom init .` en la raiz del proyecto
- [ ] Revisar `.context/index.json` — deteccion correcta
- [ ] Revisar `.context/architecture.md` — boundaries correctos
- [ ] `loom doctor .` — todo verde
- [ ] Decidir: `.context/` en git o en `.gitignore`
- [ ] Agregar `.loom/` a `.gitignore`
- [ ] Agregar `loom audit` al CI
- [ ] Primer tarea con `loom bundle "tarea" --stdout`

---

*Siguiente: [🧠 Filosofia →](./philosophy.md)*
