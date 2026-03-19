---
type: delivery
status: planned
target_version: "next"
scope: docs, tooling
---

# Demo Cross-Platform Readiness Plan

Este plan documenta el próximo paso para que `docs/demo.sh` sea amable con los entornos Windows y para que Loom conserve aquella iniciativa como parte de la próxima entrega.

## Objetivo

Que el script pueda ejecutarse desde Git Bash, WSL o macOS/Linux sin problemas y que la documentación correspondiente comunique cuándo usar `clip` vs. `pbcopy`.

## Pendientes para la siguiente entrega

- [ ] Validar la detección de SO en entornos Windows reales (Git Bash, WSL) y recopilar notas de comportamiento.
- [ ] Documentar el requerimiento de shell Unix-like en el README o la guía de contribución.
- [ ] Asegurar que Loom reporta el plan como pendiente para el siguiente hotfix y compartir el plan `.loom/reports/plan-*.md` con el equipo.

## Confirmaciones

1. El script ya muestra qué comando de portapapeles usa cada plataforma.
2. El plan será regenerado con `loom plan . --generate` y se guardará en `.loom/reports/`.
