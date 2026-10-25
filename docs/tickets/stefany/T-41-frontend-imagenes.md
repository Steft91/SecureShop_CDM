# T-41 · FE-4: Frontend: imágenes en el chat

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Incremento | Incremento 3 |
| Bloqueado por | [T-40 · MED-4](../andres/T-40-media-descarga-y-cuarentena.md) (Andrés) |
| Desbloquea | [T-42 · FE-5](../zaith/T-42-frontend-panel-admin.md) (Zaith) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-4* |
| Estado | Pendiente |

## Objetivo

Subir y ver imágenes en el chat, con la renovación de la URL firmada.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `chatEvents.test.ts`: el evento `file`, la renovación `file_url` sin duplicar y el borrado de una imagen
- [ ] Una imagen retenida muestra "archivo retenido para revisión"
- [ ] Las 4 verificaciones manuales del plan

## Entregables

- `frontend/src/pages/Chat.tsx`
- `frontend/src/lib/chatEvents.ts`

## Documentación a actualizar

- Ninguna

## Verificación

`npx vitest run` y la verificación manual del Step 3

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Zaith de que puede empezar T-42
