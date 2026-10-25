# T-42 · FE-5: Frontend: panel del admin global

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Incremento 3 |
| Bloqueado por | [T-41 · FE-4](../stefany/T-41-frontend-imagenes.md) (Stefany) |
| Desbloquea | [T-43 · E2E-1](../andres/T-43-e2e-cuentas-y-gateway.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-5* |
| Estado | Pendiente |

## Objetivo

Pestañas de usuarios, roles, salas, cuarentena y auditoría según los permisos de quien entra.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `useAlerts.test.ts`: cuenta solo las alertas nuevas, `reset()` y nada en `localStorage`
- [ ] Un rol con solo `audit:read` ve una sola pestaña
- [ ] El `409` del último admin se muestra tal como lo devuelve el servidor
- [ ] Las 4 verificaciones manuales del plan

## Entregables

- `frontend/src/pages/Admin.tsx`, `frontend/src/pages/admin/*.tsx`
- `frontend/src/lib/useAlerts.ts`

## Documentación a actualizar

- Ninguna

## Verificación

`npx vitest run` y la verificación manual del Step 3

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-43
