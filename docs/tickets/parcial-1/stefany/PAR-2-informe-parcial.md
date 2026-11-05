# PAR-2: Informe del primer parcial (RP-10)

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Entrega del parcial |
| Parcial | Primer parcial |
| Fase | C — integración y entrega |
| Necesita | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Lo necesitan | [PAR-3](../stefany/PAR-3-demo-y-ensayo.md) (Stefany) |
| Plan | [`docs/plans/2026-10-25-parcial-1.md`](../../../plans/2026-10-25-parcial-1.md), sección *Task PAR-2* |
| Estado | Pendiente |

> **Rev. 5 (2026-11-03): manda la spec §23** (enunciado oficial; entrega el 04/11/2026). Este ticket ya está ajustado a ella; si el plan dice otra cosa, vale el ticket.

## Objetivo

El informe con los entregables de la spec §23.8.

## Cómo trabajar sin esperar

Los diagramas, la explicación de JWT y RBAC, la matriz de roles y la de riesgos se redactan desde la spec §23, `docs/trazabilidad-riesgos.md` y `docs/cumplimiento-normativo.md`. Las cifras y las evidencias esperan a que todo esté en verde.

## Criterios de aceptación

- [ ] Diagrama de arquitectura (Mermaid) con los límites de confianza (cliente ↔ gateway, gateway ↔ servicios, servicios ↔ BD) y la comunicación entre AUTH y STEGO
- [ ] Diagrama entidad-relación con la N:M `users` ↔ `user_roles` ↔ `roles`
- [ ] JWT (RS256, claims, clave y vigencia), RBAC y cómo se comprueban los roles vigentes en cada petición; matriz de roles y permisos (§23.3)
- [ ] Enlace a `docs/openapi/auth.json` y `docs/openapi/stego.json`
- [ ] Justificación del estegoanálisis: técnica, parámetros, formatos, TPR/FPR y limitaciones (de `docs/calibracion-estego.md`)
- [ ] Matriz activos → amenazas → vulnerabilidades → riesgos → controles (Anexo E del enunciado), ligada a Zero Trust, Secure by Design, Shift Left e ISO/IEC 27001/27034
- [ ] Las tres desviaciones de §23.2 explicadas
- [ ] Resultados de `pytest` de `shared`, `auth` y `stego` en `docs/evidencias/`; las cifras salen de correrlo, no de memoria
- [ ] Andrés revisó las secciones de `auth` y Zaith las de arquitectura

## Entregables

- `docs/informe-parcial-1.md`
- `docs/evidencias/pytest-*.txt`

## Documentación a actualizar

- `docs/requisitos.md`
- `docs/cumplimiento-normativo.md`

## Verificación

Lectura cruzada del equipo

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
