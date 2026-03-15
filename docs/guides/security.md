# Seguridad

> *Loom opera bajo el principio de minimo privilegio: solo expone lo estrictamente necesario.*

## Las 3 Capas de Proteccion

```
┌─────────────────────────────────────────────┐
│  Capa 1: .gitignore                         │
│  Si tu proyecto ya lo excluye, Loom tambien │
├─────────────────────────────────────────────┤
│  Capa 2: .contextignore                     │
│  Exclusiones adicionales especificas de     │
│  Loom (opcional, mismo formato que gitignore│
├─────────────────────────────────────────────┤
│  Capa 3: Hardcoded Secrets                  │
│  SIEMPRE excluidos, sin importar config     │
│  .env, .pem, .key, credentials, etc.        │
└─────────────────────────────────────────────┘
```

## Capa 1: Respeto a `.gitignore`

Loom usa la libreria `pathspec` para parsear tu `.gitignore` con la misma semantica que Git. Si algo no entra a tu repositorio, Loom no lo lee.

## Capa 2: `.contextignore`

Archivo opcional en la raiz del proyecto. Mismo formato que `.gitignore`:

```gitignore
# Excluir archivos de migracion
**/migrations/
**/seeds/

# Excluir assets pesados
assets/images/
assets/fonts/

# Excluir archivos de config especificos
*.config.local.js
```

## Capa 3: Exclusiones Hardcoded

Estos patrones se excluyen **siempre**, aunque no esten en `.gitignore`:

### Directorios (siempre ignorados)
```
.git/              node_modules/      __pycache__/
.expo/             .next/             .nuxt/
dist/              build/             .cache/
.turbo/            vendor/            .venv/
venv/              env/               .tox/
.mypy_cache/       .pytest_cache/     .ruff_cache/
coverage/          .nyc_output/       .parcel-cache/
```

### Archivos de secretos (siempre ignorados)
```
*.pem              *.key              *.p12
*.p8               *.jks              *.keystore
*.mobileprovision  *.cert             *.crt
.env               .env.*             .env.local
.env.production    credentials*       secrets*
*_rsa              id_rsa*
service-account*.json
google-services.json
GoogleService-Info.plist
```

## Que Nunca Sale en el Output

| Dato | Expuesto? | Razon |
|------|-----------|-------|
| Nombres de archivos | Si | Metadata necesaria para la IA |
| Estructura de directorios | Si | Contexto arquitectonico |
| Nombres de dependencias | Si | Stack tecnologico |
| Versiones de paquetes | Si | Compatibilidad |
| Patrones de naming | Si | Convenciones |
| **Contenido de archivos** | **No** | Nunca se incluye codigo fuente |
| **Variables de entorno** | **No** | Secrets filtering |
| **Tokens/API keys** | **No** | Secrets filtering |
| **Datos de usuarios** | **No** | No se lee contenido de DB |
| **Archivos binarios** | **No** | Solo se leen archivos de texto |

## Modelo de Amenazas

### Escenario: `.context/` se filtra publicamente

**Impacto:** Bajo. Un atacante sabria:
- Que arquitectura usas (clean-arch, hexagonal)
- Que dependencias tienes y sus versiones
- Como nombras tus archivos
- Que directorios existen

**No sabria:**
- El codigo real
- Credenciales
- Logica de negocio
- Datos de usuarios

**Mitigacion:** Equivale a que alguien vea tu `package.json` y haga un `tree src/`. Informacion util pero no critica.

### Escenario: IA "alucina" basandose en `.context/`

**Impacto:** Bajo-Medio. La IA podria generar codigo que:
- Asume una estructura que cambio desde el ultimo `loom scan`
- Sigue reglas obsoletas

**Mitigacion:** Ejecutar `loom scan` frecuentemente, o usar `loom watch`.

## Recomendaciones

1. **Ejecuta `loom init` solo en proyectos donde confias en la IA** que consumira el contexto
2. **Usa `.contextignore`** para excluir areas sensibles (archivos de migracion con datos seed, configuraciones de produccion)
3. **No commitees `.context/`** en repos publicos si tu estructura es informacion competitiva
4. **Regenera con `loom scan`** antes de compartir el prompt con un nuevo agente

---

*Siguiente: [Buenas Practicas →](./best-practices.md)*
