# T-36 · FE-3: Frontend: chat cifrado y controles del dueño

| Campo | Valor |
|---|---|
| Responsable | Zaith |
| Incremento | Incremento 2 |
| Bloqueado por | [T-35 · FE-2](../stefany/T-35-frontend-cuenta-y-salas.md) (Stefany) |
| Desbloquea | [T-37 · MED-1](../andres/T-37-media-archivos-cifrados.md) (Andrés) |
| Plan | [`docs/plans/2026-10-13-08-frontend.md`](../../plans/2026-10-13-08-frontend.md), sección *Task FE-3* |
| Estado | Pendiente |

## Objetivo

El chat con el protocolo cifrado y los controles del dueño de la sala.

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
- [ ] *Estado* = Cerrado, con la fecha y el hash del commit
- [ ] Avisar a Andrés de que puede empezar T-37
