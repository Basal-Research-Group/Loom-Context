---
type: guide
audience: developer
---

# Loomy — La Mascota de Loom-Context

## TL;DR

Loomy es una neurona-araña que vive en tu terminal. Teje hilos de contexto entre los archivos de tu proyecto. Sus expresiones te dicen el estado de Loom sin leer logs.

---

## Quien es Loomy

Loomy es la mascota oficial de Loom-Context. Es una neurona que parece araña: un soma central con dendritas que se extienden en todas direcciones, tejiendo hilos de contexto a traves de tu codebase.

### Analogia

Asi como una neurona conecta sinapsis para formar memoria, Loomy conecta archivos, reglas, arquitectura y docs para formar el contexto que los agentes de IA necesitan.

### Arte ASCII (banner de init)

```
        .  *  .  *  .
         \  |  /
      ── (O O) ──
         /  |  \
        *  .  *  .  *
```

El soma `(O O)` es el nucleo de Loomy. Las dendritas `\ | /` y `/ | \` son los hilos que teje hacia tu codigo. Los puntos y asteriscos `* . *` son los nodos de tu proyecto que Loomy conecta.

---

## Expresiones

Loomy tiene 8 expresiones que comunican estado emocional:

| Expresion | Nombre | Cuando aparece | Significado |
|-----------|--------|---------------|-------------|
| `~(O O)~` | Neutral | Status dashboard | "Estoy observando tu proyecto" |
| `~(^ ^)~` | Happy | Audit limpio, operacion exitosa | "Todo conectado, sin problemas" |
| `~(! !)~` | Alert | Violaciones encontradas | "Hay hilos que necesitan atencion" |
| `~(. .)~` | Thinking | Escaneando, procesando | "Estoy analizando tu proyecto..." |
| `~(x x)~` | Fail | Error de comando, no .context/ | "No puedo tejer sin contexto" |
| `~(? ?)~` | Curious | Proyecto vacio, primer init | "Proyecto vacio... nada que tejer aun" |
| `~(- -)~` | Sleeping | Contexto stale, necesita rescan | "El contexto esta dormido, necesita actualizarse" |
| `~(^ o)~` | Wink | Decision registrada | "Anotado" (guino) |

### Donde aparece cada expresion

| Comando | Expresion | Momento |
|---------|-----------|---------|
| `loom init` | `(O O)` banner | Inicio |
| `loom init` | `~(. .)~` | Escaneando |
| `loom init` | `~(^ ^)~` | Audit limpio |
| `loom init` | `~(! !)~` | Violaciones encontradas |
| `loom init` | `~(? ?)~` | Proyecto vacio |
| `loom scan` | `~(. .)~` | Escaneando |
| `loom scan` | `~(^ ^)~` | Actualizado |
| `loom status` | `~(O O)~` | Contexto fresco |
| `loom status` | `~(- -)~` | Contexto stale |
| `loom status` | `~(x x)~` | No inicializado |
| `loom audit` | `~(^ ^)~` | Sin violaciones |
| `loom enrich` | `~(^ ^)~` | Enriquecido |
| `loom enrich` | `~(! !)~` | Hay errores |
| `loom decide` | `~(^ o)~` | Decision registrada |
| `loom log` | `~(^ ^)~` | Sesion registrada |
| `loom bundle` | `~(. .)~` | Tejiendo bundle |
| `loom bundle` | `~(^ ^)~` | Bundle listo |
| `loom bundle` | `~(? ?)~` | Sin contexto relevante |
| `loom prompt` | `~(x x)~` | No .context/ |
| `loom focus` | `~(x x)~` | No .context/ |

---

## Filosofia de diseno

- **Sin emojis** — Loomy usa ASCII puro. Funciona en cualquier terminal
- **Funcional, no decorativo** — cada expresion comunica un estado real
- **Zero cost** — son string literals, no hay computo ni dependencias
- **Sutil** — no interrumpe el flujo de trabajo, complementa la informacion
- **Developer experience** — ese toque de personalidad que convierte una herramienta en algo memorable

### Tagline

> weaving context, one thread at a time

---

## Implementacion tecnica

Todas las expresiones estan en `src/loom_context/brand.py`. El banner usa `rich.text.Text` para renderizar correctamente los backslashes en terminales. Las expresiones pequenas usan Rich markup.

### Agregar una nueva expresion

```python
# En brand.py:
LOOMY_NEW = "[magenta]~[bold bright_magenta](@ @)[/bold bright_magenta]~[/magenta]"

# En el comando CLI:
from loom_context.brand import LOOMY_NEW
console.print(f"  {LOOMY_NEW} mensaje")
```

### Regla

- Los ojos siempre son 1 caracter cada uno, separados por espacio
- Las dendritas `~` siempre rodean al soma
- El soma siempre esta en parentesis
- Magenta para normal, yellow para alert, red para fail, dim para sleeping
