---
type: guide
audience: user
---

# 🔒 Seguridad

## TL;DR

Loom nunca expone codigo fuente ni secretos. Usa 3 capas de filtrado: `.gitignore` + `.contextignore` + patrones hardcoded. El output de `.context/` es solo metadata arquitectonica.

---

## 🛡️ Las 3 Capas de Proteccion

```
┌─────────────────────────────────────────────┐
│  🔹 Capa 1: .gitignore                      │
│  Si tu proyecto ya lo excluye, Loom tambien │
├─────────────────────────────────────────────┤
│  🔹 Capa 2: .contextignore                  │
│  Exclusiones adicionales especificas de     │
│  Loom (opcional, mismo formato que gitignore)│
├─────────────────────────────────────────────┤
│  🔹 Capa 3: Hardcoded Secrets               │
│  SIEMPRE excluidos, sin importar config     │
│  .env, .pem, .key, credentials, etc.        │
└─────────────────────────────────────────────┘
```

---

## 🔹 Capa 1: Respeto a `.gitignore`

Loom usa `pathspec` para parsear tu `.gitignore` con la misma semantica que Git. Si algo no entra a tu repositorio, Loom no lo lee.

## 🔹 Capa 2: `.contextignore`

Archivo opcional en la raiz del proyecto. Mismo formato que `.gitignore`:

```gitignore
# Excluir archivos de migracion
**/migrations/
**/seeds/

# Excluir assets pesados
assets/images/
assets/fonts/

# Excluir config local
*.config.local.js
```

## 🔹 Capa 3: Exclusiones Hardcoded

Estos patrones se excluyen **siempre**, aunque no esten en `.gitignore`:

### 📁 Directorios (siempre ignorados)

```
.git/          node_modules/    __pycache__/     .expo/
.next/         .nuxt/           dist/            build/
.cache/        .turbo/          vendor/          .venv/
venv/          env/             .tox/            .mypy_cache/
.pytest_cache/ .ruff_cache/     coverage/        .parcel-cache/
```

### 🔑 Archivos de secretos (siempre ignorados)

```
*.pem          *.key           *.p12            *.jks
*.keystore     *.cert          *.crt            .env
.env.*         .env.local      .env.production
credentials*   secrets*        *_rsa            id_rsa*
service-account*.json          google-services.json
GoogleService-Info.plist
```

---

## ✅ Que expone vs ❌ Que protege

| Dato | Expuesto | Razon |
|------|----------|-------|
| 📄 Nombres de archivos | ✅ | Metadata necesaria para contexto |
| 🗂️ Estructura de directorios | ✅ | Contexto arquitectonico |
| 📦 Nombres de dependencias | ✅ | Stack tecnologico |
| 🔢 Versiones de paquetes | ✅ | Compatibilidad |
| 🏷️ Patrones de naming | ✅ | Convenciones |
| 💻 **Contenido de archivos** | ❌ | Nunca se incluye codigo fuente |
| 🔐 **Variables de entorno** | ❌ | Secrets filtering |
| 🔑 **Tokens / API keys** | ❌ | Secrets filtering |
| 👤 **Datos de usuarios** | ❌ | No se lee contenido de DB |
| 🖼️ **Archivos binarios** | ❌ | Solo se leen archivos de texto |

---

## 🎯 Modelo de Amenazas

### Escenario: `.context/` se filtra publicamente

**Impacto:** 🟢 Bajo

Un atacante sabria: arquitectura, dependencias, naming, directorios.
No sabria: codigo, credenciales, logica de negocio, datos.

> Equivale a que alguien vea tu `package.json` y haga un `tree src/`.

### Escenario: IA alucina basandose en `.context/`

**Impacto:** 🟡 Bajo-Medio

La IA podria generar codigo que asume estructura obsoleta.

> Mitigacion: `loom scan .` frecuente o `loom watch .`.

---

## 💡 Recomendaciones

1. ✅ Ejecuta `loom init` solo en proyectos donde confias en la IA consumidora
2. ✅ Usa `.contextignore` para areas sensibles (migraciones, config produccion)
3. ✅ Regenera con `loom scan` antes de compartir con un nuevo agente
4. ⚠️ No commitees `.context/` en repos publicos si tu estructura es competitiva
5. ✅ Usa `loom doctor` para verificar que `.loom/` esta en `.gitignore`

---

*Siguiente: [📐 Buenas Practicas →](./best-practices.md)*
