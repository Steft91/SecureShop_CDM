# FE-5: Frontend: panel del admin global

| Campo | Valor |
|---|---|
| Responsable | Andrés |
| Módulo | Frontend |
| Incremento | Incremento 3 |
| Necesita | [FE-3](../stefany/FE-3-frontend-chat-y-dueno.md) (Stefany), [ATH-5](../andres/ATH-5-auth-suspension-y-latido.md) (Andrés), [MED-4](../stefany/MED-4-media-descarga-y-cuarentena.md) (Stefany) |
| Lo necesitan | [E2E-3](../zaith/E2E-3-cierre-final.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-5* |
| Estado | Pendiente |

## Objetivo

Pestañas de usuarios, roles, salas, cuarentena y auditoría según los permisos de quien entra.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `useAlerts.test.ts`: cuenta solo las alertas nuevas, `reset()` y nada en `localStorage`
- [ ] Un rol con solo `audit:read` ve una sola pestaña
- [ ] El `409` del último admin se muestra tal como lo devuelve el servidor
- [ ] Las 4 verificaciones manuales del plan
- [ ] Pestaña *Estado* con las métricas y la alerta `resource.high`; prueba de contraste y Lighthouse de accesibilidad ≥ 90 (ver el recuadro de la Actividad 3 en el plan)

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Zaith de que FE-5 ya está cerrado
