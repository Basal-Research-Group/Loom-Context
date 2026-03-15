# Buenas Practicas

> *Loom es tan util como el flujo de trabajo donde lo integras.*

## Para el Ingeniero Individual

### 1. Inicia cada sesion con Loom

```bash
loom scan .                       # Actualiza contexto
loom prompt . --stdout | pbcopy   # Copia al portapapeles
# Pega en tu IA antes de empezar a trabajar
```

**Por que:** La IA arranca con contexto completo en lugar de descubrir tu proyecto archivo por archivo.

### 2. Audita antes de commit

```bash
loom audit .
git add .
git commit -m "feat: add payment flow"
```

**Por que:** Detecta violaciones de boundaries y naming antes de que lleguen al PR.

### 3. Usa watch durante desarrollo activo

```bash
loom watch . --interval 60 &     # Background, cada minuto
# ... desarrolla normalmente ...
```

**Por que:** `.context/` siempre esta fresco. Si cambias la estructura, la IA lo sabe.

---

## Para Equipos

### 1. Commitea `.context/` (en proyectos privados)

```bash
# NO agregues .context/ a .gitignore
git add .context/
git commit -m "chore: update Loom context"
```

**Beneficio:** Todo el equipo (y sus IAs) comparten el mismo entendimiento del proyecto.

### 2. Agrega `loom scan` al CI/CD

```yaml
# .github/workflows/lint.yml
- name: Update Loom context
  run: |
    pip install loom-context
    loom scan .

- name: Audit architecture
  run: loom audit .
```

**Beneficio:** PRs que violan boundaries se rechazan automaticamente.

### 3. Personaliza con `.context/loom.json` (v0.1: parcial)

Crea `.context/loom.json` para overrides basicos del equipo. En v0.1, Loom lee `project_type` de este archivo para forzar la deteccion:

```json
{
  "project_type": "react-native-expo"
}
```

> **Roadmap v0.2:** Se planea soporte para `extra_rules`, `audit_exceptions` y reglas personalizadas. Por ahora, `loom.json` solo soporta `project_type` override.

### 4. Documenta las excepciones

Si `loom audit` reporta violaciones que son **intencionales** (como el bootstrap/DI que importa de infrastructure para hacer wiring), documentalas como comentarios en el codigo:

```typescript
// LOOM-EXCEPTION: layer-boundary
// Bootstrap is the DI wiring point — must access all layers to register bindings
import { UserRepository } from '@infrastructure/repositories/UserRepository';
```

Esto no suprime el reporte de Loom (aun), pero documenta la intencion para el equipo y para futuras versiones que lean estos marcadores.

---

## Para la IA

### 1. Lee `index.json` primero

Instruccion recomendada para tu system prompt:

```
Antes de sugerir cualquier codigo, lee .context/index.json.
Respeta los quick_rules sin excepcion.
Si mi peticion viola alguna regla, dimelo antes de escribir codigo.
```

### 2. Consulta `directory-map.md` antes de crear archivos

```
Cuando necesites crear un archivo nuevo, consulta .context/directory-map.md
para ubicarlo en el directorio correcto segun la arquitectura del proyecto.
```

### 3. Verifica naming contra `naming.md`

```
Antes de nombrar una clase, interface, hook o archivo, consulta
.context/naming.md para seguir las convenciones detectadas.
```

### 4. No asumas versiones — consulta `stack.json`

```
No sugieras sintaxis obsoleta. Consulta .context/stack.json para
saber las versiones exactas de cada tecnologia.
```

---

## Anti-Patrones (que NO hacer)

### No edites `.context/` manualmente

Los archivos generados se sobreescriben en cada `loom scan`. Si necesitas personalizar, usa `.context/loom.json`.

### No ignores los boundaries

Si `loom audit` reporta un `ERROR` de layer-boundary, no lo ignores. Es una violacion real de tu arquitectura. La solucion correcta es:
- Crear una interfaz/puerto en la capa correcta
- Inyectar la implementacion via DI
- O documentar la excepcion si es intencional

### No generes el prompt una vez y lo olvides

El contexto envejece. Cada vez que:
- Agregas un directorio nuevo
- Instalas una dependencia
- Cambias una convencion

...necesitas `loom scan` para actualizar.

### No uses Loom como documentacion unica

`.context/` es un **complemento** a tu documentacion real. Es lo que la IA necesita, no lo que un nuevo ingeniero necesita. Para onboarding humano, sigue manteniendo tu `docs/` y `README.md`.

---

## Checklist de Integracion

- [ ] `pip install loom-context` en tu entorno
- [ ] `loom init .` en la raiz del proyecto
- [ ] Revisar `.context/index.json` — verificar que la deteccion es correcta
- [ ] Revisar `.context/architecture.md` — confirmar boundaries
- [ ] Decidir: commitear `.context/` o `.gitignore`
- [ ] Agregar `loom scan` a tu flujo pre-commit o CI
- [ ] Pegar `loom prompt --stdout` en tu primer mensaje a la IA
- [ ] Opcionalmente: `loom watch` durante desarrollo

---

*Siguiente: [Flujo de Datos →](../diagrams/data-flow.md)*
