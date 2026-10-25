# FE-4: Frontend: imágenes en el chat

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Frontend |
| Incremento | Incremento 3 |
| Necesita | [FE-3](../stefany/FE-3-frontend-chat-y-dueno.md) (Stefany), [MED-3](../stefany/MED-3-media-politica-y-publicacion.md) (Stefany) |
| Lo necesitan | Nadie más |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-4* |
| Estado | Pendiente |

## Objetivo

Subir y ver imágenes en el chat, con la renovación de la URL firmada.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
