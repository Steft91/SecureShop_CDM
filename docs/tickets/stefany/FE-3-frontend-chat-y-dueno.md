# FE-3: Frontend: chat cifrado y controles del dueño

| Campo | Valor |
|---|---|
| Responsable | Stefany |
| Módulo | Frontend |
| Incremento | Incremento 2 |
| Necesita | [FE-2](../stefany/FE-2-frontend-cuenta-y-salas.md) (Stefany), [ROOM-3](../andres/ROOM-3-rooms-moderacion.md) (Andrés), [CHAT-3](../zaith/CHAT-3-chat-tramas-y-mensajes.md) (Zaith), [GW-2](../zaith/GW-2-gateway-salas-media-ws.md) (Zaith) |
| Lo necesitan | [FE-4](../stefany/FE-4-frontend-imagenes.md) (Stefany), [FE-5](../andres/FE-5-frontend-panel-admin.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-3* |
| Estado | Pendiente |

## Objetivo

El chat con el protocolo cifrado y los controles del dueño de la sala.

## Cómo trabajar sin esperar

Las *Interfaces* de la tarea en el plan fijan los nombres y las firmas exactas que usan las demás tareas. Puedes escribir el código y sus tests contra esas interfaces y simular los servicios vecinos con `testing.Recorder`. El trabajo solo se detiene cuando falta algo de la fila *Necesita*, y casi siempre es la librería `shared`.

## Antes de empezar

La tarea está **por tareas**: el plan fija archivos, interfaces y tests, pero no el código. Escribe primero el código detallado partiendo de `docs/plans/rev3/2026-10-13-08-frontend.md` y de la tarea en el plan, y pide una revisión rápida al resto del equipo antes de implementarlo.

## Criterios de aceptación

- [ ] `chatEvents.test.ts` y `ws.test.ts` en verde (borrado, historial, códigos de cierre, *hello* inválido)
- [ ] Los mensajes se muestran como texto, nunca como HTML
- [ ] Las 6 verificaciones manuales del plan, con dos navegadores

## Entregables

- `frontend/src/lib/{ws,chatEvents}.ts`
- `frontend/src/pages/{Chat,RoomSettings}.tsx`

## Documentación a actualizar

- `CLAUDE.md`: incremento 2 cerrado

## Verificación

`npx vitest run` y la verificación manual del Step 3

## Al cerrar

- [ ] Los tests de la tarea están en verde, y `ruff check` y `ruff format --check` no reportan nada (o `npx vitest run`, en el frontend)
- [ ] La trazabilidad y los documentos de arriba están actualizados
- [ ] Commit con el mensaje del plan (en español y sin atribución). Nada de `push` ni de merge a `main` sin autorización
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit (aquí y en `docs/tickets/README.md`)
- [ ] Avisar a Andrés de que FE-3 ya está cerrado
