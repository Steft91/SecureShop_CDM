# AUD-3: Consulta y verificación para el admin global (R5)

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Audit |
| Incremento | Primer parcial |
| Necesita | [AUD-2](../andres/AUD-2-audit-ingesta-y-cadena.md) (Andrés) |
| Lo necesitan | [GW-1](../zaith/GW-1-gateway-parcial.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-02-audit.md`](../../plans/2026-10-13-02-audit.md), sección *Task AUD-3* |
| Estado | Pendiente |

## Objetivo

Consulta paginada y verificación de la cadena, solo con el permiso `audit:read`.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Criterios de aceptación

- [ ] `GET /api/admin/audit` con `audit:read` → eventos con `id > after_id`, del más nuevo al más viejo
- [ ] Sin el permiso → 403, y el intento queda registrado
- [ ] `GET /api/admin/audit/verify` → `{ok, broken_at}`; si la cadena está rota, registra `audit.chain.broken` (critical)
- [ ] La consulta por severidad con 100 000 eventos responde en ≤ 2 s (RNF-07)

## Entregables

- `services/audit/audit_svc/routes.py`
- `services/audit/tests/test_r05_admin.py`

## Documentación a actualizar

- Fila R5 de la trazabilidad
- `CLAUDE.md`: marcar `audit`

## Verificación

`pytest services/audit -q`

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Zaith de que AUD-3 ya está cerrado
